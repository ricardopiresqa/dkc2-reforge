"""Trace: compare both decoders byte by byte with state context."""
import sys; sys.path.insert(0, 'tools/analysis')
import decode_pac1 as ref_mod
from _decompress import decompress, LO, HI, SET1, SET2, SET2_WIDE

data = open('tools/analysis/samples/asset_b80_8F54_1266B.bin', 'rb').read()
out_ref = ref_mod.decompress(data, 0)
out_new = decompress(data)

print(f"Sizes: ref={len(out_ref)} new={len(out_new)}" if out_ref else "ref=None" if out_ref is None else f"ref={len(out_ref)}", end="")
if out_ref is not None and out_new is not None:
    print(f" new={len(out_new)}")
    print(f"Same size: {len(out_ref) == len(out_new)}")
    
    # Instrument the decompress to trace
    from _decompress import DecompressContext
    
    # Monkey-patch the dispatch to add tracing
    orig_init = DecompressContext.__init__
    
    ref_trace = []
    class RefTracer:
        pass
    
    # Run reference with tracing by reading the source
    import types
    
    # Just compare raw stream positions - build a simple trace by 
    # wrapping the read_byte and write_byte calls
    orig_write = DecompressContext.write_byte
    orig_read = DecompressContext.read_byte
    
    new_trace = []
    def traced_write(ctx, b):
        new_trace.append(('W', len(ctx.dest), b))
        return orig_write(ctx, b)
    DecompressContext.write_byte = traced_write
    
    # Build header trace too
    state_events = []
    orig_set1 = None
    
    # Let me just use a simpler approach: re-run with the actual module
    # Add a step counter to decompress
    pass

# Instead, let's find WHERE in the stream the divergence happens
# by looking at what the reference writes vs what ours writes
print("\n--- Diff positions ---")
if out_ref and out_new:
    count = 0
    for i in range(min(len(out_ref), len(out_new))):
        if out_ref[i] != out_new[i]:
            print(f"  [{i:4d}] ref={out_ref[i]:02X} new={out_new[i]:02X}")
            count += 1
            if count >= 20:
                print("  ... (truncated)")
                break
