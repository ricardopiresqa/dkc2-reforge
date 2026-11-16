"""Focused tests do importador Pirate Panic (layout + proveniencia, sem invencao)."""
import hashlib
import json
import os
import sys
from pathlib import Path

import pytest

TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
TOOLS_DIR = os.path.dirname(TESTS_DIR)
sys.path.insert(0, TOOLS_DIR)

import import_pirate_panic as ipp  # noqa: E402

try:
    from PIL import Image
except ImportError:  # pragma: no cover
    Image = None


def default_source():
    src = Path(TOOLS_DIR) / "vendor/DKC2-disasm/DKC2"
    manifest = src.parent.parent / "DKC2-disasm-manifest.json"
    return str(src) if src.is_dir() and manifest.is_file() else None


needs_disasm = pytest.mark.skipif(default_source() is None,
                                  reason="disassembly read-only ausente")


@pytest.fixture(scope="module")
def imported(tmp_path_factory):
    """Roda o pipeline uma unica vez para todos os testes."""
    src = default_source()
    if src is None:
        pytest.skip("disassembly read-only ausente")
    out = str(tmp_path_factory.mktemp("pirate") / "pirate")
    repo_root = ipp.REPO_DIR
    ipp_runtime_root = str(tmp_path_factory.mktemp("runtime"))
    try:
        # Runtime publication in tests must stay in the temporary workspace.
        ipp.REPO_DIR = ipp_runtime_root
        assert ipp.main(["--source", src, "--out", out]) == 0
    finally:
        ipp.REPO_DIR = repo_root
    man = json.load(open(os.path.join(out, "manifest.json"), encoding="utf-8"))
    return {"out": out, "manifest": man, "source": src,
            "runtime_root": ipp_runtime_root}


# ---------------------------------------------------------------------------
# CMP codec — vetores construidos pela semantica dos handlers originais
# ---------------------------------------------------------------------------

def _stream(header_tail, cmd_bytes):
    hdr = bytes(39)
    return hdr[:39] + bytes(cmd_bytes)


def test_cmp_literal_and_eof():
    # primario 0: lo=3 -> copia 3 bytes literais; primario 0 lo=0 -> EOF
    src = _stream(b"", [0x03, 0xAA, 0xBB, 0xCC, 0x00])
    assert ipp.cmp_decompress(src) == bytes([0xAA, 0xBB, 0xCC])


def test_cmp_fill_from_header():
    # header byte1 = $52 fill; primario 4 lo=1 -> 4 bytes de $52
    hdr = bytearray(39)
    hdr[1] = 0x52
    src = bytes(hdr) + bytes([0x41, 0x00])
    assert ipp.cmp_decompress(src) == bytes([0x52] * 4)


def test_cmp_backref_short():
    # literais AA BB CC, depois primario 9 lo=0 -> offset=2: copia BB CC
    src = _stream(b"", [0x03, 0xAA, 0xBB, 0xCC, 0x90, 0x00])
    assert ipp.cmp_decompress(src) == bytes([0xAA, 0xBB, 0xCC, 0xBB, 0xCC])


def test_cmp_stream_truncated_raises():
    with pytest.raises(ipp.CmpError):
        ipp.cmp_decompress(_stream(b"", [0x05]))


# ---------------------------------------------------------------------------
# Pipeline real (nivel decodificado + proveniencia)
# ---------------------------------------------------------------------------

@needs_disasm
def test_sprites_pipeline_rgba(imported):
    man = imported["manifest"]
    poses = [s["pose"] for s in man["sprites"]["rendered"]]
    for n in range(1, 14):
        assert "GFX_Diddy_Run%d.bin" % n in poses, "sem Run%d" % n
    assert any(p.startswith("GFX_Diddy_IdleSway") for p in poses), "sem Idle real"
    assert any(p.startswith("GFX_Diddy_Jump") for p in poses), "sem Jump"
    assert Image is not None
    for s in man["sprites"]["rendered"][:5]:
        img = Image.open(os.path.join(imported["out"], s["file"]))
        assert img.mode == "RGBA"
        assert img.width == s["w"] and img.height == s["h"]
        assert s["w"] > 0 and s["h"] > 0


