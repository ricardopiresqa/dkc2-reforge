rom = open('roms/dkc2.sfc', 'rb').read()

# Check vectors at end of ROM
print("=== Vectors at ROM end (last 16 bytes) ===")
for off in range(len(rom)-16, len(rom)):
    print(f"ROM offset {off:06X}: {rom[off]:02X}", end='  ')
    if (off - (len(rom)-16) + 1) % 4 == 0: print()
print()

# HiROM: vectors are at $00FFE0-$00FFFF -> ROM offset $3FFFE0-$3FFFFF
print("\n=== Interrupt vectors (HiROM $00:FFE0-$00:FFFF -> ROM $3FFFE0-$3FFFFF) ===")
vec_base = 0x3FFFE0
vector_names = [
    (0x3FFFE4, "COP (native)"),
    (0x3FFFE6, "BRK (native)"),
    (0x3FFFE8, "ABORT (native)"),
    (0x3FFFEA, "NMI (native)"),
    (0x3FFFEC, "IRQ (native)"),
    (0x3FFFF0, "COP (emu)"),
    (0x3FFFF2, "ABORT (emu)"),
    (0x3FFFF4, "NMI (emu)"),
    (0x3FFFF6, "RESET (emu)"),
    (0x3FFFF8, "IRQ/BRK (emu)"),
    (0x3FFFFC, "RESET (native)"),  # Actually emulation mode reset is at FFFC
]
# Actually for HiROM:
# $00:FFE4 = COP vector (native)
# $00:FFE6 = BRK vector (native)  
# $00:FFEA = NMI vector (native)
# $00:FFEE = IRQ vector (native)
# $00:FFF4 = NMI vector (emulation)
# $00:FFF6 = RESET vector (emulation)
# $00:FFFE = RESET vector (emulation mode)
# But these are accessed as bank $00:FFEx, which maps to ROM $3FFFE0+ for HiROM

hirom_vectors = [
    (0x00, 0xFFE4, "COP (nat)"),
    (0x00, 0xFFE6, "BRK (nat)"),
    (0x00, 0xFFE8, "ABORT (nat)"),
    (0x00, 0xFFEA, "NMI (nat)"),
    (0x00, 0xFFEC, "RESET (nat)?"),
    (0x00, 0xFFEE, "IRQ (nat)"),
    (0x00, 0xFFF0, "COP (emu)"),
    (0x00, 0xFFF2, "ABORT (emu)"),
    (0x00, 0xFFF4, "NMI (emu)"),
    (0x00, 0xFFF6, "RESET (emu)"),
    (0x00, 0xFFF8, "IRQ/BRK (emu)"),
    (0x00, 0xFFFA, "RESET (emu)"  ),
]

for bank, addr, name in hirom_vectors:
    rom_off = (bank & 0x3F) * 0x10000 + addr
    if rom_off + 3 <= len(rom):
        # 65816 vectors are 3 bytes (bank:addr)
        # For emulation mode: 2 bytes (addr)
        if "emu" in name or "RESET" in name:
            lo = rom[rom_off]
            hi = rom[rom_off + 1]
            vec = lo | (hi << 8)
            print(f"  {name}: ${vec:04X} (ROM bytes: {lo:02X} {hi:02X})")
        else:
            lo = rom[rom_off]
            hi = rom[rom_off + 1]
            bk = rom[rom_off + 2] 
            vec = lo | (hi << 8)
            print(f"  {name}: ${bk:02X}:{vec:04X} (ROM bytes: {lo:02X} {hi:02X} {bk:02X})")
    else:
        print(f"  {name}: <out of range>")
