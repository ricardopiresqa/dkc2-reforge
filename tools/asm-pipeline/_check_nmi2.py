import struct

data = open("roms/dkc2.sfc", "rb").read()

print("=== Bank FF (ROM offset 0x3F0000-0x3FFFFF) ===")
# Check what's at FF:8916 (flat vector NMI target)
test_addr = 0x3F8916
first_byte = data[test_addr]
print(f"First byte at FF:8916: ${first_byte:02X}")
code_indicators = {0x20, 0x4C, 0x5C, 0x22, 0x60, 0x6B, 0x40, 0xA9, 0xC2, 0xE2, 0x18, 0x38, 0x58, 0x78, 0xFB, 0xAD, 0x8D}
if first_byte in code_indicators:
    print("  -> Looks like code!")
else:
    print("  -> Probably data (non-code opcode)")

print()
print("=== Standard SNES LoROM vectors (0x7FC0-0x7FFF) ===")
native_nmi = struct.unpack("<H", data[0x7FE6 : 0x7FE8])[0]
emu_nmi = struct.unpack("<H", data[0x7FFA : 0x7FFC])[0]
emu_reset = struct.unpack("<H", data[0x7FFC : 0x7FFE])[0]
print(f"Native NMI ($00:FFE6): ${native_nmi:04X}")
print(f"Emulation NMI ($00:FFFA): ${emu_nmi:04X}")
print(f"Emulation RESET ($00:FFFC): ${emu_reset:04X}")

# In LoROM, $00:8000-FFFF maps to first 32KB of ROM
# So $00:85A9 maps to ROM offset 0x05A9
# In our flat mapping, this is C0:85A9
lorom_ofs = native_nmi - 0x8000
if lorom_ofs >= 0:
    print(f"  -> LoROM NMI at ROM offset 0x{lorom_ofs:06X}")
    print(f"  -> Our flat mapping: $C0:{native_nmi:04X}")
    nmibytes = " ".join(f"{data[lorom_ofs + i]:02X}" for i in range(20))
    print(f"  -> Code: {nmibytes}")
else:
    print(f"  -> LoROM NMI ${native_nmi:04X} < $8000, can't map")

# Check emulation NMI vector (for SA-1 initial boot)
emu_ofs = emu_nmi - 0x8000
if emu_ofs >= 0:
    print(f"\nEmulation NMI at ROM offset 0x{emu_ofs:06X}:")
    emb = " ".join(f"{data[emu_ofs + i]:02X}" for i in range(20))
    print(f"  -> {emb}")

# Check flat vectors at $FF:FFC0 (0x3FFFC0) - these are for SA-1 or last bank
print(f"\n=== Flat vector area at $FF:FFE0 (ROM 0x3FFFE0) ===")
flat_nmi = struct.unpack("<H", data[0x3FFFE6 : 0x3FFFE8])[0]
flat_reset = struct.unpack("<H", data[0x3FFFE8 : 0x3FFFEA])[0]
flat_irq = struct.unpack("<H", data[0x3FFFEA : 0x3FFFEC])[0]
print(f"  NMI: ${flat_nmi:04X} -> $C0:{flat_nmi:04X}? or $FF:{flat_nmi:04X}?")
print(f"  RESET: ${flat_reset:04X}")
print(f"  IRQ: ${flat_irq:04X}")

# Check both bank $C0 and $FF for flat NMI target
off_c0 = 0x8000 + (flat_nmi & 0x7FFF)  # C0-like mapping
off_ff = 0x3F0000 + flat_nmi  # FF bank mapping
c0_bytes = " ".join(f"{data[off_c0 + i]:02X}" for i in range(10))
ff_bytes = " ".join(f"{data[off_ff + i]:02X}" for i in range(10))
print(f"  C0:{flat_nmi:04X}: {c0_bytes}")
print(f"  FF:{flat_nmi:04X}: {ff_bytes}")

# Summary: which vector table is right?
print()
print("=== CONCLUSION ===")
print("The game boots via LoROM reset vector ($00:FFFC) = $8000")
print("After boot, the init code at $C0:8000 runs CLC+XCE to enter native mode")
print("The native NMI vector at $00:FFE6 = ${:04X}".format(native_nmi))
print(f"  -> Mapped through LoROM = C0:{native_nmi:X}")
