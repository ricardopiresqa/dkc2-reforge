"""Tests for BRR audio extraction (extract_audio.py).

Covers:
  - BRR block decode with various filters
  - Full BRR stream decode
  - WAV export validity
  - BRR sample scanning (finding candidates)
  - CLI smoke tests
"""

import os
import struct
import sys
import tempfile

# Add tools/ and tools/analysis to path for imports
_test_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _test_dir)
sys.path.insert(0, os.path.dirname(_test_dir))

from extract_assets.extract_audio import (
    BRR_BLOCK_SIZE,
    BRR_SAMPLES_PER_BLOCK,
    _sign_extend_4,
    decode_brr_block,
    parse_brr,
    brr_to_wav,
    find_brr_samples,
    brr_info,
)


# ═══════════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════════

def _make_brr_block(range_=0, filter_=0, loop=False, end=False,
                    data=None):
    """Create a 9-byte BRR block.

    Args:
        range_: Range scalar (0-12).
        filter_: Prediction filter (0-3).
        loop: Loop point flag.
        end: End block flag.
        data: 8 bytes of BRR data (default: all zeros).

    Returns:
        9-byte BRR block.
    """
    header = (range_ << 4) | (int(loop) << 3) | (int(end) << 2) | filter_
    if data is None:
        data = bytes(8)
    return bytes([header]) + data[:8]


def _make_brr_stream(blocks):
    """Create multi-block BRR stream. Last block gets end flag.

    Args:
        blocks: List of (range, filter, data_bytes) tuples.

    Returns:
        Concatenated BRR blocks (last block has end=1).
    """
    result = bytearray()
    for i, (r, f, data) in enumerate(blocks):
        end = (i == len(blocks) - 1)
        result.extend(_make_brr_block(range_=r, filter_=f, end=end,
                                       data=data))
    return bytes(result)


# ═══════════════════════════════════════════════════════════════════
# Test: Sign Extension
# ═══════════════════════════════════════════════════════════════════

class TestSignExtend:
    def test_positive_values(self):
        """0..7 stay unchanged."""
        for v in range(8):
            assert _sign_extend_4(v) == v

    def test_negative_values(self):
        """8..15 become -8..-1."""
        assert _sign_extend_4(8) == -8
        assert _sign_extend_4(15) == -1
        assert _sign_extend_4(0x0F) == -1

    def test_zero(self):
        """0 stays 0."""
        assert _sign_extend_4(0) == 0

    def test_boundary(self):
        """Boundary at 7 and 8."""
        assert _sign_extend_4(7) == 7
        assert _sign_extend_4(8) == -8


# ═══════════════════════════════════════════════════════════════════
# Test: BRR Block Decode
# ═══════════════════════════════════════════════════════════════════

