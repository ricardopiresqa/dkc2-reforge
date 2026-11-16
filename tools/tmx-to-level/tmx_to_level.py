"""Convert Tiled TMX (XML) → DKC2 Reforge Lua level module.

Usage:
  python tmx_to_level.py path/to/level.tmx -o data/levels/level_file.lua
  python tmx_to_level.py path/to/level.tmx (prints to stdout)

Tiled tile GID mapping (configurable via --tile-map):
  GID 1 -> tile_type 1 (solid)
  GID 2 -> tile_type 2 (platform)
  GID 3 -> tile_type 3 (spike)
  GID 4 -> tile_type 4 (slippery)
  GID 5 -> tile_type 5 (exit)
  Any unmapped GID -> tile_type 0 (empty)

Object layer: place Tiled objects with type="player_spawn",
  "banana", "banana_bunch", "kritter", "zinger", "krusha",
  "dk_coin", "life_balloon", "barrel", "kremling".
  Custom properties for zinger: patrol_min, patrol_max (int).
"""

import xml.etree.ElementTree as ET
import argparse
import os
import re


def parse_tmx(filepath):
    tree = ET.parse(filepath)
    root = tree.getroot()
    return root


def get_map_attributes(root):
    return {
        "width": int(root.attrib["width"]),
        "height": int(root.attrib["height"]),
        "tilewidth": int(root.attrib["tilewidth"]),
        "tileheight": int(root.attrib["tileheight"]),
    }


def parse_tile_layer(root, tile_map):
    width = int(root.attrib["width"])
    height = int(root.attrib["height"])
    result = []

    for layer in root.findall("layer"):
        data_el = layer.find("data")
        if data_el is None:
            continue
        encoding = data_el.attrib.get("encoding", "csv")
        if encoding == "csv":
            raw = (data_el.text or "").strip()
            values = [int(v.strip()) for v in raw.replace("\n", "").split(",") if v.strip()]
        elif encoding == "base64":
            import base64
            raw = data_el.text or ""
            decoded = base64.b64decode(raw.strip())
            values = []
            for i in range(0, len(decoded), 4):
                gid = decoded[i] | (decoded[i + 1] << 8) | (decoded[i + 2] << 16) | (decoded[i + 3] << 24)
                # Strip flip flags (top 3 bits)
                gid = gid & 0x1FFFFFFF
                values.append(gid)
        else:
            raise ValueError(f"Unsupported encoding: {encoding}")

        for row_idx in range(height):
            row_start = row_idx * width
            row = values[row_start:row_start + width]
            mapped = [tile_map.get(gid, 0) for gid in row]
            result.append(mapped)

    return result


def parse_object_layer(root):
    objects = []

    for group in root.findall("objectgroup"):
        for obj in group.findall("object"):
            obj_type = obj.attrib.get("type") or obj.attrib.get("name", "")
            if not obj_type:
                continue

            obj_type = obj_type.lower().replace(" ", "_")
            x = float(obj.attrib["x"])
            y = float(obj.attrib["y"])
            width = float(obj.attrib.get("width", 16))
            height = float(obj.attrib.get("height", 16))

            # Tiled origin is top-left; our engine is top-left too (mostly)
            # Center x, y for objects (use center of tile)
            cx = x + width / 2
            cy = y + height / 2

            if obj_type == "player_spawn":
                objects.append({
                    "type": "player_spawn",
                    "x": int(cx),
                    "y": int(cy),
                })
                continue

            entry = {
                "type": obj_type,
                "x": int(cx),
                "y": int(cy),
            }

            props = {}
            for prop in obj.findall("properties/property"):
                props[prop.attrib["name"]] = prop.attrib.get("value")
            if props:
                entry["params"] = {}
                for k, v in props.items():
                    try:
                        entry["params"][k] = int(v)
                    except ValueError:
                        try:
                            entry["params"][k] = float(v)
                        except ValueError:
                            entry["params"][k] = v

            objects.append(entry)

    return objects


def get_custom_properties(root):
    props = {}
    for prop in root.findall("properties/property"):
        props[prop.attrib["name"]] = prop.attrib.get("value")
    return props


def format_lua_value(val, indent=2):
    if isinstance(val, dict):
        items = []
        for k, v in val.items():
            fv = format_lua_value(v, indent + 2)
            items.append(f"{' ' * (indent + 2)}{k} = {fv}")
        return "{\n" + ",\n".join(items) + f"\n{' ' * indent}}}"
    elif isinstance(val, list):
        if all(isinstance(v, int) for v in val):
            return "{" + ",".join(str(v) for v in val) + "}"
        items = [f"{' ' * (indent + 2)}{format_lua_value(v, indent + 2)}" for v in val]
        return "{\n" + ",\n".join(items) + f"\n{' ' * indent}}}"
    elif isinstance(val, bool):
        return str(val).lower()
    elif isinstance(val, int):
        return str(val)
    elif isinstance(val, float):
        if val == int(val):
            return str(int(val))
        return f"{val:.2f}"
    elif isinstance(val, str):
        escaped = val.replace("\\", "\\\\").replace("'", "\\'")
        return f"'{escaped}'"
    return str(val)


