"""Search ROM for SA-1 character DMA setup sequences.

SA-1 character DMA registers (write by SNES CPU):
  $2230 - DMACR (control, write triggers DMA)
  $2232 - SA (source address low)  — 16-bit
  $2234 - SA (source address bank) — 8-bit
  $2235 - SDA (size low) — 16-bit (or $SDR low)
  $2236 - SDA (size high)
"""

import struct, sys

def search_pattern(data, pattern, name):
    """Search for byte pattern and return all offsets."""
    results = []
    idx = 0
    while True:
        idx = data.find(pattern, idx)
        if idx == -1:
            break
        results.append(idx)
        idx += 1
    return results

rom_path = '../../roms/dkc2.sfc'
with open(rom_path, 'rb') as f:
    rom = f.read()

# 65816 opcodes for absolute writes to $223X
# 8D = sta absolute, 9C = stz absolute (16-bit acc), 9D = sta absolute,X
targets = {
    '$2230 (DMACR)': b'\x8d\x30\x22',
    '$2230 stz':    b'\x9c\x30\x22',  # stz $2230 (16-bit zero)
    '$2232 (SA lo)': b'\x8d\x32\x22',
    '$2234 (SA bank)': b'\x8d\x34\x22',
    '$2235 (size lo)': b'\x8d\x35\x22',
}

for name, pat in targets.items():
    offsets = search_pattern(rom, pat, name)
    print(f'{name}: {len(offsets)} hits')
    for off in offsets[:10]:
        bank = off // 0x10000
        snes_bank = 0xC0 + bank
        snes_off = off % 0x10000
        print(f'  0x{off:08X} (${snes_bank:02X}:{snes_off:04X})')

print()

# Now find sequences of consecutive $223X writes (SA-1 DMA setup)
# A setup sequence would be: sta $2230, sta $2232, sta $2234, sta $2235
# Often with LDA #value before each STA

print('=== SA-1 DMA setup sequences (clusters of 2230-2236 writes within 20 bytes) ===')
all_223x = []
for reg_name, pat in targets.items():
    off = 0
    while True:
        off = rom.find(pat, off)
        if off == -1:
            break
        all_223x.append(off)
        off += 1

all_223x.sort()
print(f'Total $223X writes: {len(all_223x)}')

# Cluster: group writes within 20 bytes
i = 0
while i < len(all_223x):
    cluster_start = all_223x[i]
    cluster = [all_223x[i]]
    j = i + 1
    while j < len(all_223x) and all_223x[j] - cluster[-1] <= 20:
        cluster.append(all_223x[j])
        j += 1
    if len(cluster) >= 2:
        bank = cluster[0] // 0x10000
        snes_bank = 0xC0 + bank
        snes_off = cluster[0] % 0x10000
        # Show context bytes around the cluster
        start_ctx = max(0, cluster[0] - 16)
        end_ctx = min(len(rom), cluster[-1] + 8)
        ctx = rom[start_ctx:end_ctx]
        print(f'  Cluster at 0x{cluster[0]:08X} (${snes_bank:02X}:{snes_off:04X}) [{len(cluster)} writes]:')
        for c in cluster:
            print(f'    0x{c:08X}')
        # Try to decode the source address: look for LDA immediate (#) before $2232
        # Pattern: LDA #$XXXX (A9 XX XX) followed by STA $2232 (8D 32 22)
        for ci, c in enumerate(cluster):
            # Check if STA $2232 is preceded by LDA # within 5 bytes
            pre = rom[c-5:c+3]
            print(f'    ctx: {" ".join(f"{b:02X}" for b in pre)}')
        print()
    i = j
