-- Original screens after the title (menu_nav_capture.lua t2..t6, export_menu.py):
--   title -START-> Select Game (files 1-3, Copy Game, Erase Game, Mono/Stereo,
--   English/Francais; the cursor item is drawn bright) -START/B on a file-> mode
--   (ONE Player, TWO Player Team, TWO Player Contest) -START/B-> Crocodile Isle
--   "Gangplank Galleon" (waits) -START-> Pirate Panic card (waits) -START-> the level.
-- Fades measured on the captured brightness (out, black, in, in frames): title -> select
-- 60/55/40, select -> mode 40/50/50, mode -> island 40/90/15, island -> card 20/45/15,
-- card -> level 20 out (the level then loads).
-- Measured moves: 1 v 2 v 3 v Copy v Mono, Mono > English, English ^ Erase, Erase ^ 3,
-- 3 < stays, 3 ^ 2 ^ 1. B on Mono / English toggles Stereo / Francais (label only).
-- APPROXIMATIONS: the other moves are the mirror of the measured ones; Copy/Erase do
-- nothing (the files are always shown empty: the port keeps one save); the two-player
-- modes start the one-player game; Francais only changes its label; the island and card
-- loop their captured animation (t14: 560 / 600 frames, no period found: a seam per loop).
-- Mode screen (CODE_809A44.., t8-t13): on Contest or below, the 5th DOWN reveals the next
-- hidden mode (Music Test, then Cheat Mode); any other button resets the count; UP hides
-- it again. Music Test: LEFT steps back, B/Y/START/RIGHT/X/A forward through the 31
-- tracks (DATA_809C59, wrapping), the name drawn as OBJ in the area-name font at x 128,
-- y 200 (CODE_809DA2). Cheat Mode: DATA_809E35 (B A > > A < A X) sets $060B bit 0 = no
-- DK barrels, DATA_809E45 (Y A Start/Select A v < A v) bit 1 = 50 lives; a code entered
-- blanks the screen for a frame. APPROXIMATIONS: the list jumps to the new view (the
-- original scrolls 1/8 per frame); the code sound is not ported.
local M = { active = false }

local data
local MOVES = {
  game1 = { down = "game2" },
  game2 = { up = "game1", down = "game3" },
  game3 = { up = "game2", down = "copy" },
  copy = { up = "game3", down = "mono", right = "erase" },
  erase = { up = "game3", down = "english", left = "copy" },
  mono = { up = "copy", right = "english" },
  english = { up = "erase", left = "mono" },
}
local ITEMS = { "game1", "game2", "game3", "copy", "erase", "mono", "english" }
local MODES = { "one", "team", "contest", "music", "cheat" }
local MUSIC, CHEAT, REVEAL_PRESSES, TRACKS = 4, 5, 5, 31
local CODES = {
  no_dk_barrels = { "b", "a", "right", "right", "a", "left", "a", "x" },     -- DATA_809E35
  fifty_lives = { "y", "a", "start|select", "a", "down", "left", "a", "down" },  -- DATA_809E45
}
local BUTTONS = { "b", "y", "select", "start", "up", "down", "left", "right", "a", "x", "l", "r" }
M.cheats = {}
-- { out, black, in } frames from each screen to the next (see the header)
local FADES = { select = { 60, 55, 40 }, mode = { 40, 50, 50 }, island = { 40, 90, 15 },
                card = { 20, 45, 15 }, level = { 20, 0, 0 } }

function M.available()
  if data == nil then
    local ok, menu = pcall(function() return require("data.original.pirate.menu") end)
    data = ok and type(menu) == "table" and menu or false
  end
  return data ~= false
end

--- START on the title: the title fades out into Select Game.
function M.start(title_layers)
  M.active, M.screen, M.cursor, M.mode = true, "title", "game1", 1
  M.downs, M.track, M.code_index, M.flash = 0, 0, {}, 0
  M.stereo, M.francais, M.done = false, false, false
  M.title_layers = title_layers
  M.go("select")
end

function M.go(target)
  local fade = FADES[target]
  M.fade = { target = target, frame = 0, out = fade[1], black = fade[2], fade_in = fade[3] }
end

local function brightness()
  local fade = M.fade
  if not fade then return 1 end
  if fade.frame < fade.out then return 1 - fade.frame / fade.out end
  if fade.frame < fade.out + fade.black then return 0 end
  return math.min(1, (fade.frame - fade.out - fade.black) / math.max(1, fade.fade_in))
end

-- M.sound: the effect this frame asks for (menu-sound.csv: cursor $33, confirm $34 on
-- channel 6, CODE_809A09/CODE_809B42); the caller plays and clears it.

