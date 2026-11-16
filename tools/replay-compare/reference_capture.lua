-- Isolated original-game capture. Inputs are deterministic, never desktop keys.
-- Coordinates remain raw until matched to the original coordinate system.
local frames = 0
local rows = {}
local stage = "read"
local gameplay_start = nil
local gameplay_rows = {}
local camera_rows = {}
local pose_rows = {}
local kernel_rows = {}
local camera_aux_rows = {}
local camera_aux_byte_rows = {}
local targets = { [40]=true, [60]=true, [100]=true, [140]=true,
                  [153]=true, [158]=true, [165]=true, [173]=true, [180]=true }
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

local function write_ppu(filename)
  local state, fields = emu.getState(), {}
  local function collect(data, prefix)
    for key, value in pairs(data) do
      local name = prefix .. tostring(key)
      if type(value) == "table" then collect(value, name .. ".")
      elseif name:match("^ppu%.") then fields[#fields + 1] = name .. "=" .. tostring(value) end
    end
  end
  collect(state, "")
  table.sort(fields)
  local file = assert(io.open(filename, "w"))
  file:write(table.concat(fields, "\n"))
  file:close()
end
local self_path = debug.getinfo(1, "S").source:gsub("^@", "")
local project_root = assert(self_path:gsub("\\", "/"):match("^(.*)/tools/replay%-compare/[^/]+$"))
local self_file = assert(io.open(self_path, "r"))
local captured_script = self_file:read("*a")
self_file:close()
local function read_word(address)
  return emu.readWord(address, emu.memType.snesWorkRam)
end

local function input_callback()
  local buttons = { a=false, b=false, x=false, y=false, l=false, r=false,
                    start=false, select=false, up=false, down=false, left=false, right=false }
  -- Fresh boot menu navigation probe, not a claimed gameplay route.
  buttons.start = frames > 600 and frames < 3000 and frames % 120 < 8
  buttons.b = frames > 1200 and frames % 180 < 8
  if gameplay_start then
    buttons.start, buttons.b = false, false
    local step = (frames - gameplay_start) % 376
    buttons.right = step >= 40 and step < 218
    buttons.b = (step >= 150 and step < 158) or (step >= 318 and step < 326)
    buttons.left = step >= 218 and step < 258
  end
  local ok = pcall(emu.setInput, buttons, 0)
  if not ok then emu.setInput(0, buttons) end
end

emu.addEventCallback(function()
  local ok, message = pcall(input_callback)
  if not ok then emu.log(tostring(message)); emu.stop(21) end
end, emu.eventType.inputPolled)
local function capture_frame()
  frames = frames + 1
  if not gameplay_start and read_word(0xD3) == 3 and read_word(0x24) == 0x8819 then
    gameplay_start = frames
  end
  if gameplay_start then
    local active_frame = frames - gameplay_start
    if targets[active_frame] then
      write_picture(string.format(project_root .. "/assets-raw/pirate/reference-frame-%04d.ppm", active_frame))
      write_memory(string.format(project_root .. "/assets-raw/pirate/reference-frame-%04d-vram.bin", active_frame),
                   emu.memType.snesVideoRam, 0x10000)
      write_memory(string.format(project_root .. "/assets-raw/pirate/reference-frame-%04d-cgram.bin", active_frame),
                   emu.memType.snesCgRam, 0x200)
      write_ppu(string.format(project_root .. "/assets-raw/pirate/reference-frame-%04d-ppu.txt", active_frame))
    end
    local pointer = read_word(0x593)
    pose_rows[#pose_rows + 1] = string.format("%d,%d,%d,%d,%d,%d,%d,%d,%d",
      active_frame, read_word(pointer + 0x1A), read_word(pointer + 0x36),
      read_word(pointer + 0x3C), read_word(pointer + 0x12),
      read_word(pointer + 0x0E), read_word(0xD4E), read_word(0x2A),
      read_word(pointer + 0x38))
    local fields = { tostring(active_frame) }
    for _, address in ipairs({0xAC6,0xAC8,0xACA,0xACC,0xAD2,0xAD4,
                              0xADA,0xADC,0xAE2,0xAE4,0xAA6,0xAA8,0xAC2,0xAC4,0xA9E,0xA96,
                              -- Direct-page camera locals are based at $0A00 (routine TCD).
                              0x0ABC,0x0ABA,0x0ADF,0x0AE3,0x0AAA,0x0AAC,0x0AAE,0x0AB0,
                              0x0AB8,0x0A90,0x0ABF,0x0AC3,0x0AA2,0x0AA4,0x0AD6,0x0AD8,
                              0x0ADE,0x0AE0,0x0ACE,0x0AD0,0x0AC6,0x0AC8,0x0AC9,
                              0x0AEA,0x0AEC,0x0AEE,0x0ABE,0x0AC0,0x0AC2,0x0AC4}) do
      fields[#fields + 1] = tostring(read_word(address))
    end
    kernel_rows[#kernel_rows + 1] = table.concat(fields, ",")
    local aux = { tostring(active_frame) }
    for _, address in ipairs({0x0A98,0x0A9A,0x0A9C,0x0A9E,0x0AA0,0x0AA2,0x0AA4,0x0AA6,
      0x0AA8,0x0AAA,0x0AAC,0x0AAE,0x0AB0,0x0AB2,0x0AB4,0x0AB6,0x0AB8,0x0ABA,0x0ABC,
      0x0ABE,0x0AC0,0x0AC2,0x0AC4,0x0AC6,0x0AC8,0x0ACA,0x0ACC,0x0ACE,0x0AD0,0x0AD2,
      0x0AD4,0x0AD6,0x0AD8,0x0ADA,0x0ADC,0x0ADE,0x0AE0,0x0AE2,0x0AE4,0x0AE6,0x0AE8,
      0x0AEA,0x0AEC,0x0AEE,0x0AF0,0x0AF2,0x0AF4,0x0AF6,0x0AF8,0x0AFA,0x0D4E,0x0D50,
      0x0D52,0x0D54,0x0D56,0x0D58}) do
      aux[#aux + 1] = tostring(read_word(address))
    end
    camera_aux_rows[#camera_aux_rows + 1] = table.concat(aux, ",")
    local dp = { tostring(active_frame) }
    for _, offset in ipairs({0x90,0x92,0x94,0x96,0x98,0x9A,0x9C,0x9E,0x9F,0xA0,0xA2,0xA4,
      0xA6,0xA7,0xA8,0xAA,0xAC,0xAE,0xB0,0xB2,0xB4,0xB6,0xB8,0xBA,0xBC,0xBE,0xBF,
      0xC0,0xC2,0xC3,0xC4,0xC6,0xC8,0xC9,0xCA,0xCC,0xCD,0xCE,0xD0,0xD2,0xD4,
      0xD6,0xD8,0xDA,0xDB,0xDC,0xDE,0xE0,0xE2,0xE3,0xE4,0xE6,0xEA,0xEC,0xEE,
      0xF0,0xF2,0xF4,0xF6,0xF8,0xFA}) do
      dp[#dp + 1] = tostring(emu.read(0x0A00 + offset, emu.memType.snesWorkRam))
    end
    camera_aux_byte_rows[#camera_aux_byte_rows + 1] = table.concat(dp, ",")
    gameplay_rows[#gameplay_rows + 1] = string.format("%d,%d,%d,%d,%d,%d,%d,%d",
      frames - gameplay_start, read_word(pointer + 6), read_word(pointer + 10),
      read_word(pointer + 0x20), read_word(pointer + 0x24), read_word(pointer + 0x2E),
      read_word(0x50E), read_word(0x510))
    local hardware = emu.getState()
    local values = {}
    local function camera_fields(data, prefix)
      for key, value in pairs(data) do
        local path = prefix .. tostring(key)
        if type(value) == "table" then camera_fields(value, path .. ".")
        elseif path:match("^ppu%.layers%[[012]%]%.[hv]scroll$") then values[path] = value end
      end
    end
    camera_fields(hardware, "")
    camera_rows[#camera_rows + 1] = string.format("%d,%d,%d,%s,%s,%s,%s",
      frames - gameplay_start, read_word(0x17BA), read_word(0x17C0),
      tostring(values["ppu.layers[1].hscroll"]), tostring(values["ppu.layers[1].vscroll"]),
      tostring(values["ppu.layers[2].hscroll"]), tostring(values["ppu.layers[2].vscroll"]))
  end
  if frames % 60 == 0 then
    local player = read_word(0x593)
    rows[#rows + 1] = string.format("%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d",
      frames, read_word(0xD3), read_word(0x24), read_word(0x17BA),
      read_word(0x17C0), read_word(0xAFC), read_word(0xAFE), player,
      read_word(player + 6), read_word(player + 10),
      read_word(player + 0x20), read_word(player + 0x24))
  end
  if frames == 3000 then
    stage = "write"
    local target = project_root .. "/assets-raw/pirate/reference-navigation.csv"
    local file = assert(io.open(target, "w"))
    file:write("frame,level,game_mode,camera_x,camera_y,camera_max_x,camera_max_y,player_ptr,player_x_raw,player_y_raw,vx_raw,vy_raw\n")
    file:write(table.concat(rows, "\n"))
    file:close()
    local gameplay = assert(io.open(project_root .. "/assets-raw/pirate/reference-gameplay.csv", "w"))
    gameplay:write("active_frame,x_raw,y_raw,vx_raw,vy_raw,state_raw,hold_raw,pressed_raw\n")
    gameplay:write(table.concat(gameplay_rows, "\n"))
    gameplay:close()
    local poses = assert(io.open(project_root .. "/assets-raw/pirate/reference-poses.csv", "w"))
    poses:write("active_frame,pose_table_offset,animation_id,script_index,flags,meta_y,camera_floor_hint,game_counter,animation_timer\n")
    poses:write(table.concat(pose_rows, "\n"))
    poses:close()
    local kernel = assert(io.open(project_root .. "/assets-raw/pirate/reference-camera-kernel.csv", "w"))
    kernel:write("active_frame,x_cap,x_shifts,y_cap,y_shifts,y_velocity_lo,y_velocity_hi,y_position_lo,y_position_hi,y_target_lo,y_target_hi,y_prev_target_lo,y_prev_target_hi,y_focus_lo,y_focus_hi,y_shake,y_active_cap,region_index,search_index,viewport_x,viewport_y,x_low,x_high,y_low,y_high,direction,flags,aux_x,aux_y,old_target_x_lo,old_target_x_hi,old_position_x_lo,old_position_x_hi,new_target_x_lo,new_target_x_hi,camera_velocity_x_lo,camera_velocity_x_hi,accel_cap,x_shift,y_shift,camera_x_left,camera_x_right,camera_x_adjust,region_boundary_xlow,region_boundary_xhigh,region_boundary_ylow,region_boundary_yhigh\n")
    kernel:write(table.concat(kernel_rows, "\n"))
    kernel:close()
    local aux = assert(io.open(project_root .. "/assets-raw/pirate/reference-camera-aux.csv", "w"))
    aux:write("active_frame," .. table.concat({"a98","a9a","a9c","a9e","aa0","aa2","aa4","aa6","aa8","aaa","aac","aae","ab0","ab2","ab4","ab6","ab8","aba","abc","abe","ac0","ac2","ac4","ac6","ac8","aca","acc","ace","ad0","ad2","ad4","ad6","ad8","ada","adc","ade","ae0","ae2","ae4","ae6","ae8","aea","aec","aee","af0","af2","af4","af6","af8","afa","d4e","d50","d52","d54","d56","d58"}, ",") .. "\n")
    aux:write(table.concat(camera_aux_rows, "\n"))
    aux:close()
    local dpfile = assert(io.open(project_root .. "/assets-raw/pirate/reference-camera-dp-bytes.csv", "w"))
    dpfile:write("active_frame," .. table.concat({"90","92","94","96","98","9A","9C","9E","9F","A0","A2","A4","A6","A7","A8","AA","AC","AE","B0","B2","B4","B6","B8","BA","BC","BE","BF","C0","C2","C3","C4","C6","C8","C9","CA","CC","CD","CE","D0","D2","D4","D6","D8","DA","DB","DC","DE","E0","E2","E3","E4","E6","EA","EC","EE","F0","F2","F4","F6","F8","FA"}, ",") .. "\n")
    dpfile:write(table.concat(camera_aux_byte_rows, "\n"))
    dpfile:close()
    local cameras = assert(io.open(project_root .. "/assets-raw/pirate/reference-camera.csv", "w"))
    cameras:write("active_frame,camera_x_raw,camera_y_raw,bg2_hscroll,bg2_vscroll,bg3_hscroll,bg3_vscroll\n")
    cameras:write(table.concat(camera_rows, "\n"))
    cameras:close()
    local script = assert(io.open(project_root .. "/assets-raw/pirate/reference-capture-source.lua", "w"))
    script:write(captured_script)
    script:close()
    local state = emu.getState()
    local fields = {}
    local function collect(value, prefix)
      for key, item in pairs(value) do
        local name = prefix .. tostring(key)
        if type(item) == "table" then
          collect(item, name .. ".")
        elseif name:lower():find("ppu", 1, true) then
          fields[#fields + 1] = name .. "=" .. tostring(item)
        end
      end
    end
    collect(state, "")
    table.sort(fields)
    local hardware = assert(io.open(project_root .. "/assets-raw/pirate/reference-ppu.txt", "w"))
    hardware:write(table.concat(fields, "\n"))
    hardware:close()
    local size = emu.getScreenSize()
    local pixels = emu.getScreenBuffer()
    local picture = assert(io.open(project_root .. "/assets-raw/pirate/reference-navigation.ppm", "wb"))
    picture:write(string.format("P6\n%d %d\n255\n", size.width, size.height))
    for _, pixel in ipairs(pixels) do
      picture:write(string.char(math.floor(pixel / 65536) % 256,
                                math.floor(pixel / 256) % 256, pixel % 256))
    end
    picture:close()
    local snapshots = {
      { "wram", emu.memType.snesWorkRam, 0x20000 },
      { "vram", emu.memType.snesVideoRam, 0x10000 },
      { "cgram", emu.memType.snesCgRam, 0x200 },
    }
    for _, snapshot in ipairs(snapshots) do
      local dump = assert(io.open(project_root .. "/assets-raw/pirate/reference-" .. snapshot[1] .. ".bin", "wb"))
      local block = {}
      for address = 0, snapshot[3] - 1 do
        block[#block + 1] = string.char(emu.read(address, snapshot[2]))
        if #block == 1024 then dump:write(table.concat(block)); block = {} end
      end
      dump:write(table.concat(block))
      dump:close()
    end
    emu.stop(0)
  end
end
emu.addEventCallback(function()
  local ok, message = pcall(capture_frame)
  if not ok then
    emu.log(tostring(message))
    emu.stop(stage == "write" and 23 or 22)
  end
end, emu.eventType.endFrame)
