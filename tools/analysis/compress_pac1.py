"""DKC2 PAC1 (Big Data) compressor.

Produces PAC1 compressed data compatible with the original game decompressor.

Commands v1 (Set1-only, flag --simple):
  cmd=0: copy_or_return — literal copy (1-15 bytes) or terminator (count=0)
  cmd=3: stream_byte_fill_1 — RLE with stream byte (3-18 count)
  cmd=4: direct_byte_1_fill_1 — RLE with header fill1 (3-18)
  cmd=5: direct_byte_2_fill_1 — RLE with header fill2 (3-18)
  cmd=9: back_copy_word_1 — back-ref word (offset 2-17)
  cmd=10: back_copy_1 — back-ref (count 3-18, 1-byte offset)
  cmd=12: back_copy_arbitrary_1 — back-ref (count 3-18, 2-byte offset)

Commands v2 (default, with Set2):
  Same Set1 commands plus all Set2 commands, packed for efficiency.
  Uses the alternation between SET1/SET2/SET2_WIDE states to encode
  two operations per command byte where beneficial.

Usage:
    python compress_pac1.py --input raw.bin --output compressed.pac1
    python compress_pac1.py --decompress --input compressed.pac1 --output decompressed.bin
    python compress_pac1.py --simple --input raw.bin --output compressed.pac1
    cat raw.bin | python compress_pac1.py > compressed.pac1
"""

import argparse
import struct
import sys

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

HEADER_SIZE = 39

SET1, SET2, SET2_WIDE = 1, 2, 3

# ---------------------------------------------------------------------------
# Nibble LUTs (same as decode_pac1.py)
# ---------------------------------------------------------------------------

def _build_lut():
    lo = [b >> 4 for b in range(256)]
    hi = [(b & 0x0F) << 4 for b in range(256)]
    return lo, hi

LO, HI = _build_lut()


# ---------------------------------------------------------------------------
# Header building
# ---------------------------------------------------------------------------

def build_header(fill1=0x00, fill2=0x00, dir1=0x00, dir2=0x00, dirw=0x0000,
                 lut=None):
    """Build a 39-byte PAC1 header.

    Args:
        fill1, fill2: RLE fill bytes.
        dir1, dir2: Direct bytes.
        dirw: Direct word (uint16).
        lut: 16-word lookup table (default: zeros).

    Returns:
        bytes: 39-byte header.
    """
    if lut is None:
        lut = [0] * 16
    buf = bytearray(39)
    buf[0] = 0x00  # reserved
    buf[1] = fill1
    buf[2] = fill2
    buf[3] = dir1
    buf[4] = dir2
    struct.pack_into('<H', buf, 5, dirw & 0xFFFF)
    for i, w in enumerate(lut[:16]):
        struct.pack_into('<H', buf, 7 + i * 2, w & 0xFFFF)
    return bytes(buf)


# ---------------------------------------------------------------------------
# Compressed stream writer — Set1 only (legacy)
# ---------------------------------------------------------------------------

