-- Route-bot capture (read-only game state): the matched USA v1.0 reference inputs, then
-- a fixed QA bot (hold RIGHT+Y, press B 12 of every 48 frames) to reach enemies and
-- items beyond the reference route. Per frame: mode, player, lives, and every live
-- sprite slot. QA evidence only; the bot is not gameplay logic. Never overwrites.
local self_path = debug.getinfo(1, "S").source:gsub("^@", "")
local root = assert(self_path:gsub("\\", "/"):match("^(.*)/tools/replay%-compare/[^/]+$"))
local reference = dofile(root .. "/data/original/pirate/reference_inputs.lua")
local output_path = root .. "/assets-raw/pirate/route-bot-trace.csv"
local existing_output = io.open(output_path, "r")
if existing_output then
  existing_output:close()
  error("refusing to overwrite " .. output_path)
end
local LAST_FRAME = 6000
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
    if active < BOT_START then
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
    local player = read_word(0x593)
    rows[#rows + 1] = string.format("P,%d,%d,%d,%d,%d,%d,%d,%d,%d", active, mode, level,
      read_word(player + 6), read_word(player + 10), read_word(player + 0x2E),
      read_word(player + 0x36), read_word(0x08C0), read_word(0x17BA))
    for address = 0x0DE2, 0x16B2 - 0x5E, 0x5E do
      local id = read_word(address)
      if id ~= 0 then
        rows[#rows + 1] = string.format("S,%d,%d,%d,%d,%d,%d,%d,%d,%d", active,
          (address - 0x0DE2) / 0x5E, id, read_word(address + 6), read_word(address + 10),
          read_word(address + 0x1A), read_word(address + 0x36), read_word(address + 0x12),
          read_word(address + 0x2E))
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
