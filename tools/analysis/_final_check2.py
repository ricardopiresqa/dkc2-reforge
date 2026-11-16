rom = open('roms/dkc2.sfc', 'rb').read()

def r(bank, addr):
    return (bank & 0x3F) * 0x10000 + addr

# Look at dispatch table more carefully - parse events
print("=== $80:8CCE event dispatch table ===")
off = r(0x80, 0x8CCE)
p = off
while p < off + 192:  # Read ~12 entries
    if p >= len(rom): break
    # Each entry starts with: 2A (ROL A or INC $2A) or similar
    if rom[p] == 0x22:  # JSL directly
        target = rom[p+1] | (rom[p+2] << 8) | (rom[p+3] << 16)
        data = rom[p:p+8]
        print(f'  ROM 0x{p:06X}: JSL ${target:06X}')
        p += 4
    elif rom[p] == 0xE6 and rom[p+1] == 0x2A:  # INC $2A
        p += 2
        if rom[p] == 0x22:  # JSL
            target = rom[p+1] | (rom[p+2] << 8) | (rom[p+3] << 16)
            p += 4
            # Check for common return
            common = rom[p:p+5]
            if common[:3] == bytes([0x22, 0x7C, 0x89]) and common[3] == 0x80:
                rest = rom[p+4:p+8]
                print(f'  ROM 0x{p-6:06X}: INC $2A  JSL ${target:06X}  + JSL $80897C  rest={rest.hex()}')
                p += 5
            elif common[:2] == bytes([0x80, 0x43]) or rom[p] == 0x80:
                disp = rom[p+1] if rom[p+1] < 128 else rom[p+1] - 256
                print(f'  ROM 0x{p-6:06X}: INC $2A  JSL ${target:06X}  + BRA ${disp:+d}')
                p += 2
            else:
                print(f'  ROM 0x{p-6:06X}: INC $2A  JSL ${target:06X}  + {rom[p]:02X} {rom[p+1]:02X} {rom[p+2]:02X} {rom[p+3]:02X}')
                p += 1
        else:
            print(f'  ROM 0x{p-2:06X}: INC $2A  then {rom[p]:02X}')
            p += 1
    elif rom[p] == 0x80:  # BRA
        disp = rom[p+1] if rom[p+1] < 128 else rom[p+1] - 256
        rel = p + 2 + disp
        print(f'  ROM 0x{p:06X}: BRA to 0x{rel:06X}')
        break
    elif rom[p] == 0xA2:  # LDX #$xxxx
        p += 1
        # skip setup code
        dx = rom[p] | (rom[p+1] << 8)
        print(f'  ROM 0x{p-1:06X}: LDX #{dx:04X}  (setup)')
        p += 2
    elif rom[p] == 0x9A:  # TXS
        print(f'  ROM 0x{p:06X}: TXS')
        p += 1
    elif rom[p] == 0xCB:  # WAI
        print(f'  ROM 0x{p:06X}: WAI')
        p += 1
    elif rom[p] == 0x5C:  # JML
        target = rom[p+1] | (rom[p+2] << 8) | (rom[p+3] << 16)
        print(f'  ROM 0x{p:06X}: JML ${target:06X}')
        p += 4
    else:
        # Skip unknown
        print(f'  ROM 0x{p:06X}: ? {rom[p]:02X} {rom[p+1]:02X} {rom[p+2]:02X}')
        p += 1

# Check where main init goes after setup
# Look for JSL $80895F (load data) target
print("\n=== $80:895F (data load function) ===")
off = r(0x80, 0x895F)
for i in range(0, 64, 16):
    d = rom[off+i:off+i+16]
    print(f'  {off+i:06X}: {" ".join(f"{b:02X}" for b in d)}')

# $BB:8D91 (data load function called from main init)
print("\n=== $BB:8D91 (data loader) ===")
off = r(0xBB, 0x8D91)
for i in range(0, 64, 16):
    d = rom[off+i:off+i+16]
    print(f'  {off+i:06X}: {" ".join(f"{b:02X}" for b in d)}')

# What's at the end of bank $80? Check for game loop
print("\n=== Bank $80 near end ===")
for test_off in range(r(0x80, 0xFF00), r(0x80, 0x10000), 16):
    if test_off >= len(rom): break
    d = rom[test_off:test_off+16]
    # Check for common patterns
    pass

# Final check: where is the gap between end of init and dispatch table
# Main init ends at...(after last JSL $BB8D91 in $9200s)
# Dispatch table starts at $8CCE
# So dispatch is BEFORE main init in ROM order
print(f"\nROM layout bank $80:")
print(f"  Reset vector -> $83F7")
print(f"  Boot code: $83F7 - $85E0")
print(f"  Dispatch table: $8CCE - $8D87+")
print(f"  Sub $8EAE: $8EAE")
print(f"  SNES reg init $84F8 - $8563")
print(f"  VRAM clear $8591 - $85B4")
print(f"  WRAM clear $85B9 - $85CE")
print(f"  Main entry $90DA - $92xx+")
