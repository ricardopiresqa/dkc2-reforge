rom = open('roms/dkc2.sfc', 'rb').read()
def r(b,a): return (b&0x3F)*0x10000+a

# Quick raw dump from NMI handler for manual decode
print("=== Raw bytes $80:F3C1-F430 ===")
a = r(0x80, 0xF3C1)
for j in range(0, 112, 8):
    off = a + j
    bytes_str = ' '.join(f'{rom[off+k]:02X}' for k in range(8))
    print(f"$80:{0xF3C1+j:04X}: {bytes_str}")
