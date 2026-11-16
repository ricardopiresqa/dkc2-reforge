# DKC2 Compression Format (CMP/BB8D91)

## Overview

DKC2 uses a custom table-driven compression scheme implemented at $BB:8D91.
Each compressed block has a 39-byte header followed by an opcode stream.
The algorithm is a bytecode interpreter with 16 primary opcodes (selected
by high nibble of format byte) and 16 secondary opcodes (selected by low
nibble). Opcodes include literal copy, fill, back-reference, shift-copy,
indirect table lookup, and OR-based operations.

## Data Bank Convention

```
Source:  bank $7F (WRAM), pointer in X register → DP $34[$35]
Dest:    bank $7E (WRAM), pointer in A register → DP $38 → X for writes
Flags:   Y register → DP $36
DMA opt: When $32 ≠ $FFFF, result DMA'd to VRAM via $58 address
```

Calling convention at $BB:8D91:
- **A** = destination pointer (low word, bank $7E)
- **X** = source pointer (low word, bank $7F)
- **Y** = flags

Alternate entry at $BB:8D9E:
- **X** = source pointer
- **Y** = flags
- Dest = $0000 (WRAM $7E:0000)

## Compressed Block Layout

```
Offset  Range   Size  Purpose
──────────────────────────────────────────────
0       [0]     1     UNUSED (Y starts at 1, byte 0 skipped)
1       [$52]   1     Header param A (fill value 1, context byte 1)
2       [$53]   1     Header param B (fill value 2, context byte 2)
3       [$56]   1     Header param C (context byte 3)
4       [$57]   1     Header param D (context byte 4)
5-6     [$54]   2     16-bit fill/offset word
7-38    [pool]  32    Incidental data pool (accessed via opcode F)
39      [$46]   1     Format-select byte → high nibble = primary op,
                      low nibble = length modifier / secondary op
40+     [...]   var   Opcode stream (alternating format bytes + data)
```

## Opcode Category Summary

### Primary Opcodes (high nibble of format byte)

| Hi | Entry  | Handler | Description |
|----|--------|---------|-------------|
| 0  | $8E2A  | LiteralCopy | Copy N bytes from stream (N=lo, N=0→EOF) |
| 1  | $8E96  | OrCopy1 | OR-copy 1 byte via indirection table |
| 2  | $8EB4  | OrCopy2 | OR-copy 2 bytes via indirection table |
| 3  | $8EEB  | LongLiteral | Copy (lo+3) literal bytes |
| 4  | $8F26  | Fill52 | Fill (lo+3) bytes with $52 |
| 5  | $8F53  | Fill53 | Fill (lo+3) bytes with $53 |
| 6  | $8F80  | WordFill54 | Write $54 word → secondary dispatch |
| 7  | $8F9C  | Write56 | Write $56 → secondary dispatch |
| 8  | $8FAE  | Write57 | Write $57 → secondary dispatch |
| 9  | $8FC0  | BackRefShort | Copy 2 bytes from (dest - lo - 2) |
| A  | $8FFF  | BackRefExtra | Copy (lo+3) bytes from dest - offset - extra |
| B  | $9062  | BackRefLong1 | Copy (lo+3) bytes from 16-bit shifted offset + $103 |
| C  | $90C9  | BackRefLong2 | Copy (lo+3) bytes from 16-bit swapped offset |
| D  | $9138  | ByteShift | Duplicate last byte, advance 1 → secondary |
| E  | $9150  | WordShift | Duplicate last word, advance 2 → secondary |
| F  | $9176  | HeaderIndir | Read word from pool[lo*2+7], write 2 bytes |

### Secondary Opcodes (low nibble dispatched after primary)

| Lo | Entry  | Handler | Description |
|----|--------|---------|-------------|
| 0  | $8E6F  | IndirLiteral | Read stream→table index; count from table; OR-copy loop |
| 1  | $8EAA  | SingleCopy | Copy 1 byte from stream |
| 2  | $8EDB  | WordCopy | Copy 2 bytes (word) from stream |
| 3  | $8F01  | OrRepeatIndir | Read stream→index; count from table; OR-copy (lo+3) |
| 4  | $8F3B  | Fill52Indir | Read stream→index; fill $52 using table count |
| 5  | $8F68  | Fill53Indir | Read stream→index; fill $53 using table count |
| 6  | $8F8E  | WordFill54 | Write $54 word |
| 7  | $8FA5  | Write56 | Write $56 |
| 8  | $8FB7  | Write57 | Write $57 |
| 9  | $8FDE  | BackRefExtra2 | Back-ref with table-indirect offset |
| A  | $9029  | BackRefTwoExt | OR-indirect count+offset, then back-ref |
| B  | $9097  | BackRefVar | Back-ref with header indirect offset |
| C  | $90F2  | BackRef16Shift | Back-ref with 16-bit shifted offset |
| D  | $9144  | ByteShift | Duplicate last byte |
| E  | $9163  | WordShift | Duplicate last word |
| F  | $9190  | HeaderIndir2 | Read stream→new format byte; indirect header word |

