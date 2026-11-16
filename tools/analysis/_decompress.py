"""
DKC2 Compressed Data Decoder
=============================
Reverses the decompression algorithm at $BB:8D91.

Calling convention (main entry $8D91):
  A = dest pointer (WRAM bank $7E)
  X = source pointer (WRAM bank $7F)
  Y = flags (stored in $36, usage unclear)

Compressed data layout:
  Offset 1:   byte -> header param 1 ($52)
  Offset 2:   byte -> header param 2 ($53)
  Offset 3:   byte -> header param 3 ($56)
  Offset 4:   byte -> header param 4 ($57)
  Offset 5-6: 16-bit word -> header param ($54)
  Offset 7-38: incidental data pool (accessed via opcode F)
  Offset 39:  format-select byte ($46) [first opcode = high nibble]
  Offset 40+: compressed opcode stream (format bytes + data)

Algorithm: table-driven dispatch on 4-bit opcode.
  High nibble of each format byte -> primary operation (16 entries)
  Low nibble of each format byte -> secondary operation or parameter

States:
  SET1 = primary dispatch (read format byte, dispatch on high nibble)
  SET2 = secondary dispatch via $42 low nibble (reuses stream byte)
  SET2_WIDE = secondary dispatch via $46 low nibble (current format byte)

WRAM context tables (caller-initialized before calling decompress):
  $7E:2000-$20FF (table1 / index via [$42]): count/offset lookup
  $7E:2100-$21FF (table2 / index via [$46]): OR-mask lookup
  When tables are not provided, defaults approximate with LO/HI:
    LO[b] = b >> 4  (high nibble -> count/offset)
    HI[b] = (b & 0x0F) << 4  (low nibble -> OR-mask)
"""

from __future__ import annotations

import struct
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

# LO/HI look-up tables (default approximation of WRAM $7E:2000/$7E:2100)
# LO[b] = b >> 4 (high nibble -> count/offset)
# HI[b] = (b & 0x0F) << 4 (low nibble shifted to high -> OR-mask)
LO = [b >> 4 for b in range(256)]
HI = [(b & 0x0F) << 4 for b in range(256)]

SET1 = 1
SET2 = 2
SET2_WIDE = 3


@dataclass
class DecompressContext:
    """Replicates DP variables of the SNES decompressor."""

    src_data: bytes
    src_offset: int

    param52: int = 0
    param53: int = 0
    param56: int = 0
    param57: int = 0
    param54: int = 0

    dest: List[int] = field(default_factory=list)
    dest_start: int = 0

    tmp46: int = 0
    tmp42: int = 0
    state: int = SET1

    table1: Optional[List[int]] = None
    table2: Optional[List[int]] = None

    def read_byte(self) -> int:
        b = self.src_data[self.src_offset]
        self.src_offset += 1
        return b

    def read_word(self) -> int:
        w = struct.unpack_from("<H", self.src_data, self.src_offset)[0]
        self.src_offset += 2
        return w

    def write_byte(self, b: int):
        self.dest.append(b & 0xFF)

    def write_word(self, w: int):
        self.dest.append(w & 0xFF)
        self.dest.append((w >> 8) & 0xFF)

    @property
    def dest_pos(self) -> int:
        return len(self.dest) - self.dest_start

    @property
    def dest_abs(self) -> int:
        return len(self.dest)

    def get_table1(self, idx: int) -> int:
        if self.table1 is not None:
            return self.table1[idx] & 0xFF
        return LO[idx]

    def get_table2(self, idx: int) -> int:
        if self.table2 is not None:
            return self.table2[idx] & 0xFF
        return HI[idx]


def decompress(data: bytes, table1: Optional[List[int]] = None,
               table2: Optional[List[int]] = None) -> bytes:
    ctx = DecompressContext(src_data=data, src_offset=1,
                            table1=table1, table2=table2)

    ctx.param52 = ctx.read_byte()
    ctx.param53 = ctx.read_byte()
    ctx.param56 = ctx.read_byte()
    ctx.param57 = ctx.read_byte()
    ctx.param54 = ctx.read_word()

    ctx.src_offset = 0x27

    try:
        while True:
            if ctx.state == SET1:
                if not step_set1(ctx):
                    break
            elif ctx.state == SET2:
                step_set2(ctx)
            elif ctx.state == SET2_WIDE:
                step_set2_wide(ctx)
            else:
                break
    except (ValueError, IndexError, struct.error):
        pass

    return bytes(ctx.dest)


