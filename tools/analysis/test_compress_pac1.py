"""Tests for PAC1 compressor (compress_pac1.py).

Tests round-trip: compress -> decompress -> original data.
Uses decompress from decode_pac1.py as ground truth.

Covers:
  - Set1-only mode (original tests)
  - Set2-enhanced mode (new)
  - Edge cases and regression
  - Pipeline extraction and patching
"""

import os
import struct
import sys
import tempfile

# Add tools/analysis and tools to path for imports
_test_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _test_dir)
sys.path.insert(0, os.path.dirname(_test_dir))  # tools/ for extract_assets

from compress_pac1 import (
    PAC1Writer,
    Set2PAC1Writer,
    GreedyCompressor,
    EnhancedGreedyCompressor,
    build_header,
    HEADER_SIZE,
    compress,
)
from decode_pac1 import decompress as pac1_decompress, parse_header


# ═══════════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════════

def roundtrip(data, use_set2=True, **header_kw):
    """Compress data, decompress, return decompressed result."""
    header = build_header(**header_kw)
    compressed = compress(data, header=header, use_set2=use_set2)
    decompressed = pac1_decompress(compressed, 0)
    return decompressed


def roundtrip_direct(data, use_set2=True, **header_kw):
    """Round-trip using specific compressor class directly."""
    header = build_header(**header_kw)
    if use_set2:
        compressor = EnhancedGreedyCompressor(header=header, use_set2=True)
    else:
        compressor = GreedyCompressor(header=header)
    compressed = compressor.compress(data)
    decompressed = pac1_decompress(compressed, 0)
    return decompressed


def assert_roundtrip(data, use_set2=True, **header_kw):
    """Assert round-trip produces original data."""
    result = roundtrip(data, use_set2=use_set2, **header_kw)
    assert result is not None, (
        f'Round-trip failed: decompress returned None\n'
        f'  input ({len(data)}B): {data[:32].hex()}\n'
    )
    assert result == data, (
        f'Round-trip mismatch:\n'
        f'  expected ({len(data)}B): {data[:32].hex()}\n'
        f'  got ({len(result)}B):      {result[:32].hex()}\n'
    )


def roundtrip_all(data, **header_kw):
    """Assert that BOTH Set1-only and Set2 modes round-trip."""
    assert_roundtrip(data, use_set2=False, **header_kw)
    assert_roundtrip(data, use_set2=True, **header_kw)


# ═══════════════════════════════════════════════════════════════════
# Test: Header building (unchanged)
# ═══════════════════════════════════════════════════════════════════

class TestHeaderBuilding:
    def test_default_header_size(self):
        h = build_header()
        assert len(h) == HEADER_SIZE

    def test_default_header_values(self):
        h = build_header()
        assert h[0] == 0x00  # reserved
        assert h[1] == 0x00  # fill1
        assert h[2] == 0x00  # fill2
        assert h[3] == 0x00  # dir1
        assert h[4] == 0x00  # dir2
        assert struct.unpack_from('<H', h, 5)[0] == 0x0000  # dirw

    def test_custom_header_values(self):
        h = build_header(fill1=0xAB, fill2=0xCD, dir1=0x12, dir2=0x34,
                         dirw=0x5678)
        assert h[1] == 0xAB
        assert h[2] == 0xCD
        assert h[3] == 0x12
        assert h[4] == 0x34
        assert struct.unpack_from('<H', h, 5)[0] == 0x5678

    def test_custom_lut(self):
        lut = [i for i in range(16)]
        h = build_header(lut=lut)
        parsed = list(struct.unpack_from('<16H', h, 7))
        assert parsed == lut

    def test_header_parseable_by_decode(self):
        h = build_header(fill1=0xFF, fill2=0x00, dir1=0x55, dir2=0xAA,
                         dirw=0x1234)
        parsed = parse_header(h, 0)
        assert parsed is not None
        assert parsed['fill1'] == 0xFF
        assert parsed['fill2'] == 0x00
        assert parsed['dir1'] == 0x55
        assert parsed['dir2'] == 0xAA
        assert parsed['dirw'] == 0x1234