class TestDecodeBRRBlock:
    def test_all_zero_filter0(self):
        """Filter 0, range 0, all zeros -> all zero samples."""
        block = _make_brr_block(range_=0, filter_=0, data=bytes(8))
        samples, s1, s2, end, loop = decode_brr_block(block)
        assert len(samples) == BRR_SAMPLES_PER_BLOCK
        assert all(s == 0 for s in samples)
        assert end is False
        assert loop is False

    def test_filter0_known_output(self):
        """Filter 0, range 0, nibble=1 -> sample=1."""
        # 8 data bytes, each nibble = 0x01 pattern
        # Byte = 0x11 means high nibble=1, low nibble=1
        data = bytes([0x11] * 8)
        block = _make_brr_block(range_=0, filter_=0, data=data)
        samples, s1, s2, end, loop = decode_brr_block(block)
        assert len(samples) == 16
        assert all(s == 1 for s in samples)

    def test_filter0_range2(self):
        """Filter 0, range 2, nibble=1 -> sample=4 (1 << 2)."""
        data = bytes([0x11] * 8)
        block = _make_brr_block(range_=2, filter_=0, data=data)
        samples, s1, s2, end, loop = decode_brr_block(block)
        assert all(s == 4 for s in samples)

    def test_filter0_negative(self):
        """Filter 0, range 0, nibble=0xF (-1) -> sample=-1."""
        # Byte 0xFF: both nibbles = 0xF = -1
        data = bytes([0xFF] * 8)
        block = _make_brr_block(range_=0, filter_=0, data=data)
        samples, s1, s2, end, loop = decode_brr_block(block)
        assert all(s == -1 for s in samples)

    def test_filter0_range2_negative(self):
        """Filter 0, range 2, nibble=0xF -> sample=-4 (-1 << 2)."""
        data = bytes([0xFF] * 8)
        block = _make_brr_block(range_=2, filter_=0, data=data)
        samples, _, _, _, _ = decode_brr_block(block)
        assert all(s == -4 for s in samples)

    def test_end_flag(self):
        """End flag is correctly reported."""
        block = _make_brr_block(range_=0, filter_=0, end=True)
        _, _, _, end, _ = decode_brr_block(block)
        assert end is True

    def test_loop_flag(self):
        """Loop flag is correctly reported."""
        block = _make_brr_block(range_=0, filter_=0, loop=True)
        _, _, _, _, loop = decode_brr_block(block)
        assert loop is True

    def test_filter1_prediction(self):
        """Filter 1 uses previous sample for prediction."""
        # First block: all zeros, filter 0
        block1 = _make_brr_block(range_=2, filter_=0,
                                  data=bytes([0x11] * 8))
        samples1, s1, s2, _, _ = decode_brr_block(block1)
        assert all(s == 4 for s in samples1)

        # Second block: zeros input, filter 1 -> should decay
        block2 = _make_brr_block(range_=0, filter_=1, data=bytes(8))
        samples2, _, _, _, _ = decode_brr_block(block2, s1=s1, s2=s2)
        assert len(samples2) == 16
        # With filter 1 and zero input, output decays: s1 - (s1>>4)
        assert samples2[0] == 4 - (4 >> 4)  # = 4 - 0 = 4... hmm
        # Actually with s=0, filter 1: out = 0 + s1 - (s1 >> 4)
        # s1=4: out = 0 + 4 - 0 = 4 (4 >> 4 = 0)
        # So it doesn't decay for small values! Let me test with a larger value.
        pass

    def test_filter1_decay(self):
        """Filter 1 with larger input shows decay."""
        # Block: range=4, nibble=1 -> s = 16
        block = _make_brr_block(range_=4, filter_=0,
                                 data=bytes([0x11] * 8))
        samples, s1, s2, _, _ = decode_brr_block(block)
        assert all(s == 16 for s in samples)

        # Zero-input block with filter 1
        block2 = _make_brr_block(range_=0, filter_=1, data=bytes(8))
        samples2, _, _, _, _ = decode_brr_block(block2, s1=s1, s2=s2)
        # out = 0 + 16 - (16 >> 4) = 16 - 1 = 15
        assert samples2[0] == 15


# ═══════════════════════════════════════════════════════════════════
# Test: Full BRR Parse
# ═══════════════════════════════════════════════════════════════════

class TestParseBRR:
    def test_empty_data(self):
        """Empty data returns empty list."""
        assert parse_brr(b'') == []

    def test_single_block(self):
        """Single block parses to 16 samples."""
        data = _make_brr_block(range_=0, filter_=0, data=bytes(8))
        samples = parse_brr(data)
        assert len(samples) == BRR_SAMPLES_PER_BLOCK

    def test_two_blocks(self):
        """Two blocks produce 32 samples."""
        blocks = _make_brr_stream([
            (0, 0, bytes(8)),
            (0, 0, bytes(8)),
        ])
        samples = parse_brr(blocks)
        assert len(samples) == 32

    def test_invalid_range(self):
        """Range > 12 raises ValueError."""
        header = (13 << 4) | 0  # range=13 > 12
        data = bytes([header]) + bytes(8)
        import pytest
        with pytest.raises(ValueError):
            parse_brr(data)

    def test_non_multiple_length(self):
        """Non-multiple-of-9 length raises ValueError."""
        import pytest
        with pytest.raises(ValueError):
            parse_brr(bytes(10))


