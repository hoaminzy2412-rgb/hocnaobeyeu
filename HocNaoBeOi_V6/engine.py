"""Học nào bé ơi! — Python standard-library server. See README.md."""
from __future__ import annotations
import base64, hashlib, hmac, json, mimetypes, os, re, secrets, shutil, sqlite3, time
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse, parse_qs

ROOT = Path(__file__).resolve().parent
DATA_DIR = Path(os.environ.get('SCHOOL_DATA_DIR', ROOT / 'data'))
MAX_FILE = 25 * 1024 * 1024
MAX_BODY = 36 * 1024 * 1024
SESSION_HOURS = 12

def now(): return int(time.time())
def uid(): return secrets.token_hex(12)
def hash_password(value, salt=None):
    salt = salt or secrets.token_hex(16)
    return salt + ':' + hashlib.pbkdf2_hmac('sha256', value.encode(), salt.encode(), 260000).hex()
def password_ok(value, hashed):
    return hmac.compare_digest(hash_password(value, hashed.split(':')[0]), hashed)
def require(condition, message='Không có quyền truy cập.', status=403):
    if not condition: raise APIError(status, message)
class APIError(Exception):
    def __init__(self, status, message): self.status, self.message = status, message
@contextmanager
def db():
    c = sqlite3.connect(DATA_DIR / 'school.sqlite3', timeout=20)
    c.row_factory = sqlite3.Row
    c.execute('PRAGMA foreign_keys=ON')
    try:
        yield c
        c.commit()
    except Exception:
        c.rollback()
        raise
    finally: c.close()
def one(c, sql, args=()):
    row = c.execute(sql, args).fetchone()
    return dict(row) if row else None
def rows(c, sql, args=()): return [dict(r) for r in c.execute(sql, args)]
def text(d, key, limit=3000, required=False):
    val = str(d.get(key, '') or '').strip()
    require(len(val) <= limit, f'{key}: nội dung quá dài (tối đa {limit} ký tự).', 400)
    require(not required or bool(val), 'Vui lòng nhập đầy đủ thông tin.', 400)
    return val