class PAC1Writer:
    """Writes PAC1 compressed stream using only SET1->SET1 commands.

    Each byte encodes one Set1 command + its operand (lo nibble).
    All commands used here transition back to SET1 after execution,
    meaning every compressed byte starts a new command.
    """

    def __init__(self):
        self.data = bytearray()

    def cmd_copy_or_return(self, count, literal_bytes):
        """Set1 cmd=0: copy_or_return.
        count=0 -> terminator. count=1..15 -> copies that many literal bytes.
        Lo nibble = count.
        -> SET1
        """
        assert 0 <= count <= 15, f"count must be 0-15, got {count}"
        if count > 0:
            assert len(literal_bytes) == count, \
                f"expected {count} literal bytes, got {len(literal_bytes)}"
        self.data.append((0 << 4) | count)
        if count > 0:
            self.data.extend(literal_bytes)
        return self

    def cmd_stream_byte_fill(self, count, fill_byte):
        """Set1 cmd=3: stream_byte_fill_1.
        RLE fill with stream-provided byte. count 3..18.
        Lo nibble = count - 3.
        -> SET1
        """
        assert 3 <= count <= 18, f"count must be 3-18, got {count}"
        self.data.append((3 << 4) | (count - 3))
        self.data.append(fill_byte & 0xFF)
        return self

    def cmd_direct_byte_1_fill(self, count):
        """Set1 cmd=4: direct_byte_1_fill_1.
        RLE fill with header fill byte 1. count 3..18.
        Lo nibble = count - 3.
        -> SET1
        """
        assert 3 <= count <= 18
        self.data.append((4 << 4) | (count - 3))
        return self

    def cmd_direct_byte_2_fill(self, count):
        """Set1 cmd=5: direct_byte_2_fill_1. count 3..18. -> SET1"""
        assert 3 <= count <= 18
        self.data.append((5 << 4) | (count - 3))
        return self

    def cmd_back_copy_word(self, offset):
        """Set1 cmd=9: back_copy_word_1.
        Copy 1 word from output[-offset]. offset 2..17.
        Lo nibble = offset - 2.
        -> SET1
        """
        assert 2 <= offset <= 17, f"offset must be 2-17, got {offset}"
        self.data.append((9 << 4) | (offset - 2))
        return self

    def cmd_back_copy(self, count, offset_byte):
        """Set1 cmd=10: back_copy_1.
        Copy count bytes from output[-count-offset_byte].
        count 3..18, offset_byte uint8.
        Lo nibble = count - 3.
        -> SET1
        """
        assert 3 <= count <= 18
        assert 0 <= offset_byte <= 255
        self.data.append((10 << 4) | (count - 3))
        self.data.append(offset_byte & 0xFF)
        return self

    def cmd_back_copy_arbitrary(self, count, b1, b2):
        """Set1 cmd=12: back_copy_arbitrary_1.
        Copy count bytes from output[-offset] where offset = (b1<<8 | b2).
        count 3..18.
        Lo nibble = count - 3.
        -> SET1
        """
        assert 3 <= count <= 18
        self.data.append((12 << 4) | (count - 3))
        self.data.append(b1 & 0xFF)
        self.data.append(b2 & 0xFF)
        return self

    def emit_terminator(self):
        """Emit end-of-stream marker (copy_or_return with count=0)."""
        self.cmd_copy_or_return(0, b'')
        return self

    def get_data(self):
        """Return the compressed stream bytes (header NOT included)."""
        return bytes(self.data)


# ---------------------------------------------------------------------------
# Compressed stream writer — Set1 + Set2 (enhanced)
# ---------------------------------------------------------------------------

