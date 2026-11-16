"""
Trace the 4 game mode dispatch functions:
  state == 9 -> $C0:885F
  state == A -> $C0:888B
  state == B -> $C0:88B7
  state == C -> $C0:88E3
"""
import sys
sys.path.insert(0, "tools/asm-pipeline")
from disasm65816 import Dis65816

data = open('roms/dkc2.sfc', 'rb').read()
dis = Dis65816(data)

dispatch_addrs = [0xC0885F, 0xC0888B, 0xC088B7, 0xC088E3]
labels = {0xC0885F: "dispatch_state_9", 0xC0888B: "dispatch_state_A",
          0xC088B7: "dispatch_state_B", 0xC088E3: "dispatch_state_C"}

for addr in dispatch_addrs:
    print(f"\n{'='*60}")
    print(f"=== Follow dispatch ${addr:06X} ({labels[addr]}) ===")
    print(f"{'='*60}")
    dis.follow_code(addr, source='DISPATCH')

print(f"\n{'='*60}")
print("Summary")
print(f"{'='*60}")
print(f"Total visited: {len(dis.visited)}")
print(f"Functions found:")
for addr, name in sorted(dis.functions.items()):
    print(f"  ${addr:06X}: {name}")
