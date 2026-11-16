local M = {}

M.pos_x = 0
M.pos_y = 0
M.boundary_x = 2560
M.boundary_y = 1440
M.viewport_w = 256
M.viewport_h = 224
local original = nil
local original_camera = require("main.original_camera")

M.dead_zone_w = 80
M.dead_zone_h = 40
M.smooth_speed = 6

M.layers = {}

M.parallax_pos = {}

function M.init()
  original = nil
  M.pos_x = 0
  M.pos_y = 0
  M.boundary_x = 2560
  M.boundary_y = 1440
  M.parallax_pos = {}
end

function M.set_original_profile(profile)
  original = profile
  M.original_active = profile ~= nil
end

-- Actor $000E for B5E652: floor distance probed up to $50 px below the feet.
local function original_ground(x, y)
  local actor = require("main.player")
  local _, top, w, h = actor.get_hitbox()
  local distance = require("main.collision").ground_distance(x, top or y, w, h, 0x50)
  -- Unsupported source handlers yield no probe; a supported actor is on its floor.
  if distance == nil and actor.grounded then return 0 end
  return distance
end

local function original_position(x, y)
  return math.max(0, math.min(x - original.anchor_x, original.max_x)),
         math.max(0, math.min(y + 24 - original.anchor_y, original.max_y))
end

function M.set_parallax_layers(speeds)
  M.layers = {}
  for name, speed in pairs(speeds) do
    table.insert(M.layers, { name = name, speed = speed })
    M.parallax_pos[name] = 0
  end
  table.sort(M.layers, function(a, b) return a.speed < b.speed end)
end

--- Segue o alvo com dt real (game.lua passa dt; callers legados sem dt
-- caem no passo fixo 1/60 para preservar comportamento).
-- Native 256x224 world, integer upscaling handled only by native.render_script.
-- Original camera profile is capture-derived but does not emulate wave/HDMA motion.
M.INTERNAL_W = 256
M.INTERNAL_H = 224
M.PIXEL_SCALE = 4
function M.follow(target_x, target_y, screen_w, screen_h, dt)
  if original then
    local actor = require("main.player")
    -- Hit-stop mirrors $0A36 bit $80: game.lua runs follow after stomp events.
    local x, y = original_camera.update(target_x, target_y + 24, actor.direction < 0,
                                        original_ground(target_x, target_y),
                                        (actor.hitpause_frames or 0) > 0)
    if x then M.pos_x, M.pos_y = x, y
    else M.pos_x, M.pos_y = original_position(target_x, target_y) end
    for _, layer in ipairs(M.layers) do M.parallax_pos[layer.name] = M.pos_x * layer.speed end
    return
  end
  screen_w = screen_w or M.viewport_w
  screen_h = screen_h or M.viewport_h
  dt = dt or (1 / 60)

  local half_w = screen_w * 0.5
  local half_h = screen_h * 0.5

  local desired_x = target_x - half_w
  local desired_y = target_y - half_h

  if math.abs(target_x - (M.pos_x + half_w)) > M.dead_zone_w then
    local dz = M.dead_zone_w
    if target_x > M.pos_x + half_w + dz then
      desired_x = target_x - half_w - dz
    elseif target_x < M.pos_x + half_w - dz then
      desired_x = target_x - half_w + dz
    end
  else
    desired_x = M.pos_x
  end

  if math.abs(target_y - (M.pos_y + half_h)) > M.dead_zone_h then
    local dz = M.dead_zone_h
    if target_y > M.pos_y + half_h + dz then
      desired_y = target_y - half_h - dz
    elseif target_y < M.pos_y + half_h - dz then
      desired_y = target_y - half_h + dz
    end
  else
    desired_y = M.pos_y
  end

  desired_x = math.max(0, math.min(desired_x, math.max(0, M.boundary_x - screen_w)))
  desired_y = math.max(0, math.min(desired_y, math.max(0, M.boundary_y - screen_h)))

  M.pos_x = M.pos_x + (desired_x - M.pos_x) * math.min(1, M.smooth_speed * dt)
  M.pos_y = M.pos_y + (desired_y - M.pos_y) * math.min(1, M.smooth_speed * dt)

  for _, layer in ipairs(M.layers) do
    M.parallax_pos[layer.name] = M.pos_x * layer.speed
  end
end

function M.get_parallax_offset(layer_name)
  return M.parallax_pos[layer_name] or M.pos_x
end

function M.get_parallax_offsets()
  local result = {}
  for name, pos in pairs(M.parallax_pos) do
    result[name] = pos
  end
  return result
end

function M.set_boundaries(max_x, max_y)
  M.boundary_x = max_x
  M.boundary_y = max_y
end

function M.snap_to(x, y)
  if original then
    local config = sys.get_config_number or function(key, default) return tonumber(sys.get_config(key, default)) end
    local clock = config("dkc2.original_clock", 0)
    require("main.original_bg2").init()  -- BBA655 re-arms the BG2 HDMA table per level
    M.pos_x, M.pos_y = original_camera.init(clock, x, y + 24,
                                            require("main.player").direction < 0, original_ground(x, y))
    return
  end
  M.pos_x = math.max(0, math.min(x - M.viewport_w * 0.5, math.max(0, M.boundary_x - M.viewport_w)))
  M.pos_y = math.max(0, math.min(y - M.viewport_h * 0.5, math.max(0, M.boundary_y - M.viewport_h)))
end

return M
