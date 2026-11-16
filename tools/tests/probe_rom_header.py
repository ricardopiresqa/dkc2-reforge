"""Scratch probe v18: script do param $00D8."""
import os
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TOOLS = os.path.dirname(HERE)
ROM = os.path.join(TOOLS, "vendor", "DKC2-disasm", "DKC2",
                    "Donkey Kong Country 2 (USA V1.0).sfc")


def main():
    rom = open(ROM, "rb").read()
    FBE800, DEFBANK = 0x3BE800, 0x3F0000
    for param in (0x00D8, 0x0300, 0x014C):
        ent = FBE800 + param
        ptr = rom[ent] | (rom[ent + 1] << 8)
        print("param=$%04X ptr=$%04X" % (param, ptr))
        for hop in range(3):
            off = DEFBANK + ptr
            words = [rom[off + 2 * i] | (rom[off + 2 * i + 1] << 8)
                     for i in range(16)]
            print("  hop%d $%04X: %s" % (hop, ptr,
                                         " ".join("$%04X" % w for w in words)))
            if words[0] == 0x8300:
                ptr = words[1]
            else:
                break
    return 0


if __name__ == "__main__":
    sys.exit(main())
