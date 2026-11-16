"""
DKC2 Reforge — Memory Map Manager
Gerencia o schema padronizado de memory map (docs/memory-map.md como JSON).
Permite adicionar, buscar, validar e exportar entradas.
"""

import json
import sys
from pathlib import Path


SCHEMA = {
    "address": "uint24",
    "name": "string",
    "type": "enum(byte,word,dword,pointer,array,code,data)",
    "system": "enum(main,cpu,sa1,smp,dma,ppu,apu)",
    "flags": {
        "M": "bool (merchant/memory)",
        "X": "bool (executable/code)",
        "D": "bool (data only)",
        "W": "bool (write-only)",
        "R": "bool (read-only)",
        "V": "bool (verified/emulator-tested)"
    },
    "references": ["string (enderecos que referenciam esta entrada)"],
    "emu_test": "string? (metodo de verificacao no emulador)",
    "description": "string?"
}


def load_mmap(path="docs/memory-map.md"):
    """Memory map esta em markdown com blocos JSON incorporados"""
    with open(path, "r", encoding="utf-8") as f:
        text = f.read()
    # Extrai blocos ```json ... ``` 
    entries = []
    in_json = False
    buf = ""
    for line in text.split("\n"):
        if line.strip().startswith("```json"):
            in_json = True
            buf = ""
        elif line.strip().startswith("```"):
            if in_json and buf.strip():
                data = json.loads(buf)
                if isinstance(data, list):
                    entries.extend(data)
                else:
                    entries.append(data)
                in_json = False
        elif in_json:
            buf += line + "\n"
    return entries


def search(mmap, addr=None, name=None, system=None):
    results = []
    for e in mmap:
        if addr and e.get("address") == addr:
            results.append(e)
        if name and name.lower() in e.get("name", "").lower():
            results.append(e)
        if system and e.get("system") == system:
            results.append(e)
    return results


def add_entry(mmap, entry):
    """Add and validate entry before saving"""
    errors = []
    if "address" not in entry:
        errors.append("address required")
    if "name" not in entry:
        errors.append("name required")
    # Check for duplicate address
    for e in mmap:
        if e.get("address") == entry.get("address"):
            errors.append(f"duplicate address ${entry['address']:06X}")
    if errors:
        return errors
    mmap.append(entry)
    return []


def export_json(mmap, path="memory-map-export.json"):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(mmap, f, indent=2)
    print(f"Exported {len(mmap)} entries to {path}")


def interactive():
    mmap = load_mmap()
    print(f"Memory map loaded: {len(mmap)} entries")
    print("Commands: search <addr>, add, export, quit")
    while True:
        cmd = input("> ").strip().split()
        if not cmd:
            continue
        if cmd[0] == "quit":
            break
        elif cmd[0] == "search" and len(cmd) > 1:
            addr = int(cmd[1], 16) if cmd[1].startswith("$") or cmd[1].startswith("0x") else int(cmd[1])
            results = search(mmap, addr=addr)
            for r in results:
                print(json.dumps(r, indent=2))
        elif cmd[0] == "export":
            export_json(mmap)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--interactive":
        interactive()
    else:
        mmap = load_mmap()
        print(f"Memory map loaded: {len(mmap)} entries from docs/memory-map.md")
        for e in mmap:
            addr = int(e['address'], 16) if isinstance(e['address'], str) else e['address']
            print(f"  ${addr:06X}: {e['name']} ({e['type']}) [{e.get('system','?')}]")
