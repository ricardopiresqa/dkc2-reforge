rom = open('roms/dkc2.sfc', 'rb').read()

def r(bank, addr):
    return (bank & 0x3F) * 0x10000 + addr

# Look at the code after the many JSL $BB8D91 calls (approx $9200+)
# Let me find where the init ends and what happens

# First, check what's at $FAA0 - raw bytes
print("Raw bytes at $80:FAA0:")
addr = r(0x80, 0xFAA0)
for i in range(32):
    a = addr + i
    print(f"${0x80:02X}:{0xFAA0+i:04X} = {rom[a]:02X}", end='  ')
    if (i+1) % 8 == 0: print()
print()

# Check what's at $8C32-$8C9E area (the JSR targets from $FAA0)
print("\nRaw bytes at $80:8C32-8C9E:")
addr = r(0x80, 0x8C32)
for i in range(16):
    a = addr + i
    print(f"${0x80:02X}:{0x8C32+i:04X} = {rom[a]:02X}")

# Look for data after the VRAM clear - maybe $9142 code
# Actually, after the VRAM clear loop, maybe there's more init 
# Let me scan for all JSL $BB calls in the $91xx area to find the end of loading
print("\n\nScanning for JSL $BB calls in $9000-$9400:")
for b in range(0x80, 0x81):
    for p in range(0x9000, 0x9400):
        addr = r(b, p)
        if addr+3 < len(rom):
            if rom[addr] == 0x22 and rom[addr+1] == 0x91 and rom[addr+2] == 0x8D and rom[addr+3] == 0xBB:
                print(f"  JSL $BB8D91 at ${b:02X}:{p:04X}")

# Scan for all JML in $9000-$9800
print("\n\nJML/JMP targets in $9000-$9800:")
for b in range(0x80, 0x81):
    for p in range(0x9000, 0x9800):
        addr = r(b, p)
        if addr+3 < len(rom):
            if rom[addr] == 0x5C:  # JML
                t = rom[addr+1] | (rom[addr+2] << 8) | (rom[addr+3] << 16)
                print(f"  JML ${t>>16:02X}:{t&0xFFFF:04X} at ${b:02X}:{p:04X}")
            if rom[addr] == 0x4C:  # JMP
                t = rom[addr+1] | (rom[addr+2] << 8)
                if t < 0x8000 or t > 0xFFFF:
                    print(f"  JMP $80:{t:04X} at ${b:02X}:{p:04X} -> OUT OF BANK ($80 range is 8000-FFFF!)")
                # Print all JMPs for analysis