# ============================================================
# State 1: Primary Dispatch (high nibble of format byte)
# ============================================================

def step_set1(ctx: DecompressContext) -> bool:
    """Execute one cycle of SET1 (primary dispatch). Returns False to terminate."""
    fmt = ctx.read_byte()
    ctx.tmp46 = fmt
    cmd = fmt >> 4
    lo = fmt & 0x0F

    if cmd == 0:
        if lo == 0:
            return False
        for _ in range(lo):
            ctx.write_byte(ctx.read_byte())
        ctx.state = SET1

    elif cmd == 1:
        hi_val = ctx.get_table2(fmt)
        nxt = ctx.read_byte()
        ctx.write_byte(hi_val | ctx.get_table1(nxt))
        ctx.tmp42 = nxt
        ctx.state = SET2

    elif cmd == 2:
        hi_val = ctx.get_table2(fmt)
        nxt1 = ctx.read_byte()
        ctx.write_byte(hi_val | ctx.get_table1(nxt1))
        hi_val2 = ctx.get_table2(nxt1)
        nxt2 = ctx.read_byte()
        ctx.write_byte(hi_val2 | ctx.get_table1(nxt2))
        ctx.tmp42 = nxt2
        ctx.state = SET2

    elif cmd == 3:
        count = lo + 3
        fill = ctx.read_byte()
        for _ in range(count):
            ctx.write_byte(fill)
        ctx.state = SET1

    elif cmd == 4:
        count = lo + 3
        for _ in range(count):
            ctx.write_byte(ctx.param52)
        ctx.state = SET1

    elif cmd == 5:
        count = lo + 3
        for _ in range(count):
            ctx.write_byte(ctx.param53)
        ctx.state = SET1

    elif cmd == 6:
        ctx.write_word(ctx.param54)
        ctx.state = SET2_WIDE

    elif cmd == 7:
        ctx.write_byte(ctx.param56)
        ctx.state = SET2_WIDE

    elif cmd == 8:
        ctx.write_byte(ctx.param57)
        ctx.state = SET2_WIDE

    elif cmd == 9:
        off = lo + 2
        if len(ctx.dest) >= off:
            b1 = ctx.dest[-off]
            b2 = ctx.dest[-off + 1] if off > 1 else 0
            ctx.write_byte(b1)
            ctx.write_byte(b2)
        ctx.state = SET1

    elif cmd == 10:
        count = lo + 3
        extra = ctx.read_byte()
        off = count + extra
        src_pos = len(ctx.dest) - off
        if src_pos < 0:
            src_pos = 0
        for _ in range(count):
            ctx.write_byte(ctx.dest[src_pos])
            src_pos += 1
        ctx.state = SET1

    elif cmd == 11:
        count = lo + 3
        b1 = ctx.read_byte()
        b2 = ctx.read_byte()
        ctx.tmp46 = b2
        off = ((b1 << 8) | b2) >> 4
        off += 0x103
        src_pos = len(ctx.dest) - off
        if src_pos < 0:
            src_pos = 0
        for _ in range(count):
            ctx.write_byte(ctx.dest[src_pos])
            src_pos += 1
        ctx.state = SET2_WIDE

    elif cmd == 12:
        count = lo + 3
        raw = ctx.read_word()
        off = ((raw >> 8) | ((raw & 0xFF) << 8))
        src_pos = len(ctx.dest) - off
        if src_pos < 0:
            src_pos = 0
        for _ in range(count):
            ctx.write_byte(ctx.dest[src_pos])
            src_pos += 1
        ctx.state = SET1

    elif cmd == 13:
        if ctx.dest:
            ctx.write_byte(ctx.dest[-1])
        ctx.state = SET2_WIDE

    elif cmd == 14:
        if len(ctx.dest) >= 2:
            b1 = ctx.dest[-2]
            b2 = ctx.dest[-1]
            ctx.write_byte(b1)
            ctx.write_byte(b2)
        ctx.state = SET2_WIDE

    elif cmd == 15:
        off = (lo * 2) + 7
        pos = ctx.src_offset + off - 1
        ctx.write_byte(ctx.src_data[pos] if pos < len(ctx.src_data) else 0)
        if pos + 1 < len(ctx.src_data):
            ctx.write_byte(ctx.src_data[pos + 1])
        else:
            ctx.write_byte(0)
        ctx.state = SET1

    return True


