-- Capture source Neek entity RAM during the matched USA v1.0 replay.
-- Output is a new QA artifact under ignored assets-raw/pirate; source ROM and
-- game state are read-only. Run with MesenCE --testRunner.
local self_path = debug.getinfo(1, "S").source:gsub("^@", "")
local root = assert(self_path:gsub("\\", "/"):match("^(.*)/tools/replay%-compare/[^/]+$"))
local reference = dofile(root .. "/data/original/pirate/reference_inputs.lua")
local output_path = root .. "/assets-raw/pirate/reference-neek-trace-qa4.csv"
local existing_output = io.open(output_path, "r")
if existing_output then
  existing_output:close()
  error("refusing to overwrite " .. output_path)
end
local frames, gameplay_start, rows = 0, nil, {}
local SPRITE_BASE, SPRITE_END, SPRITE_STRIDE, NEEK_ID = 0x0DE2, 0x16B2, 0x5E, 0x01E4

local function read_word(address)
  return emu.readWord(address, emu.memType.snesWorkRam)
end

local function read_byte(address)
  return emu.read(address, emu.memType.snesWorkRam)
end

local function signed16(value)
  return value >= 0x8000 and value - 0x10000 or value
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
    mask = reference.inputs[active + 1] or 128
  else
    local menu_step = frames % 120
    mask = (frames > 600 and frames < 3000 and menu_step < 8) and 8 or 0
  end
  set_controller(mask)
end, emu.eventType.inputPolled)

local function capture_active_frame(active)
  if active < 840 or active > 945 then
    return
  end

  local player = read_word(0x593)
  local player_x, player_y = read_word(player + 6), read_word(player + 10)
  local player_vx, player_vy = signed16(read_word(player + 0x20)), signed16(read_word(player + 0x24))
  local player_state, player_animation = read_word(player + 0x2E), read_word(player + 0x36)
  local camera_x, found = read_word(0x0D54), false

  for address = SPRITE_BASE, SPRITE_END - SPRITE_STRIDE, SPRITE_STRIDE do
    if read_word(address) == NEEK_ID then
      found = true
      rows[#rows + 1] = string.format("%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%s,%s",
        active, (address - SPRITE_BASE) / SPRITE_STRIDE,
        read_word(address + 6), read_byte(address + 5),
        read_word(address + 10), read_byte(address + 9),
        signed16(read_word(address + 0x20)), signed16(read_word(address + 0x24)),
        player_x, player_y, player_vx, player_vy, player_state, player_animation,
        camera_x, reference.rom_sha256, reference.input_sha256)
    end
  end

  if not found then
    rows[#rows + 1] = string.format("%d,,,,,,,,%d,%d,%d,%d,%d,%d,%d,%s,%s",
      active, player_x, player_y, player_vx, player_vy, player_state, player_animation,
      camera_x, reference.rom_sha256, reference.input_sha256)
  end
end

emu.addEventCallback(function()
  frames = frames + 1
  local mode, level = read_word(0x24), read_word(0xD3)
  if not gameplay_start and level == 3 and mode == 0x8819 then
    gameplay_start = frames
  end

  if gameplay_start and mode == 0x8819 then
    local active = frames - gameplay_start
    capture_active_frame(active)
    if active >= 945 then
      local output = assert(io.open(output_path, "w"))
      output:write("active_frame,slot,neek_x_raw,neek_sub_x,neek_y_raw,neek_sub_y,neek_vx_raw,neek_vy_raw,player_x_raw,player_y_raw,player_vx_raw,player_vy_raw,player_state,player_animation,camera_x_raw,rom_sha256,input_sha256\n")
      output:write(table.concat(rows, "\n"), "\n")
      output:close()
      emu.stop(0)
    end
  elseif frames >= 3000 then
    emu.log("NEEK_TRACE_GAMEPLAY_NOT_REACHED")
    emu.stop(22)
  end
end, emu.eventType.endFrame)
