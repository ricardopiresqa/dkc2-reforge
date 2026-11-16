-- Animal route probe (read-only game state): route-bot inputs (route_bot_capture.lua)
-- with the OVERRIDES windows replaced, to reach Rambi (crate at x 4476 breaks on the
-- route-bot frame 3392), the bonus-2 wall and Rattly. Per frame from FIRST: the player
-- ($593: x, y, anim, state, vx, vy) and the Kong/animal slots (sprites 228, 232, 412
-- Rambi, 404 Rattly) -> assets-raw/pirate/animal-route-<TAG>.csv. Never overwrites.
local TAG = "t14"
local FIRST, LAST_FRAME = 4690, 5600
-- { first active frame, last active frame, pad mask } (B 1, Y 2, UP 16, LEFT 64, RIGHT 128)
local OVERRIDES = {
  { 3393, 3419, 64 },  -- t1: lands on Rambi at 3420
  { 3560, 3700, 130 },  -- t2: Rambi was hurt at 3582 while jumping: run without jumping
  -- t12: to the level end on Rambi (route-bot pattern from 3701: RIGHT+Y, B 12/48)
}
-- t13: t12 stalled at x 6800 holding an object (Y held picks barrels up).
-- t14: the stern step (designed on the port, qa-42: back up, run right, jump at x ~6437 port).
for _, window in ipairs({ { 4700, 4709, 0 }, { 4710, 4739, 64 }, { 4740, 4751, 65 }, { 4752, 4769, 64 },
                          { 4770, 4795, 130 }, { 4796, 4809, 131 }, { 4810, 4849, 130 } }) do
  OVERRIDES[#OVERRIDES + 1] = window
end
for first = 4850, LAST_FRAME, 48 do  -- then on to the goal: RIGHT+Y, B 12/48
  OVERRIDES[#OVERRIDES + 1] = { first, first + 11, 131 }
  OVERRIDES[#OVERRIDES + 1] = { first + 12, first + 47, 130 }
end

local self_path = debug.getinfo(1, "S").source:gsub("^@", "")
local root = assert(self_path:gsub("\\", "/"):match("^(.*)/tools/replay%-compare/[^/]+$"))
local reference = dofile(root .. "/data/original/pirate/reference_inputs.lua")
local output_path = root .. "/assets-raw/pirate/animal-route-" .. TAG .. ".csv"
local existing_output = io.open(output_path, "r")
if existing_output then
  existing_output:close()
  error("refusing to overwrite " .. output_path)
end
local BOT_START = 1033
local frames, gameplay_start, rows = 0, nil, {}

local function read_word(address)
  return emu.readWord(address, emu.memType.snesWorkRam)
end

local buttons = { "b", "y", "select", "start", "up", "down", "left", "right", "a", "x", "l", "r" }
local function set_controller(mask)
  local state = {}
  for index, name in ipairs(buttons) do
    state[name] = math.floor(mask / (2 ^ (index - 1))) % 2 == 1
  end
  local ok = pcall(emu.setInput, state, 0)
  if not ok then emu.setInput(0, state) end
end

emu.addEventCallback(function()
  local mask
  if gameplay_start then
    local active = frames - gameplay_start
    local override
    for _, window in ipairs(OVERRIDES) do
      if active >= window[1] and active <= window[2] then override = window[3] end
    end
    if override then
      mask = override
    elseif active < BOT_START then
      mask = reference.inputs[active + 1] or 128
    else
      local tick = (active - BOT_START) % 48
      mask = 128 + 2 + (tick < 12 and 1 or 0)  -- RIGHT + Y (run), B pressed 12/48 frames
    end
  else
    local menu_step = frames % 120
    mask = (frames > 600 and frames < 3000 and menu_step < 8) and 8 or 0
  end
  set_controller(mask)
end, emu.eventType.inputPolled)

emu.addEventCallback(function()
  frames = frames + 1
  local mode, level = read_word(0x24), read_word(0xD3)
  if not gameplay_start and level == 3 and mode == 0x8819 then
    gameplay_start = frames
  end
  if gameplay_start then
    local active = frames - gameplay_start
    if active >= FIRST then
      local player = read_word(0x593)
      rows[#rows + 1] = string.format("P,%d,%d,%d,%d,%d,%d,%d,%d,%d", active, read_word(player),
        read_word(player + 6), read_word(player + 10), read_word(player + 0x36), read_word(player + 0x2E),
        read_word(player + 0x20), read_word(player + 0x24), level)
      for _, holder in ipairs({ 0x097B, 0x097D }) do
        local hud = read_word(holder)
        if hud ~= 0 then
          rows[#rows + 1] = string.format("H,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d", active, holder, read_word(hud),
            read_word(hud + 6), read_word(hud + 10), read_word(hud + 0x2E), read_word(hud + 0x44),
            read_word(hud + 0x46), read_word(hud + 0x12), read_word(hud + 0x1A))
        end
      end
      for address = 0x0DE2, 0x16B2 - 0x5E, 0x5E do
        local id = read_word(address)
        local near = math.abs(read_word(address + 6) - read_word(player + 6)) < 160
        if id == 228 or id == 232 or id == 412 or id == 404 or (near and id ~= 0) then
          rows[#rows + 1] = string.format("S,%d,%d,%d,%d,%d,%d,%d,%d", active, id, read_word(address + 6),
            read_word(address + 10), read_word(address + 0x36), read_word(address + 0x2E),
            read_word(address + 0x20), read_word(address + 0x24))
        end
      end
    end
    if active >= LAST_FRAME then
      local output = assert(io.open(output_path, "w"))
      output:write("kind,active_frame,a,b,c,d,e,f,g,h\n")
      output:write(table.concat(rows, "\n"), "\n")
      output:close()
      emu.stop(0)
    end
  elseif frames >= 3000 then
    emu.log("ROUTE_BOT_GAMEPLAY_NOT_REACHED")
    emu.stop(22)
  end
end, emu.eventType.endFrame)