@needs_disasm
def test_level_layout_proven(imported):
    level = imported["manifest"]["level"]
    assert level["status"] == "decoded-partial"

    # tiles: 918 tiles 4bpp (29376 = 918 x 32) — prova o codec
    assert level["tiles"]["count"] == 918
    assert level["tiles"]["bpp"] == 4

    # defs: 376 metatiles x 32B (12032B)
    assert level["defs"]["count"] == 376
    assert level["defs"]["entry_bytes"] == 32

    # mapa: grid coluna-major 16 linhas/coluna; IDs completos 0..375
    m = level["map"]
    assert m["layout"] == "column-major"
    assert m["rows"] == 16
    assert m["cols"] * 32 == m["width_px"]
    assert m["max_metatile_id"] <= 375
    assert m["distinct_ids"] == 376
    assert m["flip_flags"] == {"h": 0x4000, "v": 0x8000}

    # objetos: 55 registros x 8B + terminator 2B (442B)
    o = level["objects"]
    assert o["count"] == 55
    assert o["record_bytes"] == 8
    assert o["coord_bias"] == 0x100
    assert o["bbox"]["x_max"] > o["bbox"]["x_min"]

    # colisao: 170 entradas x 4B (DATA_FC6154..FC63FC)
    c = level["collision"]
    assert c["entries"] == 170
    assert c["budget"]


@needs_disasm
def test_provenance_hashes(imported):
    man = imported["manifest"]
    for prov in man["provenance"]:
        if prov["status"] == "recorded":
            assert prov["size"] > 0 and len(prov["sha256"]) == 64
    for probe in man["level"]["probes"]:
        if "src_sha256" in probe:
            assert len(probe["src_sha256"]) == 64
        if probe.get("result") == "cmp-decoded":
            assert probe["out_size"] > 0 and len(probe["out_sha256"]) == 64
    # fonte e a copia vendor do workspace (proveniencia auditavel)
    assert "vendor" in man["source_root"].replace("/", "\\").lower()
    if "rom_sha256" in man["level"]:
        assert len(man["level"]["rom_sha256"]) == 64
    # hashes dos arquivos vendor registrados no manifest da copia
    vendor_manifest = os.path.normpath(os.path.join(
        imported["source"], "..", "..", "DKC2-disasm-manifest.json"))
    assert os.path.exists(vendor_manifest), "manifest vendor ausente"


@needs_disasm
def test_render_outputs(imported):
    assert Image is not None
    out = imported["out"]
    level = imported["manifest"]["level"]
    sheet = Image.open(os.path.join(out, level["tiles"]["sheet_png"]))
    assert sheet.width == 32 * 8 and sheet.height >= 29 * 8
    colors = sheet.getcolors(maxcolors=1 << 16)
    assert colors and len(colors) > 2, "sheet monocromatico = decode quebrado"

    render = Image.open(os.path.join(out, level["map"]["render_png"]))
    assert render.width == level["map"]["width_px"]
    assert render.height == level["map"]["height_px"]
    colors = render.getcolors(maxcolors=1 << 16)
    assert colors and len(colors) > 16, "mapa monocromatico = decode quebrado"


@needs_disasm
def test_no_invention(imported):
    level = imported["manifest"]["level"]
    # spawn: unproven/proven/derived (derived exige registro de origem)
    assert level["spawn"]["status"] in ("unproven", "proven", "derived")
    if level["spawn"]["status"] == "unproven":
        assert level["spawn"]["note"]
    if level["spawn"]["status"] == "derived":
        assert level["spawn"]["record"] and level["spawn"]["record"]["source"]
    assert len(level["delta"]) >= 1, "delta especifico obrigatorio"
    hyps = {h["id"]: h for h in level["hypotheses"]}
    assert {"H1", "H2", "H3", "H4", "H5", "H6"} <= set(hyps)
    for h in hyps.values():
        assert h["result"] in ("PROVADO", "REFUTADO", "INCONCLUSIVO",
                               "VALIDADO")
        assert h["evidence"]
    # schema declarado no manifest
    schema = imported["manifest"]["schema"]
    assert schema["version"] == 1
    assert "level.map" in schema and "level.spawn" in schema
    assert "level.collision_map" in schema and "level.limits" in schema


