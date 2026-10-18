"""Topic-agnostic, scene-driven 2D geographic motion graphics renderer."""
import argparse,io,json,math,shutil,subprocess,urllib.request
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import numpy as np
from PIL import Image,ImageDraw,ImageFont,ImageFilter,ImageOps,ImageEnhance
from map_assets import clip_flag,flagpole,select_sprite
from basemap import tile_zoom,tile_url,ATTRIBUTION,validate_basemap


def merc(lon,lat,zoom):
    scale=256*2**zoom;lat=max(-85.0511,min(85.0511,lat))
    return np.array([(lon+180)/360*scale,(1-math.asinh(math.tan(math.radians(lat)))/math.pi)/2*scale])


def ease(v):
    v=max(0,min(1,v));return v*v*(3-2*v)


def camera_at(keys,t):
    if t<=keys[0]['time']:return keys[0]
    if t>=keys[-1]['time']:return keys[-1]
    for a,b in zip(keys,keys[1:]):
        if a['time']<=t<=b['time']:
            u=(t-a['time'])/(b['time']-a['time']);u=u if b.get('ease')=='linear' else ease(u)
            # Take the short path at the antimeridian; keep an unwrapped center.
            delta=(b['center'][0]-a['center'][0]+180)%360-180
            heading=(b.get('rotation',0)-a.get('rotation',0)+180)%360-180
            return {'center':[a['center'][0]+u*delta,a['center'][1]+u*(b['center'][1]-a['center'][1])],
                    'zoom':a['zoom']+u*(b['zoom']-a['zoom']), 'rotation':a.get('rotation',0)+u*heading}


def validate(scene):
    if scene.get('duration',0)<=0:raise ValueError('duration must be positive')
    keys=scene.get('camera',[])
    if not keys:raise ValueError('camera requires at least one keyframe')
    last=-1
    for k in keys:
        if k['time']<0 or k['time']<=last:raise ValueError('camera times must increase strictly')
        last=k['time'];lon,lat=k['center']
        if not(-180<=lon<=180 and -85<=lat<=85):raise ValueError('Invalid camera coordinate')
        if not 0<=k['zoom']<=18:raise ValueError('Camera zoom must be 0–18')
    for route in scene.get('routes',[]):
        if len(route.get('points',[]))<2 or route.get('end',0)<=route.get('start',0):raise ValueError('Routes need 2+ points and end > start')
    for item in scene.get('markers',[])+scene.get('callouts',[]):
        lon,lat=item['position']
        if not(-180<=lon<=180 and -85<=lat<=85):raise ValueError('Invalid layer coordinate')


def color(value):return tuple(value or [75,222,239])


SKILL_ROOT=Path(__file__).resolve().parents[1]
DEFAULTS=json.loads((SKILL_ROOT/'defaults.json').read_text())

