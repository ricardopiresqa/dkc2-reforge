-- Carry / throw probe (read-only): the route bot (reference inputs, then RIGHT + Y with
-- B 12/48) picks up a barrel around active frame 1072 and carries it until ~1230
-- (route-bot-trace.csv). Pictures every 4th frame 1060-1240, player rows, sprite rows
-- and every sound request (A rows) -> assets-raw/pirate/carry-route-t1.csv,
-- carry-t1-frame-NNNN.ppm. Never overwrites.
local TAG = "t2"
local FIRST, TELEPORT, LAST_FRAME = 1000, -1, 1210
local TELEPORT_Y = 525
local SNAPSHOTS = {}
for frame = 1146, 1200, 2 do SNAPSHOTS[frame] = true end
-- t2: Y released at 1150 while carrying (RIGHT only): the throw.
local OVERRIDES = { { 1150, 1210, 128 } }

local self_path = debug.getinfo(1, "S").source:gsub("^@", "")
local root = assert(self_path:gsub("\\", "/"):match("^(.*)/tools/replay%-compare/[^/]+$"))
local reference = dofile(root .. "/data/original/pirate/reference_inputs.lua")
local output_path = root .. "/assets-raw/pirate/carry-route-" .. TAG .. ".csv"
local existing_output = io.open(output_path, "r")
if existing_output then
  existing_output:close()
  error("refusing to overwrite " .. output_path)
end
local BOT_START = 1033
local frames, gameplay_start, rows = 0, nil, {}

local function write_memory(filename, memory, size)
  local output = assert(io.open(filename, "wb"))
  local chunks = {}
  for address = 0, size - 1 do
    chunks[#chunks + 1] = string.char(emu.read(address, memory))
    if #chunks == 1024 then output:write(table.concat(chunks)); chunks = {} end
  end
  output:write(table.concat(chunks))
  output:close()
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

emu.addMemoryCallback(function()
  if gameplay_start then
    local x = emu.getState()["cpu.x"]
    rows[#rows + 1] = string.format("A,%d,%d,%d", frames - gameplay_start, x % 256, math.floor(x / 256) % 256)
  end
end, emu.callbackType.exec, 0xB581FB, 0xB581FB, emu.cpuType.snes)

emu.addEventCallback(function()
  local mask
  if gameplay_start then
    local active = frames - gameplay_start
    local override
    for _, window in ipairs(OVERRIDES) do
      if active >= window[1] and active <= window[2] then override = window[3] end
    end
    if override then
      mask = override
    elseif active < BOT_START then
      mask = reference.inputs[active + 1] or 128
    else
      local tick = (active - BOT_START) % 48
      mask = 128 + 2 + (tick < 12 and 1 or 0)  -- route bot: RIGHT + Y, B 12/48
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
    if active == TELEPORT then
      emu.writeWord(player + 10, TELEPORT_Y, emu.memType.snesWorkRam)
      emu.writeWord(player + 0x24, 0, emu.memType.snesWorkRam)
    end
    if SNAPSHOTS[active] then
      local base = root .. string.format("/assets-raw/pirate/carry-%s-frame-%04d", TAG, active)
      write_picture(base .. ".ppm")
    end
    if active >= FIRST then
      rows[#rows + 1] = string.format("P,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d", active, read_word(player),
        read_word(player + 6), read_word(player + 10), read_word(player + 0x36), read_word(player + 0x2E),
        read_word(player + 0x20), read_word(player + 0x24), level, read_word(0x24), read_word(0x0935))
      for index = 0, 127 do
        local y, tile = emu.read(index * 4 + 1, emu.memType.snesSpriteRam), emu.read(index * 4 + 2, emu.memType.snesSpriteRam)
        local attr = emu.read(index * 4 + 3, emu.memType.snesSpriteRam)
        tile = tile + (attr % 2) * 256
        if y < 60 and tile >= 0x1CC and tile < 0x1E0 then
          rows[#rows + 1] = string.format("D,%d,%d,%d,%d", active, emu.read(index * 4, emu.memType.snesSpriteRam), y, tile)
        end
      end
      for _, holder in ipairs({ 0x097B, 0x097D }) do
        local hud = read_word(holder)
        if hud ~= 0 then
          rows[#rows + 1] = string.format("H,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d", active, holder, hud, read_word(hud),
            read_word(hud + 6), read_word(hud + 10), read_word(hud + 0x2E), read_word(hud + 0x44),
            read_word(hud + 0x46), read_word(hud + 0x12), read_word(hud + 0x1A), read_word(hud + 0x36))
        end
      end
      for address = 0x0DE2, 0x16B2 - 0x5E, 0x5E do
        local id = read_word(address)
        if id ~= 0 then
          rows[#rows + 1] = string.format("S,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d", active, address, id,
            read_word(address + 6), read_word(address + 10), read_word(address + 0x36),
            read_word(address + 0x2E), read_word(address + 0x20), read_word(address + 0x24),
            read_word(address + 0x1A))
        end
      end
    end
    if active >= LAST_FRAME or false then
      local output = assert(io.open(output_path, "w"))
      output:write("kind,active_frame,a,b,c,d,e,f,g,h,i,j\n")
      output:write(table.concat(rows, "\n"), "\n")
      output:close()
      emu.stop(0)
    end
  elseif frames >= 3000 then
    emu.log("ROUTE_BOT_GAMEPLAY_NOT_REACHED")
    emu.stop(22)
  end
end, emu.eventType.endFrame)