# ---------------------------------------------------------------------------
# header/spawn/limites + colisao + entidades (fase 1 Pirate Panic)
# ---------------------------------------------------------------------------

@needs_disasm
def test_header_records_parsed_from_rom(imported):
    level = imported["manifest"]["level"]
    recs = level["header_records"]["records"]
    assert len(recs) == 7, "header DATA_FD4C8A: 7 registros ate flags=$FF"
    # bias declarado e aplicado
    assert level["header_records"]["bias"] == {"x": 256, "feet_y": 256}
    for r in recs:
        assert r["x"] == r["x_raw"] - 256
        assert r["feet_y"] == r["y_raw"] - 256
    # flags $40 = posicoes de BarrelCannon (objetos 32/41/51) -- prova H6
    objs = level["objects"]["items"]
    cannon = [r for r in recs if r["flags"] == 0x40]
    assert len(cannon) == 3
    by_xy = {(o["x"], o["feet_y"]) for o in objs}
    for r in cannon:
        assert (r["x"], r["feet_y"]) in by_xy


@needs_disasm
def test_spawn_and_limits_from_header(imported):
    level = imported["manifest"]["level"]
    sp = level["spawn"]
    assert sp["status"] == "derived"
    assert sp["x"] == 48 and sp["feet_y"] == 209
    assert sp["goal"] and sp["goal"]["x"] > sp["x"]
    lim = level["limits"]
    # limites vem do header, nao do bbox dos objetos
    assert lim["x_min"] == 0
    assert lim["x_max"] % 32 == 0
    assert lim["x_max"] >= sp["goal"]["x"]
    assert lim["y_max"] == 512
    assert "header" in lim["source"] or lim["status"] == "captured-byte-verified"
    bbox = level["objects"]["bbox"]
    assert lim["x_max"] >= bbox["x_max"], "objetos dentro dos limites"


@needs_disasm
def test_collision_property_mapping_budget(imported):
    level = imported["manifest"]["level"]
    cm = level["collision_map"]
    assert cm["budget"] == 170
    assert len(cm["entries"]) == 170
    # ID 0 = ar (sem colisao nas duas sub-colunas)
    assert cm["entries"][0]["left"] == 0 and cm["entries"][0]["right"] == 0
    assert cm["entries"][0]["left_class"] == 0
    # regra derivada aplicada
    for e in cm["entries"]:
        assert e["left_class"] in (0, 1, 2)
        assert e["right_class"] in (0, 1, 2)
        if e["left"] == 0:
            assert e["left_class"] == 0
    # grade coerente com o budget
    g = level["collision_grid"]
    assert g["cols"] * 16 == level["limits"]["x_max"]
    assert g["rows"] == 32 and g["tile_px"] == 16
    # RLE faz round-trip: decodifica de volta ao tamanho exato da grade
    flat = ipp.decode_rle(g["rle"])
    assert len(flat) == g["cols"] * g["rows"]
    assert set(flat) <= {0, 1, 2}
    assert any(v != 0 for v in flat), "grade vazia = colisao nao exportada"


@needs_disasm
def test_entities_resolved_via_spawn_scripts(imported):
    level = imported["manifest"]["level"]
    items = level["objects"]["items"]
    assert len(items) == 55
    named = [o for o in items if o.get("sprite_name")]
    assert len(named) == 55, "todo objeto resolve SpriteID via spawn script"
    # nomes reais do enum SpriteID (prova H5)
    names = {o["sprite_name"] for o in items}
    assert "Neek" in names and "Klomp" in names
    assert "DKBarrel" in names or "WoodenBox" in names
    # LevelEndGoal marca o fim da fase
    assert any(o["sprite_name"] == "LevelEndGoal" for o in items)