# ============================================================
# State 2: Secondary via $42 low nibble
# ============================================================

def step_set2(ctx: DecompressContext):
    b = ctx.tmp42
    ctx.tmp46 = b
    cmd = b & 0x0F
    dispatch_sec(ctx, cmd, set2=True)


# ============================================================
# State 2W: Secondary via $46 low nibble
# ============================================================

def step_set2_wide(ctx: DecompressContext):
    cmd = ctx.tmp46 & 0x0F
    dispatch_sec(ctx, cmd, set2=False)


# ============================================================
# Secondary dispatch (shared between SET2 and SET2_WIDE)
# ============================================================

def dispatch_sec(ctx: DecompressContext, cmd: int, set2: bool):
    if cmd == 0:
        sec_indirect_literal(ctx)
    elif cmd == 1:
        ctx.write_byte(ctx.read_byte())
        ctx.state = SET1
    elif cmd == 2:
        ctx.write_byte(ctx.read_byte())
        ctx.write_byte(ctx.read_byte())
        ctx.state = SET1
    elif cmd == 3:
        sec_or_repeat_indirect(ctx)
    elif cmd == 4:
        sec_fill_param_indirect(ctx, value=ctx.param52)
    elif cmd == 5:
        sec_fill_param_indirect(ctx, value=ctx.param53)
    elif cmd == 6:
        ctx.write_word(ctx.param54)
        ctx.state = SET1
    elif cmd == 7:
        ctx.write_byte(ctx.param56)
        ctx.state = SET1
    elif cmd == 8:
        ctx.write_byte(ctx.param57)
        ctx.state = SET1
    elif cmd == 9:
        sec_backref_short_extra(ctx)
    elif cmd == 10:
        sec_backref_two_extra(ctx)
    elif cmd == 11:
        sec_backref_var(ctx)
    elif cmd == 12:
        sec_backref_16bit_shifted(ctx)
    elif cmd == 13:
        if ctx.dest:
            ctx.write_byte(ctx.dest[-1])
        ctx.state = SET1
    elif cmd == 14:
        if len(ctx.dest) >= 2:
            b1 = ctx.dest[-2]
            b2 = ctx.dest[-1]
            ctx.write_byte(b1)
            ctx.write_byte(b2)
        ctx.state = SET1
    elif cmd == 15:
        sec_header_indirect_secondary(ctx)


# ============================================================
# Secondary Op Handlers
# ============================================================

def sec_indirect_literal(ctx: DecompressContext):
    """Sec 0: Read byte -> count from table. If 0 -> end. OR-copy loop."""
    nxt = ctx.read_byte()
    ctx.tmp42 = nxt
    ctx.tmp46 = nxt
    count = ctx.get_table1(nxt)
    if count == 0:
        raise ValueError("secondary indirect literal count=0 -> end")
    for _ in range(count):
        b1 = ctx.read_byte()
        ctx.tmp42 = b1
        b2 = ctx.read_byte()
        ctx.tmp42 = b2
        ctx.write_byte(ctx.get_table2(nxt) | ctx.get_table1(b2))
    ctx.state = SET2_WIDE


def sec_or_repeat_indirect(ctx: DecompressContext):
    """Sec 3: OR-based repeat from indirect. Always goes to SET2."""
    nxt = ctx.read_byte()
    ctx.tmp42 = nxt
    ctx.tmp46 = nxt
    count = ctx.get_table1(nxt) + 3
    fill_hi = ctx.get_table2(nxt)
    nxt2 = ctx.read_byte()
    ctx.tmp42 = nxt2
    fill = fill_hi | ctx.get_table1(nxt2)
    for _ in range(count):
        ctx.write_byte(fill)
    ctx.state = SET2


