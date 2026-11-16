import struct

rom = open('roms/dkc2.sfc', 'rb').read()

# Find all JSL $BB8D91 calls
pattern = b'\x22\x91\x8D\xBB'
results = []
offset = 0
while True:
    pos = rom.find(pattern, offset)
    if pos == -1:
        break
    bank = pos >> 16
    addr = pos & 0xFFFF
    results.append((pos, bank, addr))
    offset = pos + 1

print(f'Found {len(results)} JSL $BB8D91 calls:\n')
for pos, bank, addr in results:
    # Look before the JSL for the A/X/Y setup
    # Usually: LDA #$XXXX (A9 XX XX) for dest, LDX #$XXXX (A9 XX XX) for src, LDY #$XXXX (A0 XX XX) for flags
    start = max(0, pos - 30)
    ctx = rom[start:pos]
    print(f'  ROM 0x{pos:06X} -> SNES ${bank:02X}:{addr:04X}')
    # Try to extract the A/X/Y values from preceding instructions
    # Common pattern: LDY #$00 (A0 00), LDX #$XXXX (A2 XX XX), LDA #$XXXX (A9 XX XX)
    for i in range(len(ctx) - 3, -1, -1):
        if ctx[i] == 0xA9 and i + 2 < len(ctx):  # LDA #imm16
            val = struct.unpack_from('<H', ctx, i+1)[0]
            print(f'    LDA #${val:04X} at offset -{pos-start-i}')
        elif ctx[i] == 0xA2 and i + 2 < len(ctx):  # LDX #imm16
            val = struct.unpack_from('<H', ctx, i+1)[0]
            print(f'    LDX #${val:04X} at offset -{pos-start-i}')
        elif ctx[i] == 0xA0 and i + 2 < len(ctx):  # LDY #imm16
            val = struct.unpack_from('<H', ctx, i+1)[0]
            print(f'    LDY #${val:04X} at offset -{pos-start-i}')
    print()

# Also find the other decompress entry point $BB8D9E (A=0, X=src, Y=flags)
pattern2 = b'\x22\x9E\x8D\xBB'
offset = 0
while True:
    pos = rom.find(pattern2, offset)
    if pos == -1:
        break
    bank = pos >> 16
    addr = pos & 0xFFFF
    print(f'JSL $BB8D9E at ROM 0x{pos:06X} -> SNES ${bank:02X}:{addr:04X}')
    offset = pos + 1
