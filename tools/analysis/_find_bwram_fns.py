"""Find all JSL calls to SA-1 BW-RAM (bank B4) and the blob copy mechanism."""

with open('roms/dkc2.sfc', 'rb') as f:
    rom = f.read()

# Find all JSL $B4xxxxxx
print("=== JSL calls to SA-1 BW-RAM (bank B4) ===")
for i in range(len(rom)-4):
    if rom[i] == 0x22 and rom[i+3] == 0xB4:  # JSL $B4xxxxxx
        dest = rom[i+1] | (rom[i+2] << 8) | (rom[i+3] << 16)
        print(f'  ROM 0x{i:06X}: JSL ${dest:06X}')

# Also find JML $B4xxxxxx
print("\n=== JML/JMP calls to bank B4 ===")
for i in range(len(rom)-4):
    if rom[i] == 0x5C and rom[i+3] == 0xB4:  # JML $B4xxxxxx
        dest = rom[i+1] | (rom[i+2] << 8) | (rom[i+3] << 16)
        print(f'  ROM 0x{i:06X}: JML ${dest:06X}')

# Find any references to $B4 as data source (for copy)
# LDA $B4xxxx pattern (AF xx xx B4) or LDA $xxxx with bank B4
print("\n=== Long accesses to bank B4 (likely reads from BW-RAM) ===")
for i in range(len(rom)-4):
    if rom[i] == 0xAF and rom[i+3] == 0xB4:  # LDA long $B4xxxx
        addr = rom[i+1] | (rom[i+2] << 8) | (rom[i+3] << 16)
        print(f'  ROM 0x{i:06X}: LDA ${addr:06X}')

# Find writes TO bank B4 (STA long / $8F xx xx B4)
print("\n=== Long writes to bank B4 (into BW-RAM) ===")
for i in range(len(rom)-4):
    if rom[i] == 0x8F and rom[i+3] == 0xB4:  # STA long $B4xxxx
        addr = rom[i+1] | (rom[i+2] << 8) | (rom[i+3] << 16)
        ctx = rom[max(0,i-4):i+8]
        print(f'  ROM 0x{i:06X}: STA ${addr:06X}  {" ".join(f"{b:02X}" for b in ctx)}')

# Search for SA-1 DMA setup patterns
# Character conversion DMA: write to $2230-$223F
print("\n=== SA-1 DMA setup (writes to $2230-$223F) ===")
sa1_dma_regs = {0x2230: 'DMAEN', 0x2231: 'CCEN', 0x2232: 'DMA destination table', 
                0x2233: 'DMA source table', 0x2235: 'DMA length low', 
                0x2236: 'DMA length high', 0x2237: 'DMA source bank',
                0x2238: 'DMA dest bank'}
for reg, desc in sa1_dma_regs.items():
    # STA abs reg
    for i in range(len(rom)-3):
        lo = reg & 0xFF
        if rom[i] == 0x8D and rom[i+1] == lo and rom[i+2] == 0x22:
            ctx = rom[max(0,i-4):i+8]
            print(f'  ROM 0x{i:06X}: STA $22{lo:02X} ({desc})  {" ".join(f"{b:02X}" for b in ctx)}')
        # STZ abs reg
        if rom[i] == 0x9C and rom[i+1] == lo and rom[i+2] == 0x22:
            ctx = rom[max(0,i-4):i+12]
            print(f'  ROM 0x{i:06X}: STZ $22{lo:02X} ({desc})  {" ".join(f"{b:02X}" for b in ctx)}')

# Find BW-RAM copy pattern by searching for LDA #$B4 then STA $222x (BW-RAM bank register)
# For SA-1: writing to $2224-$2226 sets the BW-RAM address mapping
print("\n=== BW-RAM bank register writes ($2224-$2226) ===")
for i in range(len(rom)-4):
    if rom[i] == 0xA9:  # LDA #xx
        nxt = rom[i+2] if i+2 < len(rom) else 0
        if nxt == 0x8D and (rom[i+3] == 0x24 or rom[i+3] == 0x25 or rom[i+3] == 0x26):
            # LDA #xx, STA $222x
            val = rom[i+1]
            reg = rom[i+3]
            ctx = rom[i:i+8]
            print(f'  ROM 0x{i:06X}: LDA #${val:02X} STA $22{reg:02X}  {" ".join(f"{b:02X}" for b in ctx)}')
