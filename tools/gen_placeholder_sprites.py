"""Gera sprites placeholder (pixel-art chapado) para o pipeline visual.

Saida: assets/images/gen/<categoria>/<nome>.png (RGBA, sem anti-aliasing).
Determinista: mesma entrada -> mesmos bytes. Rodar da raiz do repo:

    python tools/gen_placeholder_sprites.py
"""

import os
from PIL import Image, ImageDraw

OUT_ROOT = os.path.join("assets", "images", "gen")

# --- paleta -----------------------------------------------------------------
FUR        = (150, 92, 42)
SHIRT      = (200, 45, 45)
SKIN       = (232, 190, 138)
ROCK       = (110, 96, 84)
ROCK_TOP   = (140, 126, 110)
DIRT       = (92, 68, 44)
WOOD       = (150, 104, 56)
STEEL      = (128, 134, 142)
ICE        = (176, 214, 230)
WATER      = (44, 110, 200, 150)
GREEN      = (72, 158, 60)
DARKGREEN  = (40, 100, 40)
YELLOW     = (238, 200, 48)
ORANGE     = (226, 130, 40)
PURPLE     = (140, 76, 176)
CYAN       = (86, 200, 214)
BLUE       = (58, 110, 200)
GREY       = (150, 150, 156)
BLACK      = (28, 28, 32)
WHITE      = (244, 244, 240)
GOLD       = (226, 178, 44)
RED        = (206, 48, 48)


def shade(color, factor=0.65):
    """Versao mais escura de uma cor, preservando alpha."""
    r, g, b = color[0], color[1], color[2]
    a = color[3] if len(color) > 3 else 255
    return (int(r * factor), int(g * factor), int(b * factor), a)


def rgba(color):
    return color if len(color) > 3 else (color[0], color[1], color[2], 255)


def canvas(w, h, bg=(0, 0, 0, 0)):
    img = Image.new("RGBA", (w, h), bg)
    return img, ImageDraw.Draw(img)


def rect(d, box, fill, outline=True):
    d.rectangle(box, fill=rgba(fill), outline=shade(fill) if outline else None)


def ellipse(d, box, fill, outline=True):
    d.ellipse(box, fill=rgba(fill), outline=shade(fill) if outline else None)


def poly(d, pts, fill, outline=True):
    d.polygon(pts, fill=rgba(fill), outline=shade(fill) if outline else None)


_COUNT = [0]


def save(img, subdir, name):
    folder = os.path.join(OUT_ROOT, subdir)
    os.makedirs(folder, exist_ok=True)
    img.save(os.path.join(folder, name + ".png"))
    _COUNT[0] += 1


# --- glifos 5x7 para letras (sem depender de fontes do sistema) --------------
GLYPHS = {
    "A": ["01110", "10001", "10001", "11111", "10001", "10001", "10001"],
    "B": ["11110", "10001", "10001", "11110", "10001", "10001", "11110"],
    "G": ["01110", "10001", "10000", "10011", "10001", "10001", "01110"],
    "K": ["10001", "10010", "10100", "11000", "10100", "10010", "10001"],
    "N": ["10001", "11001", "10101", "10101", "10101", "10011", "10001"],
    "O": ["01110", "10001", "10001", "10001", "10001", "10001", "01110"],
}


def glyph(d, ch, x, y, scale, color):
    for row, bits in enumerate(GLYPHS[ch]):
        for col, bit in enumerate(bits):
            if bit == "1":
                d.rectangle(
                    [x + col * scale, y + row * scale,
                     x + col * scale + scale - 1, y + row * scale + scale - 1],
                    fill=rgba(color),
                )