class Set2PAC1Writer(PAC1Writer):
    """PAC1 writer that can emit Set1 and Set2 commands with state alternation.

    Tracks current state (SET1, SET2, SET2_WIDE) and allows encoding
    two operations per command byte where the state machine permits.
    """

    def __init__(self):
        super().__init__()
        self.state = SET1
        self._pending_set2_byte = None  # byte whose lo nibble gets Set2
        self._pending_set2_idx = -1     # index of the pending byte in self.data
        self._set2_operands = bytearray()  # operands for the Set2 cmd

    # ── Set2 command methods (emit to current byte's lo nibble) ──────

    def cmd_stream_byte_2(self, literal_byte):
        """Set2 cmd=1: stream_byte_2. Copy 1 literal byte. -> SET1"""
        self._write_set2_cmd(1, bytes([literal_byte & 0xFF]))
        return self

    def cmd_stream_word_2(self, b1, b2):
        """Set2 cmd=2: stream_word_2. Copy 2 literal bytes. -> SET1"""
        self._write_set2_cmd(2, bytes([b1 & 0xFF, b2 & 0xFF]))
        return self

    def cmd_direct_word_put_2(self):
        """Set2 cmd=6: direct_word_put_2. Emit header word. -> SET1"""
        self._write_set2_cmd(6, b'')
        return self

    def cmd_direct_byte_1_put_2(self):
        """Set2 cmd=7: direct_byte_1_put_2. Emit dir1. -> SET1"""
        self._write_set2_cmd(7, b'')
        return self

    def cmd_direct_byte_2_put_2(self):
        """Set2 cmd=8: direct_byte_2_put_2. Emit dir2. -> SET1"""
        self._write_set2_cmd(8, b'')
        return self

    def cmd_duplicate_byte_2(self):
        """Set2 cmd=13: duplicate_byte_2. Dup last byte. -> SET1"""
        self._write_set2_cmd(13, b'')
        return self

    def cmd_duplicate_word_2(self):
        """Set2 cmd=14: duplicate_word_2. Dup last word. -> SET1"""
        self._write_set2_cmd(14, b'')
        return self

    # ── Internal: write a Set2 command into the lo nibble ────────────

    def _write_set2_cmd(self, cmd, operands):
        """Record a Set2 command to be packed into the lo nibble.

        The caller MUST ensure we're in SET2_WIDE state (i.e., a Set1
        command that exits to SET2_WIDE was just written as the hi nibble
        of the current byte, and no Set2 command was yet packed in the lo
        nibble).

        Args:
            cmd: Set2 command nibble (0-15).
            operands: Extra bytes consumed by this Set2 command.
        """
        assert self.state == SET2_WIDE, \
            f"Can only write Set2 cmd in SET2_WIDE state, got state={self.state}"
        # Patch the lo nibble of the pending byte at the stored index
        assert self._pending_set2_byte is not None
        hi_nibble = self._pending_set2_byte >> 4
        self.data[self._pending_set2_idx] = (hi_nibble << 4) | (cmd & 0x0F)
        self.data.extend(self._set2_operands)
        self.data.extend(operands)
        self._pending_set2_idx = -1
        self._pending_set2_byte = None
        self._set2_operands = bytearray()
        # Set2 commands that exit to SET1 transition us
        self.state = SET1

    # ── Set1 command methods (emit to hi nibble) ─────────────────────

    def write_set1_to_set1(self, cmd, lo_operand, extra=b''):
        """Write a Set1 command that exits to SET1.

        lo_operand encodes in the lo nibble (count, offset-2, etc.).
        """
        assert self.state == SET1, f"Expected SET1 state, got {self.state}"
        self.data.append((cmd << 4) | (lo_operand & 0x0F))
        self.data.extend(extra)
        self.state = SET1
        return self

    def write_set1_to_set2_wide(self, cmd, extra=b''):
        """Write a Set1 command that exits to SET2_WIDE.

        The lo nibble is reserved for a Set2 command. Call a Set2 method
        AFTER this to fill the lo nibble, or call finish_byte() to zero it.
        """
        assert self.state == SET1, f"Expected SET1 state, got {self.state}"
        # Reserve: write byte with lo nibble = 0, will patch later
        self.data.append((cmd << 4) | 0)
        self.data.extend(extra)
        # Command byte is BEFORE the extra bytes we just appended
        self._pending_set2_idx = len(self.data) - 1 - len(extra)
        self._pending_set2_byte = self.data[self._pending_set2_idx]
        self._set2_operands = bytearray()
        self.state = SET2_WIDE
        return self

    def finish_byte(self):
        """Finish the current byte without a Set2 command (lo nibble = 0).
        Only needed if we wrote a Set1->SET2_WIDE cmd but don't want to
        pack a Set2 cmd. In practice, this is wasteful — prefer pairing.
        """
        if self.state == SET2_WIDE:
            self._pending_set2_idx = -1
            self._pending_set2_byte = None
            self._set2_operands = bytearray()
            self.state = SET1  # 0 nibble = copy_or_return_2 with count=0? no...
            # Actually lo nibble = 0 means copy_or_return_2 with count computed
            # from next byte's hi nibble. If we zero it, it'd read a byte and
            # check if hi nibble of that byte is 0 → terminate. Very dangerous.
            # So we should never call finish_byte without a real Set2 cmd.
            raise RuntimeError("Cannot finish byte without Set2 command — "
                               "lo nibble=0 is copy_or_return_2 which may terminate!")
        return self

    # ── Other Set1 commands (same as parent) ─────────────────────────

    def cmd_copy_or_return(self, count, literal_bytes):
        """Set1 cmd=0: copy_or_return. -> SET1"""
        assert self.state == SET1
        return super().cmd_copy_or_return(count, literal_bytes)

    def cmd_stream_byte_fill(self, count, fill_byte):
        """Set1 cmd=3: stream_byte_fill_1. -> SET1"""
        assert self.state == SET1
        return super().cmd_stream_byte_fill(count, fill_byte)

    def cmd_direct_byte_1_fill(self, count):
        """Set1 cmd=4: direct_byte_1_fill_1. -> SET1"""
        assert self.state == SET1
        return super().cmd_direct_byte_1_fill(count)

    def cmd_direct_byte_2_fill(self, count):
        """Set1 cmd=5: direct_byte_2_fill_1. -> SET1"""
        assert self.state == SET1
        return super().cmd_direct_byte_2_fill(count)

    def cmd_back_copy_word(self, offset):
        """Set1 cmd=9: back_copy_word_1. -> SET1"""
        assert self.state == SET1
        return super().cmd_back_copy_word(offset)

    def cmd_back_copy(self, count, offset_byte):
        """Set1 cmd=10: back_copy_1. -> SET1"""
        assert self.state == SET1
        return super().cmd_back_copy(count, offset_byte)

    def cmd_back_copy_arbitrary(self, count, b1, b2):
        """Set1 cmd=12: back_copy_arbitrary_1. -> SET1"""
        assert self.state == SET1
        return super().cmd_back_copy_arbitrary(count, b1, b2)

    def emit_terminator(self):
        """Emit end-of-stream marker. Must be in SET1 state."""
        assert self.state == SET1, f"Cannot terminate in state {self.state}"
        return super().emit_terminator()


