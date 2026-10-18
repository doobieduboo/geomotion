"""NASA GIBS background source; imagery is separate from event observations."""
HOST = 'gibs.earthdata.nasa.gov'
LAYER = 'BlueMarble_ShadedRelief_Bathymetry'
DATE = '2004-07-01'
MAX_ZOOM = 8
ATTRIBUTION = 'NASA Blue Marble / NASA GIBS'


def tile_zoom(camera_zoom, mode):
    return max(0, min(MAX_ZOOM, int(camera_zoom) + (2 if mode == 'final' else 0)))


def tile_url(z, x, y):
    if not 0 <= z <= MAX_ZOOM or not 0 <= y < 2**z:
        raise ValueError('NASA Blue Marble tile outside supported matrix')
    return (f'https://{HOST}/wmts/epsg3857/best/{LAYER}/default/{DATE}/'
            f'GoogleMapsCompatible_Level8/{z}/{y}/{x % (2**z)}.jpeg')