# --- tiles ------------------------------------------------------------------
def gen_tiles():
    img, d = canvas(16, 16)
    rect(d, [0, 0, 15, 15], DIRT, outline=False)
    rect(d, [0, 0, 15, 3], ROCK_TOP, outline=False)
    d.rectangle([0, 0, 15, 15], outline=shade(DIRT, 0.6))
    for x in (4, 11):
        d.point([(x, 8), (x + 1, 11)], fill=shade(DIRT, 0.8))
    save(img, "tiles", "tile_solid")

    img, d = canvas(16, 16)
    rect(d, [0, 0, 15, 5], WOOD, outline=False)
    d.rectangle([0, 0, 15, 5], outline=shade(WOOD, 0.6))
    d.line([(0, 2), (15, 2)], fill=shade(WOOD, 0.8))
    save(img, "tiles", "tile_platform")

    img, d = canvas(16, 16)
    rect(d, [0, 12, 15, 15], ROCK, outline=False)
    for i in range(3):
        x = i * 5 + 1
        poly(d, [(x, 12), (x + 2, 3), (x + 4, 12)], STEEL)
    save(img, "tiles", "tile_spike")

    img, d = canvas(16, 16)
    rect(d, [0, 0, 15, 15], ICE, outline=False)
    d.rectangle([0, 0, 15, 15], outline=shade(ICE, 0.7))
    d.line([(2, 13), (13, 2)], fill=WHITE)
    save(img, "tiles", "tile_slip")

    img, d = canvas(16, 16)
    d.rectangle([0, 0, 15, 15], fill=WATER)
    d.rectangle([0, 0, 15, 2], fill=(120, 180, 235, 190))
    save(img, "tiles", "tile_water")

    img, d = canvas(16, 16)
    rect(d, [0, 0, 15, 15], ROCK, outline=False)
    d.rectangle([0, 0, 15, 15], outline=shade(ROCK, 0.6))
    d.line([(3, 0), (7, 6), (4, 11), (9, 15)], fill=shade(ROCK, 0.5))
    d.line([(12, 2), (9, 8), (13, 13)], fill=shade(ROCK, 0.5))
    save(img, "tiles", "tile_cracked")


# --- player -----------------------------------------------------------------
def _ape(d, leg_a, leg_b, arm_a, arm_b, lean=0, crouch=0):
    """Corpo base do macaco, virado para a direita. Origem 32x32."""
    top = 6 + crouch
    # pernas
    rect(d, [11, 25, 15, 25 + leg_a], FUR)
    rect(d, [17, 25, 21, 25 + leg_b], FUR)
    # tronco (camiseta)
    rect(d, [10 + lean, top + 6, 22 + lean, 26], SHIRT)
    # bracos
    rect(d, [7 + lean, top + 7 + arm_a, 10 + lean, top + 14 + arm_a], FUR)
    rect(d, [22 + lean, top + 7 + arm_b, 25 + lean, top + 14 + arm_b], FUR)
    # cabeca
    ellipse(d, [10 + lean, top - 2, 24 + lean, top + 10], FUR)
    ellipse(d, [15 + lean, top + 1, 23 + lean, top + 8], SKIN)
    # olhos
    d.rectangle([18 + lean, top + 2, 19 + lean, top + 3], fill=BLACK)
    d.rectangle([21 + lean, top + 2, 22 + lean, top + 3], fill=BLACK)