@needs_disasm
def test_runtime_module_and_chunks(imported):
    assert Image is not None
    out = imported["out"]
    level = imported["manifest"]["level"]
    rt = level["runtime"]
    expected_chunks = (level["limits"]["x_max"] + 511) // 512
    assert rt["chunks"] == expected_chunks
    assert rt["diddy_frames"] == imported["manifest"]["sprites"]["count"]
    assert rt["diddy_frames"] > 70  # original long-idle juggling referenced by ROM script
    mod = os.path.join(out, "pirate_panic_level.lua")
    assert os.path.exists(mod)
    txt = open(mod, encoding="utf-8").read()
    assert "original_semantics = true" in txt
    assert "grid_rle" in txt and "spawn = { x = 48, feet_y = 209 }" in txt
    assert "LevelEndGoal" in txt
    # chunks <= 512W
    cdir = os.path.join(out, "chunks")
    files = [f for f in os.listdir(cdir) if f.endswith(".png")]
    assert len(files) == expected_chunks
    for f in files:
        im = Image.open(os.path.join(cdir, f))
        assert im.width <= 512


@needs_disasm
def test_lua_data_file_for_tifa(imported):
    lua = open(os.path.join(imported["out"], "pirate_panic.lua"),
               encoding="utf-8").read()
    assert "GFX_Diddy_Run1" in lua
    assert "decoded-partial" in lua
    assert "_decoded/map.bin" in lua
    assert "coord_bias = 256" in lua
    assert "collision" in lua


@needs_disasm
def test_atlas_uses_project_relative_resources(imported):
    import re
    text = open(os.path.join(imported["runtime_root"], "main", "game.atlas"),
                encoding="utf-8").read()
    paths = re.findall(r'image: "([^"]+)"', text)
    assert paths and all(p.startswith("/assets/") for p in paths)
    assert all(":" not in p and "\\" not in p for p in paths)


@needs_disasm
def test_original_enemy_graphics_and_transparency(imported):
    assert Image is not None
    graphics = imported["manifest"]["level"]["runtime"]["enemy_graphics"]
    by_sprite = {g["sprite"]: g for g in graphics}
    assert by_sprite["Neek"]["frames"] == 8
    assert by_sprite["Klomp"]["frames"] == 9
    assert all(g["timing_status"] == "unverified" for g in graphics)
    assert all(len(g["gfx_sha256"]) == g["frames"] for g in graphics)
    chunk = Image.open(os.path.join(imported["out"], "chunks", "levelchunk000.png"))
    assert chunk.mode == "RGBA"
    assert chunk.getchannel("A").getextrema() == (0, 255)


@needs_disasm
def test_diddy_frames_preserve_original_oam_origin(imported):
    assert Image is not None
    import gfx_assemble
    gfx_assemble.MACROS = os.path.join(imported["source"], "Routine_Macros_DKC2.asm")
    poses = gfx_assemble.load_poses()
    anchor = imported["manifest"]["level"]["runtime"]["diddy_anchor"]
    for index in (1, 7, 13):
        name = "GFX_Diddy_Run%d.bin" % index
        parts = gfx_assemble.build_pieces(poses[name])
        assert parts is not None
        x0 = min(p[0] for p in parts) - 6
        y0 = min(p[1] for p in parts) - 6
        original = Image.open(os.path.join(imported["out"], "sprites", name + ".png"))
        emitted = Image.open(os.path.join(imported["runtime_root"], "assets", "images",
                                         "pirate", "diddy", "diddy_run_%02d.png" % index))
        left, top = anchor["x"] + x0, anchor["y"] + y0
        assert 0 <= left and 0 <= top
        assert emitted.size == (anchor["canvas_w"], anchor["canvas_h"])
        assert emitted.crop((left, top, left + original.width, top + original.height)).tobytes() == original.tobytes()


