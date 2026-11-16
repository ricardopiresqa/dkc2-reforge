-- Team-throw probe (read-only game state): route-bot inputs (route_bot_capture.lua) until
-- Dixie has left the DK barrel and both Kongs stand at x 1207 (active 2075), then idle,
-- A on TEAM_UP (pick the partner up), Y (+ THROW_UP: UP held) on THROW, idle afterwards.
-- Per frame: both Kong slots (0, 1) with x, y, pose, animation, $12, state, vx ($20),
-- vy ($24) -> assets-raw/pirate/team-throw-probe.csv. QA evidence; never overwrites.
local THROW_UP = true  -- false: the forward throw (team-throw-probe.csv)
local self_path = debug.getinfo(1, "S").source:gsub("^@", "")
local root = assert(self_path:gsub("\\", "/"):match("^(.*)/tools/replay%-compare/[^/]+$"))
local reference = dofile(root .. "/data/original/pirate/reference_inputs.lua")
local output_path = root .. "/assets-raw/pirate/team-throw-" .. (THROW_UP and "up" or "probe") .. ".csv"
local existing_output = io.open(output_path, "r")
if existing_output then
  existing_output:close()
  error("refusing to overwrite " .. output_path)
end
local LAST_FRAME = 2260
local IDLE, TEAM_UP, THROW = 2076, 2090, 2140

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
    if active >= IDLE then
      mask = (active == TEAM_UP and 256) or (active == THROW and (THROW_UP and 18 or 2))
        or (THROW_UP and active > TEAM_UP and active < THROW + 4 and 16) or 0
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
    if active >= 2070 then
      for slot = 0, 1 do
        local address = 0x0DE2 + slot * 0x5E
        rows[#rows + 1] = string.format("%d,%d,%d,%d,%d,%d,%d,%d,%d,%d", active, slot, read_word(address + 6),
          read_word(address + 10), read_word(address + 0x1A), read_word(address + 0x36),
          read_word(address + 0x12), read_word(address + 0x2E), read_word(address + 0x20),
          read_word(address + 0x24))
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
