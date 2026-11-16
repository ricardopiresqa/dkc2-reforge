"""Find sprite_type -> PAC1 mapping tables via direct binary analysis.

Approach:
1. Decompress all large PAC1 archives, identify 4bpp tile data
2. Search for tables pairing sprite_type IDs with PAC1 offsets
3. Cross-reference with known sprite behaviors
"""
import json, os, struct, sys
sys.path.insert(0, os.path.dirname(__file__))
from decode_pac1 import decompress, header_score

ROM_PATH = os.path.join(os.path.dirname(__file__), '..', '..', 'roms', 'dkc2.sfc')
JSON_PATH = os.path.join(os.path.dirname(__file__), '..', '..', 'docs', 'rom-map.json')

rom = open(ROM_PATH, 'rb').read()
ROM_SIZE = len(rom)

# HiROM addressing
def snes_to_rom(snes_addr):
    bank = (snes_addr >> 16) & 0xFF
    off = snes_addr & 0xFFFF
    if 0xC0 <= bank <= 0xFF:
        return (bank - 0xC0) * 0x10000 + off
    return None

def rom_to_snes(rom_off):
    if rom_off < 0 or rom_off >= ROM_SIZE:
        return None
    bank = 0xC0 + (rom_off // 0x10000)
    return (bank << 16) | (rom_off % 0x10000)

# Load PAC1 headers
with open(JSON_PATH) as f:
    rd = json.load(f)

print(f'=== PAC1 Sweep: {len(rd["pac1_headers"])} headers ===')

# Decompress all and classify
tile_candidates = []
for h in rd['pac1_headers']:
    off = h['rom_offset']
    try:
        data = decompress(rom, off)
    except Exception:
        continue
    if not data or len(data) < 64:
        continue
    
    size = len(data)
    # 4bpp tiles = size % 32 == 0
    # 8bpp tiles = size % 64 == 0  
    # 2bpp tiles = size % 16 == 0
    valid_formats = []
    if size % 32 == 0:
        valid_formats.append(f'4bpp({size//32}t)')
    if size % 64 == 0:
        valid_formats.append(f'8bpp({size//64}t)')
    if size % 16 == 0:
        valid_formats.append(f'2bpp({size//16}t)')
    
    tile_candidates.append({
        'rom_offset': off,
        'snes_addr': rom_to_snes(off),
        'size': size,
        'formats': '|'.join(valid_formats),
        'comp_ratio': f'{size/(39 if off+39 < ROM_SIZE else 1):.1f}x' if off+39 < ROM_SIZE else '?',
    })

tile_candidates.sort(key=lambda x: x['size'], reverse=True)

# Show top 60
print(f'\n=== Top 60 PAC1 archives by decompressed size ===')
print(f'{"#":>3} {"ROM Off":>10} {"SNES":>10} {"Size":>8} {"Format":>20} {"Ratio":>8}')
for i, c in enumerate(tile_candidates[:60]):
    snes_str = f'${c["snes_addr"]:06X}' if c['snes_addr'] else 'N/A'
    print(f'{i+1:>3} {c["rom_offset"]:#08x} {snes_str:>10} {c["size"]:>8} {c["formats"]:>20} {c["comp_ratio"]:>8}')

# Stats
sizes = [c['size'] for c in tile_candidates]
print(f'\n=== Stats ===')
print(f'Total decompressed: {len(tile_candidates)}')
print(f'Size range: {min(sizes)} - {max(sizes)}')
sizes.sort()
for pct in [50, 75, 90, 95, 99]:
    idx = int(len(sizes) * pct / 100)
    print(f'  P{pct}: {sizes[idx]:>7} bytes')
print(f' 4bpp candidates (>512B, size%32==0): {sum(1 for c in tile_candidates if c["size"] > 512 and "4bpp" in c["formats"])}')

# Now search for sprite_type -> PAC1 offset tables
# Known sprite type IDs from sprites.txt:
# $E4 = Diddy, $E8 = Dixie
# The mapping table would be an array of {sprite_type, pointer_to_pac1_data}
# Common patterns:
# - Type byte + 3-byte pointer (bank + offset)
# - Type byte + 2-byte pointer (offset within a bank)
# - Direct index table indexed by sprite_type

# Strategy: search near large PAC1 archives for type IDs
# A sprite mapping table entry is typically:
# [sprite_type_byte] + [24-bit_or_16-bit_pointer]

print(f'\n=== Searching for sprite_type mapping tables ===')

# Known sprite_type IDs range typically $00-$FF
# Common sprite types in DKC2 include $E4 (Diddy), $E8 (Dixie)
known_types = [0xE4, 0xE8]

# Search for patterns that could be mapping entries
# Pattern: byte (type) + 3 bytes (offset) repeated in sequence
# The entries are usually contiguous in ROM

# Approach: find regions where we see types E4/E8 followed by plausible PAC1 offsets
def find_nearby_pac1(rom_off, radius=0x1000):
    """Find PAC1 headers near a ROM offset."""
    nearby = []
    for h in rd['pac1_headers']:
        ho = h['rom_offset']
        if abs(ho - rom_off) <= radius:
            nearby.append(ho)
    return nearby

# Scan banks for sequences of {byte, 24-bit-offset}
print('\nScanning for {type_id, 24bit_offset} tables (entry size = 4)...')
candidates = []
for bank_start in range(0, ROM_SIZE, 0x10000):
    bank_end = min(bank_start + 0x10000, ROM_SIZE)
    table_start = None
    entries = []
    
    for off in range(bank_start, bank_end - 4):
        sprite_type = rom[off]
        offset_24 = rom[off+1] | (rom[off+2] << 8) | (rom[off+3] << 16)
        
        # Check if offset points to within ROM
        if 0 <= offset_24 < ROM_SIZE:
            # Check if the offset is near a PAC1 header
            nearby = find_nearby_pac1(offset_24, radius=64)
            if nearby:
                entries.append({
                    'type': f'${sprite_type:02X}',
                    'offset': offset_24,
                    'near_pac1': nearby
                })
    
    if entries:
        print(f'  Bank ${bank_start//0x10000:02X}: {len(entries)} candidate entries')

# More focused: search for Diddy ($E4) and Dixie ($E8) specifically
print(f'\n=== Searching for sprite_type $E4 (Diddy) and $E8 (Dixie) ===')
for target_type in [0xE4, 0xE8]:
    found = []
    for i in range(ROM_SIZE - 8):
        if rom[i] == target_type:
            # Check if nearby bytes could form a pointer to a PAC1
            for ptr_size in [3, 4]:
                if i + ptr_size < ROM_SIZE:
                    if ptr_size == 3:
                        ptr = rom[i+1] | (rom[i+2] << 8) | (rom[i+3] << 16)
                    else:
                        ptr = struct.unpack_from('<I', rom, i+1)[0]
                    nearby = find_nearby_pac1(ptr, radius=128)
                    if nearby:
                        found.append({'offset': i, 'ptr': ptr, 'ptr_size': ptr_size, 'near_pac1': nearby})
    
    print(f'\nSprite type ${target_type:02X}: {len(found)} occurrences near PAC1 data')
    for f in found[:20]:
        pac1_info = ', '.join(f'@{hex(p)}' for p in f['near_pac1'][:3])
        print(f'  ROM {hex(f["offset"])}: ptr={hex(f["ptr"])} size={f["ptr_size"]} near_PAC1=[{pac1_info}]')

# Also look for the table type that maps sprite_type -> {bank, offset}
# In SNES, this is often: sprite_type (1B) + bank (1B) + offset (2B LE) = 4B entries
print(f'\n=== Searching for {{type, bank, offset}} tables (4B entries) ===')
for bank_start in range(0, ROM_SIZE, 0x10000):
    bank_end = min(bank_start + 0x10000, ROM_SIZE)
    
    # Sliding window: look for sequences of (type, bank, loff, hoff) where
    # bank is 0x80-0xFF or 0xC0-0xFF (HiROM), and offset is 0x8000-0xFFFF
    seq_count = 0
    seq_start = None
    
    for off in range(bank_start, bank_end - 4):
        sprite_type = rom[off]
        bank = rom[off+1]
        ptr_off = rom[off+2] | (rom[off+3] << 8)
        
        # Valid HiROM bank C0-FF at offset 8000+ is where code/data typically lives
        # Or banks 80-BF at offset 8000+
        # But for the mapping, we'd expect pointers to ROM/data areas
        is_valid_bank = (0xC0 <= bank <= 0xFF) or (0x80 <= bank <= 0xBF)
        is_valid_off = (0x8000 <= ptr_off <= 0xFFFF) or (ptr_off < 0x8000 and is_valid_bank)
        
        # Convert to ROM offset and check if near PAC1
        if is_valid_bank:
            if bank >= 0xC0:
                rom_ptr = (bank - 0xC0) * 0x10000 + ptr_off
            else:
                rom_ptr = ((bank & 0x3F) * 0x8000) + (ptr_off - 0x8000) if ptr_off >= 0x8000 else None
            
            if rom_ptr and 0 <= rom_ptr < ROM_SIZE:
                nearby = find_nearby_pac1(rom_ptr, radius=128)
                if nearby:
                    if seq_start is None:
                        seq_start = off
                        seq_count = 1
                    else:
                        seq_count += 1
                else:
                    if seq_count >= 3:
                        print(f'  Bank ${bank_start//0x10000:02X}: seq at {hex(seq_start)} ({seq_count} entries)')
                    seq_start = None
                    seq_count = 0
            else:
                if seq_count >= 3:
                    print(f'  Bank ${bank_start//0x10000:02X}: seq at {hex(seq_start)} ({seq_count} entries)')
                seq_start = None
                seq_count = 0
        else:
            if seq_count >= 3:
                print(f'  Bank ${bank_start//0x10000:02X}: seq at {hex(seq_start)} ({seq_count} entries)')
            seq_start = None
            seq_count = 0
    
    if seq_count >= 3:
        print(f'  Bank ${bank_start//0x10000:02X}: seq at {hex(seq_start)} ({seq_count} entries)')
