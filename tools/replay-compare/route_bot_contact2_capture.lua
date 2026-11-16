-- Route-bot contact capture (read-only): same inputs as route_bot_capture.lua; execution
-- callbacks log the walker contact pass. At BCFE00 (end of the BCFD61 overlap test) the
-- player/enemy boxes $09A3-$09EA and the side flags $09F5; at BEBEE2 the BEBF18 dispatch
-- index (X); v2 adds $5E/$09F7 at BEC01F/BEC07A and the action (A) at BEC4EF/BEC47A. Rows only while the current sprite ($64) is a Neek/Klomp. Never overwrites.
local self_path = debug.getinfo(1, "S").source:gsub("^@", "")
local root = assert(self_path:gsub("\\", "/"):match("^(.*)/tools/replay%-compare/[^/]+$"))
local reference = dofile(root .. "/data/original/pirate/reference_inputs.lua")
local output_path = root .. "/assets-raw/pirate/route-bot-contact2.csv"
local existing_output = io.open(output_path, "r")
if existing_output then
  existing_output:close()
  error("refusing to overwrite " .. output_path)
end
local LAST_FRAME, BOT_START = 3200, 1033
local WALKERS = { [0x01E4] = true, [0x01EC] = true }
local frames, gameplay_start, rows = 0, nil, {}

local function read_word(address)
  return emu.readWord(address, emu.memType.snesWorkRam)
end

local function current_walker()
  local sprite = read_word(0x64)
  if sprite >= 0x0DE2 and sprite < 0x16B2 and WALKERS[read_word(sprite)] then return sprite end
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
      mask = 128 + 2 + (tick < 12 and 1 or 0)
    end
  else
    local menu_step = frames % 120
    mask = (frames > 600 and frames < 3000 and menu_step < 8) and 8 or 0
  end
  set_controller(mask)
end, emu.eventType.inputPolled)

emu.addMemoryCallback(function()
  local sprite = gameplay_start and current_walker()
  if not sprite then return end
  local boxes = {}
  for address = 0x09A3, 0x09F1, 2 do boxes[#boxes + 1] = string.format("%04X", read_word(address)) end
  local player = read_word(0x593)
  rows[#rows + 1] = string.format("O,%d,%d,%d,%d,%d,%d,%s", frames - gameplay_start,
    (sprite - 0x0DE2) / 0x5E, read_word(0x09F5), read_word(player + 0x41) % 256,
    read_word(player + 0x2E), read_word(player + 0x24), table.concat(boxes, " "))
end, emu.callbackType.exec, 0xBCFE00)

emu.addMemoryCallback(function()
  local sprite = gameplay_start and current_walker()
  if not sprite then return end
  local state = emu.getState()
  rows[#rows + 1] = string.format("D,%d,%d,%d,%d,,,", frames - gameplay_start,
    (sprite - 0x0DE2) / 0x5E, read_word(0x09F5), state["cpu.x"] or -1)
end, emu.callbackType.exec, 0xBEBEE2)

emu.addEventCallback(function()
  frames = frames + 1
  local mode, level = read_word(0x24), read_word(0xD3)
  if not gameplay_start and level == 3 and mode == 0x8819 then gameplay_start = frames end
  if gameplay_start and frames - gameplay_start >= LAST_FRAME then
    local output = assert(io.open(output_path, "w"))
    output:write("kind,active_frame,slot,flags,player_41,player_state,player_vy,boxes\n")
    output:write(table.concat(rows, "\n"), "\n")
    output:close()
    emu.stop(0)
  elseif not gameplay_start and frames >= 3000 then
    emu.log("ROUTE_BOT_CONTACT_GAMEPLAY_NOT_REACHED")
    emu.stop(22)
  end
end, emu.eventType.endFrame)

for _, hook in ipairs({ { "H0", 0xBEC01F }, { "H2", 0xBEC07A }, { "A", 0xBEC4EF }, { "HURT", 0xBEC47A } }) do
  emu.addMemoryCallback(function()
    local sprite = gameplay_start and current_walker()
    if not sprite then return end
    local state = emu.getState()
    rows[#rows + 1] = string.format("%s,%d,%d,%d,%d,%d,,", hook[1], frames - gameplay_start,
      (sprite - 0x0DE2) / 0x5E, read_word(0x5E), read_word(0x09F7), state["cpu.a"] or -1)
  end, emu.callbackType.exec, hook[2])
end
