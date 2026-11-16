"""Find where SA-1 is released from reset (writing bit 7 to $2200)."""

with open('roms/dkc2.sfc', 'rb') as f:
    rom = f.read()

# Method 1: Find ANY write to $2200 (8D 00 22 or 9C 00 22)
print("=== ALL writes to $2200 === (S-CPU direct access)")
for i in range(len(rom)-3):
    if rom[i] == 0x8D and rom[i+1] == 0x00 and rom[i+2] == 0x22:
        print(f"  ROM 0x{i:06X}: STA $2200")
    if rom[i] == 0x9C and rom[i+1] == 0x00 and rom[i+2] == 0x22:
        print(f"  ROM 0x{i:06X}: STZ $2200")

# Method 2: Find writes to $2200 via long addressing ($22 00 00)
print("\n=== ALL writes to $002200 (long addressing) ===")
for i in range(len(rom)-4):
    if rom[i] == 0x8F and rom[i+1] == 0x00 and rom[i+2] == 0x22 and rom[i+3] == 0x00:
        print(f"  ROM 0x{i:06X}: STA $002200 (long)")

# Method 3: Find SEP #$20 (8-bit) followed by any LDA #$xx followed by STA $2200
print("\n=== Writes to $2200 with SEP #$20 (8-bit mode) ===")
for i in range(len(rom)-12):
    if rom[i] == 0xE2 and rom[i+1] == 0x20:  # SEP #$20
        # Look for STA $2200 within next 10 bytes
        for j in range(i+2, min(i+12, len(rom)-2)):
            if rom[j] == 0x8D and rom[j+1] == 0x00 and rom[j+2] == 0x22:
                ctx = " ".join(f"{b:02X}" for b in rom[i:j+3])
                print(f"  ROM 0x{i:06X}: SEP #$20 ... STA $2200 : [{ctx}]")

# Method 4: Broader - LDA #$8x followed by any SA-1 control reg
print("\n=== LDA #$8x followed by STA $2200-$220F (any) ===")
for i in range(len(rom)-5):
    if rom[i] == 0xA9 and (rom[i+1] & 0x80):  # LDA #$xx with bit 7 set
        if rom[i+2] == 0x8D:
            addr = rom[i+3] | (rom[i+4] << 8)
            if 0x2200 <= addr <= 0x220F:
                print(f"  ROM 0x{i:06X}: LDA #${rom[i+1]:02X} STA ${addr:04X}")

# Method 5: Search for $2201 (SI-ROM pointer) patterns
print("\n=== Writes to $2201 (SI-ROM pointer) ===")
for i in range(len(rom)-3):
    if rom[i] == 0x8D and rom[i+1] == 0x01 and rom[i+2] == 0x22:
        print(f"  ROM 0x{i:06X}: STA $2201")
    if rom[i] == 0x9C and rom[i+1] == 0x01 and rom[i+2] == 0x22:
        print(f"  ROM 0x{i:06X}: STZ $2201")

# Method 6: Check SA-1 specific version - are there writes to $2300?
print("\n=== Writes to $2300-$230F (SA-1 status/version) ===")
for i in range(len(rom)-3):
    if rom[i] == 0x8D or rom[i] == 0x9C:
        addr = rom[i+1] | (rom[i+2] << 8)
        if 0x2300 <= addr <= 0x230F:
            op = "STA" if rom[i] == 0x8D else "STZ"
            print(f"  ROM 0x{i:06X}: {op} ${addr:04X}")