## Algorithm State Machine

```
Entry:
  Save params (A→$38, X→$34, Y→$36)
  Set $3a = $007f (source bank)
  Init: $32=$FFFF, $42=$2000, $44=$007e, $46=$2100, $48=$007e
  JSL $BB91AF (clear $7E2100-$7E21FF)

Init loop:
  X = $38 (dest ptr)
  Y = 1
  Read 4 bytes: [$34]+1→$52, [$34]+2→$53, [$34]+3→$56, [$34]+4→$57
  Read word: [$34]+5→$54  (16-bit)
  Y = $27  (skip bytes 7-38, they are data pool)
  $3c = $3e = 0

Dispatch:
  Read format byte at Y→$46
  Y++
  high_nibble = $46 & $F0, rotated right ×2 → dispatch table at $BB:8001+N*4
  → PEI $4e / RTS = computed JMP to handler_N

  After handler returns (via tail JMP back to Dispatch):
    Read next format byte from stream at current Y
    Repeat until op 0 with count=0

Termination (op 0 count=0 → $8E40):
  REP #$20
  PLY, PLB (restore DB)
  TXA - $38 = decompressed_size
  If $32 ≥ 0 (i.e., VRAM DMA address set):
    DMA channel 0: source = $38, bank = $3a, size = TXA, dest = $2116($58)
    Mode $1801, trigger DMA
  RTL
```

## Opcode Details

### Op 0: Literal Copy ($8E2A)
```
count = lo_nibble
if count == 0 → TERMINATE (RTL with optional DMA)
else:
  for i in range(count):
    write(read_byte())
```
Most common opcode. Small literal runs (1-15 bytes).
Count 0 is the ONLY way to end the stream.

### Op 1/2: OR-Copy ($8E96/$8EB4)
```
base = [$46]  → table[$7E:00{orig_fmt_byte}]
byte_ptr = read_byte()
write(base ORA table[byte_ptr])
```
Uses WRAM tables at $7E:0000-$00FF for base values and OR masks.
Requires pre-initialized table context. Op 1 copies 1 byte,
Op 2 copies 2 bytes (second byte re-reads the table).

### Op 3: Long Literal ($8EEB)
```
count = lo_nibble + 3   (3-18 bytes)
for i in range(count):
  write(read_byte())
```

### Op 4/5: Fill ($8F26/$8F53)
```
count = lo_nibble + 3   (3-18 bytes)
for i in range(count):
  write($52 or $53)
```
Efficient RLE for common fill bytes stored in header.

### Op 6: Word Fill ($8F80)
```
write($54 as 16-bit word)  // word from header bytes 5-6
→ secondary_dispatch(lo)
```
Useful for 16-bit patterns. Followed by secondary op.

### Op 7/8: Single Byte Write ($8F9C/$8FAE)
```
write($56 or $57)
→ secondary_dispatch(lo)
```

### Op 9: Short Back-Reference ($8FC0)
```
offset = lo_nibble + 2   (2-17 bytes back)
w = backref_read_word(offset)
write_word(w)
```
Copies 2 bytes from recently-written area. Backward offset ≤ 17.

### Op A: Back-Ref with Extra Offset ($8FFF)
```
count = lo_nibble + 3
extra = read_byte()
offset = count + extra
for i in range(count):
  write(backref_read_byte(offset))
```
Back-reference with 8-bit extra offset tacked on.

### Op B: Long Back-Ref 1 ($9062)
```
count = lo_nibble + 3
byte_a = read_byte()  // high byte via XBA
byte_b = read_byte()  // low byte
offset = ((byte_a << 8 | byte_b) >> 4) + 0x103
for i in range(count):
  write(backref_read_byte(offset))
```
Complex offset: reads 2-byte word, divides by 16, adds minimum $103.

