-- Capture HUD RAM during the matched USA v1.0 replay (read-only game state).
-- Output is a new QA artifact under ignored assets-raw/pirate; never overwrites.
-- Run with MesenCE --testrunner. Fields: $096D banana target, $096B shown count,
-- $096F banana HUD timer, $0973 lives HUD timer, $0979 lives slide,
-- $08C0 lives, $0D2C banana tile base, $002A clock.
local self_path = debug.getinfo(1, "S").source:gsub("^@", "")
local root = assert(self_path:gsub("\\", "/"):match("^(.*)/tools/replay%-compare/[^/]+$"))
local reference = dofile(root .. "/data/original/pirate/reference_inputs.lua")
local output_path = root .. "/assets-raw/pirate/reference-hud-trace.csv"
local existing_output = io.open(output_path, "r")
if existing_output then
  existing_output:close()
  error("refusing to overwrite " .. output_path)
end
local LAST_FRAME = 400
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
    rows[#rows + 1] = string.format("%d,%d,%d,%d,%d,%d,%d,%d,%d", active,
      read_word(0x096D), read_word(0x096B), read_word(0x096F), read_word(0x0973),
      read_word(0x0979), read_word(0x08C0), read_word(0x0D2C), read_word(0x2A))
    if active >= LAST_FRAME then
      local output = assert(io.open(output_path, "w"))
      output:write("active_frame,banana_target,banana_shown,banana_timer,lives_timer,lives_slide,lives,banana_tile,clock\n")
      output:write(table.concat(rows, "\n"), "\n")
      output:close()
      emu.stop(0)
    end
  elseif frames >= 3000 then
    emu.log("HUD_TRACE_GAMEPLAY_NOT_REACHED")
    emu.stop(22)
  end
end, emu.eventType.endFrame)
