"""DKC2 ROM Map — Comprehensive ROM layout analysis.

Scans the DKC2 ROM (LoROM, 4MB) and produces a structured map:
  - SNES header parsing (vectors, checksum, maker code)
  - Bank-by-bank content analysis (code/data/PAC1/empty)
  - PAC1 header locations per bank
  - Cross-reference with disassembly exports

Outputs:
  - JSON: machine-readable ROM map (rom-map.json)
  - Markdown: human-readable ROM map (rom-map.md)

Usage:
    python rom_map.py --rom ../../roms/dkc2.sfc --output-dir .
    python rom_map.py --rom ../../roms/dkc2.sfc --json-only
"""

import argparse
import json
import os
import re
import struct
import sys


# ── SNES Addressing (LoROM) ──────────────────────────────────────────────

ROM_SIZE = 4 * 1024 * 1024


def snes_to_rom(snes_addr):
    """Convert SNES LoROM address to ROM offset (matches read_rom.py)."""
    bank = (snes_addr >> 16) & 0xFF
    offset = snes_addr & 0xFFFF

    if bank >= 0xC0:
        rom_off = (bank - 0xC0) * 0x10000 + offset
    elif 0x80 <= bank <= 0xBF:
        if offset >= 0x8000:
            rom_off = (bank - 0x80) * 0x10000 + (offset - 0x8000)
        else:
            rom_off = (bank - 0x80) * 0x10000 + offset
    elif 0x40 <= bank <= 0x7F:
        if offset >= 0x8000:
            rom_off = ((bank - 0x40) * 0x8000) + (offset - 0x8000) + 0x200000
        else:
            return None
    elif 0x00 <= bank <= 0x3F:
        if offset >= 0x8000:
            rom_off = (bank * 0x8000) + (offset - 0x8000)
        else:
            return None
    else:
        return None

    if rom_off < 0 or rom_off >= ROM_SIZE:
        return None
    return rom_off


