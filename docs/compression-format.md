# DKC2 Big Data Compression Format

## Overview

DKC2 uses a **nibble-pair compressed format** (internally called "Big Data" or PAC1) for level graphics, tilemaps, collision maps, and other bulk assets. The format features:

- LZ77-style back-reference copies (distance + count)
- RLE fill with two configurable fill bytes from header
- Direct byte/word emission from header constants
- Nibble reconstruction via runtime lookup tables
- **Two alternating command sets** (Set1/Set2) — each 16 commands, dispatched by nibble value
- Variable-length encoding: each command byte encodes two nibble operations (hi nibble = Set1, lo nibble = Set2-or-next)

The decompressor lives in SA-1 BW-RAM (bank $BB, uploaded at init) and executes on the SA-1 coprocessor. The source code is stored in ROM bank $B7 and DMA'd to BW-RAM bank $BB at init time — all JSL references within the code target $BB (the upload destination), not $B7.

**ROM version note:** In the US 1.0 ROM (SHA1 `29601b58`), the decompressor code resides at ROM $3B8000–$3B91D8 (SNES $B7:8000), uploaded to SA-1 BW-RAM at $BB8000. The SA-1 firmware API in this ROM version uses `JSL $B58003` (223 call sites), not `$B5804C` as in some other versions.

Entry points (BW-RAM runtime addresses):

| Entry | Address | Description |
|---|---|---|
| `decompress_data` | $BB8D91 | Set dest bank+addr from A, source from X/Y |
| `decompress_data_default` | $BB8D9E | Dest = $7F0000, source from X/Y |
| `finalize_decompression` | $BB8E40 | Returns decompressed size in X |

---

## Packet Format

Each compressed asset is a self-contained packet:

```
+--------+--------+--------------------+
| PAC1   | Header | Command Stream     |
| (4B)   | (39B)  | (variable)         |
+--------+--------+--------------------+
```

The `PAC1` signature (`$50 $41 $43 $31` = "PAC1") is stripped by the outer wrapper before calling the decompressor. The decompressor receives a pointer to the **byte after the signature** (i.e., at the header start).

---

## Header Structure (39 bytes)

Offset relative to the byte after `PAC1`:

| Offset | Size | Field | WRAM Dest | Description |
|---|---|---|---|---|
| $00 | 1 | Reserved | — | Always $00. Skipped by decompressor (Y starts at 1). |
| $01 | 1 | Fill Byte 1 | $52 | First RLE fill byte. Used by `direct_byte_1_fill` commands. |
| $02 | 1 | Fill Byte 2 | $53 | Second RLE fill byte. Used by `direct_byte_2_fill` commands. |
| $03 | 1 | Direct Byte 1 | $56 | Emitted by `direct_byte_1_put` commands. |
| $04 | 1 | Direct Byte 2 | $57 | Emitted by `direct_byte_2_put` commands. |
| $05 | 2 | Direct Word | $54 | 16-bit value emitted by `direct_word_put` commands. |
| $07 | 32 | 16-word LUT | — | Lookup table (16 words, not loaded to WRAM — consumed by commands that reference `[$34],y` offsets). |

Total header size: 39 bytes ($00–$26). The decompressor sets Y = $27 before reading the first command byte.

**Note about offset $00:** The decompressor starts reading at Y=1 (skip byte 0). This byte is consistently $00 in all observed data.

---

## Nibble Lookup Tables

At init time, `build_decompression_lookup` ($BB91AF) populates two 256-byte tables in WRAM:

| Address | Name | Function | Formula |
|---|---|---|---|
| $7E2000–$7E20FF | Low-nibble LUT | Takes byte → returns its **high nibble** right-aligned | `LUT_LO[byte] = byte >> 4` |
| $7E2100–$7E21FF | High-nibble LUT | Takes byte → returns its **low nibble** left-shifted by 4 | `LUT_HI[byte] = (byte & 0x0F) << 4` |

These tables are used as **self-modifying pointers** in WRAM. The decompressor stores pointers in direct page:

- `$42/$43` = base $7E2000 (low-nibble LUT) — **also** doubles as temporary byte storage by overwriting the low byte
- `$46/$47` = base $7E2100 (high-nibble LUT) — **also** doubles as temporary byte storage

