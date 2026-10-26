"""Học nào bé ơi! V3 — school, roles, games, media and assessment."""
from __future__ import annotations
import base64, hashlib, hmac, json, os, re, secrets, sqlite3, time, urllib.request, urllib.error
from pathlib import Path
from urllib.parse import urlparse,parse_qs,quote
import engine as E
from engine import APIError,require,one,rows,text,now,uid,hash_password,password_ok,notify
ROOT=Path(__file__).resolve().parent
DATA_DIR=E.DATA_DIR
MAX_FILE=E.MAX_FILE
MAX_BODY=E.MAX_BODY
SESSION_HOURS=E.SESSION_HOURS
db=E.db

def isint(v):return isinstance(v,int) and not isinstance(v,bool)
def add_col(c,table,definition):
    col=definition.split()[0]
    if col not in {r['name'] for r in c.execute(f'PRAGMA table_info({table})')}:c.execute(f'ALTER TABLE {table} ADD COLUMN {definition}')
def staff(u):return u['role'] in ['teacher','admin']
def admin(u):require(u['role']=='admin','Chức năng dành cho quản trị viên.')
def class_ids(c,u):
    if u['role']=='admin':return [r['id'] for r in c.execute('SELECT id FROM classes WHERE tenant=?',(u['tenant'],))]
    if u['role']=='teacher':return [r['id'] for r in c.execute('SELECT id FROM classes WHERE tenant=? AND teacher_id=?',(u['tenant'],u['id']))]
    return [r['class_id'] for r in c.execute('SELECT class_id FROM students WHERE parent_id=? AND tenant=?',(u['id'],u['tenant']))]
def students_for(c,u):
    all=rows(c,'SELECT * FROM students WHERE tenant=? ORDER BY name',(u['tenant'],))
    if u['role']=='admin':return all
    if u['role']=='parent':return [s for s in all if s['parent_id']==u['id']]
    ids=set(class_ids(c,u));return [s for s in all if s['class_id'] in ids]
def parent_ids(c,u,cl=None):return list({s['parent_id'] for s in students_for(c,u) if not cl or s['class_id']==cl})
def validate_questions(qs):
    require(isinstance(qs,list) and 1<=len(qs)<=30,'Game cần 1–30 câu hỏi.',400);out=[]
    for q in qs:
        require(isinstance(q,dict) and isinstance(q.get('options'),list) and 2<=len(q['options'])<=4,'Mỗi câu cần 2–4 lựa chọn.',400)
        opts=[str(x).strip() for x in q['options']]
        require(all(opts) and all(len(x)<=300 for x in opts),'Nhập đủ nội dung các đáp án.',400)
        require(isint(q.get('answer')) and 0<=q['answer']<len(opts),'Đáp án đúng không hợp lệ.',400)
        out.append({'question':text(q,'question',1000,True),'options':opts,'answer':q['answer']})
    return out

def initialize():
    E.DATA_DIR=DATA_DIR
    E.initialize()
    with db() as c:
        c.executescript('''
        CREATE TABLE IF NOT EXISTS admins(user_id TEXT PRIMARY KEY REFERENCES users(id));
        CREATE TABLE IF NOT EXISTS school_info(tenant TEXT PRIMARY KEY REFERENCES tenants(id),address TEXT NOT NULL DEFAULT '',phone TEXT NOT NULL DEFAULT '',principal TEXT NOT NULL DEFAULT '');
        CREATE TABLE IF NOT EXISTS school_years(id TEXT PRIMARY KEY,tenant TEXT NOT NULL REFERENCES tenants(id),name TEXT NOT NULL,active INTEGER NOT NULL DEFAULT 1);
        CREATE TABLE IF NOT EXISTS grades(id TEXT PRIMARY KEY,tenant TEXT NOT NULL REFERENCES tenants(id),name TEXT NOT NULL,age TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS class_reviews(id TEXT PRIMARY KEY,tenant TEXT NOT NULL REFERENCES tenants(id),class_id TEXT NOT NULL REFERENCES classes(id),student_id TEXT NOT NULL REFERENCES students(id),teacher_id TEXT NOT NULL REFERENCES users(id),body TEXT NOT NULL,created INTEGER NOT NULL);
        CREATE TABLE IF NOT EXISTS plays(id TEXT PRIMARY KEY,tenant TEXT NOT NULL REFERENCES tenants(id),user_id TEXT NOT NULL REFERENCES users(id),assignment_id TEXT NOT NULL REFERENCES assignments(id),student_id TEXT NOT NULL REFERENCES students(id),nonce TEXT NOT NULL,started INTEGER NOT NULL,finished INTEGER);
        ''')
        for table,defs in {
            'classes':["grade_id TEXT REFERENCES grades(id)","teacher_id TEXT REFERENCES users(id)"],
            'resources':["illustration_id TEXT REFERENCES files(id)","theme TEXT NOT NULL DEFAULT 'auto'","category TEXT NOT NULL DEFAULT 'games'","external_url TEXT NOT NULL DEFAULT ''","integration INTEGER NOT NULL DEFAULT 0","creator_id TEXT REFERENCES users(id)"],
            'assignments':["creator_id TEXT REFERENCES users(id)","batch_id TEXT NOT NULL DEFAULT ''","origin TEXT NOT NULL DEFAULT 'teacher'"],
            'attempts':["duration INTEGER NOT NULL DEFAULT 0","source TEXT NOT NULL DEFAULT 'native'","trusted INTEGER NOT NULL DEFAULT 1","play_id TEXT","recording_id TEXT REFERENCES files(id)"],
            'news':["file_id TEXT REFERENCES files(id)","creator_id TEXT REFERENCES users(id)"]
        }.items():
            for definition in defs:add_col(c,table,definition)
        for tenant in rows(c,'SELECT * FROM tenants'):
            setup_tenant(c,tenant['id'])
        # Stable one-time V2 migration: first legacy teacher becomes administrator.
        c.execute('DELETE FROM sessions WHERE expires<?',(now(),))
        credential=DATA_DIR/'TAI_KHOAN_BAN_DAU.txt'
        if credential.exists():credential.write_text(credential.read_text(encoding='utf-8').replace('Tài khoản giáo viên:','Tài khoản quản trị viên:').replace('cohoa','cohoa'),encoding='utf-8')
    print('V4: tài khoản cohoa hiện là quản trị viên. Cấp tài khoản giáo viên trong mục Giáo viên.',flush=True)

