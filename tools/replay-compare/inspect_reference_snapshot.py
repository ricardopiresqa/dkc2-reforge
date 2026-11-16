"""Inspect captured original RAM and compare decoder output without guessing."""
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
STAGE = ROOT / "assets-raw/pirate"


def word(data, offset):
    return int.from_bytes(data[offset:offset + 2], "little")


def inspect(rom_path=None):
    ram = (STAGE / "reference-wram.bin").read_bytes()
    assert len(ram) == 0x20000
    bank = ram[0x9A]
    base = word(ram, 0x98)
    defs = word(ram, 0x17B4)
    assert bank in (0x7E, 0x7F), "unexpected map source bank"
    start = (bank - 0x7E) * 0x10000
    decoded = (STAGE / "_decoded/map.bin").read_bytes()
    captured = ram[start + base:start + base + len(decoded)]
    room_size = defs - base
    room_prefix_equal = ram[start + base:start + defs] == decoded[:room_size]
    prefix = ram[start + base:start + defs]
    mismatches = [i for i, (a, b) in enumerate(zip(prefix, decoded)) if a != b]
    decoded_defs = (STAGE / "_decoded/defs.bin").read_bytes()
    captured_defs = ram[start + defs:start + defs + len(decoded_defs)]
    player = word(ram, 0x593)
    rom_path = Path(rom_path) if rom_path else ROOT / "roms/dkc2.sfc"
    rom = rom_path.read_bytes()
    payload = rom[512:] if len(rom) % 0x8000 == 512 else rom
    spawn_offset = 1 * 32 + 6 * 2
    spawn_tile = word(ram, start + base + spawn_offset) & 0x3FFF
    collision_offset = 0x3C6154 + spawn_tile * 4
    spawn_collision = [word(payload, collision_offset + half * 2) for half in (0, 1)]
    report = {
        "level": word(ram, 0xD3), "mode": word(ram, 0x24),
        "camera": [word(ram, 0x17BA), word(ram, 0x17C0)],
        "camera_max": [word(ram, 0xAFC), word(ram, 0xAFE)],
        "camera_mode": word(ram, 0x54F),
        "game_frame_counter": word(ram, 0x2A),
        "camera_parameters": {hex(a): word(ram, a) for a in range(0xA92, 0xB00, 2)},
        "camera_regions": [{"index": i, "left": word(ram, 0x8D28 + i * 2),
                            "right": word(ram, 0x8E28 + i * 2),
                            "top": word(ram, 0x8F28 + i * 2),
                            "bottom": word(ram, 0x9028 + i * 2),
                            "left_links": word(ram, 0x9228 + i * 2),
                            "top_links": word(ram, 0x9328 + i * 2),
                            "bottom_links": word(ram, 0x9428 + i * 2),
                            "flags": word(ram, 0x9128 + i * 2)}
                           for i in range(word(ram, 0xABA) // 2 + 1)],
        "player_raw": [word(ram, player + 6), word(ram, player + 10)],
        "map_bank": bank, "map_base": base, "defs_base": defs,
        "map_bytes_equal": captured == decoded,
        "main_room_map_bytes": room_size,
        "main_room_prefix_equal": room_prefix_equal,
        "first_map_mismatches": mismatches[:12],
        "map_probe_source_offset": decoded.find(prefix[64:320]) - 64,
        "map_header_words": [word(decoded, i) for i in range(0, 32, 2)],
        "main_room_header_skipped_equal": prefix == decoded[32:32 + room_size],
        "spawn_tile_id": spawn_tile,
        "spawn_collision_words": spawn_collision,
        "spawn_property_handlers": [word(payload, 0x35CA38 + (w & 255) * 2) for w in spawn_collision],
        "defs_bytes_equal": captured_defs == decoded_defs,
        "map_capture_sha256": hashlib.sha256(captured).hexdigest(),
        "map_decoder_sha256": hashlib.sha256(decoded).hexdigest(),
        "wram_sha256": hashlib.sha256(ram).hexdigest(),
        "rom_sha256": hashlib.sha256(payload).hexdigest(),
        "rom_file_sha256": hashlib.sha256(rom).hexdigest(),
        "rom_payload_bytes": len(payload),
        "rom_revision_header": payload[0xFFDB],
        "capture_script_sha256": hashlib.sha256((STAGE / "reference-capture-source.lua").read_bytes()).hexdigest()
        if (STAGE / "reference-capture-source.lua").exists() else None,
        "scope": "original frame 3000; not full route or proof of physics fidelity",
    }
    return report


if __name__ == "__main__":
    result = inspect(sys.argv[1] if len(sys.argv) > 1 else None)
    (STAGE / "reference-snapshot-report.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    regions = result["camera_regions"]
    lines = ["-- Static camera fork table copied from hash-verified original WRAM.",
             'return { rom_sha256 = "%s", wram_sha256 = "%s", x_max = %d, y_max = %d,' %
             (result["rom_sha256"], result["wram_sha256"], result["camera_max"][0], result["camera_max"][1]),
             "  regions = {"]
    for region in regions:
        lines.append("    {%d,%d,%d,%d,%d,%d,%d,%d,%d}," %
                     tuple(region[key] for key in ("left", "right", "top", "bottom", "flags",
                                                    "left_links", "top_links", "bottom_links", "index")))
    lines.extend(["  },", "}"])
    contents = "\n".join(lines)
    (STAGE / "camera_profile.lua").write_text(contents, encoding="utf-8")
    runtime_dir = ROOT / "data/original/pirate"
    runtime_dir.mkdir(parents=True, exist_ok=True)
    (runtime_dir / "camera_profile.lua").write_text(contents, encoding="utf-8")
    print(json.dumps(result, indent=2))
