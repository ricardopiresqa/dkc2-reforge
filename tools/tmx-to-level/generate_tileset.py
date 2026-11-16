"""Generate placeholder tileset PNG for Tiled level editor.

Output: 16x16 tiles, 5 columns x 1 row.
  Tile 1 (solid)    = #5c4033 brown
  Tile 2 (platform) = #4a7c3f green
  Tile 3 (spike)    = #cc3333 red
  Tile 4 (slip)     = #3b7dbd blue
  Tile 5 (exit)     = #f0c040 gold
"""

import struct
import zlib
import sys

TILE_SIZE = 16
TILES = [
    None,  # 0 = empty (not in tileset)
    {"r": 92,  "g": 64,  "b": 51,  "label": "solid"},       # 1
    {"r": 74,  "g": 124, "b": 63,  "label": "platform"},     # 2
    {"r": 204, "g": 51,  "b": 51,  "label": "spike"},        # 3
    {"r": 59,  "g": 125, "b": 189, "label": "slippery"},     # 4
    {"r": 0,   "g": 160, "b": 200, "label": "water"},        # 5
    {"r": 240, "g": 192, "b": 64,  "label": "exit"},         # 6
]


def create_png(width, height, pixels):
    def write_chunk(chunk_type, data):
        raw = chunk_type + data
        return struct.pack(">I", len(data)) + raw + struct.pack(">I", zlib.crc32(raw) & 0xFFFFFFFF)

    header = b"\x89PNG\r\n\x1a\n"
    ihdr = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    header += write_chunk(b"IHDR", ihdr)

    raw_data = b""
    for y in range(height):
        raw_data += b"\x00"  # filter byte
        for x in range(width):
            idx = y * width + x
            raw_data += bytes(pixels[idx])

    header += write_chunk(b"IDAT", zlib.compress(raw_data))

    iend = write_chunk(b"IEND", b"")
    header += iend
    return header


def main():
    num_tiles = 6
    width = num_tiles * TILE_SIZE
    height = TILE_SIZE
    pixels = []

    for tile_id in range(1, num_tiles + 1):
        t = TILES[tile_id]
        for _ in range(TILE_SIZE * TILE_SIZE):
            pixels.append((t["r"], t["g"], t["b"]))

    png_data = create_png(width, height, pixels)

    # Add border lines between tiles for visual clarity
    pixels2 = []
    for tile_id in range(1, num_tiles + 1):
        t = TILES[tile_id]
        for py in range(TILE_SIZE):
            for px in range(TILE_SIZE):
                if px == 0 or px == TILE_SIZE - 1 or py == 0 or py == TILE_SIZE - 1:
                    pixels2.append((40, 40, 40))
                else:
                    pixels2.append((t["r"], t["g"], t["b"]))

    png_data2 = create_png(width, height, pixels2)

    outpath = "tileset_placeholder.png"
    with open(outpath, "wb") as f:
        f.write(png_data2)
    engine_types = {1:1, 2:2, 3:3, 4:4, 5:5, 6:0}
    print(f"Generated {outpath} ({width}x{height}, {num_tiles} tiles)")
    print("Tile mapping:")
    for tid in range(1, num_tiles + 1):
        t = TILES[tid]
        etype = engine_types[tid]
        print(f"  GID {tid} -> tile_type {etype} ({t['label']})")


if __name__ == "__main__":
    main()