def setup_tenant(c,t):
    lead=one(c,"SELECT id FROM users WHERE tenant=? AND role='teacher' ORDER BY rowid LIMIT 1",(t,))
    if lead and not one(c,'SELECT a.user_id FROM admins a JOIN users u ON a.user_id=u.id WHERE u.tenant=?',(t,)):c.execute('INSERT INTO admins VALUES(?)',(lead['id'],))
    c.execute('INSERT OR IGNORE INTO school_info(tenant) VALUES(?)',(t,))
    if not one(c,'SELECT id FROM school_years WHERE tenant=?',(t,)):c.execute('INSERT INTO school_years VALUES(?,?,?,1)',(uid(),t,'2026–2027'))
    for name,age in [('Nhà trẻ','18–36 tháng'),('Mẫu giáo bé','3–4 tuổi'),('Mẫu giáo nhỡ','4–5 tuổi'),('Mẫu giáo lớn','5–6 tuổi')]:
        if not one(c,'SELECT id FROM grades WHERE tenant=? AND name=?',(t,name)):c.execute('INSERT INTO grades VALUES(?,?,?,?)',(uid(),t,name,age))
    for cl in rows(c,'SELECT * FROM classes WHERE tenant=?',(t,)):
        if not one(c,'SELECT id FROM school_years WHERE tenant=? AND name=?',(t,cl['year'])):c.execute('INSERT INTO school_years VALUES(?,?,?,0)',(uid(),t,cl['year']))
        if not cl['grade_id']:
            age=cl['age'].replace('-', '–')
            name='Nhà trẻ' if 'tháng' in age else 'Mẫu giáo bé' if age.startswith('3') else 'Mẫu giáo nhỡ' if age.startswith('4') else 'Mẫu giáo lớn'
            grade=one(c,'SELECT id FROM grades WHERE tenant=? AND name=?',(t,name))
            c.execute('UPDATE classes SET grade_id=? WHERE id=?',(grade['id'],cl['id']))
    if lead:
        c.execute('UPDATE resources SET creator_id=? WHERE tenant=? AND creator_id IS NULL',(lead['id'],t))
        c.execute('UPDATE assignments SET creator_id=? WHERE tenant=? AND creator_id IS NULL',(lead['id'],t))
        c.execute('UPDATE news SET creator_id=? WHERE tenant=? AND creator_id IS NULL',(lead['id'],t))

def seed_demo(c):
    # Legacy seed uses explicit column lists because V3 adds columns.
    t,ad,te,p,p2,cl,s,s2=[uid() for _ in range(8)]
    c.execute('INSERT INTO tenants VALUES(?,?,1,?)',(t,'Trường Mầm non Hạnh Phúc · Trải nghiệm',now()))
    for id,name,role in [(ad,'Cô Hoa · Admin','teacher'),(te,'Cô Mai · Giáo viên','teacher'),(p,'Gia đình bé An','parent'),(p2,'Gia đình bé Bình','parent')]:c.execute('INSERT INTO users VALUES(?,?,?,?,?,?,1)',(id,t,'demo_'+id,name,role,hash_password(secrets.token_urlsafe(16))))
    c.execute('INSERT INTO admins VALUES(?)',(ad,));setup_tenant(c,t)
    grade=one(c,"SELECT id FROM grades WHERE tenant=? AND name='Mẫu giáo lớn'",(t,))['id']
    c.execute('INSERT INTO classes(id,tenant,name,age,year,created,grade_id,teacher_id) VALUES(?,?,?,?,?,?,?,?)',(cl,t,'Mẫu giáo lớn A4','5–6 tuổi','2026–2027',now(),grade,te))
    for id,name,code,parent in [(s,'Bé An','HS20260001',p),(s2,'Bé Bình','HS20260002',p2)]:c.execute('INSERT INTO students VALUES(?,?,?,?,?,?,?,?,?)',(id,t,cl,parent,name,code,'2021-03-08','Học sinh mẫu.',now()))
    for title,desc,qs in [('Ong tìm chữ','Bé giúp ong tìm đúng chữ nhé!',[{'question':'Chữ nào là chữ a?','options':['a','ă','â'],'answer':0},{'question':'Bé hãy tìm chữ â!','options':['ă','â','a'],'answer':1}]),('Bé đếm vui','Đếm những người bạn nhỏ quanh bé.',[{'question':'🍎 🍎 🍎 — Có mấy quả táo?','options':['2','3','4'],'answer':1},{'question':'🐠 🐠 — Có mấy chú cá?','options':['2','4','3'],'answer':0}]),('Bé đến trường','Mỗi ngày đến trường là một ngày vui.',[{'question':'Đến lớp, bé chào ai?','options':['Cô và các bạn','Không chào ai','Chỉ chào đồ chơi'],'answer':0}])]:
        rid,aid=uid(),uid()
        c.execute('INSERT INTO resources(id,tenant,title,type,description,body,file_id,questions,created,category,creator_id) VALUES(?,?,?,?,?,?,NULL,?,?,?,?)',(rid,t,title,'quiz',desc,'',json.dumps(qs,ensure_ascii=False),now(),'games',te))
        c.execute('INSERT INTO assignments(id,tenant,class_id,resource_id,student_id,instructions,due,created,creator_id,batch_id) VALUES(?,?,?,?,NULL,?,?,?,?,?)',(aid,t,cl,rid,'Bố mẹ để bé tự chọn đáp án nhé!','',now(),te,''))
    c.execute('INSERT INTO news(id,tenant,class_id,title,body,created,creator_id) VALUES(?,?,?,?,?,?,?)',(uid(),t,None,'Chào mừng gia đình đến lớp học nhỏ!','Bố mẹ cùng con khám phá và gửi lời nhắn cho cô nhé! 🌷',now(),ad))
    return ad

