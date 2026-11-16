"""Conversor PNG <-> .bin para os graficos do DKC2 (tiles SNES 4bpp).

Permite desenhar em Aseprite/Photoshop/GIMP em vez de editar tiles crus, e
devolver o resultado para a disassembly sem perder um byte.

    # um arquivo
    python tools/gfx_convert.py decode GFX_Diddy_Run1.bin diddy.png \
        --palette Sprite_Diddy_Active.bin
    python tools/gfx_convert.py encode diddy.png GFX_Diddy_Run1.bin

    # pastas inteiras
    python tools/gfx_convert.py batch-decode <dir_bin> <dir_png> [--palette P]
    python tools/gfx_convert.py batch-encode <dir_png> <dir_bin>

    # garantia: decodificar e recodificar devolve os bytes originais
    python tools/gfx_convert.py verify <dir_bin>

FORMATO
  Tile 4bpp planar, 32 bytes por tile 8x8:
    bytes  0..15 -> linhas 0-7, cada uma (bitplane0, bitplane1)
    bytes 16..31 -> linhas 0-7, cada uma (bitplane2, bitplane3)
    indice do pixel = bp0 | bp1<<1 | bp2<<2 | bp3<<3
  Paleta SNES: BGR555 little-endian, 15 cores (indice 0 = transparente).

POR QUE PNG INDEXADO
  O PNG e gravado em modo palette (16 cores) para o round-trip ser exato: o
  que volta e o INDICE que voce pintou, nao uma cor aproximada. Se o editor
  salvar em RGB, o encode faz o casamento pela paleta e avisa quando alguma
  cor nao existir nela.

SIDECAR
  Junto do PNG vai um `<nome>.png.json` com a contagem real de tiles e a
  paleta usada. Isso preserva sprites cuja contagem nao preenche a ultima
  linha da grade. Editores de imagem nao mexem nesse arquivo.
"""

import argparse
import json
import os
import sys

try:
    from PIL import Image
except ImportError:  # pragma: no cover
    sys.exit("Pillow nao instalado: pip install pillow")

TILE_BYTES = 32
TILE_W = TILE_H = 8
DEFAULT_TILES_PER_ROW = 16


# --- paleta -----------------------------------------------------------------

def load_palette(path):
    """Le uma paleta SNES BGR555 e devolve 16 tuplas RGB (indice 0 = preto)."""
    raw = open(path, "rb").read()
    colors = [(0, 0, 0)]
    for i in range(0, len(raw) - 1, 2):
        v = raw[i] | (raw[i + 1] << 8)
        colors.append((
            (v & 0x1F) * 255 // 31,
            ((v >> 5) & 0x1F) * 255 // 31,
            ((v >> 10) & 0x1F) * 255 // 31,
        ))
        if len(colors) == 16:
            break
    while len(colors) < 16:
        colors.append((255, 0, 255))     # magenta: indice sem cor definida
    return colors


def grayscale_palette():
    """Paleta de trabalho quando nenhuma e informada."""
    return [(0, 0, 0)] + [(i * 17, i * 17, i * 17) for i in range(1, 16)]


# --- codec ------------------------------------------------------------------

def decode_tile(buf):
    """32 bytes -> matriz 8x8 de indices 0..15."""
    px = []
    for y in range(TILE_H):
        p0, p1 = buf[y * 2], buf[y * 2 + 1]
        p2, p3 = buf[16 + y * 2], buf[16 + y * 2 + 1]
        row = []
        for x in range(TILE_W):
            bit = 7 - x
            row.append(((p0 >> bit) & 1)
                       | (((p1 >> bit) & 1) << 1)
                       | (((p2 >> bit) & 1) << 2)
                       | (((p3 >> bit) & 1) << 3))
        px.append(row)
    return px


def encode_tile(px):
    """Matriz 8x8 de indices -> 32 bytes."""
    out = bytearray(TILE_BYTES)
    for y in range(TILE_H):
        p0 = p1 = p2 = p3 = 0
        for x in range(TILE_W):
            idx = px[y][x] & 0x0F
            bit = 7 - x
            p0 |= (idx & 1) << bit
            p1 |= ((idx >> 1) & 1) << bit
            p2 |= ((idx >> 2) & 1) << bit
            p3 |= ((idx >> 3) & 1) << bit
        out[y * 2] = p0
        out[y * 2 + 1] = p1
        out[16 + y * 2] = p2
        out[16 + y * 2 + 1] = p3
    return bytes(out)


# --- arquivo ----------------------------------------------------------------

