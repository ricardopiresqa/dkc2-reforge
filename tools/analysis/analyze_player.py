"""Analyze DKC2 ROM for player controller, rope, barrel, and enemy data.

Reads ROM bytes, identifies state machines, physics constants, and
system-specific data patterns across all code banks.

Output: structured data used by docs/ generation.
"""
import struct
import os

ROM_PATH = "roms/dkc2.sfc"

def load_rom():
    with open(ROM_PATH, "rb") as f:
        return f.read()

def snes_to_rom(addr):
    bank = (addr >> 16) & 0xFF
    offset = addr & 0xFFFF
    if bank >= 0xC0:
        return (bank - 0xC0) * 0x10000 + offset
    elif 0x80 <= bank <= 0xBF:
        if offset >= 0x8000:
            return (bank - 0x80) * 0x10000 + (offset - 0x8000)
        else:
            return (bank - 0x80) * 0x10000 + offset
    elif 0x40 <= bank <= 0x7F:
        if offset >= 0x8000:
            return ((bank - 0x40) * 0x8000) + (offset - 0x8000) + 0x200000
        else:
            return None
    elif bank <= 0x3F:
        if offset >= 0x8000:
            return (bank * 0x8000) + (offset - 0x8000)
        else:
            return None
    return None

def read_word(data, addr):
    off = snes_to_rom(addr)
    if off is None or off + 1 >= len(data):
        return None
    return struct.unpack_from("<H", data, off)[0]

def read_byte(data, addr):
    off = snes_to_rom(addr)
    if off is None or off >= len(data):
        return None
    return data[off]

def read_bytes(data, addr, n):
    off = snes_to_rom(addr)
    if off is None or off + n > len(data):
        return None
    return data[off:off+n]

def signed16(val):
    if val is None:
        return None
    if val >= 0x8000:
        return val - 0x65536
    return val

def dump_region(data, addr, length=64):
    off = snes_to_rom(addr)
    if off is None:
        print(f"  Cannot map ${addr:06X}")
        return []
    result = []
    for i in range(0, min(length, len(data)-off), 16):
        b = data[off+i:off+i+16]
        hex_s = " ".join(f"{x:02X}" for x in b)
        ascii_s = "".join(chr(x) if 32 <= x < 127 else "." for x in b)
        result.append((addr+i, hex_s, ascii_s))
    return result

ROM = load_rom()
print(f"ROM size: {len(ROM)} bytes")
print()

# ============================================================
# 1. ENTRY POINT AND VECTORS
# ============================================================
print("=" * 60)
print("VECTORS")
print("=" * 60)
# Native mode vectors at ROM 0x00FFF0 (SNES $80:FFF0)
for vec_name, rom_off in [("NMI", 0x00FFF6), ("RESET", 0x00FFFC), ("IRQ", 0x00FFFE)]:
    v = struct.unpack_from("<H", ROM, rom_off)[0]
    print(f"  {vec_name}: ${v:04X}")

# ============================================================
# 2. KNOWN PLAYER CONSTANTS from docs/ram-map.md refs
# ============================================================
print()
print("=" * 60)
print("PLAYER CONTROLLER - KNOWN FUNCTION AREAS")
print("=" * 60)

# The main engine is in banks $C0-$C3
# Player init at $C0EDCE
# Player state machine likely near $C09BE7
# Input read at $C0A252 / $C0C15A

# Let's read the player init function and nearby data
print("\n--- func_C0EDCE (Player Init) ---")
lines = dump_region(ROM, 0xC0EDCE, 96)
for addr, h, a in lines:
    print(f"  ${addr:06X}: {h}  {a}")

print("\n--- func_C0852D (NMI Slot Dispatch) ---")
lines = dump_region(ROM, 0xC0852D, 64)
for addr, h, a in lines:
    print(f"  ${addr:06X}: {h}  {a}")

print("\n--- func_C0A252 (Input Read) ---")
lines = dump_region(ROM, 0xC0A252, 64)
for addr, h, a in lines:
    print(f"  ${addr:06X}: {h}  {a}")

