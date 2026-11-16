-- Menu flow probe (read-only game state): the probes' boot inputs (START 8 of every 120
-- frames from 600) through title -> game select -> mode -> level; a screen picture every
-- 10 frames from 600 until gameplay (level 3, mode $8819) and a row per picture with the
-- game mode ($24) and level ($D3) -> assets-raw/pirate/menu/frame-NNNN.ppm, menu-flow.csv.
-- Never overwrites.
local self_path = debug.getinfo(1, "S").source:gsub("^@", "")
local root = assert(self_path:gsub("\\", "/"):match("^(.*)/tools/replay%-compare/[^/]+$"))
local output_path = root .. "/assets-raw/pirate/menu/menu-flow.csv"
local existing = io.open(output_path, "r")
if existing then
  existing:close()
  error("refusing to overwrite " .. output_path)
end
local frames, rows = 0, {}

local function read_word(address)
  return emu.readWord(address, emu.memType.snesWorkRam)
end

local function write_picture(filename)
  local size, pixels = emu.getScreenSize(), emu.getScreenBuffer()
  local image = assert(io.open(filename, "wb"))
  image:write(string.format("P6\n%d %d\n255\n", size.width, size.height))
  local chunks = {}
  for _, pixel in ipairs(pixels) do
    chunks[#chunks + 1] = string.char(math.floor(pixel / 65536) % 256, math.floor(pixel / 256) % 256, pixel % 256)
    if #chunks == 1024 then image:write(table.concat(chunks)); chunks = {} end
  end
  image:write(table.concat(chunks))
  image:close()
end

local buttons = { "b", "y", "select", "start", "up", "down", "left", "right", "a", "x", "l", "r" }
emu.addEventCallback(function()
  local menu_step = frames % 120
  local start = frames > 600 and frames < 3000 and menu_step < 8
  local state = {}
  for _, name in ipairs(buttons) do state[name] = (name == "start" and start) or false end
  local ok = pcall(emu.setInput, state, 0)
  if not ok then emu.setInput(0, state) end
end, emu.eventType.inputPolled)

emu.addEventCallback(function()
  frames = frames + 1
  local mode, level = read_word(0x24), read_word(0xD3)
  if frames >= 600 and frames % 10 == 0 then
    write_picture(root .. string.format("/assets-raw/pirate/menu/frame-%04d.ppm", frames))
    rows[#rows + 1] = string.format("%d,%d,%d", frames, mode, level)
  end
  if (level == 3 and mode == 0x8819) or frames >= 3200 then
    local output = assert(io.open(output_path, "w"))
    output:write("frame,mode,level\n", table.concat(rows, "\n"), "\n")
    output:close()
    emu.stop(0)
  end
end, emu.eventType.endFrame)
