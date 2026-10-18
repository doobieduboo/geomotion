# Asset contract and inventory

## Map data
Use real coordinates, country/admin polygons, coastline/island geometry, and licensed imagery. Record the source version and historical applicability. GeoJSON is WGS84 lon/lat. Preserve Polygon holes and MultiPolygon parts. For long-distance scenes, unwrap longitudes or use a globe-aware projection to avoid antimeridian jumps.

## Asset families
| Family | Files / metadata |
|---|---|
| Country fill | ISO country code, flag PNG/SVG, country GeoJSON, license |
| Flagpole | Flag texture, pole/ground anchor, flutter frames or procedural deformation, shadow |
| Vehicle | RGBA atlas, 16–32 headings, frame size, ground anchor, heading order, view elevation, source/license |
| Tank | Hull atlas, optional separate turret atlas and muzzle flash |
| Aircraft | Heading atlas, engine trail, optional rotor/propeller frames, shadow |
| Ship | Heading atlas, wake, shadow |
| Land transport | Heading atlas, wheels/dust where useful |
| Effects | RGBA frame sequence, fps, lifetime, anchor, blend mode, color-space assumptions |
| Infographic | Real photo/image, verified caption/date, source/license; bubble is drawn procedurally |
| Audio | Licensed/original score and SFX, levels, timing |

## Sprite atlas schema

```json
{
  "image": "tank.png",
  "columns": 8,
  "headings": 32,
  "frame_width": 192,
  "frame_height": 192,
  "anchor": [96, 132],
  "heading_zero": "north",
  "heading_order": "clockwise",
  "view_elevation_deg": 55,
  "license": "record the actual license"
}
```

Each atlas row continues the clockwise heading sequence. Relative heading = world heading minus camera heading. Only use the 32-view claim after checking 32 distinct correct views. A fixed-camera top-down atlas supports yaw changes, not arbitrary pitch/orbit. Use screen-scaled sprites and a geographic ground anchor to avoid sliding.

## Utilities
`map_assets.py` implements:
- `clip_flag`: projected polygons → flag-filled RGBA region with polygon holes.
- `flagpole`: procedural waving flag at a ground anchor.
- `select_sprite`: camera-relative heading → atlas frame and anchor.

These helpers accept actual input assets; they do not download a complete vehicle library. Verify view order, licensing and scale before scene integration.