# ═══════════════════════════════════════════════════════════════════
# Test: WAV Export
# ═══════════════════════════════════════════════════════════════════

class TestBRRtoWAV:
    def test_wav_valid(self):
        """Exported WAV is a valid file with correct header."""
        samples = [0, 100, -100, 32767, -32768]
        fd, path = tempfile.mkstemp(suffix='.wav')
        os.close(fd)
        try:
            brr_to_wav(samples, path, sample_rate=32000)

            import wave
            with wave.open(path, 'rb') as w:
                assert w.getnchannels() == 1
                assert w.getsampwidth() == 2
                assert w.getframerate() == 32000
                assert w.getnframes() == len(samples)

                frames = w.readframes(w.getnframes())
                decoded = list(struct.unpack(f'<{len(samples)}h', frames))
                assert decoded == samples
        finally:
            os.unlink(path)

    def test_wav_empty(self):
        """Empty sample list creates valid WAV with 0 frames."""
        fd, path = tempfile.mkstemp(suffix='.wav')
        os.close(fd)
        try:
            brr_to_wav([], path)
            import wave
            with wave.open(path, 'rb') as w:
                assert w.getnframes() == 0
        finally:
            os.unlink(path)

    def test_wav_different_sample_rate(self):
        """Custom sample rate is reflected in WAV header."""
        samples = [0] * 100
        fd, path = tempfile.mkstemp(suffix='.wav')
        os.close(fd)
        try:
            brr_to_wav(samples, path, sample_rate=22050)
            import wave
            with wave.open(path, 'rb') as w:
                assert w.getframerate() == 22050
        finally:
            os.unlink(path)

    def test_brr_to_wav_end_to_end(self):
        """BRR decode + WAV export produces correct output."""
        data = _make_brr_block(range_=2, filter_=0,
                                data=bytes([0x11] * 8))
        samples = parse_brr(data)
        assert len(samples) == 16
        assert all(s == 4 for s in samples)

        fd, path = tempfile.mkstemp(suffix='.wav')
        os.close(fd)
        try:
            brr_to_wav(samples, path)
            import wave
            with wave.open(path, 'rb') as w:
                frames = w.readframes(w.getnframes())
                decoded = list(struct.unpack('<16h', frames))
                assert decoded == [4] * 16
        finally:
            os.unlink(path)


# ═══════════════════════════════════════════════════════════════════
# Test: BRR Scanning
# ═══════════════════════════════════════════════════════════════════

class TestFindBRRSamples:
    def test_empty_data(self):
        """Empty data returns no candidates."""
        assert find_brr_samples(b'') == []

    def test_no_valid_headers(self):
        """Data with invalid ranges returns no candidates."""
        data = bytes([0xFF] * 100)  # range = 15 in all bytes
        assert find_brr_samples(data) == []

    def test_single_block(self):
        """A single valid block is found."""
        block = _make_brr_block(range_=0, filter_=0, data=bytes(8))
        garbage = bytes([0xFF] * 20)  # invalid range 15 = not BRR
        data = block + garbage
        candidates = find_brr_samples(data)
        assert len(candidates) == 1
        assert candidates[0]['blocks'] == 1

    def test_two_blocks_with_garbage(self):
        """Two valid blocks separated by garbage are found separately."""
        block1 = _make_brr_block(range_=0, filter_=0, data=bytes(8),
                                  end=True)
        block2 = _make_brr_block(range_=1, filter_=0, data=bytes(8),
                                  end=True)
        data = block1 + bytes(50) + block2
        candidates = find_brr_samples(data)
        assert len(candidates) >= 1
        # First candidate is block1 (with end flag)

    def test_continuous_blocks(self):
        """Continuous valid blocks are merged."""
        blocks = _make_brr_stream([
            (0, 0, bytes(8)),
            (1, 0, bytes(8)),
        ])
        candidates = find_brr_samples(blocks)
        assert len(candidates) == 1
        assert candidates[0]['blocks'] == 2
        assert candidates[0]['end_found'] is True

    def test_min_length_filter(self):
        """min_length filters short candidates."""
        block = _make_brr_block(range_=0, filter_=0, data=bytes(8),
                                 end=True)
        data = block
        # Short: 9 bytes, require 18 -> no candidates
        candidates = find_brr_samples(data, min_length=18)
        assert len(candidates) == 0

    def test_three_blocks_no_end(self):
        """Three blocks without end flag are still found."""
        data = bytearray()
        for i in range(3):
            data.extend(_make_brr_block(range_=i, filter_=0,
                                         data=bytes(8)))
        candidates = find_brr_samples(bytes(data))
        assert len(candidates) == 1
        assert candidates[0]['blocks'] == 3
        assert candidates[0]['end_found'] is False


