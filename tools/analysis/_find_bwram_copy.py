"""Find BW-RAM copy mechanism comprehensively."""

with open('roms/dkc2.sfc', 'rb') as f:
    rom = f.read()

# Search for all STA long instructions to B4 bank
print("=== STA long to bank B4 (8F xx xx B4) ===")
for i in range(3, len(rom)):
    if rom[i-3] == 0x8F and rom[i] == 0xB4:
        addr = rom[i-2] | (rom[i-1] << 8)
        print(f"  ROM 0x{i-3:06X}: STA ${addr:04X} (bank B4)")

# Search for all STA long instructions to bank 00 (BW-RAM for SA-1)
print("\n=== STA long to bank 00 (possible BW-RAM) ===")
count = 0
for i in range(3, len(rom)):
    if rom[i-3] == 0x8F and rom[i] == 0x00 and rom[i-2] >= 0x60:
        addr = rom[i-2] | (rom[i-1] << 8)
        print(f"  ROM 0x{i-3:06X}: STA ${addr:04X} (bank 00)")
        count += 1
        if count >= 20:
            print("  ... (more truncated)")
            break

# Find SA-1 DMA enable register ($2230) - any patterns
print("\n=== STA $2230 (DMAEN) - all possible patterns ===")
for i in range(len(rom)-3):
    if rom[i] == 0x8D and rom[i+1] == 0x30 and rom[i+2] == 0x22:
        print(f"  ROM 0x{i:06X}: STA $2230 (DMAEN)")
    if rom[i] == 0x9C and rom[i+1] == 0x30 and rom[i+2] == 0x22:
        print(f"  ROM 0x{i:06X}: STZ $2230 (DMAEN)")

# Find $2200 writes more broadly (all values)
print("\n=== All writes to $2200-$223F (SA-1 registers) ===")
for i in range(len(rom)-3):
    if rom[i] == 0x8D or rom[i] == 0x9C:  # STA or STZ absolute
        addr = rom[i+1] | (rom[i+2] << 8)
        if 0x2200 <= addr <= 0x223F:
            val = rom[i+1] if rom[i] == 0x8D else 0
            op = "STA" if rom[i] == 0x8D else "STZ"
            print(f"  ROM 0x{i:06X}: {op} ${addr:04X}")

# Find writes to $2220-$223F (SA-1 control)
print("\n=== All writes to $2220-$222F (SA-1 memory mapping) ===")
for i in range(len(rom)-3):
    if rom[i] == 0x8D or rom[i] == 0x9C:
        addr = rom[i+1] | (rom[i+2] << 8)
        if 0x2220 <= addr <= 0x222F:
            val = rom[i+1] if rom[i] == 0x8D else 0
            op = "STA" if rom[i] == 0x8D else "STZ"
            print(f"  ROM 0x{i:06X}: {op} ${addr:04X}")
