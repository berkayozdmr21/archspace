import json,os,re,math,sqlite3,secrets,uuid,time
from contextlib import contextmanager
from pathlib import Path
from typing import Literal,List
from urllib.parse import urlparse
from fastapi import FastAPI,Request,Response,HTTPException
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel,Field,ConfigDict,model_validator
ROOT=Path(os.path.abspath(__file__)).parents[1]
DATA=Path(os.getenv('ARCHSPACE_DATA_DIR',str(ROOT/'data')));DATA.mkdir(parents=True,exist_ok=True)
CATALOG=json.loads((ROOT/'frontend/catalog.json').read_text(encoding='utf-8'));BY_ID={x['id']:x for x in CATALOG}
ROOMS=json.loads((ROOT/'frontend/home.json').read_text(encoding='utf-8'))
class Strict(BaseModel):model_config=ConfigDict(extra='forbid',allow_inf_nan=False)
class Room(Strict):
 width:float=Field(ge=3,le=12)
 depth:float=Field(ge=3,le=12)
 height:float=Field(ge=2.4,le=4.2)
 wall:str=Field(pattern=r'^#[a-fA-F0-9]{6}$')
 floor:Literal['oak','walnut','concrete','terrazzo']
 light:Literal['day','golden','night']
class Item(Strict):
 id:str=Field(min_length=1,max_length=80)
 type:Literal['sofa','armchair','coffee','dining','chair','plant','lamp','rug','shelf','bed','desk','console','curtain','roundrug','runner','wardrobe','nightstand','dresser','tv','fridge','oven','sink','cabinet','island','stool','washer','vanity','toilet','shower','towel','outdoorchair','bistro','planter','sunlounger','pendant','tablelamp','mirror','art','bench','shoe','singlebed','officechair','bookcase','ottoman']
 x:float
 z:float
 rotation:float=Field(ge=-360,le=360)
 scale:float=Field(ge=.6,le=1.5)
 color:str=Field(pattern=r'^#[a-fA-F0-9]{6}$')
class Finish(Strict):
 floor:Literal['oak','walnut','concrete','terrazzo']
 wall:str=Field(pattern=r'^#[a-fA-F0-9]{6}$')
class Design(Strict):
 version:Literal[1]=1
 room:Room
 items:List[Item]=Field(max_length=160)
 layout:Literal['home']=None
 finishes:dict[str,Finish]=Field(default_factory=dict)
 @model_validator(mode='after')
 def placement(self):
  if self.layout=='home' and (self.room.width!=12 or self.room.depth!=10):raise ValueError('Ev planı 12 × 10 metredir.')
  if set(self.finishes)-{'living','kitchen','hall','bedroom','study','bath','balcony'}:raise ValueError('Bilinmeyen oda.')
  if not self.layout and len(self.items)>40:raise ValueError('En fazla 40 parça.')
  ids=set()
  for i in self.items:
   if i.id in ids:raise ValueError('Mobilya kimlikleri benzersiz olmalı.')
   ids.add(i.id);m=BY_ID[i.type];a=math.radians(i.rotation);c=abs(math.cos(a));s=abs(math.sin(a));w=(m['width']*c+m['depth']*s)*i.scale;d=(m['width']*s+m['depth']*c)*i.scale
   if abs(i.x)+w/2>self.room.width/2+.001 or abs(i.z)+d/2>self.room.depth/2+.001:raise ValueError('Mobilya oda sınırlarının dışında.')
   if self.layout=='home':
    zone=next((r for r in ROOMS if abs(i.x-r['x'])<=r['width']/2+.001 and abs(i.z-r['z'])<=r['depth']/2+.001),None)
    if not zone or abs(i.x-zone['x'])+w/2>zone['width']/2+.001 or abs(i.z-zone['z'])+d/2>zone['depth']/2+.001:raise ValueError('Mobilya oda duvarını aşıyor.')
  return self