def gen_player():
    for name, legs in (("player_idle_0", (5, 5)), ("player_idle_1", (5, 4))):
        img, d = canvas(32, 32)
        _ape(d, legs[0], legs[1], 0, 0)
        save(img, "player", name)

    run_poses = [(6, 2, -2, 2), (4, 4, 0, 0), (2, 6, 2, -2), (4, 4, 0, 0)]
    for i, (la, lb, aa, ab) in enumerate(run_poses):
        img, d = canvas(32, 32)
        _ape(d, la, lb, aa, ab, lean=1)
        save(img, "player", "player_run_%d" % i)

    img, d = canvas(32, 32)
    _ape(d, 2, 3, -4, -4)
    save(img, "player", "player_jump")

    img, d = canvas(32, 32)
    _ape(d, 6, 6, 3, 3)
    save(img, "player", "player_fall")

    for i in range(4):
        img, d = canvas(32, 32)
        ellipse(d, [6, 8, 26, 28], FUR)
        # marca que gira para indicar rotacao
        marks = [(16, 10), (24, 18), (16, 26), (8, 18)][i]
        ellipse(d, [marks[0] - 3, marks[1] - 3, marks[0] + 3, marks[1] + 3], SHIRT)
        save(img, "player", "player_roll_%d" % i)

    img, d = canvas(32, 32)
    _ape(d, 2, 2, 2, 2, crouch=6)
    save(img, "player", "player_crouch")

    img, d = canvas(32, 32)
    _ape(d, 5, 3, 4, -3, lean=-2)
    d.line([(6, 30), (13, 30)], fill=shade(DIRT, 0.9))
    save(img, "player", "player_skid")

    for i, arm in enumerate((-3, 3)):
        img, d = canvas(32, 32)
        rect(d, [8, 14, 24, 22], SHIRT)
        ellipse(d, [18, 10, 30, 22], FUR)
        ellipse(d, [23, 13, 29, 19], SKIN)
        d.rectangle([26, 14, 27, 15], fill=BLACK)
        rect(d, [4, 16 + arm, 12, 19 + arm], FUR)
        rect(d, [2, 18, 9, 21], FUR)
        save(img, "player", "player_swim_%d" % i)

    img, d = canvas(32, 32)
    rect(d, [5, 8, 27, 28], WOOD)
    for y in (12, 18, 24):
        d.line([(5, y), (27, y)], fill=shade(WOOD, 0.55))
    ellipse(d, [12, 2, 24, 12], FUR)
    save(img, "player", "player_barrel")

    img, d = canvas(32, 32)
    _ape(d, 5, 5, 0, 0)
    tint = Image.new("RGBA", (32, 32), (255, 60, 60, 110))
    img = Image.alpha_composite(img, Image.composite(
        tint, Image.new("RGBA", (32, 32), (0, 0, 0, 0)), img.split()[3]))
    save(img, "player", "player_damage")

    img, d = canvas(32, 32)
    rect(d, [6, 20, 26, 27], SHIRT)
    ellipse(d, [4, 16, 16, 27], FUR)
    d.line([(8, 20), (11, 23)], fill=BLACK)
    d.line([(11, 20), (8, 23)], fill=BLACK)
    rect(d, [24, 16, 27, 22], FUR)
    save(img, "player", "player_death")

    for i, off in enumerate((0, 4)):
        img, d = canvas(32, 32)
        rect(d, [12, 12, 20, 27], SHIRT)
        ellipse(d, [11, 4, 23, 15], FUR)
        rect(d, [8, 8 + off, 12, 11 + off], FUR)
        rect(d, [20, 12 - off, 24, 15 - off], FUR)
        save(img, "player", "player_climb_%d" % i)


