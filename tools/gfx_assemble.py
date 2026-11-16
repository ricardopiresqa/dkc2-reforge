"""Monta os sprites do DKC2 a partir das poses OAM da disassembly.

Os .bin sao tiras de tiles; o personagem so aparece quando as pecas OAM sao
posicionadas. As poses vivem em `Routine_Macros_DKC2.asm` como blocos:

    DATA_C02601:
        db $02,$09,$04,$00,$00,$0D,$10,$04,$89,$59,...
        incbin "Graphics/DynamicSprites/GFX_Diddy_Run1.bin"

FORMATO (deduzido lendo CODE_B59C0C / CODE_B59D3E / CODE_B59E05 / CODE_B59E73)

  Cabecalho, 8 bytes:
    [0] quantidade de pecas 16x16
    [1] quantidade de pecas 8x8
    [2] tile VRAM inicial do grupo A de 8x8 (CODE_B59E73: $34 = $38 + base)
    [3] quantidade do grupo B de 8x8
    [4] tile VRAM inicial do grupo B        (CODE_B59EDF: $34 = $3A + base)
    [5] tiles do bloco 1 de VRAM
    [6] deslocamento, em tiles, do bloco 2 dentro da VRAM
    [7] tiles do bloco 2

  Entradas, 2 bytes cada, logo apos o cabecalho: (X, Y) com vies 128.
  Ordem: 16x16, depois grupo A de 8x8, depois grupo B de 8x8.

  Conferido em 3.194 de 3.194 poses (100%):
    tiles    == hdr[0]*4 + hdr[1] + hdr[3]
    entradas == hdr[0]   + hdr[1] + hdr[3]

  Numeracao de tiles (CODE_B59E4E):
    16x16 -> T avanca +2 por peca e +16 ao cruzar o bit 4; a peca usa
             {T, T+1, T+16, T+17} -- o padrao de 16x16 numa grade VRAM
    8x8 A -> T comeca em cabecalho[2] e avanca +1 (CODE_B59EC7)
    8x8 B -> T comeca em cabecalho[4] e avanca +1 (CODE_B59F33)

  O .bin e copiado para a VRAM em DOIS blocos, entao o indice no arquivo nao
  e o numero do tile:
    T <  cabecalho[5]  -> indice = T
    T >= cabecalho[6]  -> indice = cabecalho[5] + (T - cabecalho[6])

    python tools/gfx_assemble.py --sprite GFX_Diddy_Run1.bin -o diddy.png
    python tools/gfx_assemble.py --match "Diddy_Run" --sheet -o corrida.png
    python tools/gfx_assemble.py --coverage
"""

import argparse
import os
import re
import sys

try:
    from PIL import Image, ImageDraw
except ImportError:  # pragma: no cover
    sys.exit("Pillow nao instalado: pip install pillow")

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gfx_convert import TILE_BYTES, TILE_W, TILE_H, decode_tile, load_palette  # noqa: E402

DISASM = os.environ.get("DKC2_DISASM", os.path.join(os.path.dirname(os.path.abspath(__file__)), "vendor", "DKC2-disasm", "DKC2"))
MACROS = os.path.join(DISASM, "Routine_Macros_DKC2.asm")
GFXDIR = os.path.join(DISASM, "Graphics", "DynamicSprites")
PALDIR = os.path.join(DISASM, "Palettes")

BIAS = 128
BLOCK = re.compile(
    r"^DATA_([0-9A-F]{6}):\n((?:\tdb [^\n]*\n)+)"
    r"\tincbin \"Graphics/DynamicSprites/([^\"]+)\"", re.M)


def load_poses():
    src = open(MACROS, encoding="utf-8", errors="replace").read()
    poses = {}
    for m in BLOCK.finditer(src):
        vals = [int(x, 16) for x in re.findall(r"\$([0-9A-F]{2})", m.group(2))]
        poses.setdefault(os.path.basename(m.group(3)), vals)
    return poses


