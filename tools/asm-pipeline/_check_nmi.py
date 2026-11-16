import struct

data = open("roms/dkc2.sfc", "rb").read()

def rom_ofs(bank, offset_lo):
    """Convert SNES addr to ROM offset (SA-1 HiROM-like)."""
    bank_num = (bank << 16) >> 16
    phys_bank = bank_num - 0xC0
    if 0 <= phys_bank < 64:
        return phys_bank * 0x10000 + (offset_lo & 0xFFFF)
    return None  # not in $C0-$FF range

def check_addr(name, bank, offset):
    off = rom_ofs(bank, offset)
    if off is None or off >= len(data):
        print(f"  {name}: ${bank:02X}:{offset:04X} -> out of range")
        return
    bytes_str = " ".join(f"{data[off+i]:02X}" for i in range(20))
    print(f"  {name}: ${bank:02X}:{offset:04X} (ROM 0x{off:06X}): {bytes_str}")

# LoROM native NMI from $00:FFE6
nmi_lorom_val = struct.unpack("<H", data[0x7FE6:0x7FE8])[0]
# $00:85A9 in LoROM = offset 0x05A9 -> $C0:85A9
lorom_nmi = 0xC085A9
check_addr("LoROM NMI via $00:85A9->$C0", 0xC0, 0x85A9)

# Flat NMI from $FF:FFE6
nmi_flat_val = struct.unpack("<H", data[0x3FFFE6:0x3FFFE8])[0]
check_addr("Flat NMI via $FF:8916->$C0", 0xC0, 0x8916)

# Also check the IRQ vectors
check_addr("LoROM Native IRQ ($00:FFEA)", 0xC0, 0x8945)
irq_lorom = struct.unpack("<H", data[0x7FEA:0x7FEC])[0]
print(f"\nLoROM Native IRQ value: ${irq_lorom:04X}")
check_addr("LoROM Native IRQ resolved", 0xC0, irq_lorom)

# Check what the SA-1 registers for vectors say (if accessible)
# SA-1 vector registers at $2200-$220F
print("\nSA-1 vector registers ($2200-$220F):")
for reg in range(0x2200, 0x2210, 2):
    if reg < 0x2000:
        # Not in RAM, these are MMIO
        pass
    val = struct.unpack("<H", data[rom_ofs(0xC0, 0x8000) + (reg - 0x2000)]) if False else None
    # SA-1 registers are accessible via SNES address $2200-$22FF
    # These aren't in the ROM file, they're hardware registers

# Actually let me check init code for SA-1 vector setup
print("\nInit code writes to $420D (SA-1 enable) and vectors:")
# Search for writes to $2200-$220F in the init code
init_code = data[0:0x4000]  # First 16KB
# Look for pattern STA $22xx
for i in range(len(init_code) - 3):
    if init_code[i] == 0x8D:  # STA abs
        target = struct.unpack("<H", init_code[i+1:i+3])[0]
        if 0x2200 <= target <= 0x220F:
            print(f"  ROM 0x{i:06X}: STA ${target:04X}")
