rom = open('roms/dkc2.sfc', 'rb').read()

# Direct approach: just show raw bytes for specific areas
# to avoid the truncation issue

def r(bank, addr):
    return (bank & 0x3F) * 0x10000 + addr

# After LDA #$0011 in main entry - what happens next?
print("=== $80:90F4 onwards ===")
off = r(0x80, 0x90F4)
for i in range(0, 128, 16):
    d = rom[off+i:off+i+16]
    print(f'  {off+i:06X}: {" ".join(f"{b:02X}" for b in d)}')

# Check $B5:80D5 (entry 2 - called by main entry)
print("\n=== $B5:80D5 (entry 2 target) ===")
off = r(0xB5, 0x80D5)
for i in range(0, 128, 16):
    d = rom[off+i:off+i+16]
    print(f'  {off+i:06X}: {" ".join(f"{b:02X}" for b in d)}')

# $B5:8030 (entry 1)
print("\n=== $B5:8030 (entry 1) ===")
off = r(0xB5, 0x8030)
for i in range(0, 96, 16):
    d = rom[off+i:off+i+16]
    print(f'  {off+i:06X}: {" ".join(f"{b:02X}" for b in d)}')

# $80:90CD (sub called at start of main entry)
print("\n=== $80:90CD ===")
off = r(0x80, 0x90CD)
for i in range(0, 32, 16):
    d = rom[off+i:off+i+16]
    print(f'  {off+i:06X}: {" ".join(f"{b:02X}" for b in d)}')

# What's at $8090DA + ~32 bytes past the JSL?
print("\n=== $80:90F7 (after LDA #$0011) ===")
off = r(0x80, 0x90F7)
for i in range(0, 192, 16):
    d = rom[off+i:off+i+16]
    print(f'  {off+i:06X}: {" ".join(f"{b:02X}" for b in d)}')
