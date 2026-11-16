-- Matched opening replay followed by right-only walking to diagnose contacts.
-- Reads only the reviewed local input vector and USA v1.0 ROM; no state writes.
local self_path = debug.getinfo(1, "S").source:gsub("^@", "")
local root = assert(self_path:gsub("\\", "/"):match("^(.*)/tools/replay%-compare/[^/]+$"))
local reference = dofile(root .. "/data/original/pirate/reference_inputs.lua")
local frames, gameplay_start, rows, captured, stage = 0, nil, {}, {}, "read"
local function read_word(address)
  return emu.readWord(address, emu.memType.snesWorkRam)
end
-- Mesen table maps named keys; input-vector bit order follows SNES $4218:
-- B,Y,Select,Start,Up,Down,Left,Right,A,X,L,R.
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
    mask = reference.inputs[active + 1]
    if mask == nil then mask = 128 end -- $4218 bit7 is Right; B/Y remain unpressed
  else
    local menu_step = frames % 120
    mask = (frames > 600 and frames < 3000 and menu_step < 8) and 8 or 0 -- Start: input bit3
  end
  set_controller(mask)
end, emu.eventType.inputPolled)

emu.addEventCallback(function()
  frames = frames + 1
  local mode, level = read_word(0x24), read_word(0xD3)
  if not gameplay_start and level == 3 and mode == 0x8819 then gameplay_start = frames end
  if gameplay_start and mode == 0x8819 then
    local active = frames - gameplay_start
    local ptr = read_word(0x593)
    local row = { active, read_word(ptr + 6), read_word(ptr + 10),
                  read_word(ptr + 0x20), read_word(ptr + 0x24), read_word(ptr + 0x2E),
                  read_word(0x17BA), read_word(0x17C0), level, mode }
    rows[#rows + 1] = table.concat(row, ",")
    for _, target in ipairs({1024,1056,1072,1088,1120,1184,1248,1280,1296,1312,1320,1328,1344,1376,1408,1472,1536,1664,1792}) do
      if row[2] >= target and not captured[target] then
        captured[target] = true
        local size, pixels = emu.getScreenSize(), emu.getScreenBuffer()
        local ppm = assert(io.open(string.format(root .. "/assets-raw/pirate/reference-walk-v5-x%04d.ppm", target), "wb"))
        ppm:write(string.format("P6\n%d %d\n255\n", size.width, size.height))
        local chunk = {}
        for _, pixel in ipairs(pixels) do
          chunk[#chunk + 1] = string.char(math.floor(pixel / 65536) % 256, math.floor(pixel / 256) % 256, pixel % 256)
          if #chunk == 1024 then ppm:write(table.concat(chunk)); chunk = {} end
        end
        ppm:write(table.concat(chunk)); ppm:close()
      end
    end
  end
  if frames >= 4000 then
    stage = "write"
    local csv = assert(io.open(root .. "/assets-raw/pirate/reference-walk-collision-qa-v5.csv", "w"))
    csv:write("frame,x_raw,y_raw,vx_raw,vy_raw,state,cam_x_raw,cam_y_raw,level,mode\n")
    csv:write(table.concat(rows, "\n")); csv:close()
    emu.stop(0)
  end
end, emu.eventType.endFrame)
