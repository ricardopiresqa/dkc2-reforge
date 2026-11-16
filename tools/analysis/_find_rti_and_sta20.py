rom = open('roms/dkc2.sfc', 'rb').read()
def r(b,a): return (b&0x3F)*0x10000+a

# RTI search - where does the handler end?
print("=== RTI instructions in $80:93B8-9A00 ===")
for addr in range(0x93B8, 0x9A00):
    a = r(0x80, addr)
    if rom[a] == 0x40:  # RTI
        print(f"  $80:{addr:04X}: RTI")

# STA $20 patterns in wider range
print("\n=== STA $20 (handler change) in $80:93B8-9A00 ===")
for addr in range(0x93B8, 0x9A00):
    a = r(0x80, addr)
    if rom[a] == 0x85 and rom[a+1] == 0x20:
        # Show context: look back for LDA
        prev = 1
        lda_val = None
        while prev < 6 and addr >= prev:
            pa = r(0x80, addr-prev)
            if rom[pa] == 0xA9:  # LDA imm
                if prev >= 3:  # 16-bit
                    lda_val = rom[pa+1] | (rom[pa+2]<<8)
                else:  # 8-bit
                    lda_val = rom[pa+1]
                break
            prev += 1
        if lda_val:
            print(f"  $80:{addr-2:04X}: LDA #{lda_val:04X}")
            print(f"  $80:{addr:04X}:   STA $20")
        else:
            # raw
            print(f"  $80:{addr:04X}: STA $20  (ctx: {rom[a-2]:02X} {rom[a-1]:02X})")

# Also check for LDA #imm + JMP $B0EE (alternative pattern)
print("\n=== LDA #imm + JMP $B0EE in $80:93B8-9A00 ===")
for addr in range(0x93B8, 0x9A00):
    a = r(0x80, addr)
    if a+4 < len(rom) and rom[a] == 0xA9:
        if rom[a+3] == 0x4C and rom[a+4] == 0xEE and rom[a+5] == 0xB0:
            val = rom[a+1] | (rom[a+2]<<8)
            print(f"  $80:{addr:04X}: LDA #{val:04X} / JMP $B0EE  <-- $80:{val:04X} handler")
        elif a+3 < len(rom) and rom[a+1] == 0x4C and rom[a+2] == 0xEE and rom[a+3] == 0xB0:
            val = rom[a+1] 
            # this would be 8-bit LDA - hmm unlikely

# JMP $B0EE standalone
print("\n=== JMP $B0EE in $80:93B8-9A00 ===")
for addr in range(0x93B8, 0x9A00):
    a = r(0x80, addr)
    if a+2 < len(rom) and rom[a] == 0x4C and rom[a+1] == 0xEE and rom[a+2] == 0xB0:
        # check if preceded by LDA
        prev_a = r(0x80, addr-3)
        if prev_a >= 0 and rom[prev_a] == 0xA9:
            val = rom[prev_a+1] | (rom[prev_a+2]<<8) if len(rom) > prev_a+2 else rom[prev_a+1]
            print(f"  $80:{addr-3:04X}: ... / $80:{addr:04X}: JMP $B0EE  (A={val:04X})")
        else:
            print(f"  $80:{addr:04X}: JMP $B0EE")
