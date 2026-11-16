rom = open('roms/dkc2.sfc', 'rb').read()
def r(b,a): return (b&0x3F)*0x10000+a
print('=== Bytes at 0x80:B0EE ===')
a = r(0x80, 0xB0EE)
for i in range(64):
    print(f'80:{0xB0EE+i:04X} = {rom[a+i]:02X}', end='  ')
    if (i+1)%8 == 0: print()