# ---------------------------------------------------------------------------
# Greedy LZ77 + RLE compressor (Set1-only, legacy)
# ---------------------------------------------------------------------------

class GreedyCompressor:
    """Greedy PAC1 compressor using Set1-only commands.

    At each input position, evaluates possible commands and picks the one
    that consumes the most bytes per compressed byte.
    """

    def __init__(self, header=None, window_size=4096, min_match=3):
        if header is None:
            header = build_header()
        self.header = header
        self.fill1 = header[1]
        self.fill2 = header[2]
        self.window_size = window_size
        self.min_match = min_match

    def compress(self, data):
        """Compress data into PAC1 format (header + stream).

        Args:
            data: bytes to compress.

        Returns:
            bytes: header (39) + compressed stream.
        """
        writer = PAC1Writer()
        pos = 0
        data_len = len(data)

        while pos < data_len:
            remaining = data_len - pos
            best = self._find_best(data, pos, remaining)

            cmd_type = best['type']
            consumed = best['consumed']

            if cmd_type == 'literal':
                writer.cmd_copy_or_return(consumed, data[pos:pos + consumed])
            elif cmd_type == 'rle_stream':
                writer.cmd_stream_byte_fill(consumed, data[pos])
            elif cmd_type == 'rle_fill1':
                writer.cmd_direct_byte_1_fill(consumed)
            elif cmd_type == 'rle_fill2':
                writer.cmd_direct_byte_2_fill(consumed)
            elif cmd_type == 'back_copy_word':
                writer.cmd_back_copy_word(best['offset'])
            elif cmd_type == 'back_copy':
                writer.cmd_back_copy(consumed, best['offset'])
            elif cmd_type == 'back_copy_arbitrary':
                writer.cmd_back_copy_arbitrary(consumed,
                                               (best['offset'] >> 8) & 0xFF,
                                               best['offset'] & 0xFF)
            pos += consumed

        writer.emit_terminator()
        return self.header + writer.get_data()

    def _find_best(self, data, pos, remaining):
        """Find the best command at position pos.

        Returns dict with 'type', 'consumed', and optionally 'offset'.
        """
        candidates = []

        # 1. RLE with stream byte (cmd=3)
        if remaining >= 3:
            run = self._run_length(data, pos, min(remaining, 18))
            if run >= 3:
                candidates.append({
                    'type': 'rle_stream',
                    'consumed': run,
                    'ratio': run / 2,  # 1 cmd byte + 1 fill byte
                })

        # 2. RLE with fill1 (cmd=4)
        if remaining >= 3:
            run = self._run_length_value(data, pos, min(remaining, 18), self.fill1)
            if run >= 3:
                candidates.append({
                    'type': 'rle_fill1',
                    'consumed': run,
                    'ratio': run / 1,  # 1 cmd byte only
                })

        # 3. RLE with fill2 (cmd=5)
        if remaining >= 3:
            run = self._run_length_value(data, pos, min(remaining, 18), self.fill2)
            if run >= 3:
                candidates.append({
                    'type': 'rle_fill2',
                    'consumed': run,
                    'ratio': run / 1,
                })

        # 4. Back-reference match
        if remaining >= self.min_match and pos > 0:
            match = self._find_longest_match(data, pos, remaining)
            if match is not None:
                match_len, match_off = match
                # back_copy_word (cmd=9): offset 2-17, copies 2 bytes
                if 2 <= match_off <= 17 and match_len >= 2:
                    candidates.append({
                        'type': 'back_copy_word',
                        'consumed': 2,
                        'offset': match_off,
                        'ratio': 2 / 1,
                    })
                # back_copy (cmd=10): count 3-18, 1-byte offset
                if 3 <= match_len <= 18:
                    off = match_off - match_len
                    if 0 <= off <= 0xFF:
                        candidates.append({
                            'type': 'back_copy',
                            'consumed': match_len,
                            'offset': off,
                            'ratio': match_len / 2,
                        })
                # back_copy_arbitrary (cmd=12): count 3-18, 2-byte offset
                if 3 <= match_len <= 18 and 0 <= match_off <= 0xFFFF:
                    candidates.append({
                        'type': 'back_copy_arbitrary',
                        'consumed': match_len,
                        'offset': match_off,
                        'ratio': match_len / 3,
                    })

        # 5. Literal fallback (cmd=0): always available
        chunk = min(remaining, 15)
        candidates.append({
            'type': 'literal',
            'consumed': chunk,
            'ratio': chunk / (1 + chunk),
        })

        candidates.sort(key=lambda c: (-c['ratio'], -c['consumed']))
        return candidates[0]

    # ── Helpers ──────────────────────────────────────────────────────

    @staticmethod
    def _run_length(data, pos, max_len):
        if pos >= len(data):
            return 0
        val = data[pos]
        count = 1
        limit = min(pos + max_len, len(data))
        while pos + count < limit and data[pos + count] == val:
            count += 1
        return count

    @staticmethod
    def _run_length_value(data, pos, max_len, value):
        count = 0
        limit = min(pos + max_len, len(data))
        while pos + count < limit and data[pos + count] == value:
            count += 1
        return count

    def _find_longest_match(self, data, pos, max_len):
        window_start = max(0, pos - self.window_size)
        best_len = 0
        best_off = 0
        max_match = min(max_len, 18)

        for search_pos in range(window_start, pos):
            if data[search_pos] != data[pos]:
                continue
            ml = 1
            while (pos + ml < len(data) and ml < max_match
                   and data[search_pos + ml] == data[pos + ml]):
                ml += 1
            if ml > best_len:
                best_len = ml
                best_off = pos - search_pos

        if best_len >= self.min_match:
            return best_len, best_off
        return None