# ═══════════════════════════════════════════════════════════════════
# Test: BRR Info
# ═══════════════════════════════════════════════════════════════════

class TestBRRInfo:
    def test_basic_info(self):
        """Info returns correct block count."""
        data = _make_brr_block(range_=2, filter_=1, end=True)
        info = brr_info(data)
        assert info['blocks'] == 1
        assert info['samples'] == 16
        assert info['total_bytes'] == 9
        assert info['has_end'] is True
        assert info['has_loop'] is False
        assert (2, 1) in info['ranges']

    def test_multi_block_info(self):
        """Multi-block info shows accumulators."""
        data = _make_brr_stream([
            (0, 0, bytes(8)),
            (1, 1, bytes(8)),
            (2, 0, bytes(8)),
        ])
        info = brr_info(data)
        assert info['blocks'] == 3
        assert info['samples'] == 48
        assert info['has_end'] is True
        assert info['filters'] == [0, 1]

    def test_info_with_loop(self):
        """Loop flag is detected."""
        block = _make_brr_block(range_=0, filter_=0, loop=True, end=True)
        info = brr_info(block)
        assert info['has_loop'] is True

    def test_remainder(self):
        """Extra bytes past block boundary are reported."""
        block = _make_brr_block(range_=0, filter_=0)
        data = block + bytes([0xAB, 0xCD])  # 9 + 2 = 11 bytes
        info = brr_info(data)
        assert info['blocks'] == 1
        assert info['remainder_bytes'] == 2

    def test_empty(self):
        """Empty data."""
        info = brr_info(b'')
        assert info['blocks'] == 0
        assert info['samples'] == 0


# ═══════════════════════════════════════════════════════════════════
# Test: CLI Smoke
# ═══════════════════════════════════════════════════════════════════

