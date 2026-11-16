"""
Trace dispatch functions with more verbose output.
"""
import sys
sys.path.insert(0, "tools/asm-pipeline")
from disasm65816 import Dis65816

data = open('roms/dkc2.sfc', 'rb').read()
dis = Dis65816(data)

def trace(addr, label):
    print(f"\n=== {label} (${addr:06X}) ===")
    a = addr
    for _ in range(50):
        if a in dis.visited:
            print(f"  ${a:06X}: [already visited, stopping]")
            break
        next_a, text = dis.disasm_at(a)
        print(f"  ${a:06X}: {text}")
        dis.visited.add(a)
        if next_a is None or next_a <= a:
            break
        a = next_a

trace(0xC0885F, "state_9")
trace(0xC0888B, "state_A")
trace(0xC088B7, "state_B")
trace(0xC088E3, "state_C")