class App(E.BaseHandler):
    server_version='HocNaoBeOi/4'
    def session(self,c):
        return one(c,"""SELECT u.id,u.tenant,u.name,u.username,CASE WHEN a.user_id IS NOT NULL THEN 'admin' ELSE u.role END role,s.csrf,s.demo,s.token FROM sessions s JOIN users u ON s.user_id=u.id LEFT JOIN admins a ON a.user_id=u.id WHERE s.token=? AND s.expires>? AND u.active=1""",(self.token(),now()))
    def get_object(self,c,table,id,u):
        require(table in ['classes','students','resources','assignments','attempts','news','files','users','school_years','grades','plays'])
        r=one(c,f'SELECT * FROM {table} WHERE id=? AND tenant=?',(id,u['tenant']))
        require(r,'Không tìm thấy dữ liệu hoặc không có quyền.',404);return r
    def authorized_class(self,c,id,u):
        r=self.get_object(c,'classes',id,u);require(u['role']=='admin' or (u['role']=='teacher' and r['teacher_id']==u['id']),'Lớp chưa được phân công cho giáo viên này.');return r
    def authorized_student(self,c,id,u):
        r=self.get_object(c,'students',id,u)
        if u['role']=='parent':require(r['parent_id']==u['id'])
        else:self.authorized_class(c,r['class_id'],u)
        return r
    def can_assignment(self,c,a,u):
        if u['role']=='admin':return True
        if u['role']=='teacher':return a['class_id'] in class_ids(c,u)
        return any(s['class_id']==a['class_id'] and (not a['student_id'] or s['id']==a['student_id']) for s in students_for(c,u))
    def can_resource(self,c,r,u):
        if staff(u):return True  # Staff share the school resource bank.
        if r['category'] in ['stories','music']:return True
        return any(self.can_assignment(c,a,u) for a in rows(c,'SELECT * FROM assignments WHERE resource_id=? AND tenant=?',(r['id'],u['tenant'])))
    def can_file(self,c,id,u):
        f=self.get_object(c,'files',id,u)
        if u['role']=='admin' or f['uploaded_by']==u['id']:return True
        for r in rows(c,'SELECT * FROM resources WHERE (file_id=? OR illustration_id=?) AND tenant=?',(id,id,u['tenant'])):
            if self.can_resource(c,r,u):return True
        for n in rows(c,'SELECT * FROM news WHERE file_id=? AND tenant=?',(id,u['tenant'])):
            if not n['class_id'] or n['class_id'] in class_ids(c,u):return True
        return any((a['file_id']==id or a.get('recording_id')==id) for a in rows(c,'SELECT * FROM attempts WHERE tenant=?',(u['tenant'],)) if a['student_id'] in {s['id'] for s in students_for(c,u)})
    def ranking(self,c,u):
        students=rows(c,'SELECT * FROM students WHERE tenant=?',(u['tenant'],))
        if u['role']=='teacher':students=students_for(c,u)
        mine={s['id'] for s in students_for(c,u)} if u['role']=='parent' else set()
        if u['role']=='parent':students=[s for s in students if s['class_id'] in class_ids(c,u)]
        result=[]
        for s in students:
            best={}
            for a in rows(c,"SELECT a.* FROM attempts a JOIN assignments g ON a.assignment_id=g.id WHERE a.student_id=? AND a.trusted=1 AND g.origin='teacher'",(s['id'],)):
                key=(a['score'] if a['score'] is not None else 0,-a['duration'])
                if a['assignment_id'] not in best or key>best[a['assignment_id']][0]:best[a['assignment_id']]=(key,a)
            aa=[a for _,a in best.values()]
            result.append({'student_id':s['id'] if staff(u) or s['id'] in mine else '', 'class_id':s['class_id'],'name':s['name'] if staff(u) or s['id'] in mine else 'Bạn nhỏ '+str(len(result)+1),'mine':s['id'] in mine,'completed':len(aa),'correct':sum(a['score'] or 0 for a in aa),'total':sum(a['total'] or 0 for a in aa),'duration':sum(a['duration'] for a in aa)})
        result.sort(key=lambda r:(-r['completed'],-r['correct'],r['duration'],r['name']))
        rank=0;last=None
        for i,r in enumerate(result):
            key=(r['completed'],r['correct'],r['duration'])
            if key!=last:rank=i+1;last=key
            r['rank']=rank if r['completed'] else None
        return result
    def bootstrap(self,c,u):
        t=u['tenant'];classes=rows(c,'SELECT * FROM classes WHERE tenant=? ORDER BY name',(t,));kids=students_for(c,u);ids={s['id'] for s in kids};cis=set(class_ids(c,u))
        assignments=[a for a in rows(c,'SELECT * FROM assignments WHERE tenant=? ORDER BY created DESC',(t,)) if self.can_assignment(c,a,u)]
        resources=[r for r in rows(c,'SELECT * FROM resources WHERE tenant=? ORDER BY created DESC',(t,)) if self.can_resource(c,r,u)]
        for r in resources:
            r['questions']=json.loads(r['questions'])
            if not staff(u):
                for q in r['questions']:q.pop('answer',None)
        news=[n for n in rows(c,'SELECT * FROM news WHERE tenant=? ORDER BY created DESC',(t,)) if u['role']=='admin' or not n['class_id'] or n['class_id'] in cis]
        attempts=[a for a in rows(c,'SELECT * FROM attempts WHERE tenant=? ORDER BY created DESC',(t,)) if a['student_id'] in ids]
        for a in attempts:a['answers']=json.loads(a['answers'])
        parents=rows(c,"SELECT id,name,username,active FROM users WHERE tenant=? AND role='parent'",(t,))
        if u['role']=='teacher':parents=[p for p in parents if p['id'] in {s['parent_id'] for s in kids}]
        if u['role']=='parent':parents=[]
        pids={p['id'] for p in parents} if staff(u) else {u['id']}
        messages=[m for m in rows(c,'SELECT m.*,u.name sender_name FROM messages m JOIN users u ON m.sender_id=u.id WHERE m.tenant=? ORDER BY m.created,m.rowid',(t,)) if m['parent_id'] in pids]
        allowed={r['illustration_id'] for r in resources}|{r['file_id'] for r in resources}|{n['file_id'] for n in news}|{a['file_id'] for a in attempts}|{a.get('recording_id') for a in attempts}
        files=rows(c,'SELECT id,name,mime,size FROM files WHERE tenant=?',(t,))
        if u['role']!='admin':
            owned={x['id'] for x in c.execute('SELECT id FROM files WHERE tenant=? AND uploaded_by=?',(t,u['id']))}
            files=[f for f in files if f['id'] in allowed or f['id'] in owned]
        teachers=rows(c,"SELECT u.id,u.name,u.username,u.active FROM users u LEFT JOIN admins a ON u.id=a.user_id WHERE u.tenant=? AND u.role='teacher' AND a.user_id IS NULL ORDER BY u.name",(t,)) if staff(u) else []
        config={} if u['demo'] else read_ai_config()
        return {'user':{k:u[k] for k in ['id','name','username','role','demo']},'csrf':u['csrf'],'school':one(c,'SELECT name FROM tenants WHERE id=?',(t,))['name'],'school_info':one(c,'SELECT * FROM school_info WHERE tenant=?',(t,)),'years':rows(c,'SELECT * FROM school_years WHERE tenant=? ORDER BY name DESC',(t,)),'grades':rows(c,'SELECT * FROM grades WHERE tenant=? ORDER BY rowid',(t,)),'classes':classes if u['role']=='admin' else [cl for cl in classes if cl['id'] in cis],'students':kids,'parents':parents,'teachers':teachers,'resources':resources,'assignments':assignments,'attempts':attempts,'news':news,'messages':messages,'files':files,'notifications':rows(c,'SELECT * FROM notifications WHERE user_id=? ORDER BY created DESC LIMIT 100',(u['id'],)),'class_reviews':[r for r in rows(c,'SELECT r.*,u.name teacher_name FROM class_reviews r JOIN users u ON r.teacher_id=u.id WHERE r.tenant=? ORDER BY r.created DESC',(t,)) if r['student_id'] in ids],'rankings':self.ranking(c,u),'ai':{'configured':bool(config.get('key') and config.get('url') and config.get('model')),'url':config.get('url','') if u['role']=='admin' else '', 'model':config.get('model','') if u['role']=='admin' else ''},'demo_parents':rows(c,"SELECT id,name FROM users WHERE tenant=? AND role='parent' ORDER BY rowid",(t,)) if u['demo'] else []}
    def headers_common(self):
        self.send_header('Permissions-Policy', 'microphone=(), camera=()' if getattr(self,'game_response',False) else 'microphone=(self), camera=()')
        if getattr(self,'game_response',False):
            self.send_header('X-Content-Type-Options','nosniff');self.send_header('Referrer-Policy','no-referrer')
            self.send_header('Content-Security-Policy',"sandbox allow-scripts; default-src 'none'; script-src 'unsafe-inline' https: data: blob:; style-src 'unsafe-inline' https:; img-src data: blob: https:; media-src data: blob: https:; connect-src https:; font-src data: https:; frame-ancestors 'self'; base-uri 'none'; form-action 'none'")
        else:
            self.send_header('X-Content-Type-Options','nosniff');self.send_header('X-Frame-Options','DENY');self.send_header('Referrer-Policy','same-origin')
            self.send_header('Content-Security-Policy',"default-src 'self'; img-src 'self' data: blob:; media-src 'self' blob:; style-src 'self'; script-src 'self'; connect-src 'self'; frame-src 'self' https:; frame-ancestors 'none'; base-uri 'self'; form-action 'self'")
    def do_GET(self):
        self.game_response=False
        try:
            parsed=urlparse(self.path);path=parsed.path
            if path=='/api/bootstrap':
                with db() as c:u=self.session(c);require(u,'Vui lòng đăng nhập.',401);result=self.bootstrap(c,u)
                return self.reply(value=result)
            if path.startswith('/api/files/') or path.startswith('/api/game/'):
                with db() as c:
                    u=self.session(c);require(u,'Vui lòng đăng nhập.',401)
                    f=self.get_object(c,'files',path.split('/')[-1],u);require(self.can_file(c,f['id'],u))
                game=path.startswith('/api/game/');require(not game or f['mime']=='text/html; charset=utf-8','Định dạng game không hợp lệ.',400)
                self.game_response=game
                download=parse_qs(parsed.query).get('download')==['1'] or (f['mime'].startswith('text/html') and not game)
                return self.serve_file(DATA_DIR/'uploads'/f['path'],f['mime'],f['name'],download)
            if path.startswith('/api/'):raise APIError(404,'Không tìm thấy chức năng.')
            p=(ROOT/'static'/('index.html' if path=='/' else path.lstrip('/'))).resolve()
            require(p.is_relative_to((ROOT/'static').resolve()) and p.is_file(),'Không tìm thấy tệp.',404)
            return self.serve_file(p,E.mimetypes.guess_type(p.name)[0] or 'application/octet-stream')
        except APIError as e:self.reply(e.status,{'error':e.message})
        except (BrokenPipeError,ConnectionResetError):pass
        except Exception:
            import traceback;traceback.print_exc();self.reply(500,{'error':'Không thể tải dữ liệu. Xem Terminal để biết chi tiết.'})
    def do_POST(self):
        self.game_response=False
        try:
            require(self.headers.get('Content-Type','').split(';')[0]=='application/json','Yêu cầu JSON.',415)
            if self.headers.get('Origin'):require(urlparse(self.headers['Origin']).netloc==self.headers.get('Host'),'Nguồn thao tác không hợp lệ.')
            n=int(self.headers.get('Content-Length','0'));require(0<n<=MAX_BODY,'Dữ liệu quá lớn.',413)
            d=json.loads(self.rfile.read(n));require(isinstance(d,dict),'Dữ liệu không hợp lệ.',400)
            path=urlparse(self.path).path
            with db() as c:
                if path=='/api/login':
                    ip=self.client_address[0];fails=self.server.failures.setdefault(ip,[]);fails[:]=[x for x in fails if now()-x<300];require(len(fails)<12,'Thử quá nhiều lần. Chờ 5 phút rồi thử lại.',429)
                    username=text(d,'username',100).lower();u=one(c,'SELECT * FROM users WHERE lower(username)=? AND active=1',(username,))
                    # Legacy profiles may use a separate parent username; their original credentials remain valid.
                    if not u or not password_ok(text(d,'password',200),u['password']):fails.append(now());raise APIError(403,'Mã/tên đăng nhập hoặc mật khẩu chưa đúng.')
                    require(not one(c,'SELECT id FROM tenants WHERE id=? AND demo=1',(u['tenant'],)),'Dùng nút trải nghiệm để vào dữ liệu mẫu.')
                    cookie=self.login_session(c,u['id']);c.commit();return self.reply(value={'ok':True},cookie=cookie)
                if path=='/api/demo/start':
                    old=self.session(c)
                    if old and old['demo']:return self.reply(value={'ok':True})
                    require(one(c,'SELECT count(*) n FROM tenants WHERE demo=1')['n']<300,'Đã đầy không gian trải nghiệm. Liên hệ quản trị.',429)
                    ad=seed_demo(c);cookie=self.login_session(c,ad,True);c.commit();return self.reply(value={'ok':True},cookie=cookie)
                u=self.session(c);require(u,'Phiên đăng nhập hết hạn. Vui lòng đăng nhập lại.',401)
                require(hmac.compare_digest(self.headers.get('X-CSRF-Token',''),u['csrf']),'Phiên thao tác không hợp lệ. Hãy tải lại trang.')
                t=u['tenant']
                if path=='/api/logout':
                    c.execute('DELETE FROM sessions WHERE token=?',(u['token'],));c.commit();return self.reply(value={'ok':True},cookie='school_session=; HttpOnly; SameSite=Strict; Path=/; Max-Age=0')
                if path=='/api/demo/switch':
                    require(u['demo'],'Chỉ dùng cho khu giám khảo.')
                    role=text(d,'role',20);require(role in ['admin','teacher','parent'],'Vai trò không hợp lệ.',400)
                    targets=rows(c,"SELECT u.id,u.role,a.user_id admin_id FROM users u LEFT JOIN admins a ON u.id=a.user_id WHERE u.tenant=? AND u.active=1 ORDER BY u.rowid",(t,))
                    targets=[x for x in targets if ('admin' if x['admin_id'] else x['role'])==role and (not d.get('user_id') or x['id']==d['user_id'])];require(targets,'Chưa có tài khoản cho vai trò này.',400)
                    c.execute('UPDATE sessions SET user_id=? WHERE token=?',(targets[0]['id'],u['token']));c.commit();return self.reply(value={'ok':True})
                if path=='/api/password':
                    r=self.get_object(c,'users',u['id'],u);require(password_ok(text(d,'old',200),r['password']),'Mật khẩu hiện tại chưa đúng.',400)
                    p=text(d,'password',200,True);require(len(p)>=10,'Mật khẩu mới ít nhất 10 ký tự.',400)
                    c.execute('UPDATE users SET password=? WHERE id=?',(hash_password(p),u['id']));c.execute('DELETE FROM sessions WHERE user_id=? AND token<>?',(u['id'],u['token']));c.commit();return self.reply(value={'ok':True})
                if path=='/api/notifications/read':
                    c.execute('UPDATE notifications SET read_at=? WHERE user_id=?',(now(),u['id']));c.commit();return self.reply(value={'ok':True})
                if path in ['/api/messages','/api/messages/read']:
                    p=self.get_object(c,'users',text(d,'parent_id',100) if staff(u) else u['id'],u);require(p['role']=='parent' and p['active'],'Tài khoản phụ huynh không hoạt động.',400)
                    require(u['role']=='admin' or u['role']=='parent' or p['id'] in parent_ids(c,u))
                    if path.endswith('/read'):c.execute('UPDATE messages SET read_at=? WHERE tenant=? AND parent_id=? AND sender_id<>? AND read_at IS NULL',(now(),t,p['id'],u['id']))
                    else:
                        c.execute('INSERT INTO messages VALUES(?,?,?,?,?,NULL,?)',(uid(),t,p['id'],u['id'],text(d,'body',5000,True),now()))
                        recipients=[p['id']] if staff(u) else [x['id'] for x in c.execute("SELECT id FROM users WHERE tenant=? AND role='teacher' AND (id IN (SELECT user_id FROM admins) OR id IN (SELECT cl.teacher_id FROM classes cl JOIN students s ON s.class_id=cl.id WHERE s.parent_id=?))",(t,u['id']))]
                        notify(c,t,recipients,'Bạn có tin nhắn mới.','messages')
                    c.commit();return self.reply(value={'ok':True})
                if path=='/api/files':
                    result=self.upload_file(c,u,d);c.commit();return self.reply(value=result)
                if path=='/api/practice/start':
                    require(u['role']=='parent','Chức năng dành cho gia đình.')
                    r=self.get_object(c,'resources',text(d,'resource_id',100),u)
                    require(r['category'] in ['stories','music'] and r['type'] in ['audio','video'],'Chỉ tự luyện từ kho thơ truyện hoặc âm nhạc.',400)
                    s=self.authorized_student(c,text(d,'student_id',100),u)
                    existing=[a for a in rows(c,'SELECT * FROM assignments WHERE tenant=? AND resource_id=? AND class_id=? ORDER BY created DESC',(t,r['id'],s['class_id'])) if not a['student_id'] or a['student_id']==s['id']]
                    if existing:a=next((a for a in existing if a['origin']=='teacher'),existing[0])
                    else:
                        aid=uid()
                        c.execute('INSERT INTO assignments(id,tenant,class_id,resource_id,student_id,instructions,due,created,creator_id,batch_id,origin) VALUES(?,?,?,?,?,?,?,?,?,?,?)',(aid,t,s['class_id'],r['id'],s['id'],'Bài tự luyện do gia đình gửi từ kho thơ truyện hoặc âm nhạc.','',now(),u['id'],'','practice'))
                        a=self.get_object(c,'assignments',aid,u)
                    play,nonce=uid(),secrets.token_urlsafe(30)
                    c.execute('INSERT INTO plays VALUES(?,?,?,?,?,?,?,NULL)',(play,t,u['id'],a['id'],s['id'],nonce,now()))
                    c.commit();return self.reply(value={'play_id':play,'nonce':nonce,'started':now(),'assignment_id':a['id'],'origin':a['origin']})
                if path=='/api/plays/start':
                    require(u['role']=='parent','Giáo viên dùng nút Chơi thử.',400)
                    a=self.get_object(c,'assignments',text(d,'assignment_id',100),u);s=self.authorized_student(c,text(d,'student_id',100),u)
                    require(s['class_id']==a['class_id'] and (not a['student_id'] or a['student_id']==s['id']))
                    play,nonce=uid(),secrets.token_urlsafe(30);c.execute('INSERT INTO plays VALUES(?,?,?,?,?,?,?,NULL)',(play,t,u['id'],a['id'],s['id'],nonce,now()));c.commit();return self.reply(value={'play_id':play,'nonce':nonce,'started':now()})
                if path in ['/api/attempts','/api/external-result']:
                    require(u['role']=='parent','Hãy dùng vai phụ huynh để nộp bài.')
                    play=self.get_object(c,'plays',text(d,'play_id',100),u);require(play['user_id']==u['id'] and play['finished'] is None,'Lượt chơi đã nộp hoặc không thuộc tài khoản.',409)
                    a=self.get_object(c,'assignments',play['assignment_id'],u);s=self.authorized_student(c,play['student_id'],u);require(s['class_id']==a['class_id'] and (not a['student_id'] or s['id']==a['student_id']))
                    r=self.get_object(c,'resources',a['resource_id'],u);answers=d.get('answers',[]);require(isinstance(answers,list) and len(answers)<=30,'Đáp án không hợp lệ.',400)
                    score=total=None;source='native';trusted=1
                    if r['type']=='quiz':
                        qs=json.loads(r['questions']);require(len(answers)==len(qs) and all(isint(x) and 0<=x<len(qs[i]['options']) for i,x in enumerate(answers)),'Bé hoàn thành tất cả câu hỏi nhé.',400)
                        score=sum(v==q['answer'] for v,q in zip(answers,qs));total=len(qs)
                    elif r['type'] in ['link','html']:
                        require(path=='/api/external-result' and r['integration'],'Game này không hỗ trợ gửi điểm tự động.',400)
                        require(hmac.compare_digest(text(d,'nonce',100),play['nonce']),'Mã lượt chơi không hợp lệ.')
                        score,total=d.get('correct'),d.get('total');require(isint(score) and isint(total) and 0<=score<=total<=1000 and total>0,'Điểm game ngoài không hợp lệ.',400);source='external';trusted=0
                    else:require(path!='/api/external-result','Loại bài không phù hợp.',400)
                    response=text(d,'response',10000);fid=d.get('file_id') or None;recording_id=d.get('recording_id') or None
                    if fid:require(self.get_object(c,'files',fid,u)['uploaded_by']==u['id'],'Tệp không thuộc tài khoản này.')
                    if recording_id:
                        recording=self.get_object(c,'files',recording_id,u)
                        require(recording['uploaded_by']==u['id'],'Bản thu không thuộc tài khoản này.')
                        require(recording['mime'].startswith('audio/'),'Bản thu phải là tệp âm thanh.',400)
                    require(r['type'] in ['quiz','html','link'] or response or fid or recording_id,'Nhập câu trả lời, thu âm hoặc gửi tệp bài làm.',400)
                    id=uid();duration=max(0,min(now()-play['started'],86400))
                    c.execute('INSERT INTO attempts(id,tenant,assignment_id,student_id,answers,response,file_id,score,total,review,stars,reviewed,created,duration,source,trusted,play_id) VALUES(?,?,?,?,?,?,?,?,?,?,0,NULL,?,?,?,?,?)',(id,t,a['id'],s['id'],json.dumps(answers),response,fid,score,total,'',now(),duration,source,trusted,play['id']))
                    if recording_id:c.execute('UPDATE attempts SET recording_id=? WHERE id=?',(recording_id,id))
                    c.execute('UPDATE plays SET finished=? WHERE id=?',(now(),play['id']))
                    teachers=[x['id'] for x in c.execute("SELECT id FROM users WHERE tenant=? AND role='teacher' AND (id IN (SELECT user_id FROM admins) OR id=(SELECT teacher_id FROM classes WHERE id=?))",(t,s['class_id']))]
                    notify(c,t,teachers,s['name']+' vừa nộp bài.','results');c.commit();return self.reply(value={'id':id,'score':score,'total':total,'duration':duration,'trusted':trusted})
                require(staff(u),'Chức năng dành cho giáo viên hoặc admin.')
                if path=='/api/ai/generate':
                    require(not u['demo'],'Khu trải nghiệm không dùng khóa AI của trường. Dùng Nhập JSON để thử tạo game.',400)
                    cfg=read_ai_config();require(cfg.get('key') and cfg.get('url') and cfg.get('model'),'Admin cần cấu hình API AI trong Cài đặt. Có thể dùng tab Nhập JSON khi chưa có API.',400)
                    rate=self.server.ai_calls.setdefault(u['id'],[]);rate[:]=[v for v in rate if now()-v<3600];require(len(rate)<20,'Giới hạn 20 lần tạo AI mỗi giờ cho mỗi tài khoản.',429);rate.append(now())
                    topic=text(d,'topic',1500,True);count=d.get('count',5);require(isint(count) and 1<=count<=20,'Số câu từ 1–20.',400)
                    # Do not retain a database write transaction while waiting for the provider.
                    c.commit();draft=generate_ai(cfg,topic,text(d,'age',40) or '5–6 tuổi',count);return self.reply(value=draft)
                if path=='/api/ai/settings':
                    admin(u);require(not u['demo'],'Không thay cấu hình API thật trong khu trải nghiệm.')
                    cfg=read_ai_config();url=text(d,'url',500,True);validate_url(url)
                    model=text(d,'model',120,True);key=text(d,'key',500) or cfg.get('key','');require(key,'Nhập API key.',400)
                    (DATA_DIR/'ai_config.json').write_text(json.dumps({'url':url,'model':model,'key':key}),encoding='utf-8')
                    try:os.chmod(DATA_DIR/'ai_config.json',0o600)
                    except OSError:pass
                    return self.reply(value={'ok':True})
                if path=='/api/school':
                    admin(u);c.execute('UPDATE tenants SET name=? WHERE id=?',(text(d,'name',200,True),t));c.execute('UPDATE school_info SET address=?,phone=?,principal=? WHERE tenant=?',(text(d,'address',500),text(d,'phone',60),text(d,'principal',100),t));c.commit();return self.reply(value={'ok':True})
                if path=='/api/years':
                    admin(u);id=d.get('id') or uid()
                    if d.get('id'):
                        old_year=self.get_object(c,'school_years',id,u)
                        new_name=text(d,'name',40,True)
                        c.execute('UPDATE classes SET year=? WHERE tenant=? AND year=?',(new_name,t,old_year['name']))
                    active=int(bool(d.get('active',1)))
                    if active:c.execute('UPDATE school_years SET active=0 WHERE tenant=?',(t,))
                    c.execute('INSERT INTO school_years VALUES(?,?,?,?) ON CONFLICT(id) DO UPDATE SET name=excluded.name,active=excluded.active',(id,t,text(d,'name',40,True),active));c.commit();return self.reply(value={'id':id})
                if path=='/api/grades':
                    admin(u);id=d.get('id') or uid()
                    if d.get('id'):self.get_object(c,'grades',id,u)
                    c.execute('INSERT INTO grades VALUES(?,?,?,?) ON CONFLICT(id) DO UPDATE SET name=excluded.name,age=excluded.age',(id,t,text(d,'name',100,True),text(d,'age',40,True)));c.commit();return self.reply(value={'id':id})
                if path in ['/api/teachers','/api/teachers/reset','/api/teachers/status']:
                    admin(u);id=d.get('id') or uid()
                    if d.get('id'):
                        target=self.get_object(c,'users',id,u);require(target['role']=='teacher' and not one(c,'SELECT user_id FROM admins WHERE user_id=?',(id,)),'Không thay tài khoản admin bằng chức năng giáo viên.')
                    if path.endswith('/status'):
                        c.execute('UPDATE users SET active=? WHERE id=?',(int(bool(d.get('active'))),id));c.execute('DELETE FROM sessions WHERE user_id=?',(id,))
                    elif path.endswith('/reset'):
                        p=text(d,'password',200,True);require(len(p)>=10,'Mật khẩu giáo viên ít nhất 10 ký tự.',400);c.execute('UPDATE users SET password=? WHERE id=?',(hash_password(p),id));c.execute('DELETE FROM sessions WHERE user_id=?',(id,))
                    elif d.get('id'):c.execute('UPDATE users SET name=? WHERE id=?',(text(d,'name',100,True),id))
                    else:
                        username=text(d,'username',80,True).lower();require(re.fullmatch(r'[a-z0-9_.-]{3,60}',username),'Tên đăng nhập dùng chữ thường không dấu, số, . _ -',400)
                        p=text(d,'password',200,True);require(len(p)>=10,'Mật khẩu giáo viên ít nhất 10 ký tự.',400)
                        if u['demo']:username='demo_'+uid()+'_'+username
                        c.execute('INSERT INTO users VALUES(?,?,?,?,?,?,1)',(id,t,username,text(d,'name',100,True),'teacher',hash_password(p)))
                    c.commit();return self.reply(value={'id':id})
                if path=='/api/parents/reset':
                    admin(u);target=self.get_object(c,'users',text(d,'id',100),u);require(target['role']=='parent')
                    p=text(d,'password',200,True);require(len(p)>=4,'Mật khẩu ít nhất 4 ký tự.',400);c.execute('UPDATE users SET password=? WHERE id=?',(hash_password(p),target['id']));c.execute('DELETE FROM sessions WHERE user_id=?',(target['id'],));c.commit();return self.reply(value={'ok':True})
                if path=='/api/classes':
                    id=d.get('id') or uid()
                    if d.get('id'):self.authorized_class(c,id,u)
                    if u['role']=='teacher':teacher_id=u['id']
                    else:teacher_id=d.get('teacher_id') or None
                    if teacher_id:
                        target=self.get_object(c,'users',teacher_id,u);require(target['role']=='teacher' and target['active'],'Chọn giáo viên đang hoạt động.',400)
                    grade=self.get_object(c,'grades',text(d,'grade_id',100),u)
                    c.execute('INSERT INTO classes(id,tenant,name,age,year,created,grade_id,teacher_id) VALUES(?,?,?,?,?,?,?,?) ON CONFLICT(id) DO UPDATE SET name=excluded.name,age=excluded.age,year=excluded.year,grade_id=excluded.grade_id,teacher_id=excluded.teacher_id',(id,t,text(d,'name',100,True),grade['age'],text(d,'year',40,True),now(),grade['id'],teacher_id));c.commit();return self.reply(value={'id':id})
                if path=='/api/students':
                    admin(u);id=d.get('id') or uid();cl=self.get_object(c,'classes',text(d,'class_id',100),u);name=text(d,'name',100,True);credentials=None
                    if d.get('id'):
                        old=self.get_object(c,'students',id,u);parent=old['parent_id'];code=old['code']
                        if old['class_id']!=cl['id']:require(not one(c,'SELECT id FROM attempts WHERE student_id=?',(id,)),'Học sinh đã có bài làm, giữ nguyên lớp để bảo toàn lịch sử.',409)
                    else:
                        while True:
                            code='HS'+str(time.localtime().tm_year)+f'{secrets.randbelow(10**8):08d}'
                            if not one(c,'SELECT id FROM users WHERE lower(username)=?',(code.lower(),)):break
                        pin=code[-4:];parent=uid();c.execute('INSERT INTO users VALUES(?,?,?,?,?,?,1)',(parent,t,code,'Phụ huynh '+name,'parent',hash_password(pin)));credentials={'username':code,'password':pin}
                    c.execute('INSERT INTO students VALUES(?,?,?,?,?,?,?,?,?) ON CONFLICT(id) DO UPDATE SET name=excluded.name,class_id=excluded.class_id,birthday=excluded.birthday,note=excluded.note',(id,t,cl['id'],parent,name,code,text(d,'birthday',20),text(d,'note',1000),now()));c.commit();return self.reply(value={'id':id,'code':code,'credentials':credentials})
                if path=='/api/resources':
                    result=self.save_resource(c,u,d);c.commit();return self.reply(value=result)
                if path=='/api/assignments':
                    rid=text(d,'resource_id',100);r=self.get_object(c,'resources',rid,u);scope=text(d,'scope',20) or 'class';require(scope in ['class','school','student'],'Phạm vi giao bài không hợp lệ.',400)
                    sid=None
                    if scope=='school':admin(u);classes=rows(c,'SELECT * FROM classes WHERE tenant=?',(t,))
                    else:
                        if scope=='student':s=self.authorized_student(c,text(d,'student_id',100),u);sid=s['id'];cl=s['class_id']
                        else:cl=text(d,'class_id',100)
                        classes=[self.authorized_class(c,cl,u)]
                    require(classes,'Chưa có lớp để giao bài.',400);due=text(d,'due',20);require(not due or re.fullmatch(r'\d{4}-\d{2}-\d{2}',due),'Ngày không hợp lệ.',400)
                    batch=uid();ids=[]
                    for cl in classes:
                        id=uid();ids.append(id);c.execute('INSERT INTO assignments(id,tenant,class_id,resource_id,student_id,instructions,due,created,creator_id,batch_id) VALUES(?,?,?,?,?,?,?,?,?,?)',(id,t,cl['id'],rid,sid,text(d,'instructions',3000),due,now(),u['id'],batch))
                        recipients=[s['parent_id']] if sid else [x['parent_id'] for x in c.execute('SELECT DISTINCT parent_id FROM students WHERE class_id=?',(cl['id'],))]
                        notify(c,t,recipients,'Cô giao bài mới: '+r['title'],'assignments')
                    c.commit();return self.reply(value={'ids':ids,'id':ids[0]})
                if path=='/api/reviews':
                    a=self.get_object(c,'attempts',text(d,'id',100),u);s=self.authorized_student(c,a['student_id'],u);stars=d.get('stars',0);require(isint(stars) and 0<=stars<=5,'Số sao từ 0–5.',400)
                    trusted=1 if a['source']=='native' or d.get('accept_external') else a['trusted']
                    c.execute('UPDATE attempts SET review=?,stars=?,reviewed=?,trusted=? WHERE id=?',(text(d,'review',5000,True),stars,now(),trusted,a['id']));notify(c,t,[s['parent_id']],'Cô vừa nhận xét bài của '+s['name'],'results');c.commit();return self.reply(value={'ok':True})
                if path=='/api/class-reviews':
                    cl=self.authorized_class(c,text(d,'class_id',100),u);entries=d.get('entries',[]);require(isinstance(entries,list) and 0<len(entries)<=200,'Danh sách nhận xét không hợp lệ.',400)
                    count=0
                    for entry in entries:
                        s=self.authorized_student(c,text(entry,'student_id',100),u);require(s['class_id']==cl['id'],'Học sinh không thuộc lớp.',400);body=text(entry,'body',5000)
                        if body:c.execute('INSERT INTO class_reviews VALUES(?,?,?,?,?,?,?)',(uid(),t,cl['id'],s['id'],u['id'],body,now()));notify(c,t,[s['parent_id']],'Cô có nhận xét mới cho '+s['name'],'comments');count+=1
                    require(count>0,'Nhập ít nhất một nhận xét.',400);c.commit();return self.reply(value={'count':count})
                if path=='/api/news':
                    id=d.get('id') or uid();cl=d.get('class_id') or None
                    if d.get('id'):
                        old=self.get_object(c,'news',id,u);require(u['role']=='admin' or old['creator_id']==u['id'])
                    if cl:self.authorized_class(c,cl,u)
                    else:admin(u)
                    fid=d.get('file_id') or None
                    if fid:require(self.get_object(c,'files',fid,u)['mime'].startswith('image/'),'Thông báo chỉ đính kèm ảnh PNG/JPG.',400)
                    c.execute('INSERT INTO news(id,tenant,class_id,title,body,created,file_id,creator_id) VALUES(?,?,?,?,?,?,?,?) ON CONFLICT(id) DO UPDATE SET class_id=excluded.class_id,title=excluded.title,body=excluded.body,file_id=excluded.file_id',(id,t,cl,text(d,'title',180,True),text(d,'body',10000,True),now(),fid,u['id']))
                    notify(c,t,parent_ids(c,u,cl),'Thông báo: '+text(d,'title',180),'news');c.commit();return self.reply(value={'id':id})
                if path=='/api/delete':
                    table=text(d,'table',30);require(table in ['classes','students','resources','assignments','news','school_years','grades'],'Không thể xóa loại dữ liệu này.',400)
                    r=self.get_object(c,table,text(d,'id',100),u)
                    if table in ['students','school_years','grades']:admin(u)
                    elif table=='classes':self.authorized_class(c,r['id'],u)
                    elif table=='assignments':require(u['role']=='admin' or r['creator_id']==u['id'])
                    else:require(u['role']=='admin' or r['creator_id']==u['id'])
                    if table=='resources':require(not one(c,'SELECT id FROM assignments WHERE resource_id=?',(r['id'],)),'Học liệu đã giao, không thể xóa.',409)
                    if table=='school_years':require(not one(c,'SELECT id FROM classes WHERE tenant=? AND year=?',(t,r['name'])),'Năm học đang được lớp sử dụng.',409)
                    c.execute(f'DELETE FROM {table} WHERE id=?',(r['id'],));c.commit();return self.reply(value={'ok':True})
                raise APIError(404,'Không tìm thấy chức năng.')
        except APIError as e:self.reply(e.status,{'error':e.message})
        except sqlite3.IntegrityError as e:self.reply(409,{'error':'Dữ liệu đang liên kết với hồ sơ/bài làm, không thể xóa.' if 'FOREIGN KEY' in str(e) else 'Tên đăng nhập hoặc mã đã tồn tại.'})
        except (ValueError,TypeError,KeyError):self.reply(400,{'error':'Dữ liệu không hợp lệ. Kiểm tra các trường đã nhập.'})
        except (BrokenPipeError,ConnectionResetError):pass
        except Exception:
            import traceback;traceback.print_exc();self.reply(500,{'error':'Máy chủ gặp lỗi. Xem Terminal để biết chi tiết.'})
    def upload_file(self,c,u,d):
        name=Path(text(d,'name',180,True).replace('\\','/')).name;ext=Path(name).suffix.lower()
        types={'.txt':'text/plain; charset=utf-8','.mp3':'audio/mpeg','.mp4':'video/mp4','.png':'image/png','.jpg':'image/jpeg','.jpeg':'image/jpeg','.pdf':'application/pdf','.html':'text/html; charset=utf-8','.json':'application/json','.webm':'audio/webm','.ogg':'audio/ogg','.m4a':'audio/mp4','.wav':'audio/wav'}
        require(ext in types,'Hỗ trợ TXT, MP3, MP4, WebM/OGG/M4A/WAV, PNG, JPG, PDF, HTML hoặc JSON.',400)
        require(staff(u) or ext not in ['.html','.json'],'Chỉ giáo viên/admin tải game HTML/JSON.')
        try:raw=base64.b64decode(d.get('data',''),validate=True)
        except Exception:raise APIError(400,'Tệp không hợp lệ.')
        require(0<len(raw)<=MAX_FILE,'Mỗi tệp tối đa 25 MB.',413)
        require(one(c,'SELECT coalesce(sum(size),0) n FROM files WHERE tenant=?',(u['tenant'],))['n']+len(raw)<(100 if u['demo'] else 1000)*1024*1024,'Đã hết dung lượng tệp của không gian này.',413)
        if ext in ['.txt','.html','.json']:
            try:content=raw.decode('utf-8-sig')
            except UnicodeDecodeError:raise APIError(400,'Tệp văn bản cần dùng UTF-8.')
            require(b'\0' not in raw,'Văn bản không hợp lệ.',400)
            if ext=='.json':
                try:json.loads(content)
                except Exception:raise APIError(400,'JSON không hợp lệ.')
        elif ext=='.mp3':require(raw.startswith(b'ID3') or (len(raw)>1 and raw[0]==255 and raw[1]&224==224),'Tệp không đúng MP3.',400)
        elif ext=='.mp4':require(len(raw)>12 and raw[4:8]==b'ftyp','Tệp không đúng MP4.',400)
        elif ext=='.m4a':require(len(raw)>12 and raw[4:8]==b'ftyp','Bản thu M4A không hợp lệ.',400)
        elif ext=='.webm':require(raw.startswith(b'\x1a\x45\xdf\xa3'),'Bản thu WebM không hợp lệ.',400)
        elif ext=='.ogg':require(raw.startswith(b'OggS'),'Bản thu OGG không hợp lệ.',400)
        elif ext=='.wav':require(len(raw)>12 and raw.startswith(b'RIFF') and raw[8:12]==b'WAVE','Bản thu WAV không hợp lệ.',400)
        elif ext=='.png':require(raw.startswith(b'\x89PNG\r\n\x1a\n'),'Tệp không đúng PNG.',400)
        elif ext in ['.jpg','.jpeg']:require(raw.startswith(b'\xff\xd8\xff'),'Tệp không đúng JPG.',400)
        elif ext=='.pdf':require(raw.startswith(b'%PDF-'),'Tệp không đúng PDF.',400)
        fid=uid();disk=fid+ext;(DATA_DIR/'uploads'/disk).write_bytes(raw)
        c.execute('INSERT INTO files VALUES(?,?,?,?,?,?,?,?)',(fid,u['tenant'],name,types[ext],len(raw),disk,u['id'],now()))
        return {'id':fid,'name':name,'mime':types[ext],'size':len(raw)}
    def save_resource(self,c,u,d):
        id=d.get('id') or uid()
        theme=text(d,'theme',20) or 'auto'
        require(theme in ['auto','garden','ocean','music'],'Giao diện game không hợp lệ.',400)
        if d.get('id'):
            old=self.get_object(c,'resources',id,u);require(u['role']=='admin' or old['creator_id']==u['id'],'Chỉ sửa học liệu do mình tạo.')
            require(not one(c,'SELECT id FROM assignments WHERE resource_id=?',(id,)),'Bài đã giao: tạo bản mới để giữ lịch sử.',409)
        illustration=d.get('illustration_id') or None
        if illustration:
            image=self.get_object(c,'files',illustration,u)
            require(image['mime'] in ['image/png','image/jpeg'],'Ảnh minh họa cần là PNG hoặc JPG.',400)
            require(self.can_file(c,illustration,u),'Không có quyền dùng ảnh này.')
        kind=text(d,'type',20);category=text(d,'category',20) or 'games'
        require(kind in ['quiz','text','audio','video','link','html'],'Loại học liệu không hợp lệ.',400)
        require(category in ['games','stories','music'],'Kho lưu không hợp lệ.',400)
        require(category=='games' or kind in ['audio','video'],'Kho thơ truyện/âm nhạc dùng MP3 hoặc MP4.',400)
        qs=validate_questions(d.get('questions',[])) if kind=='quiz' else []
        fid=d.get('file_id') or None
        if fid:
            f=self.get_object(c,'files',fid,u)
            expected={'text':'text/plain','audio':'audio/mpeg','video':'video/mp4','html':'text/html'}
            require(kind in expected and f['mime'].startswith(expected[kind]),'Tệp không phù hợp loại học liệu.',400)
        require(kind not in ['audio','video','html'] or fid,'Chọn tệp học liệu.',400)
        body=text(d,'body',30000);require(kind!='text' or body or fid,'Nhập nội dung hoặc tải TXT.',400)
        url=text(d,'external_url',2000)
        if kind=='link':validate_url(url)
        integration=int(bool(d.get('integration'))) if kind in ['html','link'] else 0
        c.execute('INSERT INTO resources(id,tenant,title,type,description,body,file_id,questions,created,category,external_url,integration,creator_id) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?) ON CONFLICT(id) DO UPDATE SET title=excluded.title,type=excluded.type,description=excluded.description,body=excluded.body,file_id=excluded.file_id,questions=excluded.questions,category=excluded.category,external_url=excluded.external_url,integration=excluded.integration',(id,u['tenant'],text(d,'title',150,True),kind,text(d,'description',3000),body,fid,json.dumps(qs,ensure_ascii=False),now(),category,url,integration,u['id']))
        c.execute('UPDATE resources SET theme=?,illustration_id=? WHERE id=?',(theme,illustration,id))
        return {'id':id}

