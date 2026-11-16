"""PAC1 Asset Extraction Pipeline.

Scans a DKC2 ROM for PAC1 compressed headers, extracts compressed and
decompressed data, and supports round-trip verification.

Usage:
    # Scan for all assets
    python extract_pac1.py --rom roms/dkc2.sfc --scan

    # Extract a single asset
    python extract_pac1.py --rom roms/dkc2.sfc --offset 0x296B2A --output-dir assets/

    # Extract all found assets
    python extract_pac1.py --rom roms/dkc2.sfc --extract-all --output-dir assets/

    # Round-trip verify all assets
    python extract_pac1.py --rom roms/dkc2.sfc --verify-all

    # List asset headers summary
    python extract_pac1.py --rom roms/dkc2.sfc --list
"""

import argparse
import os
import struct
import sys

# Add tools/analysis to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'analysis'))

from decode_pac1 import decompress as pac1_decompress, parse_header, header_score
from compress_pac1 import compress as pac1_compress


# ── ROM Scanning ─────────────────────────────────────────────────────────

def scan_rom(rom_data, min_score=12, max_count=None):
    """Scan ROM data for valid PAC1 headers.

    Uses header_score() to evaluate each 39-byte-aligned position.
    Filters by minimum LUT validity score and decompressability.

    Args:
        rom_data: Full ROM bytes.
        min_score: Minimum header_score to consider (default: 12).
        max_count: Maximum results to return (default: all).

    Returns:
        List of dicts:
            offset: ROM offset of header.
            score: Header validity score (0-16).
            fill1, fill2: Header fill bytes.
            dir1, dir2, dirw: Header direct values.
            lut: 16-word lookup table.
            size_compressed: Total bytes from header to end-of-stream.
            size_decompressed: Decompressed size in bytes.
            valid: True if decompression produced output.
    """
    results = []
    data_len = len(rom_data)

    for off in range(data_len - 39):
        score = header_score(rom_data, off)
        if score < min_score:
            continue

        h = rom_data[off:off + 39]
        fill1, fill2 = h[1], h[2]
        dir1, dir2 = h[3], h[4]
        dirw = struct.unpack_from('<H', h, 5)[0]
        lut = list(struct.unpack_from('<16H', h, 7))

        # Try decompressing to validate
        dec = pac1_decompress(rom_data, off, max_output=0x20000)
        valid = dec is not None
        decomp_size = len(dec) if dec else 0

        # Estimate compressed size by scanning for terminator
        # The terminator is 0x00 byte (copy_or_return with count=0)
        comp_end = off + 39
        while comp_end < data_len:
            if rom_data[comp_end] == 0x00:
                comp_end += 1  # include the terminator byte
                break
            comp_end += 1
        comp_size = comp_end - off

        results.append({
            'offset': off,
            'score': score,
            'fill1': fill1,
            'fill2': fill2,
            'dir1': dir1,
            'dir2': dir2,
            'dirw': dirw,
            'lut': lut,
            'size_compressed': comp_size,
            'size_decompressed': decomp_size,
            'valid': valid,
        })

    results.sort(key=lambda r: (-r['score'], -r['size_decompressed'] if r['valid'] else 0, r['offset']))

    if max_count is not None and max_count > 0:
        results = results[:max_count]

    return results


def list_assets(rom_data, min_score=12, max_count=None):
    """Scan and return a summary list of assets."""
    return scan_rom(rom_data, min_score=min_score, max_count=max_count)


# ── Extraction ───────────────────────────────────────────────────────────

def extract_asset(rom_data, offset, output_dir='.', prefix=''):
    """Extract a single asset from ROM at the given header offset.

    Creates three files:
        {prefix}{offset}_header.bin -- Raw 39-byte header.
        {prefix}{offset}_compressed.bin -- Full compressed data (header + stream).
        {prefix}{offset}_decompressed.bin -- Decompressed output.

    Args:
        rom_data: Full ROM bytes.
        offset: ROM offset of PAC1 header.
        output_dir: Directory to write output files.
        prefix: Optional filename prefix.

    Returns:
        dict with file paths and sizes, or None on failure.
    """
    h = parse_header(rom_data, offset)
    if h is None:
        print(f"  Invalid header at 0x{offset:X}")
        return None

    # Decompress
    dec = pac1_decompress(rom_data, offset, max_output=0x20000)
    if dec is None:
        print(f"  Decompression failed at 0x{offset:X}")
        return None

    # Find compressed size (accurate: decompress tells us)
    compressed_data = rom_data[offset:offset + 39]  # header minimum

    # Scan for terminator
    pos = offset + 39
    while pos < len(rom_data):
        if rom_data[pos] == 0x00:
            compressed_data = rom_data[offset:pos + 1]
            break
        pos += 1

    os.makedirs(output_dir, exist_ok=True)

    def safe_write(name, data):
        path = os.path.join(output_dir, name)
        with open(path, 'wb') as f:
            f.write(data)
        return path

    hex_off = f"{offset:08X}"
    info = {}

    # Header only
    path = safe_write(f"{prefix}{hex_off}_header.bin", compressed_data[:39])
    info['header_file'] = path

    # Compressed (header + stream)
    path = safe_write(f"{prefix}{hex_off}_compressed.bin", compressed_data)
    info['compressed_file'] = path
    info['compressed_size'] = len(compressed_data)

    # Decompressed
    path = safe_write(f"{prefix}{hex_off}_decompressed.bin", dec)
    info['decompressed_file'] = path
    info['decompressed_size'] = len(dec)

    return info