def initialize():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    (DATA_DIR / 'uploads').mkdir(exist_ok=True)
    with db() as c:
        c.executescript('''
        PRAGMA journal_mode=WAL;
        CREATE TABLE IF NOT EXISTS tenants(id TEXT PRIMARY KEY, name TEXT NOT NULL, demo INTEGER NOT NULL DEFAULT 0, created INTEGER NOT NULL);
        CREATE TABLE IF NOT EXISTS users(id TEXT PRIMARY KEY, tenant TEXT NOT NULL REFERENCES tenants(id), username TEXT UNIQUE NOT NULL, name TEXT NOT NULL, role TEXT NOT NULL CHECK(role IN ('teacher','parent')), password TEXT NOT NULL, active INTEGER NOT NULL DEFAULT 1);
        CREATE TABLE IF NOT EXISTS sessions(token TEXT PRIMARY KEY, user_id TEXT NOT NULL REFERENCES users(id), csrf TEXT NOT NULL, expires INTEGER NOT NULL, demo INTEGER NOT NULL DEFAULT 0);
        CREATE TABLE IF NOT EXISTS classes(id TEXT PRIMARY KEY, tenant TEXT NOT NULL REFERENCES tenants(id), name TEXT NOT NULL, age TEXT NOT NULL, year TEXT NOT NULL, created INTEGER NOT NULL);
        CREATE TABLE IF NOT EXISTS students(id TEXT PRIMARY KEY, tenant TEXT NOT NULL REFERENCES tenants(id), class_id TEXT NOT NULL REFERENCES classes(id), parent_id TEXT NOT NULL REFERENCES users(id), name TEXT NOT NULL, code TEXT NOT NULL, birthday TEXT NOT NULL DEFAULT '', note TEXT NOT NULL DEFAULT '', created INTEGER NOT NULL, UNIQUE(tenant,code));
        CREATE TABLE IF NOT EXISTS files(id TEXT PRIMARY KEY, tenant TEXT NOT NULL REFERENCES tenants(id), name TEXT NOT NULL, mime TEXT NOT NULL, size INTEGER NOT NULL, path TEXT NOT NULL, uploaded_by TEXT NOT NULL REFERENCES users(id), created INTEGER NOT NULL);
        CREATE TABLE IF NOT EXISTS resources(id TEXT PRIMARY KEY, tenant TEXT NOT NULL REFERENCES tenants(id), title TEXT NOT NULL, type TEXT NOT NULL, description TEXT NOT NULL, body TEXT NOT NULL, file_id TEXT REFERENCES files(id), questions TEXT NOT NULL DEFAULT '[]', created INTEGER NOT NULL);
        CREATE TABLE IF NOT EXISTS assignments(id TEXT PRIMARY KEY, tenant TEXT NOT NULL REFERENCES tenants(id), class_id TEXT NOT NULL REFERENCES classes(id), resource_id TEXT NOT NULL REFERENCES resources(id), student_id TEXT REFERENCES students(id), instructions TEXT NOT NULL, due TEXT NOT NULL, created INTEGER NOT NULL);
        CREATE TABLE IF NOT EXISTS attempts(id TEXT PRIMARY KEY, tenant TEXT NOT NULL REFERENCES tenants(id), assignment_id TEXT NOT NULL REFERENCES assignments(id), student_id TEXT NOT NULL REFERENCES students(id), answers TEXT NOT NULL, response TEXT NOT NULL, file_id TEXT REFERENCES files(id), score INTEGER, total INTEGER, review TEXT NOT NULL DEFAULT '', stars INTEGER NOT NULL DEFAULT 0, reviewed INTEGER, created INTEGER NOT NULL);
        CREATE TABLE IF NOT EXISTS news(id TEXT PRIMARY KEY, tenant TEXT NOT NULL REFERENCES tenants(id), class_id TEXT REFERENCES classes(id), title TEXT NOT NULL, body TEXT NOT NULL, created INTEGER NOT NULL);
        CREATE TABLE IF NOT EXISTS messages(id TEXT PRIMARY KEY, tenant TEXT NOT NULL REFERENCES tenants(id), parent_id TEXT NOT NULL REFERENCES users(id), sender_id TEXT NOT NULL REFERENCES users(id), body TEXT NOT NULL, read_at INTEGER, created INTEGER NOT NULL);
        CREATE TABLE IF NOT EXISTS notifications(id TEXT PRIMARY KEY, tenant TEXT NOT NULL REFERENCES tenants(id), user_id TEXT NOT NULL REFERENCES users(id), title TEXT NOT NULL, target TEXT NOT NULL, read_at INTEGER, created INTEGER NOT NULL);
        CREATE INDEX IF NOT EXISTS students_parent ON students(parent_id);
        CREATE INDEX IF NOT EXISTS messages_parent ON messages(parent_id,created);
        CREATE INDEX IF NOT EXISTS attempts_student ON attempts(student_id,created);
        ''')
        if not one(c, "SELECT id FROM tenants WHERE demo=0"):
            tenant, teacher = uid(), uid()
            p = os.environ.get('SCHOOL_TEACHER_PASSWORD') or secrets.token_urlsafe(12)
            require(len(p) >= 10, 'SCHOOL_TEACHER_PASSWORD cần ít nhất 10 ký tự.', 400)
            c.execute('INSERT INTO tenants VALUES(?,?,0,?)', (tenant, 'Trường Mầm non Vạn Hà · Phân hiệu Thiệu Nguyên', now()))
            c.execute('INSERT INTO users VALUES(?,?,?,?,?,?,1)', (teacher,tenant,'cohoa','Cô Hoa','teacher',hash_password(p)))
            credentials = f'Tài khoản quản trị viên: cohoa\nMật khẩu: {p}\nĐịa chỉ: http://localhost:8000\nĐổi mật khẩu tại Cài đặt sau khi đăng nhập.\n'
            (DATA_DIR / 'TAI_KHOAN_BAN_DAU.txt').write_text(credentials, encoding='utf-8')
            try: os.chmod(DATA_DIR / 'TAI_KHOAN_BAN_DAU.txt', 0o600)
            except OSError: pass
            print('\n'+credentials, flush=True)

def notify(c, tenant, users, title, target):
    for u in set(users):
        c.execute('INSERT INTO notifications VALUES(?,?,?,?,?,NULL,?)', (uid(),tenant,u,title,target,now()))
def tenant_parents(c, t, class_id=None):
    if class_id: return [r['parent_id'] for r in c.execute('SELECT DISTINCT parent_id FROM students WHERE tenant=? AND class_id=?',(t,class_id))]
    return [r['id'] for r in c.execute("SELECT id FROM users WHERE tenant=? AND role='parent' AND active=1",(t,))]

