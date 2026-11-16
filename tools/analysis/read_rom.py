"""Read ROM bytes for DKC2 analysis."""
import struct

data = open("roms/dkc2.sfc", "rb").read()

def dump_region(label, addr_start, length=48):
    """addr_start is SNES address, e.g. 0xC08880"""
    bank = (addr_start >> 16) & 0xFF
    offset = addr_start & 0xFFFF
    
    rom_off = -1
    if bank >= 0xC0:
        rom_off = (bank - 0xC0) * 0x10000 + offset
    else:
        rom_off = (bank & 0x7F) * 0x8000 + (offset & 0x7FFF)
    
    if rom_off < 0 or rom_off >= len(data):
        # Try alt mapping for bank 80-BF
        if 0x80 <= bank <= 0xBF and offset >= 0x8000:
            rom_off = (bank - 0x80) * 0x10000 + (offset - 0x8000)
        elif 0x80 <= bank <= 0xBF:
            rom_off = (bank - 0x80) * 0x10000 + offset
    
    if rom_off < 0 or rom_off >= len(data):
        print(f"{label}: cannot map SNES addr ${addr_start:06X} (bank ${bank:02X})")
        return
    
    print(f"\n{'='*60}")
    print(f"{label} @ SNES ${addr_start:06X} (ROM offset ${rom_off:06X})")
    print(f"{'='*60}")
    for base in range(rom_off, min(rom_off + length, len(data)), 16):
        b = data[base:base+16]
        hex_str = " ".join(f"{x:02X}" for x in b)
        ascii_str = "".join(chr(x) if 32 <= x < 127 else "." for x in b)
        snes_addr = addr_start + (base - rom_off)
        print(f"  ${snes_addr:06X}: {hex_str:48s}  {ascii_str}")


# Task 1: Full $C088B7 investigation
dump_region("Before C088B7 (state A handler)", 0xC08880, 32)
dump_region("C088B7 area", 0xC088AF, 80)
dump_region("State C handler + SA-1 shared", 0xC088E0, 48)
dump_region("Full state area C0885F-C088FF", 0xC0885F, 0xA0)

# Task 2: $C00000 and $C00018
dump_region("C00000 area", 0xC00000, 128)
dump_region("Vector area", 0xC0FFE0, 32)

# Try to read B5804C - bank B5
# SA-1 games: B5 is typically the BW-RAM area
# Let's check if there's data at ROM offset by trying various mappings
print("\n\n=== Attempting to locate B5804C in ROM ===")
# Try 1: Standard HiROM mapping (banks 80-BF)
if 0xB5 >= 0x80 and 0xB5 <= 0xBF:
    rom_off = (0xB5 - 0x80) * 0x10000 + 0x804C
    if rom_off < len(data):
        dump_region("B5804C (HiROM alt)", 0xB5804C, 64)
    else:
        rom_off2 = (0xB5 - 0x80) * 0x10000 + (0x804C - 0x8000)
        if rom_off2 < len(data):
            dump_region("B5804C (HiROM 2)", 0xB5804C, 64)
        else:
            print(f"  B5804C not found in ROM (tried offsets ${rom_off:06X} and ${rom_off2:06X})")
else:
    print(f"  Bank B5 not in range 80-BF, trying LoROM fallback")
    rom_off = (0xB5 & 0x7F) * 0x8000 + (0x804C & 0x7FFF)
    if rom_off < len(data):
        dump_region("B5804C (LoROM)", 0xB5804C, 64)
    else:
        print(f"  Not found (offset ${rom_off:06X})")

# Also check the ROM size and SA-1 mapping
print(f"\n\nROM size: {len(data)} bytes ({len(data)//1024} KB)")
print(f"Last bank C3: offset ${3*0x10000:06X}")
