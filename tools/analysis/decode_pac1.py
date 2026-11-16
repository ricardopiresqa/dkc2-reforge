"""DKC2 Big Data (PAC1) decompressor and header scanner."""
import argparse
import struct
import sys

SET1 = 1
SET2 = 2
SET2_WIDE = 3


def build_lut():
    lo = [b >> 4 for b in range(256)]
    hi = [(b & 0x0F) << 4 for b in range(256)]
    return lo, hi


LO, HI = build_lut()


def parse_header(data, offset):
    h = data[offset:offset+39]
    if len(h) < 39:
        return None
    return {
        'reserved': h[0],
        'fill1': h[1], 'fill2': h[2],
        'dir1': h[3], 'dir2': h[4],
        'dirw': struct.unpack_from('<H', h, 5)[0],
        'lut': list(struct.unpack_from('<16H', h, 7)),
    }


def header_score(data, offset):
    h = data[offset:offset+39]
    if len(h) < 39 or h[0] != 0x00:
        return 0
    valid = 0
    all_zero = 0
    sequential = 0
    prev = None
    for i in range(16):
        w = struct.unpack_from('<H', h, 7 + i*2)[0]
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


class BitReader:
    def __init__(self, data, offset):
        self.data = data
        self.pos = offset

    def read(self):
        if self.pos >= len(self.data):
            raise ValueError("stream underflow")
        b = self.data[self.pos]
        self.pos += 1
        return b


