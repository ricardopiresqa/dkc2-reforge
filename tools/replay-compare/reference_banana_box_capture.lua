-- Capture the player banana-collision box $09B3-$09BA (B5F739) during the replay.
-- Output is a new QA artifact under ignored assets-raw/pirate; never overwrites.
-- Run with MesenCE --testrunner. Fields: box words $09B3/$09B5/$09B7/$09B9
-- (left, top, right, bottom as read by B5F756), player x/y, banana HUD timer.
local self_path = debug.getinfo(1, "S").source:gsub("^@", "")
local root = assert(self_path:gsub("\\", "/"):match("^(.*)/tools/replay%-compare/[^/]+$"))
local reference = dofile(root .. "/data/original/pirate/reference_inputs.lua")
local output_path = root .. "/assets-raw/pirate/reference-banana-box.csv"
local existing_output = io.open(output_path, "r")
if existing_output then
  existing_output:close()
  error("refusing to overwrite " .. output_path)
end
local LAST_FRAME = 240
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
    mask = reference.inputs[frames - gameplay_start + 1] or 128
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
  if gameplay_start and mode == 0x8819 then
    local active = frames - gameplay_start
    local player = read_word(0x593)
    rows[#rows + 1] = string.format("%d,%d,%d,%d,%d,%d,%d,%d", active,
      read_word(0x09B3), read_word(0x09B5), read_word(0x09B7), read_word(0x09B9),
      read_word(player + 6), read_word(player + 10), read_word(0x096F))
    if active >= LAST_FRAME then
      local output = assert(io.open(output_path, "w"))
      output:write("active_frame,box_left,box_top,box_right,box_bottom,player_x,player_y,banana_timer\n")
      output:write(table.concat(rows, "\n"), "\n")
      output:close()
      emu.stop(0)
    end
  elseif frames >= 3000 then
    emu.log("HUD_TRACE_GAMEPLAY_NOT_REACHED")
    emu.stop(22)
  end
end, emu.eventType.endFrame)
