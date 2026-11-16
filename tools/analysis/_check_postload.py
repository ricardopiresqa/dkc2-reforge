rom = open('roms/dkc2.sfc', 'rb').read()

def r(bank, addr):
    return (bank & 0x3F) * 0x10000 + addr

# Look at the area after the last JSL $BB8D91 calls
# We know they occur up to $92C0 from scan
# Check what's at $92C0-$9400

print("=== Raw bytes $80:92BD-$93FF ===")
for off in range(0x92BD, 0x9400):
    a = r(0x80, off)
    print(f"${0x80:02X}:{off:04X} = {rom[a]:02X}", end='  ')
    if (off - 0x92BD + 1) % 8 == 0: print()

print()

# Also check: the JML found earlier at $97C0
print("=== Raw bytes $80:97B0-9820 ===")
for off in range(0x97B0, 0x9820):
    a = r(0x80, off)
    print(f"${0x80:02X}:{off:04X} = {rom[a]:02X}", end='  ')
    if (off - 0x97B0 + 1) % 8 == 0: print()

print()

# Check what's at $80:A5F1 (JML target from $90AD - init)
print("=== Raw bytes $80:A5F1-A630 ===")
for off in range(0xA5F1, 0xA630):
    a = r(0x80, off)
    print(f"${0x80:02X}:{off:04X} = {rom[a]:02X}", end='  ')
    if (off - 0xA5F1 + 1) % 8 == 0: print()
