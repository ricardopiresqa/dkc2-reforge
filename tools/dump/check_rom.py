import binascii

with open('roms/dkc2.sfc', 'rb') as f:
    data = f.read()

print(f'Tamanho: {len(data)} bytes')

# LoROM header
chunk = data[0x00FFC0:0x010000]
for i in range(0, len(chunk), 16):
    hexstr = binascii.hexlify(chunk[i:i+16]).decode()
    printable = ' '.join(chr(b) if 32 <= b < 127 else '.' for b in chunk[i:i+16])
    print(f'  0x00FFC0+{i:02X}: {hexstr}  {printable}')

rom_type = data[0x00FFD5]
rom_size = data[0x00FFD7]
rom_speed = data[0x00FFD6]
print(f'\nROM type: {hex(rom_type)} (LoROM=0, HiROM=1)')
print(f'ROM speed: {hex(rom_speed)}')
print(f'ROM size byte: {hex(rom_size)}')
if rom_size >= 7 and rom_size <= 16:
    expected = 1 << (rom_size + 10)
print(f'  => {expected} bytes ({expected // 1024 // 1024} MB)')

# Check for HiROM in extended area  
for bank in range(0, 0x80, 1):
    addr = bank * 0x10000 + 0xFFC0
    if addr + 21 <= len(data):
        title = data[addr:addr+21]
        try:
            t = title.decode('utf-8').rstrip(chr(0)).rstrip()
            if t and len(t) > 5:
                print(f'Title at bank {hex(bank)}: \"{t}\"')
        except:
            pass

# Checksum check
checksum = int.from_bytes(data[0x00FFDE:0x00FFE0], 'little')
checksum_inv = int.from_bytes(data[0x00FFDC:0x00FFDE], 'little')
print(f'\nChecksum: {hex(checksum)}, inv: {hex(checksum_inv)}')
calc = sum(data[i] for i in range(0x00FFDC)) & 0xFFFF
inv_check = sum(data[i] for i in range(0x00FFDC)) & 0xFFFF
print(f'Calculated: {hex((calc ^ checksum) & 0xFFFF)}')
print(f'Checksum verify: {(checksum_inv ^ checksum) & 0xFFFF == 0xFFFF}')
