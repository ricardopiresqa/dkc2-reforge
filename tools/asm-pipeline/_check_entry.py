import struct

data = open('roms/dkc2.sfc', 'rb').read()

# Entry at bank $C0, offset $8000 = ROM offset 0
# JMP at $C0801D -> $A8CF -> jumps to $C0:A8CF
# JSR at $C0A8CF -> $C0:A8A4 
# JSL at $C0A8A4 -> $B8:819F

# What follows JSL at $C0A8A7?
offset = 0xA8A7
print(f"JSL return at $C0:A8A7 (ROM offset 0x{offset:06X}):")
print(f"  Bytes: {' '.join(f'{data[offset+i]:02X}' for i in range(16))}")

# JSL encoding: $22 + 3-byte target (LoROM format)
# At $C0A8A4: check the JSL bytes
print(f"\nJSL instruction at $C0:A8A4: {' '.join(f'{data[0xA8A4+i]:02X}' for i in range(4))}")
jsl_target = struct.unpack('<I', data[0xA8A4:0xA8A8])[0] & 0xFFFFFF
print(f"  -> Decoded target: ${jsl_target:06X}")

# Check what comes after the JSR at $C0A8CF (after RTS from $A8A4)
print(f"\nAfter JSR $A8A4 at $C0:A8D2:")
print(f"  Bytes: {' '.join(f'{data[0xA8D2+i]:02X}' for i in range(16))}")

# Check what's in bank $C0 near $A8AB (next function target)
print(f"\nAt $C0:A8AB (next function):")
print(f"  Bytes: {' '.join(f'{data[0xA8AB+i]:02X}' for i in range(20))}")

# Check what the main loop might be
# Look for pattern: infinite loop or WAI/STP
print(f"\nSearching for common init patterns in bank $C0...")

# Check the SA-1 configuration registers initial values
print(f"\nSA-1 SNES register area $004200+ initialization:")
for addr in range(0x80, 0x100, 2):
    offset = 0x8000 + addr - 0x80  # At $C0:8080-$C0:8100 area
    if offset < len(data):
        pass  # Just scan for interesting values

# Check the vector area at end of bank $FF
vec_offset = 0x3FFFE0  # ROM offset for $FF:FFE0
print(f"\nVectors at ROM 0x{vec_offset:06X} ($FF:FFE0):")
for i in range(0, 32, 2):
        addr = struct.unpack('<H', data[vec_offset+i:vec_offset+i+2])[0]
        print(f"  ${(0xFF0000 | (vec_offset - 0x3F0000 + i)):06X}: ${addr:04X}")