# ---------------------------------------------------------------------------
# Enhanced greedy compressor with Set2 support
# ---------------------------------------------------------------------------

class EnhancedGreedyCompressor(GreedyCompressor):
    """Greedy PAC1 compressor with Set2 command optimization.

    Uses the same greedy approach as GreedyCompressor but additionally
    evaluates Set1+Set2 command pairs that can be packed into a single
    command byte (hi nibble = Set1, lo nibble = Set2).

    The compression works in two modes:
    1. Pure Set1 mode (same as GreedyCompressor, used as baseline)
    2. Set1+Set2 packed mode (tries to pair commands)

    For each position, evaluates:
    - Best single Set1 command
    - Best Set1→SET2_WIDE command followed by Set2→SET1 command
    Picks the option with the best byte-per-output ratio.
    """

    def __init__(self, header=None, window_size=4096, min_match=3,
                 use_set2=True):
        super().__init__(header, window_size, min_match)
        self.use_set2 = use_set2

    def compress(self, data):
        if not self.use_set2:
            return super().compress(data)

        writer = Set2PAC1Writer()
        pos = 0
        data_len = len(data)

        while pos < data_len:
            remaining = data_len - pos
            best = self._find_best_set2(data, pos, remaining, writer)

            if best is None:
                # Fallback: pure Set1 encoding
                best = self._find_best(data, pos, remaining)

            cmd_type = best['type']
            consumed = best['consumed']

            if cmd_type == 'literal':
                writer.cmd_copy_or_return(consumed, data[pos:pos + consumed])
            elif cmd_type == 'rle_stream':
                writer.cmd_stream_byte_fill(consumed, data[pos])
            elif cmd_type == 'rle_fill1':
                writer.cmd_direct_byte_1_fill(consumed)
            elif cmd_type == 'rle_fill2':
                writer.cmd_direct_byte_2_fill(consumed)
            elif cmd_type == 'back_copy_word':
                writer.cmd_back_copy_word(best['offset'])
            elif cmd_type == 'back_copy':
                writer.cmd_back_copy(consumed, best['offset'])
            elif cmd_type == 'back_copy_arbitrary':
                writer.cmd_back_copy_arbitrary(consumed,
                                               (best['offset'] >> 8) & 0xFF,
                                               best['offset'] & 0xFF)
            elif cmd_type == 'pair':
                # Packed pair: the writer handles both
                s1_type = best['s1_type']
                s1_consumed = best['s1_consumed']
                s2_type = best['s2_type']
                s2_consumed = best['s2_consumed']

                # Write Set1->SET2_WIDE first
                # (the writer saves room for Set2 lo nibble)
                self._emit_set1_to_wide(writer, s1_type, data, pos,
                                        s1_consumed, best)
                # Then write Set2->SET1 in the lo nibble
                self._emit_set2_to_set1(writer, s2_type, data,
                                        pos + s1_consumed, s2_consumed, best)
            else:
                raise ValueError(f"Unknown cmd_type: {cmd_type}")

            pos += consumed

        writer.emit_terminator()
        return self.header + writer.get_data()

    def _emit_set1_to_wide(self, writer, s1_type, data, pos, consumed, best):
        """Emit a Set1 command that exits to SET2_WIDE, reserving lo nibble."""
        if s1_type == 'direct_word_put':
            writer.write_set1_to_set2_wide(6)
        elif s1_type == 'direct_byte_1_put':
            writer.write_set1_to_set2_wide(7)
        elif s1_type == 'direct_byte_2_put':
            writer.write_set1_to_set2_wide(8)
        elif s1_type == 'duplicate_byte':
            writer.write_set1_to_set2_wide(13)
        elif s1_type == 'duplicate_word':
            writer.write_set1_to_set2_wide(14)
        else:
            raise ValueError(f"Unsupported Set1→SET2_WIDE type: {s1_type}")

    def _emit_set2_to_set1(self, writer, s2_type, data, pos, consumed, best):
        """Emit a Set2 command that exits to SET1, filling the lo nibble."""
        if s2_type == 'stream_byte':
            writer.cmd_stream_byte_2(data[pos])
        elif s2_type == 'stream_word':
            writer.cmd_stream_word_2(data[pos], data[pos + 1])
        elif s2_type == 'direct_word_put':
            writer.cmd_direct_word_put_2()
        elif s2_type == 'direct_byte_1_put':
            writer.cmd_direct_byte_1_put_2()
        elif s2_type == 'direct_byte_2_put':
            writer.cmd_direct_byte_2_put_2()
        elif s2_type == 'duplicate_byte':
            writer.cmd_duplicate_byte_2()
        elif s2_type == 'duplicate_word':
            writer.cmd_duplicate_word_2()
        else:
            raise ValueError(f"Unsupported Set2→SET1 type: {s2_type}")

    def _find_best_set2(self, data, pos, remaining, writer):
        """Find the best Set2-optimized command at position pos.

        Returns candidate dict for packed pairs, or None if Set1-only
        is better than any pair.
        """
        # Only evaluate pairs when in SET1 state
        if writer.state != SET1:
            return None

        candidates = []

        # Evaluate Set1 -> SET2_WIDE candidates
        s1_wide_candidates = self._find_set1_to_wide(data, pos, remaining)

        for s1_cand in s1_wide_candidates:
            s1_consumed = s1_cand['consumed']
            s1_comp_size = s1_cand['comp_size']  # operand bytes

            if remaining <= s1_consumed:
                # No room for Set2 command
                continue

            # Find a Set2->SET1 candidate after this
            s2_pos = pos + s1_consumed
            s2_remaining = remaining - s1_consumed
            s2_candidates = self._find_set2_to_set1(data, s2_pos, s2_remaining)

            for s2_cand in s2_candidates:
                s2_consumed = s2_cand['consumed']
                s2_comp_size = s2_cand['comp_size']

                total_consumed = s1_consumed + s2_consumed
                # Packed: 1 command byte + s1 operands + s2 operands
                total_comp_size = 1 + s1_comp_size + s2_comp_size
                ratio = total_consumed / total_comp_size if total_comp_size > 0 else 0

                candidates.append({
                    'type': 'pair',
                    'consumed': total_consumed,
                    'ratio': ratio,
                    's1_type': s1_cand['cmd_type'],
                    's1_consumed': s1_consumed,
                    's2_type': s2_cand['cmd_type'],
                    's2_consumed': s2_consumed,
                    's1_offset': s1_cand.get('offset'),
                    's2_offset': s2_cand.get('offset'),
                })

        if not candidates:
            return None

        candidates.sort(key=lambda c: (-c['ratio'], -c['consumed']))

        # Compare packed best vs Set1-only best
        set1_best = self._find_best(data, pos, remaining)
        if set1_best['ratio'] >= candidates[0]['ratio']:
            return None  # Set1 is at least as good

        return candidates[0]

    def _find_set1_to_wide(self, data, pos, remaining):
        """Find Set1 commands that exit to SET2_WIDE.

        Only returns commands that can correctly encode the data at pos.
        Direct/duplicate commands check that the actual data matches
        what the command would produce.
        """
        candidates = []
        dirw = struct.unpack('<H', self.header[5:7])[0]

        # cmd 6: direct_word_put_1 — emit hdr word, comp_size=0
        if remaining >= 2 and data[pos:pos+2] == struct.pack('<H', dirw):
            candidates.append({
                'cmd_type': 'direct_word_put',
                'consumed': 2,
                'comp_size': 0,
            })

        # cmd 7: direct_byte_1_put_1 — emit dir1, comp_size=0
        if remaining >= 1 and data[pos] == self.header[3]:
            candidates.append({
                'cmd_type': 'direct_byte_1_put',
                'consumed': 1,
                'comp_size': 0,
            })

        # cmd 8: direct_byte_2_put_1 — emit dir2, comp_size=0
        if remaining >= 1 and data[pos] == self.header[4]:
            candidates.append({
                'cmd_type': 'direct_byte_2_put',
                'consumed': 1,
                'comp_size': 0,
            })

        # cmd 13: duplicate_byte_1 — dup last byte, comp_size=0
        # Valid when current byte matches previous data byte
        if remaining >= 1 and pos >= 1 and data[pos] == data[pos - 1]:
            candidates.append({
                'cmd_type': 'duplicate_byte',
                'consumed': 1,
                'comp_size': 0,
            })

        # cmd 14: duplicate_word_1 — dup last word, comp_size=0
        if remaining >= 2 and pos >= 2 and data[pos:pos+2] == data[pos-2:pos]:
            candidates.append({
                'cmd_type': 'duplicate_word',
                'consumed': 2,
                'comp_size': 0,
            })

        # NOTE: cmd 11 (back_copy_far_1) exits to SET2_WIDE but uses the lo
        # nibble for count-3. It CANNOT be packed with a Set2 command because
        # the lo nibble would be overwritten, corrupting the count.
        # So it's intentionally excluded from Set1->SET2_WIDE candidates.

        return candidates

    def _find_set2_to_set1(self, data, pos, remaining):
        """Find Set2 commands that exit to SET1.

        Only includes direct/duplicate commands when the data at pos
        actually matches what the command would produce.
        """
        candidates = []
        dirw = struct.unpack('<H', self.header[5:7])[0]

        # cmd 1: stream_byte_2 — always valid, encodes literal byte
        if remaining >= 1:
            candidates.append({
                'cmd_type': 'stream_byte',
                'consumed': 1,
                'comp_size': 1,
            })

        # cmd 2: stream_word_2 — always valid, encodes 2 literal bytes
        if remaining >= 2:
            candidates.append({
                'cmd_type': 'stream_word',
                'consumed': 2,
                'comp_size': 2,
            })

        # cmd 6: direct_word_put_2 — emit hdr word, only if data matches
        if remaining >= 2 and data[pos:pos+2] == struct.pack('<H', dirw):
            candidates.append({
                'cmd_type': 'direct_word_put',
                'consumed': 2,
                'comp_size': 0,
            })

        # cmd 7: direct_byte_1_put_2 — emit dir1, only if data matches
        if remaining >= 1 and data[pos] == self.header[3]:
            candidates.append({
                'cmd_type': 'direct_byte_1_put',
                'consumed': 1,
                'comp_size': 0,
            })

        # cmd 8: direct_byte_2_put_2 — emit dir2, only if data matches
        if remaining >= 1 and data[pos] == self.header[4]:
            candidates.append({
                'cmd_type': 'direct_byte_2_put',
                'consumed': 1,
                'comp_size': 0,
            })

        # cmd 13: duplicate_byte_2 — dup last byte, only if matches
        if remaining >= 1 and pos >= 1 and data[pos] == data[pos - 1]:
            candidates.append({
                'cmd_type': 'duplicate_byte',
                'consumed': 1,
                'comp_size': 0,
            })

        # cmd 14: duplicate_word_2 — dup last word, only if matches
        if remaining >= 2 and pos >= 2 and data[pos:pos+2] == data[pos-2:pos]:
            candidates.append({
                'cmd_type': 'duplicate_word',
                'consumed': 2,
                'comp_size': 0,
            })

        return candidates