When the command byte `$AB` is stored into `$42` via `STA $42`:
- `$42` = $AB, `$43` = $7E → forms address `$7E20AB`
- `LDA [$42]` reads `$7E2000[$AB]` = `$AB >> 4` = `$0A`
- This extracts the high nibble into the low nibble position

Similarly for `$46`: storing `$AB` forms address `$7E21AB`, and `LDA [$46]` reads `$7E2100[$AB]` = `($AB & 0x0F) << 4` = `$B0`.

This trick allows the decompressor to extract and reassemble nibbles with a single indexed indirect load, no shift/and instructions needed in the hot path.

---

## Dispatch Mechanism

The decompressor alternates between two command sets. Each command byte encodes two operations:

Command byte `$XY`:
- **High nibble** (`X`): dispatched as Set1 command
- **Low nibble** (`Y`): dispatched as Set2 command (either from $46 or from a new byte)

### Initial Dispatch

```
Read byte from stream → store in $46
Set1 index = ($46 & 0xF0) >> 2   (hi nibble × 4, range $00–$3C)
JMP to Set1 table[$BB8000 + index + 1]
```

The `+1` is via the RTS convention: PEI pushes target-1, RTS adds 1.

### Alternation Rules

After each Set1 command, one of three things happens:

| Exit | Mechanism | When |
|---|---|---|
| `JMP execute_command_set_1` | Reads a **new** byte from stream → Set1 dispatch | Command consumed a byte from stream |
| `JMP execute_command_set_2` | Uses existing byte in **$42** (from `STA $42` side-effect) → Set2 dispatch | Command stored its consumed byte into $42 |
| `JMP execute_command_set_2_wide` | Uses existing byte in **$46** (the original command byte) → Set2 dispatch | Command did NOT consume a new byte |

After each Set2 command, one of two things happens:

| Exit | Mechanism |
|---|---|
| `JMP execute_command_set_1` | Reads new byte → Set1 dispatch |
| `JMP execute_command_set_2_wide` | Uses $46 (original Set2 command byte) → Set2 dispatch again |

### Set1 Dispatch

```
execute_command_set_1:
  LDA [$34],y   ; Read next byte from compressed stream
  INY
  STA $46       ; Store in $46 (doubles as high-LUT pointer)
  AND #$F0      ; Extract hi nibble
  LSR A; LSR A  ; ×4 → index $00–$3C
  STA $4E       ; $4E = index, $4F = $80
  PEI ($4E)     ; Push $8000 + index
  RTS           ; Jump to $BB8000 + index + 1
```

### Set2 Dispatch

```
execute_command_set_2:
  LDA $42       ; Get stored byte from $42 (set by previous command)
  AND #$0F      ; Extract lo nibble
  ASL A; ASL A  ; ×4 → index $00–$3C
  ADC #$3F      ; +63 → index $3F–$7B
  STA $4A       ; $4A = index, $4B = $80
  PEI ($4A)     ; Push $8000 + index
  RTS           ; Jump to $BB8000 + index + 1
```

```
execute_command_set_2_wide:
  LDA $46       ; Get byte from $46 (original command byte)
  (same ×4+$3F formula as above)
```

### Jump Table Addresses

**Set1 table:** $BB8000, 16 entries × 4 bytes each

| nibble | Entry addr | JMP addr | Command |
|---|---|---|---|
| 0 | $BB8000 | $BB8001 | copy_or_return_1 |
| 1 | $BB8004 | $BB8005 | stream_byte_1 |
| 2 | $BB8008 | $BB8009 | stream_word_1 |
| 3 | $BB800C | $BB800D | stream_byte_fill_1 |
| 4 | $BB8010 | $BB8011 | direct_byte_1_fill_1 |
| 5 | $BB8014 | $BB8015 | direct_byte_2_fill_1 |
| 6 | $BB8018 | $BB8019 | direct_word_put_1 |
| 7 | $BB801C | $BB801D | direct_byte_1_put_1 |
| 8 | $BB8020 | $BB8021 | direct_byte_2_put_1 |
| 9 | $BB8024 | $BB8025 | back_copy_word_1 |
| 10 | $BB8028 | $BB8029 | back_copy_1 |
| 11 | $BB802C | $BB802D | back_copy_far_1 |
| 12 | $BB8030 | $BB8031 | back_copy_arbitrary_1 |
| 13 | $BB8034 | $BB8035 | duplicate_byte_1 |
| 14 | $BB8038 | $BB8039 | duplicate_word_1 |
| 15 | $BB803C | $BB803D | copy_future_word_1 |

