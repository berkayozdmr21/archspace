import os,tempfile,unittest,copy
TEMP=tempfile.TemporaryDirectory(prefix='archspace-tests-');os.environ['ARCHSPACE_DATA_DIR']=TEMP.name
from fastapi.testclient import TestClient
from backend.main import app,database
HEAD={'X-Archspace-Client':'archspace'}
SCENE={'version':1,'room':{'width':6,'depth':5,'height':2.8,'wall':'#e7e3d8','floor':'oak','light':'day'},'items':[{'id':'sofa-1','type':'sofa','x':0,'z':0,'scale':1,'rotation':0,'color':'#b7b29d'}]}
class ArchTests(unittest.TestCase):
 def setUp(self):
  with database() as db:db.execute('DELETE FROM projects')
  self.c=TestClient(app);self.c.get('/api/session')
 def save(self):return self.c.post('/api/projects',json={'title':'Quiet room','scene':SCENE},headers=HEAD)
 def quote(self,d):return self.c.post('/api/estimate',json=d,headers=HEAD)
 def test_catalog(self):self.assertEqual(len(self.c.get('/api/catalog').json()),44)
 def test_estimate(self):self.assertEqual(self.quote(SCENE).json()['total'],24500)
 def test_room_limits(self):
  d=copy.deepcopy(SCENE);d['room']['width']=1;self.assertEqual(self.quote(d).status_code,422)
 def test_bounds(self):
  d=copy.deepcopy(SCENE);d['items'][0]['x']=10;self.assertEqual(self.quote(d).status_code,422)
 def test_rotated_bounds(self):
  d=copy.deepcopy(SCENE);d['items'][0].update(x=2,rotation=90);self.assertEqual(self.quote(d).status_code,200);d['items'][0]['rotation']=0;self.assertEqual(self.quote(d).status_code,422)
 def test_scale_limits(self):
  d=copy.deepcopy(SCENE);d['items'][0]['scale']=3;self.assertEqual(self.quote(d).status_code,422)
 def test_invalid_color(self):
  d=copy.deepcopy(SCENE);d['room']['wall']='red';self.assertEqual(self.quote(d).status_code,422)
 def test_duplicate_ids(self):
  d=copy.deepcopy(SCENE);d['items'].append(d['items'][0]);self.assertEqual(self.quote(d).status_code,422)
 def test_unknown_furniture(self):
  d=copy.deepcopy(SCENE);d['items'][0]['type']='fake';self.assertEqual(self.quote(d).status_code,422)
 def test_object_limit(self):
  d=copy.deepcopy(SCENE);d['items']=[dict(d['items'][0],id=str(i)) for i in range(41)];self.assertEqual(self.quote(d).status_code,422)
 def test_untrusted_price_rejected(self):
  d=copy.deepcopy(SCENE);d['total']=1;self.assertEqual(self.quote(d).status_code,422)
 def test_session_required(self):self.assertEqual(TestClient(app).post('/api/projects',json={'title':'Room','scene':SCENE},headers=HEAD).status_code,401)
 def test_cross_origin_blocked(self):self.assertEqual(self.c.post('/api/estimate',json=SCENE,headers={**HEAD,'Origin':'https://evil.example'}).status_code,403)
 def test_header_required(self):self.assertEqual(self.c.post('/api/estimate',json=SCENE).status_code,403)
 def test_save_public_read(self):
  saved=self.save();self.assertEqual(saved.status_code,201);shared=TestClient(app).get('/api/projects/'+saved.json()['id']).json();self.assertEqual(shared['scene'],SCENE);self.assertNotIn('owner',shared)
 def test_owner_isolation(self):
  key=self.save().json()['id'];other=TestClient(app);other.get('/api/session');self.assertEqual(other.get('/api/projects').json(),[]);self.assertEqual(other.delete('/api/projects/'+key,headers=HEAD).status_code,404)
 def test_delete_revokes_link(self):
  key=self.save().json()['id'];self.assertEqual(self.c.delete('/api/projects/'+key,headers=HEAD).status_code,204);self.assertEqual(self.c.get('/api/projects/'+key).status_code,404)
 def test_static_home(self):self.assertEqual(self.c.get('/').status_code,200)

 def home(self):
  d=copy.deepcopy(SCENE);d.update(layout='home',finishes={'bath':{'floor':'terrazzo','wall':'#e7e3d8'}});d['room'].update(width=12,depth=10);d['items'][0].update(x=-3,z=-3);return d
 def test_home_round_trip(self):
  d=self.home();r=self.c.post('/api/projects',json={'title':'Full home','scene':d},headers=HEAD);self.assertEqual(r.status_code,201);self.assertEqual(r.json()['scene'],d)
 def test_internal_wall_bounds(self):
  d=self.home();d['items'][0]['x']=-.1;self.assertEqual(self.quote(d).status_code,422)
 def test_home_limit(self):
  d=self.home();d['items']=[dict(d['items'][0],id=str(i)) for i in range(160)];self.assertEqual(self.quote(d).status_code,200);d['items'].append(dict(d['items'][0],id='extra'));self.assertEqual(self.quote(d).status_code,422)
 def test_unknown_room_finish(self):
  d=self.home();d['finishes']['attic']={'floor':'oak','wall':'#e7e3d8'};self.assertEqual(self.quote(d).status_code,422)
 def test_balcony_furniture(self):
  d=self.home();d['items'][0].update(type='bistro',x=5,z=3);self.assertEqual(self.quote(d).status_code,200)
