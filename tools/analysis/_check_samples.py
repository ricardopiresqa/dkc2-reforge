import struct

# Check a 0-byte output case
data = open('samples/asset_b80_D0CA_2075B.bin', 'rb').read()
print('asset_b80_D0CA_2075B:')
print(f'  Total size: {len(data)}')
print(f'  byte[0]: {data[0]:02X}')
print(f'  header[1-4]: {data[1]:02X} {data[2]:02X} {data[3]:02X} {data[4]:02X}')
w = struct.unpack_from('<H', data, 5)[0]
print(f'  word[5-6]: {w:04X}')
print(f'  pool[7-38][:8]: {list(data[7:15])}')
print(f'  fmt at 39: ${data[39]:02X} (hi={(data[39]>>4)&0xF} lo={data[39]&0xF})')
print(f'  fmt at 40: ${data[40]:02X} (hi={(data[40]>>4)&0xF} lo={data[40]&0xF})')
print(f'  fmt at 41: ${data[41]:02X} (hi={(data[41]>>4)&0xF} lo={data[41]&0xF})')
print()

# Check the error case
data2 = open('samples/asset_b80_943C_908B.bin', 'rb').read()
print('asset_b80_943C_908B:')
print(f'  Total size: {len(data2)}')
print(f'  byte[0]: {data2[0]:02X}')
print(f'  header[1-4]: {data2[1]:02X} {data2[2]:02X} {data2[3]:02X} {data2[4]:02X}')
w = struct.unpack_from('<H', data2, 5)[0]
print(f'  word[5-6]: {w:04X}')
print(f'  pool[7-38][:8]: {list(data2[7:15])}')
print(f'  fmt at 39: ${data2[39]:02X} (hi={(data2[39]>>4)&0xF} lo={data2[39]&0xF})')
print(f'  fmt at 40: ${data2[40]:02X} (hi={(data2[40]>>4)&0xF} lo={data2[40]&0xF})')
print(f'  fmt at 41: ${data2[41]:02X} (hi={(data2[41]>>4)&0xF} lo={data2[41]&0xF})')
print()

# Let's look at the first format byte pattern of 0-byte outputs
from _decompress import decompress
for name in ['asset_b80_D0CA_2075B.bin', 'asset_b83_CDA1_751B.bin', 'asset_b84_B0DA_1553B.bin']:
    data = open(f'samples/{name}', 'rb').read()
    f0 = data[39]
    f1 = data[40] if len(data) > 40 else -1
    f2 = data[41] if len(data) > 41 else -1
    print(f'{name}: fmt0=${f0:02X} fmt1=${f1:02X} fmt2=${f2:02X} -> ', end='')
    try:
        r = decompress(data)
        print(f'{len(r)} bytes')
    except Exception as e:
        print(f'ERROR: {e}')