def seed_demo(c):
    t, teacher, parent, parent2, cl, s, s2 = [uid() for _ in range(7)]
    c.execute('INSERT INTO tenants VALUES(?,?,1,?)',(t,'Trường mầm non Hạnh Phúc · Dữ liệu trải nghiệm',now()))
    for id,name,role in [(teacher,'Cô Hoa · Trải nghiệm','teacher'),(parent,'Mẹ bé An · Trải nghiệm','parent'),(parent2,'Bố bé Bình · Trải nghiệm','parent')]:
        c.execute('INSERT INTO users VALUES(?,?,?,?,?,?,1)',(id,t,'demo_'+id,name,role,hash_password(secrets.token_urlsafe(24))))
    c.execute('INSERT INTO classes VALUES(?,?,?,?,?,?)',(cl,t,'Mẫu giáo lớn A4','5–6 tuổi','2026–2027',now()))
    for id,name,code,p in [(s,'Bé An','HS0001',parent),(s2,'Bé Bình','HS0002',parent2)]:
        c.execute('INSERT INTO students VALUES(?,?,?,?,?,?,?,?,?)',(id,t,cl,p,name,code,'2021-03-08','Học sinh mẫu, không phải dữ liệu thật.',now()))
    games = [('Ong tìm chữ','🐝 Bé chạm vào bông hoa có chữ đúng nhé!',[{'question':'Bông hoa nào có chữ a?','options':['a','ă','â'],'answer':0},{'question':'Bé hãy tìm chữ ă!','options':['â','a','ă'],'answer':2},{'question':'Chữ nào có chiếc mũ?','options':['a','â','ă'],'answer':1}]),('Bé đếm vui','🐠 Cùng đếm với những người bạn nhỏ!',[{'question':'🍎 🍎 🍎 — Có mấy quả táo?','options':['2','3','4'],'answer':1},{'question':'🐟 🐟 🐟 🐟 — Có mấy chú cá?','options':['4','5','6'],'answer':0}]),('Ghép đôi thông minh','🌈 Chọn điều phù hợp nhất!',[{'question':'🐄 Con bò cho chúng mình sản phẩm nào?','options':['🥛 Sữa','🥚 Trứng','🍯 Mật ong'],'answer':0},{'question':'Trời mưa, bé cần mang gì?','options':['🕶️ Kính râm','☂️ Ô','🪁 Diều'],'answer':1}])]
    for title,desc,qs in games:
        r,a=uid(),uid()
        c.execute('INSERT INTO resources VALUES(?,?,?,?,?,?,?,?,?)',(r,t,title,'quiz',desc,'',None,json.dumps(qs,ensure_ascii=False),now()))
        c.execute('INSERT INTO assignments VALUES(?,?,?,?,?,?,?,?)',(a,t,cl,r,None,'Bố mẹ đồng hành, để con tự chọn đáp án nhé!','',now()))
    c.execute('INSERT INTO news VALUES(?,?,?,?,?,?)',(uid(),t,cl,'Chào mừng gia đình đến với lớp A4!','Mỗi ngày một niềm vui. Bố mẹ hãy cùng con khám phá các trò chơi cô đã chuẩn bị nhé! 🌷',now()))
    c.execute('INSERT INTO messages VALUES(?,?,?,?,?,NULL,?)',(uid(),t,parent,teacher,'Chào bố mẹ bé An! Hôm nay con đã rất hào hứng tham gia hoạt động cùng các bạn. 💗',now()))
    return teacher

