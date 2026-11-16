rom = open('roms/dkc2.sfc', 'rb').read()

# Verified: SA-1 linear mapping = (bank & 0x3F) * 0x10000 + addr (full 64KB banks)
def sa1(bank, addr):
    return (bank & 0x3F) * 0x10000 + addr

# Check main game entry at $80:90DA
print('=== Main entry JML $8090DA ===')
off = sa1(0x80, 0x90DA)
print(f'ROM 0x{off:06X}: {" ".join(f"{b:02X}" for b in rom[off:off+64])}')

# Check what subroutines it calls  
# JSR $90CD - relative or absolute? In 65816, JSR $90CD is absolute within bank
off2 = sa1(0x80, 0x90CD)
print(f'\nSub $80:90CD @ ROM 0x{off2:06X}: {" ".join(f"{b:02X}" for b in rom[off2:off2+32])}')

# Check JSL $B58000
print('\n=== JSL $B58000 ===')
off3 = sa1(0xB5, 0x8000)
print(f'ROM 0x{off3:06X}: {" ".join(f"{b:02X}" for b in rom[off3:off3+32])}')

# Follow the JMP at $B5:8000 (it's 4C 8D 81 = JMP $818D)
# JMP $818D in bank $B5
off4 = sa1(0xB5, 0x818D)
print(f'\nJMP target $B5:818D @ ROM 0x{off4:06X}: {" ".join(f"{b:02X}" for b in rom[off4:off4+32])}')

# Check JSL $BB91D9
print('\n=== JSL $BB91D9 ===')
off5 = sa1(0xBB, 0x91D9)
print(f'ROM 0x{off5:06X}: {" ".join(f"{b:02X}" for b in rom[off5:off5+48])}')

# Verify the $B5 table more completely
print('\n=== $B5:8000 vector table ===')
for i in range(8):
    base = sa1(0xB5, 0x8000 + i*3)
    if base + 2 < len(rom):
        op = rom[base]
        target = rom[base+1] | (rom[base+2] << 8)
        if op == 0x4C:  # JMP abs
            print(f'  Entry {i}: JMP ${target:04X}')
        elif op == 0x5C:  # JML long
            target_long = target | (rom[base+3] << 16)
            print(f'  Entry {i}: JML ${target_long:06X}')
        else:
            print(f'  Entry {i}: opcode ${op:02X} data={rom[base]:02X} {rom[base+1]:02X} {rom[base+2]:02X}')

# Check what the JMP $818D does (the first entry of $B5)
print('\n=== $B5:818D code ===')
off6 = sa1(0xB5, 0x818D)
d = rom[off6:off6+64]
for i in range(0, 64, 16):
    print(f'  ROM 0x{off6+i:06X}: {" ".join(f"{b:02X}" for b in d[i:i+16])}')