def test_player_renderer_uses_original_graphics():
    from pathlib import Path
    renderer = Path(TOOLS_DIR).parent / "main" / "renderer.lua"
    text = renderer.read_text(encoding="utf-8")
    start = text.index("local function draw_player")
    assert 'anim = "diddy_run"' in text[start:]
    assert 'anim = "diddy_jump"' in text[start:]
    assert "image_height * 0.5" in text[start:]


def test_pipeline_never_deletes_existing_artifacts():
    from pathlib import Path
    text = Path(ipp.__file__).read_text(encoding="utf-8")
    assert "os.remove(" not in text


def test_input_previous_state_survives_pre_update_callbacks():
    from pathlib import Path
    text = (Path(TOOLS_DIR).parent / "main/input.lua").read_text(encoding="utf-8")
    update_body = text.split("function M.update()", 1)[1].split("\nend", 1)[0]
    post_body = text.split("function M.post_update()", 1)[1].split("\nend", 1)[0]
    assert "prev_hold = hold" not in update_body
    assert post_body.index("edge = bit.band") < post_body.index("prev_hold = hold")


def test_native_projection_is_not_widescreen():
    from pathlib import Path
    import configparser
    root = Path(TOOLS_DIR).parent
    project = configparser.ConfigParser()
    project.read(root / "game.project", encoding="utf-8")
    assert project.getint("display", "width") == 1024
    assert project.getint("display", "height") == 896
    assert project.getint("display", "high_dpi") == 0
    assert project.get("bootstrap", "render") == "/main/native.renderc"
    assert project.get("graphics", "default_texture_mag_filter") == "nearest"
    assert project.getint("display", "width") // 256 == project.getint("display", "height") // 224
    renderer = (root / "main/native.render_script").read_text(encoding="utf-8")
    assert "local WIDTH, HEIGHT = 256, 224" in renderer
    assert "graphics.BUFFER_TYPE_COLOR0_BIT" in renderer
    assert "render.BUFFER_COLOR_BIT" not in renderer


def test_original_unresolved_scripts_are_not_fake_gameplay():
    from pathlib import Path
    import re
    text = (Path(TOOLS_DIR).parent / "data/levels/level_1_1.lua").read_text(encoding="utf-8")
    assert not re.search(r'BarrelCannon\s*=\s*"bonus_barrel"', text)
    assert not re.search(r'NoAnimalBuddySign\s*=\s*"rope"', text)
    assert not re.search(r'UnknownSprite0084\s*=\s*"banana"', text)
    assert not re.search(r'KleeverPieces4\s*=\s*"krusha"', text)
    assert re.search(r'Klobber\s*=\s*"original_static"', text)
    assert re.search(r'WoodenBox\s*=\s*"original_static"', text)
    assert re.search(r'KongLetters\s*=\s*"original_static"', text)
    objects = (Path(TOOLS_DIR).parent / "main/objects.lua").read_text(encoding="utf-8")
    assert "OBJ_ORIGINAL_STATIC = 31" in objects


def test_original_simulation_tick_keeps_real_dt_metrics_separate():
    from pathlib import Path
    game = (Path(TOOLS_DIR).parent / "main/game.lua").read_text(encoding="utf-8")
    body = game.split("function M.update(dt)", 1)[1]
    assert body.index("perf.note_dt(dt)") < body.index("dt = 1 / 60") < body.index("player.update(dt)")


