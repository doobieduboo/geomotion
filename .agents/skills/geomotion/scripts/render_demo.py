from PIL import Image,ImageDraw,ImageFont,ImageFilter,ImageEnhance
import numpy as np,math,os,urllib.request,time,wave,subprocess,json
from concurrent.futures import ThreadPoolExecutor,as_completed
from pathlib import Path
import argparse,shutil
from prepare_assets import prepare
SKILL_ROOT=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser(description='GeoMotion reference scene: Jakarta–Rengasdengklok')
parser.add_argument('--mode',choices=['preview','final'],default='preview')
parser.add_argument('--start',type=float,default=0)
parser.add_argument('--duration',type=float,default=15)
parser.add_argument('--output',type=Path)
args=parser.parse_args()
if not (0<=args.start<15 and 0<args.duration<=15-args.start):
 parser.error('Choose an excerpt within the 15-second reference timeline')
if shutil.which('ffmpeg') is None:parser.error('Install FFmpeg before rendering')
D=prepare(SKILL_ROOT)
O=SKILL_ROOT/'cache'/'cinematic';(O/'tiles').mkdir(parents=True,exist_ok=True)
EXPORT=SKILL_ROOT/'outputs';EXPORT.mkdir(exist_ok=True)
OUTPUT=(args.output or EXPORT/(args.mode+'.mp4')).resolve();OUTPUT.parent.mkdir(parents=True,exist_ok=True)
W,H=720,1280;FPS=24 if args.mode=='preview' else 30
OUT_SIZE=(360,640) if args.mode=='preview' else (720,1280)
START=args.start;N=round(args.duration*FPS)
def find_font(bold):
 import os
 candidates=[os.environ.get('GEOMOTION_FONT_BOLD' if bold else 'GEOMOTION_FONT_REGULAR',''),'/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf' if bold else '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf']
 for candidate in candidates:
  if candidate and Path(candidate).is_file():return candidate
 if shutil.which('fc-match'):
  candidate=subprocess.check_output(['fc-match','-f','%{file}','DejaVu Sans:style='+('Bold' if bold else 'Book')],text=True)
  if candidate and Path(candidate).is_file():return candidate
 parser.error('Install DejaVu Sans or set GEOMOTION_FONT_BOLD and GEOMOTION_FONT_REGULAR')
F=find_font(True);FR=find_font(False)
fonts={}
def font(n,b=True):
 if (n,b) not in fonts:fonts[n,b]=ImageFont.truetype(F if b else FR,n)
 return fonts[n,b]
def smooth(x):x=np.clip(x,0,1);return x*x*(3-2*x)
def mix(a,b,v):return a*(1-v)+b*v
def merc(lon,lat,z):
 s=256*2**z;return np.array([(lon+180)/360*s,(1-math.asinh(math.tan(math.radians(lat)))/math.pi)/2*s])
jkt=np.array([106.8467,-6.203]);reng=np.array([107.2945,-6.1586])
def route(v,back=False):
 a,b=(reng,jkt) if back else (jkt,reng)
 return a*(1-v)+b*v+np.array([0,-.055*math.sin(math.pi*v)])
def cam(t):
 if t<2.5:
  e=smooth(t/2.5);pos=mix(np.array([109.8,-7.0]),np.array([107.06,-6.30]),e);zoom=mix(7.0,10.4,e)
 elif t<6.3:
  e=smooth((t-2.5)/3.8);pos=mix(np.array([107.06,-6.30]),np.array([107.09,-6.20]),e);zoom=10.4+0.1*e
 elif t<10.2:
  e=smooth((t-6.3)/3.9);pos=mix(np.array([107.09,-6.20]),np.array([107.05,-6.24]),e);zoom=10.5-.1*e
 else:
  e=smooth((t-10.2)/4.8);pos=mix(np.array([107.05,-6.24]),jkt,e);zoom=mix(10.4,13.15,e)
 angle=mix(-9,5,t/15)
 return pos,float(zoom),angle