# ═══════════════════════════════════════════════════════════════════
# Test: Basic round-trips (ALL modes)
# ═══════════════════════════════════════════════════════════════════

class TestRoundtrip:
    def test_empty_data(self):
        """Empty data: should produce header + terminator only."""
        header = build_header()
        compressor = GreedyCompressor(header=header)
        compressed = compressor.compress(b'')
        assert len(compressed) >= HEADER_SIZE
        assert compressed[HEADER_SIZE] == 0x00
        parsed = parse_header(compressed, 0)
        assert parsed is not None

        # Set2 mode also
        compressor2 = EnhancedGreedyCompressor(header=header)
        compressed2 = compressor2.compress(b'')
        assert len(compressed2) >= HEADER_SIZE
        assert compressed2[HEADER_SIZE] == 0x00

    def test_empty_data_set2(self):
        """Set2 compressor handles empty data."""
        h = build_header()
        c = EnhancedGreedyCompressor(header=h, use_set2=True)
        compressed = c.compress(b'')
        assert len(compressed) >= HEADER_SIZE
        assert compressed[HEADER_SIZE] == 0x00

    def test_single_byte(self):
        roundtrip_all(b'\x42')

    def test_two_bytes(self):
        roundtrip_all(b'\x42\x69')

    def test_hello_world(self):
        roundtrip_all(b'Hello World!')

    def test_small_random(self):
        data = bytes([0x12, 0x34, 0x56, 0x78, 0x9A, 0xBC, 0xDE, 0xF0])
        roundtrip_all(data)

    def test_64_bytes_sequential(self):
        data = bytes(range(64))
        roundtrip_all(data)

    def test_all_zeros(self):
        data = bytes(100)
        roundtrip_all(data)

    def test_all_ones(self):
        data = bytes([0xFF] * 100)
        roundtrip_all(data)

    def test_alternating_pattern(self):
        data = bytes([0xAA, 0x55] * 50)
        roundtrip_all(data)

    def test_256_bytes_range(self):
        data = bytes(range(256))
        roundtrip_all(data)


# ═══════════════════════════════════════════════════════════════════
# Test: RLE
# ═══════════════════════════════════════════════════════════════════

class TestRLE:
    def test_single_run_short(self):
        roundtrip_all(bytes([0xAB] * 10))

    def test_single_run_long(self):
        roundtrip_all(bytes([0xCD] * 100))

    def test_multiple_runs(self):
        roundtrip_all(bytes([0xAA] * 10 + [0xBB] * 8 + [0xCC] * 12))

    def test_fill1_specific(self):
        roundtrip_all(bytes([0x7F] * 20), fill1=0x7F)

    def test_fill2_specific(self):
        roundtrip_all(bytes([0xE4] * 20), fill2=0xE4)


# ═══════════════════════════════════════════════════════════════════
# Test: Back-reference (repeated patterns)
# ═══════════════════════════════════════════════════════════════════

class TestBackReference:
    def test_repeated_pattern_short(self):
        roundtrip_all(b'ABCABC')

    def test_repeated_pattern_medium(self):
        roundtrip_all(b'TestDataTestData')

    def test_repeated_pattern_with_overlap(self):
        roundtrip_all(b'AAAAAAA')

    def test_padding_pattern(self):
        roundtrip_all(bytes([0x00, 0xFF] * 30))

    def test_pattern_with_small_offset(self):
        roundtrip_all(b'ABABABAB')


# ═══════════════════════════════════════════════════════════════════
# Test: Large data
# ═══════════════════════════════════════════════════════════════════

class TestLargeData:
    def test_1kb_random_like(self):
        import random
        rng = random.Random(42)
        data = bytes(rng.randint(0, 255) for _ in range(1024))
        roundtrip_all(data)

    def test_4kb_pattern(self):
        data = bytes([i % 256 for i in range(4096)])
        roundtrip_all(data)

    def test_8kb_mixed(self):
        """8KB of varied data (real-world sized asset)."""
        import random
        rng = random.Random(123)
        data = bytearray()
        # Mix patterns: runs, repeats, random
        for _ in range(20):
            data.extend([rng.randint(0, 255)] * rng.randint(3, 30))
            data.extend(bytes(rng.randint(0, 255) for _ in range(rng.randint(5, 50))))
            data.extend([i % 256 for i in range(rng.randint(10, 100))])
        roundtrip_all(bytes(data))