@needs_disasm
def test_original_half_height_floor_uses_original_handler(imported):
    rom = open(os.path.join(imported["source"], "Donkey Kong Country 2 (USA V1.0).sfc"), "rb").read()
    assert ipp.constant_collision_height(5, rom) == 15  # DATA_B5CA38[5] -> CODE_B5CC00
    assert ipp.constant_collision_height(1, rom) == 31
    assert ipp.constant_collision_height(0, rom) == -1
    assert ipp.constant_collision_height(0x4005, rom) == -2
    surfaces = imported["manifest"]["level"]["flat_surfaces"]
    assert ipp.execute_collision_handler(12, 0, rom) == 12
    assert ipp.execute_collision_handler(12, 7, rom) == 13
    assert ipp.execute_collision_handler(12, 15, rom) == 15
    assert [ipp.execute_collision_handler(54, x, rom) for x in range(12)] == [-1] * 12
    assert [ipp.execute_collision_handler(54, x, rom) for x in range(12, 16)] == [0, 4, 8, 12]
    assert ipp.execute_collision_handler(255, 0, rom) == -1
    assert ipp.execute_collision_handler(80, 0, rom) == -1  # outside source handler table: no handler
    assert surfaces["status"] == "source-bytecode-subset"
    assert surfaces["unknown_cells"] == 0
    heights = ipp.decode_rle(surfaces["rle"])
    assert surfaces["cols"] == 7104  # one original world pixel per surface sample
    assert heights[6 * surfaces["cols"] + 48] == 15  # observed Pirate Panic spawn
    assert heights[6 * surfaces["cols"] + 3503] == 15  # adjacent flat floor, property5
    assert heights[6 * surfaces["cols"] + 3520] == 15  # slope property12, flipped left edge
    assert heights[6 * surfaces["cols"] + 3527] == 14
    assert heights[6 * surfaces["cols"] + 3535] == 12
    assert heights[6 * surfaces["cols"] + 3536] == 12  # same metatile, right half
    assert 6 * 32 + 32 - heights[6 * surfaces["cols"] + 3535] == 212
    fixture = (Path(TOOLS_DIR).parent / "main/test/collision_check.lua").read_text(encoding="utf-8")
    assert "1px original ramp was misclassified as wall" in fixture


@needs_disasm
def test_native_hv_flip_bits_do_not_turn_collision_into_unknown(imported):
    rom = open(os.path.join(imported["source"], "Donkey Kong Country 2 (USA V1.0).sfc"), "rb").read()
    props = ipp.collision_property_map(rom)

    def profile(word):
        raw = bytearray(ipp.MAP_COL_BYTES)
        raw[6 * 2:6 * 2 + 2] = word.to_bytes(2, "little")
        return ipp.build_flat_surfaces(bytes(raw), props, rom, max_cols=1)

    normal = profile(50)
    vertical = profile(0x8000 | 50)
    horizontal = profile(0x4000 | 50)
    both = profile(0xC000 | 50)
    assert normal["unknown_cells"] == vertical["unknown_cells"] == 0
    assert horizontal["unknown_cells"] == both["unknown_cells"] == 0
    heights = lambda item: ipp.decode_rle(item["rle"])
    n, v, h, hv = map(heights, (normal, vertical, horizontal, both))
    assert n == v and h == hv
    assert h[6 * 32:7 * 32] == list(reversed(n[6 * 32:7 * 32]))


def test_runtime_collision_unit_fixture_uses_pixel_column_coordinates():
    from pathlib import Path
    test_source = (Path(TOOLS_DIR).parent / "main/test/collision_check.lua").read_text(encoding="utf-8")
    assert "cols = 16, rows = 7" in test_source
    assert "heights[6 * 16 + column + 1] = 15" in test_source


@needs_disasm
def test_room_boundaries_do_not_claim_proven_fidelity(imported):
    level = imported["manifest"]["level"]
    assert level["limits"]["status"] in ("estimated", "captured-byte-verified")
    if level["limits"]["status"] == "captured-byte-verified":
        assert level["main_room"]["bytes"] == 7136
        assert level["main_room"]["source_offset"] == 32
        assert level["limits"]["x_max"] == 7104