# ============================================================
# 3. PLAYER PHYSICS - Look for velocity tables / gravity constants
# ============================================================
print()
print("=" * 60)
print("PHYSICS CONSTANTS SEARCH")
print("=" * 60)

# Look for common 16-bit constants used in platformers:
# Gravity in DKC is typically around 0x0040-0x0100 range
# Jump velocity around 0xFD00-0xFFFF (negative = up)
# Walk speed around 0x0020-0x0080

# Search for potential physics tables near known code
# Check banks $C0-$C3 for word patterns

# Read the area around state machine for constants
print("\n--- func_C09BE7 (State Machine) ---")
lines = dump_region(ROM, 0xC09BE7, 80)
for addr, h, a in lines:
    print(f"  ${addr:06X}: {h}  {a}")

# Look at bank $BA, $BB, $BC (SA-1 object code)
print("\n--- Bank BA start (SA-1 Object Code) ---")
lines = dump_region(ROM, 0xBA8000, 64)
for addr, h, a in lines:
    print(f"  ${addr:06X}: {h}  {a}")

print("\n--- Bank BB start (SA-1 Object Code) ---")
lines = dump_region(ROM, 0xBB8000, 64)
for addr, h, a in lines:
    print(f"  ${addr:06X}: {h}  {a}")

print("\n--- Bank BC start (SA-1 Object/Collision) ---")
lines = dump_region(ROM, 0xBC8000, 64)
for addr, h, a in lines:
    print(f"  ${addr:06X}: {h}  {a}")

# ============================================================
# 4. ROPE SYSTEM SEARCH
# ============================================================
print()
print("=" * 60)
print("ROPE SYSTEM SEARCH")
print("=" * 60)

# DKC2 ropes - search banks for rope-related patterns
# Common rope mechanics involve:
# - Vertical climb speed
# - Horizontal swing
# - Disconnect detection

# Look for known rope sprite type IDs
# In DKC2, sprite/object types are often mapped via dispatch tables
# Let's scan banks for patterns

# Bank BA (SA-1 code) likely has object-specific handlers
print("\n--- Bank BA $A000 region ---")
# BA8000 is SA-1 mapped; let's also check $00-$7F area
# In LoROM, bank $BA maps to ROM offset (0xBA-0x80)*0x10000 = 0x3A0000
rom_off_BA = 0x3A0000  # BA80
print(f"  BA8000 ROM offset: ${rom_off_BA:06X}")

# Check BD bank - additional object logic
print("\n--- Bank BD start ---")
lines = dump_region(ROM, 0xBD8000, 64)
for addr, h, a in lines:
    print(f"  ${addr:06X}: {h}  {a}")

# ============================================================
# 5. BARREL SYSTEM SEARCH
# ============================================================
print()
print("=" * 60)
print("BARREL SYSTEM SEARCH")
print("=" * 60)

# Barrel cannons and DK barrels are iconic DKC2 features
# Look in the sprite code areas

print("\n--- Bank BE (Timer/Sound) ---")
lines = dump_region(ROM, 0xBE8000, 64)
for addr, h, a in lines:
    print(f"  ${addr:06X}: {h}  {a}")

# ============================================================
# 6. ENEMY AI SEARCH  
# ============================================================
print()
print("=" * 60)
print("ENEMY AI SEARCH")
print("=" * 60)

# Bank BB likely has enemy AI logic
print("\n--- Bank BB $8000-$8100 ---")
lines = dump_region(ROM, 0xBB8000, 256)
for addr, h, a in lines:
    print(f"  ${addr:06X}: {h}  {a}")

# ============================================================
# 7. SA-1 DISPATCH TABLES
# ============================================================
print()
print("=" * 60)
print("SA-1 DISPATCH TABLES")
print("=" * 60)

# Table at $C08DF9 (state $0038 handler)
print("\n--- SA-1 table 1 ($C08DF9, state=0x38) ---")
off = snes_to_rom(0xC08DF9)
if off:
    # The table contains 65816 code executed by SA-1
    for i in range(0, min(64, len(ROM)-off), 16):
        b = ROM[off+i:off+i+16]
        h = " ".join(f"{x:02X}" for x in b)
        print(f"  ${0xC08DF9+i:06X}: {h}")