# Determine the satellite tiles required by the moving camera.
needed=set();frames=[]
for n in range(N):
 pos,zoom,angle=cam(START+n/FPS);z=int(zoom);center=merc(*pos,z);scale=2**(zoom-z);rad=math.hypot(W,H)/2/scale+35
 frames.append((pos,zoom,angle))
 for x in range(int((center[0]-rad)//256),int((center[0]+rad)//256)+1):
  for y in range(int((center[1]-rad)//256),int((center[1]+rad)//256)+1):needed.add((z,x,y))
def fetch(tile):
 z,x,y=tile;p=O/'tiles'/f'{z}_{x}_{y}.jpg'
 if p.exists():return
 url=f'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}'
 for attempt in range(3):
  try:
   with urllib.request.urlopen(url,timeout=25) as r:data=r.read()
   p.write_bytes(data)
   with Image.open(p) as im:im.verify()
   return
  except Exception:
   if attempt==2:raise
print('Satellite tiles:',len(needed),flush=True)
with ThreadPoolExecutor(max_workers=12) as pool:
 for i,f in enumerate(as_completed([pool.submit(fetch,k) for k in needed])):
  f.result()
  if (i+1)%60==0:print('Downloaded',i+1,flush=True)
mos={}
for z in sorted(set(k[0] for k in needed)):
 ts=[k for k in needed if k[0]==z];xmin=min(k[1] for k in ts);xmax=max(k[1] for k in ts);ymin=min(k[2] for k in ts);ymax=max(k[2] for k in ts)
 im=Image.new('RGB',((xmax-xmin+1)*256,(ymax-ymin+1)*256))
 for _,x,y in ts:
  with Image.open(O/'tiles'/f'{z}_{x}_{y}.jpg') as tile:im.paste(tile,(256*(x-xmin),256*(y-ymin)))
 mos[z]=(im,np.array([xmin*256,ymin*256]))
if not (O/'score.wav').exists():
 sr=44100;ts=np.arange(sr*15)/sr;rng=np.random.default_rng(1945)
 a=np.zeros_like(ts)
 for bt in np.arange(0,15,.6):
  dt=ts-bt;env=np.exp(-np.maximum(dt,0)*18)*(dt>=0);phase=2*np.pi*(47*dt+5*(1-np.exp(-np.maximum(dt,0)*20)))
  a+=.22*np.sin(phase)*env
 for bt in np.arange(.3,15,.3):
  dt=ts-bt;a+=rng.normal(0,1,len(ts))*.018*np.exp(-np.maximum(dt,0)*70)*(dt>=0)
 for k,bt in enumerate(np.arange(0,15,.6)):
  dt=ts-bt;f=[146.83,174.61,220,293.66,261.63,220,174.61,196][k%8]
  a+=(np.sin(2*np.pi*f*dt)+.18*np.sin(2*np.pi*2*f*dt))*.055*np.exp(-np.maximum(dt,0)*3.7)*(dt>=0)
 for bt in [1.7,5.9,9.8]:
  env=np.exp(-((ts-bt)/.28)**2);a+=rng.normal(0,1,len(ts))*.025*env
 fade=np.minimum(np.minimum(ts/.12,(15-ts)/.7),1).clip(0,1);a=np.tanh(a*1.8)*fade
 stereo=np.stack([a,np.roll(a,180)*.97],axis=1)
 with wave.open(str(O/'score.wav'),'w') as w:w.setnchannels(2);w.setsampwidth(2);w.setframerate(sr);w.writeframes((stereo*29000).astype('<i2').tobytes())
from PIL import ImageOps
D=SKILL_ROOT/"assets"/"demo"
C=(239,247,239);CY=(75,222,239);GOLD=(255,196,95);RED=(255,105,68)
regions=[]
for f in json.load(open(D/'boundaries.geojson'))['features']:
 name=f['properties']['shapeName']
 if name not in ['Banten','West Java','Central Java','East Java','Special Region of Yogyakarta','Jakarta Special Capital Region','Bali']:continue
 geometry=f['geometry'];pol=geometry['coordinates'] if geometry['type']=='MultiPolygon' else [geometry['coordinates']]
 for p0 in pol:
  arr=np.array(p0[0]);lon=arr[:,0];lat=arr[:,1]
  world=np.column_stack(((lon+180)/360*256,(1-np.arcsinh(np.tan(np.radians(lat)))/np.pi)/2*256))
  regions.append((name,world))
photo=Image.open(D/'proclamation.jpg').convert('RGB')
# Local pin with an icon: house, document, flag.
def symbol(layer,x,y,kind,color=C):
 d=ImageDraw.Draw(layer)
 if kind=='house':
  d.line([(x-8,y),(x,y-7),(x+8,y)],fill=(*color,255),width=2);d.rectangle((x-6,y,x+6,y+8),outline=(*color,255),width=2);d.line((x,y+3,x,y+8),fill=(*color,255),width=2)
 elif kind=='document':
  d.rounded_rectangle((x-6,y-8,x+6,y+8),2,outline=(*color,255),width=2)
  for yy in [-3,1,5]:d.line((x-3,y+yy,x+3,y+yy),fill=(*color,255),width=1)
 elif kind=='flag':
  d.line((x-5,y-9,x-5,y+9),fill=(*color,255),width=2);d.polygon([(x-4,y-8),(x+8,y-6),(x+6,y+1),(x-4,y-1)],fill=(*color,255))
def text(layer,xy,s,n=22,color=C,bold=False,opacity=255):
 ImageDraw.Draw(layer).text(xy,s,font=font(n,bold),fill=(*color,opacity))
def bubble(anchor,box,title,lines,kind,color,visibility,pic=False):
 x,y,w,h=box;x=int(x);y=int(y);v=float(smooth(visibility));y+=int((1-v)*18)
 layer=Image.new('RGBA',(W,H));d=ImageDraw.Draw(layer);ax,ay=anchor
 # Leader is attached to the closest vertical edge.
 px=max(x+24,min(x+w-24,ax));edge=y+h if ay>y+h/2 else y
 d.line([(ax,ay),(px,edge+14 if edge==y+h else edge-14),(px,edge)],fill=(*color,200),width=2)
 d.rounded_rectangle((x,y,x+w,y+h),16,fill=(9,22,29,240),outline=(*color,190),width=1)
 d.line((x+18,y+1,x+w-18,y+1),fill=(*color,255),width=2)
 yy=y+17
 if pic:
  p=ImageOps.fit(photo,(w-24,168),method=Image.Resampling.LANCZOS,centering=(.55,.35));mask=Image.new('L',p.size);ImageDraw.Draw(mask).rounded_rectangle((0,0,p.width,p.height),10,fill=255)
  layer.paste(p,(x+12,y+12),mask);yy=y+194
 symbol(layer,x+26,yy+10,kind,color);text(layer,(x+46,yy-2),title,23,C,True)
 for i,line in enumerate(lines):text(layer,(x+19,yy+38+i*28),line,19,(196,215,218))
 # Shadow, restrained glow, then glass card.
 a=layer.getchannel('A').point(lambda z:int(z*v));layer.putalpha(a)
 return layer
# Mild edge shading, leaving the map itself dominant.
y=np.arange(H)[:,None];alpha=np.broadcast_to((np.clip(1-y/250,0,1)*80+np.clip((y-1100)/180,0,1)*120),(H,W)).astype('uint8')
shade=Image.new('RGBA',(W,H),(3,9,15));shade.putalpha(Image.fromarray(alpha))
p=subprocess.Popen(['ffmpeg','-y','-loglevel','error','-f','rawvideo','-pix_fmt','rgb24','-s',f'{OUT_SIZE[0]}x{OUT_SIZE[1]}','-r',str(FPS),'-i','-','-ss',str(START),'-i',str(O/'score.wav'),'-c:v','libx264','-preset','fast','-crf','25' if args.mode=='preview' else '18','-pix_fmt','yuv420p','-c:a','aac','-b:a','192k','-t',str(N/FPS),'-movflags','+faststart',str(OUTPUT)],stdin=subprocess.PIPE)
for n,(pos,zoom,angle) in enumerate(frames):
 t=START+n/FPS;z=int(zoom);scale=2**(zoom-z);theta=math.radians(angle);cs,sn=math.cos(theta),math.sin(theta);center=merc(*pos,z);mosaic,origin=mos[z];mid=center-origin
 af=(cs/scale,sn/scale,mid[0]-(cs*W/2+sn*H/2)/scale,-sn/scale,cs/scale,mid[1]-(-sn*W/2+cs*H/2)/scale)
 im=mosaic.transform((W,H),Image.Transform.AFFINE,af,Image.Resampling.BICUBIC)
 im=ImageEnhance.Color(im).enhance(.53);im=ImageEnhance.Contrast(im).enhance(1.12);im=ImageEnhance.Brightness(im).enhance(.69);im=im.convert('RGBA')
 def project(ll):
  v=(merc(*ll,z)-center)*scale;return np.array([W/2+cs*v[0]-sn*v[1],H/2+sn*v[0]+cs*v[1]])
 fills=Image.new('RGBA',(W,H));edges=Image.new('RGBA',(W,H));df=ImageDraw.Draw(fills);de=ImageDraw.Draw(edges)
 reveal=float(smooth((t-.15)/1.5))
 for name,world in regions:
  a=(world*2**z-center)*scale;pts=np.column_stack((W/2+cs*a[:,0]-sn*a[:,1],H/2+sn*a[:,0]+cs*a[:,1]))
  if pts[:,0].max()<0 or pts[:,0].min()>W or pts[:,1].max()<0 or pts[:,1].min()>H:continue
  pp=[tuple(v) for v in pts];col=GOLD if name.startswith('Jakarta') else CY
  df.polygon(pp,fill=(*col,int((22 if name.startswith('Jakarta') else 8)*reveal)))
  count=max(2,int(len(pp)*reveal));de.line(pp[:count],fill=(*col,190),width=2,joint='curve')
 im.alpha_composite(fills);im.alpha_composite(edges.filter(ImageFilter.GaussianBlur(10)));im.alpha_composite(edges.filter(ImageFilter.GaussianBlur(3)));im.alpha_composite(edges)
 # World-anchored administrative labels.
 labels=Image.new('RGBA',(W,H));dl=ImageDraw.Draw(labels)
 for ll,label in [((106.4,-6.7),'BANTEN'),((107.48,-6.73),'JAWA BARAT'),((110.2,-7.3),'JAWA TENGAH')]:
  x,y=project(ll)
  if -100<x<W-80 and 300<y<1090:
   opacity=int(125*min(1,t/.7));dl.text((x,y),label,font=font(17,True),fill=(*CY,opacity),stroke_width=2,stroke_fill=(3,10,15,90))
 im.alpha_composite(labels)
 # Outbound and inbound route, with a car marker following the line.
 trails=Image.new('RGBA',(W,H));dt=ImageDraw.Draw(trails)
 for back,start,end,col in [(False,1.8,5.8,RED),(True,6.6,9.8,C)]:
  v=float(smooth((t-start)/(end-start)))
  if v<=0:continue
  opacity=int(255*(1-smooth((t-10.2)/1.1))) if t>10.2 else 255
  if opacity<=0:continue
  pts=[tuple(project(route(u,back))) for u in np.linspace(0,v,120)]
  dt.line(pts,fill=(*col,opacity),width=4 if not back else 3,joint='curve')
  if start<t<end:
   x,y=pts[-1];q=project(route(max(0,v-.01),back));ang=math.degrees(math.atan2(y-q[1],x-q[0]))
   icon=Image.new('RGBA',(46,32));di=ImageDraw.Draw(icon);di.rounded_rectangle((10,7,36,24),4,fill=(9,22,29,255),outline=(*col,255),width=2);di.rectangle((17,10,28,21),fill=(*col,255));di.rectangle((21,9,24,22),fill=(9,22,29,255))
   icon=icon.rotate(-ang,resample=Image.Resampling.BICUBIC,expand=True);trails.alpha_composite(icon,(int(x-icon.width/2),int(y-icon.height/2)))
 im.alpha_composite(trails.filter(ImageFilter.GaussianBlur(7)));im.alpha_composite(trails)
 # Persistent map pins with house / flag icons and geographic labels.
 pins=Image.new('RGBA',(W,H));dp=ImageDraw.Draw(pins)
 for ll,name,kind,color,visible in [(jkt,'JAKARTA','flag',GOLD,t>1.0),(reng,'RENGASDENGKLOK','house',CY,2.3<t<11.2)]:
  if not visible:continue
  x,y=project(ll)
  if not(-40<x<W+40 and 180<y<1100):continue
  rr=23+4*math.sin(t*3)**2;dp.ellipse((x-rr,y-rr,x+rr,y+rr),outline=(*color,90),width=1)
  dp.ellipse((x-17,y-17,x+17,y+17),fill=(8,22,28,245),outline=(*color,255),width=2);symbol(pins,x,y,kind,color)
  lx=max(28,min(W-(285 if len(name)>10 else 150),x-65));ly=y+35
  dp.text((lx,ly),name,font=font(21,True),fill=(*C,255),stroke_width=3,stroke_fill=(4,11,16,220))
 im.alpha_composite(pins)
 # Compact, connected infographic callouts. No editorial headline typography.
 if 3.2<t<6.3:
  rx,ry=project(reng);v=min((t-3.2)/.35,(6.3-t)/.3,1)
  b=bubble((rx,ry),(max(40,min(340,rx-220)),max(140,ry-270),340,172),'Rengasdengklok',['16 Agustus 1945','Soekarno & Hatta','dibawa ke Rengasdengklok.'],'house',CY,v)
  im.alpha_composite(b)
 if 7.1<t<10.25:
  x,y=project(jkt);v=min((t-7.1)/.35,(10.25-t)/.3,1)
  b=bubble((x,y),(max(40,min(330,x+15)),min(925,y+150),350,188),'Kembali ke Jakarta',['Malam, 16 Agustus 1945','Naskah dirumuskan hingga','dini hari 17 Agustus.'],'document',GOLD,v)
  im.alpha_composite(b)
 if t>10.65:
  x,y=project(jkt);v=min((t-10.65)/.45,1)
  b=bubble((x,y),(max(40,min(320,x-130)),max(130,y-450),360,318),'Proklamasi',['17 Agustus 1945 · 10.00 WIB','Pegangsaan Timur 56, Jakarta.'],'flag',GOLD,v,True)
  im.alpha_composite(b)
 im.alpha_composite(shade)

 if n in [28,112,196,320]:im.convert('RGB').resize(OUT_SIZE,Image.Resampling.LANCZOS).save(OUTPUT.parent/f'{OUTPUT.stem}_frame_{n}.jpg')
 p.stdin.write(im.convert('RGB').resize(OUT_SIZE,Image.Resampling.LANCZOS).tobytes())
 if n%150==0:print('Rendered',n,flush=True)
p.stdin.close();assert p.wait()==0
print('DONE',OUTPUT,flush=True)