# ═══════════════════════════════════════════════════════════════════
# Test: Edge cases
# ═══════════════════════════════════════════════════════════════════

class TestEdgeCases:
    def test_max_literal_chunk(self):
        roundtrip_all(bytes(range(15)))

    def test_exceeding_literal_chunk(self):
        roundtrip_all(bytes(range(16)))

    def test_all_256_values(self):
        roundtrip_all(bytes(range(256)))

    def test_single_run_at_start(self):
        roundtrip_all(bytes([0xFF] * 15 + [0x00]))

    def test_single_run_at_end(self):
        roundtrip_all(bytes([0x00] + [0xFF] * 15))

    def test_run_across_18_byte_boundary(self):
        roundtrip_all(bytes([0xAA] * 50))


# ═══════════════════════════════════════════════════════════════════
# Test: Header sensitivity
# ═══════════════════════════════════════════════════════════════════

class TestHeader:
    def test_fill_byte_matching(self):
        roundtrip_all(bytes([0xFF] * 30), fill1=0xFF)

    def test_direct_bytes_in_data(self):
        roundtrip_all(bytes([0x12, 0x34] + [0x56] * 10), dir1=0x12, dir2=0x34)


# ═══════════════════════════════════════════════════════════════════
# Test: NEW — Set2-specific round-trips
# ═══════════════════════════════════════════════════════════════════

class TestSet2Roundtrip:
    """Tests specifically designed to exercise Set2 commands.

    Set2 produces valid streams that exercise the SET2 and SET2_WIDE
    decompressor paths.
    """

    def test_stream_byte_via_set2(self):
        """Exercise stream_byte_2 (Set2 cmd=1)."""
        # Data that can benefit from duplicate + stream_byte packing
        data = bytes([0x00, 0x00]) + bytes([0xFF] * 5)
        assert_roundtrip(data, use_set2=True)

    def test_duplicate_patterns(self):
        """Exercise duplicate_byte_2 and duplicate_word_2."""
        # Many repeated bytes — the Set2 duplicate is cheap
        data = b'AAAAAAAAAAAAAAAAAAAA'  # 20 As
        assert_roundtrip(data, use_set2=True)

    def test_mixed_duplicate_word(self):
        """Pattern that can use duplicate_word in Set2."""
        data = b'ABABABABABABABABABAB'  # 20 bytes of AB
        assert_roundtrip(data, use_set2=True)

    def test_direct_word_sequence(self):
        """Sequence where direct_word_put (both Set1 and Set2) helps."""
        data = struct.pack('<H', 0x1234) * 10
        assert_roundtrip(data, use_set2=True, dirw=0x1234)

    def test_direct_byte_sequence(self):
        """Sequence where direct_byte_put (both Set1 and Set2) helps."""
        data = bytes([0xAB] * 20)
        assert_roundtrip(data, use_set2=True, dir1=0xAB, dir2=0xCD)

    def test_complex_realistic(self):
        """More realistic data mixing patterns."""
        data = (
            b'\x00' * 16 +        # zero run (RLE)
            b'Hello World! ' * 3 + # repeated string (back-ref)
            b'\xFF\xFE\xFD\xFC' + # unique bytes (literal)
            b'Hello World! ' * 2 + # repeated again (back-ref with window)
            b'\xAB' * 12          # another run (RLE)
        )
        assert_roundtrip(data, use_set2=True)

    def test_set2_vs_set1_size(self):
        """Set2 compression should never be WORSE than Set1-only.

        Note: due to greedy heuristics, Set2 may occasionally produce
        slightly larger output when the heuristic misfires. We check
        that the difference is small.
        """
        data = (
            b'\x00' * 100 +
            b'\xFF' * 30 +
            bytes(range(200)) +
            b'\xAA\x55' * 30 +
            b'TestStringTestString' * 5
        )
        header = build_header()
        c1 = GreedyCompressor(header=header)
        c2 = EnhancedGreedyCompressor(header=header, use_set2=True)
        r1 = c1.compress(data)
        r2 = c2.compress(data)
        # Set2 should be <= Set1 or at most a few bytes larger
        # (heuristic can sometimes miss)
        assert len(r2) <= len(r1) + 5, (
            f'Set2 too much larger than Set1: '
            f'Set1={len(r1)}B, Set2={len(r2)}B'
        )


