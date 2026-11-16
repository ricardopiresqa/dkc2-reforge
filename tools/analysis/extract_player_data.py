"""Extract player physics and state data from DKC2 ROM."""
import struct, os

ROM_PATH = "roms/dkc2.sfc"
with open(ROM_PATH, "rb") as f:
    ROM = f.read()

def snes_to_rom(addr):
    bank, offset = (addr >> 16) & 0xFF, addr & 0xFFFF
    if bank >= 0xC0: return (bank - 0xC0) * 0x10000 + offset
    if 0x80 <= bank <= 0xBF:
        return (bank - 0x80) * 0x10000 + (offset - 0x8000 if offset >= 0x8000 else offset)
    if 0x40 <= bank <= 0x7F and offset >= 0x8000:
        return ((bank - 0x40) * 0x8000) + (offset - 0x8000) + 0x200000
    if bank <= 0x3F and offset >= 0x8000:
        return bank * 0x8000 + (offset - 0x8000)
    return None

def rdw(addr):
    off = snes_to_rom(addr)
    if off is None or off + 2 > len(ROM): return None
    return struct.unpack_from("<H", ROM, off)[0]

def rdb(addr):
    off = snes_to_rom(addr)
    if off is None or off >= len(ROM): return None
    return ROM[off]

def s16(v):
    if v is None: return "?"
    if v >= 0x8000: return str(v - 0x65536)
    return str(v)

# --- Bank BD dispatch table (object handlers) ---
print("=== Bank BD Object Dispatch Table ===")
# $BD8000 appears to be a jump table of 16-bit addresses
for i in range(32):
    addr = 0xBD8000 + i*2
    w = rdw(addr)
    if w:
        bank = 0xBD
        full = (bank << 16) | w
        print(f"  entry[{i:2d}] = ${w:04X} (${full:06X})")

# --- Look at bank $C0-C3 for player logic ---
print("\n=== Bank C0 key areas ===")
for addr, label in [(0xC0A000, "unk_A000"), (0xC0A100, "unk_A100"), 
                     (0xC0A14B, "AreaInit"), (0xC0A252, "InputRead"),
                     (0xC0A7B5, "EventQueue"), (0xC0A8CF, "MainInit"),
                     (0xC0B000, "unk_B000"), (0xC0C000, "unk_C000"),
                     (0xC0C15A, "InputReadAlt"), (0xC0C21C, "PRNG"),
                     (0xC0E696, "SlotScan"), (0xC0EDCE, "PlayerInit")]:
    w = rdw(addr)
    print(f"  ${addr:06X} ({label}): ${w:04X} ({s16(w)})")

# --- Bank BD $82xx area - another dispatch area ---
print("\n=== Bank BD $8200 - secondary dispatch ===")
for i in range(16):
    addr = 0xBD8200 + i*2
    w = rdw(addr)
    if w:
        print(f"  ${addr:04X}: ${w:04X} ({s16(w)})")

# --- Check for constant tables in bank C0 ---
# Look for blocks of 16-bit values that look like physics
print("\n=== Physics constant candidates ===")
candidates = [
    (0xC0B500, "C0_B500"), (0xC0B600, "C0_B600"), (0xC0B700, "C0_B700"),
    (0xC0B800, "C0_B800"), (0xC0B900, "C0_B900"), (0xC0BA00, "C0_BA00"),
    (0xC0BB00, "C0_BB00"), (0xC0BC00, "C0_BC00"), (0xC0BD00, "C0_BD00"),
    (0xC0BE00, "C0_BE00"), (0xC0BF00, "C0_BF00"),
]
for addr, label in candidates:
    vals = []
    for i in range(0, 16, 2):
        w = rdw(addr + i)
        if w is not None:
            vals.append(f"${w:04X}({s16(w)})")
    if vals:
        print(f"  ${addr:06X} ({label}): {' '.join(vals)}")

# --- Check BD bank ---
# $BD4C1F is first entry in BD dispatch
print("\n=== BD $4C00 area (first dispatch target) ===")
off = snes_to_rom(0xBD4C00)
if off:
    for i in range(0, 128, 16):
        b = ROM[off+i:off+i+16]
        h = " ".join(f"{x:02X}" for x in b)
        print(f"  ${0xBD4C00+i:06X}: {h}")

# --- Look at BD $5000-5200 range for state tables ---
print("\n=== BD $5000-5200 ===")
for base in range(0xBD5000, 0xBD5200, 0x20):
    off = snes_to_rom(base)
    if off:
        b = ROM[off:off+32]
        h = " ".join(f"{x:02X}" for x in b[:16])
        print(f"  ${base:06X}: {h}")

# --- Analyze BD dispatch table entries ---
# First entry at BD8000 = $4B1F → handler at BD:$4B1F
# These 32 entries likely correspond to object types
print("\n=== BD dispatch - first handler analysis ===")
# Read handler at BD4B1F
handler_addr = 0xBD4B1F
off = snes_to_rom(handler_addr)
if off:
    print(f"\n--- Handler at ${handler_addr:06X} (object type 0) ---")
    for i in range(0, 64, 16):
        b = ROM[off+i:off+i+16]
        h = " ".join(f"{x:02X}" for x in b)
        print(f"  ${handler_addr+i:06X}: {h}")

# Entry 1 = $4C52
handler_addr2 = 0xBD4C52
off2 = snes_to_rom(handler_addr2)
if off2:
    print(f"\n--- Handler at ${handler_addr2:06X} (object type 1) ---")
    for i in range(0, 64, 16):
        b = ROM[off2+i:off2+i+16]
        h = " ".join(f"{x:02X}" for x in b)
        print(f"  ${handler_addr2+i:06X}: {h}")

# --- Check bank C2/C3 for more code ---
print("\n=== Bank C2 (ROM bank $02) start ===")
off = snes_to_rom(0xC28000)
if off:
    for i in range(0, 128, 16):
        b = ROM[off+i:off+i+16]
        h = " ".join(f"{x:02X}" for x in b)
        print(f"  ${0xC28000+i:06X}: {h}")

# --- Check for level data pointers ---
print("\n=== Level data / sprite tables ===")
# The area init at C0A14B loads level data
# Check bank C0 for level table pointers
off = snes_to_rom(0xC08000)
if off:
    print("\n--- C08000 (Reset handler) ---")
    for i in range(0, 64, 16):
        b = ROM[off+i:off+i+16]
        h = " ".join(f"{x:02X}" for x in b)
        print(f"  ${0xC08000+i:06X}: {h}")

# Check the NMI handler  
print("\n--- NMI Handler ($C04F4B) ---")
off = snes_to_rom(0xC04F4B)
if off:
    for i in range(0, 64, 16):
        b = ROM[off+i:off+i+16]
        h = " ".join(f"{x:02X}" for x in b)
        print(f"  ${0xC04F4B+i:06X}: {h}")

# Bank CB code areas
print("\n=== Bank CB (ROM bank $0B) ===")
off = snes_to_rom(0xCB8000)
if off:
    for i in range(0, 128, 16):
        b = ROM[off+i:off+i+16]
        h = " ".join(f"{x:02X}" for x in b)
        print(f"  ${0xCB8000+i:06X}: {h}")
