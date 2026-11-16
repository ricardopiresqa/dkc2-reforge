-- Music snapshot (read-only game state): matched USA v1.0 reference inputs into Pirate
-- Panic, then at gameplay frame SNAPSHOT_FRAME the SPC700 state (64 KB ARAM, 128 DSP
-- registers, SPC CPU registers; $F0-$FF rebuilt from the I/O state: control, DSP address,
-- ports, timer targets) is written as an .spc file (v0.30 layout) for local
-- rendering (tools/replay-compare/render_music.py). Never overwrites.
local self_path = debug.getinfo(1, "S").source:gsub("^@", "")
local root = assert(self_path:gsub("\\", "/"):match("^(.*)/tools/replay%-compare/[^/]+$"))
local reference = dofile(root .. "/data/original/pirate/reference_inputs.lua")
local output_path = root .. "/assets-raw/pirate/pirate-panic-music2.spc"
local existing_output = io.open(output_path, "rb")
if existing_output then
  existing_output:close()
  error("refusing to overwrite " .. output_path)
end
local SNAPSHOT_FRAME = 2
local frames, gameplay_start = 0, nil

local function read_word(address)
  return emu.readWord(address, emu.memType.snesWorkRam)
end

local function mem_type(...)
  for _, name in ipairs({ ... }) do
    if emu.memType[name] ~= nil then return emu.memType[name] end
  end
  error("no SPC memory type among: " .. table.concat({ ... }, ", "))
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

local function write_spc()
  local ram = mem_type("spcRam", "snesSpcRam")
  local dsp = mem_type("spcDspRegisters", "snesSpcDspRegisters")
  local state = emu.getState()
  local function reg(...)
    for _, key in ipairs({ ... }) do
      if state[key] ~= nil then return state[key] end
    end
    error("missing SPC register " .. table.concat({ ... }, "/"))
  end
  local pc = reg("spc.pc", "snes.spc.pc")
  local header = "SNES-SPC700 Sound File Data v0.30" .. string.char(26, 26, 27, 30)
  local out = { header,
    string.char(pc % 256, math.floor(pc / 256) % 256,
                reg("spc.a", "snes.spc.a") % 256, reg("spc.x", "snes.spc.x") % 256,
                reg("spc.y", "snes.spc.y") % 256, reg("spc.ps", "spc.psw", "snes.spc.ps") % 256,
                reg("spc.sp", "snes.spc.sp") % 256, 0, 0) }
  out[#out + 1] = string.rep("\0", 0x100 - 0x2E)
  local io_regs = {}  -- $F0-$FF as the hardware registers hold them
  local function flag(key) return state[key] == true and 1 or 0 end
  io_regs[0xF0] = 0x0A
  io_regs[0xF1] = flag("spc.timer0.enabled") + 2 * flag("spc.timer1.enabled") + 4 * flag("spc.timer2.enabled")
             + 128 * flag("spc.romEnabled")
  io_regs[0xF2] = (state["spc.dspReg"] or 0) % 256
  io_regs[0xF3] = emu.read(io_regs[0xF2] % 128, dsp)
  for port = 0, 3 do io_regs[0xF4 + port] = (state["spc.cpuRegs[" .. port .. "]"] or 0) % 256 end
  io_regs[0xF8] = (state["spc.ramReg[0]"] or 0) % 256
  io_regs[0xF9] = (state["spc.ramReg[1]"] or 0) % 256
  for timer = 0, 2 do
    io_regs[0xFA + timer] = (state["spc.timer" .. timer .. ".target"] or 0) % 256
    io_regs[0xFD + timer] = (state["spc.timer" .. timer .. ".output"] or 0) % 16
  end
  local chunk = {}
  for address = 0, 0xFFFF do
    chunk[#chunk + 1] = string.char(io_regs[address] or emu.read(address, ram))
    if #chunk == 4096 then out[#out + 1] = table.concat(chunk); chunk = {} end
  end
  out[#out + 1] = table.concat(chunk)
  chunk = {}
  for address = 0, 0x7F do chunk[#chunk + 1] = string.char(emu.read(address, dsp)) end
  out[#out + 1] = table.concat(chunk)
  out[#out + 1] = string.rep("\0", 0x80)
  local file = assert(io.open(output_path, "wb"))
  file:write(table.concat(out))
  file:close()
end

emu.addEventCallback(function()
  frames = frames + 1
  local mode, level = read_word(0x24), read_word(0xD3)
  if not gameplay_start and level == 3 and mode == 0x8819 then gameplay_start = frames end
  if gameplay_start and frames - gameplay_start >= SNAPSHOT_FRAME then
    write_spc()
    emu.stop(0)
  elseif not gameplay_start and frames >= 3000 then
    emu.log("MUSIC_SPC_GAMEPLAY_NOT_REACHED")
    emu.stop(22)
  end
end, emu.eventType.endFrame)