# --- inimigos ---------------------------------------------------------------
def gen_enemies():
    for i, jaw in enumerate((0, 2)):
        img, d = canvas(32, 32)
        rect(d, [11, 16, 21, 29], GREEN)
        rect(d, [9, 28, 23, 31], DARKGREEN)
        ellipse(d, [8, 6, 24, 20], GREEN)
        poly(d, [(22, 12), (31, 14 + jaw), (22, 18)], DARKGREEN)
        d.rectangle([14, 10, 16, 12], fill=WHITE)
        d.rectangle([15, 11, 16, 12], fill=BLACK)
        save(img, "enemies", "en_kritter_%d" % i)

    for i, wing in enumerate((0, 3)):
        img, d = canvas(32, 32)
        ellipse(d, [8, 12, 26, 26], YELLOW)
        for band in (13, 18, 23):
            d.rectangle([band, 13, band + 2, 25], fill=BLACK)
        ellipse(d, [4, 14 - wing, 14, 20 - wing], (230, 230, 255, 170))
        ellipse(d, [18, 14 - wing, 28, 20 - wing], (230, 230, 255, 170))
        poly(d, [(26, 18), (31, 20), (26, 22)], BLACK)
        save(img, "enemies", "en_zinger_%d" % i)

    img, d = canvas(32, 32)
    rect(d, [4, 12, 28, 30], BLUE)
    ellipse(d, [8, 2, 26, 16], BLUE)
    d.rectangle([12, 7, 14, 9], fill=WHITE)
    d.rectangle([20, 7, 22, 9], fill=WHITE)
    rect(d, [2, 16, 6, 26], shade(BLUE, 0.8))
    rect(d, [26, 16, 30, 26], shade(BLUE, 0.8))
    save(img, "enemies", "en_krusha")

    for i, wing in enumerate((0, 4)):
        img, d = canvas(32, 32)
        rect(d, [12, 14, 26, 18], CYAN)
        ellipse(d, [22, 12, 30, 20], CYAN)
        ellipse(d, [2, 8 - wing, 18, 14 - wing], (200, 240, 255, 160))
        ellipse(d, [2, 18 + wing, 18, 24 + wing], (200, 240, 255, 160))
        save(img, "enemies", "en_flitter_%d" % i)

    img, d = canvas(32, 32)
    poly(d, [(3, 22), (16, 10), (29, 22)], GREY)
    poly(d, [(3, 24), (16, 30), (29, 24)], shade(GREY, 0.8))
    for x in (10, 16, 22):
        poly(d, [(x - 2, 22), (x, 17), (x + 2, 22)], WHITE)
    save(img, "enemies", "en_klamp")

    img, d = canvas(32, 32)
    rect(d, [8, 6, 24, 28], ORANGE)
    for y in (11, 17, 23):
        d.line([(8, y), (24, y)], fill=shade(ORANGE, 0.55))
    rect(d, [3, 14, 8, 17], ORANGE)
    rect(d, [24, 14, 29, 17], ORANGE)
    d.rectangle([12, 9, 14, 11], fill=WHITE)
    d.rectangle([18, 9, 20, 11], fill=WHITE)
    save(img, "enemies", "en_klobber")

    img, d = canvas(32, 32)
    rect(d, [4, 18, 26, 28], shade(STEEL, 0.75))
    ellipse(d, [2, 20, 12, 30], STEEL)
    rect(d, [22, 14, 31, 24], STEEL)
    d.ellipse([26, 16, 31, 22], fill=BLACK)
    save(img, "enemies", "en_kannon")

    img, d = canvas(32, 32)
    rect(d, [13, 18, 19, 31], shade(PURPLE, 0.8))
    ellipse(d, [8, 6, 26, 20], PURPLE)
    poly(d, [(24, 10), (31, 13), (24, 16)], shade(PURPLE, 0.7))
    d.rectangle([14, 10, 16, 12], fill=YELLOW)
    save(img, "enemies", "en_mininecky")

    img, d = canvas(32, 32)
    rect(d, [7, 8, 25, 29], RED)
    for y in (13, 19, 25):
        d.line([(7, y), (25, y)], fill=shade(RED, 0.55))
    d.line([(16, 8), (19, 2)], fill=WOOD)
    ellipse(d, [18, 0, 22, 4], YELLOW)
    save(img, "enemies", "en_kaboom")

    img, d = canvas(32, 32)
    rect(d, [12, 14, 20, 28], DARKGREEN)
    ellipse(d, [10, 4, 24, 17], DARKGREEN)
    d.line([(10, 14), (2, 4)], fill=STEEL, width=2)
    d.line([(22, 14), (30, 4)], fill=STEEL, width=2)
    d.rectangle([15, 8, 17, 10], fill=YELLOW)
    save(img, "enemies", "en_kutlass")

    img, d = canvas(32, 32)
    rect(d, [8, 12, 24, 30], (120, 84, 48))
    ellipse(d, [7, 1, 25, 16], (120, 84, 48))
    d.rectangle([12, 6, 14, 9], fill=WHITE)
    d.rectangle([19, 6, 21, 9], fill=WHITE)
    rect(d, [24, 6, 28, 24], WOOD)
    save(img, "enemies", "en_kludge")

    img, d = canvas(12, 12)
    ellipse(d, [0, 0, 11, 11], (48, 48, 54))
    d.point([(3, 3), (4, 3), (3, 4)], fill=GREY)
    save(img, "enemies", "en_projectile")