def extract_all(rom_data, output_dir='assets', min_score=12, max_assets=None,
                prefix=''):
    """Extract all valid assets from ROM.

    Args:
        rom_data: Full ROM bytes.
        output_dir: Output directory.
        min_score: Minimum header score.
        max_assets: Maximum number to extract.
        prefix: Filename prefix.

    Returns:
        List of extraction info dicts.
    """
    assets = scan_rom(rom_data, min_score=min_score, max_count=max_assets)
    results = []

    print(f"Found {len(assets)} candidate assets (min_score={min_score})")
    valid_count = sum(1 for a in assets if a['valid'])

    if max_assets and len(assets) > max_assets:
        assets = assets[:max_assets]

    extracted = 0
    for i, asset in enumerate(assets):
        off = asset['offset']
        info = extract_asset(rom_data, off, output_dir,
                             prefix=f"{prefix}{i:04d}_")
        if info:
            results.append(info)
            extracted += 1
            status = 'OK' if asset['valid'] else 'FAIL'
            print(f"  [{i:04d}] 0x{off:06X} -> {os.path.basename(info['decompressed_file'])} "
                  f"({info['decompressed_size']}B from {info['compressed_size']}B comp) [{status}]")

    print(f"\nExtracted {extracted}/{len(assets)} valid assets to {output_dir}/")
    return results


# ── Round-trip Verification ──────────────────────────────────────────────

def verify_asset(rom_data, offset, use_set2=True):
    """Verify round-trip for a single asset.

    Extracts from ROM, decompresses, re-compresses, and checks integrity.

    Args:
        rom_data: Full ROM bytes.
        offset: ROM offset of PAC1 header.
        use_set2: Use Set2-enhanced compression.

    Returns:
        dict with results, or None on failure.
    """
    h = parse_header(rom_data, offset)
    if h is None:
        return None

    dec = pac1_decompress(rom_data, offset, max_output=0x20000)
    if dec is None:
        return {'offset': offset, 'valid': False, 'reason': 'decompress_failed'}

    # Re-compress with the same header (but may produce different output)
    header = rom_data[offset:offset + 39]
    try:
        recompressed = pac1_compress(dec, header=header, use_set2=use_set2)
    except Exception as e:
        return {'offset': offset, 'valid': False, 'reason': f'recompress_exception: {e}'}

    # Decompress again
    redec = pac1_decompress(recompressed, 0, max_output=0x20000)
    if redec is None:
        return {'offset': offset, 'valid': False, 'reason': 're_decompress_failed'}

    match = (redec == dec)
    orig_comp_size = 0
    pos = offset + 39
    while pos < len(rom_data):
        if rom_data[pos] == 0x00:
            orig_comp_size = pos - offset + 1
            break
        pos += 1

    new_comp_size = len(recompressed)

    return {
        'offset': offset,
        'valid': match,
        'decompressed_size': len(dec),
        'original_comp_size': orig_comp_size,
        'new_comp_size': new_comp_size,
        'size_change': new_comp_size - orig_comp_size,
        'improvement': orig_comp_size - new_comp_size,
        'reason': None if match else 'data_mismatch',
    }


def verify_all(rom_data, min_score=12, max_assets=None, use_set2=True):
    """Verify round-trip for all assets."""
    assets = scan_rom(rom_data, min_score=min_score, max_count=max_assets)
    results = []

    print(f"Verifying {len(assets)} assets...")
    ok = 0
    fail = 0
    total_improvement = 0

    for i, asset in enumerate(assets):
        off = asset['offset']
        result = verify_asset(rom_data, off, use_set2=use_set2)
        if result is None:
            print(f"  [{i:04d}] 0x{off:06X} -- skipped (parse fail)")
            continue
        results.append(result)

        if result['valid']:
            ok += 1
            impr = result.get('improvement', 0)
            total_improvement += impr
            if impr != 0:
                sig = '+' if impr < 0 else '+'
                print(f"  [{i:04d}] 0x{off:06X} [OK] {result['decompressed_size']}B "
                      f"({result['original_comp_size']}->{result['new_comp_size']}B, "
                      f"Delta={result['size_change']:+d})")
            else:
                print(f"  [{i:04d}] 0x{off:06X} [OK] {result['decompressed_size']}B "
                      f"({result['original_comp_size']}B)")
        else:
            fail += 1
            print(f"  [{i:04d}] 0x{off:06X} [FAIL] {result['reason']}")

    print(f"\nRound-trip: {ok} OK, {fail} FAIL, total Delta={total_improvement:+d}B")
    return results


