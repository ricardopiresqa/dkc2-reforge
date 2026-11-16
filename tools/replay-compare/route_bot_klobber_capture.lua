-- Route-bot walker capture (read-only game state): same inputs as route_bot_capture.lua
-- (reference inputs, then the fixed QA bot) and, per frame, the full 0x5E-byte sprite
-- struct of every live Klobber slot as hex, plus the player position. Klobber port evidence; QA evidence
-- for the walker port only; the bot is not gameplay logic. Never overwrites.
local self_path = debug.getinfo(1, "S").source:gsub("^@", "")
local root = assert(self_path:gsub("\\", "/"):match("^(.*)/tools/replay%-compare/[^/]+$"))
local reference = dofile(root .. "/data/original/pirate/reference_inputs.lua")
local output_path = root .. "/assets-raw/pirate/route-bot-klobber.csv"
local existing_output = io.open(output_path, "r")
if existing_output then
  existing_output:close()
  error("refusing to overwrite " .. output_path)
end
local LAST_FRAME = 3500
local BOT_START = 1033
local WALKERS = { [0x01AC] = true }  -- Klobber
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
    for address = 0x0DE2, 0x16B2 - 0x5E, 0x5E do
      if WALKERS[read_word(address)] then
        local bytes = {}
        for offset = 0, 0x5D do
          bytes[#bytes + 1] = string.format("%02X", emu.read(address + offset, emu.memType.snesWorkRam))
        end
        rows[#rows + 1] = string.format("%d,%d,%d,%d,%s", active, (address - 0x0DE2) / 0x5E,
          read_word(player + 6), read_word(player + 10), table.concat(bytes))
      end
    end
    if active >= LAST_FRAME then
      local output = assert(io.open(output_path, "w"))
      output:write("active_frame,slot,player_x,player_y,struct_hex\n")
      output:write(table.concat(rows, "\n"), "\n")
      output:close()
      emu.stop(0)
    end
  elseif frames >= 3000 then
    emu.log("ROUTE_BOT_WALKERS_GAMEPLAY_NOT_REACHED")
    emu.stop(22)
  end
end, emu.eventType.endFrame)