def read_tiles(name, gfxdir=None):
    path = os.path.join(gfxdir or GFXDIR, name)
    if not os.path.exists(path):
        return []
    data = open(path, "rb").read()
    return [decode_tile(data[i * TILE_BYTES:(i + 1) * TILE_BYTES])
            for i in range(len(data) // TILE_BYTES)]


def vram_to_index(t, hdr):
    """Numero do tile em VRAM -> indice dentro do .bin (dois blocos)."""
    chunk1, offset = hdr[5], hdr[6]
    if t < chunk1:
        return t
    if t >= offset:
        return chunk1 + (t - offset)
    return None                      # buraco entre os blocos


def build_pieces(hdr):
    """[(x, y, largura_em_tiles, [indices])], ou None se a pose estiver
    truncada."""
    if len(hdr) < 8:
        return None
    big, small, small_start = hdr[0], hdr[1], hdr[2]
    third, third_start = hdr[3], hdr[4]
    entries = hdr[8:]
    if len(entries) < (big + small + third) * 2:
        return None

    pieces = []
    t = 0
    for i in range(big):
        x = entries[i * 2] - BIAS
        y = entries[i * 2 + 1] - BIAS
        pieces.append((x, y, 2,
                       [vram_to_index(v, hdr) for v in (t, t + 1, t + 16, t + 17)]))
        t += 2
        if t & 0x10:                 # cruzou a metade da linha: pula uma linha
            t += 16

    # dois grupos de 8x8, com tiles iniciais diferentes (CODE_B59E73 e
    # CODE_B59EDF); ambos avancam +1
    i = big
    for start, count in ((small_start, small), (third_start, third)):
        t = start
        for _ in range(count):
            x = entries[i * 2] - BIAS
            y = entries[i * 2 + 1] - BIAS
            pieces.append((x, y, 1, [vram_to_index(t, hdr)]))
            t += 1
            i += 1
    return pieces


def render_pose(name, poses, palette, pad=6, gfxdir=None):
    tiles = read_tiles(name, gfxdir)
    if not tiles:
        return None, "sem tiles"
    hdr = poses.get(name)
    if hdr is None:
        return None, "sem pose no asm"
    pieces = build_pieces(hdr)
    if pieces is None:
        return None, "pose truncada"

    xs, ys = [], []
    for x, y, w, _ in pieces:
        xs += [x, x + w * TILE_W]
        ys += [y, y + w * TILE_H]
    x0, x1 = min(xs) - pad, max(xs) + pad
    y0, y1 = min(ys) - pad, max(ys) + pad

    img = Image.new("RGBA", (x1 - x0, y1 - y0), (0, 0, 0, 0))
    px = img.load()
    for x, y, w, idxs in pieces:
        for k, ti in enumerate(idxs):
            if ti is None or ti >= len(tiles):
                continue
            ox = x - x0 + (k % w) * TILE_W
            oy = y - y0 + (k // w) * TILE_H
            tile = tiles[ti]
            for yy in range(TILE_H):
                for xx in range(TILE_W):
                    idx = tile[yy][xx]
                    if idx and 0 <= ox + xx < img.width and 0 <= oy + yy < img.height:
                        c = palette[idx]
                        px[ox + xx, oy + yy] = (c[0], c[1], c[2], 255)
    return img, None


def on_bg(img, zoom, bg=(52, 52, 64)):
    flat = Image.new("RGB", img.size, bg)
    flat.paste(img, (0, 0), img)
    return flat.resize((flat.width * zoom, flat.height * zoom), Image.NEAREST)


def cmd_coverage(poses):
    total = ok = short = missing = 0
    for name, hdr in poses.items():
        if not os.path.exists(os.path.join(GFXDIR, name)):
            missing += 1
            continue
        total += 1
        if build_pieces(hdr) is None:
            short += 1
        else:
            ok += 1
    print("poses com .bin presente : %d" % total)
    print("  montaveis             : %d (%.1f%%)" % (ok, 100.0 * ok / total))
    print("  entradas insuficientes: %d" % short)
    print("  .bin ausente          : %d" % missing)


def main():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("-o", "--output")
    p.add_argument("--sprite")
    p.add_argument("--match")
    p.add_argument("--palette", default=os.path.join(PALDIR, "Sprite_Diddy_Active.bin"))
    p.add_argument("--zoom", type=int, default=4)
    p.add_argument("--cols", type=int, default=8)
    p.add_argument("--limit", type=int, default=40)
    p.add_argument("--sheet", action="store_true")
    p.add_argument("--coverage", action="store_true")
    p.add_argument("--gfxdir",
                   help="pasta alternativa de .bin -- use para pre-visualizar "
                        "sprites que voce editou, sem tocar na disassembly")
    a = p.parse_args()

    poses = load_poses()
    if a.coverage:
        return cmd_coverage(poses)
    if not a.output:
        sys.exit("-o e obrigatorio")

    palette = load_palette(a.palette)
    if a.sprite:
        names = [os.path.basename(a.sprite)]
    elif a.match:
        names = sorted(n for n in poses if a.match.lower() in n.lower())[:a.limit]
    else:
        sys.exit("informe --sprite, --match ou --coverage")

    panels, skipped = [], []
    for n in names:
        img, err = render_pose(n, poses, palette, gfxdir=a.gfxdir)
        if img is None:
            skipped.append((n, err))
            continue
        panels.append((on_bg(img, a.zoom),
                       n.replace("GFX_", "").replace(".bin", "")[:22]))

    if not panels:
        for n, e in skipped[:5]:
            print("  pulado: %s (%s)" % (n, e), file=sys.stderr)
        sys.exit("nada renderizado")

    if len(panels) == 1 and not a.sheet:
        panels[0][0].save(a.output)
    else:
        cw = max(q[0].width for q in panels)
        ch = max(q[0].height for q in panels)
        cols = min(a.cols, len(panels))
        rows = (len(panels) + cols - 1) // cols
        sheet = Image.new("RGB", (cols * (cw + 8), rows * (ch + 22)), (24, 24, 30))
        d = ImageDraw.Draw(sheet)
        for i, (im, label) in enumerate(panels):
            x, y = (i % cols) * (cw + 8), (i // cols) * (ch + 22)
            sheet.paste(im, (x, y + 16))
            d.text((x + 2, y + 3), label, fill=(230, 230, 230))
        sheet.save(a.output)

    print("renderizados: %d | pulados: %d -> %s" % (len(panels), len(skipped), a.output))
    for n, e in skipped[:5]:
        print("  pulado: %s (%s)" % (n, e))


if __name__ == "__main__":
    main()