# ---------------------------------------------------------------------------
# Convenience compress function (auto-sets use_set2 based on header fill bytes)
# ---------------------------------------------------------------------------

def compress(data, header=None, use_set2=True, simple=False):
    """Compress data into PAC1 format.

    Args:
        data: Bytes to compress.
        header: 39-byte PAC1 header (default: built from zeros).
        use_set2: Use Set2-enhanced compression (default: True).
        simple: Force Set1-only compression (overrides use_set2).

    Returns:
        bytes: Header (39) + compressed stream.
    """
    if header is None:
        header = build_header()
    if simple:
        compressor = GreedyCompressor(header=header)
    elif use_set2:
        compressor = EnhancedGreedyCompressor(header=header, use_set2=True)
    else:
        compressor = GreedyCompressor(header=header)
    return compressor.compress(data)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_hex_int(s):
    """Parse hex integer (e.g., '0xFF' or 'FF')."""
    if s.startswith('0x') or s.startswith('0X'):
        return int(s, 16)
    return int(s, 16)


def main():
    parser = argparse.ArgumentParser(
        description='DKC2 PAC1 (Big Data) compressor / decompressor')

    io_group = parser.add_argument_group('I/O')
    io_group.add_argument('--input', '-i',
                          help='Input file (default: stdin)')
    io_group.add_argument('--output', '-o',
                          help='Output file (default: stdout)')
    io_group.add_argument('--decompress', '-d', action='store_true',
                          help='Decompress instead of compress')

    compress_group = parser.add_argument_group('Compression options')
    compress_group.add_argument('--simple', action='store_true',
                                help='Use Set1-only compression (v1)')
    compress_group.add_argument('--no-set2', action='store_true',
                                help='Disable Set2 optimization')

    header_group = parser.add_argument_group('Header options (compress)')
    header_group.add_argument('--fill1', type=parse_hex_int, default='0x00',
                              help='Fill byte 1 (hex, default: 0x00)')
    header_group.add_argument('--fill2', type=parse_hex_int, default='0x00',
                              help='Fill byte 2 (hex, default: 0x00)')
    header_group.add_argument('--dir1', type=parse_hex_int, default='0x00',
                              help='Direct byte 1 (hex, default: 0x00)')
    header_group.add_argument('--dir2', type=parse_hex_int, default='0x00',
                              help='Direct byte 2 (hex, default: 0x00)')
    header_group.add_argument('--dirw', type=parse_hex_int, default='0x0000',
                              help='Direct word (hex, default: 0x0000)')
    header_group.add_argument('--header',
                              help='Read 39-byte header from file')

    args = parser.parse_args()

    # Read input
    if args.input:
        with open(args.input, 'rb') as f:
            input_data = f.read()
    else:
        input_data = sys.stdin.buffer.read()

    if args.decompress:
        from decode_pac1 import decompress as pac1_decompress
        offset = 0
        if input_data[:4] == b'PAC1':
            offset = 4
        result = pac1_decompress(input_data, offset)
        if result is None:
            print('Decompression failed.', file=sys.stderr)
            sys.exit(1)
    else:
        if args.header:
            with open(args.header, 'rb') as f:
                header = f.read(39)
            if len(header) < 39:
                print('Header file must be 39 bytes.', file=sys.stderr)
                sys.exit(1)
        else:
            header = build_header(
                fill1=args.fill1 & 0xFF,
                fill2=args.fill2 & 0xFF,
                dir1=args.dir1 & 0xFF,
                dir2=args.dir2 & 0xFF,
                dirw=args.dirw & 0xFFFF,
            )

        if args.simple:
            compressor = GreedyCompressor(header=header)
        else:
            compressor = EnhancedGreedyCompressor(
                header=header, use_set2=not args.no_set2)
        result = compressor.compress(input_data)

    if args.output:
        with open(args.output, 'wb') as f:
            f.write(result)
    else:
        sys.stdout.buffer.write(result)


if __name__ == '__main__':
    main()
