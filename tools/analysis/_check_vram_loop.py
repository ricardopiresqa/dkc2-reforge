rom = open('roms/dkc2.sfc', 'rb').read()

def r(bank, addr):
    return (bank & 0x3F) * 0x10000 + addr

# Show raw bytes around $913E to understand where code continues after the VRAM clear loop
base = 0x80
print("Raw bytes around $80:9138:")
addr = r(base, 0x9138)
for i in range(32):
    off = 0x9138 + i
    a = r(base, off)
    print(f"${base:02X}:{off:04X} = {rom[a]:02X}")
