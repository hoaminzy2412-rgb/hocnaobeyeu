import base64, http.cookiejar, json, os, sqlite3, sys, tempfile, threading, unittest, urllib.error, urllib.request
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).parents[1]))
import server as app
class Client:
    def __init__(self,base):self.base=base;self.csrf='';self.http=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
    def call(self,path,d=None,csrf=True):
        h={'Content-Type':'application/json'}
        if csrf:h['X-CSRF-Token']=self.csrf
        with self.http.open(urllib.request.Request(self.base+'/api/'+path,data=json.dumps(d).encode() if d is not None else None,headers=h)) as r:v=json.load(r)
        if path=='bootstrap':self.csrf=v['csrf']
        return v
    def login(self,username,password):self.call('login',{'username':username,'password':password});return self.call('bootstrap')
class V3Tests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();app.DATA_DIR=Path(self.temp.name);os.environ['SCHOOL_TEACHER_PASSWORD']='Teacher-test-123';app.initialize();self.srv=app.SchoolServer(('127.0.0.1',0));self.base='http://127.0.0.1:'+str(self.srv.server_port);threading.Thread(target=self.srv.serve_forever,daemon=True).start();self.a=Client(self.base);self.initial=self.a.login('cohoa','Teacher-test-123')
    def tearDown(self):self.srv.shutdown();self.srv.server_close();self.temp.cleanup()
    def deny(self,status,fn):
        with self.assertRaises(urllib.error.HTTPError) as e:fn()
        self.assertEqual(e.exception.code,status);e.exception.close()
    def fixture(self):
        teacher=self.a.call('teachers',{'username':'comai','name':'Cô Mai','password':'Teacher-Mai-123'})['id']
        other=self.a.call('teachers',{'username':'colan','name':'Cô Lan','password':'Teacher-Lan-123'})['id']
        grade=self.initial['grades'][0]['id'];cls=self.a.call('classes',{'name':'A4','year':'2026–2027','grade_id':grade,'teacher_id':teacher})['id'];cls2=self.a.call('classes',{'name':'A5','year':'2026–2027','grade_id':grade,'teacher_id':other})['id']
        s=self.a.call('students',{'name':'Bé An','class_id':cls});s2=self.a.call('students',{'name':'Bé Bình','class_id':cls2})
        p,q=Client(self.base),Client(self.base);p.login(s['credentials']['username'],s['credentials']['password']);q.login(s2['credentials']['username'],s2['credentials']['password']);t=Client(self.base);t.login('comai','Teacher-Mai-123')
        r=t.call('resources',{'title':'Bé chọn chữ','type':'quiz','category':'games','questions':[{'question':'Chữ a đâu?','options':['a','b','c'],'answer':0},{'question':'2+1?','options':['3','2','4'],'answer':0}]})['id']
        return {'teacher':teacher,'other':other,'cls':cls,'cls2':cls2,'s':s,'s2':s2,'p':p,'q':q,'t':t,'r':r}
    def test_admin_teacher_and_auto_pin(self):
        self.assertEqual(self.initial['user']['role'],'admin');self.assertEqual(len(self.initial['grades']),4)
        f=self.fixture();bs=f['t'].call('bootstrap');self.assertEqual([c['id'] for c in bs['classes']],[f['cls']]);self.assertEqual(len(bs['students']),1)
        s=f['s'];self.assertTrue(s['code'].startswith('HS'));self.assertEqual(s['credentials']['password'],s['code'][-4:]);self.assertEqual(f['p'].call('bootstrap')['students'][0]['id'],s['id'])
        self.deny(403,lambda:f['t'].call('teachers',{'name':'hack'}));self.deny(403,lambda:f['t'].call('students',{'name':'hack'}));self.deny(403,lambda:f['t'].call('classes',{'id':f['cls2'],'name':'hack'}))
        self.deny(403,lambda:f['p'].call('classes',{'name':'hack'}));self.deny(403,lambda:f['p'].call('messages',{'body':'CSRF'},csrf=False))
        self.a.call('teachers/status',{'id':f['teacher'],'active':False});self.deny(401,lambda:f['t'].call('bootstrap'))
    def test_school_assignments_native_results_and_comments(self):
        f=self.fixture();res=self.a.call('assignments',{'scope':'school','resource_id':f['r']});self.assertEqual(len(res['ids']),2)
        bp=f['p'].call('bootstrap');bq=f['q'].call('bootstrap');self.assertEqual(len(bp['assignments']),1);self.assertEqual(len(bq['assignments']),1);self.assertNotIn('answer',bp['resources'][0]['questions'][0])
        a=bp['assignments'][0]['id'];play=f['p'].call('plays/start',{'assignment_id':a,'student_id':f['s']['id']});r=f['p'].call('attempts',{'play_id':play['play_id'],'answers':[0,0],'score':999});self.assertEqual(r['score'],2)
        self.deny(409,lambda:f['p'].call('attempts',{'play_id':play['play_id'],'answers':[0,0]}));self.deny(403,lambda:f['q'].call('plays/start',{'assignment_id':a,'student_id':f['s']['id']}))
        play=f['p'].call('plays/start',{'assignment_id':a,'student_id':f['s']['id']});f['p'].call('attempts',{'play_id':play['play_id'],'answers':[0,1]})
        ranks=self.a.call('bootstrap')['rankings'];row=next(x for x in ranks if x['student_id']==f['s']['id']);self.assertEqual(row['completed'],1);self.assertEqual(row['correct'],2)
        f['t'].call('reviews',{'id':r['id'],'review':'Con cố gắng lắm!','stars':5});f['t'].call('class-reviews',{'class_id':f['cls'],'entries':[{'student_id':f['s']['id'],'body':'Bé mạnh dạn hơn mỗi ngày.'}]})
        self.assertEqual(len(f['p'].call('bootstrap')['class_reviews']),1);self.assertEqual(f['q'].call('bootstrap')['class_reviews'],[])
        f['p'].call('messages',{'body':'Chào cô'});f['t'].call('messages',{'parent_id':bp['students'][0]['parent_id'],'body':'Chào gia đình'});self.assertEqual(len(f['q'].call('bootstrap')['messages']),0);self.assertEqual(len(f['p'].call('bootstrap')['messages']),2)
        self.deny(409,lambda:self.a.call('delete',{'table':'assignments','id':a}));self.deny(409,lambda:self.a.call('resources',{'id':f['r'],'title':'Changed'}))
    def test_teacher_illustration_permissions_and_replacement(self):
        f=self.fixture();t=f['t']
        image=t.call('files',{'name':'minh-hoa.png','data':base64.b64encode(b'\x89PNG\r\n\x1a\n'+b'image').decode()})['id']
        payload={'title':'Game có ảnh','type':'quiz','category':'games','questions':[{'question':'Bé chọn nhé','options':['A','B'],'answer':0}],'illustration_id':image}
        rid=t.call('resources',payload)['id']
        self.deny(403,lambda:f['p'].http.open(self.base+'/api/files/'+image))
        self.a.call('assignments',{'scope':'student','student_id':f['s']['id'],'resource_id':rid})
        b=f['p'].call('bootstrap');self.assertEqual(next(r for r in b['resources'] if r['id']==rid)['illustration_id'],image)
        self.assertIn(image,[x['id'] for x in b['files']])
        with f['p'].http.open(self.base+'/api/files/'+image) as response:self.assertEqual(response.status,200)
        self.deny(403,lambda:f['q'].http.open(self.base+'/api/files/'+image))
        mp3=t.call('files',{'name':'nhac.mp3','data':base64.b64encode(b'ID3'+b'0'*20).decode()})['id']
        for category in ['music','stories']:
            data={'title':'Thơ nhạc có ảnh','type':'audio','category':category,'file_id':mp3,'illustration_id':image}
            resource=t.call('resources',data)['id']
            self.assertEqual(next(r for r in f['q'].call('bootstrap')['resources'] if r['id']==resource)['illustration_id'],image)
            t.call('resources',{**data,'id':resource,'illustration_id':None})
            self.assertIsNone(next(r for r in t.call('bootstrap')['resources'] if r['id']==resource)['illustration_id'])
        self.deny(400,lambda:t.call('resources',{**payload,'illustration_id':mp3}))
        self.deny(403,lambda:f['p'].call('resources',payload))

    def test_files_media_and_image_news(self):
        f=self.fixture()
        for ext,raw,kind in [('txt','Đếm cùng bé'.encode(),'text'),('mp3',b'ID3'+b'\0'*80,'audio'),('mp4',b'\0\0\0\x18ftypisom'+b'\0'*30,'video')]:
            fid=self.a.call('files',{'name':'bai.'+ext,'data':base64.b64encode(raw).decode()})['id'];rid=self.a.call('resources',{'title':'Bài '+ext,'type':kind,'category':'stories' if kind in ['audio','video'] else 'games','file_id':fid})['id']
            aid=self.a.call('assignments',{'scope':'student','student_id':f['s']['id'],'resource_id':rid})['id']
            with f['p'].http.open(urllib.request.Request(self.base+'/api/files/'+fid,headers={'Range':'bytes=0-5'})) as response:self.assertEqual(response.status,206);self.assertEqual(len(response.read()),6)
            if kind=='text':self.deny(403,lambda:f['q'].http.open(self.base+'/api/files/'+fid))
            play=f['p'].call('plays/start',{'assignment_id':aid,'student_id':f['s']['id']});f['p'].call('attempts',{'play_id':play['play_id'],'response':'Con đã học xong'})
        png=base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+aD1sAAAAASUVORK5CYII=');image=self.a.call('files',{'name':'thongbao.png','data':base64.b64encode(png).decode()})['id']
        self.a.call('news',{'title':'Thông báo nhà trường','body':'Cùng bé đến lớp','file_id':image})
        self.assertEqual(f['p'].call('bootstrap')['news'][0]['file_id'],image)
        with f['p'].http.open(self.base+'/api/files/'+image) as rr:self.assertEqual(rr.status,200)
        self.deny(403,lambda:f['t'].call('news',{'title':'X','body':'X'}));self.deny(400,lambda:self.a.call('files',{'name':'bad.mp4','data':base64.b64encode(b'wrong').decode()}))
    def test_external_game_protocol_and_privacy(self):
        f=self.fixture();html=b'<!doctype html><script>parent.postMessage({type:"hocnaobeoi:ready"},"*")</script>'
        fid=self.a.call('files',{'name':'game.html','data':base64.b64encode(html).decode()})['id'];rid=self.a.call('resources',{'title':'Game ngoài','type':'html','category':'games','file_id':fid,'integration':True})['id'];aid=self.a.call('assignments',{'scope':'student','student_id':f['s']['id'],'resource_id':rid})['id']
        with f['p'].http.open(self.base+'/api/game/'+fid) as rr:self.assertIn('sandbox allow-scripts',rr.headers['Content-Security-Policy']);self.assertNotIn('allow-same-origin',rr.headers['Content-Security-Policy'])
        with f['p'].http.open(self.base+'/api/files/'+fid) as rr:self.assertTrue(rr.headers['Content-Disposition'].startswith('attachment'))
        self.deny(403,lambda:f['q'].http.open(self.base+'/api/game/'+fid))
        p=f['p'].call('plays/start',{'assignment_id':aid,'student_id':f['s']['id']});self.deny(403,lambda:f['p'].call('external-result',{'play_id':p['play_id'],'nonce':'fake','correct':2,'total':3}))
        r=f['p'].call('external-result',{'play_id':p['play_id'],'nonce':p['nonce'],'correct':2,'total':3});self.assertEqual(r['trusted'],0);self.assertEqual(next(x for x in self.a.call('bootstrap')['rankings'] if x['student_id']==f['s']['id'])['completed'],0)
        f['t'].call('reviews',{'id':r['id'],'review':'Đã kiểm tra kết quả','stars':4,'accept_external':True});self.assertEqual(next(x for x in self.a.call('bootstrap')['rankings'] if x['student_id']==f['s']['id'])['correct'],2)
        self.assertTrue(all(not row['student_id'] for row in f['q'].call('bootstrap')['rankings'] if not row['mine']))
    def test_demo_and_ai_configuration(self):
        d,e=Client(self.base),Client(self.base);d.call('demo/start',{});bs=d.call('bootstrap');e.call('demo/start',{});be=e.call('bootstrap');self.assertEqual(bs['user']['role'],'admin');self.assertNotEqual(bs['classes'][0]['id'],be['classes'][0]['id'])
        for role in ['teacher','parent','admin']:d.call('demo/switch',{'role':role});self.assertEqual(d.call('bootstrap')['user']['role'],role)
        self.deny(403,lambda:d.call('ai/settings',{'url':'https://example.com/v1/chat/completions','key':'secret','model':'test'}))
        self.a.call('ai/settings',{'url':'https://example.com/v1/chat/completions','key':'test-key-not-real','model':'test-model'})
        bs=self.a.call('bootstrap');self.assertTrue(bs['ai']['configured']);self.assertNotIn('key',bs['ai'])
        with patch.object(app,'generate_ai',return_value={'title':'Bé đếm','description':'Nháp','questions':[{'question':'Có mấy quả?','options':['1','2','3'],'answer':0}]}):self.assertEqual(self.a.call('ai/generate',{'topic':'Đếm quả','count':1})['title'],'Bé đếm')
    def test_voice_submission_and_file_isolation(self):
        f=self.fixture()
        fid=self.a.call('files',{'name':'bai-mau.mp4','data':base64.b64encode(b'\0\0\0\x18ftypisom'+b'\0'*30).decode()})['id']
        r=self.a.call('resources',{'title':'Bé hát lại','type':'video','category':'music','theme':'music','file_id':fid})['id']
        a=self.a.call('assignments',{'scope':'student','student_id':f['s']['id'],'resource_id':r})['id']
        recorded=f['p'].call('files',{'name':'bai-thu.webm','data':base64.b64encode(b'\x1a\x45\xdf\xa3'+b'voice data').decode()})['id']
        extra=f['p'].call('files',{'name':'loi-chia-se.txt','data':base64.b64encode('Con rất thích hát'.encode()).decode()})['id']
        play=f['p'].call('plays/start',{'assignment_id':a,'student_id':f['s']['id']})
        result=f['p'].call('attempts',{'play_id':play['play_id'],'recording_id':recorded,'file_id':extra})
        out=f['p'].call('bootstrap');attempt=next(x for x in out['attempts'] if x['id']==result['id']);self.assertEqual(attempt['recording_id'],recorded);self.assertEqual(attempt['file_id'],extra)
        self.assertTrue(any(x['id']==recorded for x in out['files']))
        with f['t'].http.open(self.base+'/api/files/'+recorded) as response:self.assertEqual(response.headers['Content-Type'],'audio/webm')
        self.deny(403,lambda:f['q'].http.open(self.base+'/api/files/'+recorded))
        a2=self.a.call('assignments',{'scope':'student','student_id':f['s2']['id'],'resource_id':r})['id'];qplay=f['q'].call('plays/start',{'assignment_id':a2,'student_id':f['s2']['id']})
        self.deny(403,lambda:f['q'].call('attempts',{'play_id':qplay['play_id'],'recording_id':recorded}))
        self.deny(400,lambda:f['p'].call('files',{'name':'bad.webm','data':base64.b64encode(b'not audio').decode()}))
    def test_practice_recordings_and_3d_themes(self):
        f=self.fixture()
        mp3=self.a.call('files',{'name':'tho.mp3','data':base64.b64encode(b'ID3'+b'\0'*20).decode()})['id']
        rid=self.a.call('resources',{'title':'Bé đọc thơ','type':'audio','category':'stories','file_id':mp3,'theme':'garden'})['id']
        self.assertEqual(next(r for r in self.a.call('bootstrap')['resources'] if r['id']==rid)['theme'],'garden')
        self.deny(400,lambda:self.a.call('resources',{'title':'Sai','type':'audio','category':'stories','file_id':mp3,'theme':'unknown'}))
        for name,raw,mime in [('voice.m4a',b'\0\0\0\x18ftypM4A '+b'\0'*20,'audio/mp4'),('voice.ogg',b'OggS'+b'\0'*20,'audio/ogg'),('voice.wav',b'RIFF'+b'\0'*4+b'WAVE'+b'\0'*20,'audio/wav')]:
            file=f['p'].call('files',{'name':name,'data':base64.b64encode(raw).decode()});self.assertEqual(file['mime'],mime)
            play=f['p'].call('practice/start',{'resource_id':rid,'student_id':f['s']['id']});self.assertEqual(play['origin'],'practice')
            f['p'].call('attempts',{'play_id':play['play_id'],'recording_id':file['id']})
        b=self.a.call('bootstrap');self.assertEqual(len([a for a in b['assignments'] if a['origin']=='practice']),1)
        self.assertEqual(next(r for r in b['rankings'] if r['student_id']==f['s']['id'])['completed'],0)
        self.assertEqual(len(f['t'].call('bootstrap')['attempts']),3)
        self.deny(400,lambda:f['p'].call('practice/start',{'resource_id':f['r'],'student_id':f['s']['id']}))
        self.deny(403,lambda:f['q'].call('practice/start',{'resource_id':rid,'student_id':f['s']['id']}))
        # Once a teacher assigns the lesson, direct practice reuses that assigned task.
        assigned=self.a.call('assignments',{'scope':'class','class_id':f['cls'],'resource_id':rid})['id']
        play=f['p'].call('practice/start',{'resource_id':rid,'student_id':f['s']['id']});self.assertEqual(play['assignment_id'],assigned);self.assertEqual(play['origin'],'teacher')
        f['p'].call('attempts',{'play_id':play['play_id'],'response':'Đã hoàn thành bài cô giao'})
        self.assertEqual(next(r for r in self.a.call('bootstrap')['rankings'] if r['student_id']==f['s']['id'])['completed'],1)
    def test_v2_migration_keeps_password_and_profiles(self):
        original=app.DATA_DIR
        with tempfile.TemporaryDirectory() as legacy_dir:
            app.DATA_DIR=Path(legacy_dir);app.E.DATA_DIR=app.DATA_DIR
            try:
                app.E.initialize()
                with app.db() as c:
                    tenant=c.execute('SELECT id FROM tenants WHERE demo=0').fetchone()[0]
                    c.execute('INSERT INTO users VALUES(?,?,?,?,?,?,1)',('old_parent',tenant,'me_cu','Mẹ bé cũ','parent',app.hash_password('Old-parent-123')))
                    c.execute('INSERT INTO classes VALUES(?,?,?,?,?,?)',('old_class',tenant,'Lớp cũ','3–4 tuổi','2025–2026',app.now()))
                    c.execute('INSERT INTO students VALUES(?,?,?,?,?,?,?,?,?)',('old_student',tenant,'old_class','old_parent','Bé cũ','OLD1234','','',app.now()))
                app.initialize()
                with app.db() as c:
                    self.assertTrue(app.password_ok('Old-parent-123',c.execute("SELECT password FROM users WHERE id='old_parent'").fetchone()[0]))
                    row=c.execute("SELECT c.name,c.grade_id,g.name grade_name FROM classes c JOIN grades g ON c.grade_id=g.id WHERE c.id='old_class'").fetchone()
                    self.assertEqual(row['grade_name'],'Mẫu giáo bé')
                    self.assertEqual(c.execute("SELECT code FROM students WHERE id='old_student'").fetchone()[0],'OLD1234')
                    self.assertTrue(c.execute("SELECT id FROM school_years WHERE name='2025–2026'").fetchone())
                    self.assertEqual(c.execute('SELECT count(*) FROM admins').fetchone()[0],1)
            finally:app.DATA_DIR=original;app.E.DATA_DIR=original
        after=self.a.login('cohoa','Teacher-test-123');self.assertEqual(after['user']['role'],'admin')
if __name__=='__main__':unittest.main()
