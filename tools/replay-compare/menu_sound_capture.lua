-- Menu sound probe (read-only): every request the game sends to the APU (B581FB writes
-- the 16-bit word to $2141/$2142: low = sound or command id, high = channel) and the
-- current music ($1C) per frame, from boot through the title, Select Game (cursor
-- moves, game 1), the mode screen (cursor moves, One Player) and the level intro.
-- -> assets-raw/pirate/menu-nav/menu-sound.csv (frame,music,mode,port1,port2,pressed).
-- Never overwrites.
local self_path = debug.getinfo(1, "S").source:gsub("^@", "")
local root = assert(self_path:gsub("\\", "/"):match("^(.*)/tools/replay%-compare/[^/]+$"))
local output_path = root .. "/assets-raw/pirate/menu-nav/menu-sound.csv"
local existing = io.open(output_path, "r")
if existing then
  existing:close()
  error("refusing to overwrite " .. output_path)
end
local frames, rows, pressed = 0, {}, nil
local requests = {}
local NAV = {
  { 960, "start" },                                  -- title
  { 1100, "down" }, { 1130, "up" }, { 1160, "start" },  -- Select Game: cursor, game 1
  { 1340, "down" }, { 1370, "up" }, { 1400, "start" },  -- mode screen: cursor, One Player
}

local function read_word(address)
  return emu.readWord(address, emu.memType.snesWorkRam)
end

-- B581FB starts with TXA: X is the request word (a $2141 write hook only saw the boot upload)
emu.addMemoryCallback(function()
  local x = emu.getState()["cpu.x"]
  requests[#requests + 1] = string.format("%d,%d,%d,%d,%d,%s", frames, read_word(0x1C),
    read_word(0x24), x % 256, math.floor(x / 256) % 256, pressed or "")
end, emu.callbackType.exec, 0xB581FB, 0xB581FB, emu.cpuType.snes)

local buttons = { "b", "y", "select", "start", "up", "down", "left", "right", "a", "x", "l", "r" }
emu.addEventCallback(function()
  local state = {}
  for _, name in ipairs(buttons) do state[name] = false end
  pressed = nil
  for _, step in ipairs(NAV) do
    if frames >= step[1] and frames < step[1] + 4 then state[step[2]], pressed = true, step[2] end
  end
  local ok = pcall(emu.setInput, state, 0)
  if not ok then emu.setInput(0, state) end
end, emu.eventType.inputPolled)

local last_music
emu.addEventCallback(function()
  frames = frames + 1
  local music = read_word(0x1C)
  if music ~= last_music then
    rows[#rows + 1] = string.format("%d,%d,%d,music,,", frames, music, read_word(0x24))
    last_music = music
  end
  if frames >= 2700 then
    local output = assert(io.open(output_path, "w"))
    output:write("frame,music,mode,port1,port2,pressed\n", table.concat(rows, "\n"), "\n",
                 table.concat(requests, "\n"), "\n")
    output:close()
    emu.stop(0)
  end
end, emu.eventType.endFrame)