def generate_lua(level_data):
    lines = []
    lines.append("return {")
    lines.append(f"  id = {format_lua_value(level_data['id'])},")
    lines.append(f"  name = {format_lua_value(level_data['name'])},")
    lines.append(f"  width = {level_data['width']},")
    lines.append(f"  height = {level_data['height']},")
    lines.append(f"  tile_size = {level_data['tile_size']},")

    spawn = level_data.get("player_spawn")
    if spawn:
        lines.append(f"  player_spawn = {{ x = {spawn['x']}, y = {spawn['y']} }},")
    else:
        lines.append("  player_spawn = { x = 64, y = 128 },")

    camera = level_data.get("camera")
    if camera:
        lines.append(f"  camera = {{ bound_x = {camera['bound_x']}, bound_y = {camera['bound_y']} }},")
    else:
        bx = level_data["width"] * level_data["tile_size"]
        by = level_data["height"] * level_data["tile_size"]
        lines.append(f"  camera = {{ bound_x = {bx}, bound_y = {by} }},")

    parallax = level_data.get("parallax", {"bg": 0.25, "far": 0.5, "mid": 0.75})
    lines.append("  parallax = {")
    for k in ("bg", "far", "mid"):
        lines.append(f"    {k} = {parallax.get(k, 0.5)},")
    lines.append("  },")

    lines.append("  tiles = {")
    for row in level_data["tiles"]:
        lines.append(f"    {{ {','.join(str(t) for t in row)} }},")
    lines.append("  },")

    objects = level_data.get("objects", [])
    if objects:
        lines.append("  objects = {")
        for obj in objects:
            otype = obj["type"]
            ox = obj["x"]
            oy = obj["y"]
            if "params" in obj:
                params_str = ", ".join(f"{k} = {format_lua_value(v, 6)}" for k, v in obj["params"].items())
                lines.append(f"    {{ type = '{otype}', x = {ox}, y = {oy}, params = {{{params_str}}} }},")
            else:
                lines.append(f"    {{ type = '{otype}', x = {ox}, y = {oy} }},")
        lines.append("  },")

    lines.append("}")
    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser(description="Convert Tiled TMX to DKC2 Reforge Lua level")
    parser.add_argument("tmx", help="Path to .tmx file")
    parser.add_argument("-o", "--output", help="Output Lua file path")
    parser.add_argument("--tile-map", help="Tile mapping: gid1=gid2:type,... e.g. 1=1,2=2,3=3,4=4,5=5", default="1=1,2=2,3=3,4=4,5=5")
    parser.add_argument("--id", help="Level ID (e.g. 1-1). Default: derived from filename")
    parser.add_argument("--name", help="Level name. Default: derived from filename")
    parser.add_argument("--tile-size", type=int, default=16, help="Tile size in pixels (default: 16)")
    parser.add_argument("--parallax-bg", type=float, default=0.25)
    parser.add_argument("--parallax-far", type=float, default=0.5)
    parser.add_argument("--parallax-mid", type=float, default=0.75)

    args = parser.parse_args()

    # Parse tile map
    tile_map = {}
    for part in args.tile_map.split(","):
        if "=" in part:
            gid_str, lua_val = part.split("=", 1)
            tile_map[int(gid_str.strip())] = int(lua_val.strip())

    root = parse_tmx(args.tmx)
    attrs = get_map_attributes(root)

    base = os.path.splitext(os.path.basename(args.tmx))[0]
    level_id = args.id or base
    level_name = args.name or base.replace("_", " ").replace("-", " ").title()

    tiles = parse_tile_layer(root, tile_map)
    objects = parse_object_layer(root)
    props = get_custom_properties(root)

    # Extract spawn and camera from props or first object
    player_spawn = None
    camera = None
    filtered_objects = []
    for obj in objects:
        if obj["type"] == "player_spawn":
            player_spawn = obj
        else:
            filtered_objects.append(obj)

    camera_bounds = None
    if "camera_bound_x" in props:
        camera_bounds = {
            "bound_x": int(props["camera_bound_x"]),
            "bound_y": int(props.get("camera_bound_y", attrs["height"] * args.tile_size)),
        }

    level_data = {
        "id": level_id,
        "name": level_name,
        "width": attrs["width"],
        "height": attrs["height"],
        "tile_size": args.tile_size,
        "player_spawn": player_spawn or ({"x": 64, "y": 128} if "player_spawn" not in props else {"x": int(props["player_spawn_x"]), "y": int(props["player_spawn_y"])}),
        "camera": camera_bounds or {"bound_x": attrs["width"] * args.tile_size, "bound_y": attrs["height"] * args.tile_size},
        "parallax": {
            "bg": args.parallax_bg,
            "far": args.parallax_far,
            "mid": args.parallax_mid,
        },
        "tiles": tiles,
        "objects": filtered_objects,
    }

    lua_content = generate_lua(level_data)

    if args.output:
        os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(lua_content)
        print(f"Written: {args.output} ({len(tiles)} rows, {len(filtered_objects)} objects)")
    else:
        print(lua_content)


if __name__ == "__main__":
    main()