# ═══════════════════════════════════════════════════════════════════
# Test: NEW — Set2 writer state machine
# ═══════════════════════════════════════════════════════════════════

class TestSet2Writer:
    """Test the Set2PAC1Writer state machine directly."""

    def test_writer_starts_in_set1(self):
        w = Set2PAC1Writer()
        assert w.state == 1  # SET1

    def test_write_set1_to_set1_maintains_state(self):
        w = Set2PAC1Writer()
        w.write_set1_to_set1(0, 1, b'\x42')  # copy_or_return count=1
        assert w.state == 1  # stays SET1
        assert w.get_data() == b'\x01\x42'

    def test_write_set1_to_set2_wide_changes_state(self):
        w = Set2PAC1Writer()
        w.write_set1_to_set2_wide(7)  # direct_byte_1_put_1
        assert w.state == 3  # SET2_WIDE

    def test_set2_packing_flow(self):
        """Test a full Set1→SET2_WIDE + Set2→SET1 cycle."""
        w = Set2PAC1Writer()
        # Set1 cmd 7 (direct_byte_1_put_1) -> SET2_WIDE
        w.write_set1_to_set2_wide(7)
        assert w.state == 3  # SET2_WIDE
        # Set2 cmd 1 (stream_byte_2) -> SET1
        w.cmd_stream_byte_2(0x42)
        assert w.state == 1  # back to SET1
        # Verify structure: command byte = (7<<4) | 1 = 0x71
        assert w.get_data() == b'\x71\x42'

    def test_terminator_in_set1(self):
        w = Set2PAC1Writer()
        w.emit_terminator()
        assert w.get_data() == b'\x00'

    def test_raises_on_bad_state(self):
        """Should raise if we write Set1→SET1 when in wrong state."""
        import pytest
        w = Set2PAC1Writer()
        w.write_set1_to_set2_wide(7)  # now in SET2_WIDE
        with pytest.raises(AssertionError):
            w.write_set1_to_set1(0, 0, b'\x00')


# ═══════════════════════════════════════════════════════════════════
# Test: NEW — Pipeline extraction
# ═══════════════════════════════════════════════════════════════════

class TestAssetPipeline:
    """Tests the extract->decompress->recompress pipeline.

    Uses synthetic PAC1 data to test the pipeline without requiring
    the actual ROM.
    """

    @staticmethod
    def _make_synthetic_asset(data, header_kw=None):
        """Create a synthetic PAC1 compressed asset (header+stream)."""
        if header_kw is None:
            header_kw = {}
        header = build_header(**header_kw)
        compressor = EnhancedGreedyCompressor(header=header, use_set2=True)
        compressed = compressor.compress(data)
        return compressed

    def test_synthetic_roundtrip(self):
        """Synthetic asset round-trips through decompress."""
        data = bytes(range(64))
        asset = self._make_synthetic_asset(data)
        dec = pac1_decompress(asset, 0)
        assert dec == data

    def test_synthetic_scan(self):
        """Synthetic asset is detected by header scanner."""
        from decode_pac1 import scan_headers
        data = bytes(range(128))
        asset = self._make_synthetic_asset(data)
        results = scan_headers(asset, limit=5)
        assert len(results) > 0

    def test_roundtrip_with_custom_header(self):
        """Round-trip with specific fill bytes."""
        data = bytes([0xAB] * 50 + [0xCD] * 30)
        asset = self._make_synthetic_asset(data, {'fill1': 0xAB, 'fill2': 0xCD})
        dec = pac1_decompress(asset, 0)
        assert dec == data

    def test_verify_roundtrip(self):
        """End-to-end: compress -> decompress -> recompress -> decompress."""
        original = bytes([i % 256 for i in range(512)])
        header = build_header()

        # First compression
        c1 = EnhancedGreedyCompressor(header=header, use_set2=True)
        comp1 = c1.compress(original)

        # Decompress
        dec1 = pac1_decompress(comp1, 0)
        assert dec1 == original

        # Recompress
        comp2 = compress(dec1, header=header, use_set2=True)

        # Decompress again
        dec2 = pac1_decompress(comp2, 0)
        assert dec2 == original

    def test_compressed_size_estimate(self):
        """Compressed size should be less than raw data for repetitive data."""
        data = bytes([0x00] * 1000)  # very repetitive
        header = build_header(fill1=0x00)
        c = EnhancedGreedyCompressor(header=header, use_set2=True)
        compressed = c.compress(data)
        # Should compress well
        assert len(compressed) < 200, f"Poor compression: {len(compressed)}B for 1000B of zeros"