--- One frame. `edge(name)` reads a pressed button ("up", "down", "left", "right", "start", "b").
--- Returns "start_game" once the card is left.
function M.update(edge)
  if not M.active then return nil end
  local fade = M.fade
  if fade then
    fade.frame = fade.frame + 1
    if fade.frame == fade.out then
      if fade.target == "level" then M.active, M.fade = false, nil; return "start_game" end
      M.screen, M.clock = fade.target, 0
    end
    M.clock = (M.clock or 0) + 1
    if fade.frame >= fade.out + fade.black + fade.fade_in then M.fade = nil end
    return nil
  end
  M.clock = (M.clock or 0) + 1
  if M.flash > 0 then M.flash = M.flash - 1 end
  local confirm = edge("start") or edge("b")
  if M.screen == "select" then
    for _, direction in ipairs({ "up", "down", "left", "right" }) do
      if edge(direction) and MOVES[M.cursor][direction] then
        M.cursor, M.sound = MOVES[M.cursor][direction], "move_menu"
      end
    end
    if confirm then
      M.sound = "menu_select"
      if M.cursor:sub(1, 4) == "game" then M.go("mode")
      elseif M.cursor == "mono" then M.stereo = not M.stereo
      elseif M.cursor == "english" then M.francais = not M.francais end
    end
  elseif M.screen == "mode" then
    if M.update_mode(edge) then M.go("island"); M.sound = "menu_select" end
  elseif M.screen == "island" then
    if edge("start") then M.go("card") end
  elseif M.screen == "card" then
    if edge("start") then M.go("level") end
  end
  return nil
end

local function play(track)
  M.track = track
  if M.play_music then M.play_music(track > 0 and track or nil) end
end

--- One mode-screen frame; true when a game mode is confirmed.
function M.update_mode(edge)
  local pressed = {}
  for _, name in ipairs(BUTTONS) do pressed[name] = edge(name) end
  local any = false
  for _, value in pairs(pressed) do any = any or value end
  if any and not pressed.down then M.downs = 0 end
  if pressed.up and M.mode > 1 then
    if M.mode == MUSIC and M.track > 0 then play(0) end
    M.mode, M.sound = M.mode - 1, "move_menu"
  elseif pressed.down and M.mode < 3 then
    M.mode, M.sound = M.mode + 1, "move_menu"
  elseif pressed.down then
    M.downs = M.downs + 1
    if M.downs == REVEAL_PRESSES then
      M.downs = 0
      if M.mode < CHEAT then
        if M.mode == MUSIC and M.track > 0 then play(0) end
        M.mode, M.sound = M.mode + 1, "move_menu"
      end
    end
  end
  if M.mode == MUSIC then
    if pressed.left then play(M.track <= 1 and TRACKS or M.track - 1)
    elseif pressed.b or pressed.y or pressed.start or pressed.right or pressed.x or pressed.a then
      play(M.track >= TRACKS and 1 or M.track + 1)
    end
  elseif M.mode == CHEAT and any then
    for name, code in pairs(CODES) do
      local index = M.code_index[name] or 1
      local wanted = false
      for button in code[index]:gmatch("[^|]+") do wanted = wanted or pressed[button] end
      if wanted then
        index = index + 1
        if index > #code then M.cheats[name], M.flash, index = true, 1, 1 end
      else  -- a wrong button may be the first one of a new try
        local first = false
        for button in code[1]:gmatch("[^|]+") do first = first or pressed[button] end
        index = first and 2 or 1
      end
      M.code_index[name] = index
    end
  end
  return M.mode <= 3 and (pressed.start or pressed.b or pressed.y or pressed.x or pressed.a)
end

--- Layers to draw: { {sprite, x, y, w, h}, ... } (top-left boxes on 256x224), brightness.
function M.layers()
  if not M.active then return {}, 0 end  -- the frame the level is handed over: black
  local layers = {}
  local function add(sprite, box) layers[#layers + 1] = { sprite, box[1], box[2], box[3], box[4] } end
  local full = { 0, 0, 256, 224 }
  if M.screen == "title" then
    for _, layer in ipairs(M.title_layers or {}) do layers[#layers + 1] = layer end
  elseif M.screen == "select" then
    add("original_menu_select", full)
    for _, item in ipairs(ITEMS) do
      local on = item == M.cursor and "on" or "off"
      local box = data.items[item]
      if item == "mono" and M.stereo then  -- the toggled label's box covers the other's
        add("original_menu_stereo_" .. on, data.stereo)
      elseif item == "english" and M.francais then
        add("original_menu_francais_" .. on, data.francais)
      else
        add("original_menu_" .. item .. "_" .. on, box)
      end
    end
  elseif M.screen == "mode" then
    add("original_menu_mode_" .. MODES[M.mode], full)
    if M.mode == MUSIC and M.track > 0 then  -- the track name (CODE_809DA2)
      local x = 128
      for char in data.tracks[M.track]:gmatch(".") do
        if char ~= " " then add(string.format("original_menu_font_%02x", char:byte()), { x, 200, 8, 16 }) end
        x = x + 8
      end
    end
    if M.flash > 0 then return layers, 0 end  -- a code entered: one blank frame
  else
    add("original_menu_" .. M.screen, full)
    local anim = data[M.screen .. "_anim"]
    if anim then  -- island / card: each region's patch for this frame of the loop
      local t = (M.clock or 0) % anim.frames
      for _, region in ipairs(anim.regions) do
        local current
        for _, step in ipairs(region.seq) do
          if step[1] > t then break end
          current = step[2]
        end
        if current then add(current, region.box) end
      end
    end
  end
  return layers, brightness()
end

return M
