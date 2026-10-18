"""Reusable 2D map layers. Input coordinates for polygons are projected screen pixels."""
import math
from PIL import Image, ImageDraw


def clip_flag(flag, polygons, size, opacity=255):
    """Clip one flag across all rings. Each polygon = [outer, hole1, ...]."""
    polygons = list(polygons)
    points = [point for polygon in polygons for ring in polygon for point in ring]
    if not points:
        return Image.new('RGBA', size)
    left = math.floor(min(p[0] for p in points))
    top = math.floor(min(p[1] for p in points))
    right = math.ceil(max(p[0] for p in points))
    bottom = math.ceil(max(p[1] for p in points))
    if right <= left or bottom <= top:
        return Image.new('RGBA', size)
    # Caller should clip extreme off-screen polygons before allocating a huge texture.
    if (right-left)*(bottom-top) > 40_000_000:
        raise ValueError('Projected flag region is too large; clip to the viewport first')
    mask = Image.new('L', size)
    for polygon in polygons:
        part = Image.new('L', size)
        draw = ImageDraw.Draw(part)
        if polygon:
            draw.polygon(polygon[0], fill=opacity)
            for hole in polygon[1:]:
                draw.polygon(hole, fill=0)
            from PIL import ImageChops
            mask = ImageChops.lighter(mask, part)
    image = Image.new('RGBA', size)
    texture = flag.convert('RGBA').resize((right-left,bottom-top), Image.Resampling.LANCZOS)
    image.paste(texture,(left,top))
    from PIL import ImageChops
    image.putalpha(ImageChops.multiply(image.getchannel('A'),mask))
    return image


def flagpole(flag, ground, time_s, size=(50,32), pole_height=65, canvas_size=(720,1280)):
    """Billboard marker; pole's foot remains exactly on its geographic anchor."""
    x,y = map(int,ground)
    width,height = size
    out = Image.new('RGBA',canvas_size)
    draw = ImageDraw.Draw(out)
    draw.ellipse((x-11,y-3,x+12,y+4),fill=(0,0,0,75))
    draw.line((x,y,x,y-pole_height),fill=(225,231,232,255),width=2)
    draw.ellipse((x-2,y-pole_height-2,x+2,y-pole_height+2),fill=(255,220,135,255))
    flag = flag.convert('RGBA').resize((width,height),Image.Resampling.LANCZOS)
    for col in range(width):
        dy=round(math.sin(col/width*math.pi*2-time_s*5)*height*.08*(col/width))
        out.alpha_composite(flag.crop((col,0,col+1,height)),(x+1+col,y-pole_height+3+dy))
    return out


def select_sprite(atlas, metadata, world_heading_deg, camera_heading_deg=0):
    """Returns (RGBA frame, frame-local ground anchor, selected heading index)."""
    n=int(metadata['headings']);cols=int(metadata['columns'])
    fw=int(metadata['frame_width']);fh=int(metadata['frame_height'])
    if min(n,cols,fw,fh)<1:
        raise ValueError('Invalid atlas dimensions')
    if metadata.get('heading_zero','north')!='north' or metadata.get('heading_order','clockwise')!='clockwise':
        raise ValueError('Normalize atlas headings to north-zero, clockwise')
    if atlas.width<cols*fw or atlas.height<math.ceil(n/cols)*fh:
        raise ValueError('Atlas image is smaller than its metadata grid')
    relative=(world_heading_deg-camera_heading_deg)%360
    index=int(math.floor(relative/(360/n)+.5))%n
    x=(index%cols)*fw;y=(index//cols)*fh
    return atlas.crop((x,y,x+fw,y+fh)).convert('RGBA'),tuple(metadata['anchor']),index
