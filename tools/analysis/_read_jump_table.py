"""Read the jump table at $BB:8000-807F."""
import struct

rom = open('roms/dkc2.sfc','rb').read()

# Jump table at $BB:8000
bank = 0xBB
addr = 0x8000
phys = ((bank & 0x3F) << 16) | (addr & 0xFFFF)
print(f'Physical offset for $BB:8000 = 0x{phys:06X}')
print()

# Read the jump table: entries 0-15 (primary) at $BB:8001 + N*4
print('=== Primary dispatch table ($BB:8001 + N*4) ===')
for n in range(16):
    off = phys + 1 + n*4
    if off + 3 >= len(rom):
        break
    jmp_addr = rom[off+1] | (rom[off+2] << 8)
    print(f'  Entry {n:2d}: JMP ${jmp_addr:04X}')

print()
print('=== Secondary dispatch table ($BB:8040 + N*4) ===')
for n in range(16):
    off = phys + 0x40 + n*4
    if off + 3 >= len(rom):
        break
    jmp_addr = rom[off+1] | (rom[off+2] << 8)
    print(f'  Entry {n:2d}: JMP ${jmp_addr:04X}')
