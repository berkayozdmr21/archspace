import ROOMS from '../home.json';
import CATALOG from '../catalog.json';
export {CATALOG};
export const FLOORS=[{id:'oak',name:'Natural Oak',color:'#b99b76'},{id:'walnut',name:'Smoked Walnut',color:'#75604a'},{id:'concrete',name:'Soft Concrete',color:'#b4b2a9'},{id:'terrazzo',name:'Warm Terrazzo',color:'#ccc5b5'}];
export const WALLS=['#e7e3d8','#bfc2b1','#c2b09a','#89968a','#d8d0c2','#f1efea'];
export const COLORS=['#b7b29d','#817f65','#b78769','#d8d0be','#444e49','#b5bfc0','#9b765d','#c0a37b'];
export const model=id=>CATALOG.find(x=>x.id===id);
export const clone=x=>JSON.parse(JSON.stringify(x));
export const newId=()=>crypto.randomUUID();
const make=(id,type,x,z,rotation=0)=>({id,type,x,z,rotation,scale:1,color:model(type).color});
export {ROOMS};
export const zoneAt=(x,z)=>ROOMS.find(r=>Math.abs(x-r.x)<=r.width/2+.001&&Math.abs(z-r.z)<=r.depth/2+.001);
export function housePlace(item,doc,x=item.x,z=item.z,snap=false,zone){
 if(doc.layout!=='home')return place(item,doc.room,x,z,snap);
 const r=ROOMS.find(r=>r.id===zone)||zoneAt(x,z)||zoneAt(item.x,item.z)||ROOMS[0];
 const p=place(item,r,x-r.x,z-r.z,snap);return {...p,x:p.x+r.x,z:p.z+r.z};
}
export function preset(name='Nordic'){
 const room={width:12,depth:10,height:2.8,wall:name==='Japandi'?'#c2b09a':name==='Gallery'?'#f1efea':'#e7e3d8',floor:name==='Japandi'?'walnut':'oak',light:name==='Japandi'?'golden':'day'};
 const list=[['sofa',-3,-4],['rug',-3,-2.4],['coffee',-3,-2.4],['armchair',-1.1,-2.8, -30],['tv',-5.7,-2.4,90],['dining',-3,-.05],['chair',-4.15,-.05,90],['chair',-1.85,-.05,-90],['plant',-5.4,-4.4],['lamp',-1,-4.3],['curtain',-3,-4.8],['fridge',5.45,-4.45],['oven',4.65,-4.55],['sink',3.5,-4.55],['cabinet',2.35,-4.55],['island',2.7,-2.4],['stool',2.2,-1.65],['stool',3.2,-1.65],['curtain',1.5,-4.8],['runner',3,0,90],['bench',1.3,0],['shoe',5.4,0],['mirror',4.5,-.7],['bed',-4.3,3],['nightstand',-5.55,2.3],['tablelamp',-5.55,2.3],['wardrobe',-3,4.65],['roundrug',-3,2.1],['curtain',-4,4.8],['singlebed',-1.25,3.5],['desk',.7,4.5],['officechair',.7,3.5],['bookcase',1.7,2,90],['art',.4,1.4],['runner',0,3],['shower',3.45,4.45],['toilet',2.5,4.45],['vanity',3.7,2.7,90],['washer',2.5,1.5],['towel',3.5,1.3],['bistro',5,2.4],['outdoorchair',5,3.25],['outdoorchair',5,1.6,180],['planter',5,4.6],['plant',4.5,4.3]];
 const d={version:1,layout:'home',finishes:name==='Nordic'?{}:Object.fromEntries(ROOMS.filter(r=>!['bath','balcony','kitchen'].includes(r.id)).map(r=>[r.id,{floor:room.floor,wall:room.wall}])),room,items:[]};const counts={};d.items=list.map(([type,x,z,rotation=0])=>housePlace(make(type+'-'+(counts[type]=(counts[type]||0)+1),type,x,z,rotation),d));return d;
}
export function upgradeHome(doc){if(!doc||doc.layout==='home')return doc||preset();const d=preset();d.items=d.items.filter(i=>zoneAt(i.x,i.z)?.id!=='living');for(const i of doc.items){try{d.items.push(housePlace({...i,id:'legacy-'+newId()},d,i.x-3,i.z-2,false,'living'));}catch{}}return d;}
export function extent(item){const m=model(item.type),a=item.rotation*Math.PI/180,c=Math.abs(Math.cos(a)),s=Math.abs(Math.sin(a));return {w:(m.width*c+m.depth*s)*item.scale,d:(m.width*s+m.depth*c)*item.scale};}
export function place(item,room,x=item.x,z=item.z,snap=false){const e=extent(item);if(e.w>room.width-.04||e.d>room.depth-.04)throw Error('Bu boyuttaki mobilya odaya sığmıyor. Ölçeği veya oda ölçüsünü değiştir.');const quant=v=>snap?Math.round(v*4)/4:v;return {...item,x:Math.max(-room.width/2+e.w/2+.02,Math.min(room.width/2-e.w/2-.02,quant(x))),z:Math.max(-room.depth/2+e.d/2+.02,Math.min(room.depth/2-e.d/2-.02,quant(z)))};}
export function fitRoom(doc){return {...doc,items:doc.items.map(item=>{const e=extent({...item,scale:1}),scale=Math.min(item.scale,(doc.room.width-.08)/e.w,(doc.room.depth-.08)/e.d);if(scale<.6)throw Error('Oda bu yerleşim için çok küçük.');return place({...item,scale},doc.room);})};}
export function validDesign(value){
 if(!value||value.version!==1||!value.room||!Array.isArray(value.items)||value.items.length>(value.layout==='home'?160:40))return null;
 const r=value.room;if(![r.width,r.depth,r.height].every(Number.isFinite)||r.width<3||r.width>12||r.depth<3||r.depth>12||r.height<2.4||r.height>4.2||!/^#[a-f0-9]{6}$/i.test(r.wall)||!FLOORS.some(f=>f.id===r.floor)||!['day','golden','night'].includes(r.light))return null;
 if(value.layout && value.layout!=='home')return null; if(value.layout==='home'&&(r.width!==12||r.depth!==10))return null;
 const finishes={};if(value.finishes&&(!value.finishes||typeof value.finishes!=='object'||Array.isArray(value.finishes)))return null;if(value.finishes){for(const [id,f] of Object.entries(value.finishes)){if(!f||typeof f!=='object'||!ROOMS.some(z=>z.id===id)||!FLOORS.some(x=>x.id===f.floor)||!/^#[a-f0-9]{6}$/i.test(f.wall))return null;finishes[id]={floor:f.floor,wall:f.wall};}}
 const ids=new Set();for(const i of value.items){if(!model(i.type)||typeof i.id!=='string'||i.id.length>80||!i.id||ids.has(i.id)||![i.x,i.z,i.scale,i.rotation].every(Number.isFinite)||i.scale<.6||i.scale>1.5||Math.abs(i.rotation)>360||!/^#[a-f0-9]{6}$/i.test(i.color))return null;ids.add(i.id);const e=extent(i);if(Math.abs(i.x)+e.w/2>r.width/2+.001||Math.abs(i.z)+e.d/2>r.depth/2+.001)return null;if(value.layout==='home'){const z=zoneAt(i.x,i.z);if(!z||Math.abs(i.x-z.x)+e.w/2>z.width/2+.001||Math.abs(i.z-z.z)+e.d/2>z.depth/2+.001)return null;}}
 return {version:1,...(value.layout==='home'?{layout:'home',finishes}:{}),room:{width:r.width,depth:r.depth,height:r.height,wall:r.wall,floor:r.floor,light:r.light},items:value.items.map(({id,type,x,z,scale,rotation,color})=>({id,type,x,z,scale,rotation,color}))};
}
export const total=doc=>doc.items.reduce((n,i)=>n+model(i.type).price,0);
export const money=n=>new Intl.NumberFormat('tr-TR',{style:'currency',currency:'TRY',maximumFractionDigits:0}).format(n);
export function overlapping(doc,id){const a=doc.items.find(i=>i.id===id);if(!a||['rug','roundrug','runner','curtain','tablelamp'].includes(a.type))return false;const ea=extent(a);return doc.items.some(b=>{if(b.id===id||['rug','roundrug','runner','curtain','tablelamp'].includes(b.type))return false;const eb=extent(b);return Math.abs(a.x-b.x)<(ea.w+eb.w)/2-.05&&Math.abs(a.z-b.z)<(ea.d+eb.d)/2-.05;});}
export async function api(path,body,method){const r=await fetch('/api'+path,body===undefined&&!method?{}:{method:method||'POST',headers:{'Content-Type':'application/json','X-Archspace-Client':'archspace'},...(body===undefined?{}:{body:JSON.stringify(body)})});if(!r.ok){let message='İşlem tamamlanamadı.';try{const data=await r.json();if(typeof data.detail==='string')message=data.detail;}catch{}throw Error(message);}return r.status===204?null:r.json();}