def rom_to_snes(rom_off):
    """Convert ROM offset to SNES HiROM address.

    DKC2 is HiROM (type 0x31): ROM offset 0 maps to SNES bank $C0.
    For a 4MB ROM, banks 0-63 ($00-$3F chunk) map to SNES $C0-$FF.
    """
    if rom_off < 0 or rom_off >= ROM_SIZE:
        return None
    bank = (rom_off // 0x10000) + 0xC0
    offset = rom_off % 0x10000
    return (bank << 16) | offset


# ── Header Parsing ────────────────────────────────────────────────────────

HEADER_OFFSET = 0xFFC0
VECTOR_OFFSET_EMU = 0xFFE4
VECTOR_OFFSET_NATIVE = 0xFFF0
RESET_VECTOR_OFFSET = 0xFFFC


class RomHeader:
    """Parsed SNES ROM header fields (at ROM offset 0xFFC0)."""

    def __init__(self, data):
        self.raw = data

        off = HEADER_OFFSET
        self.maker_code = data[off:off + 2].decode('ascii', errors='replace')
        self.game_code = data[off + 2:off + 6].decode('ascii', errors='replace')
        self.title = data[off + 0x00:off + 0x15].rstrip(b'\x00').rstrip().decode('ascii', errors='replace')

        self.rom_type = data[off + 0x15]
        self.rom_speed_sub = data[off + 0x16]
        self.rom_size_exp = data[off + 0x17]
        self.sram_size_exp = data[off + 0x18]
        self.dest_code = data[off + 0x19]
        self.fixed_val = data[off + 0x1A]
        self.version = data[off + 0x1B]
        self.checksum_complement = struct.unpack_from('<H', data, off + 0x1C)[0]
        self.checksum = struct.unpack_from('<H', data, off + 0x1E)[0]

        self.rom_size = 1 << (self.rom_size_exp + 10) if 0 <= self.rom_size_exp <= 12 else 0
        self.sram_size = (1 << (self.sram_size_exp + 10)) if 1 <= self.sram_size_exp <= 7 else 0
        self.checksum_valid = (self.checksum ^ self.checksum_complement) == 0xFFFF

        self.vectors = self._parse_vectors(data)

    @staticmethod
    def _parse_vectors(data):
        """Parse interrupt vectors.

        SNES emulation-mode vectors at $FFE4: COP, BRK, ABORT, NMI, RESET, IRQ.
        SNES native-mode vectors at $FFF0: COP, BRK, ABORT, NMI, RESET, IRQ.
        RESET at $00:FFFC overrides emulation RESET.

        All vectors are 16-bit addresses. Bank is implicit:
          - emulation: bank $00
          - native: bank $80 (for LoROM) or as set by the CPU
        """
        vec_names = ['cop', 'brk', 'abort', 'nmi', 'reset', 'irq']
        vectors = {}

        for i, name in enumerate(vec_names):
            addr = struct.unpack_from('<H', data, VECTOR_OFFSET_EMU + i * 2)[0]
            vectors[f'emu_{name}'] = addr

        for i, name in enumerate(vec_names):
            addr = struct.unpack_from('<H', data, VECTOR_OFFSET_NATIVE + i * 2)[0]
            vectors[f'native_{name}'] = addr

        reset = struct.unpack_from('<H', data, RESET_VECTOR_OFFSET)[0]
        vectors['reset'] = reset

        return vectors

    def to_dict(self):
        return {
            'title': self.title,
            'maker_code': self.maker_code,
            'game_code': self.game_code,
            'rom_type': f'0x{self.rom_type:02X}',
            'rom_speed_sub': f'0x{self.rom_speed_sub:02X}',
            'rom_size_bytes': self.rom_size,
            'rom_size_mb': self.rom_size // (1024 * 1024),
            'sram_size_bytes': self.sram_size,
            'version': self.version,
            'checksum': f'0x{self.checksum:04X}',
            'checksum_complement': f'0x{self.checksum_complement:04X}',
            'checksum_valid': self.checksum_valid,
            'vectors': {k: f'0x{v:04X}' for k, v in self.vectors.items()},
        }


# ── PAC1 Header Scanning ─────────────────────────────────────────────────

def header_score(data, offset):
    """Score a potential PAC1 header at given ROM offset.

    A PAC1 header is 39 bytes: byte 0 = 0x00, then 16 page-in pointers
    (16-bit little-endian) where the high byte should be zero.
    """
    if offset + 39 > len(data):
        return 0
    h = data[offset:offset + 39]
    if h[0] != 0x00:
        return 0
    valid = 0
    all_zero = 0
    sequential = 0
    prev = None
    for i in range(16):
        w = struct.unpack_from('<H', h, 7 + i * 2)[0]
        if (w >> 8) == 0:
            valid += 1
        if w == 0:
            all_zero += 1
        if prev is not None and w == prev + 1:
            sequential += 1
        prev = w
    if all_zero >= 14 or sequential >= 10:
        return 0
    return valid if valid >= 12 else 0


def scan_pac1_bank(data, bank_num, min_score=12):
    """Scan a single ROM bank (64KB chunk) for PAC1 headers.

    Uses stride=1 for data-dense upper banks (ROM offset >= 0x200000)
    where large sprite archives may reside at any alignment.
    Uses stride=39 for lower banks (code) for speed.
    """
    bank_start = bank_num * 0x10000
    bank_end = min(bank_start + 0x10000, len(data))
    results = []
    step = 1 if bank_start >= 0x200000 else 39
    for off in range(bank_start, bank_end, step):
        if data[off] != 0x00:
            if step == 1:
                continue
            else:
                off += 38
                continue
        score = header_score(data, off)
        if score >= min_score:
            snes = rom_to_snes(off)
            results.append({
                'rom_offset': off,
                'snes_addr': f'0x{snes:06X}' if snes else None,
                'score': score,
            })
    return results


# ── Bank Classification ───────────────────────────────────────────────────

def classify_bank(data, bank_num):
    """Classify a ROM bank's content: code, data, empty, or unmapped."""
    bank_start = bank_num * 0x10000
    bank_end = min(bank_start + 0x10000, len(data))
    chunk = data[bank_start:bank_end]

    if len(chunk) == 0:
        return 'unmapped'

    if len(set(chunk)) <= 2:
        return 'empty'

    return 'data'


def count_unique_bytes(chunk):
    """Number of distinct byte values in a chunk."""
    return len(set(chunk))


# ── Disassembly Cross-Reference ──────────────────────────────────────────

def load_disassembly_banks(disasm_dir):
    """Load labels/functions from Mesen2 disassembly export."""
    labels = {}
    if not os.path.isdir(disasm_dir):
        return labels

    label_file = os.path.join(disasm_dir, 'labels.asm')
    func_file = os.path.join(disasm_dir, 'functions.txt')

    if os.path.exists(label_file):
        with open(label_file, 'r') as f:
            current_addr = None
            for line in f:
                m = re.match(r'^\s*org\s+\$([0-9A-Fa-f]+)', line, re.I)
                if m:
                    current_addr = int(m.group(1), 16)
                    continue
                m = re.match(r'^(\w+):', line)
                if m and current_addr is not None:
                    labels[m.group(1)] = current_addr

    if os.path.exists(func_file):
        with open(func_file, 'r') as f:
            for line in f:
                m = re.match(r'^\s*\$([0-9A-Fa-f]{6}):\s+(\w+)', line)
                if m:
                    labels[m.group(2)] = int(m.group(1), 16)

    return labels


# ── ROM Map Generation ───────────────────────────────────────────────────

class RomMap:
    """Complete ROM map for DKC2."""

    def __init__(self, rom_path, disasm_dir=None):
        with open(rom_path, 'rb') as f:
            self.data = f.read()

        self.rom_path = rom_path
        self.size = len(self.data)
        self.header = RomHeader(self.data)
        self.labels = load_disassembly_banks(disasm_dir) if disasm_dir else {}
        self.banks = []
        self.pac1_headers = []
        self._analyze()

    def _analyze(self):
        """Run full ROM analysis across all 128 ROM banks."""
        for b in range(128):
            bank_start = b * 0x10000
            bank_end = min(bank_start + 0x10000, self.size)
            chunk_size = bank_end - bank_start

            bank_type = classify_bank(self.data, b)
            unique = count_unique_bytes(self.data[bank_start:bank_end]) if chunk_size > 0 else 0

            pac1 = scan_pac1_bank(self.data, b)
            self.pac1_headers.extend(pac1)

            snes_bank = 0xC0 + b
            bank_info = {
                'bank': b,
                'snes_bank': f'${snes_bank:02X}',
                'rom_start': bank_start,
                'rom_end': bank_end - 1,
                'size': chunk_size,
                'type': bank_type,
                'unique_bytes': unique,
                'pac1_count': len(pac1),
                'pac1_offsets': [p['rom_offset'] for p in pac1],
            }

            if self.labels and b < 64:
                syms = self._get_bank_symbols(b)
                bank_info['symbols'] = len(syms)
                if syms:
                    bank_info['type'] = 'code'

            self.banks.append(bank_info)

    def _get_bank_symbols(self, bank_num):
        """Get labels that fall within a given SNES bank."""
        bank_start = (0xC0 + bank_num) << 16 if bank_num < 64 else 0
        bank_end = bank_start + 0x10000
        return {name: addr for name, addr in self.labels.items()
                if bank_start <= addr < bank_end}

    def to_dict(self):
        return {
            'rom': os.path.basename(self.rom_path),
            'size_bytes': self.size,
            'size_mb': self.size / (1024 * 1024),
            'header': self.header.to_dict(),
            'banks': self.banks,
            'pac1_total': len(self.pac1_headers),
            'pac1_headers': self.pac1_headers,
        }

    def to_markdown(self):
        """Generate human-readable ROM map as Markdown."""
        h = self.header
        lines = [
            f"# ROM Map — DKC2 ({os.path.basename(self.rom_path)})",
            "",
            "## Header",
            "",
            f"| Field | Value |",
            f"|-------|-------|",
            f"| Title | {h.title} |",
            f"| Maker Code | {h.maker_code} |",
            f"| Game Code | {h.game_code} |",
            f"| ROM Type | 0x{h.rom_type:02X} |",
            f"| ROM Size | {h.rom_size // (1024*1024)}MB |",
            f"| SRAM Size | {h.sram_size}B |",
            f"| Version | {h.version} |",
            f"| Checksum | 0x{h.checksum:04X} |",
            f"| Checksum Complement | 0x{h.checksum_complement:04X} |",
            f"| Checksum Valid | {h.checksum_valid} |",
            "",
            "### Vectors (16-bit, bank $00 emulation / $80 native)",
            "",
            "| Interrupt | Emulation | Native |",
            "|-----------|-----------|--------|",
        ]
        for name in ['cop', 'brk', 'abort', 'nmi', 'reset', 'irq']:
            emu = h.vectors.get(f'emu_{name}', 0)
            nat = h.vectors.get(f'native_{name}', 0)
            lines.append(f"| {name.upper()} | `0x{emu:04X}` | `0x{nat:04X}` |")

        lines += [
            "",
            f"| **RESET (from $00:FFFC)** | `0x{h.vectors['reset']:04X}` |",
            "",
            "## Bank Summary",
            "",
            f"Total banks: {len(self.banks)} "
            f"(${0x80:02X}-${0x80 + len(self.banks) - 1:02X})",
            f"PAC1 headers found: {len(self.pac1_headers)}",
            "",
            f"### Bank Map ({sum(1 for b in self.banks if b['type'] != 'unmapped')} mapped, "
            f"{sum(1 for b in self.banks if b['type'] == 'unmapped')} unmapped banks hidden)",
            "",
            "| Bank | SNES | Offset | Type | Unique | PAC1 | Syms |",
            "|------|------|--------|------|--------|------|------|",
        ]
        for b in self.banks:
            if b['type'] == 'unmapped':
                continue
            lines.append(
                f"| ${b['bank']:02X} | {b['snes_bank']} | "
                f"0x{b['rom_start']:06X}-0x{b['rom_end']:06X} | "
                f"{b['type']} | {b['unique_bytes']} | "
                f"{b['pac1_count']} | {b.get('symbols', '-')} |"
            )

        lines += [
            "",
            "### PAC1 Headers",
            "",
        ]
        if self.pac1_headers:
            lines += [
                "| ROM Offset | SNES Address | Score |",
                "|------------|--------------|-------|",
            ]
            for p in self.pac1_headers:
                lines.append(f"| 0x{p['rom_offset']:06X} | {p['snes_addr']} | {p['score']} |")

        lines.append("")
        return '\n'.join(lines)


# ── CLI ───────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description='DKC2 ROM Map — comprehensive ROM layout analysis')
    parser.add_argument('--rom', required=True, help='Path to DKC2 ROM')
    parser.add_argument('--output-dir', default='.',
                        help='Output directory for reports')
    parser.add_argument('--disasm-dir',
                        default='../disassembly/export',
                        help='Disassembly export directory')
    parser.add_argument('--json-only', action='store_true',
                        help='Only output JSON')
    parser.add_argument('--md-only', action='store_true',
                        help='Only output Markdown')

    args = parser.parse_args()

    if not os.path.exists(args.rom):
        print(f"ERROR: ROM not found: {args.rom}")
        sys.exit(1)

    script_dir = os.path.dirname(os.path.abspath(__file__))
    disasm_dir = os.path.join(script_dir, args.disasm_dir) if args.disasm_dir else None
    if disasm_dir and not os.path.isdir(disasm_dir):
        disasm_dir = None
        print(f"Note: disassembly dir not found, skipping code labels")

    print(f"Analyzing ROM: {args.rom} ({os.path.getsize(args.rom)} bytes)...")
    rom_map = RomMap(args.rom, disasm_dir=disasm_dir)

    output_dir = args.output_dir
    os.makedirs(output_dir, exist_ok=True)

    if not args.md_only:
        json_path = os.path.join(output_dir, 'rom-map.json')
        with open(json_path, 'w') as f:
            json.dump(rom_map.to_dict(), f, indent=2)
        print(f"JSON map: {json_path}")

    if not args.json_only:
        md_path = os.path.join(output_dir, 'rom-map.md')
        with open(md_path, 'w') as f:
            f.write(rom_map.to_markdown())
        print(f"Markdown map: {md_path}")

    h = rom_map.header
    print(f"\nSummary:")
    print(f"  ROM size: {rom_map.size / (1024*1024):.1f}MB")
    code_banks = sum(1 for b in rom_map.banks if b['type'] == 'code')
    data_banks = sum(1 for b in rom_map.banks if b['type'] == 'data')
    empty_banks = sum(1 for b in rom_map.banks if b['type'] == 'empty')
    unmapped_banks = sum(1 for b in rom_map.banks if b['type'] == 'unmapped')
    print(f"  Banks: {len(rom_map.banks)} (code={code_banks}, data={data_banks}, empty={empty_banks}, unmapped={unmapped_banks})")
    print(f"  PAC1 headers: {len(rom_map.pac1_headers)}")
    print(f"  Game: {h.title} ({h.game_code})")
    print(f"  Checksum valid: {h.checksum_valid}")
    print(f"  Vectors: NMI=0x{h.vectors['emu_nmi']:04X}, "
          f"RESET=0x{h.vectors['reset']:04X}, "
          f"IRQ=0x{h.vectors['emu_irq']:04X}")


if __name__ == '__main__':
    main()
