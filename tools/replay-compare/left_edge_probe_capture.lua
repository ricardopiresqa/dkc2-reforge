-- Level start left edge probe (read-only): from the first gameplay frame of Pirate Panic
-- hold LEFT (B every 60 frames: jumps too) for 300 frames. Per frame: player x/y raw,
-- vx, state ($2E) and camera x ($17BA) -> assets-raw/pirate/left-edge-t1.csv.
-- Never overwrites.
local self_path = debug.getinfo(1, "S").source:gsub("^@", "")
local root = assert(self_path:gsub("\\", "/"):match("^(.*)/tools/replay%-compare/[^/]+$"))
local output_path = root .. "/assets-raw/pirate/left-edge-t1.csv"
local existing = io.open(output_path, "r")
if existing then
  existing:close()
  error("refusing to overwrite " .. output_path)
end
local frames, gameplay_start, rows = 0, nil, {}

local function read_word(address)
  return emu.readWord(address, emu.memType.snesWorkRam)
end

local buttons = { "b", "y", "select", "start", "up", "down", "left", "right", "a", "x", "l", "r" }
emu.addEventCallback(function()
  local state = {}
  for _, name in ipairs(buttons) do state[name] = false end
  if gameplay_start then
    local active = frames - gameplay_start
    state.left = true
    state.b = active > 120 and active % 60 < 10
  else
    state.start = frames > 600 and frames < 3000 and frames % 120 < 8
  end
  local ok = pcall(emu.setInput, state, 0)
  if not ok then emu.setInput(0, state) end
end, emu.eventType.inputPolled)

emu.addEventCallback(function()
  frames = frames + 1
  if not gameplay_start and read_word(0xD3) == 3 and read_word(0x24) == 0x8819 then
    gameplay_start = frames
  end
  if gameplay_start then
    local active = frames - gameplay_start
    local player = read_word(0x593)
    rows[#rows + 1] = string.format("%d,%d,%d,%d,%d,%d", active, read_word(player + 6),
      read_word(player + 10), read_word(player + 0x20), read_word(player + 0x2E), read_word(0x17BA))
    if active >= 300 then
      local output = assert(io.open(output_path, "w"))
      output:write("active_frame,x_raw,y_raw,vx,state,camera_x\n", table.concat(rows, "\n"), "\n")
      output:close()
      emu.stop(0)
    end
  elseif frames >= 3000 then
    emu.stop(22)
  end
end, emu.eventType.endFrame)
