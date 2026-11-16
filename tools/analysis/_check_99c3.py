rom = open('roms/dkc2.sfc', 'rb').read()
def r(b,a): return (b&0x3F)*0x10000+a

# Check what $99C3 handler does
pos = 0
target = 0x99C3
print(f"=== Handler $99C3 (set by $99BD) ===")
while pos < 30:
    a = r(0x80, target+pos)
    if a >= len(rom): break
    byte = rom[a]
    if byte == 0x4C:
        t = rom[a+1] | (rom[a+2]<<8)
        print(f"  {target+pos:04X}: JMP ${t:04X}"); break
    elif byte == 0x22:
        b = rom[a+1] | (rom[a+2]<<8) | (rom[a+3]<<16)
        print(f"  {target+pos:04X}: JSL ${b:06X}"); pos+=4
    elif byte == 0x5C:
        t = rom[a+1] | (rom[a+2]<<8) | (rom[a+3]<<16)
        print(f"  {target+pos:04X}: JML ${t:06X}"); break
    elif byte == 0x40:
        print(f"  {target+pos:04X}: RTI"); break
    elif byte == 0xA9:
        val = rom[a+1] | (rom[a+2]<<8)
        print(f"  {target+pos:04X}: LDA #{val:04X}"); pos+=3
    elif byte == 0x20:
        t = rom[a+1] | (rom[a+2]<<8)
        print(f"  {target+pos:04X}: JSR ${t:04X}"); pos+=3
    elif byte == 0x8F:
        val = rom[a+1] | (rom[a+2]<<8) | (rom[a+3]<<16)
        print(f"  {target+pos:04X}: STA ${val:06X}"); pos+=4
    else:
        print(f"  {target+pos:04X}: ${byte:02X}"); pos+=1

# Also check what's before $99BD handler set
print(f"\n=== Context around $99BD handler transition ===")
for offset in range(-12, 8):
    addr = 0x99BD + offset
    a = r(0x80, addr)
    byte = rom[a]
    print(f"  {addr:04X}: ${byte:02X}")

# Check $8085EF - the JML target from $9678 
print(f"\n=== $80:85EF (JML target from $9678) ===")
for i in range(10):
    a = r(0x80, 0x85EF+i)
    print(f"  {0x85EF+i:04X}: ${rom[a]:02X}")
