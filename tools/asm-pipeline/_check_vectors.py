import struct

data = open("roms/dkc2.sfc", "rb").read()

print(f"ROM size: {len(data)} bytes ({len(data)//1024} KB)\n")

# ============= LoROM vectors =============
# $00:FFC0-$00:FFFF mapped to ROM offset 0x7FC0-0x7FFF
print("=== LoROM vectors (ROM offset 0x7FC0, $00:FFC0) ===")

# Native vectors ($00:FFE0-$00:FFEB)
print("\nNative mode vectors ($00:FFE0-$FFEB):")
native_names = ["COP", "BRK", "ABORT", "NMI", "RESET", "IRQ"]
for i, name in enumerate(native_names):
    off = 0x7FE0 + i * 2
    val = struct.unpack("<H", data[off : off + 2])[0]
    bank = 0x00 if val < 0x8000 else 0xC0
    print(f"  $00:FFE{0+i*2:02X}: {name}: ${val:04X} -> ${bank:02X}:{val:04X}")

# Emulation vectors ($00:FFF0-$00:FFFF)
print("\nEmulation vectors ($00:FFF0-$FFFF):")
emu_names = [
    ("$FFF0", "unused"),
    ("$FFF2", "unused"),
    ("$FFF4", "COP"),
    ("$FFF6", "BRK (ABORT)"),
    ("$FFF8", "ABORT (COP)"),
    ("$FFFA", "NMI"),
    ("$FFFC", "RESET"),
    ("$FFFE", "IRQ/BRK"),
]
for loc, name in emu_names:
    off = 0x7FF0 + int(loc[1:5], 16) - 0xFFF0
    val = struct.unpack("<H", data[off : off + 2])[0]
    print(f"  $00:{loc}: {name}: ${val:04X}")

# ============= Flat mapping vectors at $FF:FFC0 =============
print("\n=== Flat mapping ($FF:FFC0, ROM offset 0x3FFFC0) ===")
# These are at a different ROM location
# $FF:FFE0 = bank $FF, offset $FFE0 = (0xFF-0xC0)*0x10000 + 0xFFE0 = 0x3FFFE0
native_names2 = ["COP", "BRK", "ABORT", "NMI", "RESET", "IRQ"]
for i, name in enumerate(native_names2):
    off = 0x3FFFE0 + i * 2
    val = struct.unpack("<H", data[off : off + 2])[0]
    print(f"  $FF:FFE{0+i*2:02X}: {name}: ${val:04X}")

# Check if $C0:8916 is valid NMI code
print("\n=== Checking NMI candidate $C0:8916 ===")
nmi_off = 0x8000 + 0x0916  # $C0:8916 = bank 0 offset 0x0916
nmi_bytes = " ".join(f"{data[nmi_off+i]:02X}" for i in range(30))
print(f"  Bytes at $C0:8916: {nmi_bytes}")

# Check $C0:877C (native RESET/IRQ from flat mapping)
print("\n=== Checking $C0:877C (Native IRQ from flat vec) ===")
irq_off = 0x8000 + 0x077C
irq_bytes = " ".join(f"{data[irq_off+i]:02X}" for i in range(30))
print(f"  Bytes at $C0:877C: {irq_bytes}")

# Check $C0:8811 (native COP from flat mapping)
print("\n=== Checking $C0:8811 (Native COP from flat vec) ===")
cop_off = 0x8000 + 0x0811
cop_bytes = " ".join(f"{data[cop_off+i]:02X}" for i in range(30))
print(f"  Bytes at $C0:8811: {cop_bytes}")
