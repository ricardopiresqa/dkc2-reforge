local M = {}

local sounds = {}
local music_resource = nil
local music_playing = false
local music_duration = 2.0
local music_timer = 0
local original_semantics = false

-- Pirate Panic music: the level's SPC700 state rendered locally from the ROM
-- (tools/replay-compare/music_spc_capture.lua + ffmpeg libgme -> assets/music/pirate,
-- not versioned). APPROXIMATION: 5 minutes with a fade, looped as a whole; the
-- song's own loop point is not found yet.
local ORIGINAL_MUSIC = "main:/go#music_pirate"
-- The goal hit switches the level song to its victory part (render_music_test.py --victory;
-- APPROXIMATION: rendered as a 180 s one-shot, its loop point not found).
local VICTORY_MUSIC = "main:/go#music_victory"

function M.play_original_music()
  pcall(sound.stop, VICTORY_MUSIC)
  pcall(sound.stop, ORIGINAL_MUSIC)
  pcall(sound.play, ORIGINAL_MUSIC)
end

function M.stop_original_music()
  pcall(sound.stop, VICTORY_MUSIC)
  pcall(sound.stop, ORIGINAL_MUSIC)
end

function M.play_victory()
  pcall(sound.stop, ORIGINAL_MUSIC)
  pcall(sound.stop, VICTORY_MUSIC)
  pcall(sound.play, VICTORY_MUSIC)
end

-- Music Test tracks (DATA_809C59 ids 1-31, rendered by render_music_test.py into
-- main.collection's music_test_NN components). nil stops the playing one.
local playing_track
function M.play_track(track)
  if playing_track == track then return end
  if playing_track then pcall(sound.stop, string.format("main:/go#music_test_%02d", playing_track)) end
  playing_track = track
  if track then pcall(sound.play, string.format("main:/go#music_test_%02d", track)) end
end

function M.set_original_semantics(enabled)
  original_semantics = enabled == true
  if original_semantics then
    M.stop_music()
    M.play_original_music()
  else
    M.stop_original_music()
  end
end

local function safe_load(path)
  local ok, res = pcall(resource.load, path)
  if ok then return res end
  return nil
end

function M.init()
  sounds.jump = safe_load("/assets/sfx/jump.wav")
  sounds.stomp = safe_load("/assets/sfx/stomp.wav")
  sounds.collect = safe_load("/assets/sfx/collect.wav")
  sounds.damage = safe_load("/assets/sfx/damage.wav")
  sounds.barrel_shoot = safe_load("/assets/sfx/barrel_shoot.wav")
  sounds.start = safe_load("/assets/sfx/start.wav")
  music_resource = safe_load("/assets/music/jungle_hijinks.wav")
end

-- Original sound effects rendered from the ROM's SPC700 driver (tools/replay-compare/
-- render_sfx.py -> assets/sfx/pirate, one sound component `sfx_<name>` each). Generic
-- port names map to the effect the original plays for that event.
local ORIGINAL_SFX = {
  stomp = "stomp", collect = "collect_banana", damage = "diddy_hurt", barrel_shoot = "load_cannon",
}
local ORIGINAL_NAMES = {
  barrel_break = true, break_wall = true, collect_banana = true, collect_banana_coin = true,
  collect_dk_coin = true, collect_g = true, collect_k = true, collect_n = true, collect_o = true,
  diddy_dead = true, diddy_hurt = true, dk_barrel = true, kill_neek = true, klobber_emerge = true,
  klobber_turn = true, load_cannon = true, lost_life = true, neek_squeek = true, open_buddy_box = true,
  rambi_jump = true, rambi_stab = true, spawn_kremcoin = true, stomp = true, timer_tick = true,
  collect_balloon = true, read_note = true, gain_life = true,
}
-- menu effects play before any level sets original_semantics
local MENU_SFX = { move_menu = true, menu_select = true }

function M.play(name)
  -- Do not label unrelated prototype WAV files as SNES sounds.
  if MENU_SFX[name] then pcall(sound.play, "main:/go#sfx_" .. name) return end
  if original_semantics then
    local id = ORIGINAL_SFX[name] or (ORIGINAL_NAMES[name] and name)
    if id then pcall(sound.play, "main:/go#sfx_" .. id) end
    return
  end
  if sounds[name] then
    sound.play(sounds[name])
  end
end

function M.play_music()
  if original_semantics then return end
  if music_resource then
    sound.play(music_resource)
    music_playing = true
    music_timer = 0
  end
end

function M.stop_music()
  music_playing = false
  music_timer = 0
end

function M.update(dt)
  if music_playing then
    music_timer = music_timer + dt
    if music_timer >= music_duration then
      sound.play(music_resource)
      music_timer = 0
    end
  end
end

return M
