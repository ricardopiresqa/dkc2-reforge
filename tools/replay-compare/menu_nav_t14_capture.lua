-- Game-select navigation probe (read-only game state): START at the title (frame 720),
-- then on the Select Game screen (from ~1000) one d-pad press every 60 frames (NAV); a
-- screen picture every 5 frames from 1000 and a row per frame with the pad mask ->
-- assets-raw/pirate/menu-nav/frame-NNNN.ppm, menu-nav.csv.
-- Never overwrites.
-- (generated from menu_nav_capture.lua for t14)
local self_path = debug.getinfo(1, "S").source:gsub("^@", "")
local root = assert(self_path:gsub("\\", "/"):match("^(.*)/tools/replay%-compare/[^/]+$"))
local output_path = root .. "/assets-raw/pirate/menu-nav/menu-nav-t14.csv"
local existing = io.open(output_path, "r")
if existing then
  existing:close()
  error("refusing to overwrite " .. output_path)
end
local frames, rows = 0, {}
-- { frame, button }: DOWN x4, RIGHT, UP x2, LEFT, UP x2 (back to game 1)
-- (t1: START on 720 was ignored, the title takes it later: menu-flow START on 960 worked)
-- t3: game 1 (START 1160), then the mode screen: DOWN, DOWN, UP, then B (back?)
-- t4: game 1 (START 1160), ONE Player (START 1400), then no input: does the intro
-- (Gangplank Galleon -> Pirate Panic card) run by itself?
-- t14: island and card animations: game 1, ONE Player, the island waits from ~1545
-- (every frame 1560-2159 pictured), START at 2160, the card from ~2245 (2260-2859).
local NAV = { { 1160, "start" }, { 1400, "start" }, { 2160, "start" } }
local pressed = nil

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
  local state = {}
  for _, name in ipairs(buttons) do state[name] = false end
  state.start = frames >= 960 and frames < 968
  pressed = nil
  for _, step in ipairs(NAV) do
    if frames >= step[1] and frames < step[1] + 4 then state[step[2]], pressed = true, step[2] end
  end
  local ok = pcall(emu.setInput, state, 0)
  if not ok then emu.setInput(0, state) end
end, emu.eventType.inputPolled)

emu.addEventCallback(function()
  frames = frames + 1
  local mode, level = read_word(0x24), read_word(0xD3)
  if (frames >= 1560 and frames < 2160) or (frames >= 2260 and frames < 2860) then
    write_picture(root .. string.format("/assets-raw/pirate/menu-nav/t14-frame-%04d.ppm", frames))
  end
  rows[#rows + 1] = string.format("%d,%d,%d,%s", frames, mode, level, pressed or "")
  if frames >= 2860 then
    local output = assert(io.open(output_path, "w"))
    output:write("frame,mode,level\n", table.concat(rows, "\n"), "\n")
    output:close()
    emu.stop(0)
  end
end, emu.eventType.endFrame)
