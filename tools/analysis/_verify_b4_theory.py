"""Verify the $B4 memory mapping theory:
- $2224 maps $B4 window to different banks
- JSL $B4xxxx actually calls code from whichever bank $2224 points to
- Find the $2224 value set before each JSL $B4 call
"""

with open('roms/dkc2.sfc', 'rb') as f:
    rom = f.read()

# 1. Check what's at ROM offset 0x00BE60 (if JSL $B4BE60 with $2224=$80 maps to bank $80)
print("=== Verify: if $2224=$80, $B4BE60 = $80BE60 = ROM offset 0x00BE60 ===")
print("  Content at ROM 0x00BE60:")
for i in range(0x00BE60, 0x00BE80):
    b = rom[i]
    print(f"    {i:06X}: {b:02X}", end="")
    if i == 0x00BE60:
        # Check: is it the start of a subroutine? (PHA, PHX, PHY, SEP, REP, etc.)
        print("  <-- First byte of JSL target")
    else:
        print()

# 2. Check code near 0x008CDF (JSL $B4BE60) to find $2224 setting context
print("\n=== Context around JSL $B4BE60 at ROM 0x008CDF ===")
start = 0x008CA0
for i in range(start, min(start+100, 0x008D80)):
    b = rom[i]
    # Interpret the bytes
    if b == 0x22 and i+4 <= len(rom):  # JSL
        dest = rom[i+1] | (rom[i+2] << 8) | (rom[i+3] << 16)
        print(f"  ROM 0x{i:06X}: JSL ${dest:06X}")
        i += 3
    elif b == 0x8D and i+3 <= len(rom):  # STA abs
        addr = rom[i+1] | (rom[i+2] << 8)
        print(f"  ROM 0x{i:06X}: STA ${addr:04X}")
        i += 2
    elif b == 0xA9:  # LDA #xx
        print(f"  ROM 0x{i:06X}: LDA #${rom[i+1]:02X}")
        i += 1
    elif b == 0x48: print(f"  ROM 0x{i:06X}: PHA")
    elif b == 0x68: print(f"  ROM 0x{i:06X}: PLA")
    elif b == 0xDA: print(f"  ROM 0x{i:06X}: PHX")
    elif b == 0xFA: print(f"  ROM 0x{i:06X}: PLX")
    elif b == 0x5A: print(f"  ROM 0x{i:06X}: PHY")
    elif b == 0x7A: print(f"  ROM 0x{i:06X}: PLY")
    elif b == 0xC2: print(f"  ROM 0x{i:06X}: REP #${rom[i+1]:02X}"); i+=1
    elif b == 0xE2: print(f"  ROM 0x{i:06X}: SEP #${rom[i+1]:02X}"); i+=1
    elif b == 0xAD:  # LDA abs
        addr = rom[i+1] | (rom[i+2] << 8)
        print(f"  ROM 0x{i:06X}: LDA ${addr:04X}")
        i += 2
    elif b == 0xAF:  # LDA long
        addr = rom[i+1] | (rom[i+2] << 8) | (rom[i+3] << 16)
        print(f"  ROM 0x{i:06X}: LDA ${addr:06X}")
        i += 3
    elif b == 0x8F:  # STA long
        addr = rom[i+1] | (rom[i+2] << 8) | (rom[i+3] << 16)
        print(f"  ROM 0x{i:06X}: STA ${addr:06X}")
        i += 3
    elif b == 0x9C:  # STZ abs
        addr = rom[i+1] | (rom[i+2] << 8)
        print(f"  ROM 0x{i:06X}: STZ ${addr:04X}")
        i += 2
    elif b in [0x20, 0x4C]:  # JSR/JMP abs
        addr = rom[i+1] | (rom[i+2] << 8)
        name = "JSR" if b == 0x20 else "JMP"
        print(f"  ROM 0x{i:06X}: {name} ${addr:04X}")
        i += 2
    elif b == 0xEA: print(f"  ROM 0x{i:06X}: NOP")
    elif b == 0x60: print(f"  ROM 0x{i:06X}: RTS")
    elif b == 0x6B: print(f"  ROM 0x{i:06X}: RTL")
    elif b == 0x18: print(f"  ROM 0x{i:06X}: CLC")
    elif b == 0x38: print(f"  ROM 0x{i:06X}: SEC")
    elif b == 0xE8: print(f"  ROM 0x{i:06X}: INX")
    elif b == 0xCA: print(f"  ROM 0x{i:06X}: DEX")
    elif b == 0xC8: print(f"  ROM 0x{i:06X}: INY")
    elif b == 0x88: print(f"  ROM 0x{i:06X}: DEY")
    elif b == 0x1A: print(f"  ROM 0x{i:06X}: INA")
    elif b == 0x3A: print(f"  ROM 0x{i:06X}: DEA")
    elif b == 0xAA: print(f"  ROM 0x{i:06X}: TAX")
    elif b == 0x8A: print(f"  ROM 0x{i:06X}: TXA")
    elif b == 0xA8: print(f"  ROM 0x{i:06X}: TAY")
    elif b == 0x98: print(f"  ROM 0x{i:06X}: TYA")
    elif b == 0x9B: print(f"  ROM 0x{i:06X}: TXY")
    elif b == 0xBB: print(f"  ROM 0x{i:06X}: TYX")
    elif b == 0x08: print(f"  ROM 0x{i:06X}: PHP")
    elif b == 0x28: print(f"  ROM 0x{i:06X}: PLP")
    elif b == 0x0B: print(f"  ROM 0x{i:06X}: PHD")
    elif b == 0x2B: print(f"  ROM 0x{i:06X}: PLD")
    elif b == 0x5C:  # JML
        dest = rom[i+1] | (rom[i+2] << 8) | (rom[i+3] << 16)
        print(f"  ROM 0x{i:06X}: JML ${dest:06X}")
        i += 3
    elif b == 0xFB: print(f"  ROM 0x{i:06X}: XCE")
    elif b == 0xDB: print(f"  ROM 0x{i:06X}: STP")
    elif b == 0xCB: print(f"  ROM 0x{i:06X}: WAI")
    elif b == 0xD0 and i+2 <= len(rom):  # BNE
        print(f"  ROM 0x{i:06X}: BNE 0x{i+2+(rom[i+1] if rom[i+1]<128 else rom[i+1]-256):06X}")
        i += 1
    elif b == 0xF0:  # BEQ
        print(f"  ROM 0x{i:06X}: BEQ 0x{i+2+(rom[i+1] if rom[i+1]<128 else rom[i+1]-256):06X}")
        i += 1
    elif b == 0x80:  # BRA
        print(f"  ROM 0x{i:06X}: BRA 0x{i+2+(rom[i+1] if rom[i+1]<128 else rom[i+1]-256):06X}")
        i += 1
    elif b == 0xB0:  # BCS
        print(f"  ROM 0x{i:06X}: BCS 0x{i+2+(rom[i+1] if rom[i+1]<128 else rom[i+1]-256):06X}")
        i += 1
    elif b == 0x90:  # BCC
        print(f"  ROM 0x{i:06X}: BCC 0x{i+2+(rom[i+1] if rom[i+1]<128 else rom[i+1]-256):06X}")
        i += 1
    elif b == 0x10:  # BPL
        print(f"  ROM 0x{i:06X}: BPL 0x{i+2+(rom[i+1] if rom[i+1]<128 else rom[i+1]-256):06X}")
        i += 1
    elif b == 0x30:  # BMI
        print(f"  ROM 0x{i:06X}: BMI 0x{i+2+(rom[i+1] if rom[i+1]<128 else rom[i+1]-256):06X}")
        i += 1
    else:
        print(f"  ROM 0x{i:06X}: .db ${b:02X}")