# --- objetos ----------------------------------------------------------------
def gen_objects():
    img, d = canvas(16, 16)
    poly(d, [(3, 3), (13, 8), (7, 14), (2, 9)], YELLOW)
    d.line([(3, 3), (5, 1)], fill=shade(WOOD, 0.7))
    save(img, "objects", "obj_banana")

    img, d = canvas(24, 24)
    for dx in (0, 5, 10):
        poly(d, [(2 + dx, 4), (12 + dx, 10), (6 + dx, 18), (1 + dx, 11)], YELLOW)
    save(img, "objects", "obj_banana_bunch")

    img, d = canvas(20, 20)
    ellipse(d, [0, 0, 19, 19], GOLD)
    ellipse(d, [3, 3, 16, 16], shade(GOLD, 1.15))
    glyph(d, "K", 6, 6, 2, shade(GOLD, 0.5))
    save(img, "objects", "obj_dk_coin")

    img, d = canvas(24, 24)
    ellipse(d, [3, 1, 20, 17], RED)
    poly(d, [(10, 16), (13, 16), (12, 19)], shade(RED, 0.7))
    d.line([(12, 19), (12, 23)], fill=WHITE)
    ellipse(d, [7, 4, 11, 8], (255, 180, 180, 200), outline=False)
    save(img, "objects", "obj_life")

    img, d = canvas(24, 24)
    rect(d, [3, 1, 20, 22], WOOD)
    for y in (6, 12, 18):
        d.line([(3, y), (20, y)], fill=shade(WOOD, 0.5))
    save(img, "objects", "obj_barrel")

    img, d = canvas(24, 24)
    rect(d, [3, 1, 20, 22], (120, 60, 160))
    for y in (5, 19):
        d.line([(3, y), (20, y)], fill=shade((120, 60, 160), 0.5))
    glyph(d, "B", 7, 8, 2, WHITE)
    save(img, "objects", "obj_bonus_barrel")

    img, d = canvas(24, 24)
    rect(d, [2, 3, 21, 21], (170, 130, 80))
    d.rectangle([2, 3, 21, 21], outline=shade((170, 130, 80), 0.5))
    glyph(d, "A", 7, 7, 2, shade((170, 130, 80), 0.4))
    save(img, "objects", "obj_animal_crate")

    for ch in ("K", "O", "N", "G"):
        img, d = canvas(20, 20)
        ellipse(d, [0, 0, 19, 19], WHITE)
        glyph(d, ch, 5, 6, 2, (40, 60, 140))
        save(img, "objects", "obj_letter_" + ch.lower())

    img, d = canvas(8, 16)
    rect(d, [2, 0, 5, 15], (160, 128, 80), outline=False)
    for y in range(0, 16, 4):
        d.line([(2, y), (5, y + 2)], fill=shade((160, 128, 80), 0.6))
    save(img, "objects", "obj_rope")


# --- animal buddies ---------------------------------------------------------
def gen_animals():
    img, d = canvas(32, 32)
    rect(d, [4, 12, 26, 26], GREY)
    ellipse(d, [20, 10, 31, 22], GREY)
    poly(d, [(29, 12), (31, 5), (26, 12)], WHITE)
    rect(d, [6, 25, 9, 30], shade(GREY, 0.8))
    rect(d, [20, 25, 23, 30], shade(GREY, 0.8))
    save(img, "animals", "an_rambi")

    img, d = canvas(32, 32)
    ellipse(d, [4, 11, 26, 23], BLUE)
    poly(d, [(0, 12), (6, 17), (0, 22)], shade(BLUE, 0.8))
    d.line([(26, 17), (31, 17)], fill=STEEL, width=2)
    d.rectangle([20, 14, 22, 16], fill=WHITE)
    save(img, "animals", "an_enguarde")

    img, d = canvas(32, 32)
    ellipse(d, [9, 12, 23, 24], GREEN)
    for dx, dy in ((-7, -4), (-8, 4), (7, -4), (8, 4)):
        d.line([(16, 18), (16 + dx, 18 + dy), (16 + int(dx * 1.5), 28)], fill=shade(GREEN, 0.7))
    d.rectangle([12, 14, 14, 16], fill=WHITE)
    d.rectangle([18, 14, 20, 16], fill=WHITE)
    save(img, "animals", "an_squitter")

    img, d = canvas(32, 32)
    for i in range(4):
        ellipse(d, [2 + i * 6, 16 + (i % 2) * 4, 12 + i * 6, 26 + (i % 2) * 4], YELLOW)
    ellipse(d, [20, 8, 31, 18], YELLOW)
    d.rectangle([27, 11, 29, 13], fill=BLACK)
    save(img, "animals", "an_rattly")

    img, d = canvas(32, 32)
    ellipse(d, [8, 10, 24, 26], GREEN)
    ellipse(d, [18, 4, 30, 16], GREEN)
    poly(d, [(28, 9), (31, 11), (28, 13)], ORANGE)
    ellipse(d, [4, 12, 16, 20], shade(GREEN, 0.75))
    d.rectangle([25, 7, 27, 9], fill=BLACK)
    save(img, "animals", "an_squawks")

    img, d = canvas(32, 32)
    ellipse(d, [6, 12, 22, 24], ORANGE)
    rect(d, [18, 4, 21, 14], ORANGE)
    ellipse(d, [17, 1, 27, 8], ORANGE)
    poly(d, [(26, 4), (30, 5), (26, 7)], YELLOW)
    rect(d, [9, 23, 11, 31], shade(ORANGE, 0.8))
    rect(d, [16, 23, 18, 31], shade(ORANGE, 0.8))
    save(img, "animals", "an_expresso")


