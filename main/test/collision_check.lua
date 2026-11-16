local collision = require("main.collision")
local M = {}

function M.run()
  collision.load({{1}}, 1, 1)
  local heights = {}
  for index = 1, 16 * 7 do heights[index] = -1 end
  for column = 3, 13 do heights[6 * 16 + column + 1] = 15 end
  collision.load_original_surfaces({ cols = 16, rows = 7, heights = heights })
  local y, hit, kind = collision.resolve_y(8, 185, 10, 24, 1)
  assert(y == 185 and hit and kind == "ground", "original half-height floor must be at 209")
  local x, wall = collision.resolve_x(8, 185, 10, 24, 1)
  assert(x == 9 and not wall, "ground mistaken for horizontal wall")
  assert(collision.is_grounded(8, 185, 10, 24))
  collision.clear()
  local slope = {}
  for index = 1, 32 * 7 do slope[index] = -1 end
  for column = 3, 13 do slope[6 * 32 + column + 1] = 15 end
  slope[6 * 32 + 14 + 1] = 16
  slope[6 * 32 + 15 + 1] = 17
  collision.load_original_surfaces({ cols = 32, rows = 7, heights = slope })
  local slope_x, slope_wall = collision.resolve_x(8, 185, 10, 24, 1, true)
  assert(slope_x == 9 and not slope_wall, "1px original ramp was misclassified as wall")
  local slope_y, slope_hit, slope_kind = collision.resolve_y(slope_x, 185, 10, 24, 1)
  assert(slope_y == 184 and slope_hit and slope_kind == "ground", "player did not snap to original ramp height")
  collision.clear()
  heights = {}
  for index = 1, 32 * 7 do heights[index] = -1 end
  heights[6 * 32 + 12 + 1] = 16 -- one-pixel rise in original handler profile
  collision.load_original_surfaces({ cols = 32, rows = 7, heights = heights })
  -- Original surface columns are pixel-indexed; this step reaches column 12.
  local airborne_x, airborne_wall, airborne_y = collision.resolve_x(6, 185, 10, 24, 1, false)
  assert(airborne_x == 6 and airborne_wall and airborne_y == nil,
         "airborne player must not step through a source wall")
  local stepped_x, stepped_wall, stepped_y = collision.resolve_x(6, 185, 10, 24, 1, true)
  local step_error = string.format("one-pixel rise result: x=%s wall=%s y=%s",
                                   tostring(stepped_x), tostring(stepped_wall), tostring(stepped_y))
  assert(stepped_x == 7 and not stepped_wall and stepped_y == 184,
          step_error)
  local stepped, landed, step_kind = collision.resolve_y(stepped_x, stepped_y, 10, 24, 1)
  assert(stepped == 184 and landed and step_kind == "ground", "stepped player should remain on source surface")
  collision.clear()
  return true
end

return M
