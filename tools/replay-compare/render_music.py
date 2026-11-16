"""Render Pirate Panic's music from the captured SPC700 snapshot (local, ROM-derived).

Input: assets-raw/pirate/pirate-panic-music.spc (music_spc_capture.lua, gameplay frame 2).
ffmpeg's libgme plays the snapshot; the loop period is the lag with the best
normalized correlation of the sample stream after the intro. Output (ignored by git):
assets/music/pirate/pirate_panic_intro.ogg (start -> loop start) and
pirate_panic_loop.ogg (one period), played back to back by main/sound.lua.
APPROXIMATION: the snapshot starts a couple of frames into the song.
"""
import subprocess
import sys
import wave
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
SPC = ROOT / "assets-raw/pirate/pirate-panic-music.spc"
OUT = ROOT / "assets/music/pirate"
RATE, SECONDS = 32000, 240


def render(path):
    subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-f", "libgme", "-i", str(SPC),
                    "-t", str(SECONDS), "-ar", str(RATE), "-ac", "2", str(path)], check=True)
    with wave.open(str(path)) as handle:
        data = np.frombuffer(handle.readframes(handle.getnframes()), dtype=np.int16)
    return data.reshape(-1, 2).astype(np.float64)


def find_loop(samples):
    """(loop_start, period) in samples: best repeat of a 4 s probe window taken at 20 s."""
    mono = samples.mean(axis=1)
    probe_start, probe = 20 * RATE, 4 * RATE
    window = mono[probe_start:probe_start + probe]
    best = (0.0, 0)
    for period in range(20 * RATE, 150 * RATE, RATE // 100):  # 10 ms steps, refined below
        other = mono[probe_start + period:probe_start + period + probe]
        if len(other) < probe:
            break
        score = float(np.dot(window, other) / (np.linalg.norm(window) * np.linalg.norm(other) + 1e-9))
        if score > best[0]:
            best = (score, period)
    score, period = best
    for fine in range(period - RATE // 100, period + RATE // 100):
        other = mono[probe_start + fine:probe_start + fine + probe]
        value = float(np.dot(window, other) / (np.linalg.norm(window) * np.linalg.norm(other) + 1e-9))
        if value > score:
            score, period = value, fine
    # earliest start where the stream repeats with this period
    start = probe_start
    while start > 0 and np.allclose(mono[start - RATE // 10:start], mono[start - RATE // 10 + period:start + period],
                                    atol=64):
        start -= RATE // 10
    return start, period, score


def encode(samples, path):
    raw = path.with_suffix(".wav")
    with wave.open(str(raw), "wb") as handle:
        handle.setnchannels(2)
        handle.setsampwidth(2)
        handle.setframerate(RATE)
        handle.writeframes(samples.astype(np.int16).tobytes())
    subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", str(raw), "-c:a", "libvorbis",
                    "-q:a", "6", str(path)], check=True)
    raw.unlink()


def export():
    OUT.mkdir(parents=True, exist_ok=True)
    samples = render(OUT / "_render.wav")
    (OUT / "_render.wav").unlink()
    start, period, score = find_loop(samples)
    encode(samples[:start], OUT / "pirate_panic_intro.ogg")
    encode(samples[start:start + period], OUT / "pirate_panic_loop.ogg")
    return start / RATE, period / RATE, score


if __name__ == "__main__":
    start, period, score = export()
    print("loop start %.2f s, period %.2f s, correlation %.4f" % (start, period, score))
    sys.exit(0 if score > 0.98 else 1)
