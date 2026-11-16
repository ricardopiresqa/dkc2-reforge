"""Render the 31 Music Test tracks from their SPC700 snapshots (local, ROM-derived).

Input: assets-raw/pirate/music-test3/track-NN.spc (music_test_spc_capture.lua; each taken
240 frames into its song, checked by music id), except songs 2 (title) and 17 (Opening):
boot-NN.spc from boot_music_spc_capture.lua, taken as each song starts. ffmpeg's libgme plays a snapshot; the loop is found as in
render_music.py (correlation of a 4 s probe at 20 s), here from 4 s periods up. Output
(ignored by git): assets/music/pirate/test/track_NN_intro.ogg + track_NN_loop.ogg for a
loop with correlation > 0.98, else track_NN.ogg (a one-shot, trailing silence cut).
APPROXIMATIONS: the first 4 s of the other songs are missing (snapshot 240 frames in); these
music-test snapshots do not repeat sample-exactly in libgme (best loop correlation
0.14-0.84 over 4-330 s periods, against > 0.98 for the gameplay snapshot), so most
tracks are rendered as 180 s one-shots.
"""
import subprocess
import sys
import wave
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "assets-raw/pirate/music-test3"  # v3: snapshots checked by music id ($1C)
OUT = ROOT / "assets/music/pirate/test"
RATE, SECONDS = 32000, 180
BOOT = (2, 17)  # songs the boot plays from their first frame
sys.path.insert(0, str(Path(__file__).resolve().parent))
import render_music as base  # noqa: E402


def render(spc, path):
    subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-f", "libgme", "-i", str(spc),
                    "-t", str(SECONDS), "-ar", str(RATE), "-ac", "2", str(path)], check=True)
    with wave.open(str(path)) as handle:
        data = np.frombuffer(handle.readframes(handle.getnframes()), dtype=np.int16)
    return data.reshape(-1, 2).astype(np.float64)


def find_loop(samples):
    mono = samples.mean(axis=1)
    probe_start, probe = 20 * RATE, 4 * RATE
    window = mono[probe_start:probe_start + probe]
    if np.linalg.norm(window) < 1:
        return None
    best = (0.0, 0)
    for period in range(4 * RATE, 150 * RATE, RATE // 100):
        other = mono[probe_start + period:probe_start + period + probe]
        if len(other) < probe:
            break
        score = float(np.dot(window, other) / (np.linalg.norm(window) * np.linalg.norm(other) + 1e-9))
        if score > best[0]:
            best = (score, period)
    score, period = best
    if score <= 0.98:
        return None
    start = probe_start
    while start > 0 and np.allclose(mono[start - RATE // 10:start], mono[start - RATE // 10 + period:start + period],
                                    atol=64):
        start -= RATE // 10
    return start, period, score


def export_track(number):
    spc = SOURCE / ("boot-%02d.spc" % number if number in BOOT else "track-%02d.spc" % number)
    work = OUT / ("_render_%02d.wav" % number)
    samples = render(spc, work)
    work.unlink()
    loop = find_loop(samples)
    if loop:
        start, period, score = loop
        base.encode(samples[:start], OUT / ("track_%02d_intro.ogg" % number))
        base.encode(samples[start:start + period], OUT / ("track_%02d_loop.ogg" % number))
        return number, "loop", round(start / RATE, 2), round(period / RATE, 2), round(score, 4)
    loud = np.nonzero(np.abs(samples).max(axis=1) > 64)[0]
    end = int(loud[-1]) + RATE // 10 if len(loud) else RATE
    base.encode(samples[:end], OUT / ("track_%02d.ogg" % number))
    return number, "once", round(end / RATE, 2)


def export_victory():
    """The level-end music: Pirate Panic's song jumped to its victory part by the goal hit
    ($FB 3, $FE, $FA; goal-route-t8.csv 4916), from goal-victory-4925.spc (goal_probe_capture t9;
    4918 is still silent).
    -> assets/music/pirate/victory.ogg, a one-shot (trailing silence cut)."""
    work = OUT / "_render_victory.wav"
    samples = render(ROOT / "assets-raw/pirate/goal-victory-4925.spc", work)
    work.unlink()
    loud = np.nonzero(np.abs(samples).max(axis=1) > 64)[0]
    end = int(loud[-1]) + RATE // 10 if len(loud) else RATE
    base.encode(samples[:end], OUT.parent / "victory.ogg")
    return "victory", round(end / RATE, 2), find_loop(samples)


def export():
    OUT.mkdir(parents=True, exist_ok=True)
    with ThreadPoolExecutor(max_workers=6) as pool:
        return list(pool.map(export_track, range(1, 32)))


if __name__ == "__main__":
    if sys.argv[1:] == ["--victory"]:
        print(export_victory())
        sys.exit(0)
    for row in export():
        print(row)