# Table at $C08E21 (state $003B handler)
print("\n--- SA-1 table 2 ($C08E21, state=0x3B) ---")
off = snes_to_rom(0xC08E21)
if off:
    for i in range(0, min(64, len(ROM)-off), 16):
        b = ROM[off+i:off+i+16]
        h = " ".join(f"{x:02X}" for x in b)
        print(f"  ${0xC08E21+i:06X}: {h}")

# ============================================================
# 8. SPRITE DISPATCH TABLES
# ============================================================
print()
print("=" * 60)
print("SPRITE TYPE DISPATCH SEARCH")
print("=" * 60)

# Look at the Game Phase Dispatch area
print("\n--- Phase Dispatch ($C08687) ---")
lines = dump_region(ROM, 0xC08687, 48)
for addr, h, a in lines:
    print(f"  ${addr:06X}: {h}  {a}")

# Look at SA-1 shared handler ($C088F9)
print("\n--- SA-1 Shared Handler ($C088F9) ---")
lines = dump_region(ROM, 0xC088F9, 64)
for addr, h, a in lines:
    print(f"  ${addr:06X}: {h}  {a}")

# ============================================================
# 9. SCAN FOR JUMP/VELOCITY TABLES
# ============================================================
print()
print("=" * 60)
print("VELOCITY/GRAVITY TABLES")
print("=" * 60)

# Common platformer constant patterns:
# 16-bit signed values used as velocity
# Scan bank $C0 for word patterns that look like velocity tables

# Look at commonly referenced addresses for values
candidates = [0xC0A000, 0xC0A100, 0xC0A200, 0xC0A300, 0xC0A400,
              0xC0A500, 0xC0A600, 0xC0A700, 0xC0A800, 0xC0A900,
              0xC0AA00, 0xC0AB00, 0xC0AC00, 0xC0ED00]

for addr in candidates:
    off = snes_to_rom(addr)
    if off and off + 32 <= len(ROM):
        vals = []
        for i in range(0, 32, 2):
            w = struct.unpack_from("<H", ROM, off+i)[0]
            s = signed16(w)
            vals.append(f"${w:04X}({s})" if s is not None else f"${w:04X}")
        print(f"  ${addr:06X}: {' '.join(vals[:8])}")
        if len(vals) > 8:
            nxt = ' '.join(vals[8:16])
            print(f"  {'':10s} {' '.join(vals[8:16])}")

# ============================================================
# 10. BANK SUMMARY INFO
# ============================================================
print()
print("=" * 60)
print("ROM LAYOUT")
print("=" * 60)

# From rom_map.py output ROM size is 4MB, 128 banks (64 mapped)
# Banks $00-$3F = $80-$BF (LoROM mapping)
# Banks $40-$63 = $C0-$FF (top half of ROM)
for b_idx in range(64):
    bank_start = b_idx * 0x10000
    bank_end = min(bank_start + 0x10000, len(ROM))
    chunk = ROM[bank_start:bank_end]
    unique = len(set(chunk))
    if unique <= 2:
        continue  # skip empty banks
    snes_bank_lo = 0x80 + b_idx
    snes_bank_hi = 0xC0 + b_idx
    # Check for JML/JMP vectors at start
    has_code = any(chunk[i] == 0x5C or chunk[i] == 0x4C for i in range(min(16, len(chunk))))
    # Check for PAC1 headers
    pac1_count = 0
    for po in range(0, len(chunk)-39, 39):
        if chunk[po] == 0x00:
            valid = 0
            for pi in range(16):
                pw = struct.unpack_from("<H", chunk, po+7+pi*2)[0]
                if (pw >> 8) == 0:
                    valid += 1
            if valid >= 12:
                pac1_count += 1
    tag = "code" if has_code else "data"
    print(f"  Bank ${b_idx:02X} (SNES ${snes_bank_lo:02X}/C${snes_bank_hi:02X}): "
          f"{len(chunk):6d}B unique={unique:4d} PAC1={pac1_count:3d} [{tag}]")