# ── CLI ──────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description='DKC2 PAC1 Asset Extraction Pipeline')

    parser.add_argument('--rom', required=True,
                        help='Path to DKC2 ROM file')
    parser.add_argument('--offset', type=lambda x: int(x, 16),
                        help='ROM offset of PAC1 header (hex)')
    parser.add_argument('--output-dir', default='assets',
                        help='Output directory for extracted assets')
    parser.add_argument('--min-score', type=int, default=12,
                        help='Minimum header score (default: 12)')
    parser.add_argument('--max', type=int, default=0,
                        help='Maximum assets to process')
    parser.add_argument('--prefix', default='',
                        help='Filename prefix')

    parser.add_argument('--scan', action='store_true',
                        help='Scan ROM for PAC1 headers')
    parser.add_argument('--extract', action='store_true',
                        help='Extract a single asset (requires --offset)')
    parser.add_argument('--extract-all', action='store_true',
                        help='Extract all valid assets')
    parser.add_argument('--list', action='store_true',
                        help='List assets with summary')
    parser.add_argument('--verify', action='store_true',
                        help='Round-trip verify a single asset (requires --offset)')
    parser.add_argument('--verify-all', action='store_true',
                        help='Round-trip verify all assets')
    parser.add_argument('--simple', action='store_true',
                        help='Use Set1-only compression (v1)')

    args = parser.parse_args()

    with open(args.rom, 'rb') as f:
        rom_data = f.read()

    max_count = args.max if args.max > 0 else None

    if args.scan or args.list:
        assets = scan_rom(rom_data, min_score=args.min_score,
                          max_count=max_count)
        if not assets:
            print("No PAC1 headers found.")
            return

        print(f"\n{'Offset':>10} {'Score':>5} {'F1':>3} {'F2':>3} {'D1':>3} {'D2':>3} "
              f"{'DW':>6} {'Comp':>6} {'Decomp':>7} {'Valid':>6}  LUT[0..3]")
        print("-" * 95)
        for asset in assets:
            off = asset['offset']
            lut4 = ' '.join(f"{w:04X}" for w in asset['lut'][:4])
            valid = '[OK]' if asset['valid'] else '[FAIL]'
            print(f"  0x{off:06X}  {asset['score']:3d}  {asset['fill1']:02X}  "
                  f"{asset['fill2']:02X}  {asset['dir1']:02X}  {asset['dir2']:02X}  "
                  f"{asset['dirw']:04X}  {asset['size_compressed']:5d}B  "
                  f"{asset['size_decompressed']:5d}B  {valid:>6}  {lut4}")

        valid_count = sum(1 for a in assets if a['valid'])
        print(f"\nTotal: {len(assets)} candidates, {valid_count} valid")

    elif args.extract:
        if args.offset is None:
            print("--offset required for --extract")
            sys.exit(1)
        info = extract_asset(rom_data, args.offset, args.output_dir,
                             prefix=args.prefix)
        if info:
            print(f"Extracted asset at 0x{args.offset:X}:")
            print(f"  Header:     {info['header_file']}")
            print(f"  Compressed: {info['compressed_file']} ({info['compressed_size']}B)")
            print(f"  Decompressed: {info['decompressed_file']} ({info['decompressed_size']}B)")

    elif args.extract_all:
        extract_all(rom_data, output_dir=args.output_dir,
                    min_score=args.min_score, max_assets=max_count,
                    prefix=args.prefix)

    elif args.verify:
        if args.offset is None:
            print("--offset required for --verify")
            sys.exit(1)
        result = verify_asset(rom_data, args.offset,
                              use_set2=not args.simple)
        if result is None:
            print(f"Invalid header at 0x{args.offset:X}")
        elif result['valid']:
            print(f"[OK] 0x{args.offset:X}: round-trip OK "
                  f"({result['original_comp_size']}->{result['new_comp_size']}B, "
                  f"Delta={result['size_change']:+d})")
        else:
            print(f"[FAIL] 0x{args.offset:X}: {result['reason']}")

    elif args.verify_all:
        verify_all(rom_data, min_score=args.min_score,
                   max_assets=max_count, use_set2=not args.simple)

    else:
        parser.print_help()


if __name__ == '__main__':
    main()