**Set2 table:** $BB8040, 16 entries × 4 bytes each (entry 0 is 3 bytes)

| nibble | Entry addr | JMP addr | Command |
|---|---|---|---|
| 0 | $BB8040 | $BB8040 | copy_or_return_2 |
| 1 | $BB8043 | $BB8044 | stream_byte_2 |
| 2 | $BB8047 | $BB8048 | stream_word_2 |
| 3 | $BB804B | $BB804C | stream_byte_fill_2 |
| 4 | $BB804F | $BB8050 | direct_byte_1_fill_2 |
| 5 | $BB8053 | $BB8054 | direct_byte_2_fill_2 |
| 6 | $BB8057 | $BB8058 | direct_word_put_2 |
| 7 | $BB805B | $BB805C | direct_byte_1_put_2 |
| 8 | $BB805F | $BB8060 | direct_byte_2_put_2 |
| 9 | $BB8063 | $BB8064 | back_copy_word_2 |
| 10 | $BB8067 | $BB8068 | back_copy_2 |
| 11 | $BB806B | $BB806C | back_copy_far_2 |
| 12 | $BB806F | $BB8070 | back_copy_arbitrary_2 |
| 13 | $BB8073 | $BB8074 | duplicate_byte_2 |
| 14 | $BB8077 | $BB8078 | duplicate_word_2 |
| 15 | $BB807B | $BB807C | copy_future_word_2 |

The JMP addr column shows where RTS lands (entry address + 1 for Set1, entry address + low nibble offset for Set2). Set1 entries are NOP+JMP (4 bytes). Set2 entries are JMP+NOP padding (4 bytes).

**ROM source:** In the US 1.0 ROM (SHA1 `29601b58`), the jump tables are stored at ROM $3B8000 (Set1, 16×4) and ROM $3B8040 (Set2, 16×4), which map to SNES $B7:8000 and $B7:8040 respectively. These are uploaded to SA-1 BW-RAM at $BB:8000 / $BB:8040 at init.

---

## Command Set 1 (Hi Nibble)

### Nibble 0 — copy_or_return_1
```
count = byte & 0x0F
if count == 0 → finalize (return decompressed size)
copy count bytes from stream to output
→ Set1 (read new byte)
```

Terminates decompression when count = 0. Otherwise copies 1–15 literal bytes from the compressed stream.

### Nibble 1 — stream_byte_1
```
hi = LUT_HI[byte]          ; (byte & 0x0F) << 4  — low nibble of byte in high position
next = read stream byte
store (hi | LUT_LO[next])  ; hi_nibble | (next >> 4)
→ Set2 (using $42 = next)
```

Rebuilds a byte from two components: the low nibble of the command byte (in high position) plus the high nibble of the next stream byte. Writes 1 reconstructed byte.

### Nibble 2 — stream_word_1
```
hi = LUT_HI[byte]          ; low nibble of cmd byte in high position
next1 = read stream byte
store (hi | LUT_LO[next1])
hi2 = LUT_HI[next1]        ; low nibble of next1 in high position
next2 = read stream byte
store (hi2 | LUT_LO[next2])
→ Set2 (using $42 = next2)
```

Same as stream_byte_1 but writes 2 reconstructed bytes.

### Nibble 3 — stream_byte_fill_1
```
count = (byte & 0x0F) + 3  ; 3–18
fill = read stream byte
fill count copies of fill byte to output
→ Set1 (read new byte)
```

RLE fill with a stream-provided fill byte. Count range 3–18.

### Nibble 4 — direct_byte_1_fill_1
```
count = (byte & 0x0F) + 3  ; 3–18
fill = $52                 ; header fill byte 1
fill count copies of fill byte to output
→ Set1 (read new byte)
```

RLE fill with header-defined fill byte 1.

### Nibble 5 — direct_byte_2_fill_1
Same as nibble 4, but uses header fill byte 2 ($53).

### Nibble 6 — direct_word_put_1
```
emit $54 (header direct word, 2 bytes)
→ Set2_wide (using $46 = current byte)
```