def validate_url(url):
    parsed=urlparse(url)
    require(parsed.scheme=='https' and parsed.hostname and not parsed.username and not parsed.password and parsed.port in [None,443],'Dùng URL HTTPS đầy đủ, không chứa mật khẩu hoặc cổng riêng.',400)
    host=parsed.hostname.lower();require(host not in ['localhost','localhost.localdomain'] and not host.endswith(('.local','.internal')),'Không dùng địa chỉ nội bộ.',400)
    import ipaddress
    try:require(ipaddress.ip_address(host).is_global,'Không dùng địa chỉ mạng nội bộ.',400)
    except ValueError:pass

def read_ai_config():
    cfg={}
    try:cfg=json.loads((DATA_DIR/'ai_config.json').read_text(encoding='utf-8'))
    except (OSError,ValueError):pass
    for key,var in [('url','AI_API_URL'),('key','AI_API_KEY'),('model','AI_MODEL')]:
        if os.environ.get(var):cfg[key]=os.environ[var]
    return cfg

def generate_ai(cfg,topic,age,count):
    validate_url(cfg['url'])
    prompt=f'Tạo {count} câu hỏi trò chơi cho trẻ mầm non {age}. Chủ đề: {topic}. Nội dung an toàn, ngắn, gần gũi. Mỗi câu có 3 lựa chọn. Trả về duy nhất JSON hợp lệ, không markdown, schema: {{"title":"Tên trò chơi", "description":"Giới thiệu", "questions":[{{"question":"Câu hỏi","options":["A","B","C"],"answer":0}}]}}. answer là vị trí đáp án đúng, bắt đầu từ 0. Không yêu cầu dữ liệu cá nhân trẻ.'
    payload=json.dumps({'model':cfg['model'],'messages':[{'role':'system','content':'Bạn là trợ lý biên soạn học liệu mầm non, chỉ trả JSON theo schema được yêu cầu.'},{'role':'user','content':prompt}]}).encode()
    request=urllib.request.Request(cfg['url'],data=payload,headers={'Content-Type':'application/json','Authorization':'Bearer '+cfg['key']})
    class NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self,*a,**k):return None
    try:
        with urllib.request.build_opener(NoRedirect).open(request,timeout=45) as response:
            raw=response.read(2*1024*1024+1);require(len(raw)<=2*1024*1024,'Phản hồi AI quá lớn.',502);result=json.loads(raw)
        content=result['choices'][0]['message']['content'].strip()
        if content.startswith('```'):content=re.sub(r'^```(?:json)?\s*|\s*```$','',content)
        result=json.loads(content);qs=validate_questions(result.get('questions'));return {'title':text(result,'title',150,True),'description':text(result,'description',3000),'questions':qs}
    except APIError:raise
    except urllib.error.HTTPError as e:raise APIError(502,'Nhà cung cấp AI báo lỗi '+str(e.code)+'. Kiểm tra endpoint, model, khóa và hạn mức trong Cài đặt.')
    except Exception:raise APIError(502,'Không nhận được bộ câu hỏi hợp lệ từ AI. Kiểm tra cấu hình hoặc dùng Nhập JSON.')

class SchoolServer(E.ThreadingHTTPServer):
    def __init__(self,address):super().__init__(address,App);self.failures={};self.ai_calls={}

if __name__=='__main__':
    initialize();host=os.environ.get('SCHOOL_HOST','127.0.0.1');port=int(os.environ.get('PORT','8000'))
    print(f'🌈 Học nào bé ơi! V4 → http://localhost:{port}\nDừng bằng Ctrl+C.',flush=True)
    if os.environ.get('SCHOOL_OPEN_BROWSER')=='1':
        import threading,webbrowser
        threading.Timer(1,lambda:webbrowser.open(f'http://localhost:{port}')).start()
    try:SchoolServer((host,port)).serve_forever()
    except KeyboardInterrupt:print('\nĐã dừng máy chủ.')
