"""Descobre a largura de montagem de um sprite do DKC2 e renderiza a figura.

Os .bin sao tiras lineares de tiles 8x8. Quando dispostos na largura certa,
formam o personagem -- os graficos dinamicos do DKC2 sao blocos retangulares
copiados para a VRAM. Este utilitario testa todas as larguras que dividem a
contagem de tiles e escolhe a que minimiza a descontinuidade entre tiles
vizinhos (a costura vertical e horizontal).

NAO interpreta os cabecalhos de pose/OAM. Para sprites montados a partir de
varias entradas OAM com espacos, o palpite pode nao ser o arranjo final do
jogo -- por isso `--all` mostra todas as larguras lado a lado para voce
escolher a olho.

    python tools/gfx_layout.py <sprite.bin> --palette <pal.bin> -o saida.png
    python tools/gfx_layout.py <sprite.bin> --palette <pal.bin> --all -o grade.png
    python tools/gfx_layout.py <dir> --palette <pal.bin> --sheet -o folha.png
"""

import argparse
import os
import sys

try:
    from PIL import Image, ImageDraw
except ImportError:  # pragma: no cover
    sys.exit("Pillow nao instalado: pip install pillow")

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gfx_convert import (TILE_BYTES, TILE_W, TILE_H, decode_tile,  # noqa: E402
                         load_palette, grayscale_palette)


def tiles_of(path):
    data = open(path, "rb").read()
    n = len(data) // TILE_BYTES
    return [decode_tile(data[i * TILE_BYTES:(i + 1) * TILE_BYTES])
            for i in range(n)]


def seam_cost(tiles, per_row):
    """Soma das diferencas de indice ao longo das costuras entre tiles.

    Quanto menor, mais os tiles vizinhos 'continuam' um no outro -- sinal de
    que a largura corresponde ao arranjo original. Bordas transparentes
    (indice 0 dos dois lados) nao contam, senao larguras que empilham vazio
    ganhariam de graca.
    """
    n = len(tiles)
    rows = (n + per_row - 1) // per_row
    cost = pairs = 0
    for r in range(rows):
        for c in range(per_row):
            i = r * per_row + c
            if i >= n:
                continue
            # costura com o tile a direita
            if c + 1 < per_row and i + 1 < n:
                a, b = tiles[i], tiles[i + 1]
                for y in range(TILE_H):
                    l, rgt = a[y][TILE_W - 1], b[y][0]
                    if l or rgt:
                        cost += 0 if (l != 0) == (rgt != 0) else 1
                        pairs += 1
            # costura com o tile abaixo
            j = i + per_row
            if j < n:
                a, b = tiles[i], tiles[j]
                for x in range(TILE_W):
                    up, dn = a[TILE_H - 1][x], b[0][x]
                    if up or dn:
                        cost += 0 if (up != 0) == (dn != 0) else 1
                        pairs += 1
    return cost / pairs if pairs else 1.0


def candidate_widths(n):
    """Larguras plausiveis: divisores de n, limitados a um formato de sprite."""
    out = [w for w in range(1, n + 1) if n % w == 0 and w <= 16]
    return out or [min(n, 8)]


def render(tiles, per_row, palette):
    n = len(tiles)
    rows = (n + per_row - 1) // per_row
    img = Image.new("RGBA", (per_row * TILE_W, rows * TILE_H), (0, 0, 0, 0))
    px = img.load()
    for i, t in enumerate(tiles):
        ox, oy = (i % per_row) * TILE_W, (i // per_row) * TILE_H
        for y in range(TILE_H):
            for x in range(TILE_W):
                idx = t[y][x]
                if idx:
                    c = palette[idx]
                    px[ox + x, oy + y] = (c[0], c[1], c[2], 255)
    return img


def on_bg(img, zoom, bg=(48, 48, 58)):
    flat = Image.new("RGB", img.size, bg)
    flat.paste(img, (0, 0), img)
    return flat.resize((flat.width * zoom, flat.height * zoom), Image.NEAREST)


def best_width(tiles):
    scored = sorted(((seam_cost(tiles, w), w) for w in candidate_widths(len(tiles))))
    return scored[0][1], scored


def cmd_single(a, palette):
    tiles = tiles_of(a.target)
    if not tiles:
        sys.exit("sem tiles em %s" % a.target)
    w, scored = best_width(tiles)
    print("%s: %d tiles | largura escolhida: %d" % (
        os.path.basename(a.target), len(tiles), w))
    print("  custos por largura:", ", ".join(
        "%d=%.3f" % (ww, cc) for cc, ww in scored[:8]))

    if a.all:
        panels = [(on_bg(render(tiles, ww, palette), a.zoom), "w=%d (%.3f)" % (ww, cc))
                  for cc, ww in scored]
        cw = max(p[0].width for p in panels)
        ch = max(p[0].height for p in panels)
        cols = min(len(panels), 4)
        rows = (len(panels) + cols - 1) // cols
        sheet = Image.new("RGB", (cols * (cw + 10), rows * (ch + 24)), (22, 22, 28))
        d = ImageDraw.Draw(sheet)
        for i, (im, label) in enumerate(panels):
            x, y = (i % cols) * (cw + 10), (i // cols) * (ch + 24)
            sheet.paste(im, (x, y + 18))
            d.text((x + 2, y + 4), label, fill=(235, 235, 235))
        sheet.save(a.output)
    else:
        on_bg(render(tiles, w, palette), a.zoom).save(a.output)
    print("->", a.output)


def cmd_sheet(a, palette):
    files = [f for f in sorted(os.listdir(a.target)) if f.lower().endswith(".bin")]
    if a.limit:
        files = files[:a.limit]
    panels = []
    for f in files:
        tiles = tiles_of(os.path.join(a.target, f))
        if not tiles:
            continue
        w, _ = best_width(tiles)
        panels.append((on_bg(render(tiles, w, palette), a.zoom),
                       f.replace("GFX_", "").replace(".bin", "")[:22]))
    if not panels:
        sys.exit("nenhum sprite em %s" % a.target)
    cw = max(p[0].width for p in panels)
    ch = max(p[0].height for p in panels)
    cols = a.cols
    rows = (len(panels) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * (cw + 8), rows * (ch + 22)), (22, 22, 28))
    d = ImageDraw.Draw(sheet)
    for i, (im, label) in enumerate(panels):
        x, y = (i % cols) * (cw + 8), (i // cols) * (ch + 22)
        sheet.paste(im, (x, y + 16))
        d.text((x + 2, y + 3), label, fill=(225, 225, 225))
    sheet.save(a.output)
    print("%d sprites -> %s" % (len(panels), a.output))


def main():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("target", help="arquivo .bin ou pasta (com --sheet)")
    p.add_argument("-o", "--output", required=True)
    p.add_argument("--palette")
    p.add_argument("--zoom", type=int, default=4)
    p.add_argument("--all", action="store_true",
                   help="mostra todas as larguras candidatas lado a lado")
    p.add_argument("--sheet", action="store_true",
                   help="folha de contato de uma pasta inteira")
    p.add_argument("--cols", type=int, default=8)
    p.add_argument("--limit", type=int, default=0)
    a = p.parse_args()

    palette = load_palette(a.palette) if a.palette else grayscale_palette()
    (cmd_sheet if a.sheet else cmd_single)(a, palette)


if __name__ == "__main__":
    main()
