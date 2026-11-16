# TMX → Level Converter

Converts Tiled (.tmx) maps into DKC2 Reforge Lua level modules.

## Workflow

1. **Open Tiled** → New Map (16×16 tile size, orthogonal)
2. **Add tileset**: `tileset_placeholder.png` (5 colored tiles)
3. **Paint terrain** using the colored tiles:
   - Tile 1 (brown) = Solid wall/floor
   - Tile 2 (green)  = One-way platform
   - Tile 3 (red)    = Spike
   - Tile 4 (blue)   = Slippery surface
   - Tile 5 (gold)   = Exit portal
4. **Add object layer** with object types:
   - `player_spawn` — start position
   - `banana`, `banana_bunch`, `dk_coin`, `life_balloon`
   - `kritter`, `zinger`, `krusha`, `barrel`, `kremling`
5. **Export as TMX** (File → Save As → .tmx)
6. **Convert** to Lua:

```bash
python tools/tmx-to-level/tmx_to_level.py path/to/level.tmx \
  -o data/levels/level_file.lua \
  --id "1-1" --name "Jungle Hijinks"
```

7. **Add to game**: in `main/level_loader.lua`, add:

```lua
level_file = require("data.levels.level_file"),
```

## Tile Mapping

| Tiled GID | Tile Type | Color  |
|-----------|-----------|--------|
| 1         | Solid     | Brown  |
| 2         | Platform  | Green  |
| 3         | Spike     | Red    |
| 4         | Slippery  | Blue   |
| 5         | Water     | Cyan   |
| 6         | Exit*     | Gold   |
| 0 (none)  | Empty     | —      |

*Exit tile (GID 6) maps to empty by default; use `--tile-map 1=1,2=2,3=3,4=4,5=5,6=0` explicitly.

## Object Properties

Zinger patrol range: add custom properties `patrol_min` and `patrol_max` (integer) to the zinger object.

## CLI Options

```
--tile-map    Custom GID→type mapping (e.g. "1=1,5=5")
--id          Level ID (default: filename)
--name        Display name (default: filename → Title Case)
--tile-size   Tile size in px (default: 16)
--parallax-*  Parallax scroll speeds
```

## Generating Tileset

```bash
python tools/tmx-to-level/generate_tileset.py
```

Output: `tileset_placeholder.png` (96×16, 6 tiles with borders)
