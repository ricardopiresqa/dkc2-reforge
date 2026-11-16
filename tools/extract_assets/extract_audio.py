"""SNES BRR Audio Extraction.

Extracts audio data from DKC2 ROM using BRR (Bit Rate Reduction) decoding.
BRR is the native audio compression format of the SNES SPC700 sound chip.

BRR Block Format (9 bytes per block, decodes to 16 PCM16 samples):
  Byte 0: Header
    bits 7-4: Range (scalar 0-12)
    bit 3: Loop flag (1 = loop point)
    bit 2: End flag (1 = last block)
    bits 1-0: Filter (0-3)
  Bytes 1-8: 16 4-bit signed delta values

Usage:
    python extract_audio.py --input audio.brr --info
    python extract_audio.py --input audio.brr --brr-to-wav output.wav
    python extract_audio.py --rom roms/dkc2.sfc --find-samples --offset 0x100000
    python extract_audio.py --rom roms/dkc2.sfc --scan-pac1
"""

import argparse
import os
import struct
import sys
import wave

# Add tools/analysis to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                '..', 'analysis'))


# ── BRR Constants ─────────────────────────────────────────────────

BRR_BLOCK_SIZE = 9
BRR_SAMPLES_PER_BLOCK = 16


# ── BRR Decoding ──────────────────────────────────────────────────

def _sign_extend_4(val: int) -> int:
    """Sign-extend a 4-bit value to 16-bit signed integer."""
    return val - 16 if val & 0x08 else val


def decode_brr_block(block: bytes, s1: int = 0, s2: int = 0) -> tuple:
    """Decode a single 9-byte BRR block into 16 PCM16 samples.

    Args:
        block: 9 bytes of BRR compressed data.
        s1: Previous sample (out[-1]), used by prediction filters.
        s2: Sample before previous (out[-2]), used by prediction filters.

    Returns:
        Tuple of (samples, s1, s2, end_flag, loop_flag).
    """
    header = block[0]
    range_ = (header >> 4) & 0x0F
    loop = bool((header >> 3) & 1)
    end = bool((header >> 2) & 1)
    filter_ = header & 0x03

    samples = []
    for i in range(8):
        byte = block[1 + i]
        hi = (byte >> 4) & 0x0F
        lo = byte & 0x0F

        for nibble in (hi, lo):
            s = _sign_extend_4(nibble) << range_

            if filter_ == 0:
                out = s
            elif filter_ == 1:
                out = s + s1 - (s1 >> 4)
            elif filter_ == 2:
                out = s + (s1 << 1) - s2 - ((s1 << 1) >> 5) - (s2 >> 4)
            elif filter_ == 3:
                out = s + (s1 << 1) - s2 - ((s1 << 1) >> 5) + (-s2 >> 4)
            else:
                out = s

            out = max(-32768, min(32767, out))
            samples.append(out)
            s2, s1 = s1, out

    return samples, s1, s2, end, loop


def parse_brr(data: bytes) -> list[int]:
    """Decode BRR compressed data into PCM16 samples.

    Args:
        data: Raw BRR data (one or more 9-byte blocks).

    Returns:
        List of 16-bit signed PCM samples.

    Raises:
        ValueError: If data length is not a multiple of 9, or
                    if an invalid range (>12) is encountered.
    """
    if not data:
        return []

    if len(data) % BRR_BLOCK_SIZE != 0:
        raise ValueError(
            f'BRR data length {len(data)} is not a multiple of '
            f'{BRR_BLOCK_SIZE}')

    all_samples = []
    s1, s2 = 0, 0

    for offset in range(0, len(data), BRR_BLOCK_SIZE):
        block = data[offset:offset + BRR_BLOCK_SIZE]
        header = block[0]
        range_ = (header >> 4) & 0x0F

        if range_ > 12:
            raise ValueError(
                f'Invalid range {range_} at block offset 0x{offset:X}')

        samples, s1, s2, end, loop = decode_brr_block(block, s1, s2)
        all_samples.extend(samples)

    return all_samples


# ── BRR to WAV Export ─────────────────────────────────────────────

def brr_to_wav(samples: list[int], output_path: str,
               sample_rate: int = 32000):
    """Export PCM16 samples as a WAV file.

    Args:
        samples: List of 16-bit signed PCM samples.
        output_path: Path for the output .wav file.
        sample_rate: Sample rate in Hz (default: 32000, SNES rate).
    """
    os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)

    with wave.open(output_path, 'wb') as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(sample_rate)
        wav.writeframes(struct.pack(f'<{len(samples)}h', *samples))


# ── BRR Sample Scanning ───────────────────────────────────────────

