"""Sample a supplied transparent Web Mercator world texture, with longitude wrap."""
import math
from PIL import Image


def project_world_overlay(texture, camera, size, scale):
    if texture.width != texture.height:
        raise ValueError('World overlay must be a square EPSG:3857 world image')
    if texture.mode != 'RGBa':
        texture = texture.convert('RGBa')
    width, height = size
    side = texture.width
    lon, lat = camera['center']
    lat = max(-85.0511, min(85.0511, lat))
    center_x = ((lon + 180) / 360 * side) % side
    center_y = (1 - math.asinh(math.tan(math.radians(lat))) / math.pi) / 2 * side
    factor = side / (256 * 2**camera['zoom'] * scale)
    angle = math.radians(camera.get('rotation',0))
    cs, sn = math.cos(angle), math.sin(angle)
    a,b,d,e = cs*factor,sn*factor,-sn*factor,cs*factor
    c = center_x - (a*width+b*height)/2
    f = center_y - (d*width+e*height)/2
    result = Image.new('RGBA',size)
    # The premultiplied source is immutable during a render. Cache its alpha
    # extent, then sample only the output rectangle affected by that extent.
    key = '_geomotion_alpha_extent'
    if key not in texture.info:
        texture.info[key] = texture.getchannel(3).getbbox()
    extent = texture.info[key]
    if extent is None:
        return result
    determinant = a*e-b*d
    for shift in (-side,0,side):
        # Bicubic support is two input pixels; pad conservatively on both grids.
        corners=[]
        for sx in (extent[0]-3,extent[2]+3):
            for sy in (extent[1]-3,extent[3]+3):
                tx,ty=sx-c-shift,sy-f
                corners.append(((e*tx-b*ty)/determinant,(-d*tx+a*ty)/determinant))
        left=max(0,math.floor(min(p[0] for p in corners))-2)
        top=max(0,math.floor(min(p[1] for p in corners))-2)
        right=min(width,math.ceil(max(p[0] for p in corners))+2)
        bottom=min(height,math.ceil(max(p[1] for p in corners))+2)
        if left>=right or top>=bottom:
            continue
        transform=(a,b,c+shift+a*left+b*top,d,e,f+d*left+e*top)
        layer=texture.transform((right-left,bottom-top),Image.Transform.AFFINE,transform,Image.Resampling.BICUBIC).convert('RGBA')
        result.alpha_composite(layer,(left,top))
    return result
