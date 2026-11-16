-- Capture screen pictures + CGRAM at item-visible frames of the matched USA v1.0 replay
-- (read-only game state). Outputs are new QA artifacts under ignored assets-raw/pirate;
-- never overwrites. Run with MesenCE --testrunner.
local self_path = debug.getinfo(1, "S").source:gsub("^@", "")
local root = assert(self_path:gsub("\\", "/"):match("^(.*)/tools/replay%-compare/[^/]+$"))
local reference = dofile(root .. "/data/original/pirate/reference_inputs.lua")
local output_path = root .. "/assets-raw/pirate/reference-items-frames.csv"
local existing_output = io.open(output_path, "r")
if existing_output then
  existing_output:close()
  error("refusing to overwrite " .. output_path)
end
local TARGETS = { [600] = true, [700] = true, [800] = true, [900] = true, [950] = true, [1000] = true }
local LAST_FRAME = 1000
local frames, gameplay_start, rows = 0, nil, {}

local function write_picture(filename)
  local size, pixels = emu.getScreenSize(), emu.getScreenBuffer()
  local image = assert(io.open(filename, "wb"))
  image:write(string.format("P6\n%d %d\n255\n", size.width, size.height))
  local chunks = {}
  for _, pixel in ipairs(pixels) do
    chunks[#chunks + 1] = string.char(math.floor(pixel / 65536) % 256,
                                      math.floor(pixel / 256) % 256, pixel % 256)
    if #chunks == 1024 then image:write(table.concat(chunks)); chunks = {} end
  end
  image:write(table.concat(chunks))
  image:close()
end

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
    if TARGETS[active] then
      local base = root .. string.format("/assets-raw/pirate/items-frame-%04d", active)
      write_picture(base .. ".ppm")
      write_memory(base .. "-cgram.bin", emu.memType.snesCgRam, 0x200)
      rows[#rows + 1] = string.format("%d,%d,%d,%d", active, read_word(0x17BA), read_word(0x17C0), read_word(0x2A))
    end
    if active >= LAST_FRAME then
      local output = assert(io.open(output_path, "w"))
      output:write("active_frame,layer1_x,layer1_y,clock\n")
      output:write(table.concat(rows, "\n"), "\n")
      output:close()
      emu.stop(0)
    end
  elseif frames >= 3000 then
    emu.log("ITEMS_FRAMES_GAMEPLAY_NOT_REACHED")
    emu.stop(22)
  end
end, emu.eventType.endFrame)