### Op C: Long Back-Ref 2 ($90C9)
```
count = lo_nibble + 3
word = read_word()
offset = byte_swap(word)    // XBA
for i in range(count):
  write(backref_read_byte(offset))
```
Simple swapped 16-bit offset back-ref.

### Op D/E: Shift Copy ($9138/$9150)
```
// Byte: read dest[-1] → write at dest[0]
// Word: read dest[-2:0] → write at dest[0:2]
write(backref_read(1 or 2))
→ secondary_dispatch(lo)
```
Shift-right copy: duplicates last written byte(s).

### Op F: Header Indirect ($9176)
```
ptr = lo_nibble * 2 + 7
w = read_word_from_source(ptr)  // from header pool (bytes 7-38)
write_word(w)
```
Accesses 16-bit values embedded in the header data pool.
Lo selects which of the 16 possible words (offsets 7,9,11,...,37).

## Secondary Dispatch

Called from primary ops 6,7,8,D,E,F (and internally from some secondaries).
Lo nibble selects the secondary handler. Most secondaries JMP back to
$8E02 (main dispatch loop) when done; some JMP to $8E10 (low nibble
re-dispatch) for chaining.

Secondary ops 0,3,4,5,9,A,B,C use the same `[$42]` indirection pattern
as primary op 1: read stream byte → table index; read count/base from
table in WRAM $7E:0000-$00FF. This means these opcodes require the
game's WRAM context table to be present.

Secondary op 15 (F) reads a new format byte from the stream, then reads
a word from the header pool using the new format byte's low nibble,
effectively allowing format-byte redirection.

## Termination Sequence

When op 0 is encountered with lo = 0:
1. Restore registers (PLY, PLB)
2. Compute decompressed size: X = write_ptr - initial_write_ptr ($38)
3. If DMA VRAM address ($32) is ≥ 0 (i.e., caller set $58/$32):
   DMA channel 0 transfers decompressed data to VRAM at $58 address
4. RTL

The DMA uses mode $1801 (2-register write, increment source, fixed dest)
which writes 2 bytes per VRAM access (word mode).

## WRAM Context Tables

Several opcodes (1,2, and secondaries 0,3,4,5,9,A,B,C) use indirect
table lookups in WRAM $7E:0000-$00FF, indexed by a byte read from the
stream. These tables must be populated before calling the decompressor
and contain format-specific base values, OR masks, and run lengths.

The tables are at DP address $42 (used as `[$42]`) and $46 (used as `[$46]`).
Both $42 and $44 are initialized to $2000 and $007e respectively, making
them read from $7E:$2000 + stream_byte. However, $46 is initially $2100,
read from $7E:$2100 + stream_byte.

Wait — re-reading the init more carefully:
- $46 = $2100  (VRAM shadow buffer in WRAM)
- $44 = $007e  (bank for all indirect reads)
- $42 = $2000  (base offset)

So `[$42]` where $42=byte reads from $7E:20{byte} (0x2000 + byte).
And `[$46]` where $46=byte reads from $7E:21{byte} (0x2100 + byte).

These are WRAM regions initialized by JSL $BB91AF (clears $7E2100-$7E21FF)
and populated with format-specific data before calling decompress.

The OR-copy opcodes work as:
```
base = table2[$7E:21{fmt_byte}]     // [$46]
count = table1[$7E:20{idx_byte}]    // [$42]
op = table2[$7E:21{idx_byte}]       // [$46]
write(base | op)
```

## Notes

- The format is NOT standard LZ77/LZSS — it is a custom bytecode VM.
- The `PEI $4e / RTS` computed jump pattern is unusual and efficient:
  pushes 16-bit value at DP $4e onto stack as a return address, then RTS
  "returns" to it, effectively JMPing to that address.
  $4e stores $8001 + high_nibble*4, giving addresses $8001, $8005, $8009...
  These contain JMP instructions to the actual handler code.
- The primary dispatch entry at $BB:8000 is a NOP placeholder (byte 0x00).
- Bank $7F is fully WRAM; compressed data is pre-loaded from ROM by
  separate loader functions.
- The "data pool" at bytes 7-38 is exactly 32 bytes (16 words), perfectly
  matching the 16 entries of opcode F (header indirect).
- This format appears to be designed for tile/graphics compression:
  the header params often encode common tile colors (palette indices),
  DMA integration suggests VRAM-targeted data.
