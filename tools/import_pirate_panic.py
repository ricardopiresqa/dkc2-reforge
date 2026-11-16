"""Importador Pirate Panic (1-1) a partir da disassembly read-only.

Le a disassembly (`--source`, nunca escreve nela) e gera em `--out`
(estagio `assets-raw/pirate/`, git-ignorado):

  sprites/Diddy_*.png   poses RGBA 1x do Diddy via gfx_assemble.render_pose
                        (nomes reais: GFX_Diddy_IdleSwayN, Run1-13, Jump1-13)
  palette_fgbg_piratepanic.png  swatch da paleta FGBG (BGR555 -> RGB, provado)
  pirate_panic.lua      data file Lua (contrato com runtime Tifa: o wrapper
                        data/levels/level_1_1.lua e escrito pela Tifa)
  manifest.json         provenance completa (path/size/sha256), dimensoes dos
                        PNGs e status do nivel

Mapas/colisao das areas especiais nao estao interpretados. Os assets visuais
brutos da Captain's Cabin sao apenas copiados/decodificados com provenance;
isso nao prova layout, limites ou colisao. O importador registra lacunas em vez
de inventar dados.

Uso:
    python tools/import_pirate_panic.py --source C:\\Projetos\\DKC2-disasm\\DKC2
    python tools/import_pirate_panic.py --source tools/vendor/DKC2-disasm/DKC2
"""

import argparse
import hashlib
import importlib.util
import json
import os
import re
import struct
import sys
from datetime import datetime, timezone

TOOLS_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_DIR = os.path.dirname(TOOLS_DIR)
sys.path.insert(0, TOOLS_DIR)

from gfx_assemble import build_pieces, load_poses, render_pose  # noqa: E402
from gfx_convert import decode_tile, encode_tile, load_palette  # noqa: E402

try:
    from PIL import Image
except ImportError:  # pragma: no cover
    sys.exit("Pillow nao instalado: pip install pillow")

DEFAULT_SOURCES = (
    os.path.join(REPO_DIR, "tools", "vendor", "DKC2-disasm", "DKC2"),
    os.environ.get("DKC2_DISASM") or "",
    r"C:\Projetos\DKC2-disasm\DKC2",
)

# poses Diddy exportadas (nomes reais da disassembly)
POSE_PREFIXES = ("GFX_Diddy_IdleSway", "GFX_Diddy_Walk", "GFX_Diddy_Run", "GFX_Diddy_Jump", "GFX_Diddy_Fall", "GFX_Diddy_Land", "GFX_Diddy_Juggling")

# arquivos de nivel com papel declarado (nada aqui e decodificado sem prova)
LEVEL_SOURCES = (
    ("LevelData/ShipDeckLevels.bin", "collision/layout"),
    ("LevelData/SpriteData/PiratePanic_Main.bin", "objects"),
    ("LevelData/SpriteData/PiratePanic_KaptainsKabin.bin", "subarea-objects"),
    ("LevelData/SpriteData/PiratePanic_Bonus1.bin", "subarea-objects"),
    ("LevelData/SpriteData/PiratePanic_Bonus2.bin", "subarea-objects"),
    ("LevelData/SpriteData/PiratePanic_Warp.bin", "subarea-objects"),
    ("LevelData/BananaFormations/PiratePanic_Main.bin", "objects/bananas"),
    ("Graphics/Compressed/GFX_Layer1_Level_ShipDeck.bin", "gfx-compressed"),
    ("Graphics/Compressed/GFX_Layer2_Level_ShipDeck.bin", "gfx-compressed"),
    ("Tilemaps/Map32/Layer1_Level_ShipDeck.bin", "tilemap"),
    ("Tilemaps/Compressed/Layer2_Level_ShipDeck.bin", "tilemap-compressed"),
    ("Tilemaps/Layer3_ShipDeck.bin", "tilemap-l3"),
    ("Palettes/FGBG_Level_PiratePanic.bin", "palette-fgbg"),
)

PIRATE_PANIC_SUBAREAS = (
    ("captains_kabin", "PiratePanic_KaptainsKabin"),
    ("bonus_1", "PiratePanic_Bonus1"),
    ("bonus_2", "PiratePanic_Bonus2"),
    ("warp", "PiratePanic_Warp"),
)

CAPTAINS_KABIN_ASSETS = (
    ("layer1_tilemap", "Tilemaps/Compressed/Layer1_Level_KaptainsKabin.bin", "cmp"),
    ("layer1_gfx", "Graphics/Compressed/GFX_Layer1_Level_KaptainsKabin.bin", "cmp"),
    ("palette", "Palettes/FGBG_Level_KaptainsKabin.bin", "raw"),
)


def resolve_source(cli):
    if cli:
        cands = [cli]
    else:
        cands = [c for c in DEFAULT_SOURCES if c]
    tried = []
    for c in cands:
        tried.append(c)
        if c and os.path.isdir(c):
            return c, (("cli" if cli else "default") + ":" + c)
    return None, "tried:" + ";".join(tried)


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def natural_key(name):
    return [int(t) if t.isdigit() else t for t in re.split(r"(\d+)", name)]


def select_poses(poses, gfxdir):
    """Nomes reais da disassembly, so os com .bin presente e pose montavel."""
    names = [n for n in poses
             if n.startswith(POSE_PREFIXES)
             and os.path.exists(os.path.join(gfxdir, n))]
    names.sort(key=natural_key)
    ok, skipped = [], []
    for n in names:
        if build_pieces(poses[n]) is None:
            skipped.append({"pose": n, "reason": "pose truncada (header OAM incompleto)"})
        else:
            ok.append(n)
    return ok, skipped


