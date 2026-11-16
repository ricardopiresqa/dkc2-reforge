-- Music Test order probe (read-only): the music_test_spc_capture.lua inputs (title ->
-- game 1 -> 7 DOWN -> START steps from 1600), one step every 40 frames, and the music
-- id the game asked for ($1C) 30 frames after each step: checks that the snapshot
-- track-NN.spc really is music id NN. -> assets-raw/pirate/music-test2/order.csv.
-- Never overwrites.
local self_path = debug.getinfo(1, "S").source:gsub("^@", "")
local root = assert(self_path:gsub("\\", "/"):match("^(.*)/tools/replay%-compare/[^/]+$"))
local output_path = root .. "/assets-raw/pirate/music-test2/order.csv"
local existing = io.open(output_path, "r")
if existing then
  existing:close()
  error("refusing to overwrite " .. output_path)
end
local STEP0, SKIP, frames, rows = 1600, 40, 0, {}

local function pressed_at(f)
  if f >= 960 and f < 966 then return "start" end
  if f >= 1160 and f < 1166 then return "start" end
  for index = 0, 6 do
    local at = 1340 + index * 30
    if f >= at and f < at + 4 then return "down" end
  end
  for track = 1, 31 do
    local at = STEP0 + (track - 1) * SKIP
    if f >= at and f < at + 4 then return "start" end
  end
  return nil
end

local buttons = { "b", "y", "select", "start", "up", "down", "left", "right", "a", "x", "l", "r" }
emu.addEventCallback(function()
  local name = pressed_at(frames)
  local state = {}
  for _, button in ipairs(buttons) do state[button] = button == name end
  local ok = pcall(emu.setInput, state, 0)
  if not ok then emu.setInput(0, state) end
end, emu.eventType.inputPolled)

emu.addEventCallback(function()
  frames = frames + 1
  local step = (frames - STEP0 - 30) / SKIP
  if step >= 0 and step < 31 and step == math.floor(step) then
    rows[#rows + 1] = string.format("%d,%d", step + 1, emu.readWord(0x1C, emu.memType.snesWorkRam))
  end
  if frames >= STEP0 + 31 * SKIP + 40 then
    local output = assert(io.open(output_path, "w"))
    output:write("track,music\n", table.concat(rows, "\n"), "\n")
    output:close()
    emu.stop(0)
  end
end, emu.eventType.endFrame)