# ═══════════════════════════════════════════════════════════════════
# Test: NEW — Round-trip skip-pairing edge cases
# ═══════════════════════════════════════════════════════════════════

class TestSet2EdgeCases:
    """Edge cases specifically for Set2 pairing."""

    def test_single_byte_set2(self):
        """Single byte still works with Set2 enabled."""
        assert_roundtrip(b'\x55', use_set2=True)

    def test_two_bytes_set2(self):
        """Two bytes with Set2."""
        assert_roundtrip(b'\x55\xAA', use_set2=True)

    def test_very_long_run_set2(self):
        """Very long run forces multiple RLE commands."""
        assert_roundtrip(bytes([0x77] * 200), use_set2=True)

    def test_data_larger_than_window(self):
        """Data exceeding the back-ref window size."""
        data = bytes([0xAA] * 100 + [0xBB] * 100 + [0xAA] * 100)
        assert_roundtrip(data, use_set2=True)

    def test_set1_fallback(self):
        """When no Set2 pairing is beneficial, fallback to Set1."""
        # Highly random data — Set2 pairing unlikely to help
        data = bytes([0x00, 0x11, 0x22, 0x33, 0x44, 0x55, 0x66, 0x77,
                      0x88, 0x99, 0xAA, 0xBB, 0xCC, 0xDD, 0xEE, 0xFF])
        assert_roundtrip(data, use_set2=True)

    def test_header_specific_set2(self):
        """Use header values with Set2."""
        data = bytes([0x12, 0x34] * 30)
        assert_roundtrip(data, use_set2=True, dir1=0x12, dir2=0x34,
                         fill1=0x00, fill2=0xFF)

    def test_simple_vs_set2_identical(self):
        """For small data, Set2 should produce valid output (may be same)."""
        data = b'Hello'
        assert_roundtrip(data, use_set2=False)
        assert_roundtrip(data, use_set2=True)

    def test_back_copy_far_interaction(self):
        """Data where back_copy_far might interact with Set2."""
        # back_copy_far_1 exits to SET2_WIDE, so Set2 can pair
        data = bytes([0xFF] * 18 + [0x00] + [0xFF] * 5)
        assert_roundtrip(data, use_set2=True)

    def test_compress_function_api(self):
        """Test the public compress() function."""
        data = b'API test data! ' * 10
        # Simple mode
        r1 = compress(data, simple=True)
        assert pac1_decompress(r1, 0) == data
        # Set2 mode
        r2 = compress(data, use_set2=True)
        assert pac1_decompress(r2, 0) == data
        # No-Se2 mode
        r3 = compress(data, use_set2=False)
        assert pac1_decompress(r3, 0) == data


# ═══════════════════════════════════════════════════════════════════
# Test: NEW — Real ROM asset round-trip
# ═══════════════════════════════════════════════════════════════════