def find_brr_samples(data: bytes, min_length: int = 9) -> list[dict]:
    """Scan data for candidate BRR sample sequences.

    Looks for sequences of BRR blocks with valid headers (range <= 12).
    A complete sample continues until an end flag or invalid header.

    Args:
        data: Raw bytes to scan.
        min_length: Minimum total bytes for a candidate (default 9).

    Returns:
        List of dicts with offset, blocks, total_bytes, end_found.
    """
    candidates = []
    data_len = len(data)
    i = 0

    while i <= data_len - BRR_BLOCK_SIZE:
        header = data[i]
        range_ = (header >> 4) & 0x0F

        if range_ > 12:
            i += 1
            continue

        blocks = 0
        pos = i
        end_found = False

        while pos <= data_len - BRR_BLOCK_SIZE:
            h = data[pos]
            r = (h >> 4) & 0x0F
            if r > 12:
                break

            blocks += 1
            end_flag = (h >> 2) & 1
            if end_flag:
                end_found = True
                pos += BRR_BLOCK_SIZE
                break

            pos += BRR_BLOCK_SIZE

        total_bytes = blocks * BRR_BLOCK_SIZE
        if total_bytes >= min_length:
            candidates.append({
                'offset': i,
                'blocks': blocks,
                'total_bytes': total_bytes,
                'end_found': end_found,
            })
            if end_found:
                i = pos
            else:
                i = pos + 1
        else:
            i += 1

    return candidates


# ── PAC1 Audio Detection ──────────────────────────────────────────

def detect_pac1_audio(rom_data: bytes, min_score: int = 12,
                      max_assets: int = None) -> list[dict]:
    """Scan PAC1 archives and test if their data is BRR audio.

    Decompresses each valid PAC1 and attempts BRR decode. Reports
    candidates based on BRR block validity and sample statistics.

    Args:
        rom_data: Full ROM bytes.
        min_score: Minimum PAC1 header score.
        max_assets: Maximum PAC1 archives to test.

    Returns:
        List of dicts with PAC1 info + BRR detection results.
    """
    from extract_assets.extract_pac1 import scan_rom
    from decode_pac1 import decompress as pac1_decompress

    assets = scan_rom(rom_data, min_score=min_score,
                      max_count=max_assets)

    results = []
    for asset in assets:
        off = asset['offset']
        if not asset['valid']:
            continue

        dec = pac1_decompress(rom_data, off, max_output=0x20000)
        if dec is None or len(dec) == 0:
            continue

        brr_blocks = len(dec) // BRR_BLOCK_SIZE
        if brr_blocks == 0:
            continue

        all_valid = True
        for i in range(brr_blocks):
            block = dec[i * BRR_BLOCK_SIZE:(i + 1) * BRR_BLOCK_SIZE]
            if len(block) < BRR_BLOCK_SIZE:
                all_valid = False
                break
            r = (block[0] >> 4) & 0x0F
            if r > 12:
                all_valid = False
                break

        if not all_valid:
            continue

        try:
            samples = parse_brr(dec[:brr_blocks * BRR_BLOCK_SIZE])
        except (ValueError, IndexError):
            samples = None

        min_val = min(samples) if samples else 0
        max_val = max(samples) if samples else 0
        clipped = sum(1 for s in samples if abs(s) >= 32767) if samples else 0

        variance = (sum(abs(s) for s in samples) / len(samples)
                    if samples and len(samples) > 0 else 0)
        score = variance + max(abs(min_val), abs(max_val)) / 100

        results.append({
            'pac1_offset': off,
            'decompressed_size': len(dec),
            'brr_blocks': brr_blocks,
            'brr_samples': len(samples) if samples else 0,
            'sample_min': min_val,
            'sample_max': max_val,
            'clipped_samples': clipped,
            'score': score,
        })

    results.sort(key=lambda r: -r['score'])
    return results


# ── Info ───────────────────────────────────────────────────────────

def brr_info(data: bytes) -> dict:
    """Get info about BRR data.

    Args:
        data: Raw BRR bytes.

    Returns:
        Dict with block_count, sample_count, has_loop, has_end, etc.
    """
    blocks = len(data) // BRR_BLOCK_SIZE
    remainder = len(data) % BRR_BLOCK_SIZE

    has_loop = False
    has_end = False
    range_usage = {}
    filters_used = set()

    for i in range(blocks):
        block = data[i * BRR_BLOCK_SIZE:(i + 1) * BRR_BLOCK_SIZE]
        if len(block) < BRR_BLOCK_SIZE:
            break
        h = block[0]
        r = (h >> 4) & 0x0F
        loop = (h >> 3) & 1
        end = (h >> 2) & 1
        filt = h & 0x03

        range_usage[r] = range_usage.get(r, 0) + 1
        filters_used.add(filt)
        if loop:
            has_loop = True
        if end:
            has_end = True

    return {
        'total_bytes': len(data),
        'blocks': blocks,
        'remainder_bytes': remainder,
        'samples': blocks * BRR_SAMPLES_PER_BLOCK,
        'has_loop': has_loop,
        'has_end': has_end,
        'ranges': sorted(range_usage.items()),
        'filters': sorted(filters_used),
    }