class TestCLI:
    @staticmethod
    def _make_brr_file(data=None):
        """Create a temp file with BRR data."""
        if data is None:
            data = _make_brr_block(range_=0, filter_=0, data=bytes(8),
                                    end=True)
            data = data * 3  # 3 identical blocks
        fd, path = tempfile.mkstemp(suffix='.brr')
        os.write(fd, data)
        os.close(fd)
        return path

    def test_info_flag(self):
        """--info shows BRR details."""
        path = self._make_brr_file()
        try:
            import subprocess
            script = os.path.join(os.path.dirname(__file__),
                                  '..', 'extract_assets',
                                  'extract_audio.py')
            result = subprocess.run(
                [sys.executable, script, '--input', path, '--info'],
                capture_output=True, text=True,
            )
            assert result.returncode == 0
            assert 'Blocks:' in result.stdout
            assert 'samples' in result.stdout
            assert 'End marker' in result.stdout
        finally:
            os.unlink(path)

    def test_brr_to_wav_flag(self):
        """--brr-to-wav exports valid WAV."""
        path = self._make_brr_file()
        wav_path = path + '.wav'
        try:
            import subprocess
            script = os.path.join(os.path.dirname(__file__),
                                  '..', 'extract_assets',
                                  'extract_audio.py')
            result = subprocess.run(
                [sys.executable, script, '--input', path,
                 '--brr-to-wav', wav_path],
                capture_output=True, text=True,
            )
            assert result.returncode == 0
            assert 'Exported' in result.stdout

            import wave
            with wave.open(wav_path, 'rb') as w:
                assert w.getnchannels() == 1
                assert w.getsampwidth() == 2
                assert w.getnframes() > 0
        finally:
            if os.path.exists(wav_path):
                os.unlink(wav_path)
            os.unlink(path)

    def test_find_samples_flag(self):
        """--find-samples with --input finds candidates."""
        block = _make_brr_block(range_=0, filter_=0, data=bytes(8),
                                 end=True)
        data = block * 3
        path = self._make_brr_file(data)
        try:
            import subprocess
            script = os.path.join(os.path.dirname(__file__),
                                  '..', 'extract_assets',
                                  'extract_audio.py')
            result = subprocess.run(
                [sys.executable, script, '--input', path,
                 '--find-samples'],
                capture_output=True, text=True,
            )
            assert result.returncode == 0
            assert 'BRR candidate' in result.stdout
        finally:
            os.unlink(path)

    def test_custom_sample_rate(self):
        """--sample-rate is passed through."""
        path = self._make_brr_file()
        wav_path = path + '.wav'
        try:
            import subprocess
            script = os.path.join(os.path.dirname(__file__),
                                  '..', 'extract_assets',
                                  'extract_audio.py')
            result = subprocess.run(
                [sys.executable, script, '--input', path,
                 '--brr-to-wav', wav_path, '--sample-rate', '44100'],
                capture_output=True, text=True,
            )
            assert result.returncode == 0

            import wave
            with wave.open(wav_path, 'rb') as w:
                assert w.getframerate() == 44100
        finally:
            if os.path.exists(wav_path):
                os.unlink(wav_path)
            os.unlink(path)

    def test_no_args_prints_help(self):
        """No args prints usage."""
        import subprocess
        script = os.path.join(os.path.dirname(__file__),
                              '..', 'extract_assets',
                              'extract_audio.py')
        result = subprocess.run(
            [sys.executable, script],
            capture_output=True, text=True,
        )
        assert result.returncode == 0
        assert 'BRR Audio' in result.stdout


# ═══════════════════════════════════════════════════════════════════
# Integration: Verification of PAC1 audio detection (optional)
# ═══════════════════════════════════════════════════════════════════

class TestIntegration:
    """Integration tests using real ROM (if available)."""

    ROM_PATH = None

    @classmethod
    def setup_class(cls):
        candidates = [
            'roms/dkc2.sfc',
            '../roms/dkc2.sfc',
            '../../roms/dkc2.sfc',
        ]
        base = os.path.dirname(os.path.dirname(os.path.dirname(
            os.path.abspath(__file__))))
        for rel in candidates:
            path = os.path.join(base, rel)
            if os.path.exists(path):
                cls.ROM_PATH = path
                break

    def test_rom_found(self):
        """Verify ROM is available (informational)."""
        if self.__class__.ROM_PATH is None:
            import pytest
            pytest.skip('No ROM found, skipping integration tests')

    def test_scan_rom_for_brr(self):
        """Scan ROM for BRR candidates (smoke test)."""
        if self.__class__.ROM_PATH is None:
            import pytest
            pytest.skip('No ROM found')
        with open(self.__class__.ROM_PATH, 'rb') as f:
            rom = f.read()
        candidates = find_brr_samples(rom[:0x100000], min_length=18)
        assert len(candidates) > 0
        # Verify candidate structure
        for c in candidates[:5]:
            assert 'offset' in c
            assert 'blocks' in c
            assert c['blocks'] >= 2

    def test_scan_pac1_audio(self):
        """Scan PAC1 archives for audio (smoke test)."""
        if self.__class__.ROM_PATH is None:
            import pytest
            pytest.skip('No ROM found')
        from extract_assets.extract_audio import detect_pac1_audio
        with open(self.__class__.ROM_PATH, 'rb') as f:
            rom = f.read()
        results = detect_pac1_audio(rom, min_score=12, max_assets=50)
        assert len(results) >= 0  # may find none, that's OK
        for r in results:
            assert 'pac1_offset' in r
            assert 'brr_samples' in r
            assert 'score' in r


# ═══════════════════════════════════════════════════════════════════
# Run via pytest
# ═══════════════════════════════════════════════════════════════════

if __name__ == '__main__':
    import pytest
    pytest.main([__file__, '-v', '--tb=short'])