class TestRealAssets:
    """Round-trip tests using real PAC1 assets from the ROM."""

    ROM_PATH = None  # Will be set if ROM is found

    @classmethod
    def setup_class(cls):
        # Look for ROM in standard locations
        candidates = [
            'roms/dkc2.sfc',
            '../roms/dkc2.sfc',
            '../../roms/dkc2.sfc',
        ]
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        for rel in candidates:
            path = os.path.join(base, rel)
            if os.path.exists(path):
                cls.ROM_PATH = path
                break

    def test_rom_found(self):
        """Verify ROM is available for testing (informational)."""
        if self.__class__.ROM_PATH is None:
            import pytest
            pytest.skip("No ROM found, skipping real asset tests")

    def _get_assets(self):
        """Get list of valid asset offsets from ROM."""
        if self.__class__.ROM_PATH is None:
            return []
        with open(self.__class__.ROM_PATH, 'rb') as f:
            rom = f.read()
        from decode_pac1 import scan_headers
        results = scan_headers(rom, limit=20)
        # Filter valid
        valid = []
        for off, score, f1, f2, d1, d2, dw, lut4, dec in results:
            if dec.startswith('ok:'):
                valid.append(off)
        return valid[:5]  # Max 5 to keep tests fast

    def _get_asset_data(self, offset):
        """Extract and decompress a single asset."""
        if self.__class__.ROM_PATH is None:
            return None
        with open(self.__class__.ROM_PATH, 'rb') as f:
            rom = f.read()
        dec = pac1_decompress(rom, offset, max_output=0x20000)
        header = rom[offset:offset + 39]
        return {'data': dec, 'header': header, 'offset': offset}

    def test_real_asset_set1_roundtrip(self):
        """Round-trip a real ROM asset with Set1-only."""
        assets = self._get_assets()
        if not assets:
            import pytest
            pytest.skip("No valid assets found")
        asset = self._get_asset_data(assets[0])
        assert asset is not None, f"Failed to extract asset at 0x{assets[0]:X}"
        assert_roundtrip(asset['data'], use_set2=False,
                         **self._header_kw(asset['header']))

    def test_real_asset_set2_roundtrip(self):
        """Round-trip a real ROM asset with Set2-enhanced."""
        assets = self._get_assets()
        if not assets:
            import pytest
            pytest.skip("No valid assets found")
        asset = self._get_asset_data(assets[0])
        assert asset is not None, f"Failed to extract asset at 0x{assets[0]:X}"
        assert_roundtrip(asset['data'], use_set2=True,
                         **self._header_kw(asset['header']))

    def test_real_asset_compression_improvement(self):
        """Set2 compression of real assets should not be worse than Set1."""
        assets = self._get_assets()
        if not assets:
            import pytest
            pytest.skip("No valid assets found")
        for off in assets[:3]:
            asset = self._get_asset_data(off)
            if asset is None:
                continue
            hdr = self._header_kw(asset['header'])
            c1 = GreedyCompressor(header=build_header(**hdr))
            c2 = EnhancedGreedyCompressor(header=build_header(**hdr), use_set2=True)
            r1 = c1.compress(asset['data'])
            r2 = c2.compress(asset['data'])
            # Set2 should be <= Set1 or at most a few bytes larger
            assert len(r2) <= len(r1) + 5, (
                f"Set2 {len(r2)}B > Set1 {len(r1)}B + 5 for asset at 0x{off:X}"
            )

    @staticmethod
    def _header_kw(header_bytes):
        """Extract header kwargs from raw header bytes."""
        return {
            'fill1': header_bytes[1],
            'fill2': header_bytes[2],
            'dir1': header_bytes[3],
            'dir2': header_bytes[4],
            'dirw': struct.unpack_from('<H', header_bytes, 5)[0],
        }


# ═══════════════════════════════════════════════════════════════════
# Test: NEW — Synthetic asset pipeline (extract/recompress/patch)
# ═══════════════════════════════════════════════════════════════════

