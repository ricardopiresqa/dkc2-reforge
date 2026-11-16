"""Search for STA $06A7 and STA $0687 in ROM to find sprite graphics setup."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'asm-pipeline'))
from disasm65816 import rom_offset

rom = open(os.path.join(os.path.dirname(__file__), '..', '..', 'roms', 'dkc2.sfc'), 'rb').read()

# STA $06A7 = 8D A7 06 (store sprite_gfx_bank)
# STA $0687 = 8D 87 06 (store sprite_code_id)

for name, needle, snes_base in [
    ('STA $06A7 (sprite_gfx_bank)', b'\x8d\xa7\x06', 0x800000),
    ('STA $0687 (sprite_code_id)', b'\x8d\x87\x06', 0x800000),
]:
    print(f'\n=== {name} ===')
    # Search at all possible values of base (FastROM area $200000-$3FFFFF)
    search_area = rom[0x200000:0x400000]
    pos = 0
    while True:
        idx = search_area.find(needle, pos)
        if idx == -1:
            break
        rom_abs = 0x200000 + idx
        bank_num = 0x80 + idx // 0x8000
        offset_in_bank = 0x8000 + (idx % 0x8000)
        snes_addr = bank_num * 0x10000 + offset_in_bank
        
        ctx_start = max(0, idx - 12)
        ctx = rom[0x200000 + ctx_start : 0x200000 + idx + 6]
        hex_ctx = ' '.join(f'{b:02x}' for b in ctx)
        print(f'  ROM {rom_abs:#010x} = ${snes_addr:06X}  ctx: ... {hex_ctx}')
        
        pos = idx + 3
