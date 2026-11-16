"""Render Pirate Panic's original sound effects from an SPC700 snapshot (local, ROM-derived).

Base: assets-raw/pirate/pirate-panic-sfxbase-1440.spc (sfx_base_spc_capture.lua: route-bot
frame 1440, after the first death: music stopped, level samples still loaded; renders
at -91 dB). A request is what B581FB sends: port 1/2 = {sound id, channel byte} and port 0
incremented as the handshake, so writing those three CPU->SPC port bytes ($F4-$F6) into
the snapshot makes the driver play exactly that effect from silence. Channel bytes are
the ones the game ORs into each request (Routine_Macros_DKC2.asm). ffmpeg/libgme renders,
trailing silence is trimmed. Output: assets/sfx/pirate/<name>.ogg (not versioned).
Menu effects (MENU_SFX, ids from menu_sound_capture.lua) need the menu's samples: their base
is assets-raw/pirate/music-test3/menu-sfxbase.spc (menu_sfxbase_capture.lua, driver silent).
"""
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "assets-raw/pirate/pirate-panic-sfxbase-1440.spc"
MENU_BASE = ROOT / "assets-raw/pirate/music-test3/menu-sfxbase.spc"
OUT = ROOT / "assets/sfx/pirate"
RAM = 0x100
SFX = {  # name: (SoundID, channel byte, seconds)
    "stomp": (0x02, 0x04, 1.0), "kill_neek": (0x04, 0x05, 1.0), "diddy_hurt": (0x06, 0x06, 1.5),
    "collect_banana": (0x08, 0x06, 1.0), "diddy_dead": (0x0A, 0x05, 3.0), "klobber_turn": (0x11, 0x07, 1.0),
    "klobber_emerge": (0x12, 0x04, 1.5), "break_wall": (0x19, 0x07, 2.0), "barrel_break": (0x1A, 0x05, 1.5),
    "dk_barrel": (0x1B, 0x05, 1.5), "timer_tick": (0x1C, 0x06, 0.5), "rambi_jump": (0x1D, 0x05, 1.0),
    "spawn_kremcoin": (0x21, 0x06, 1.5), "neek_squeek": (0x24, 0x05, 1.0), "collect_k": (0x27, 0x07, 1.5),
    "collect_o": (0x28, 0x06, 1.5), "collect_n": (0x29, 0x05, 1.5), "collect_g": (0x2A, 0x04, 1.5),
    "lost_life": (0x2B, 0x05, 2.0), "collect_banana_coin": (0x2D, 0x05, 1.5),
    "open_buddy_box": (0x39, 0x04, 1.5), "load_cannon": (0x4A, 0x05, 1.0),
    "rambi_stab": (0x53, 0x05, 1.0), "collect_dk_coin": (0x56, 0x05, 2.0),
    "collect_balloon": (0x2C, 0x07, 2.0), "read_note": (0x2E, 0x06, 2.0), "gain_life": (0x38, 0x05, 2.0),
}
MENU_SFX = {"move_menu": (0x33, 0x06, 1.0), "menu_select": (0x34, 0x06, 1.5)}


def render(name, sound_id, channel, seconds, tmp, base=BASE):
    data = bytearray(base.read_bytes())
    data[RAM + 0xF4] = (data[RAM + 0xF4] + 1) & 0xFF
    data[RAM + 0xF5], data[RAM + 0xF6] = sound_id, channel
    spc = Path(tmp) / (name + ".spc")
    spc.write_bytes(bytes(data))
    out = OUT / (name + ".ogg")
    subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-f", "libgme", "-i", str(spc),
                    "-t", str(seconds), "-af", "areverse,silenceremove=start_periods=1:start_threshold=-70dB,areverse",
                    "-c:a", "libvorbis", "-q:a", "6", str(out)], check=True)
    probe = subprocess.run(["ffmpeg", "-hide_banner", "-i", str(out), "-af", "volumedetect", "-f", "null", "-"],
                           capture_output=True, text=True).stderr
    peak = [line.split(":")[-1].strip() for line in probe.splitlines() if "max_volume" in line]
    return peak[0] if peak else "?"


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        for name, (sound_id, channel, seconds) in SFX.items():
            print(name, render(name, sound_id, channel, seconds, tmp))
        for name, (sound_id, channel, seconds) in MENU_SFX.items():
            print(name, render(name, sound_id, channel, seconds, tmp, MENU_BASE))
