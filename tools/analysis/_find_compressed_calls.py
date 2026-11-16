rom = open('roms/dkc2.sfc', 'rb').read()

# Find JSL $BB8D91 and show context
count = 0
results = []
for i in range(len(rom)-4):
    if rom[i] == 0x22 and rom[i+1] == 0x91 and rom[i+2] == 0x8D and rom[i+3] == 0xBB:
        bank = i >> 16
        off = i & 0xFFFF
        snes_b = (bank & 0x3F) | 0x80
        results.append((i, snes_b, off, bank))
        count += 1

print(f"Found {count} calls to JSL $BB8D91")
print()

# Show first 20 with context
for idx, (rom_off, snes_b, addr, bank) in enumerate(results[:25]):
    ctx_start = max(0, rom_off - 20)
    ctx = rom[ctx_start:rom_off]
    
    # Format context bytes
    ctx_str = " ".join(f"{b:02X}" for b in ctx)
    
    print(f"Call {idx+1}: ROM 0x{rom_off:06X} (SNES ${snes_b:02X}:{addr:04X}, phys bank ${bank:02X})")
    print(f"  Pre:  {ctx_str}")
    
    # Look for A setup (LDA # + 2/3 bytes)
    j = rom_off - 3
    if j >= 0 and rom[j] == 0xA9:  # LDA # 16-bit
        val = rom[j+1] | (rom[j+2] << 8)
        print(f"  A = ${val:04X} (LDA #\${val:04X} at offset -3)")
    j = rom_off - 2
    if j >= 0 and rom[j] == 0xA9:  # LDA # 8-bit
        print(f"  A = ${rom[j+1]:02X} (LDA #\${rom[j+1]:02X} at offset -2)")
    
    # Look for X setup (LDX)
    for j in range(rom_off - 8, rom_off - 2):
        if j >= 0 and rom[j] == 0xA2:  # LDX
            if rom[j+1] == 0x00 and rom[j+2] == 0x00:
                print(f"  X = $0000 (LDX #$0000 at offset {j-rom_off})")
            else:
                print(f"  X = ${rom[j+1]:02X} (LDX # at offset {j-rom_off})")
            break
    
    # Look for Y setup (LDY)
    for j in range(rom_off - 8, rom_off - 2):
        if j >= 0 and rom[j] == 0xA0:  # LDY
            val = rom[j+1]
            if rom[j+1] != 0 or rom[j+2] != 0:
                val = rom[j+1] | (rom[j+2] << 8)
                print(f"  Y = ${val:04X} (LDY # at offset {j-rom_off})")
            break
    
    # Show the full instruction context
    print()
