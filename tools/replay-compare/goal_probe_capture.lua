-- Level-end probe. No original route reaches the goal (animal-route-t12..t14 stall at the
-- stern step, x ~6800 raw), so this probe WRITES the leader's position once: at active
-- frame TELEPORT the Kong is put on the stern deck (raw = port + $100, goal at raw x 7240,
-- deck feet 465), then walks right and jumps on the goal. Everything after is the game's
-- own: per frame the player ($593), the game mode ($24) and every live sprite slot ->
-- assets-raw/pirate/goal-route-<TAG>.csv. Inputs before TELEPORT: animal_route_capture t1/t2.
-- Never overwrites.
local TAG = "t9"
local FIRST, TELEPORT, LAST_FRAME = 4690, 4700, 4985
local TELEPORT_X, TELEPORT_Y = 7120, 440
-- t7 = t6 inputs plus VRAM/OAM/CGRAM/screen at SNAPSHOTS (high hit at 4921: barrel pieces
-- and the $23C effect at 4941/4946, prize landing 4958, bunch 4962, $1CC sprite 5050).
local SNAPSHOTS = {}
-- t8 = t7 inputs; pictures only, every 20th frame of the dance (4930-5400), and every
-- sound request (B581FB) as A rows with the current music ($1C): the dance music.
for frame = 4930, 5400, 20 do SNAPSHOTS[frame] = true end
-- t9 = t8 inputs, no pictures: the SPC700 state at VICTORY_SPC (the goal hit sends $FB 3,
-- $FE, $FA at 4916: the level song jumps to its victory part) -> goal-victory.spc.
SNAPSHOTS = {}
-- (4918 rendered silent: also 4925/4945/4980)
local VICTORY_SPC = { [4918] = true, [4925] = true, [4945] = true, [4980] = true }
-- { first active frame, last active frame, pad mask } (B 1, Y 2, UP 16, LEFT 64, RIGHT 128)
local OVERRIDES = {
  { 3393, 3419, 64 },
  { 3560, 3700, 130 },
  { TELEPORT, TELEPORT + 39, 0 },     -- land on the deck
  { TELEPORT + 40, TELEPORT + 99, 128 },  -- walk right
  { TELEPORT + 100, TELEPORT + 111, 129 },  -- t1: up onto the stern rail step (x 7090, feet 401)
  { TELEPORT + 112, 4869, 0 },
  -- t5 (the high hit, B3A2F6: goal y - camera y >= $68): jump off the rail step onto the
  -- goal box. t2-t4 kept as found: t4 (stop under the goal, jump straight up) = low hit.
  -- t6: t5 peaked at 325 ($0935 = the jump's highest y, not the camera) but landed at
  -- x 7176, short of the box: same jump running (Y).
  { 4870, 4881, 131 },
  { 4882, LAST_FRAME, 130 },
}

local self_path = debug.getinfo(1, "S").source:gsub("^@", "")
local root = assert(self_path:gsub("\\", "/"):match("^(.*)/tools/replay%-compare/[^/]+$"))
local reference = dofile(root .. "/data/original/pirate/reference_inputs.lua")
local output_path = root .. "/assets-raw/pirate/goal-route-" .. TAG .. ".csv"
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


emu.addMemoryCallback(function()
  if gameplay_start then
    local x = emu.getState()["cpu.x"]
    rows[#rows + 1] = string.format("A,%d,%d,%d,%d", frames - gameplay_start, x % 256,
      math.floor(x / 256) % 256, read_word(0x1C))
  end
end, emu.callbackType.exec, 0xB581FB, 0xB581FB, emu.cpuType.snes)

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
      emu.writeWord(player + 6, TELEPORT_X, emu.memType.snesWorkRam)
      emu.writeWord(player + 10, TELEPORT_Y, emu.memType.snesWorkRam)
      emu.writeWord(player + 0x24, 0, emu.memType.snesWorkRam)
    end
    if VICTORY_SPC[active] then
      local path = root .. string.format("/assets-raw/pirate/goal-victory-%d.spc", active)
      local existing = io.open(path, "rb")
      if existing then existing:close() else write_spc(path) end
    end
    if SNAPSHOTS[active] then
      local base = root .. string.format("/assets-raw/pirate/goal-%s-frame-%04d", TAG, active)
      write_picture(base .. ".ppm")
    end
    if active >= FIRST then
      rows[#rows + 1] = string.format("P,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d", active, read_word(player),
        read_word(player + 6), read_word(player + 10), read_word(player + 0x36), read_word(player + 0x2E),
        read_word(player + 0x20), read_word(player + 0x24), level, read_word(0x24), read_word(0x0935))
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
    if active >= LAST_FRAME or (active > TELEPORT and level ~= 3) then
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