def decode_bgr555_word(v):
    return ((v & 0x1F) * 255 // 31,
            ((v >> 5) & 0x1F) * 255 // 31,
            ((v >> 10) & 0x1F) * 255 // 31)


# ---------------------------------------------------------------------------
# Descompressor original DKC2 (CMP) — port byte-a-byte de
# Routine_Macros_DKC2.asm: CODE_BB8D91/8D9E (entrada), jump table
# CODE_BB8000..8040+, handlers CODE_BB8E2A..BB9190, LUT CODE_BB91AF.
# Header 39 bytes; cmds a partir de $27. EOF: primario 0 com lo=0
# (CODE_BB8E2A) ou secundario 0 com b>>4==0 (CODE_BB8E6F).
# Apos todo dispatch o carry e 0 (LSR/ADC da tabela), portanto as
# contagens `ADC #$03` somam exatamente o imediato.
# ---------------------------------------------------------------------------

_EOF = object()


class CmpError(ValueError):
    pass


def _lut_lo(b):
    return b >> 4          # CODE_BB91C9


def _lut_hi(b):
    return (b & 0x0F) << 4  # CODE_BB91B6


def cmp_decompress(src, max_out=1 << 22):
    """Decodifica um stream CMP (como CODE_BB8D9E faz com ROM->WRAM)."""
    if len(src) < 39:
        raise CmpError("stream menor que o header de 39 bytes")
    fill52, fill53, b56, b57 = src[1], src[2], src[3], src[4]
    word54 = src[5] | (src[6] << 8)
    pool = [src[7 + i * 2] | (src[8 + i * 2] << 8) for i in range(16)]

    out = bytearray()
    pos = 39

    def rd():
        nonlocal pos
        if pos >= len(src):
            raise CmpError("stream truncado em %d" % pos)
        b = src[pos]
        pos += 1
        return b

    def emit(bs):
        out.extend(bs)
        if len(out) > max_out:
            raise CmpError("saida excedeu max_out")

    def copy_back(count, offset):
        if offset <= 0:
            raise CmpError("backref com offset %d" % offset)
        start = len(out) - offset
        if start < 0:
            raise CmpError("backref antes do inicio da saida")
        for i in range(count):
            out.append(out[start + i])

    # secundarios (stub table CODE_BB8040+)
    def sec_0():                       # CODE_BB8E6F
        b1 = rd()
        count = _lut_lo(b1)
        if count == 0:
            return _EOF
        cur = b1
        for _ in range(count):
            hi = _lut_hi(cur)
            cur = rd()
            emit(bytes([hi | _lut_lo(cur)]))
        return ("sec", cur)

    def sec_1():                       # CODE_BB8EAA
        emit(bytes([rd()]))
        return "cmd"

    def sec_2():                       # CODE_BB8EDB
        emit(bytes([rd(), rd()]))
        return "cmd"

    def sec_3():                       # CODE_BB8F01
        b1 = rd()
        count = _lut_lo(b1) + 3
        b2 = rd()
        emit(bytes([_lut_hi(b1) | _lut_lo(b2)]) * count)
        return ("sec", b2)

    def sec_4():                       # CODE_BB8F3B
        b = rd()
        emit(bytes([fill52]) * (_lut_lo(b) + 3))
        return ("sec", b)

    def sec_5():                       # CODE_BB8F68
        b = rd()
        emit(bytes([fill53]) * (_lut_lo(b) + 3))
        return ("sec", b)

    def sec_6():                       # CODE_BB8F8E
        emit(bytes([word54 & 0xFF, word54 >> 8]))
        return "cmd"

    def sec_7():                       # CODE_BB8FA5
        emit(bytes([b56]))
        return "cmd"

    def sec_8():                       # CODE_BB8FB7
        emit(bytes([b57]))
        return "cmd"

    def sec_9():                       # CODE_BB8FDE
        b = rd()
        copy_back(2, _lut_lo(b) + 2)
        return ("sec", b)

    def sec_a():                       # CODE_BB9029
        b1 = rd()
        count = _lut_lo(b1) + 3
        b2 = rd()
        copy_back(count, count + (_lut_hi(b1) | _lut_lo(b2)))
        return ("sec", b2)

    def sec_b():                       # CODE_BB9097
        b1 = rd()
        count = _lut_lo(b1) + 3
        b2 = rd()
        copy_back(count, ((b1 & 0x0F) << 8 | b2) + 0x103)
        return "cmd"

    def sec_c():                       # CODE_BB90F2
        b1 = rd()
        count = _lut_lo(b1) + 3
        b2 = rd()
        b3 = rd()
        copy_back(count, (((b1 << 8 | b2) << 4) & 0xFFFF) | _lut_lo(b3))
        return ("sec", b3)

    def sec_d():                       # CODE_BB9144
        if not out:
            raise CmpError("sec_d sem historico")
        emit(bytes([out[-1]]))
        return "cmd"

    def sec_e():                       # CODE_BB9163
        if len(out) < 2:
            raise CmpError("sec_e sem historico")
        emit(bytes([out[-2], out[-1]]))
        return "cmd"

    def sec_f():                       # CODE_BB9190
        b = rd()
        w = pool[_lut_lo(b)]
        emit(bytes([w & 0xFF, w >> 8]))
        return ("sec", b)

    SEC = [sec_0, sec_1, sec_2, sec_3, sec_4, sec_5, sec_6, sec_7,
           sec_8, sec_9, sec_a, sec_b, sec_c, sec_d, sec_e, sec_f]

    # primarios (stub table CODE_BB8000+)
    def pri_0(lo):                     # CODE_BB8E2A
        if lo == 0:
            return _EOF
        emit(bytes(rd() for _ in range(lo)))
        return "cmd"

    def pri_1(lo):                     # CODE_BB8E96
        b1 = rd()
        emit(bytes([(lo << 4) | _lut_lo(b1)]))
        return ("sec", b1)

    def pri_2(lo):                     # CODE_BB8EB4
        b1 = rd()
        emit(bytes([(lo << 4) | _lut_lo(b1)]))
        b2 = rd()
        emit(bytes([_lut_hi(b1) | _lut_lo(b2)]))
        return ("sec", b2)

    def pri_3(lo):                     # CODE_BB8EEB
        emit(bytes([rd()]) * (lo + 3))
        return "cmd"

    def pri_4(lo):                     # CODE_BB8F26
        emit(bytes([fill52]) * (lo + 3))
        return "cmd"

    def pri_5(lo):                     # CODE_BB8F53
        emit(bytes([fill53]) * (lo + 3))
        return "cmd"

    def pri_6(lo):                     # CODE_BB8F80
        emit(bytes([word54 & 0xFF, word54 >> 8]))
        return ("sec_lo", lo)

    def pri_7(lo):                     # CODE_BB8F9C
        emit(bytes([b56]))
        return ("sec_lo", lo)

    def pri_8(lo):                     # CODE_BB8FAE
        emit(bytes([b57]))
        return ("sec_lo", lo)

    def pri_9(lo):                     # CODE_BB8FC0
        copy_back(2, lo + 2)
        return "cmd"

    def pri_a(lo):                     # CODE_BB8FFF
        count = lo + 3
        copy_back(count, count + rd())
        return "cmd"

    def pri_b(lo):                     # CODE_BB9062
        count = lo + 3
        b1 = rd()
        b2 = rd()
        copy_back(count, ((b1 << 8 | b2) >> 4) + 0x103)
        return ("sec", b2)

    def pri_c(lo):                     # CODE_BB90C9
        count = lo + 3
        b1 = rd()
        b2 = rd()
        copy_back(count, (b1 << 8) | b2)
        return "cmd"

    def pri_d(lo):                     # CODE_BB9138
        if not out:
            raise CmpError("pri_d sem historico")
        emit(bytes([out[-1]]))
        return ("sec_lo", lo)

    def pri_e(lo):                     # CODE_BB9150
        if len(out) < 2:
            raise CmpError("pri_e sem historico")
        emit(bytes([out[-2], out[-1]]))
        return ("sec_lo", lo)

    def pri_f(lo):                     # CODE_BB9176
        w = pool[lo]
        emit(bytes([w & 0xFF, w >> 8]))
        return "cmd"

    PRI = [pri_0, pri_1, pri_2, pri_3, pri_4, pri_5, pri_6, pri_7,
           pri_8, pri_9, pri_a, pri_b, pri_c, pri_d, pri_e, pri_f]

    mode, chain = "cmd", 0
    while True:
        if mode == "cmd":
            cmd = rd()
            r = PRI[cmd >> 4](cmd & 0x0F)
        else:
            r = SEC[chain & 0x0F]()
        if r is _EOF:
            break
        if r == "cmd":
            mode = "cmd"
        else:
            mode, chain = "sec", r[1]
    return bytes(out)


def decode_gfx_4bpp(raw):
    """4bpp SNES -> lista de 64 bytes RGBA-index (0..15 por pixel).

    Bitplanes: p0,p1 juntos, depois p2,p3 (formato de tile SNES).
    """
    tiles = []
    for base in range(0, len(raw) - 31, 32):
        t = raw[base:base + 32]
        px = [0] * 64
        for y in range(8):
            lo0, lo1 = t[y * 2], t[y * 2 + 1]
            hi0, hi1 = t[16 + y * 2], t[16 + y * 2 + 1]
            for x in range(8):
                bit = 7 - x
                px[y * 8 + x] = (((lo0 >> bit) & 1)
                                 | (((lo1 >> bit) & 1) << 1)
                                 | (((hi0 >> bit) & 1) << 2)
                                 | (((hi1 >> bit) & 1) << 3))
        tiles.append(px)
    return tiles


def render_metatile(def_words, map_word):
    """Renderiza 1 metatile 32x32 (16 tiles) respeitando flips do mapa.

    Fiel a CODE_B5ACF3 (normal), CODE_B5AD2B (H: sub-coluna espelhada +
    EOR $4000), CODE_B5AD53 (V: linhas invertidas + EOR $8000),
    CODE_B5AD80 (ambos). def_words = 16 words row-major 4x4.
    """
    hflip = bool(map_word & 0x4000)
    vflip = bool(map_word & 0x8000)
    rows = [def_words[r * 4:(r + 1) * 4] for r in range(4)]
    if vflip:
        rows = [list(reversed(r)) for r in reversed(rows)]
    out_rows = []
    for r in rows:
        row = list(reversed(r)) if hflip else list(r)
        if hflip:
            row = [w ^ 0x4000 for w in row]
        if vflip:
            row = [w ^ 0x8000 for w in row]
        out_rows.append(row)
    return out_rows  # 4x4 palavras de tile SNES


def tile_pixel(tiles, tile_index, palette, x, y, hflip, vflip, pal):
    """Pixel RGB de um tile 8x8 4bpp com paleta BG (0-7)."""
    if tile_index >= len(tiles):
        return (255, 0, 255)
    sx = 7 - x if hflip else x
    sy = 7 - y if vflip else y
    idx = tiles[tile_index][sy * 8 + sx]
    if idx == 0:
        return None  # transparente BG
    return palette[pal * 16 + idx]


def render_level(map_raw, defs_raw, gfx_raw, palette_rgb, bands=1):
    """Renderiza o level em pixels. Retorna imagem PIL.

    map: grid coluna-major 16 linhas/coluna (provado em CODE_B5ACA8/ACB7).
    defs: 376 metatiles x 16 tile words (provado em CODE_B5ACF3).
    """
    ncol = len(map_raw) // MAP_COL_BYTES
    tiles = decode_gfx_4bpp(gfx_raw)
    ndefs = len(defs_raw) // 32
    cols_per_band = ncol // bands if bands > 1 else ncol
    rows_total = MAP_ROWS * bands
    img = Image.new("RGBA", (cols_per_band * 32, rows_total * 32), (0, 0, 0, 0))
    pixels = img.load()  # PixelAccess writes (faster than putpixel)
    for c in range(cols_per_band):
        for r in range(rows_total):
            band, row = divmod(r, MAP_ROWS)
            src_col = band * cols_per_band + c
            off = src_col * MAP_COL_BYTES + row * 2
            mw = map_raw[off] | (map_raw[off + 1] << 8)
            mid = mw & 0x3FFF
            if mid >= ndefs:
                continue
            d = [defs_raw[mid * 32 + i] | (defs_raw[mid * 32 + i + 1] << 8)
                 for i in range(0, 32, 2)]
            mt = render_metatile(d, mw)
            for ry in range(4):
                for rx in range(4):
                    w = mt[ry][rx]
                    ti, pal = w & 0x3FF, (w >> 10) & 7
                    hf, vf = bool(w & 0x4000), bool(w & 0x8000)
                    for py in range(8):
                        for px in range(8):
                            col = tile_pixel(tiles, ti, palette_rgb,
                                             px, py, hf, vf, pal)
                            if col is not None:
                                pixels[c * 32 + rx * 8 + px, r * 32 + ry * 8 + py] = (*col, 255)
    return img


def render_tile_sheet(gfx_raw, palette_rgb, cols=32):
    """Sheet com todos os tiles 4bpp usando sub-paleta 0 (sanidade visual)."""
    tiles = decode_gfx_4bpp(gfx_raw)
    rows = (len(tiles) + cols - 1) // cols
    img = Image.new("RGB", (cols * 8, rows * 8), (32, 32, 32))
    pixels = img.load()  # PixelAccess writes (faster than putpixel)
    for i, t in enumerate(tiles):
        ox, oy = (i % cols) * 8, (i // cols) * 8
        for y in range(8):
            for x in range(8):
                idx = t[y * 8 + x]
                if idx:
                    pixels[ox + x, oy + y] = palette_rgb[idx]
    return img


def load_pac1_helpers():
    """decode_pac1 existente (tools/analysis). None se indisponivel."""
    path = os.path.join(TOOLS_DIR, "analysis", "decode_pac1.py")
    if not os.path.exists(path):
        return None
    spec = importlib.util.spec_from_file_location("pirate_pac1", path)
    if spec is None or spec.loader is None:
        return None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def cmp_decode_file(path):
    """Decodifica arquivo com o codec original. None se nao for stream CMP."""
    try:
        return cmp_decompress(open(path, "rb").read())
    except CmpError:
        return None


# mapa provado em CODE_B5ACA8/ACB7 e CODE_B5C80C/92D:
#   celula(col,row) esta em bytes [col*32 + row*2 ..+1], col = X/32 (32px),
#   row = (Y/32) mod 16 (16 linhas = 512px por banda); word: bits 0-13 id
#   do metatile (< $A0), bit14 = flip X ($4000), bit6 = flag extra ($0040).
MAP_COL_BYTES = 32
MAP_ROWS = 16


def parse_metatile_grid(raw):
    """Grid coluna-major provado pelo consumer. Retorna (cols, rows, words)."""
    ncol = len(raw) // MAP_COL_BYTES
    cols = []
    for c in range(ncol):
        col = []
        for r in range(MAP_ROWS):
            off = c * MAP_COL_BYTES + r * 2
            col.append(raw[off] | (raw[off + 1] << 8))
        cols.append(col)
    return ncol, MAP_ROWS, cols


def probe_level(source, proven, out_dir=None):
    """Sonda honesta dos arquivos de nivel. Nunca inventa formato.

    Tenta o descompressor ORIGINAL (CMP, CODE_BB8D91) em cada arquivo e
    registra tamanho/hash da saida; falha vira evidencia, nao invencao.
    """
    pac1 = load_pac1_helpers()
    decoded = {}
    probes = [] if pac1 is not None else [
        {"probe": "pac1-import", "result": "tools/analysis/decode_pac1.py ausente; "
                                           "nenhuma tentativa de descompressao"}]
    for rel, role in LEVEL_SOURCES:
        p = os.path.join(source, rel)
        if not os.path.exists(p):
            continue
        data = open(p, "rb").read()
        entry = {"probe": "cmp-original", "file": rel, "role": role,
                 "src_size": len(data)}
        try:
            out = cmp_decompress(data)
            entry["result"] = "decoded"
            entry["out_size"] = len(out)
            entry["out_sha256"] = hashlib.sha256(out).hexdigest()
            decoded[rel] = out
        except CmpError as e:
            entry["result"] = "rejected: %s" % e
        if role.endswith("compressed") and pac1 is not None:
            score = pac1.header_score(data, 0)
            probes.append({"probe": "pac1 header_score@0", "file": rel,
                           "score": score,
                           "result": "rejected: sem header PAC1 provado "
                                     "(score 0 em offsets 0..255 no survey)"})
        probes.append(entry)

    # dumps de parse autenticos (provenance) + estrutura dos grids
    grids = {}
    if out_dir:
        ddir = os.path.join(out_dir, "_decoded")
        os.makedirs(ddir, exist_ok=True)
        for rel, out in decoded.items():
            name = rel.replace("/", "_").replace("\\", "_")
            with open(os.path.join(ddir, name), "wb") as fh:
                fh.write(out)
    for rel, out in decoded.items():
        if rel.startswith("Tilemaps/Map32") or rel.startswith("LevelData/"):
            ncol, nrows, cols = parse_metatile_grid(out)
            ids = [w & 0x3FFF for col in cols for w in col]
            grids[rel] = {
                "cols": ncol, "rows": nrows,
                "width_px": ncol * 32, "height_px": nrows * 32,
                "max_metatile_id": max(ids) if ids else 0,
                "distinct_ids": len(set(ids)),
                "fits_metatile_budget": (max(ids) < 0xAA) if ids else False,
            }
    return {
        "status": "undecoded",
        "reason": "formato de tilemap/colisao/objetos nao provado: RomMap/Macro "
                  "so da incbin (sem layout); PAC1 rejeitado por header_score; "
                  "nenhum decoder alternativo verificado no repo",
        "probes": probes,
        "grids": grids,
        "delta": [
            "tracear o consumer de LevelData/ShipDeckLevels.bin (banco E3/E4) "
            "para provar stride da linha/metatile antes de emitir tiles",
            "tracear o consumer da tabela FE0A1E (SPR_PiratePanic_Main) para "
            "provar o layout de registros de SpriteData antes de emitir objects",
            "tracear o consumer da tabela FDAFA2 (BFD_PiratePanic_Main) para "
            "provar o layout de BananaFormations",
            "identificar o compressor de Graphics/Compressed e "
            "Tilemaps/Compressed (PAC1 descartado) antes de decodificar GFX",
        ],
    }


def write_lua(out_dir, sprites, palette_info, level, source_label):
    lines = ["-- Pirate Panic data file (gerado; nao editar a mao).",
             "-- Contrato: wrapper data/levels/level_1_1.lua e da Tifa.",
             "-- Fontes decodificadas com o codec original (CODE_BB8D91);",
             "-- ver manifest.json para provenance/hashes e hipoteses.",
             "-- source: " + source_label, "",
             "return {", "  id = 'pirate-panic',"]
    lines.append("  sprites = {")
    for s in sprites:
        lines.append("    %s = { file = 'sprites/%s.png', w = %d, h = %d },"
                     % (s["pose"], s["pose"], s["w"], s["h"]))
    lines.append("  },")
    lines.append("  palette = { file = '%s', colors = %d },"
                 % (palette_info["file"], palette_info["colors"]))
    lines.append("  level = { status = '%s' }," % level["status"])
    if "map" in level:
        m = level["map"]
        lines.append("  map = { file = '_decoded/map.bin', cols = %d, rows = %d,"
                     " width_px = %d, height_px = %d, metatile_px = %d,"
                     " render = '%s' },"
                     % (m["cols"], m["rows"], m["width_px"], m["height_px"],
                        m["metatile_px"], m["render_png"]))
        lines.append("  defs = { file = '_decoded/defs.bin', count = %d },"
                     % level["defs"]["count"])
        lines.append("  tiles = { file = '_decoded/gfx1.bin', count = %d,"
                     " sheet = '%s' },"
                     % (level["tiles"]["count"], level["tiles"]["sheet_png"]))
    else:
        lines.append("  map = nil,")
        lines.append("  defs = nil,")
        lines.append("  tiles = nil,")
    if "objects" in level:
        o = level["objects"]
        lines.append("  objects = { file = '_decoded/objects.bin', count = %d,"
                     " coord_bias = %d },"
                     % (o["count"], o["coord_bias"]))
    else:
        lines.append("  objects = nil,")
    spawn = level.get("spawn", {})
    lines.append("  spawn = { status = '%s' }," % spawn.get("status", "unproven"))
    if "collision" in level:
        c = level["collision"]
        lines.append("  collision = { file = '%s', entries = %d },"
                     % (c["table"], c["entries"]))
    lines.append("}")
    path = os.path.join(out_dir, "pirate_panic.lua")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
    return path


def write_runtime_lua(out_dir, level, chunks, source_label, repo_root):
    """Gera o modulo Lua consumido pelo wrapper data/levels/level_1_1.lua.

    O wrapper e versionado; este arquivo e gerado (git-ignored) e carrega o
    layout original decodificado. A grade de colisao vai RLE (celulas 16px).
    """
    spawn = level.get("spawn", {}) or {}
    goal = spawn.get("goal") or {}
    lim = level.get("limits", {}) or {}
    grid = level.get("collision_grid", {}) or {}
    objs = (level.get("objects", {}) or {}).get("items", [])
    lines = [
        "-- Pirate Panic level data (gerado por tools/import_pirate_panic.py).",
        "-- NAO editar a mao. Fonte: " + source_label,
        "-- Contrato: data/levels/level_1_1.lua (wrapper original_semantics).",
        "return {",
        "  id = '1-1',",
        "  name = 'Pirate Panic',",
        "  original_semantics = true,",
        "  original_camera_max = { x = %d, y = %d }," % tuple(
            level.get("main_room", {}).get("camera_max", [0, 0])),
        "  surface_cols = %d," % level.get("flat_surfaces", {}).get("cols", 0),
        "  surface_rows = %d," % level.get("flat_surfaces", {}).get("rows", 0),
        "  surface_rle = '%s'," % level.get("flat_surfaces", {}).get("rle", ""),
        "  tile_px = 16,",
        "  metatile_px = 32,",
        "  width_px = %d," % (grid.get("cols", 0) * 16),
        "  height_px = %d," % (grid.get("rows", 0) * 16),
        "  grid_cols = %d," % grid.get("cols", 0),
        "  grid_rows = %d," % grid.get("rows", 0),
        "  grid_rle = '%s'," % grid.get("rle", ""),
        "  spawn = { x = %d, feet_y = %d },"
        % (spawn.get("x") or 0, spawn.get("feet_y") or 0),
        "  goal = { x = %d, feet_y = %d },"
        % (goal.get("x") or 0, goal.get("feet_y") or 0),
        "  limits = { x_min = %d, x_max = %d, y_min = %d, y_max = %d },"
        % (lim.get("x_min", 0), lim.get("x_max", 0),
           lim.get("y_min", 0), lim.get("y_max", 512)),
        "  chunks = {",
    ]
    for ch in chunks:
        anim = os.path.splitext(os.path.basename(ch["file"]))[0]
        lines.append("    { anim = '%s', x = %d, w = %d, h = %d },"
                     % (anim, ch["x"], ch["w"], ch["h"]))
    lines.append("  },")
    lines.append("  objects = {")
    for o in objs:
        lines.append(
            "    { type = %d, script = %d, class = %d, x = %d, feet_y = %d,"
            " param = %d, sprite = %s },"
            % (o.get("type", 0), o.get("script", 0), o.get("class", 0),
               o.get("x", 0), o.get("feet_y", 0), o.get("param", 0),
               ("'%s'" % o["sprite_name"]) if o.get("sprite_name") else "nil"))
    lines.append("  },")
    lines.append("  subareas = {")
    for key, area in (level.get("subareas") or {}).items():
        level_id = area.get("level_id")
        level_id_text = str(level_id) if level_id is not None else "nil"
        lines.append("    %s = { level_id = %s, status = '%s', objects = {" % (
            key, level_id_text, area["status"]))
        for o in area.get("objects", []):
            lines.append(
                "      { type = %d, script = %d, class = %d, x = %d,"
                " feet_y = %d, param = %d, sprite = %s }," % (
                    o.get("type", 0), o.get("script", 0), o.get("class", 0),
                    o.get("x", 0), o.get("feet_y", 0), o.get("param", 0),
                    ("'%s'" % o["sprite_name"])
                    if o.get("sprite_name") else "nil"))
        lines.append("    },")
        header = area.get("header")
        if header:
            lines.append(
                "      header = { pointer = %d, header_type = %d,"
                " status = '%s', record_offset = %d, records = {" % (
                    header["pointer"], header["header_type"], header["status"],
                    header["record_offset"]))
            for rec in header["records"]:
                lines.append(
                    "        { flags = %d, x = %d, feet_y = %d }," % (
                        rec["flags"], rec["x"], rec["feet_y"]))
            post_words = ", ".join(str(value)
                                   for value in header["post_record_words"])
            tail_words = ", ".join(str(value) for value in header["tail_words"])
            lines.append("      }, post_record_words = { %s }, tail_words = { %s } },"
                         % (post_words, tail_words))
        lines.append("    },")
    lines.append("  },")
    lines.append("  parallax = { bg = 0.25, far = 0.5, mid = 0.75 },")
    lines.append("}")
    contents = "\n".join(lines) + "\n"
    path = os.path.join(out_dir, "pirate_panic_level.lua")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(contents)
    runtime_dir = os.path.join(repo_root, "data", "original", "pirate")
    os.makedirs(runtime_dir, exist_ok=True)
    runtime_path = os.path.join(runtime_dir, "pirate_panic_level.lua")
    with open(runtime_path, "w", encoding="utf-8") as fh:
        fh.write(contents)
    return runtime_path


DIDDY_CANVAS = 64          # estavel: todos os frames no mesmo canvas
DIDDY_SETS = (
    ("idle", "GFX_Diddy_IdleSway"),
    ("walk", "GFX_Diddy_Walk"),
    ("fall", "GFX_Diddy_Fall"),
    ("land", "GFX_Diddy_Land"),
    ("juggle", "GFX_Diddy_Juggling"),
    ("jump", "GFX_Diddy_Jump"),
    ("run", "GFX_Diddy_Run"),
)


def pose_bounds(name, poses):
    pieces = build_pieces(poses[name])
    if not pieces:
        raise ValueError("invalid original OAM pose: " + name)
    return (min(p[0] for p in pieces) - 6, min(p[1] for p in pieces) - 6,
            max(p[0] + p[2] * 8 for p in pieces) + 6,
            max(p[1] + p[2] * 8 for p in pieces) + 6)


def write_diddy_sprites(sprites, out_src, img_root, poses):
    """Copia os frames RGBA do Diddy para assets/images/pirate/diddy/.

    A shared canvas preserves the ORIGINAL OAM coordinate origin in every frame.
    No independent centering or fitted 'feet' origin; run has Run1-13 poses.
    """
    ddir = os.path.join(img_root, "diddy")
    os.makedirs(ddir, exist_ok=True)
    out = []
    bounds = {s["pose"]: pose_bounds(s["pose"], poses) for s in sprites}
    left = min(b[0] for b in bounds.values())
    top = min(b[1] for b in bounds.values())
    right = max(b[2] for b in bounds.values())
    bottom = max(b[3] for b in bounds.values())
    width = ((right - left + 7) // 8) * 8
    height = ((bottom - top + 7) // 8) * 8
    for set_name, prefix in DIDDY_SETS:
        frames = sorted(
            (s for s in sprites if s["pose"].startswith(prefix)),
            key=lambda s: natural_key(s["pose"]))
        for i, s in enumerate(frames, 1):
            src = os.path.join(out_src, s["file"])
            if not os.path.exists(src):
                continue
            im = Image.open(src).convert("RGBA")
            canvas = Image.new("RGBA", (width, height),
                                (0, 0, 0, 0))
            x0, y0, _, _ = bounds[s["pose"]]
            canvas.paste(im, (x0 - left, y0 - top))
            # Preserve original pose numbering, including gaps in valid files.
            pose_match = re.search(r"(\d+)\.bin$", s["pose"])
            if pose_match is None:
                raise ValueError("invalid original pose number: " + s["pose"])
            pose_number = int(pose_match.group(1))
            name = "diddy_%s_%02d.png" % (set_name, pose_number)
            canvas.save(os.path.join(ddir, name))
            out.append({"set": set_name, "name": name, "index": i,
                        "w": im.width, "h": im.height,
                        "src_pose": s["pose"], "canvas_w": width,
                        "canvas_h": height, "anchor_x": -left, "anchor_y": -top})
    return out


def write_enemy_sprites(source, poses, img_root):
    """Export verified OAM graphics; animation timing still needs ROM tracing."""
    sets = (("Neek", "original_neek", "GFX_Neek_Walk", "Sprite_Neek.bin"),
            ("Klomp", "original_klomp", "GFX_Klomp_Walk", "Sprite_Klomp.bin"))
    out_dir = os.path.join(img_root, "enemies")
    os.makedirs(out_dir, exist_ok=True)
    results = []
    gfxdir = os.path.join(source, "Graphics", "DynamicSprites")
    for sprite_name, anim, prefix, pal_name in sets:
        palette_path = os.path.join(source, "Palettes", pal_name)
        palette = load_palette(palette_path)
        names = sorted((n for n in poses if n.startswith(prefix)), key=natural_key)
        frames = []
        for name in names:
            image, error = render_pose(name, poses, palette, gfxdir=gfxdir)
            if error:
                raise ValueError("%s: %s" % (name, error))
            frames.append((name, image))
        if not frames:
            raise ValueError("original frames missing: " + prefix)
        width = max(image.width for _, image in frames)
        height = max(image.height for _, image in frames)
        for index, (name, image) in enumerate(frames, 1):
            canvas = Image.new("RGBA", (width, height), (0, 0, 0, 0))
            # Presentation anchor only; not a claim of original collision origin.
            canvas.paste(image, ((width - image.width) // 2, height - image.height))
            canvas.save(os.path.join(out_dir, "%s_%02d.png" % (anim, index)))
        results.append({"sprite": sprite_name, "animation": anim, "frames": len(frames),
                        "width": width, "height": height,
                        "palette": pal_name, "palette_sha256": sha256_file(palette_path),
                        "poses": [name for name, _ in frames],
                        "gfx_sha256": [sha256_file(os.path.join(gfxdir, name)) for name, _ in frames],
                        "timing_status": "unverified", "anchor_status": "presentation-only"})
    return results


def write_atlas(repo_root, img_root):
    """Gera main/game.atlas juntando assets/images/gen e assets/images/pirate."""
    groups = {}
    for base_dir in (os.path.join(img_root, "gen"),
                     os.path.join(img_root, "pirate")):
        if not os.path.isdir(base_dir):
            continue
        for root, _dirs, files in os.walk(base_dir):
            for f in sorted(files):
                if not f.lower().endswith(".png"):
                    continue
                stem = f[:-4]
                path = "/" + os.path.relpath(os.path.join(root, f), repo_root).replace(os.sep, "/")
                m = re.match(r"^(?P<base>.+)_(?P<idx>\d+)$", stem)
                if m:
                    key = m.group("base")
                    groups.setdefault(key, []).append(
                        (int(m.group("idx")), path))
                else:
                    groups.setdefault(stem, []).append((0, path))
    fps = {"player_idle": 3, "player_run": 12, "player_roll": 16,
           "player_swim": 6, "player_climb": 8, "en_kritter": 5,
           "en_zinger": 12, "en_flitter": 14, "diddy_idle": 8,
           "diddy_run": 12, "diddy_jump": 10}
    out = []
    for anim_id in sorted(groups):
        frames = [p for _i, p in sorted(groups[anim_id])]
        loop = len(frames) > 1
        out.append("animations {")
        out.append('  id: "%s"' % anim_id)
        for path in frames:
            out.append("  images {")
            out.append('    image: "%s"' % path)
            out.append("    sprite_trim_mode: SPRITE_TRIM_MODE_OFF")
            out.append("  }")
        out.append("  playback: %s"
                   % ("PLAYBACK_LOOP_FORWARD" if loop else "PLAYBACK_NONE"))
        out.append("  fps: %d" % fps.get(anim_id, 8))
        out.append("  flip_horizontal: 0")
        out.append("  flip_vertical: 0")
        out.append("}")
    # Frames are played by image name ("x_0"): declare each one as its own animation (the
    # engine does not resolve image names inside groups; qa-24..qa-48 regression).
    for anim_id in sorted(groups):
        for _i, path in sorted(groups[anim_id]):
            stem = os.path.splitext(os.path.basename(path))[0]
            if stem not in groups:
                out.append('animations {\n  id: "%s"\n  images {\n    image: "%s"\n'
                           '    sprite_trim_mode: SPRITE_TRIM_MODE_OFF\n  }\n  playback: PLAYBACK_NONE\n'
                           '  fps: 8\n  flip_horizontal: 0\n  flip_vertical: 0\n}' % (stem, path))
    out.append("margin: 0")
    out.append("extrude_borders: 2")
    out.append("inner_padding: 0")
    dest = os.path.join(repo_root, "main", "game.atlas")
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    with open(dest, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(out) + "\n")
    return dest, len(groups)


def dump_stats(source):
    """Analise rapida dos streams decodificados (diagnostico de formato)."""
    for rel, role in LEVEL_SOURCES:
        p = os.path.join(source, rel)
        if not os.path.exists(p):
            continue
        out = cmp_decode_file(p)
        if out is None:
            print("%-46s nao-CMP" % rel)
            continue
        words = [out[i] | (out[i + 1] << 8) for i in range(0, len(out) - 1, 2)]
        stats = []
        for mask in (0xFF, 0x1FF, 0x3FF, 0x3FFF):
            ids = [w & mask for w in words]
            stats.append("mask=%04X max=%d n_dist=%d fits170=%s" % (
                mask, max(ids), len(set(ids)), max(ids) < 0xAA))
        print("%-46s %6dB words=%d" % (rel, len(out), len(words)))
        for s in stats:
            print("    " + s)
        print("    head: %s" % " ".join("%04X" % w for w in words[:16]))
        if rel.startswith("LevelData/") and len(words) >= 16:
            ncol = len(words) // 16
            prof = []
            for c in range(ncol):
                col = words[c * 16:(c + 1) * 16]
                nz = sum(1 for w in col if (w & 0x3FFF) != 0)
                prof.append(nz)
            runs = []
            start = None
            for c, nz in enumerate(prof):
                if nz and start is None:
                    start = c
                elif not nz and start is not None:
                    runs.append((start, c - 1))
                    start = None
            if start is not None:
                runs.append((start, ncol - 1))
            print("    cols=%d secoes densas: %s" % (ncol, runs[:20]))
        if rel.startswith("LevelData/SpriteData"):
            raw = open(p, "rb").read()
            print("    objetos RAW %dB (script=w0&F classe=(w0>>4)&F "
                  "type=(w0>>8)&1F):" % len(raw))
            for o in parse_objects(raw):
                print("      [%02d] w0=%04X script=%2d class=%2d type=%2d "
                      "x=%5d y=%5d param=%04X"
                      % (o["index"], o["flags_lo"] | (o["type"] << 8)
                         | (o["subtype"] << 4),
                         o["flags_lo"] & 0x0F, o["subtype"], o["type"],
                         o["x"], o["y"], o["param"]))


# ---------------------------------------------------------------------------
# Formatos provados (cada um rastreado no codigo original):
#   mapa      ShipDeckLevels.bin (CMP) — grid coluna-major, 16 words/coluna
#             (32px/metatile), word = ID 0..375 | $4000 H-flip | $8000 V-flip
#             (CODE_B5ACA8/ACB7 offset; CODE_B5ACF3/AD2B/AD53/AD80 flips)
#   defs      Tilemaps/Map32/Layer1_Level_ShipDeck.bin (CMP) — 376 metatiles
#             x 16 tile words (4x4 row-major) = 32 bytes/def (CODE_B5ACF3
#             ASL x5 = ID*32; colunas +0/8/10/18)
#   gfx       GFX_Layer1_Level_ShipDeck.bin (CMP) — 918 tiles 4bpp (32B)
#   paleta    Palettes/FGBG_Level_PiratePanic.bin — 128 cores BGR555
#   colisao   RomMap DATA_FC6154 (ROM $3C6154, 680B = 170 x 4B) — 2 words
#             por metatile (esquerda/direita, bit15 = espelho V) cujo byte
#             baixo indexa DATA_B5CA38 (CODE_B5C92D). Budget $A0=$AA=170:
#             IDs >= 170 sao decorativos, sem colisao.
#   objetos   SpriteData/PiratePanic_Main.bin (RAW) — 55 registros de 8B
#             (word0: low!=0 + type<<8 + subtype<<4; word1: x_raw; word2:
#             y_raw; word3: param) + terminator 2B. x = x_raw-$100,
#             y = y_raw-$100 (CODE_BBB390/BBB3D0, tabela DATA_FE0000[3]).
# ---------------------------------------------------------------------------

FC_TABLE_ROM_OFFSET = 0x3C6154   # HiROM $FC6154 -> arquivo
FC_TABLE_BYTES = 680             # DATA_FC6154..DATA_FC63FC = 170 x 4B
OBJ_RECORD = 8
OBJ_XY_BIAS = 0x100
# Normalize original sprite origins, not a fitted collision-box bottom.
# Captured same-ROM Diddy origin (304,465) agrees with header R0.
# World origin subtracts $100 on BOTH axes; old $111 was a fitted guess.
OBJ_Y_FEET_BIAS = 0x100
HEADER_ROM_OFFSET = 0x3D4C8A     # HiROM $FD4C8A (RomMap DATA_FD4C8A)
LEVEL_HEADER_TABLE_ROM_OFFSET = 0x3D0000  # DATA_FD0000, u16 offsets within bank $FD
LEVEL_HEADER_BANK_ROM_OFFSET = 0x3D0000
HEADER_REC_BYTES = 5             # (flags:u8, x_raw:u16, y_raw:u16)
PROPS_ROM_OFFSET = 0x35CA38      # HiROM $B5CA38: 80 handler pointers (not 170 metatiles)
COLL_BUDGET = 170                # IDs >= $AA sao decorativos (sem colisao)
# pipeline de identidade do objeto (prova: CODE_BBB8BF):
#   w3 (param) = byte offset em DATA_FBE800 ($3BE800); entrada = ponteiro
#   16-bit para o definition block em banco $FF (arquivo $3F0000+ptr);
#   tag $0000 do bloco = SpriteID (enum em Misc_Defines_DKC2.asm).
FBE800_ROM_OFFSET = 0x3BE800
DEF_BANK_FILE_OFFSET = 0x3F0000
SPRITE_ID_LEVEL_END_GOAL = 0x0160   # !Define_DKC2_SpriteID_LevelEndGoal
SPRITE_ID_EXIT_DOOR = 0x0094        # !Define_DKC2_SpriteID_ExitDoor


def load_sprite_id_names(defines_path):
    """Enum SpriteID do proprio fonte (Misc_Defines_DKC2.asm)."""
    names = {}
    try:
        text = open(defines_path, "r", encoding="utf-8", errors="replace").read()
    except OSError:
        return names
    for m in re.finditer(r"!Define_DKC2_SpriteID_(\w+)\s*=\s*\$([0-9A-Fa-f]+)",
                         text):
        names[int(m.group(2), 16)] = m.group(1)
    return names


def load_level_id_values(defines_path):
    """LevelID enum from the same read-only disassembly as SpriteID names."""
    values = {}
    try:
        with open(defines_path, "r", encoding="utf-8", errors="replace") as fh:
            text = fh.read()
    except OSError:
        return values
    for match in re.finditer(
            r"!Define_DKC2_LevelID_(\w+)\s*=\s*\$([0-9A-Fa-f]+)", text):
        values[match.group(1)] = int(match.group(2), 16)
    return values


def resolve_object_sprite_ids(objs, rom, names=None):
    """Resolve o SpriteID de cada objeto via spawn script original.

    `param` (w3) e um byte offset em DATA_FBE800; a entrada e um ponteiro u16
    para um SPRITE SPAWN SCRIPT em banco $FF (formato dos opcodes $XX00, ver
    AsarScripts/DisassembleSpriteSpawnScript.asm). O script e uma lista de
    instrucoes: `$8300 : <ptr>` (Op131) salta para um sub-script em $FF<ptr>;
    `$0000 : <sid>` (Op0) carrega o SpriteID. Seguimos a cadeia $8300 ate o
    primeiro par `$0000 : <sid>`.

    Provado por nomes reais: Neek $01E4, Klomp $01EC, DKBarrel $01A8,
    WoodenBox $01BC, KongLetters $0174, BarrelCannon $0140.
    """
    if not rom or len(rom) < FBE800_ROM_OFFSET + 0x1000:
        return
    names = names or {}
    for o in objs:
        o["sprite_id"] = _sprite_id_from_script(rom, o["param"])
        o["sprite_name"] = names.get(o["sprite_id"],
                                     "SpriteID_%04X" % (o["sprite_id"] or 0)
                                     if o["sprite_id"] is not None else None)


def _script_words(rom, ptr, count=16):
    off = DEF_BANK_FILE_OFFSET + ptr
    if off + 2 * count > len(rom):
        return []
    return [rom[off + 2 * i] | (rom[off + 2 * i + 1] << 8)
            for i in range(count)]


def _sprite_id_from_script(rom, param, max_hops=8):
    """Segue os saltos $8300 e extrai o primeiro `$0000 : <sprite_id>`.

    O par valido e (opcode $0000, sid em 1..$03FF); o sub-script alcancado por
    `$8300 : <ptr>` comeca com esse par. Procuramos primeiro na posicao 0,
    depois em qualquer par valido, e seguimos o primeiro salto $8300 do script
    (nao so o da cabeca).
    """
    if param is None or FBE800_ROM_OFFSET + param + 2 > len(rom):
        return None
    ent = FBE800_ROM_OFFSET + param
    ptr = rom[ent] | (rom[ent + 1] << 8)
    seen = set()
    for _ in range(max_hops):
        if ptr in seen:
            return None
        seen.add(ptr)
        words = _script_words(rom, ptr, 24)
        if not words:
            return None
        if words[0] == 0x0000 and len(words) > 1 and 0 < words[1] < 0x400:
            return words[1]
        for i in range(len(words) - 1):
            if words[i] == 0x0000 and 0 < words[i + 1] < 0x400:
                return words[i + 1]
        nxt = None
        for i in range(len(words) - 1):
            if words[i] == 0x8300:
                nxt = words[i + 1]
                break
        if nxt is None:
            return None
        ptr = nxt
    return None


def parse_objects(raw):
    """55 registros x 8B + terminator 2B (CODE_BBB3D0)."""
    objs = []
    for i in range(0, len(raw) - 1, OBJ_RECORD):
        w0 = raw[i] | (raw[i + 1] << 8)
        if (w0 & 0xFF) == 0:
            break
        w1 = raw[i + 2] | (raw[i + 3] << 8)
        w2 = raw[i + 4] | (raw[i + 5] << 8)
        w3 = raw[i + 6] | (raw[i + 7] << 8)
        objs.append({
            "index": len(objs),
            "type": (w0 >> 8) & 0x1F,
            "script": w0 & 0x0F,
            "class": (w0 >> 4) & 0x0F,
            "subtype": (w0 >> 4) & 0x0F,
            "flags_lo": w0 & 0xFF,
            "x": w1 - OBJ_XY_BIAS,
            "y": w2 - OBJ_XY_BIAS,
            "x_raw": w1, "y_raw": w2, "param": w3,
        })
    return objs


def parse_pirate_panic_subareas(source, rom):
    """Import the four linked room object tables without inventing room maps."""
    defines = os.path.join(source, "Misc_Defines_DKC2.asm")
    sprite_names = load_sprite_id_names(defines)
    level_ids = load_level_id_values(defines)
    areas = {}
    for key, symbol in PIRATE_PANIC_SUBAREAS:
        rel = "LevelData/SpriteData/%s.bin" % symbol
        path = os.path.join(source, rel)
        if not os.path.isfile(path):
            areas[key] = {
                "level_id": level_ids.get(symbol), "source_file": rel,
                "status": "missing", "count": 0, "objects": [],
            }
            continue
        raw = open(path, "rb").read()
        objects = parse_objects(raw)
        resolve_object_sprite_ids(objects, rom, sprite_names)
        for obj in objects:
            obj["feet_y"] = obj["y_raw"] - OBJ_Y_FEET_BIAS
        areas[key] = {
            "level_id": level_ids.get(symbol), "source_file": rel,
            "source_sha256": hashlib.sha256(raw).hexdigest(),
            "status": "objects-only; room map and collision not decoded",
            "count": len(objects), "objects": objects,
            "header": parse_level_header(rom, level_ids.get(symbol)),
        }
    return areas


def extract_captains_kabin_assets(source, out_dir, area):
    """Preserve Cabin visual source streams without asserting their layout."""
    decoded_dir = os.path.join(out_dir, "_decoded")
    os.makedirs(decoded_dir, exist_ok=True)
    files = {}
    for name, rel, codec in CAPTAINS_KABIN_ASSETS:
        path = os.path.join(source, rel)
        entry = {"source_file": rel}
        if not os.path.isfile(path):
            entry["status"] = "missing"
            files[name] = entry
            continue

        raw = open(path, "rb").read()
        entry["source_sha256"] = hashlib.sha256(raw).hexdigest()
        try:
            decoded = cmp_decompress(raw) if codec == "cmp" else raw
        except CmpError as exc:
            entry.update(status="rejected", reason=str(exc))
            files[name] = entry
            continue

        filename = "captains_kabin_%s.bin" % name
        with open(os.path.join(decoded_dir, filename), "wb") as fh:
            fh.write(decoded)
        entry.update({
            "codec": "cmp-original" if codec == "cmp" else "raw",
            "decoded_file": "_decoded/" + filename,
            "decoded_size": len(decoded),
            "decoded_sha256": hashlib.sha256(decoded).hexdigest(),
            "status": "decoded" if codec == "cmp" else "copied-raw",
        })
        files[name] = entry

    complete = all(files[name]["status"] in ("decoded", "copied-raw")
                   for name, _, _ in CAPTAINS_KABIN_ASSETS)
    area["assets"] = {
        "status": ("source-assets-extracted; room layout/collision unproven" if complete
                   else "partial; room layout/collision unproven"),
        "files": files,
    }


def parse_level_header(rom, level_id):
    """Read a LevelID header using CODE_BBAEFF's pointer/preamble layout.

    Only types 0 and 1 are needed here. CODE_BBAF4B consumes one extra byte
    for type 1; CODE_BBAFD4/BBB04F/BBB059 then lead to five-byte records.
    Words after the $FF record terminator stay raw: their game semantics are
    not established by this importer.
    """
    if not rom or not isinstance(level_id, int) or not 0 <= level_id < 0x100:
        return None

    pointer_at = LEVEL_HEADER_TABLE_ROM_OFFSET + level_id * 2
    if pointer_at + 2 > len(rom):
        return None
    pointer = int.from_bytes(rom[pointer_at:pointer_at + 2], "little")
    base = LEVEL_HEADER_BANK_ROM_OFFSET + pointer

    def word_at(offset):
        if offset < 0 or offset + 2 > len(rom):
            return None
        return int.from_bytes(rom[offset:offset + 2], "little")

    kind = word_at(base)
    if kind not in (0, 1):
        return None
    pos = base + 2
    extra_byte = None
    if kind == 1:
        if pos >= len(rom):
            return None
        extra_byte = rom[pos]
        pos += 1

    # CODE_BBAFD4: one word, one byte, then word/byte pairs through word 0.
    preamble_word = word_at(pos)
    if preamble_word is None or pos + 3 > len(rom):
        return None
    pos += 2
    preamble_byte = rom[pos]
    pos += 1
    preamble_pairs = []
    for _ in range(256):
        value = word_at(pos)
        if value is None:
            return None
        pos += 2
        if value == 0:
            break
        if pos >= len(rom):
            return None
        preamble_pairs.append({"word": value, "byte": rom[pos]})
        pos += 1
    else:
        return None

    # CODE_BBB04F reads one byte; CODE_BBB059 reads a word and a byte.
    trailing_word = word_at(pos + 1)
    if pos + 4 > len(rom) or trailing_word is None:
        return None
    pos += 4
    record_offset = pos - base
    records = []
    for index in range(256):
        if pos >= len(rom):
            return None
        if rom[pos] == 0xFF:
            break
        if pos + HEADER_REC_BYTES > len(rom):
            return None
        x_raw = int.from_bytes(rom[pos + 1:pos + 3], "little")
        y_raw = int.from_bytes(rom[pos + 3:pos + 5], "little")
        records.append({
            "index": index, "flags": rom[pos],
            "x_raw": x_raw, "y_raw": y_raw,
            "x": x_raw - OBJ_XY_BIAS,
            "feet_y": y_raw - OBJ_Y_FEET_BIAS,
        })
        pos += HEADER_REC_BYTES
    else:
        return None

    pos += 1  # CODE_BBAFB6 skips the $FF record marker.
    post_record_words = []
    for _ in range(256):
        value = word_at(pos)
        if value is None:
            return None
        post_record_words.append(value)
        pos += 2
        if value & 0x8000:  # CODE_BBB088 stops on a negative word.
            break
    else:
        return None
    tail = [word_at(pos), word_at(pos + 2)]
    if None in tail:
        return None

    return {
        "level_id": level_id, "pointer": pointer, "header_type": kind,
        "type_byte": extra_byte, "record_offset": record_offset,
        "preamble_word": preamble_word, "preamble_byte": preamble_byte,
        "preamble_pairs": preamble_pairs, "trailing_word": trailing_word,
        "records": records, "post_record_words": post_record_words,
        "tail_words": tail, "status": "source-codec-supported",
    }


def parse_header(rom):
    """Pirate Panic main records, retained as the existing compatibility API."""
    header = parse_level_header(rom, 0x0003)
    return header["records"] if header else []


def collision_property_map(rom):
    """Mapeamento de colisao por metatile ID (budget 170).

    Tabela DATA_FC6154: 170 entradas x 4B = (left:u16, right:u16), indexada
    pelo metatile ID. Cada word descreve UMA das duas sub-colunas de 16px do
    metatile de 32px: word == 0 -> sem colisao na sub-coluna; caso contrario a
    sub-coluna colide. O byte alto carrega flags ($00/$40/$80/$C0) e o baixo e
    o property_index em DATA_B5CA38 (CODE_B5C92D) -- exportado bruto.

    Validacao: com esse modelo 27/55 objetos apoiam exatamente no topo de um
    bloco colidivel (antigo ajuste y_raw-273 nao prova altura). IDs >= 170 sao decorativos (sem
    colisao) -- o "budget" provado.
    """
    if not rom or len(rom) < FC_TABLE_ROM_OFFSET + FC_TABLE_BYTES:
        return []
    props = []
    for i in range(FC_TABLE_BYTES // 4):
        left, right = struct.unpack(
            "<HH", rom[FC_TABLE_ROM_OFFSET + i * 4:FC_TABLE_ROM_OFFSET + i * 4 + 4])
        props.append({
            "id": i,
            "left": left, "right": right,
            "left_property": left & 0xFF, "right_property": right & 0xFF,
            "left_flags": (left >> 8) & 0xFF, "right_flags": (right >> 8) & 0xFF,
            "left_class": class_from_word(left),
            "right_class": class_from_word(right),
        })
    return props


def class_from_word(word):
    """Classe de colisao derivada de uma word da tabela FC6154.

    0 = vazio, 1 = solido, 2 = plataforma (one-way). O flag $40 na word e
    tratado como plataforma -- HIPOTESE nao provada fisicamente; todos os
    demais valores nao-zero sao solido (conservador).
    """
    if word == 0:
        return 0
    if (word & 0xFF00) == 0x4000:
        return 2
    return 1


def build_collision_grid(map_raw, props, max_cols=None):
    """Grade de colisao em celulas de 16px (linha a linha, row-major).

    Cada metatile de 32px vira 2x2 celulas de 16px: a sub-coluna esquerda
    (word left) cobre as duas celulas da esquerda, a direita (word right) as
    duas da direita. `max_cols` restringe ao trecho do nivel main.
    Retorna (cols, rows, lista de classes).
    """
    ncol = len(map_raw) // MAP_COL_BYTES
    if max_cols is not None:
        ncol = min(ncol, max_cols)
    cols, rows = ncol * 2, MAP_ROWS * 2
    grid = [0] * (cols * rows)
    for c in range(ncol):
        for r in range(MAP_ROWS):
            off = c * MAP_COL_BYTES + r * 2
            mid = (map_raw[off] | (map_raw[off + 1] << 8)) & 0x3FFF
            if mid == 0 or mid >= COLL_BUDGET or mid >= len(props):
                continue
            p = props[mid]
            for half in (0, 1):
                cls = p["left_class"] if half == 0 else p["right_class"]
                if cls == 0:
                    continue
                cx = c * 2 + half
                for dy in (0, 1):
                    grid[(r * 2 + dy) * cols + cx] = cls
    return cols, rows, grid


def rle_encode(grid):
    """RLE de bytes: sequencia 'classe:contagem,' (base 10, texto puro)."""
    parts = []
    i, n = 0, len(grid)
    while i < n:
        v = grid[i]
        j = i + 1
        while j < n and grid[j] == v:
            j += 1
        parts.append("%d:%d," % (v, j - i))
        i = j
    return "".join(parts)


def decode_rle(text):
    """Inverso de rle_encode (usado nos testes; o runtime tem o equivalente)."""
    out = []
    i, n = 0, len(text)
    while i < n:
        colon = text.find(":", i)
        if colon < 0:
            break
        comma = text.find(",", colon + 1)
        last = comma if comma >= 0 else n
        v = int(text[i:colon] or 0)
        cnt = int(text[colon + 1:last] or 0)
        out.extend([v] * cnt)
        i = last + 1
    return out


def write_level_chunks(img, out_dir, chunk_w=512):
    """Fatia o render em chunks estaticos de no maximo `chunk_w` px de largura.

    Evita um sprite por tile: o runtime desenha ~3-4 chunks por frame.
    O nome nao pode terminar em `_<digitos>` (senao o gen_atlas agrupa todos
    numa animacao so); por isso `levelchunkNNN`.
    """
    ddir = os.path.join(out_dir, "chunks")
    os.makedirs(ddir, exist_ok=True)
    chunks = []
    x = 0
    idx = 0
    while x < img.width:
        w = min(chunk_w, img.width - x)
        crop = img.crop((x, 0, x + w, img.height))
        name = "levelchunk%03d.png" % idx
        crop.save(os.path.join(ddir, name))
        chunks.append({"file": "chunks/" + name, "x": x, "w": w,
                       "h": img.height})
        x += w
        idx += 1
    return chunks


def execute_collision_handler(index, x_offset, rom):
    """Interpret the tiny verified 65816 A-only subset used by FC6154.

    Pirate Panic references only handlers with immediate math/branches/RTS;
    unknown opcodes fail closed instead of producing a guessed platform.
    """
    if index >= 80:
        return -1
    table = 0x35CA38 + index * 2
    pointer = int.from_bytes(rom[table:table + 2], "little")
    pc = 0x350000 + pointer
    a, carry, negative, zero = x_offset & 0xFFFF, bool(index & 0x80), False, x_offset == 0
    for _ in range(32):
        opcode = rom[pc]
        pc += 1
        if opcode == 0xA9:  # LDA immediate
            a = int.from_bytes(rom[pc:pc + 2], "little"); pc += 2
            negative, zero = bool(a & 0x8000), a == 0
        elif opcode == 0x4A:  # LSR A
            carry = bool(a & 1); a >>= 1; negative, zero = False, a == 0
        elif opcode == 0x6A:  # ROR A
            old_carry = int(carry); carry = bool(a & 1)
            a = (a >> 1) | (old_carry << 15); negative, zero = bool(a & 0x8000), a == 0
        elif opcode == 0x0A:  # ASL A
            carry = bool(a & 0x8000); a = (a << 1) & 0xFFFF
            negative, zero = bool(a & 0x8000), a == 0
        elif opcode == 0x2A:  # ROL A
            old_carry = int(carry); carry = bool(a & 0x8000)
            a = ((a << 1) | old_carry) & 0xFFFF; negative, zero = bool(a & 0x8000), a == 0
        elif opcode in (0x18, 0x38):  # CLC / SEC
            carry = opcode == 0x38
        elif opcode in (0x69, 0xE9, 0xC9, 0x29, 0x09, 0x49):
            immediate = int.from_bytes(rom[pc:pc + 2], "little"); pc += 2
            if opcode == 0x69:
                result = a + immediate + int(carry); carry = result > 0xFFFF
                a = result & 0xFFFF
            elif opcode == 0xE9:
                result = a - immediate - (0 if carry else 1); carry = result >= 0
                a = result & 0xFFFF
            elif opcode == 0xC9:
                result = (a - immediate) & 0xFFFF; carry = a >= immediate
                negative, zero = bool(result & 0x8000), result == 0
                continue
            elif opcode == 0x29: a &= immediate
            elif opcode == 0x09: a |= immediate
            else: a ^= immediate
            negative, zero = bool(a & 0x8000), a == 0
        elif opcode in (0x30, 0x10, 0xF0, 0xD0, 0x90, 0xB0, 0x80):
            offset = rom[pc]; pc += 1
            take = {0x30: negative, 0x10: not negative, 0xF0: zero,
                    0xD0: not zero, 0x90: not carry, 0xB0: carry, 0x80: True}[opcode]
            if take: pc += offset - 256 if offset & 0x80 else offset
        elif opcode == 0xEA:  # NOP
            pass
        elif opcode == 0x60:  # RTS
            signed = a if a < 0x8000 else a - 0x10000
            # CODE_B5C92D tests BMI on this result: every signed-negative value
            # means “no floor at this local X”, not “handler unsupported”.
            return -1 if signed < 0 else min(signed, 31)
        else:
            return -2
    return -2


def constant_collision_height(word, rom):
    """Compatibility check for simple property handlers; flagged ceilings unknown."""
    if word & 0x4000:
        return -2
    index = word & 255
    x_offset = 15 if word & 0x8000 else 0
    return execute_collision_handler(index, x_offset, rom)


def build_flat_surfaces(map_raw, props, rom, max_cols):
    metatile_cols = min(len(map_raw) // MAP_COL_BYTES, max_cols)
    cols, rows = metatile_cols * 32, MAP_ROWS
    values = [-1] * (cols * rows)
    cache = {}
    for col in range(metatile_cols):
        for row in range(rows):
            offset = col * MAP_COL_BYTES + row * 2
            word = int.from_bytes(map_raw[offset:offset + 2], "little")
            index = word & 0x3FFF
            if index >= len(props):
                continue
            pair = (props[index]["left"], props[index]["right"])
            for local_x in range(32):
                sample_x = 31 - local_x if word & 0x4000 else local_x
                prop = pair[1 if sample_x >= 16 else 0]
                pixel_x = sample_x & 0x0F
                if prop & 0x8000:
                    pixel_x ^= 0x0F
                if word & 0x4000:
                    prop ^= 0x8000
                # The native routine tests the MAP word's H flip, not $4000 in
                # the selected property value. V-flip is also not a collision
                # flag. Both bits had made valid surfaces fall back to a solid
                # metatile grid and caused invisible walls.
                key = (prop & 0xFF, pixel_x)
                if key not in cache:
                    cache[key] = execute_collision_handler(key[0], key[1], rom)
                values[row * cols + col * 32 + local_x] = cache[key]
    return {"cols": cols, "rows": rows, "rle": rle_encode(values),
            "status": "source-bytecode-subset", "unknown_cells": values.count(-2),
            "source": "DATA_B5CA38 immediate arithmetic/short-branch interpreter; unsupported properties remain -2"}


def verified_room_capture(map_raw, rom):
    """Accept only a snapshot whose ROM/RAM hashes and complete map slice match."""
    folder = os.path.join(TOOLS_DIR, "..", "assets-raw", "pirate")
    report_path = os.path.join(folder, "reference-snapshot-report.json")
    if not os.path.isfile(report_path):
        return None
    with open(report_path, encoding="utf-8") as fh:
        report = json.load(fh)
    if report.get("rom_sha256") != hashlib.sha256(rom).hexdigest() or report.get("level") != 3:
        return None
    with open(os.path.join(folder, "reference-wram.bin"), "rb") as fh:
        ram = fh.read()
    if hashlib.sha256(ram).hexdigest() != report.get("wram_sha256"):
        raise ValueError("reference snapshot changed; capture report is stale")
    actual_level = int.from_bytes(ram[0xD3:0xD5], "little")
    camera_max = [int.from_bytes(ram[a:a + 2], "little") for a in (0xAFC, 0xAFE)]
    if actual_level != 3 or camera_max != report.get("camera_max"):
        raise ValueError("room or camera metadata contradicts captured RAM")
    bank, base = report["map_bank"], report["map_base"]
    offset = report["map_probe_source_offset"]
    size = report["main_room_map_bytes"]
    if bank not in (0x7E, 0x7F) or offset < 0 or size <= 0 or size % MAP_COL_BYTES:
        raise ValueError("invalid original room boundary evidence")
    captured = ram[(bank - 0x7E) * 65536 + base:(bank - 0x7E) * 65536 + base + size]
    if captured != map_raw[offset:offset + size]:
        raise ValueError("decoded room does not match original RAM byte for byte")
    return {"source_offset": offset, "bytes": size,
            "camera_max": camera_max, "wram_sha256": report["wram_sha256"],
            "rom_sha256": report["rom_sha256"], "status": "captured-byte-verified"}


def build_level(source, out_dir):
    """Decodifica nivel + gera artefatos visuais. Sempre com provenance."""
    src_files = {
        "map": "LevelData/ShipDeckLevels.bin",
        "defs": "Tilemaps/Map32/Layer1_Level_ShipDeck.bin",
        "gfx1": "Graphics/Compressed/GFX_Layer1_Level_ShipDeck.bin",
        "gfx2": "Graphics/Compressed/GFX_Layer2_Level_ShipDeck.bin",
        "objects": "LevelData/SpriteData/PiratePanic_Main.bin",
        "palette": "Palettes/FGBG_Level_PiratePanic.bin",
    }
    dec = {}
    probes = []
    for key, rel in src_files.items():
        p = os.path.join(source, rel)
        if not os.path.exists(p):
            probes.append({"file": rel, "result": "missing"})
            continue
        raw = open(p, "rb").read()
        entry = {"file": rel, "src_size": len(raw),
                 "src_sha256": hashlib.sha256(raw).hexdigest()}
        if key in ("objects", "palette"):
            dec[key] = raw
            entry["result"] = "raw"
        else:
            try:
                out = cmp_decompress(raw)
                dec[key] = out
                entry.update({"result": "cmp-decoded", "out_size": len(out),
                              "out_sha256": hashlib.sha256(out).hexdigest()})
            except CmpError as e:
                entry["result"] = "rejected: %s" % e
        probes.append(entry)

    ddir = os.path.join(out_dir, "_decoded")
    os.makedirs(ddir, exist_ok=True)
    for key, data in dec.items():
        with open(os.path.join(ddir, "%s.bin" % key), "wb") as fh:
            fh.write(data)

    level = {
        "status": "decoded-partial",
        "codecs": {"cmp": "CODE_BB8D91 original (port fiel)"},
        "probes": probes,
    }

    # ROM da propria disassembly (fonte para colisao e sprite IDs)
    rom = None
    for cand in ("Donkey Kong Country 2 (USA V1.0).sfc", "dkc2.sfc"):
        p = os.path.join(source, cand)
        if os.path.exists(p):
            rom = open(p, "rb").read()
            break

    # colisao: extrai a tabela do ROM da propria disassembly
    if rom and len(rom) >= FC_TABLE_ROM_OFFSET + FC_TABLE_BYTES:
        fc = rom[FC_TABLE_ROM_OFFSET:FC_TABLE_ROM_OFFSET + FC_TABLE_BYTES]
        with open(os.path.join(ddir, "collision_fc6154.bin"), "wb") as fh:
            fh.write(fc)
        level["collision"] = {
            "table": "_decoded/collision_fc6154.bin",
            "rom_offset": "0x%X" % FC_TABLE_ROM_OFFSET,
            "entries": FC_TABLE_BYTES // 4,
            "entry_words": ["left", "right"],
            "property_index": "word & $FF -> DATA_B5CA38 (CODE_B5C92D)",
            "budget": "IDs >= $AA (170) sao decorativos, sem colisao",
            "sha256": hashlib.sha256(fc).hexdigest(),
        }
        if rom:
            level["rom_sha256"] = hashlib.sha256(rom).hexdigest()

    # ROM da propria disassembly (fonte para colisao e sprite IDs)
    rom = None
    for cand in ("Donkey Kong Country 2 (USA V1.0).sfc", "dkc2.sfc"):
        p = os.path.join(source, cand)
        if os.path.exists(p):
            rom = open(p, "rb").read()
            break

    # objetos / spawn
    if "objects" in dec:
        objs = parse_objects(dec["objects"])
        names = load_sprite_id_names(os.path.join(source, "Misc_Defines_DKC2.asm"))
        resolve_object_sprite_ids(objs, rom, names)
        for o in objs:
            o["feet_y"] = o["y_raw"] - OBJ_Y_FEET_BIAS
        xs = [o["x"] for o in objs]
        ys = [o["feet_y"] for o in objs]
        level["objects"] = {
            "file": "_decoded/objects.bin",
            "count": len(objs),
            "record_bytes": OBJ_RECORD,
            "coord_bias": OBJ_XY_BIAS,
            "feet_bias": OBJ_Y_FEET_BIAS,
            "bbox": {"x_min": min(xs), "x_max": max(xs),
                     "y_min": min(ys), "y_max": max(ys)} if objs else None,
            "items": objs,
        }
    level["subareas"] = parse_pirate_panic_subareas(source, rom)
    extract_captains_kabin_assets(
        source, out_dir, level["subareas"]["captains_kabin"])
    # header original (DATA_FD4C8A) -> limites + spawn do nivel main
    header_recs = parse_header(rom) if rom else []
    level["header_records"] = {
        "source": "RomMap DATA_FD4C8A (PiratePanic_Main $0003)",
        "format": "(flags:u8, x_raw:u16, y_raw:u16) em FD4C8A+11, ate flags=$FF",
        "bias": {"x": OBJ_XY_BIAS, "feet_y": OBJ_Y_FEET_BIAS},
        "records": header_recs,
    }
    main_recs = [r for r in header_recs if r["flags"] == 0x00]
    goal_recs = [r for r in header_recs if r["flags"] == 0x00]
    spawn = None
    goal = None
    if main_recs:
        spawn = {"x": main_recs[0]["x"], "feet_y": main_recs[0]["feet_y"],
                 "source": "header R%d (flags=0x00)" % main_recs[0]["index"]}
        if len(goal_recs) > 1:
            last = goal_recs[-1]
            goal = {"x": last["x"], "feet_y": last["feet_y"],
                    "source": "header R%d (flags=0x00)" % last["index"]}
    level["spawn"] = {
        "status": "derived" if spawn else "unproven",
        "x": spawn and spawn["x"], "feet_y": spawn and spawn["feet_y"],
         "note": "primeiro registro flags=0x00 do header; origem raw (304,465) "
                 "observada no primeiro frame de gameplay original. feet_y e "
                 "nome legado, nao altura de hitbox original.",
        "record": spawn,
        "goal": goal,
    }

    # mapa + defs + tiles + render
    pal_rgb = []
    if all(k in dec for k in ("map", "defs", "gfx1", "palette")):
        map_raw, defs_raw, gfx_raw = dec["map"], dec["defs"], dec["gfx1"]
        ncol = len(map_raw) // MAP_COL_BYTES
        ids = []
        for c in range(ncol):
            for r in range(MAP_ROWS):
                off = c * MAP_COL_BYTES + r * 2
                ids.append((map_raw[off] | (map_raw[off + 1] << 8)) & 0x3FFF)
        pal_rgb = [decode_bgr555_word(dec["palette"][i] | (dec["palette"][i + 1] << 8))
                   for i in range(0, len(dec["palette"]) - 1, 2)]
        tiles = decode_gfx_4bpp(gfx_raw)
        level["map"] = {
            "file": "_decoded/map.bin",
            "layout": "column-major",
            "cols": ncol, "rows": MAP_ROWS,
            "width_px": ncol * 32, "height_px": MAP_ROWS * 32,
            "metatile_px": 32,
            "max_metatile_id": max(ids), "distinct_ids": len(set(ids)),
            "flip_flags": {"h": 0x4000, "v": 0x8000},
        }
        level["defs"] = {
            "file": "_decoded/defs.bin",
            "count": len(defs_raw) // 32,
            "entry_bytes": 32, "layout": "4x4 tile words row-major",
            "tile_word": "bits0-9 tile, 10-12 paleta, 13 prio, 14 H, 15 V",
        }
        level["tiles"] = {
            "file": "_decoded/gfx1.bin",
            "count": len(tiles), "bpp": 4, "tile_bytes": 32,
        }
        level["palette"] = {
            "file": "_decoded/palette.bin",
            "colors": len(pal_rgb), "format": "BGR555 LE",
        }

        os.makedirs(out_dir, exist_ok=True)
        sheet = render_tile_sheet(gfx_raw, pal_rgb)
        sheet.save(os.path.join(out_dir, "tile_sheet_shipdeck.png"))
        level["tiles"]["sheet_png"] = "tile_sheet_shipdeck.png"

        img = render_level(map_raw, defs_raw, gfx_raw, pal_rgb)
        img.save(os.path.join(out_dir, "ship_deck_map.png"))
        level["map"]["render_png"] = "ship_deck_map.png"
        level["map"]["render_px"] = {"w": img.width, "h": img.height}

        # preview recortado na bbox dos objetos (coords do jogo = mapa+256)
        bb = level.get("objects", {}).get("bbox")
        if bb:
            x0 = max(0, min(img.width, bb["x_min"] - 320))
            x1 = max(0, min(img.width, bb["x_max"] + 320))
            if x1 > x0:
                img.crop((x0, 0, x1, img.height)).save(
                    os.path.join(out_dir, "ship_deck_preview.png"))
                level["map"]["preview_png"] = "ship_deck_preview.png"
                level["map"]["preview_px"] = {"w": x1 - x0, "h": img.height,
                                              "x0": x0, "x1": x1}

    # colisao: tabela de propriedades por metatile ID (budget 170) + grade
    props = []
    if rom:
        props = collision_property_map(rom)
        level["collision_map"] = {
            "budget": COLL_BUDGET,
            "rule": "ID < 170 e ID != 0 -> colidivel; ID >= 170 -> decorativo "
                    "(sem colisao); ID 0 -> ar",
            "word_rule": "word == 0 -> sub-coluna vazia; flag $40 -> plataforma; "
                         "demais -> solido (conservador)",
            "entries": props,
        }

    # limites do nivel main: derivados SOMENTE do header (nao do bbox dos
    # objetos -- bbox nao e nivel). O trecho do mapa cobre [0, x_max].
    hdr_max_x = max([r["x"] for r in header_recs], default=0)
    x_max = (int((hdr_max_x + 256 + 31) // 32) * 32) if header_recs else 0
    level["limits"] = {
        "status": "estimated",
        "x_min": 0,
        "x_max": x_max,
        "y_min": 0,
        "y_max": MAP_ROWS * 32,
        "source": "header DATA_FD4C8A: maior x dos registros + 256px de folga, "
                  "arredondado para 32px; spawn/goal vem dos registros "
                  "flags=0x00",
    }
    runtime_map = dec.get("map", b"")
    captured_room = verified_room_capture(runtime_map, rom) if rom and runtime_map else None
    if captured_room and pal_rgb:
        start = captured_room["source_offset"]
        runtime_map = runtime_map[start:start + captured_room["bytes"]]
        level["main_room"] = captured_room
        # Original camera max is in cartridge coordinates; world X subtracts $100.
        # Adding the native 256px viewport cancels that bias at the right edge.
        x_max = captured_room["camera_max"][0]
        level["limits"].update(status="captured-byte-verified", x_max=x_max,
                               source="same-ROM original RAM room/camera snapshot; full decoded slice verified")
        runtime_image = render_level(runtime_map, dec["defs"], dec["gfx1"], pal_rgb)
        runtime_image.save(os.path.join(out_dir, "main_room_map.png"))
    if "map" in level:
        gcols, grows, grid = build_collision_grid(
            runtime_map, props if rom else [], max_cols=x_max // 32)
        level["collision_grid"] = {
            "cols": gcols, "rows": grows,
            "tile_px": 16,
            "rle": rle_encode(grid),
        }
        if rom:
            level["flat_surfaces"] = build_flat_surfaces(runtime_map, props, rom, x_max // 32)

    level["hypotheses"] = [
        {"id": "H1", "claim": "stream CMP CODE_BB8D91 decodifica os bins "
                              "Compressed/ e os level data",
         "result": "PROVADO", "evidence": "GFX_Layer1 = 29376B = 918 tiles x 32B; "
                   "Map32 words cobrem exatamente os 918 tiles; sem erros de "
                   "stream em map/defs/gfx"},
        {"id": "H2", "claim": "ShipDeckLevels = mapa de metatiles coluna-major "
                              "(16 words/col); Map32 = 376 defs x 32B",
         "result": "PROVADO", "evidence": "offset (X&$FFE0)+((Y&$1E0)>>4) em "
                   "CODE_B5ACA8/ACB7; ASL x5 = ID*32 em CODE_B5ACF3; IDs "
                   "0..375 completos no mapa; 376 defs x 32B = 12032B"},
        {"id": "H3", "claim": "objeto = registro 8B (type,x_raw,y_raw,param) "
                              "com x/y - $100; colisao = 170 x 4B em FC6154",
         "result": "PROVADO", "evidence": "loop CODE_BBB3D0 (ADC #$0008, "
                   "terminador low byte 0); subtracao $0100 em CODE_BBB390; "
                   "DATA_FC6154..FC63FC = 680B = 170 x 4B (budget $A0=$AA)"},
        {"id": "H4", "claim": "origens x/y normalizadas por $100; ajuste antigo "
                              "$111 nao era prova de colisao",
         "result": "VALIDADO", "evidence": "trace same-ROM de gameplay: origem "
                   "Diddy raw (304,465), igual ao header R0; subtrair 256 produz "
                   "(48,209). Altura de colisao ainda nao portado"},
        {"id": "H5", "claim": "param (w3) e offset em DATA_FBE800 para um "
                              "sprite spawn script (opcodes $XX00); o SpriteID "
                              "vem do par $0000:<sid> apos saltos $8300",
         "result": "VALIDADO", "evidence": "Neek $01E4, Klomp $01EC, DKBarrel "
                   "$01A8, WoodenBox $01BC, KongLetters $0174, BarrelCannon "
                   "$0140 -- nomes reais do enum SpriteID"},
        {"id": "H6", "claim": "registros flags=$40 do header sao posicoes de "
                              "BarrelCannon (objetos 32/41/51)",
         "result": "PROVADO", "evidence": "R3/R4/R5 (x_raw,y_raw) coincidem "
                   "exatamente com os objetos 32/41/51"},
    ]
    level["delta"] = [
        "flat collision handlers decoded from DATA_B5CA38; slopes, ceilings and "
        "conditional/moving collision handlers remain unimplemented",
        "main camera-region table comes from hash-verified RAM; neighbor "
        "interpolation and airborne camera predictor remain incomplete",
        "bonus/cabin/warp sections and native completion route unresolved",
        "original enemy/entity state machines, partner interactions, bonuses and "
        "original audio remain unimplemented",
    ]
    return level


def run(source_arg, out_dir):
    source, source_label = resolve_source(source_arg)
    if source is None:
        print("erro: disassembly nao encontrada (%s)" % source_label, file=sys.stderr)
        return 2
    gfxdir = os.path.join(source, "Graphics", "DynamicSprites")
    pal_path = os.path.join(source, "Palettes", "Sprite_Diddy_Active.bin")
    macros = os.path.join(source, "Routine_Macros_DKC2.asm")
    for need in (gfxdir, pal_path, macros):
        if not os.path.exists(need):
            print("erro: fonte incompleta, falta %s" % need, file=sys.stderr)
            return 2

    os.makedirs(os.path.join(out_dir, "sprites"), exist_ok=True)

    import gfx_assemble
    gfx_assemble.MACROS = macros
    poses = load_poses()
    palette = load_palette(pal_path)

    # sanidade do codec em dado real (decode_tile/encode_tile round-trip)
    with open(os.path.join(gfxdir, "GFX_Diddy_Run1.bin"), "rb") as fh:
        raw = fh.read(32)
    assert encode_tile(decode_tile(raw)) == raw, "codec 4bpp quebrou"

    wanted, skipped_poses = select_poses(poses, gfxdir)
    sprites, skipped = [], list(skipped_poses)
    for n in wanted:
        img, err = render_pose(n, poses, palette, gfxdir=gfxdir)
        if img is None:
            skipped.append({"pose": n, "reason": err})
            continue
        rel = os.path.join("sprites", n + ".png")
        img.save(os.path.join(out_dir, rel))
        sprites.append({"pose": n, "file": rel, "w": img.width, "h": img.height})

    if not sprites:
        print("erro: nada renderizado", file=sys.stderr)
        for s in skipped[:5]:
            print("  pulado: %s (%s)" % (s["pose"], s["reason"]), file=sys.stderr)
        return 1

    # paleta FGBG: 256 bytes = 128 cores BGR555 (decode direto, provado)
    fgbg_rel = os.path.join(source, "Palettes", "FGBG_Level_PiratePanic.bin")
    palette_info = {"file": None, "colors": 0}
    if os.path.exists(fgbg_rel):
        raw = open(fgbg_rel, "rb").read()
        colors = [decode_bgr555_word(raw[i] | (raw[i + 1] << 8))
                  for i in range(0, len(raw) - 1, 2)]
        sw = Image.new("RGB", (16 * 12, ((len(colors) + 15) // 16) * 12), (0, 0, 0))
        swatch = sw.load()  # PixelAccess writes (faster than putpixel)
        for k, (r, g, b) in enumerate(colors):
            ox, oy = (k % 16) * 12, (k // 16) * 12
            for y in range(12):
                for x in range(12):
                    swatch[ox + x, oy + y] = (r, g, b)
        sw.save(os.path.join(out_dir, "palette_fgbg_piratepanic.png"))
        palette_info = {"file": "palette_fgbg_piratepanic.png", "colors": len(colors)}

    proven = {"diddy_palette": os.path.relpath(pal_path, source)}
    level = build_level(source, out_dir)

    lua_path = write_lua(out_dir, sprites, palette_info, level, source_label)

    # ---- artefatos do runtime (gerados, git-ignored) ----
    repo_root = REPO_DIR
    img_root = os.path.join(repo_root, "assets", "images")
    pirate_img = os.path.join(img_root, "pirate")
    os.makedirs(pirate_img, exist_ok=True)

    chunks = []
    runtime_map_png = "main_room_map.png" if level.get("main_room") else "ship_deck_map.png"
    map_png = os.path.join(out_dir, runtime_map_png)
    if os.path.exists(map_png):
        img = Image.open(map_png).convert("RGBA")
        # so o trecho do nivel main (limites do header) vira chunk estatico
        x_cut = level.get("limits", {}).get("x_max") or img.width
        x_cut = max(0, min(img.width, int(x_cut)))
        if x_cut > 0:
            img = img.crop((0, 0, x_cut, img.height))
        raw_chunks = write_level_chunks(img, out_dir, chunk_w=512)
        cdir = os.path.join(pirate_img, "chunks")
        os.makedirs(cdir, exist_ok=True)
        for ch in raw_chunks:
            base = os.path.basename(ch["file"])
            src = os.path.join(out_dir, "chunks", base)
            with open(src, "rb") as fh:
                data = fh.read()
            with open(os.path.join(cdir, base), "wb") as fh:
                fh.write(data)
            chunks.append(ch)

    diddy = write_diddy_sprites(sprites, out_dir, pirate_img, poses)
    enemies = write_enemy_sprites(source, poses, os.path.join(pirate_img, "original"))
    render_lines = ["return {\n"]
    player_art = diddy[0]
    render_lines.append("  player = { height = %d, center_offset_x = %s, center_offset_y = %s },\n" %
                        (player_art["canvas_h"], player_art["canvas_w"] / 2 - player_art["anchor_x"],
                         player_art["canvas_h"] / 2 - player_art["anchor_y"]))
    for entry in enemies:
        render_lines.append('  %s = { animation = "%s", height = %d },\n' %
                            (entry["sprite"], entry["animation"], entry["height"]))
    render_lines.append("}\n")
    render_contents = "".join(render_lines)
    with open(os.path.join(out_dir, "render_info.lua"), "w", encoding="utf-8") as fh:
        fh.write(render_contents)
    runtime_dir = os.path.join(repo_root, "data", "original", "pirate")
    os.makedirs(runtime_dir, exist_ok=True)
    with open(os.path.join(runtime_dir, "render_info.lua"), "w", encoding="utf-8") as fh:
        fh.write(render_contents)
    runtime_path = write_runtime_lua(out_dir, level, chunks, source_label,
                                     repo_root)
    atlas_path, n_anim = write_atlas(repo_root, img_root)
    level["runtime"] = {
        "module": "data/original/pirate/pirate_panic_level.lua",
        "chunks": len(chunks),
        "diddy_frames": len(diddy),
        "diddy_anchor": {"canvas_w": diddy[0]["canvas_w"], "canvas_h": diddy[0]["canvas_h"],
                         "x": diddy[0]["anchor_x"], "y": diddy[0]["anchor_y"],
                         "source": "original OAM coordinate union; not per-frame recentering"},
        "enemy_graphics": enemies,
        "atlas": "main/game.atlas",
        "atlas_animations": n_anim,
    }

    proven_files = [("Palettes/Sprite_Diddy_Active.bin", "palette-sprite"),
                    ("Routine_Macros_DKC2.asm", "poses-oam")]
    proven_files.extend((rel, "captains-kabin-%s" % name)
                        for name, rel, _ in CAPTAINS_KABIN_ASSETS)
    if palette_info["file"]:
        proven_files.append(("Palettes/FGBG_Level_PiratePanic.bin", "palette-fgbg"))
    provenance = []
    for rel, role in list(LEVEL_SOURCES) + proven_files:
        p = os.path.join(source, rel)
        if not os.path.exists(p):
            provenance.append({"file": rel, "role": role, "status": "missing"})
            continue
        provenance.append({"file": rel, "role": role, "status": "recorded",
                           "size": os.path.getsize(p), "sha256": sha256_file(p)})

    manifest = {
        "schema": {
            "version": 1,
            "level.status": "decoded-partial | undecoded",
            "level.map": "{file, layout, cols, rows, width_px, height_px, "
                         "metatile_px, max_metatile_id, distinct_ids, "
                         "flip_flags, render_png, render_px}",
            "level.defs": "{file, count, entry_bytes, layout, tile_word}",
            "level.tiles": "{file, count, bpp, tile_bytes, sheet_png}",
            "level.palette": "{file, colors, format}",
            "level.objects": "{file, count, record_bytes, coord_bias, bbox, "
                             "items:[{index,type,subtype,flags_lo,x,y,x_raw,"
                             "y_raw,param}]}",
            "level.collision": "{table, rom_offset, entries, entry_words, "
                               "property_index, budget, sha256}",
            "level.spawn": "{status, note} — status honesto, nunca inventado",
            "level.header_records": "{source, format, bias, records:[{index,"
                                    "flags,x_raw,y_raw,x,feet_y}]}",
            "level.collision_map": "{budget, rule, word_rule, entries:[{id,"
                                   "left,right,left_property,right_property,"
                                   "left_flags,right_flags,left_class,"
                                   "right_class}]}",
            "level.collision_grid": "{cols, rows, tile_px, rle}",
            "level.subareas": "{level_id, source_file, source_sha256, status, "
                              "objects:[...], assets:{status,files}, "
                              "header:{pointer,header_type,record_offset,"
                              "records,post_record_words,tail_words,status}}",
            "level.limits": "{x_min, x_max, y_min, y_max, source}",
            "level.runtime": "{module, chunks, diddy_frames, atlas, "
                             "atlas_animations}",
            "level.hypotheses": "[{id, claim, result, evidence}]",
            "level.delta": "[str] — lacunas explicitas, sem fabricacao",
        },
        "tool": "tools/import_pirate_panic.py",
        "source_root": source,
        "source_resolved_from": source_label,
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "provenance": provenance,
        "sprites": {"rendered": sprites, "skipped": skipped,
                    "count": len(sprites)},
        "palette_fgbg": palette_info,
        "level": level,
        "outputs": (["sprites/%s.png" % s["pose"] for s in sprites]
                    + ([palette_info["file"]] if palette_info["file"] else [])
                    + ["tile_sheet_shipdeck.png", "ship_deck_map.png",
                       "ship_deck_preview.png"]
                    + ["chunks/levelchunk%03d.png" % i
                       for i in range(len(chunks))]
                    + ["pirate_panic.lua", "pirate_panic_level.lua",
                       "manifest.json"]
                    + ["../assets/images/pirate/diddy/%s" % d["name"]
                       for d in diddy]),
    }
    with open(os.path.join(out_dir, "manifest.json"), "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, indent=2)

    print("sprites: %d renderizados, %d pulados" % (len(sprites), len(skipped)))
    print("nivel: %s (sem dados inventados)" % level["status"])
    print("-> %s" % out_dir)
    return 0


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--source", default="",
                   help="raiz read-only da disassembly (default: env "
                        "DKC2_DISASM, C:\\Projetos\\DKC2-disasm\\DKC2 ou "
                        "tools/vendor/DKC2-disasm/DKC2)")
    p.add_argument("--out", default=os.path.join(REPO_DIR, "assets-raw", "pirate"),
                   help="pasta de saida dentro do workspace")
    p.add_argument("--dump-stats", action="store_true",
                   help="so imprime estatisticas dos streams decodificados")
    a = p.parse_args(argv)
    if a.dump_stats:
        source, label = resolve_source(a.source)
        if source is None:
            print("erro: disassembly nao encontrada (%s)" % label, file=sys.stderr)
            return 2
        dump_stats(source)
        return 0
    return run(a.source, a.out)


if __name__ == "__main__":
    sys.exit(main())
