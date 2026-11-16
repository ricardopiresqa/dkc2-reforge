"""PAC1 ROM Patching — Recompress and inject assets back into ROM.

Supports:
- Recompressing modified decompressed data.
- Checking if recompressed data fits in the original space.
- Creating a patched ROM with the new asset.

Usage:
    # Recompress and inject (must fit)
    python patch_rom.py --rom roms/dkc2.sfc --asset-offset 0x296B2A \\
        --input modified.bin --output patched.sfc

    # Recompress and check size (dry-run)
    python patch_rom.py --rom roms/dkc2.sfc --asset-offset 0x296B2A \\
        --input modified.bin --check
"""

import argparse
import os
import shutil
import struct
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'analysis'))

from decode_pac1 import decompress as pac1_decompress, parse_header
from compress_pac1 import compress as pac1_compress


# ── Recompression ────────────────────────────────────────────────────────

def find_compressed_boundary(rom_data, header_offset):
    """Find the end of compressed data starting at header_offset.

    Scans forward from header+39 for the terminator byte (0x00) that
    signals end-of-stream. The terminator is copy_or_return with count=0.

    Returns:
        (compressed_start, compressed_end) byte offsets in rom_data.
        compressed_start = header_offset
        compressed_end = first byte after the terminator.
    """
    pos = header_offset + 39
    while pos < len(rom_data):
        if rom_data[pos] == 0x00:
            return (header_offset, pos + 1)  # include terminator
        pos += 1
    return (header_offset, len(rom_data))


def recompress_asset(rom_data, header_offset, new_decompressed_data,
                     use_set2=True, simple=False):
    """Re-compress modified decompressed data and check if it fits.

    Args:
        rom_data: Original ROM bytes (to read original header and size).
        header_offset: ROM offset of the PAC1 header.
        new_decompressed_data: Modified raw data to compress.
        use_set2: Use Set2-enhanced compression.
        simple: Force Set1-only compression.

    Returns:
        dict with:
            success: True if recompression succeeded and fits.
            header: 39-byte header from original ROM.
            old_compressed: Original compressed bytes (header+stream).
            new_compressed: Recompressed bytes (header+stream).
            old_size: Original compressed size.
            new_size: New compressed size.
            fits: True if new_size <= old_size (padded if smaller).
            padding_needed: old_size - new_size (negative if doesn't fit).
            error: Error message if failed.
    """
    # Validate header
    h = parse_header(rom_data, header_offset)
    if h is None:
        return {'success': False, 'error': 'Invalid PAC1 header'}

    # Get original header bytes
    header = rom_data[header_offset:header_offset + 39]

    # Find original compressed boundary
    orig_start, orig_end = find_compressed_boundary(rom_data, header_offset)
    old_compressed = rom_data[orig_start:orig_end]
    old_size = len(old_compressed)

    # Decompress original to verify
    orig_dec = pac1_decompress(rom_data, header_offset, max_output=0x20000)
    if orig_dec is None:
        return {'success': False, 'error': 'Original decompression failed'}

    # Recompress new data
    try:
        new_compressed = pac1_compress(new_decompressed_data, header=header,
                                       use_set2=use_set2, simple=simple)
    except Exception as e:
        return {'success': False, 'error': f'Recompression failed: {e}'}

    new_size = len(new_compressed)
    fits = new_size <= old_size
    padding_needed = old_size - new_size

    return {
        'success': True,
        'fits': fits,
        'header': header,
        'old_compressed': old_compressed,
        'new_compressed': new_compressed,
        'old_size': old_size,
        'new_size': new_size,
        'padding_needed': padding_needed,
    }


# ── ROM Patching ─────────────────────────────────────────────────────────

def patch_rom(rom_data, header_offset, new_compressed, output_path):
    """Create a patched ROM with the new compressed asset at the given offset.

    Args:
        rom_data: Original ROM bytes.
        header_offset: Offset where the new data will be written.
        new_compressed: New compressed data (header + stream) to inject.
        output_path: Path for the patched ROM file.

    Returns:
        dict with result info.
    """
    orig_start, orig_end = find_compressed_boundary(rom_data, header_offset)
    old_size = orig_end - orig_start
    new_size = len(new_compressed)

    if new_size > old_size:
        return {
            'success': False,
            'error': f'New data ({new_size}B) exceeds original space ({old_size}B)',
        }

    # Build patched ROM
    patched = bytearray(rom_data)

    # Replace the asset
    patched[orig_start:orig_start + new_size] = new_compressed

    # Pad remaining space with zeros if new data is smaller
    if new_size < old_size:
        padding = bytes(old_size - new_size)
        patched[orig_start + new_size:orig_end] = padding

    # Write output
    os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)
    with open(output_path, 'wb') as f:
        f.write(patched)

    return {
        'success': True,
        'output_path': output_path,
        'offset': header_offset,
        'old_size': old_size,
        'new_size': new_size,
        'padding': old_size - new_size,
    }


# ── CLI ──────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description='DKC2 PAC1 ROM Patching — Recompress and inject assets')
    parser.add_argument('--rom', required=True,
                        help='Path to original DKC2 ROM')
    parser.add_argument('--asset-offset', '--offset', type=lambda x: int(x, 16),
                        required=True,
                        help='ROM offset of the PAC1 header (hex)')
    parser.add_argument('--input', '-i',
                        help='Modified decompressed data file (.bin)')
    parser.add_argument('--output', '-o',
                        help='Output patched ROM file')
    parser.add_argument('--check', action='store_true',
                        help='Dry-run: only check if new data fits')
    parser.add_argument('--simple', action='store_true',
                        help='Use Set1-only compression (v1)')

    args = parser.parse_args()

    with open(args.rom, 'rb') as f:
        rom_data = f.read()

    if args.input:
        with open(args.input, 'rb') as f:
            new_data = f.read()
    else:
        print("--input is required")
        sys.exit(1)

    result = recompress_asset(rom_data, args.asset_offset, new_data,
                              use_set2=not args.simple, simple=args.simple)

    if not result['success']:
        print(f"Error: {result['error']}")
        sys.exit(1)

    print(f"Asset at 0x{args.asset_offset:X}:")
    print(f"  Original compressed: {result['old_size']}B")
    print(f"  New compressed:      {result['new_size']}B")
    print(f"  Fits:                {'YES' if result['fits'] else 'NO'} "
          f"(needs {result['padding_needed']:+d}B)")

    if not result['fits']:
        print(f"\nERROR: New compressed data is {abs(result['padding_needed'])}B too large!")
        print("Cannot patch without expanding the asset. "
              "Options: reduce modifications, use simpler compression, "
              "or relocate the asset in the ROM.")
        sys.exit(1)

    if args.check:
        print("\n[OK] Asset fits. Use --output to create patched ROM.")
        return

    if args.output:
        patch_result = patch_rom(rom_data, args.asset_offset,
                                 result['new_compressed'], args.output)
        if patch_result['success']:
            print(f"\n[OK] Patched ROM written to: {patch_result['output_path']}")
            print(f"  Offset: 0x{patch_result['offset']:X}")
            print(f"  Space used: {patch_result['new_size']}/{patch_result['old_size']}B "
                  f"({patch_result['padding']}B padding)")
        else:
            print(f"\nError: {patch_result['error']}")
            sys.exit(1)
    else:
        print("\nUse --output to write patched ROM.")


if __name__ == '__main__':
    main()