# ── CLI ───────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description='DKC2 BRR Audio Extraction Tool')

    parser.add_argument('--input',
                        help='Input file (BRR data)')
    parser.add_argument('--rom',
                        help='Path to DKC2 ROM file')
    parser.add_argument('--offset', type=lambda x: int(x, 16),
                        default=0,
                        help='ROM offset (hex)')
    parser.add_argument('--length', type=lambda x: int(x, 16),
                        default=0,
                        help='Data length from offset (hex)')

    parser.add_argument('--brr-to-wav',
                        help='Export BRR data as WAV file')
    parser.add_argument('--find-samples', action='store_true',
                        help='Scan for BRR sample candidates')
    parser.add_argument('--scan-pac1', action='store_true',
                        help='Test PAC1 archives as BRR audio')
    parser.add_argument('--info', action='store_true',
                        help='Show BRR file info')

    parser.add_argument('--sample-rate', type=int, default=32000,
                        help='WAV sample rate in Hz (default: 32000)')
    parser.add_argument('--min-score', type=int, default=12,
                        help='Min PAC1 header score (default: 12)')
    parser.add_argument('--max', type=int, default=0,
                        help='Maximum results')

    args = parser.parse_args()

    if args.scan_pac1:
        _handle_scan_pac1(args)
        return

    if args.input:
        _handle_input_file(args)
        return

    if args.rom and args.find_samples:
        _handle_rom_scan(args)
        return

    parser.print_help()


def _handle_scan_pac1(args):
    if not args.rom:
        print('--rom required for --scan-pac1')
        sys.exit(1)
    with open(args.rom, 'rb') as f:
        rom_data = f.read()
    max_count = args.max if args.max > 0 else None
    results = detect_pac1_audio(rom_data, min_score=args.min_score,
                                max_assets=max_count)
    if not results:
        print('No PAC1 archives detected as audio.')
        return

    print(f"{'PAC1 Offset':>12} {'DecSize':>8} {'BRR Blocks':>10} "
          f"{'Samples':>8} {'Min':>6} {'Max':>6} {'Clip':>5} {'Score':>8}")
    print('-' * 70)
    for r in results:
        print(f"  0x{r['pac1_offset']:06X}  {r['decompressed_size']:6d}B  "
              f"{r['brr_blocks']:4d} blocks  {r['brr_samples']:5d}  "
              f"{r['sample_min']:5d}  {r['sample_max']:5d}  "
              f"{r['clipped_samples']:3d}  {r['score']:7.1f}")


def _handle_input_file(args):
    with open(args.input, 'rb') as f:
        data = f.read()

    if args.info:
        info = brr_info(data)
        print(f"BRR Audio Info: {args.input}")
        print(f"  Total bytes: {info['total_bytes']}")
        print(f"  Blocks: {info['blocks']} ({info['samples']} samples)")
        if info['remainder_bytes']:
            print(f"  Remainder bytes (ignored): {info['remainder_bytes']}")
        print(f"  Loop point: {'yes' if info['has_loop'] else 'no'}")
        print(f"  End marker: {'yes' if info['has_end'] else 'no'}")
        print(f"  Ranges used: {', '.join(f'r{r}={c}' for r, c in info['ranges'])}")
        print(f"  Filters used: {info['filters']}")

    if args.brr_to_wav:
        samples = parse_brr(data)
        brr_to_wav(samples, args.brr_to_wav, sample_rate=args.sample_rate)
        duration = len(samples) / args.sample_rate
        print(f"Exported {len(samples)} samples to {args.brr_to_wav} "
              f"({args.sample_rate}Hz, {duration:.2f}s)")

    if args.find_samples:
        candidates = find_brr_samples(data)
        print(f"Found {len(candidates)} BRR candidate sequences:")
        for c in candidates:
            end_mark = ' [END]' if c['end_found'] else ''
            print(f"  0x{c['offset']:06X}: {c['blocks']} blocks, "
                  f"{c['total_bytes']}B{end_mark}")

    if not args.info and not args.brr_to_wav and not args.find_samples:
        print('No action specified. Use --info, --brr-to-wav, or --find-samples.')


def _handle_rom_scan(args):
    with open(args.rom, 'rb') as f:
        rom_data = f.read()

    offset = args.offset
    length = args.length or (len(rom_data) - offset)

    chunk = rom_data[offset:offset + length]
    candidates = find_brr_samples(chunk)

    print(f"Scanning ROM at 0x{offset:X} for {length}B "
          f"({len(candidates)} candidates):")
    for c in candidates:
        abs_off = offset + c['offset']
        end_mark = ' [END]' if c['end_found'] else ''
        print(f"  0x{abs_off:06X}: {c['blocks']} blocks, "
              f"{c['total_bytes']}B{end_mark}")


if __name__ == '__main__':
    main()