# --- bosses -----------------------------------------------------------------
def gen_boss():
    img, d = canvas(64, 64)
    ellipse(d, [10, 20, 52, 54], (46, 46, 54))
    ellipse(d, [34, 8, 60, 32], (46, 46, 54))
    poly(d, [(56, 18), (63, 21), (56, 25)], ORANGE)
    poly(d, [(10, 30), (0, 20), (6, 40)], (30, 30, 38))
    d.rectangle([48, 15, 52, 19], fill=RED)
    save(img, "boss", "boss_krow")

    img, d = canvas(64, 64)
    poly(d, [(30, 4), (36, 4), (36, 34), (30, 34)], STEEL)
    poly(d, [(6, 34), (58, 34), (44, 58), (20, 58)], STEEL)
    d.line([(20, 40), (44, 40)], fill=shade(STEEL, 0.6), width=2)
    ellipse(d, [26, 0, 40, 10], shade(STEEL, 0.8))
    save(img, "boss", "boss_kleaver")

    img, d = canvas(64, 64)
    ellipse(d, [12, 20, 54, 52], YELLOW)
    for band in (22, 32, 42):
        d.rectangle([band, 21, band + 5, 51], fill=BLACK)
    ellipse(d, [2, 14, 30, 30], (235, 235, 255, 170))
    ellipse(d, [34, 14, 62, 30], (235, 235, 255, 170))
    poly(d, [(54, 36), (63, 40), (54, 44)], BLACK)
    save(img, "boss", "boss_zing")

    img, d = canvas(64, 64)
    ellipse(d, [8, 6, 56, 50], (110, 170, 235, 170))
    poly(d, [(8, 40), (16, 58), (24, 44), (32, 58), (40, 44), (48, 58), (56, 40)],
         (110, 170, 235, 170))
    d.ellipse([20, 20, 28, 30], fill=WHITE)
    d.ellipse([36, 20, 44, 30], fill=WHITE)
    save(img, "boss", "boss_kreep")

    img, d = canvas(64, 64)
    poly(d, [(6, 22), (58, 22), (52, 60), (12, 60)], RED)
    rect(d, [16, 26, 48, 58], GREEN)
    ellipse(d, [14, 6, 50, 34], GREEN)
    poly(d, [(46, 14), (63, 20), (46, 26)], DARKGREEN)
    poly(d, [(18, 8), (24, 0), (30, 8), (36, 0), (42, 8)], GOLD)
    d.rectangle([24, 16, 28, 20], fill=YELLOW)
    save(img, "boss", "boss_krool")


# --- backgrounds ------------------------------------------------------------
def gen_bg():
    # 640x360: o renderer desenha estas camadas com escala 2x (economiza atlas)
    w, h = 640, 360
    img = Image.new("RGBA", (w, h))
    d = ImageDraw.Draw(img)
    for y in range(h):
        t = y / (h - 1)
        # topo (y=0) mais escuro; base mais clara -- em Defold a textura nao e invertida
        col = (int(70 + 90 * t), int(130 + 80 * t), int(210 + 30 * t), 255)
        d.line([(0, y), (w, y)], fill=col)
    save(img, "bg", "bg_sky")

    # montanhas e selva crescem a partir da BASE da imagem (o sprite e desenhado
    # na vertical certa pelo Defold; conteudo no topo do PNG ficaria de cabeca
    # para baixo em relacao ao horizonte)
    img, d = canvas(w, h)
    peaks = [(-40, 150), (70, 240), (180, 180), (300, 260), (430, 200), (550, 235), (670, 165)]
    for cx, ph in peaks:
        poly(d, [(cx - 130, h), (cx, h - ph), (cx + 130, h)], (96, 118, 150), outline=False)
    save(img, "bg", "bg_far")

    # copas baixas e escuras: a camada fica atras do nivel e nao pode competir
    # em contraste com tiles, inimigos e coletaveis
    img, d = canvas(w, h)
    for i in range(11):
        cx = i * 64 + 20
        d.rectangle([cx - 4, h - 52, cx + 4, h], fill=(38, 30, 20, 255))
        d.ellipse([cx - 28, h - 78, cx + 28, h - 42], fill=(26, 62, 34, 255))
    save(img, "bg", "bg_mid")


def main():
    gen_tiles()
    gen_player()
    gen_enemies()
    gen_objects()
    gen_animals()
    gen_boss()
    gen_bg()
    print("generated %d sprites" % _COUNT[0])


if __name__ == "__main__":
    main()
