# ADR-006: Nibble-Pair Compression Format (CMP/PAC1)

## Status

Accepted — 2026-07-03

## Context

DKC2 stores level graphics, tilemaps, collision maps, and bulk assets in a proprietary compressed format. The decompressor runs on the SA-1 coprocessor from BW-RAM bank $BB. Two format variants exist:

- **PAC1** (4-byte signature `$50 $41 $43 $31`): header-based, self-contained packets. Used for most assets loaded at runtime.
- **Raw CMP** (no signature): inline command stream only. Used for assets embedded in code via `.incbin`.

Both share the same bytecode VM: 16 primary commands + 16 secondary commands, dispatched by nibble value. The format uses:

- Nibble reconstruction via WRAM lookup tables ($7E:2000, $7E:2100) rather than shift/and instructions
- LZ77-style back-references (distance + count) with variable-length encoding
- Two configurable fill bytes from header
- OR-copy operations that merge nibbles from source data using the LUT

The format was partially documented during the reverse-engineering phase but never formally recorded as an architectural decision.

## Decision

Formalize the nibble-pair compression format as the canonical asset storage format for the DKC2 Reforge project:

1. **Python decoder** (`tools/analysis/_decompress.py`): reference implementation with all 32 opcodes, tested against 490 real asset samples.
2. **WRAM table fallback**: LO/HI nibble approximation used when WRAM tables are unavailable — sufficient for all known assets.
3. **PAC1 round-trip** (`tools/analysis/test_compress_pac1.py`): 79 tests confirm compressor/decompressor symmetry.
4. **Documentation** in `docs/compression-format.md`: full spec including header structure, dispatch mechanism, all 32 commands, and pipeline integration.

## Consequences

### Positive

- Asset pipeline clear: compressed ROM → decode → Lua table → game runtime
- Any tool can decode DKC2 assets without SNES emulation
- 490 real samples validate correctness across diverse asset types (graphics, maps, collision data)
- Format is simple enough to implement in Lua for runtime decompression in Defold

### Negative

- Two opcodes (sec 9-12) depend on WRAM tables for exact behavior; LO/HI fallback may diverge for unknown asset types
- WRAM tables $7E:2000/$7E:2100 not yet extracted from ROM (require Mesen2 session)
- No formal fuzz testing against edge cases (empty streams, malformed headers)

### Risks

- Unknown assets may expose incorrect fallback behavior for sec ops 9-12
- ROM revision differences (US 1.0 vs others) may affect dispatch table layout but not command semantics

## Compliance

- All tools in `tools/analysis/` must reference `pac1_decode()` from `_decompress.py` as canonical decoder
- New decoders (Lua, other languages) must produce bit-identical output to the Python reference for all 490 samples
- Any format extension must be proposed via new ADR

## References

- `docs/compression-format.md` — full format specification
- `tools/analysis/_decompress.py` — reference decoder implementation
- `tools/analysis/_test_samples.py` — 490-sample validation suite
- `tools/analysis/test_compress_pac1.py` — 79 round-trip tests
- `tools/analysis/_wram_map.md` — WRAM address map for decompressor