### Nibble 7 — direct_byte_1_put_1
```
emit $56 (header direct byte 1)
→ Set2_wide (using $46 = current byte)
```

### Nibble 8 — direct_byte_2_put_1
```
emit $57 (header direct byte 2)
→ Set2_wide (using $46 = current byte)
```

### Nibble 9 — back_copy_word_1
```
offset = (byte & 0x0F) + 2  ; 2–17
copy 1 word from output[-offset]
→ Set1 (read new byte)
```

Back-reference: copies a single word from a position behind the current output pointer.

### Nibble 10 — back_copy_1
```
count = (byte & 0x0F) + 3  ; 3–18
offset = read stream byte
copy count bytes from output[-count-offset]
→ Set1 (read new byte)
```

Back-reference: copies multiple bytes. The negative offset is computed as `-(count + offset)`, where offset is an 8-bit unsigned value from the stream.

### Nibble 11 — back_copy_far_1
```
count = (byte & 0x0F) + 3  ; 3–18
hi = read stream byte (XBA to high byte)
lo = read stream byte → store to $46 (LUT index)
offset = (hi_byte << 4 | (lo & 0x0F)) ???

Actually:
  XBA           ; hi → high byte of A
  LDA [$34],y   ; lo byte
  INY
  STA $46       ; store lo in table

  REP #$20
  LSR A; LSR A; LSR A; LSR A  ; lo >> 4
  CLC
  ADC #$0103                   ; offset = (lo >> 4) + 0x0103
```

Wait, this re-reads the same byte. Let me re-trace:

Actually in back_copy_far_1:
```
LDA [$34],y   ; read byte
INY
XBA           ; swap: hi byte of 16-bit A = read byte
LDA [$34],y   ; read another byte into lo byte of A
INY
STA $46       ; store 2nd byte
REP #$20      ; 16-bit A = (1st_byte << 8) | 2nd_byte
LSR A; LSR A; LSR A; LSR A  ; A = (value >> 4)
CLC
ADC #$0103    ; offset = (value >> 4) + 0x0103
STA $40
```

So 2 bytes are read: B1 and B2. The offset is `((B1 << 8 | B2) >> 4) + 0x0103`. That's a 12-bit offset (the top nibble of the 16-bit value is discarded) + 0x0103 base.

Then:
```
Y = X - offset   ; current write position minus offset
copy count bytes from Y to output
→ Set2_wide
```

### Nibble 12 — back_copy_arbitrary_1
```
count = (byte & 0x0F) + 3  ; 3–18
word = read 2 bytes (big-endian: XBA then read)
offset = word
Y = X - offset
copy count bytes from Y
→ Set1
```

Full 16-bit back-reference offset.

### Nibble 13 — duplicate_byte_1
```
output[0] = output[-1]    ; duplicate previous byte
→ Set2_wide
```

### Nibble 14 — duplicate_word_1
```
output[0..1] = output[-2..-1]  ; duplicate previous word
→ Set2_wide
```

### Nibble 15 — copy_future_word_1
```
offset = (byte & 0x0F) << 1 + 7  ; 7–37 bytes ahead
copy 1 word from stream at Y + offset
→ Set1
```

Copies a word from a position ahead in the compressed stream (not the output). Useful for metadata or interleaved data.

---

## Command Set 2 (Lo Nibble)

Set2 commands are mostly analogous to Set1 but with different nibble extraction patterns:

- Set2 reads its count from **$42** (low-nibble LUT: byte >> 4) instead of `byte & 0x0F`
- Set2 reads its byte operands from the stream more aggressively
- Some Set2 commands use nibble reassembly (via LUTs) where Set1 uses raw bytes

### Nibble 0 — copy_or_return_2
```
next = read stream byte → $42, $46
count = LUT_LO[next]      ; next >> 4 (high nibble)
if count == 0 → finalize
```

Same termination condition as Set1's copy_or_return, but reads a new byte and extracts its high nibble as the count.

### Nibble 1 — stream_byte_2
```
Direct copy: read 1 byte from stream → output
→ Set1
```

Simple literal byte copy (complement to Set1 stream_byte_1 which does nibble reassembly).

### Nibble 2 — stream_word_2
```
Direct copy: read 1 word (2 bytes) from stream → output
→ Set1
```