@needs_disasm
def test_pirate_panic_subarea_objects_keep_source_ids_and_partial_status(imported):
    from pathlib import Path
    level = imported["manifest"]["level"]
    areas = level["subareas"]
    assert {name: areas[name]["level_id"] for name in areas} == {
        "captains_kabin": 0x1B,
        "bonus_1": 0x6F,
        "bonus_2": 0x70,
        "warp": 0x1D,
    }
    assert {name: areas[name]["count"] for name in areas} == {
        "captains_kabin": 5,
        "bonus_1": 3,
        "bonus_2": 10,
        "warp": 1,
    }
    assert all("objects-only" in area["status"] for area in areas.values())
    assert any(o["sprite_name"] == "Rattly" for o in areas["bonus_2"]["objects"])
    assert any(o["sprite_name"] == "Coins" for o in areas["bonus_1"]["objects"])

    expected_headers = {
        "captains_kabin": (0x51B5, 3, (2, 208, 192), [12, 112, 0xFFFF]),
        "bonus_1": (0x56D8, 1, (0, 44, 465), [12, 0xFFFF]),
        "bonus_2": (0x56F2, 1, (0, 44, 209), [12, 0xFFFF]),
        "warp": (0x51F5, 3, (0, 64, 465), [5, 0xFFFF]),
    }
    for name, (pointer, count, first_record, post_words) in expected_headers.items():
        header = areas[name]["header"]
        assert header["status"] == "source-codec-supported"
        assert header["pointer"] == pointer and header["header_type"] == 1
        assert header["record_offset"] == 12
        assert len(header["records"]) == count
        first = header["records"][0]
        assert (first["flags"], first["x"], first["feet_y"]) == first_record
        assert header["post_record_words"] == post_words

    main_header = ipp.parse_level_header(
        (Path(imported["source"]) / "Donkey Kong Country 2 (USA V1.0).sfc").read_bytes(), 3)
    assert main_header["pointer"] == 0x4C8A
    assert main_header["header_type"] == 0
    assert main_header["record_offset"] == 11
    assert main_header["records"] == level["header_records"]["records"]
    assert main_header["post_record_words"] == [12, 0x1B, 0x6F, 0x70, 0x1D, 0xFFFF]

    runtime = (Path(imported["runtime_root"]) / "data/original/pirate"
               / "pirate_panic_level.lua").read_text(encoding="utf-8")
    assert "captains_kabin = { level_id = 27" in runtime
    assert "bonus_1 = { level_id = 111" in runtime
    assert "bonus_2 = { level_id = 112" in runtime
    assert "warp = { level_id = 29" in runtime
    assert "header_type = 1" in runtime
    assert "post_record_words = { 12, 112, 65535 }" in runtime
    assert "room map and collision not decoded" in runtime


@needs_disasm
def test_captains_kabin_assets_decode_without_geometry_claims(imported):
    from pathlib import Path

    area = imported["manifest"]["level"]["subareas"]["captains_kabin"]
    assets = area["assets"]
    assert assets["status"] == "source-assets-extracted; room layout/collision unproven"
    expected = {
        "layer1_tilemap": ("Tilemaps/Compressed/Layer1_Level_KaptainsKabin.bin",
                           "cmp", 1792),
        "layer1_gfx": ("Graphics/Compressed/GFX_Layer1_Level_KaptainsKabin.bin",
                       "cmp", 21024),
        "palette": ("Palettes/FGBG_Level_KaptainsKabin.bin", "raw", 256),
    }
    for name, (rel, codec, size) in expected.items():
        entry = assets["files"][name]
        source = (Path(imported["source"]) / rel).read_bytes()
        decoded = (ipp.cmp_decompress(source) if codec == "cmp" else source)
        output = (Path(imported["out"]) / entry["decoded_file"]).read_bytes()
        assert output == decoded
        assert len(output) == size
        assert entry["source_sha256"] == hashlib.sha256(source).hexdigest()
        assert entry["decoded_sha256"] == hashlib.sha256(output).hexdigest()
        assert entry["status"] == ("decoded" if codec == "cmp" else "copied-raw")
    assert not {"width_px", "height_px", "collision", "room_bounds"} & set(assets)


def test_bad_source_clean_exit(tmp_path):
    rc = ipp.main(["--source", str(tmp_path / "nope"),
                   "--out", str(tmp_path / "pirate")])
    assert rc == 2
