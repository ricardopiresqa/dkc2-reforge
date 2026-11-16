import os
rom = open('roms/dkc2.sfc', 'rb').read()
def rb(bank, addr):
    return rom[((bank & 0x3F) * 0x10000) + addr]

def dump(bank, start, end):
    for a in range(start, end):
        idx = a - start
        if idx % 16 == 0:
            print('%04X: ' % a, end='')
        print('%02x ' % rb(bank, a), end='')
        if idx % 16 == 15:
            print()
    if (end - start) % 16 != 0:
        print()

print("=== $80:B461-$B700 ===")
dump(0x80, 0xB461, 0xB700)

print()
print("=== $80:A2C0-$A300 ===")
dump(0x80, 0xA2C0, 0xA300)

print()
print("=== $80:A800-$A900 ===")
dump(0x80, 0xA800, 0xA900)

print()
print("=== $80:99C0-$9A40 ===")
dump(0x80, 0x99C0, 0x9A40)

# Check what's at $B0EE (handler transition JMP target)
print()
print("=== $80:B0E0-$B110 ===")
dump(0x80, 0xB0E0, 0xB110)

# Check what's around $8CAC (JSR target from dead code area)
print()
print("=== $80:8CAC-$8CE0 ===")
dump(0x80, 0x8CAC, 0x8CE0)

# Check the $099B related code in $8C8x area
print()
print("=== $80:8C80-$8CA0 ===")
dump(0x80, 0x8C80, 0x8CA0)

# Check $80A5F1 (JML target from $099B path)
print()
print("=== $80:A5F0-$A660 ===")
dump(0x80, 0xA5F0, 0xA660)
