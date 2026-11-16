-- Framebuffer capture of this game only, opt-in QA; never desktop capture.
local M = { enabled = false, pending = 0 }
local frames = { [40]=true, [60]=true, [100]=true, [140]=true,
                 [153]=true, [158]=true, [165]=true, [173]=true, [180]=true,
                 [540]=true, [600]=true, [660]=true, [900]=true, [960]=true,
                 [1020]=true, [1080]=true, [1140]=true, [1200]=true, [1260]=true,
                 [566]=true, [567]=true, [568]=true, [938]=true, [939]=true,
                 [940]=true, [941]=true }
-- Mesen screenshots show RAM state 1-4 frames earlier: also capture f-4..f-1.
for _, reference in ipairs({ 40, 60, 100, 140, 153, 158, 165, 173, 180 }) do
  for back = 1, 4 do frames[reference - back] = true end
end
-- Banana pickup -> flight -> counter window of the reference route (197-238).
for _, frame in ipairs({ 200, 215, 230, 245 }) do frames[frame] = true end
-- Route QA: Klobber area (x 3800-4100) and level end.
for frame = 1880, 2060, 30 do frames[frame] = true end
local captures = {}
local captured_collision_sites = {}
local max_collision_captures = 12

function M.init()
  M.enabled = (sys.get_config_string or sys.get_config)("dkc2.capture_qa", "0") == "1"
  captures = {}
  captured_collision_sites = {}
  M.pending = 0
  if M.enabled then
    assert(screenshot and screenshot.png, "QA capture requires approved screenshot native engine")
    -- QA only: extra frames, "first-last/step" ranges separated by commas (e.g. 1600-1700/4)
    for first, last, step in ((sys.get_config_string or sys.get_config)("dkc2.capture_frames", "")):gmatch("(%d+)-(%d+)/(%d+)") do
      for frame = tonumber(first), tonumber(last), tonumber(step) do frames[frame] = true end
    end
  end
end

local function capture(frame, metadata)
  captures[#captures + 1] = { status = "pending", frame = frame, metadata = metadata }
  local index = #captures
  M.pending = M.pending + 1
  -- Callback runs after renderer has drawn the frame, not before it.
  screenshot.png(function(self, png, width, height)
    assert(type(png) == "string" and #png > 0, "empty QA framebuffer capture")
    local filename = metadata and string.format("qa-collision-%s-c%d-r%d-f%04d.png",
      metadata.kind, metadata.col, metadata.row, frame)
      or string.format("qa-frame-%04d.png", frame)
    local file = assert(io.open(filename, "wb"))
    file:write(png)
    file:close()
    captures[index] = { status = "captured", frame = frame, file = filename,
                        metadata = metadata, width = width, height = height, bytes = #png }
    M.pending = M.pending - 1
    local manifest = assert(io.open("qa-captures.json", "w"))
    local list = {}
    for _, capture in pairs(captures) do list[#list + 1] = capture end
    manifest:write(json.encode({ scope = "game framebuffer only; not visual-fidelity verdict",
                                 captures = list, pending = M.pending }))
    manifest:close()
  end)
end

function M.after_update(frame)
  if not M.enabled then return end
  if frames[frame] and not captures[frame] then capture(frame, nil) end

  local get_config = sys.get_config_string or sys.get_config
  if get_config("dkc2.collision_walk_qa", "0") ~= "1"
      or #captured_collision_sites >= max_collision_captures then return end
  local events = require("main.collision").collision_trace_snapshot()
  -- Floor probes can dominate a frame; search all contacts from the current
  -- processed frame instead of only a small tail of the event array.
  for index = #events, 1, -1 do
    local event = events[index]
    if event.frame < frame - 1 then break end
    -- Contact trace may be appended by player and object collision passes in
    -- different order. Capture current rendered scene for every new wall site;
    -- metadata retains exact source event frame/coordinates.
    if event.kind == "source_wall" or event.kind == "legacy_grid_wall" then
      local key = table.concat({event.kind, event.col, event.row, event.source_value}, ":")
      if not captured_collision_sites[key] then
        captured_collision_sites[key] = true
        captured_collision_sites[#captured_collision_sites + 1] = key
        local camera = require("main.camera")
        capture(frame, { kind = event.kind, frame = event.frame, x = event.x, y = event.y,
          col = event.col, row = event.row, source_value = event.source_value,
          surface_y = event.surface_y, camera_x = camera.pos_x, camera_y = camera.pos_y })
        break
      end
    end
  end
end

return M