def decompress(rom, offset, max_output=0x20000):
    h = rom[offset:offset+39]
    if len(h) < 39:
        return None

    fill1, fill2 = h[1], h[2]
    dir1, dir2 = h[3], h[4]
    dirw = struct.unpack_from('<H', h, 5)[0]
    lut = list(struct.unpack_from('<16H', h, 7))

    src = BitReader(rom, offset + 39)
    out = bytearray()
    _42 = 0
    _46 = 0
    state = SET1

    def emit(b):
        out.append(b & 0xFF)

    try:
        while len(out) < max_output:
            if state == SET1:
                b = src.read()
                _46 = b
                cmd = b >> 4

                if cmd == 0:
                    count = b & 0x0F
                    if count == 0:
                        break
                    for _ in range(count):
                        emit(src.read())
                    state = SET1

                elif cmd == 1:
                    hi_val = HI[b]
                    nxt = src.read()
                    emit(hi_val | LO[nxt])
                    _42 = nxt
                    state = SET2

                elif cmd == 2:
                    hi_val = HI[b]
                    nxt1 = src.read()
                    emit(hi_val | LO[nxt1])
                    hi_val2 = HI[nxt1]
                    nxt2 = src.read()
                    emit(hi_val2 | LO[nxt2])
                    _42 = nxt2
                    state = SET2

                elif cmd == 3:
                    count = (b & 0x0F) + 3
                    fill = src.read()
                    for _ in range(count):
                        emit(fill)
                    state = SET1

                elif cmd == 4:
                    count = (b & 0x0F) + 3
                    for _ in range(count):
                        emit(fill1)
                    state = SET1

                elif cmd == 5:
                    count = (b & 0x0F) + 3
                    for _ in range(count):
                        emit(fill2)
                    state = SET1

                elif cmd == 6:
                    emit(dirw & 0xFF)
                    emit((dirw >> 8) & 0xFF)
                    state = SET2_WIDE

                elif cmd == 7:
                    emit(dir1)
                    state = SET2_WIDE

                elif cmd == 8:
                    emit(dir2)
                    state = SET2_WIDE

                elif cmd == 9:
                    off = (b & 0x0F) + 2
                    if len(out) >= off:
                        b1 = out[-off]
                        b2 = out[-off+1] if off > 1 else 0
                        emit(b1)
                        emit(b2)
                    state = SET1

                elif cmd == 10:
                    count = (b & 0x0F) + 3
                    off = src.read()
                    src_pos = len(out) - count - off
                    if src_pos < 0:
                        src_pos = 0
                    for _ in range(count):
                        emit(out[src_pos])
                        src_pos += 1
                    state = SET1

                elif cmd == 11:
                    count = (b & 0x0F) + 3
                    b1 = src.read()
                    b2 = src.read()
                    _46 = b2
                    off = ((b1 << 8) | b2) >> 4
                    off += 0x103
                    src_pos = len(out) - off
                    if src_pos < 0:
                        src_pos = 0
                    for _ in range(count):
                        emit(out[src_pos])
                        src_pos += 1
                    state = SET2_WIDE

                elif cmd == 12:
                    count = (b & 0x0F) + 3
                    b1 = src.read()
                    b2 = src.read()
                    off = (b1 << 8) | b2
                    src_pos = len(out) - off
                    if src_pos < 0:
                        src_pos = 0
                    for _ in range(count):
                        emit(out[src_pos])
                        src_pos += 1
                    state = SET1

                elif cmd == 13:
                    if out:
                        emit(out[-1])
                    state = SET2_WIDE

                elif cmd == 14:
                    if len(out) >= 2:
                        b_first = out[-2]
                        b_second = out[-1]
                        emit(b_first)
                        emit(b_second)
                    state = SET2_WIDE

                elif cmd == 15:
                    off = ((b & 0x0F) * 2) + 7
                    tw = src.data[src.pos + off - 1] if src.pos + off - 1 < len(src.data) else 0
                    emit(tw)
                    tw2 = src.data[src.pos + off] if src.pos + off < len(src.data) else 0
                    emit(tw2)
                    state = SET1

            elif state == SET2:
                b = _42
                cmd = b & 0x0F

                if cmd == 0:
                    nxt = src.read()
                    _42 = nxt
                    _46 = nxt
                    count = LO[nxt]
                    if count == 0:
                        break
                    for _ in range(count):
                        b1 = src.read()
                        _42 = b1
                        b2 = src.read()
                        _42 = b2
                        emit(HI[nxt] | LO[b2])
                    state = SET2_WIDE

                elif cmd == 1:
                    emit(src.read())
                    state = SET1

                elif cmd == 2:
                    emit(src.read())
                    emit(src.read())
                    state = SET1

                elif cmd == 3:
                    nxt = src.read()
                    _42 = nxt
                    _46 = nxt
                    count = LO[nxt] + 3
                    fill_hi = HI[nxt]
                    nxt2 = src.read()
                    _42 = nxt2
                    fill = fill_hi | LO[nxt2]
                    for _ in range(count):
                        emit(fill)
                    state = SET2

                elif cmd == 4:
                    nxt = src.read()
                    _42 = nxt
                    count = LO[nxt] + 3
                    for _ in range(count):
                        emit(fill1)
                    state = SET2

                elif cmd == 5:
                    nxt = src.read()
                    _42 = nxt
                    count = LO[nxt] + 3
                    for _ in range(count):
                        emit(fill2)
                    state = SET2

                elif cmd == 6:
                    emit(dirw & 0xFF)
                    emit((dirw >> 8) & 0xFF)
                    state = SET1

                elif cmd == 7:
                    emit(dir1)
                    state = SET1

                elif cmd == 8:
                    emit(dir2)
                    state = SET1

                elif cmd == 9:
                    nxt = src.read()
                    _42 = nxt
                    off = LO[nxt] + 2
                    if len(out) >= off:
                        b1 = out[-off]
                        b2 = out[-off+1] if off > 1 else 0
                        emit(b1)
                        emit(b2)
                    state = SET2

                elif cmd == 10:
                    nxt = src.read()
                    _42 = nxt
                    _46 = nxt
                    count = LO[nxt] + 3
                    offset_hi = HI[nxt]
                    nxt2 = src.read()
                    _42 = nxt2
                    off = offset_hi | LO[nxt2]
                    src_pos = len(out) - count - off
                    if src_pos < 0:
                        src_pos = 0
                    for _ in range(count):
                        emit(out[src_pos])
                        src_pos += 1
                    state = SET2

                elif cmd == 11:
                    nxt = src.read()
                    _42 = nxt
                    count = LO[nxt] + 3
                    lo_nib = nxt & 0x0F
                    lo_byte = src.read()
                    off = (lo_nib << 8 | lo_byte) + 0x103
                    src_pos = len(out) - off
                    if src_pos < 0:
                        src_pos = 0
                    for _ in range(count):
                        emit(out[src_pos])
                        src_pos += 1
                    state = SET1

                elif cmd == 12:
                    nxt = src.read()
                    _42 = nxt
                    count = LO[nxt] + 3
                    lo_nib = nxt & 0x0F
                    lo_byte = src.read()
                    offset_raw = (lo_nib << 8 | lo_byte) << 4
                    nxt2 = src.read()
                    _42 = nxt2
                    low4 = LO[nxt2]
                    off = offset_raw | low4
                    src_pos = len(out) - off
                    if src_pos < 0:
                        src_pos = 0
                    for _ in range(count):
                        emit(out[src_pos])
                        src_pos += 1
                    state = SET2

                elif cmd == 13:
                    if out:
                        emit(out[-1])
                    state = SET1

                elif cmd == 14:
                    if len(out) >= 2:
                        b_first = out[-2]
                        b_second = out[-1]
                        emit(b_first)
                        emit(b_second)
                    state = SET1

                elif cmd == 15:
                    nxt = src.read()
                    _46 = nxt
                    off = ((nxt & 0xF0) >> 3) + 7
                    tw = src.data[src.pos + off - 1] if src.pos + off - 1 < len(src.data) else 0
                    emit(tw)
                    tw2 = src.data[src.pos + off] if src.pos + off < len(src.data) else 0
                    emit(tw2)
                    state = SET2_WIDE

            elif state == SET2_WIDE:
                b = _46
                cmd = b & 0x0F

                if cmd == 0:
                    nxt = src.read()
                    _42 = nxt
                    _46 = nxt
                    count = LO[nxt]
                    if count == 0:
                        break
                    for _ in range(count):
                        b1 = src.read()
                        _42 = b1
                        b2 = src.read()
                        _42 = b2
                        emit(HI[nxt] | LO[b2])
                    state = SET2_WIDE

                elif cmd == 1:
                    emit(src.read())
                    state = SET1

                elif cmd == 2:
                    emit(src.read())
                    emit(src.read())
                    state = SET1

                elif cmd == 3:
                    nxt = src.read()
                    _42 = nxt
                    _46 = nxt
                    count = LO[nxt] + 3
                    fill_hi = HI[nxt]
                    nxt2 = src.read()
                    _42 = nxt2
                    fill = fill_hi | LO[nxt2]
                    for _ in range(count):
                        emit(fill)
                    state = SET2

                elif cmd == 4:
                    nxt = src.read()
                    _42 = nxt
                    count = LO[nxt] + 3
                    for _ in range(count):
                        emit(fill1)
                    state = SET2

                elif cmd == 5:
                    nxt = src.read()
                    _42 = nxt
                    count = LO[nxt] + 3
                    for _ in range(count):
                        emit(fill2)
                    state = SET2

                elif cmd == 6:
                    emit(dirw & 0xFF)
                    emit((dirw >> 8) & 0xFF)
                    state = SET1

                elif cmd == 7:
                    emit(dir1)
                    state = SET1

                elif cmd == 8:
                    emit(dir2)
                    state = SET1

                elif cmd == 9:
                    nxt = src.read()
                    _42 = nxt
                    off = LO[nxt] + 2
                    if len(out) >= off:
                        b1 = out[-off]
                        b2 = out[-off+1] if off > 1 else 0
                        emit(b1)
                        emit(b2)
                    state = SET2

                elif cmd == 10:
                    nxt = src.read()
                    _42 = nxt
                    _46 = nxt
                    count = LO[nxt] + 3
                    offset_hi = HI[nxt]
                    nxt2 = src.read()
                    _42 = nxt2
                    off = offset_hi | LO[nxt2]
                    src_pos = len(out) - count - off
                    if src_pos < 0:
                        src_pos = 0
                    for _ in range(count):
                        emit(out[src_pos])
                        src_pos += 1
                    state = SET2

                elif cmd == 11:
                    nxt = src.read()
                    _42 = nxt
                    count = LO[nxt] + 3
                    lo_nib = nxt & 0x0F
                    lo_byte = src.read()
                    off = (lo_nib << 8 | lo_byte) + 0x103
                    src_pos = len(out) - off
                    if src_pos < 0:
                        src_pos = 0
                    for _ in range(count):
                        emit(out[src_pos])
                        src_pos += 1
                    state = SET1

                elif cmd == 12:
                    nxt = src.read()
                    _42 = nxt
                    count = LO[nxt] + 3
                    lo_nib = nxt & 0x0F
                    lo_byte = src.read()
                    offset_raw = (lo_nib << 8 | lo_byte) << 4
                    nxt2 = src.read()
                    _42 = nxt2
                    low4 = LO[nxt2]
                    off = offset_raw | low4
                    src_pos = len(out) - off
                    if src_pos < 0:
                        src_pos = 0
                    for _ in range(count):
                        emit(out[src_pos])
                        src_pos += 1
                    state = SET2

                elif cmd == 13:
                    if out:
                        emit(out[-1])
                    state = SET1

                elif cmd == 14:
                    if len(out) >= 2:
                        b_first = out[-2]
                        b_second = out[-1]
                        emit(b_first)
                        emit(b_second)
                    state = SET1

                elif cmd == 15:
                    nxt = src.read()
                    _46 = nxt
                    off = ((nxt & 0xF0) >> 3) + 7
                    tw = src.data[src.pos + off - 1] if src.pos + off - 1 < len(src.data) else 0
                    emit(tw)
                    tw2 = src.data[src.pos + off] if src.pos + off < len(src.data) else 0
                    emit(tw2)
                    state = SET2_WIDE

            else:
                break

    except (ValueError, IndexError):
        pass

    return bytes(out) if out else None