class Project(Strict):
 title:str=Field(min_length=1,max_length=70)
 scene:Design
def estimate(scene):return {'total':sum(BY_ID[i.type]['price'] for i in scene.items),'currency':'TRY','demo':True,'items':len(scene.items)}
@contextmanager
def database():
 db=sqlite3.connect(DATA/'projects.sqlite3',timeout=20);db.row_factory=sqlite3.Row
 try:
  with db:yield db
 finally:db.close()
with database() as db:db.execute('CREATE TABLE IF NOT EXISTS projects(id TEXT PRIMARY KEY,owner TEXT,title TEXT,scene TEXT,created REAL)')
app=FastAPI(title='ArchSpace API',version='1.0.0');COOKIE='archspace_owner'
def owner(request):
 token=request.cookies.get(COOKIE,'')
 if not re.fullmatch('[a-f0-9]{64}',token):raise HTTPException(401,'Oturum başlatılmalı.')
 return token
@app.middleware('http')
async def protect(request,call_next):
 if request.method in ['POST','PUT','PATCH','DELETE'] and request.url.path.startswith('/api/'):
  origin=request.headers.get('origin')
  if request.headers.get('x-archspace-client')!='archspace' or (origin and urlparse(origin).netloc!=request.headers.get('host')):return JSONResponse({'detail':'Yazma isteği engellendi.'},status_code=403)
 return await call_next(request)
@app.get('/api/health')
def health():return {'status':'ok'}
@app.get('/api/catalog')
def catalog():return CATALOG
@app.get('/api/session')
def session(request:Request,response:Response):
 if not re.fullmatch('[a-f0-9]{64}',request.cookies.get(COOKIE,'')):response.set_cookie(COOKIE,secrets.token_hex(32),httponly=True,samesite='lax',secure=request.url.scheme=='https',max_age=31536000)
 response.headers['Cache-Control']='no-store';return {'status':'ready'}
@app.post('/api/estimate')
def quote(body:Design):return estimate(body)
def serialize(row):
 scene=json.loads(row['scene']);return {'id':row['id'],'title':row['title'],'scene':scene,'quote':estimate(Design(**scene)),'created_at':row['created']}
@app.get('/api/projects')
def projects(request:Request):
 with database() as db:rows=db.execute('SELECT * FROM projects WHERE owner=? ORDER BY created DESC',(owner(request),)).fetchall()
 return [serialize(row) for row in rows]
@app.post('/api/projects',status_code=201)
def save(body:Project,request:Request):
 token=owner(request);title=body.title.strip()
 if not title:raise HTTPException(422,'Proje adı boş olamaz.')
 key=uuid.uuid4().hex
 with database() as db:
  if db.execute('SELECT COUNT(*) FROM projects WHERE owner=?',(token,)).fetchone()[0]>=100:raise HTTPException(409,'En fazla 100 proje saklanabilir.')
  db.execute('INSERT INTO projects VALUES(?,?,?,?,?)',(key,token,title,json.dumps(body.scene.model_dump(exclude_unset=True)),time.time()));row=db.execute('SELECT * FROM projects WHERE id=?',(key,)).fetchone()
 return serialize(row)
@app.get('/api/projects/{key}')
def shared(key:str):
 with database() as db:row=db.execute('SELECT * FROM projects WHERE id=?',(key,)).fetchone()
 if not row:raise HTTPException(404,'Proje bulunamadı.')
 return serialize(row)
@app.delete('/api/projects/{key}',status_code=204)
def delete(key:str,request:Request):
 with database() as db:changed=db.execute('DELETE FROM projects WHERE id=? AND owner=?',(key,owner(request))).rowcount
 if not changed:raise HTTPException(404,'Proje bulunamadı.')
if (ROOT/'frontend/dist').exists():app.mount('/',StaticFiles(directory=ROOT/'frontend/dist',html=True),name='web')
