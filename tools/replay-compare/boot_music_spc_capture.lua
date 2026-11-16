-- Opening and title music from their start (read-only game state): from boot, no input.
-- menu-sound.csv: song 17 (Opening) starts playing on frame 145, song 2 (title) on 766;
-- the SPC700 state one frame later -> assets-raw/pirate/music-test3/boot-17.spc, boot-02.spc.
-- Never overwrites.
local self_path = debug.getinfo(1, "S").source:gsub("^@", "")
local root = assert(self_path:gsub("\\", "/"):match("^(.*)/tools/replay%-compare/[^/]+$"))
local out_dir = root .. "/assets-raw/pirate/music-test3/"
local frames = 0
local function mem_type(...)
  for _, name in ipairs({ ... }) do
    if emu.memType[name] ~= nil then return emu.memType[name] end
  end
  error("no SPC memory type among: " .. table.concat({ ... }, ", "))
end

local function write_spc(output_path)
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


local SNAPS = { [146] = "boot-17.spc", [767] = "boot-02.spc" }
emu.addEventCallback(function()
  frames = frames + 1
  local name = SNAPS[frames]
  if name then
    local path = out_dir .. name
    local existing = io.open(path, "rb")
    if existing then existing:close() else write_spc(path) end
  end
  if frames >= 770 then emu.stop(0) end
end, emu.eventType.endFrame)