def sec_fill_param_indirect(ctx: DecompressContext, value: int):
    """Sec 4/5: Read byte -> count from table, fill with param."""
    nxt = ctx.read_byte()
    ctx.tmp42 = nxt
    count = ctx.get_table1(nxt) + 3
    for _ in range(count):
        ctx.write_byte(value)
    ctx.state = SET2


def sec_backref_short_extra(ctx: DecompressContext):
    """Sec 9: Read byte -> table1 -> offset, copy 2 bytes back. Always goes to SET2."""
    nxt = ctx.read_byte()
    ctx.tmp42 = nxt
    off = ctx.get_table1(nxt) + 2
    if len(ctx.dest) >= off:
        b1 = ctx.dest[-off]
        b2 = ctx.dest[-off + 1] if off > 1 else 0
        ctx.write_byte(b1)
        ctx.write_byte(b2)
    ctx.state = SET2


def sec_backref_two_extra(ctx: DecompressContext):
    """Sec 10: Read byte -> table1 (count) + table2 (OR-base). Second byte -> table2 (OR-mask)."""
    nxt = ctx.read_byte()
    ctx.tmp42 = nxt
    ctx.tmp46 = nxt
    count = ctx.get_table1(nxt) + 3
    or_base = ctx.get_table2(nxt)
    nxt2 = ctx.read_byte()
    ctx.tmp42 = nxt2
    off = or_base | ctx.get_table1(nxt2)
    src_pos = len(ctx.dest) - count - off
    if src_pos < 0:
        src_pos = 0
    for _ in range(count):
        ctx.write_byte(ctx.dest[src_pos])
        src_pos += 1
    ctx.state = SET2


def sec_backref_var(ctx: DecompressContext):
    """Sec 11: Read byte -> table1 -> count + 3. Combined with stream as offset."""
    nxt = ctx.read_byte()
    ctx.tmp42 = nxt
    count = ctx.get_table1(nxt) + 3
    lo_nib = nxt & 0x0F
    byte2 = ctx.read_byte()
    off = (lo_nib << 8 | byte2) + 0x103
    src_pos = len(ctx.dest) - off
    if src_pos < 0:
        src_pos = 0
    for _ in range(count):
        ctx.write_byte(ctx.dest[src_pos])
        src_pos += 1
    ctx.state = SET1


def sec_backref_16bit_shifted(ctx: DecompressContext):
    """Sec 12: Read byte -> table1 -> count + 3. Complex 16-bit offset with table lookup."""
    nxt = ctx.read_byte()
    ctx.tmp42 = nxt
    count = ctx.get_table1(nxt) + 3
    lo_nib = nxt & 0x0F
    byte2 = ctx.read_byte()
    offset_raw = (lo_nib << 8 | byte2) << 4
    nxt2 = ctx.read_byte()
    ctx.tmp42 = nxt2
    low4 = ctx.get_table1(nxt2)
    off = offset_raw | low4
    src_pos = len(ctx.dest) - off
    if src_pos < 0:
        src_pos = 0
    for _ in range(count):
        ctx.write_byte(ctx.dest[src_pos])
        src_pos += 1
    ctx.state = SET2


def sec_header_indirect_secondary(ctx: DecompressContext):
    """Sec 15: Read from stream -> new format byte, indirect header copy."""
    nxt = ctx.read_byte()
    ctx.tmp46 = nxt
    off = ((nxt & 0xF0) >> 3) + 7
    pos = ctx.src_offset + off - 1
    ctx.write_byte(ctx.src_data[pos] if pos < len(ctx.src_data) else 0)
    if pos + 1 < len(ctx.src_data):
        ctx.write_byte(ctx.src_data[pos + 1])
    else:
        ctx.write_byte(0)
    ctx.state = SET2_WIDE


# ============================================================
# Main entry
# ============================================================

def main():
    import sys
    if len(sys.argv) < 2:
        print("Usage: python _decompress.py <compressed_file>")
        return

    path = Path(sys.argv[1])
    data = path.read_bytes()
    try:
        result = decompress(data)
        out_path = path.with_suffix(".bin")
        out_path.write_bytes(result)
        print(f"Decompressed {len(data)} -> {len(result)} bytes (ratio {len(result)/len(data):.2f}x)")
        print(f"Output: {out_path}")
    except NotImplementedError as e:
        print(f"Cannot decompress: {e}")
    except ValueError as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()