def load_font(size,bold=False):
    import os
    name='DejaVuSans-Bold.ttf' if bold else 'DejaVuSans.ttf'
    env=os.environ.get('GEOMOTION_FONT_BOLD' if bold else 'GEOMOTION_FONT_REGULAR')
    path=env or str(SKILL_ROOT/DEFAULTS['typography']['bold_font' if bold else 'regular_font'])
    if not Path(path).exists() and shutil.which('fc-match'):
        path=subprocess.check_output(['fc-match','-f','%{file}','DejaVu Sans:style='+('Bold' if bold else 'Book')],text=True)
    return ImageFont.truetype(path,size)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('scene',type=Path);parser.add_argument('--mode',choices=['preview','final'],default='preview')
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    scene=json.loads(args.scene.read_text());validate(scene)
    if not shutil.which('ffmpeg'):parser.error('Install FFmpeg')
    root=args.scene.resolve().parent
    def path(value):return (root/value).resolve()
    export={**DEFAULTS['export'][args.mode],**scene.get('export',{}).get(args.mode,{})}
    width,height,fps=(int(export[k]) for k in ('width','height','fps'))
    if min(width,height,fps)<=0 or width%2 or height%2:raise ValueError('Export requires positive even dimensions and positive fps')
    duration=float(scene['duration']);count=max(1,round(duration*fps));scale=width/720
    basemap={**DEFAULTS['basemap'],**scene.get('basemap',{})}
    validate_basemap(basemap)
    if ATTRIBUTION not in scene.get('attribution',''):
        scene['attribution']=' · '.join(filter(None,[scene.get('attribution'),ATTRIBUTION]))
    # Session-memory tiles only: this viewing service does not allow offline tile export.
    tile_images={}
    prepared=[camera_at(scene['camera'],n/fps) for n in range(count)]
    needed=set()
    if basemap.get('type')=='satellite':
        for camera in prepared:
            z=tile_zoom(camera['zoom'],args.mode);c=merc(*camera['center'],z);s=2**(camera['zoom']-z)*scale;r=math.hypot(width,height)/2/s+3
            for x in range(math.floor((c[0]-r)/256),math.floor((c[0]+r)/256)+1):
                for y in range(max(0,math.floor((c[1]-r)/256)),min(2**z-1,math.floor((c[1]+r)/256))+1):needed.add((z,x,y))
    # Deduplicate wrapped tiles before parallel requests.
    physical_tiles={(z,x%(2**z),y) for z,x,y in needed}
    def fetch(tile):
        z,x,y=tile;url=tile_url(z,x,y)
        req=urllib.request.Request(url,headers={'User-Agent':'GeoMotion/1.0'})
        try:
            with urllib.request.urlopen(req,timeout=40) as response:data=response.read()
            with Image.open(io.BytesIO(data)) as image:
                image.load()
                if image.size!=(256,256):raise ValueError('Expected a 256px imagery tile')
                return tile,image.convert('RGB')
        except Exception as exc:
            raise RuntimeError(f'Esri World Imagery request failed from {url}: {exc}. Check access/network policy; no alternate basemap is permitted.') from exc
    with ThreadPoolExecutor(max_workers=8) as pool:
        tile_images.update(pool.map(fetch,physical_tiles))
    mosaics={}
    for z in sorted({k[0] for k in needed}):
        tiles=[k for k in needed if k[0]==z];xmin=min(k[1] for k in tiles);xmax=max(k[1] for k in tiles);ymin=min(k[2] for k in tiles);ymax=max(k[2] for k in tiles)
        # Protect memory on overly wide multi-stop scenes. Split the scene if necessary.
        if (xmax-xmin+1)*(ymax-ymin+1)>1800:raise ValueError('Tile mosaic too large; split camera sequence into shots')
        im=Image.new('RGB',((xmax-xmin+1)*256,(ymax-ymin+1)*256))
        for _,x,y in tiles:
            im.paste(tile_images[(z,x%(2**z),y)],((x-xmin)*256,(y-ymin)*256))
        mosaics[z]=(im,np.array([xmin*256,ymin*256]))
    image_cache={}
    def image_file(value):
        if value not in image_cache:image_cache[value]=Image.open(path(value)).convert('RGBA')
        return image_cache[value]
    regions=[]
    for region in scene.get('regions',[]):
        data=json.loads(path(region['geojson']).read_text())
        features=data['features'] if data['type']=='FeatureCollection' else [data] if data['type']=='Feature' else [{'geometry':data,'properties':{}}]
        for feature in features:
            if any(feature.get('properties',{}).get(k)!=v for k,v in region.get('match',{}).items()):continue
            g=feature['geometry']
            if g['type'] not in ['Polygon','MultiPolygon']:continue
            polys=g['coordinates'] if g['type']=='MultiPolygon' else [g['coordinates']]
            regions.append((region,polys))
    args.output.parent.mkdir(parents=True,exist_ok=True)
    command=['ffmpeg','-y','-loglevel','error','-f','rawvideo','-pix_fmt','rgb24','-s',f'{width}x{height}','-r',str(fps),'-i','-']
    if scene.get('audio'):command+=['-i',str(path(scene['audio'])),'-af','apad']
    command+=['-c:v','libx264','-preset',export['preset'],'-crf',str(export['crf']),'-maxrate',export['maxrate'],'-bufsize',export['bufsize'],'-pix_fmt','yuv420p']
    if scene.get('audio'):command+=['-c:a','aac','-b:a',export['audio_bitrate']]
    command+=['-t',str(count/fps),'-movflags','+faststart',str(args.output)]
    p=subprocess.Popen(command,stdin=subprocess.PIPE)
    try:
        for n,camera in enumerate(prepared):
            t=n/fps;z=tile_zoom(camera['zoom'],args.mode);zoom_scale=2**(camera['zoom']-z)*scale;center=merc(*camera['center'],z)
            a=math.radians(camera.get('rotation',0));cs,sn=math.cos(a),math.sin(a)
            def project(ll):
                xy=merc(*ll,z);world=256*2**z
                xy[0]=center[0]+(xy[0]-center[0]+world/2)%world-world/2
                v=(xy-center)*zoom_scale
                return (width/2+cs*v[0]-sn*v[1],height/2+sn*v[0]+cs*v[1])
            if mosaics:
                mosaic,origin=mosaics[z];mid=center-origin
                af=(cs/zoom_scale,sn/zoom_scale,mid[0]-(cs*width/2+sn*height/2)/zoom_scale,-sn/zoom_scale,cs/zoom_scale,mid[1]-(-sn*width/2+cs*height/2)/zoom_scale)
                im=mosaic.transform((width,height),Image.Transform.AFFINE,af,Image.Resampling.BICUBIC)
                im=ImageEnhance.Color(im).enhance(basemap.get('saturation',1.0));im=ImageEnhance.Brightness(im).enhance(basemap.get('brightness',1.0));im=im.convert('RGBA')
            else:raise RuntimeError('Esri imagery is missing; cannot render an alternate basemap')
            def visible(item):return item.get('start',0)<=t<item.get('end',duration)
            edges=Image.new('RGBA',im.size);ed=ImageDraw.Draw(edges)
            for region,polys in regions:
                if not visible(region):continue
                projected=[[[project(ll) for ll in ring] for ring in poly] for poly in polys]
                if region.get('fill'):
                    texture=Image.new('RGBA',(1,1),color(region['fill'])+(255,))
                    im.alpha_composite(clip_flag(texture,projected,im.size,region.get('opacity',80)))
                if region.get('flag'):
                    im.alpha_composite(clip_flag(image_file(region['flag']),projected,im.size,region.get('opacity',180)))
                col=color(region.get('color'));reveal=ease((t-region.get('start',0))/max(.01,region.get('reveal',1)))
                for poly in projected:
                    for ring in poly:
                        limit=max(2,int(len(ring)*reveal))
                        if reveal>0 and len(ring)>1:ed.line(ring[:limit],fill=col+(210,),width=max(1,round(2*scale)),joint='curve')
            im.alpha_composite(edges.filter(ImageFilter.GaussianBlur(6*scale)));im.alpha_composite(edges)
            routes=Image.new('RGBA',im.size);rd=ImageDraw.Draw(routes)
            for route in scene.get('routes',[]):
                if t<route['start'] or t>=route.get('hide_at',duration):continue
                u=ease((t-route['start'])/(route['end']-route['start']));points=route['points']
                projected=[project(ll) for ll in points];lengths=[math.dist(a,b) for a,b in zip(projected,projected[1:])];remaining=sum(lengths)*u;trail=[projected[0]];heading=0
                for i,length in enumerate(lengths):
                    start,end=projected[i:i+2];fraction=min(1,remaining/max(length,.0001));tail=tuple(start[k]+fraction*(end[k]-start[k]) for k in range(2));trail.append(tail)
                    heading=math.degrees(math.atan2(end[0]-start[0],-(end[1]-start[1])))
                    remaining-=length
                    if remaining<=0:break
                col=color(route.get('color',[255,105,68]));rd.line(trail,fill=col+(255,),width=max(1,round(route.get('width',4)*scale)),joint='curve');x,y=trail[-1]
                if route.get('atlas'):
                    meta=json.loads(path(route['atlas_metadata']).read_text());frame,anchor,_=select_sprite(image_file(route['atlas']),meta,heading)
                    factor=route.get('sprite_scale',1)*scale;size=(max(1,round(frame.width*factor)),max(1,round(frame.height*factor)));frame=frame.resize(size,Image.Resampling.LANCZOS)
                    routes.alpha_composite(frame,(round(x-anchor[0]*factor),round(y-anchor[1]*factor)))
                else:rd.ellipse((x-3,y-3,x+3,y+3),fill=(255,246,222,255))
            im.alpha_composite(routes.filter(ImageFilter.GaussianBlur(4*scale)));im.alpha_composite(routes)
            overlay=Image.new('RGBA',im.size);draw=ImageDraw.Draw(overlay)
            for marker in scene.get('markers',[]):
                if not visible(marker):continue
                x,y=project(marker['position']);col=color(marker.get('color'));r=max(3,round(12*scale))
                if marker.get('flag'):
                    overlay.alpha_composite(flagpole(image_file(marker['flag']),(x,y),t,size=(round(50*scale),round(32*scale)),pole_height=round(65*scale),canvas_size=im.size))
                else:
                    draw.ellipse((x-r,y-r,x+r,y+r),fill=(7,20,28,230),outline=col+(255,),width=max(1,round(2*scale)))
                    draw.ellipse((x-2,y-2,x+2,y+2),fill=col+(255,))
                label=marker.get('label')
                if label:
                    offset=marker.get('offset',[18,15]);draw.text((x+offset[0]*scale,y+offset[1]*scale),label,font=load_font(max(10,round(marker.get('font_size',21)*scale)),True),fill=(239,247,239,255),stroke_width=1,stroke_fill=(0,0,0,230))
            for callout in scene.get('callouts',[]):
                if not visible(callout):continue
                ax,ay=project(callout['position']);image=callout.get('image');lines=callout.get('lines',[]);w=round(callout.get('width',330)*scale)
                h=round((80+len(lines)*27+(160 if image else 0))*scale)
                offset=callout.get('offset',[-100,-300]);x=int(max(10,min(width-w-10,ax+offset[0]*scale)));y=int(max(10,min(height-h-10,ay+offset[1]*scale)))
                col=color(callout.get('color'));px=max(x+12,min(x+w-12,ax));edge=y+h if ay>y+h/2 else y
                draw.line([(ax,ay),(px,edge)],fill=col+(210,),width=1);draw.rounded_rectangle((x,y,x+w,y+h),radius=max(4,round(14*scale)),fill=(9,22,29,240),outline=col+(210,),width=1)
                yy=y+round(15*scale)
                if image:
                    pic=ImageOps.fit(image_file(image),(w-round(24*scale),round(150*scale)),method=Image.Resampling.LANCZOS);overlay.alpha_composite(pic,(x+round(12*scale),yy));yy+=round(165*scale)
                draw.text((x+12*scale,yy),callout.get('title',''),font=load_font(max(11,round(22*scale)),True),fill=(239,247,239,255))
                for i,line in enumerate(lines):draw.text((x+12*scale,yy+(35+i*27)*scale),line,font=load_font(max(9,round(19*scale))),fill=(196,215,218,255))
            if scene.get('attribution'):
                draw.text((10,height-20),scene['attribution'],font=load_font(max(8,round(12*scale))),fill=(185,207,212,240))
            im.alpha_composite(overlay)
            if n in {0,count//2,count-1}:im.convert('RGB').save(args.output.with_name(args.output.stem+f'_frame_{n}.jpg'))
            p.stdin.write(im.convert('RGB').tobytes())
    except BaseException:
        p.stdin.close();p.wait();args.output.unlink(missing_ok=True)
        raise
    else:p.stdin.close()
    if p.wait()!=0:
        args.output.unlink(missing_ok=True)
        raise RuntimeError('FFmpeg render failed')
    print(args.output.resolve())


if __name__=='__main__':main()