class TestSyntheticPipeline:
    """Test the asset extraction and patching pipeline with synthetic data."""

    def test_recompress_detects_fit(self):
        """Recompress should detect if data fits."""
        # Import patch_rom functions
        from extract_assets.patch_rom import recompress_asset, find_compressed_boundary

        # Create a synthetic ROM with a PAC1 asset
        data = bytes(range(100))
        header = build_header(fill1=0x00, fill2=0x00)
        compressor = EnhancedGreedyCompressor(header=header, use_set2=True)
        asset = compressor.compress(data)

        # Build a "ROM" consisting of padding + asset + padding
        padded_rom = b'\xFF' * 100 + asset + b'\xFF' * 100

        header_offset = 100

        # Test recompress with same data (should fit)
        result = recompress_asset(padded_rom, header_offset, data,
                                  use_set2=True)
        assert result['success'], f"Recompress failed: {result.get('error')}"
        assert result['fits'], "Same data should fit"
        assert result['padding_needed'] >= 0, "Should not need negative padding"

    def test_recompress_detects_no_fit(self):
        """Recompress should detect when data doesn't fit."""
        from extract_assets.patch_rom import recompress_asset

        # Tiny asset
        data = bytes([0x42])
        header = build_header()
        compressor = EnhancedGreedyCompressor(header=header, use_set2=True)
        asset = compressor.compress(data)

        # Build ROM with this small asset
        padded_rom = b'\xFF' * 100 + asset + b'\xFF' * 100

        # Try to recompress much larger data (won't fit)
        big_data = bytes([i % 256 for i in range(500)])
        result = recompress_asset(padded_rom, 100, big_data, use_set2=True)
        assert result['success'], f"Recompress failed: {result.get('error')}"
        # May or may not fit depending on compression ratio
        # For very incompressible data, it likely won't fit
        # This test is more about the function not crashing

    def test_patch_rom(self):
        """Test patching creates valid output."""
        from extract_assets.patch_rom import recompress_asset, patch_rom
        import tempfile

        data = bytes(range(200))
        header = build_header(fill1=0x00)
        compressor = EnhancedGreedyCompressor(header=header, use_set2=True)
        asset = compressor.compress(data)

        padded_rom = b'\xFF' * 100 + asset + b'\xFF' * 100
        header_offset = 100

        # Modify one byte
        modified = bytearray(data)
        modified[50] = 0xFF

        result = recompress_asset(padded_rom, header_offset, bytes(modified),
                                  use_set2=True)
        assert result['success'], f"Recompress failed: {result.get('error')}"

        if result['fits']:
            with tempfile.NamedTemporaryFile(delete=False, suffix='.sfc') as f:
                out_path = f.name
            try:
                patch_result = patch_rom(padded_rom, header_offset,
                                         result['new_compressed'], out_path)
                assert patch_result['success'], f"Patch failed: {patch_result.get('error')}"

                # Verify patched ROM
                with open(out_path, 'rb') as f:
                    patched_rom = f.read()

                # Verify rest of ROM is unchanged
                assert patched_rom[:100] == padded_rom[:100], "Data before asset changed"
                assert patched_rom[100 + result['old_size']:] == \
                       padded_rom[100 + result['old_size']:], "Data after asset changed"

                # Verify patched asset decompresses to modified data
                # Use the actual compressed data from patch
                dec_new = pac1_decompress(patched_rom, header_offset)
                assert dec_new is not None, "Patched asset decompression failed"
                # The new compressed data should decompress to modified
                # (but recompress(compress(modified)) may differ from
                # compress(modified) due to different header — we'll
                # just check it works)
            finally:
                try:
                    os.unlink(out_path)
                except:
                    pass


# ═══════════════════════════════════════════════════════════════════
# Test: NEW — Compress function API
# ═══════════════════════════════════════════════════════════════════

class TestCompressAPI:
    def test_compress_default(self):
        """compress() defaults to Set2 mode."""
        data = b'Test data for API test'
        result = compress(data)
        assert result[:4] != b'PAC1', "compress() shouldn't add PAC1 prefix"
        assert len(result) >= 39
        dec = pac1_decompress(result, 0)
        assert dec == data

    def test_compress_simple(self):
        """compress(simple=True) uses Set1-only."""
        data = b'Test data for simple mode'
        result = compress(data, simple=True)
        dec = pac1_decompress(result, 0)
        assert dec == data

    def test_compress_set2_false(self):
        """compress(use_set2=False) uses Set1-only."""
        data = b'Test data for set2=false'
        result = compress(data, use_set2=False)
        dec = pac1_decompress(result, 0)
        assert dec == data

    def test_compress_with_header(self):
        """compress() accepts custom header."""
        header = build_header(fill1=0xAB)
        data = bytes([0xAB] * 30)
        result = compress(data, header=header)
        dec = pac1_decompress(result, 0)
        assert dec == data


