-- Cartwheel probe (read-only game state): matched reference inputs until frame 479 (Diddy
-- walking right on the deck), then RIGHT+Y on frame 480 only and RIGHT afterwards.
-- Records player x/y (with subpixel), vx, vy, state, animation and $1E per frame
-- 470-600 -> assets-raw/pirate/cartwheel-probe.csv. QA evidence; never overwrites.
local self_path = debug.getinfo(1, "S").source:gsub("^@", "")
local root = assert(self_path:gsub("\\", "/"):match("^(.*)/tools/replay%-compare/[^/]+$"))
local reference = dofile(root .. "/data/original/pirate/reference_inputs.lua")
local output_path = root .. "/assets-raw/pirate/cartwheel-probe.csv"
local existing_output = io.open(output_path, "r")
if existing_output then
  existing_output:close()
  error("refusing to overwrite " .. output_path)
end
local TAP, LAST = 480, 600
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
    if active < TAP then mask = reference.inputs[active + 1] or 128
    elseif active == TAP then mask = 128 + 2
    else mask = 128 end
  else
    local menu_step = frames % 120
    mask = (frames > 600 and frames < 3000 and menu_step < 8) and 8 or 0
  end
  set_controller(mask)
end, emu.eventType.inputPolled)

emu.addEventCallback(function()
  frames = frames + 1
  local mode, level = read_word(0x24), read_word(0xD3)
  if not gameplay_start and level == 3 and mode == 0x8819 then gameplay_start = frames end
  if gameplay_start then
    local active = frames - gameplay_start
    if active >= 470 then
      local p = read_word(0x593)
      rows[#rows + 1] = string.format("%d,%d,%d,%d,%d,%d,%d,%d,%d,%d", active, read_word(p + 6),
        emu.read(p + 5, emu.memType.snesWorkRam), read_word(p + 10), read_word(p + 0x20), read_word(p + 0x24),
        read_word(p + 0x2E), read_word(p + 0x36), read_word(p + 0x1E), read_word(p + 0x1A))
    end
    if active >= LAST then
      local output = assert(io.open(output_path, "w"))
      output:write("frame,x,x_frac,y,vx,vy,state,anim,flags1e,pose\n", table.concat(rows, "\n"), "\n")
      output:close()
      emu.stop(0)
    end
  elseif frames >= 3000 then
    emu.stop(22)
  end
end, emu.eventType.endFrame)
