-- Opening capture (read-only game state): no input; one screen picture every 10
-- frames from 150 to 800 -> assets-raw/pirate/opening/frame-NNNN.ppm. Source for the
-- port's opening/title screens. Never overwrites.
local self_path = debug.getinfo(1, "S").source:gsub("^@", "")
local root = assert(self_path:gsub("\\", "/"):match("^(.*)/tools/replay%-compare/[^/]+$"))
local marker = root .. "/assets-raw/pirate/opening/frame-0150.ppm"
local existing = io.open(marker, "r")
if existing then
  existing:close()
  error("refusing to overwrite " .. marker)
end
local frames = 0

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

emu.addEventCallback(function()
  frames = frames + 1
  if frames >= 150 and frames % 10 == 0 then
    write_picture(root .. string.format("/assets-raw/pirate/opening/frame-%04d.ppm", frames))
  end
  if frames >= 800 then emu.stop(0) end
end, emu.eventType.endFrame)
