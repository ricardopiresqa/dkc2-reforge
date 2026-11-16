-- Opening: the original boot sequence (Rare logo, Nintendo presents, copyright, title
-- "Diddy's Kong Quest") replayed from frames captured at their original times
-- (data/original/pirate/opening.lua, tools/replay-compare/export_opening.py).
-- The logos (150-800) come from a capture of every frame (opening60_capture.lua), each
-- frame cropped to its picture (x, y, w, h on the 256x224 screen); a frame without a
-- sprite is black. The Nintendo logo frames are hi-res (512 wide): drawn at scale 0.5.
-- The title (title60_capture.lua): from 800 the steady picture fades in by the measured
-- brightness steps, then the chest sparkles play as patches over it (one per captured
-- frame). APPROXIMATION: the sparkles are not periodic in the original (850 frames
-- captured); the port loops the captured 850-1700 run.
local M = { frame = 0 }

local FIRST_FRAME = 150   -- first captured boot frame (screen black before it)
local TITLE_FRAME = 720   -- the title screen is fully faded in from here on
local frames

function M.init(skip_to_title)
  local ok, data = pcall(function() return require("data.original.pirate.opening") end)
  frames = ok and type(data) == "table" and #data > 0 and data or nil
  M.frame = skip_to_title and TITLE_FRAME or FIRST_FRAME
end

function M.available()
  return frames ~= nil
end

function M.update()
  if not frames then return end
  M.frame = M.frame + 1
  local title = frames.title
  if title and M.frame > title.loop_end then M.frame = title.steady end
end

--- Screen layers { {sprite, x, y, w, h, scale}, ... } and brightness (renderer.draw_layers).
function M.layers()
  local title = frames and frames.title
  if title and M.frame >= title.from then
    local layers = { { title.base, 0, 0, 256, 224 } }
    if M.frame < title.steady then
      return layers, title.fade[M.frame - title.from + 1] or 1
    end
    local current
    for _, entry in ipairs(title.sparkles) do
      if entry[1] > M.frame then break end
      current = entry[2]
    end
    if current then layers[2] = { current, title.box[1], title.box[2], title.box[3], title.box[4] } end
    return layers, 1
  end
  local sprite, x, y, w, h, scale = M.sprite()
  if not sprite then return {}, 1 end
  return { { sprite, x, y, w, h, scale } }, 1
end

--- START during the logos jumps to the title.
function M.skip()
  M.frame = math.max(M.frame, TITLE_FRAME)
end

function M.at_title()
  return M.frame >= TITLE_FRAME
end

--- Current screen: atlas animation, x, y, w, h (top-left box on 256x224), or nil.
function M.sprite()
  if not frames then return nil end
  local current = frames[1]
  for _, entry in ipairs(frames) do
    if entry.frame > M.frame then break end
    current = entry
  end
  if not current.sprite then return nil end
  return current.sprite, current.x or 0, current.y or 0, current.w or 256, current.h or 224, current.scale
end

return M
