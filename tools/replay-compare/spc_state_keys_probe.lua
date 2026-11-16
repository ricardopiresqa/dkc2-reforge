-- Probe (read-only): lists emu.getState() keys containing "spc" after boot, to build
-- correct .spc headers (timer targets / control registers). Writes a new text file.
local self_path = debug.getinfo(1, "S").source:gsub("^@", "")
local root = assert(self_path:gsub("\\", "/"):match("^(.*)/tools/replay%-compare/[^/]+$"))
local output_path = root .. "/assets-raw/pirate/spc-state-keys.txt"
local existing = io.open(output_path, "r")
if existing then existing:close(); error("refusing to overwrite " .. output_path) end
local frames = 0
emu.addEventCallback(function()
  frames = frames + 1
  if frames == 300 then
    local lines = {}
    for key, value in pairs(emu.getState()) do
      if tostring(key):lower():find("spc") or tostring(key):lower():find("dsp") then
        lines[#lines + 1] = tostring(key) .. "=" .. tostring(value)
      end
    end
    table.sort(lines)
    local mem = {}
    for name, value in pairs(emu.memType) do mem[#mem + 1] = tostring(name) end
    table.sort(mem)
    local file = assert(io.open(output_path, "w"))
    file:write(table.concat(lines, "\n"), "\n\nmemTypes: ", table.concat(mem, ", "), "\n")
    file:close()
    emu.stop(0)
  end
end, emu.eventType.endFrame)