### Nibble 3 — stream_byte_fill_2
```
next = read stream byte → $42, $46
count = LUT_LO[next] + 3  ; (next >> 4) + 3, range 3–18
fill_hi = LUT_HI[next]    ; (next & 0x0F) << 4
next2 = read stream byte → $42
fill = fill_hi | LUT_LO[next2]  ; reconstruct fill byte from nibbles
fill count copies of fill byte
→ Set2 (using $42 = next2)
```

### Nibble 4 — direct_byte_1_fill_2
```
next = read stream byte → $42
count = LUT_LO[next] + 3  ; (next >> 4) + 3
fill = $52 (header fill byte 1)
→ Set2
```

### Nibble 5 — direct_byte_2_fill_2
Same as nibble 4, fill = $53.

### Nibble 6 — direct_word_put_2
```
emit $54 (header direct word, 2 bytes)
→ Set1
```

### Nibble 7 — direct_byte_1_put_2
```
emit $56 (header direct byte 1)
→ Set1
```

### Nibble 8 — direct_byte_2_put_2
```
emit $57 (header direct byte 2)
→ Set1
```

### Nibble 9 — back_copy_word_2
```
next = read stream byte → $42
offset = LUT_LO[next] + 2  ; (next >> 4) + 2
copy 1 word from output[-offset]
→ Set2 (using $42 = next)
```

### Nibble 10 — back_copy_2
```
next = read stream byte → $42, $46
count = LUT_LO[next] + 3
offset_hi = LUT_HI[next]       ; (next & 0x0F) << 4
next2 = read stream byte → $42
offset = offset_hi | LUT_LO[next2]  ; reconstruct 8-bit offset
Y = X - count - offset
copy count bytes
→ Set2 (using $42 = next2)
```

### Nibble 11 — back_copy_far_2
```
next = read stream byte → $42
count = LUT_LO[next] + 3
lo_nibble = next & 0x0F → XBA (store as high byte of 16-bit A)
lo_byte = read stream byte
offset = (lo_nibble << 8 | lo_byte) + 0x0103
Y = X - offset
copy count bytes
→ Set1
```

### Nibble 12 — back_copy_arbitrary_2
```
next = read stream byte → $42
count = LUT_LO[next] + 3
lo_nibble = next & 0x0F → XBA
lo_byte = read stream byte
offset_raw = (lo_nibble << 8 | lo_byte) << 4
offset = offset_raw & 0xFF00 | ...
then next2 = read stream byte → $42
low4 = LUT_LO[next2]  ; next2 >> 4
offset = offset_raw | low4
Y = X - offset
copy count bytes
→ Set2 (using $42 = next2)
```

This is the most complex command. It builds an 11-bit back-reference offset from three nibbles across two stream bytes, then copies.

### Nibble 13 — duplicate_byte_2
```
output[0] = output[-1]
→ Set1
```

### Nibble 14 — duplicate_word_2
```
output[0..1] = output[-2..-1]
→ Set1
```

### Nibble 15 — copy_future_word_2
```
next = read stream byte → $46
offset = (next & 0xF0) >> 3 + 7  ; hi nibble × 2 + 7? 

Actually:
  REP #$20
  AND #$00F0    ; hi nibble only
  LSR A; LSR A; LSR A  ; hi_nibble × 2
  PHY
  ADC #$0007           ; +7
  
So offset = (hi_nibble × 2) + 7
```

Wait, `AND #$00F0` with 16-bit A keeps the hi nibble. Then 3 LSR = divide by 8. `$00F0 >> 3 = $001E = 30`. Hmm, that's `hi_nibble × 16 >> 3 = hi_nibble × 2`.

So for hi_nibble = F (15): offset = 15 × 2 + 7 = 37.
For hi_nibble = 0: offset = 7.

```
copy 1 word from stream at Y + offset
→ Set2_wide (using $46 = next)
```

---

## LZ77/RLE Semantics Summary

The format implements standard LZ77 with literal, back-reference and RLE modes:

| Category | Commands | Description |
|---|---|---|
| **Literal copy** | stream_byte_1/2, stream_word_1/2, copy_or_return_1/2, copy_future_word_1/2 | Copies raw bytes from the compressed stream to output |
| **Nibble-reconstruct literal** | stream_byte_1, stream_word_1, stream_byte_fill_2, back_copy_2, back_copy_arbitrary_2 | Reassembles bytes from nibbles stored in different positions of the byte stream |
| **Back-reference** | back_copy_word_1/2, back_copy_1/2, back_copy_far_1/2, back_copy_arbitrary_1/2 | Copies previously decompressed bytes from output[-offset] |
| **RLE fill** | stream_byte_fill_1, direct_byte_1/2_fill_1/2 | Fills output with repeated byte |
| **Direct const emit** | direct_word_put_1/2, direct_byte_1/2_put_1/2 | Emits bytes/words from header |
| **Duplicate** | duplicate_byte_1/2, duplicate_word_1/2 | Copies last 1–2 bytes |

---

## Comparison with dkcomp Library

[Kingizor/dkcomp](https://github.com/Kingizor/dkcomp) implements a **single-set** compression format that is structurally different from the original game format:

| Feature | Original DKC2 | dkcomp |
|---|---|---|
| Command sets | Two (Set1/Set2, alternating) | One (no alternation) |
| Dispatch | Multi-phase: hi nibble→Set1, lo nibble→Set2 | Single: nibble→command |
| Nibble 0 | copy_or_return (terminator) | copy_or_return (terminator) |
| Nibble 3 | RLE fill | stream_word (completely different) |
| Nibble 4 | Fill from header byte 1 | back_copy (completely different) |
| Nibble 5 | Fill from header byte 2 | back_copy (different parameters) |
| Header | 39 bytes | Similar but not identical |

**Data compressed with dkcomp cannot be decompressed by the original game**, and vice versa. The format signatures may appear similar (both use PAC1 + nibble dispatch), but the command semantics diverged during the compression tool's development.

---

## Algorithm Walkthrough

```
Input:  pointer to PAC1 data (after signature)
Output: decompressed data at WRAM destination ($7F0000 default)

1. Read 39-byte header into WRAM variables:
   fill1 = header[1], fill2 = header[2]
   dir1 = header[3], dir2 = header[4]
   dirW = header[5..6]

2. Build nibble lookup tables at $7E2000 / $7E2100

3. Read first command byte
   → dispatch Set1 using hi nibble

4. Execute Set1 command:
   - Consumes 0–3 bytes from stream (depending on command)
   - Writes 0–18 bytes to output
   - Exits via:
     → Set1: read new byte, goto 3
     → Set2: use existing byte in $42/$46, goto 5
     → Return: if count=0 in copy_or_return, goto 7

5. Dispatch Set2 using lo nibble (from $42 or $46)

6. Execute Set2 command:
   - Similar semantics to Set1
   - Exits via:
     → Set1: read new byte, goto 3
     → Set2_wide: use $46, goto 5
     → Return: if count=0 in copy_or_return_2

7. Return decompressed size in X
```

The key insight is that each command byte drives **two** dispatch operations (hi nibble → first command, lo nibble → second command), though some commands may read additional bytes and re-enter the same set.

---

## WRAM Variables

| Address | Size | Name | Description |
|---|---|---|---|
| $34 | 3 | src_ptr | Compressed source pointer (bank:addr) |
| $38 | 3 | dst_ptr | Decompression destination (bank:addr) |
| $32 | 2 | dma_flag | Auto-DMA control; always $FFFF (disabled) |
| $3C | 1 | operand1 | Generic count operand |
| $3E | 1 | operand2 | Generic offset/value operand |
| $40 | 2 | operandW | 16-bit work value (offset or temporary) |
| $42 | 2 | lut_lo_ptr | Low-nibble LUT pointer base ($7E2000), low byte used as index |
| $46 | 2 | lut_hi_ptr | High-nibble LUT pointer base ($7E2100), low byte used as index |
| $4A | 2 | set2_jmp | Set2 jump table pointer ($BB8040) |
| $4E | 2 | set1_jmp | Set1 jump table pointer ($BB8000) |
| $52 | 1 | fill_byte_1 | Header fill byte 1 |
| $53 | 1 | fill_byte_2 | Header fill byte 2 |
| $54 | 2 | direct_word | Header direct word |
| $56 | 1 | direct_byte_1 | Header direct byte 1 |
| $57 | 1 | direct_byte_2 | Header direct byte 2 |

All addresses are in direct page (bank $00).
