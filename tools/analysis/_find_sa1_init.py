"""Find SA-1 initialization code in ROM (first 2MB)."""

with open('roms/dkc2.sfc', 'rb') as f:
    rom = f.read()

# Search first 2MB for SA-1 register writes
limit = 0x200000
print("=== SA-1 register writes in first 2MB ===")
for i in range(limit - 3):
    if rom[i] == 0x8D or rom[i] == 0x9C:  # STA or STZ
        addr = rom[i+1] | (rom[i+2] << 8)
        if 0x2200 <= addr <= 0x223F:
            op = "STA" if rom[i] == 0x8D else "STZ"
            print(f"  ROM 0x{i:06X}: {op} ${addr:04X}")

# Also check for SEP #$30 + LDA #$xx + STA $2200 pattern
print("\n=== Writing bit 7 to $2200 (release SA-1 reset) ===")
for i in range(len(rom)-10):
    # Pattern: LDA #$80 + STA $2200, or LDA #$xx (bit7=1) + STA $2200
    if rom[i] == 0xA9 and (rom[i+1] & 0x80) and i+4 < limit:
        if rom[i+2] == 0x8D and rom[i+3] == 0x00 and rom[i+4] == 0x22:
            bank = i >> 16
            ctx_bytes = rom[max(0,i-5):i+6]
            ctx = " ".join(f"{b:02X}" for b in ctx_bytes)
            print(f"  ROM 0x{i:06X}: LDA #${rom[i+1]:02X} STA $2200  [{ctx}]")
        # Also for STA $2200 with $8F (long) addressing
        if rom[i+2] == 0x8F and rom[i+3] == 0x00 and rom[i+4] == 0x22 and rom[i+5] == 0x00:
            ctx_bytes = rom[max(0,i-5):i+7]
            ctx = " ".join(f"{b:02X}" for b in ctx_bytes)
            print(f"  ROM 0x{i:06X}: LDA #${rom[i+1]:02X} STA $002200  [{ctx}]")