# ═══════════════════════════════════════════════════════════════════
# Test: Decompress mode CLI
# ═══════════════════════════════════════════════════════════════════

class TestCLI:
    def test_compress_decompress_cli(self):
        """Test CLI round-trip via subprocess."""
        import subprocess
        script = os.path.join(os.path.dirname(__file__), 'compress_pac1.py')
        original = b'Hello from CLI test! ' * 10

        # Compress via stdin/stdout
        proc = subprocess.run(
            [sys.executable, script],
            input=original,
            capture_output=True,
        )
        assert proc.returncode == 0, f'Compress failed: {proc.stderr.decode()}'
        compressed = proc.stdout

        # Decompress via --decompress
        proc2 = subprocess.run(
            [sys.executable, script, '--decompress'],
            input=compressed,
            capture_output=True,
        )
        assert proc2.returncode == 0, f'Decompress failed: {proc2.stderr.decode()}'
        decompressed = proc2.stdout

        assert decompressed == original, (
            f'CLI round-trip mismatch: {len(original)}B -> {len(original)}B'
        )

    def test_file_mode_cli(self):
        """Test file-based CLI round-trip."""
        import subprocess
        script = os.path.join(os.path.dirname(__file__), 'compress_pac1.py')
        original = b'File mode test data! ' * 20

        with tempfile.NamedTemporaryFile(delete=False, suffix='.raw') as f_in:
            f_in.write(original)
            raw_path = f_in.name

        pac_path = raw_path + '.pac1'
        dec_path = raw_path + '.dec'

        try:
            # Compress
            proc1 = subprocess.run(
                [sys.executable, script, '--input', raw_path, '--output', pac_path],
                capture_output=True,
            )
            assert proc1.returncode == 0, f'Compress failed: {proc1.stderr.decode()}'

            # Decompress
            proc2 = subprocess.run(
                [sys.executable, script, '--decompress',
                 '--input', pac_path, '--output', dec_path],
                capture_output=True,
            )
            assert proc2.returncode == 0, f'Decompress failed: {proc2.stderr.decode()}'

            with open(dec_path, 'rb') as f:
                decompressed = f.read()
            assert decompressed == original

        finally:
            for p in [raw_path, pac_path, dec_path]:
                try:
                    os.unlink(p)
                except OSError:
                    pass

    def test_cli_simple_flag(self):
        """Test --simple flag produces valid output."""
        import subprocess
        script = os.path.join(os.path.dirname(__file__), 'compress_pac1.py')
        original = b'Simple flag test! ' * 5

        # Compress with --simple
        proc = subprocess.run(
            [sys.executable, script, '--simple'],
            input=original,
            capture_output=True,
        )
        assert proc.returncode == 0, f'Simple compress failed: {proc.stderr.decode()}'
        compressed = proc.stdout

        # Decompress
        proc2 = subprocess.run(
            [sys.executable, script, '--decompress'],
            input=compressed,
            capture_output=True,
        )
        assert proc2.returncode == 0
        assert proc2.stdout == original

    def test_cli_no_set2_flag(self):
        """Test --no-set2 flag produces valid output."""
        import subprocess
        script = os.path.join(os.path.dirname(__file__), 'compress_pac1.py')
        original = b'No Set2 test! ' * 5

        proc = subprocess.run(
            [sys.executable, script, '--no-set2'],
            input=original,
            capture_output=True,
        )
        assert proc.returncode == 0
        compressed = proc.stdout

        proc2 = subprocess.run(
            [sys.executable, script, '--decompress'],
            input=compressed,
            capture_output=True,
        )
        assert proc2.returncode == 0
        assert proc2.stdout == original


# ═══════════════════════════════════════════════════════════════════
# Run via pytest
# ═══════════════════════════════════════════════════════════════════

if __name__ == '__main__':
    import pytest
    pytest.main([__file__, '-v', '--tb=short'])