class BaseHandler(BaseHTTPRequestHandler):
    server_version='HocNaoBeOi/2'
    def log_message(self, fmt, *args):
        if os.environ.get('SCHOOL_LOG'): super().log_message(fmt,*args)
    def headers_common(self):
        self.send_header('X-Content-Type-Options','nosniff')
        self.send_header('X-Frame-Options','DENY')
        self.send_header('Referrer-Policy','same-origin')
        self.send_header('Content-Security-Policy',"default-src 'self'; img-src 'self' data: blob:; media-src 'self' blob:; style-src 'self'; script-src 'self'; connect-src 'self'; frame-ancestors 'none'; base-uri 'self'; form-action 'self'")
    def reply(self, status=200, value=None, cookie=None):
        body=json.dumps(value or {},ensure_ascii=False).encode()
        self.send_response(status);self.headers_common()
        self.send_header('Content-Type','application/json; charset=utf-8')
        self.send_header('Cache-Control','no-store');self.send_header('Content-Length',str(len(body)))
        if cookie:self.send_header('Set-Cookie',cookie)
        self.end_headers();self.wfile.write(body)
    def token(self):
        for part in self.headers.get('Cookie','').split(';'):
            if part.strip().startswith('school_session='):return hashlib.sha256(part.strip().split('=',1)[1].encode()).hexdigest()
        return ''
    def session(self,c):
        return one(c,'''SELECT u.id,u.tenant,u.name,u.username,u.role,s.csrf,s.demo,s.token FROM sessions s JOIN users u ON s.user_id=u.id WHERE s.token=? AND s.expires>? AND u.active=1''',(self.token(),now()))
    def login_session(self,c,user_id,demo=False):
        token,csrf=secrets.token_urlsafe(40),secrets.token_urlsafe(30)
        c.execute('INSERT INTO sessions VALUES(?,?,?,?,?)',(hashlib.sha256(token.encode()).hexdigest(),user_id,csrf,now()+SESSION_HOURS*3600,int(demo)))
        secure='; Secure' if os.environ.get('SCHOOL_SECURE_COOKIE')=='1' else ''
        return f'school_session={token}; HttpOnly; SameSite=Strict; Path=/; Max-Age={SESSION_HOURS*3600}'+secure
    def get_object(self,c,table,id,u):
        require(table in ['classes','students','resources','assignments','attempts','news','files','users'])
        r=one(c,f'SELECT * FROM {table} WHERE id=? AND tenant=?',(id,u['tenant']))
        require(r is not None,'Không tìm thấy dữ liệu hoặc bạn không có quyền.',404)
        return r
    def kids(self,c,u):return rows(c,'SELECT * FROM students WHERE parent_id=? AND tenant=?',(u['id'],u['tenant']))
    def can_assignment(self,c,a,u):
        if u['role']=='teacher':return True
        return any(s['class_id']==a['class_id'] and (not a['student_id'] or a['student_id']==s['id']) for s in self.kids(c,u))
    def can_file(self,c,id,u):
        if u['role']=='teacher':return True
        if one(c,'SELECT id FROM files WHERE id=? AND uploaded_by=?',(id,u['id'])):return True
        kids=self.kids(c,u)
        for a in rows(c,'''SELECT a.*,r.file_id FROM assignments a JOIN resources r ON a.resource_id=r.id WHERE a.tenant=? AND r.file_id=?''',(u['tenant'],id)):
            if self.can_assignment(c,a,u):return True
        return any(one(c,'SELECT id FROM attempts WHERE file_id=? AND student_id=?',(id,s['id'])) for s in kids)
    def bootstrap(self,c,u):
        t=u['tenant'];out={'user':{k:u[k] for k in ['id','name','username','role','demo']},'csrf':u['csrf'],'school':one(c,'SELECT name FROM tenants WHERE id=?',(t,))['name']}
        teacher=u['role']=='teacher'
        out['demo_parents']=rows(c,"SELECT id,name FROM users WHERE tenant=? AND role='parent' AND active=1 ORDER BY rowid",(t,)) if u['demo'] else []
        out['classes']=rows(c,'SELECT * FROM classes WHERE tenant=? ORDER BY created DESC',(t,))
        out['students']=rows(c,'SELECT * FROM students WHERE tenant=? ORDER BY name',(t,)) if teacher else self.kids(c,u)
        cls={s['class_id'] for s in out['students']};kid_ids={s['id'] for s in out['students']}
        if not teacher:out['classes']=[x for x in out['classes'] if x['id'] in cls]
        out['parents']=rows(c,"SELECT id,name,username,active FROM users WHERE tenant=? AND role='parent' ORDER BY name",(t,)) if teacher else []
        out['assignments']=rows(c,'SELECT * FROM assignments WHERE tenant=? ORDER BY created DESC',(t,))
        if not teacher:out['assignments']=[a for a in out['assignments'] if a['class_id'] in cls and (not a['student_id'] or a['student_id'] in kid_ids)]
        rs={a['resource_id'] for a in out['assignments']}
        out['resources']=rows(c,'SELECT * FROM resources WHERE tenant=? ORDER BY created DESC',(t,))
        if not teacher:out['resources']=[r for r in out['resources'] if r['id'] in rs]
        for r in out['resources']:
            r['questions']=json.loads(r['questions'])
            if not teacher:
                for q in r['questions']:q.pop('answer',None)
        out['attempts']=rows(c,'SELECT * FROM attempts WHERE tenant=? ORDER BY created DESC',(t,))
        if not teacher:out['attempts']=[a for a in out['attempts'] if a['student_id'] in kid_ids]
        for a in out['attempts']:a['answers']=json.loads(a['answers'])
        out['news']=rows(c,'SELECT * FROM news WHERE tenant=? ORDER BY created DESC',(t,))
        if not teacher:out['news']=[n for n in out['news'] if not n['class_id'] or n['class_id'] in cls]
        out['messages']=rows(c,'SELECT m.*,u.name AS sender_name FROM messages m JOIN users u ON u.id=m.sender_id WHERE m.tenant=? ORDER BY m.created,m.rowid',(t,))
        if not teacher:out['messages']=[m for m in out['messages'] if m['parent_id']==u['id']]
        out['notifications']=rows(c,'SELECT * FROM notifications WHERE user_id=? ORDER BY created DESC LIMIT 80',(u['id'],))
        allowed_files={r['file_id'] for r in out['resources']}|{a['file_id'] for a in out['attempts']}
        out['files']=rows(c,'SELECT id,name,mime,size FROM files WHERE tenant=?',(t,))
        if not teacher:out['files']=[f for f in out['files'] if f['id'] in allowed_files]
        return out
    def do_GET(self):
        try:
            parsed=urlparse(self.path);path=parsed.path
            if path=='/api/bootstrap':
                with db() as c:
                    u=self.session(c);require(u,'Vui lòng đăng nhập.',401);value=self.bootstrap(c,u)
                return self.reply(value=value)
            if path.startswith('/api/files/'):
                with db() as c:
                    u=self.session(c);require(u,'Vui lòng đăng nhập.',401)
                    f=self.get_object(c,'files',path.split('/')[-1],u);require(self.can_file(c,f['id'],u))
                return self.serve_file(DATA_DIR/'uploads'/f['path'],f['mime'],f['name'],parse_qs(parsed.query).get('download')==['1'])
            if path.startswith('/api/'):raise APIError(404,'Không tìm thấy chức năng.')
            rel='index.html' if path=='/' else path.lstrip('/')
            p=(ROOT/'static'/rel).resolve()
            require(p.is_relative_to((ROOT/'static').resolve()) and p.is_file(),'Không tìm thấy tệp.',404)
            return self.serve_file(p,mimetypes.guess_type(p.name)[0] or 'application/octet-stream')
        except APIError as e:self.reply(e.status,{'error':e.message})
        except (BrokenPipeError,ConnectionResetError):pass
    def serve_file(self,path,mime,name=None,download=False):
        require(path.is_file(),'Tệp không còn tồn tại.',404)
        size=path.stat().st_size;start,end=0,size-1;status=200
        rng=self.headers.get('Range')
        if rng:
            m=re.fullmatch(r'bytes=(\d*)-(\d*)',rng)
            require(m is not None,'Khoảng tải không hợp lệ.',416)
            if m[1]:start=int(m[1]);end=min(int(m[2]) if m[2] else size-1,size-1)
            else:start=max(0,size-int(m[2] or 0))
            require(0<=start<=end<size,'Khoảng tải không hợp lệ.',416);status=206
        self.send_response(status);self.headers_common();self.send_header('Content-Type',mime)
        self.send_header('Cache-Control','private, no-store' if name else 'no-cache')
        self.send_header('Accept-Ranges','bytes');self.send_header('Content-Length',str(max(0,end-start+1)))
        if status==206:self.send_header('Content-Range',f'bytes {start}-{end}/{size}')
        if name:
            from urllib.parse import quote
            self.send_header('Content-Disposition',('attachment' if download else 'inline')+"; filename*=UTF-8''"+quote(name))
        self.end_headers()
        with path.open('rb') as f:
            f.seek(start);left=end-start+1
            while left>0:
                chunk=f.read(min(left,65536))
                if not chunk:break
                self.wfile.write(chunk);left-=len(chunk)
