rom = open('roms/dkc2.sfc', 'rb').read()
def r(b,a): return (b&0x3F)*0x10000+a

# The NMI handler jumps to event handler via JMP ($0020)
# At init end: A = $93B8, JMP $B0EE -> STA $20
# So first event handler = $80:93B8
print("=== First event handler at $80:93B8 ===")
a = r(0x80, 0x93B8)
for j in range(0, 96, 8):
    off = a + j
    bytes_str = ' '.join(f'{rom[off+k]:02X}' for k in range(min(8, len(rom)-off)))
    print(f"$80:{0x93B8+j:04X}: {bytes_str}")
