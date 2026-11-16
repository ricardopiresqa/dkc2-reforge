# Parse VRAM payload table from bank_FD.asm
# Structure: pointer table at $FD8000, then 8-byte records

import re, struct, sys

with open(r'C:\Projetos Cursor\dkc2-reforge\tools\disassembly\export\bank_FD.asm', 'r') as f:
    lines = f.readlines()

# Extract all db bytes from the file with their ROM offsets
# Format: ;FDXXXX|  in comments
data = {}  # offset -> [bytes]
current_offset = None
current_bytes = []

for i, line in enumerate(lines):
    # Match ROM offset comment like ;FD8000|
    m = re.search(r';FD([0-9A-F]{4})\|', line, re.IGNORECASE)
    if m:
        if current_offset is not None and current_bytes:
            data[current_offset] = current_bytes
        current_offset = int(m.group(1), 16)
        current_bytes = []
    
    # Extract db data bytes
    db_match = re.search(r'db\s+(.+?)\s*;', line)
    if db_match:
        bytes_str = db_match.group(1).strip()
        # Parse bytes like $40,$00,$FD,$A2
        for b in bytes_str.split(','):
            b = b.strip()
            m2 = re.match(r'\$([0-9A-F]{2})', b, re.IGNORECASE)
            if m2:
                current_bytes.append(int(m2.group(1), 16))

if current_offset is not None and current_bytes:
    data[current_offset] = current_bytes

print(f"Parsed {len(data)} data blocks from bank_FD.asm")

# Find the VRAM payload table structure
# Pointer table at FD8000 (word entries pointing to data)
ptr_table_start = 0x8000
ptr_table_end = 0x81CC  # based on data analysis (456 bytes = 228 pointers)
ptr_data = data.get(ptr_table_start, [])
print(f"\nPointer table at FD8000: {len(ptr_data)} bytes")

# Extract all 2-byte pointers (LE)
ptrs = []
for i in range(0, len(ptr_data) - 1, 2):
    word_val = ptr_data[i] | (ptr_data[i+1] << 8)
    ptrs.append(word_val)

# Find where pointers end (when values become too small to be addresses)
# Pointers should be > 0x81CC (after the pointer table itself)
# But let's find the boundary automatically
print(f"\nFirst 50 pointers from FD8000:")
for i, p in enumerate(ptrs[:50]):
    print(f"  [{i:3d}] -> FD{p:04X}")

# Now look at the actual records starting from FD81CC
records_start = 0x81CC
rec_data = []
for off in sorted(data.keys()):
    if off >= records_start:
        rec_data.extend(data[off])

print(f"\nRecords at FD81CC: {len(rec_data)} bytes = {len(rec_data)//8} entries")

# Parse 8-byte records
# Try format: bank, flags, source_lo, source_hi, size_lo, size_hi, vram_lo, vram_hi
# Or: source_lo, source_hi, bank, flags, size_lo, size_hi, vram_lo, vram_hi
print(f"\nFirst 30 records (8 bytes each):")
for i in range(min(30, len(rec_data)//8)):
    offset = i * 8
    b = rec_data[offset:offset+8]
    hex_str = ' '.join(f'{x:02X}' for x in b)
    # Try different interpretations
    
    # Interpretation: source_addr = bank:offset (3 bytes), then 1 byte pad, size (2), vram_dest (2)
    src_off = b[1] | (b[2] << 8)  # uint16
    src_bank = b[0]
    size = b[4] | (b[5] << 8)
    vram_dest = b[6] | (b[7] << 8)
    
    # SNES address = bank:offset
    # For LoROM, bank $00-$7F maps to ROM offset bank*$8000 + offset
    # bank $80-$FF maps to ROM offset (bank-0x80)*$8000 + offset + 0x400000
    if src_bank >= 0x80:
        rom_offset = (src_bank - 0x80) * 0x8000 + src_off + 0x400000
    else:
        rom_offset = src_bank * 0x8000 + src_off
    
    print(f"  [{i:3d}] {hex_str} | bank=${src_bank:02X} off=${src_off:04X} (ROM={rom_offset:06X}) size={size:5d} VRAM=${vram_dest:04X}")