def decode_file(bin_path, png_path, palette=None, palette_name="",
                tiles_per_row=DEFAULT_TILES_PER_ROW):
    data = open(bin_path, "rb").read()
    n_tiles = len(data) // TILE_BYTES
    # Bytes alem do ultimo tile completo nao sao grafico 4bpp (ha arquivos
    # Layer3/Mode7 com outro formato). Guardamos no sidecar e devolvemos
    # intactos no encode -- descartar aqui corromperia a ROM.
    tail = data[n_tiles * TILE_BYTES:]
    if tail:
        print("  nota: %s tem %d byte(s) fora da grade de tiles; preservados "
              "no sidecar" % (os.path.basename(bin_path), len(tail)),
              file=sys.stderr)
    if n_tiles == 0 and not tail:
        return 0

    # arquivos so com sobra (0 tiles) ainda geram PNG minimo + sidecar, para o
    # encode conseguir reconstruir o original
    per_row = max(1, min(tiles_per_row, n_tiles))
    rows = max(1, (n_tiles + per_row - 1) // per_row)
    img = Image.new("P", (per_row * TILE_W, rows * TILE_H), 0)

    colors = palette or grayscale_palette()
    flat = []
    for c in colors:
        flat.extend(c)
    img.putpalette(flat + [0] * (768 - len(flat)))

    px = img.load()
    for t in range(n_tiles):
        tile = decode_tile(data[t * TILE_BYTES:(t + 1) * TILE_BYTES])
        ox, oy = (t % per_row) * TILE_W, (t // per_row) * TILE_H
        for y in range(TILE_H):
            for x in range(TILE_W):
                px[ox + x, oy + y] = tile[y][x]

    # indice 0 e transparente no SNES
    img.save(png_path, transparency=0)
    with open(png_path + ".json", "w", encoding="utf-8") as fh:
        json.dump({"tiles": n_tiles, "tiles_per_row": per_row,
                   "palette": palette_name,
                   # guardamos as cores usadas: se o editor salvar em RGB,
                   # o encode volta ao indice correto por elas
                   "colors": colors,
                   "source": os.path.basename(bin_path),
                   "tail_hex": tail.hex()}, fh, indent=2)
    return n_tiles


def _reindex(img, colors, png_path):
    """RGB/RGBA -> imagem indexada usando a paleta original.

    Cor exata vira o indice dela; alfa zero vira indice 0 (transparente).
    Uma cor que nao esteja na paleta e um erro do editor (ele saiu do espaco
    de 16 cores do SNES), entao avisamos com a cor e o total de pixels.
    """
    rgba = img.convert("RGBA")
    exact = {}
    for i, c in enumerate(colors):
        exact.setdefault((c[0], c[1], c[2]), i)

    out = Image.new("P", rgba.size, 0)
    flat = []
    for c in colors:
        flat.extend(c[:3])
    out.putpalette(flat + [0] * (768 - len(flat)))

    src, dst = rgba.load(), out.load()
    strangers = {}
    for y in range(rgba.height):
        for x in range(rgba.width):
            r, g, b, alpha = src[x, y]
            if alpha == 0:
                dst[x, y] = 0
                continue
            idx = exact.get((r, g, b))
            if idx is None:
                # cai na mais proxima, mas registra para o usuario saber
                best, bd = 0, None
                for i, c in enumerate(colors):
                    d = (r - c[0]) ** 2 + (g - c[1]) ** 2 + (b - c[2]) ** 2
                    if bd is None or d < bd:
                        best, bd = i, d
                strangers[(r, g, b)] = strangers.get((r, g, b), 0) + 1
                idx = best
            dst[x, y] = idx
    if strangers:
        top = sorted(strangers.items(), key=lambda kv: -kv[1])[:3]
        print("  aviso: %s tem %d cor(es) fora da paleta SNES; aproximadas. "
              "Ex.: %s" % (os.path.basename(png_path), len(strangers),
                           ", ".join("#%02X%02X%02X x%d" % (c[0], c[1], c[2], n)
                                     for c, n in top)), file=sys.stderr)
    return out


def encode_file(png_path, bin_path):
    img = Image.open(png_path)
    meta_path = png_path + ".json"
    meta = {}
    if os.path.exists(meta_path):
        meta = json.load(open(meta_path, encoding="utf-8"))

    if img.mode != "P":
        # Editor salvou em RGB/RGBA. NAO use quantize(): ele inventa uma paleta
        # nova por clusterizacao e os indices saem trocados -- corrompe o
        # sprite em silencio. Mapeamos cada pixel de volta ao indice da paleta
        # original, guardada no sidecar.
        colors = meta.get("colors")
        if not colors:
            sys.exit("erro: %s nao esta indexado e o sidecar nao tem a paleta; "
                     "regere o PNG com `decode` antes de editar"
                     % os.path.basename(png_path))
        img = _reindex(img, [tuple(c) for c in colors], png_path)

    # `or` nao serve aqui: tiles == 0 e valido (arquivo so com sobra) e cairia
    # no fallback, encodando um tile placeholder que nao existe no original
    per_row = meta.get("tiles_per_row")
    if not per_row:
        per_row = max(1, img.width // TILE_W)
    n_tiles = meta.get("tiles")
    if n_tiles is None:
        n_tiles = (img.width // TILE_W) * (img.height // TILE_H)

    px = img.load()
    out = bytearray()
    for t in range(n_tiles):
        ox, oy = (t % per_row) * TILE_W, (t // per_row) * TILE_H
        if ox + TILE_W > img.width or oy + TILE_H > img.height:
            print("  erro: tile %d fora da imagem em %s"
                  % (t, os.path.basename(png_path)), file=sys.stderr)
            return 0
        tile = [[px[ox + x, oy + y] & 0x0F for x in range(TILE_W)]
                for y in range(TILE_H)]
        out += encode_tile(tile)

    out += bytes.fromhex(meta.get("tail_hex", ""))   # sobra fora da grade
    open(bin_path, "wb").write(bytes(out))
    return n_tiles


# --- comandos ---------------------------------------------------------------

def cmd_decode(a):
    pal = load_palette(a.palette) if a.palette else None
    name = os.path.basename(a.palette) if a.palette else ""
    n = decode_file(a.input, a.output, pal, name, a.tiles_per_row)
    print("%s -> %s (%d tiles)" % (a.input, a.output, n))


def cmd_encode(a):
    n = encode_file(a.input, a.output)
    print("%s -> %s (%d tiles)" % (a.input, a.output, n))


def cmd_batch_decode(a):
    pal = load_palette(a.palette) if a.palette else None
    name = os.path.basename(a.palette) if a.palette else ""
    os.makedirs(a.outdir, exist_ok=True)
    n = 0
    for f in sorted(os.listdir(a.indir)):
        if not f.lower().endswith(".bin"):
            continue
        out = os.path.join(a.outdir, f[:-4] + ".png")
        if decode_file(os.path.join(a.indir, f), out, pal, name,
                       a.tiles_per_row):
            n += 1
    print("%d arquivos -> %s" % (n, a.outdir))


def cmd_batch_encode(a):
    os.makedirs(a.outdir, exist_ok=True)
    n = 0
    for f in sorted(os.listdir(a.indir)):
        if not f.lower().endswith(".png"):
            continue
        out = os.path.join(a.outdir, f[:-4] + ".bin")
        if encode_file(os.path.join(a.indir, f), out):
            n += 1
    print("%d arquivos -> %s" % (n, a.outdir))


def cmd_verify(a):
    """Decodifica e recodifica cada .bin; exige bytes identicos.

    Testa os tres caminhos que existem na pratica, porque o editor do usuario
    decide o modo do PNG:
      P    -- editor preservou o modo indexado
      RGB  -- editor salvou em cor (Photoshop em modo RGB)
      RGBA -- editor salvou com canal alfa (Aseprite)
    Verificar so o primeiro esconde corrupcao silenciosa nos outros dois.
    """
    import tempfile
    modes = ["P"] if a.indexed_only else ["P", "RGB", "RGBA"]
    stats = {m: [0, 0] for m in modes}        # [ok, falhou]
    failures = []
    tmp = tempfile.mkdtemp(prefix="gfxverify_")
    files = [f for f in sorted(os.listdir(a.indir)) if f.lower().endswith(".bin")]
    if a.limit:
        files = files[:a.limit]

    for f in files:
        src = os.path.join(a.indir, f)
        original = open(src, "rb").read()
        for mode in modes:
            png = os.path.join(tmp, f[:-4] + ".png")
            back = os.path.join(tmp, f)
            decode_file(src, png)
            if not os.path.exists(png):
                break
            if mode != "P":
                Image.open(png).convert(mode).save(png)
            encode_file(png, back)
            # compara contra o arquivo INTEIRO -- truncar aqui seria corrigir a
            # propria prova e deixaria passar perda de bytes no encode
            if open(back, "rb").read() == original:
                stats[mode][0] += 1
            else:
                stats[mode][1] += 1
                failures.append("%s (%s)" % (f, mode))

    bad = sum(v[1] for v in stats.values())
    for mode in modes:
        ok, nok = stats[mode]
        print("round-trip %-4s: %d OK, %d FALHOU" % (mode, ok, nok))
    for f in failures[:10]:
        print("  FALHOU:", f)
    return 1 if bad else 0


def main():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)

    def add_common(sp):
        sp.add_argument("--palette", help="arquivo .bin de paleta SNES")
        sp.add_argument("--tiles-per-row", type=int, default=DEFAULT_TILES_PER_ROW)

    d = sub.add_parser("decode", help="um .bin -> .png")
    d.add_argument("input"); d.add_argument("output"); add_common(d)
    d.set_defaults(func=cmd_decode)

    e = sub.add_parser("encode", help="um .png -> .bin")
    e.add_argument("input"); e.add_argument("output")
    e.set_defaults(func=cmd_encode)

    bd = sub.add_parser("batch-decode", help="pasta de .bin -> pasta de .png")
    bd.add_argument("indir"); bd.add_argument("outdir"); add_common(bd)
    bd.set_defaults(func=cmd_batch_decode)

    be = sub.add_parser("batch-encode", help="pasta de .png -> pasta de .bin")
    be.add_argument("indir"); be.add_argument("outdir")
    be.set_defaults(func=cmd_batch_encode)

    v = sub.add_parser("verify", help="checa round-trip byte a byte")
    v.add_argument("indir")
    v.add_argument("--limit", type=int, default=0)
    v.add_argument("--indexed-only", action="store_true",
                   help="testa so o modo P (mais rapido)")
    v.set_defaults(func=cmd_verify)

    a = p.parse_args()
    sys.exit(a.func(a) or 0)


if __name__ == "__main__":
    main()
