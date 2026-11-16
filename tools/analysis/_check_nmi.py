rom = open('roms/dkc2.sfc', 'rb').read()

# The linear mapping formula was confirmed for $80-$BF
# Let's check the vectors at ROM $00FFE4+
print("=== Vectors at ROM $00FFE4+ (linear mapping for bank $00) ===")
for i, (offset, name) in enumerate([
    (0x00FFE4, 'COP (nat)'),
    (0x00FFE6, 'BRK (nat)'),
    (0x00FFE8, 'ABORT (nat)'),
    (0x00FFEA, 'NMI (nat)'),
    (0x00FFEC, 'RES (nat)?'),
    (0x00FFEE, 'IRQ (nat)'),
    (0x00FFF0, 'COP (emu)'),
    (0x00FFF2, 'ABORT (emu)'),
    (0x00FFF4, 'NMI (emu)'),
    (0x00FFF6, 'RESET (emu)'),
    (0x00FFF8, 'IRQ/BRK (emu)'),
    (0x00FFFA, 'RESET'),
    (0x00FFFC, 'RESET (emu main)'),
    (0x00FFFE, 'BRK (emu)'),
]):
    if offset+1 < len(rom):
        lo = rom[offset]
        hi = rom[offset+1]
        vec16 = lo | (hi << 8)
        bk = rom[offset+2] if offset+2 < len(rom) else 0
        
        if 'nat' in name:
            vec24 = lo | (hi << 8) | (bk << 16)
            print(f"  {name}: ${bk:02X}:{vec16:04X}")
        else:
            print(f"  {name}: ${vec16:04X}")

# Check what's at NMI vector target
print("\n=== Bytes at NMI handler $80:F3BD ===")
# NMI vector = $00:F3BD, map to ROM: (0 & 0x3F)*0x10000 + F3BD = 0x00F3BD
# But wait, maybe $00:F3BD with SA-1 mapping maps differently?
# The SA-1 linear mapping gives: (bank & 0x3F) * 0x10000 + addr
# For bank $00: 0 * 0x10000 + F3BD = 0x00F3BD
nmi_rom = 0x00F3BD
print(f"NMI at ROM offset {nmi_rom:06X}")
for i in range(48):
    if nmi_rom + i < len(rom):
        print(f"  {nmi_rom+i:06X}: {rom[nmi_rom+i]:02X}", end='')
        if (i+1)%8 == 0: print()

# Also check the init / boot vector
print("\n=== Reset vector check ===")
# $00:FFFC contains the reset vector
reset_vec = rom[0x00FFFC] | (rom[0x00FFFD] << 8)
print(f"Reset vector (from $00:FFFC): ${reset_vec:04X}")
# In emulation mode, this is just a 16-bit address in bank $00
# So reset goes to $00:{reset_vec}
# For HiROM, does $00:xxxx map to ROM?
# $00:xxxx -> (0 & 0x3F)*0x10000 + xxxx = 0xxxxx
print(f"That maps to ROM offset {reset_vec:06X}")
print(f"Bytes at ROM {reset_vec:06X}: {rom[reset_vec]:02X} {rom[reset_vec+1]:02X}")

# Now, let me verify: what about bank $80 for NMI?
# Actually the native NMI vector is $00:F3BD, but maybe it should be $80:F3BD?
# Let me check what's at ROM offset (0x80 & 0x3F)*0x10000 + 0xF3BD = 0x40 * 0x10000 + F3BD
# Wait, 0x80 & 0x3F = 0x00... that gives offset 0x00F3BD
# Hmm, that doesn't make sense for 4MB ROM