def scan_headers(data, limit=20):
    candidates = []
    for off in range(len(data) - 39):
        score = header_score(data, off)
        if score > 0:
            h = data[off:off+39]
            f1, f2 = h[1], h[2]
            d1, d2 = h[3], h[4]
            dw = struct.unpack_from('<H', h, 5)[0]
            lut = list(struct.unpack_from('<16H', h, 7))
            candidates.append((off, score, f1, f2, d1, d2, dw, lut))
    candidates.sort(key=lambda x: (-x[1], x[0]))
    candidates = candidates[:limit]
    results = []
    for off, score, f1, f2, d1, d2, dw, lut in candidates:
        dec = decompress(data, off, max_output=256)
        dec_info = f"ok:{len(dec)}B" if dec else "fail"
        results.append((off, score, f1, f2, d1, d2, dw, lut[:4], dec_info))
    return results


def main():
    parser = argparse.ArgumentParser(description="DKC2 PAC1 (Big Data) decompressor")
    parser.add_argument("--rom", required=True)
    parser.add_argument("--offset", type=lambda x: int(x, 16), help="ROM offset of PAC1 header (hex)")
    parser.add_argument("--output", help="Output file for decompressed data")
    parser.add_argument("--scan", action="store_true", help="Scan ROM for PAC1 headers")
    args = parser.parse_args()

    with open(args.rom, "rb") as f:
        rom = f.read()

    if args.scan:
        results = scan_headers(rom, limit=20)
        if not results:
            print("No PAC1 headers found.")
            return
        print(f"{'Offset':>10} {'Score':>5} {'F1':>3} {'F2':>3} {'D1':>3} {'D2':>3} {'DW':>6}  {'LUT[0..3]':<20} {'Result':>12}")
        print("-" * 85)
        for off, score, f1, f2, d1, d2, dw, lut4, dec in results:
            lut_str = " ".join(f"{w:02X}" for w in lut4)
            bank = f"C0+{(off-0x200000)//0x8000:02X}" if off >= 0x200000 else f"{off//0x8000:02X}"
            snes_guess = f"${bank}:{off & 0x7FFF:04X}"
            print(f"  {off:08X}  {score:3d}  {f1:02X}  {f2:02X}  {d1:02X}  {d2:02X}  {dw:04X}  {lut_str:<20} {dec:>12}  {snes_guess}")

    elif args.offset is not None:
        header = parse_header(rom, args.offset)
        if header is None:
            print(f"Invalid header at ROM 0x{args.offset:X}")
            sys.exit(1)
        print(f"Header at ROM 0x{args.offset:X}:")
        print(f"  Fill:  0x{header['fill1']:02X}, 0x{header['fill2']:02X}")
        print(f"  Direct: 0x{header['dir1']:02X}, 0x{header['dir2']:02X}, word=0x{header['dirw']:04X}")
        print(f"  LUT: {' '.join(f'{w:02X}' for w in header['lut'])}")

        dec = decompress(rom, args.offset)
        if dec is None:
            print("Decompression failed.")
            sys.exit(1)
        print(f"Decompressed: {len(dec)} bytes")
        print(f"First 64: {' '.join(f'{b:02X}' for b in dec[:64])}")
        if args.output:
            with open(args.output, "wb") as f:
                f.write(dec)
            print(f"Wrote to {args.output}")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
