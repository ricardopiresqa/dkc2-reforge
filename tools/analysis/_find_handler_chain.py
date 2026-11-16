rom = open('roms/dkc2.sfc', 'rb').read()
def r(b,a): return (b&0x3F)*0x10000+a

# Track all handler chain in bank $80 by finding:
#   LDA #XXXX  → STA $20 → JMP $B106  (set new handler and return to WAI)
#   JMP $95B3  etc. (jump to next handler)

print("=== Scanning for handler transitions in $80:93B8-97FF ===")

# Find LDA #imm followed by JMP $B0EE (sets new handler)
for addr in range(0x93B8, 0x9800):
    a = r(0x80, addr)
    if addr < len(rom):
        # Pattern: LDA #XXXX (A9 xx xx or A9 xx) + JMP $B0EE (4C EE B0)
        if rom[a] == 0xA9:  # LDA imm
            # Get bytes after LDA to check for JMP $B0EE
            next3 = rom[a+3:a+6] if a+6 < len(rom) else b''
            if next3 == b'\x4c\xee\xb0':
                val = rom[a+1] | (rom[a+2]<<8)
                print(f"  $80:{addr:04X}: LDA #{val:04X} → JMP $B0EE (NEW HANDLER)")
            elif a+4 < len(rom) and rom[a+3] == 0x85 and rom[a+4] == 0x20:
                val = rom[a+1] | (rom[a+2]<<8)
                print(f"  $80:{addr:04X}: LDA #{val:04X} → STA $20 → ... (NEW HANDLER at ${val:04X})")
            elif a+3 < len(rom) and rom[a+2] == 0x4c:
                target = rom[a+3]
                if target == 0xB0:
                    val = rom[a+1]
                    print(f"  $80:{addr:04X}: LDA #{val:02X} → JMP $B0EE (8-bit, NEW HANDLER)")

print("\n=== JMP $95B3 (handler transition in $93B8) ===")
print("Found at $80:950D")

print("\n=== JMP $964C (handler transition from $95B3) ===")
for addr in range(0x95B3, 0x9700):
    a = r(0x80, addr)
    if a+2 < len(rom) and rom[a] == 0x4C:
        target = rom[a+1] | (rom[a+2]<<8)
        if target > 0x9600:
            print(f"  $80:{addr:04X}: JMP ${target:04X}")

print("\n=== JMP $96FB (handler transition from $95B3) ===")
# Found at $95D4: JMP $96FB

print("\n=== STA $20 patterns (handler set) ===")
for addr in range(0x93B8, 0x9900):
    a = r(0x80, addr)
    if a+1 < len(rom) and rom[a] == 0x85 and rom[a+1] == 0x20:
        # STA $20 - check what LDA preceded it
        prev_a = r(0x80, addr-3)
        if prev_a >= 0 and rom[prev_a] == 0xA9:
            val = rom[prev_a+1] | (rom[prev_a+2]<<8)
            print(f"  $80:{addr-3:04X}: LDA #{val:04X} / $80:{addr:04X}: STA $20 → handler = ${val:04X}")

# JMP $B106 pattern (return to WAI)
print("\n=== JMP $B106 (return to WAI loop) ===")
for addr in range(0x93B8, 0x9900):
    a = r(0x80, addr)
    if a+2 < len(rom) and rom[a] == 0x4C:
        target = rom[a+1] | (rom[a+2]<<8)
        if target == 0xB106:
            print(f"  $80:{addr:04X}: JMP $B106")
