local M = {}

M.TILE_EMPTY    = 0
M.TILE_SOLID    = 1
M.TILE_PLATFORM = 2
M.TILE_SPIKE    = 3
M.TILE_SLIP     = 4
M.TILE_WATER    = 5
M.TILE_CRACKED  = 6

M.tile_size = 16

local current_tilemap = nil
local map_width = 0
local map_height = 0
local original_surfaces = nil
local trace_enabled = false
local trace_frame = -1
local trace_events = {}
local TRACE_LIMIT = 4096

function M.set_collision_trace(enabled)
  trace_enabled, trace_frame, trace_events = enabled == true, -1, {}
end

function M.set_collision_trace_frame(frame)
  if trace_enabled then trace_frame = frame end
end

function M.collision_trace_snapshot()
  return trace_events
end

local function trace_contact(kind, pos_x, pos_y, col, row, value, surface)
  if not trace_enabled or #trace_events >= TRACE_LIMIT then return end
  trace_events[#trace_events + 1] = {
    frame = trace_frame, kind = kind,
    x = pos_x, y = pos_y, col = col, row = row,
    source_value = value, surface_y = surface,
  }
end

function M.load_original_surfaces(data)
  original_surfaces = data and data.cols > 0 and data or nil
end

local function original_height(col, row)
  if row < 0 or row >= original_surfaces.rows then return -1 end
  if col < 0 or col >= original_surfaces.cols then return 31 end
  return original_surfaces.heights[row * original_surfaces.cols + col + 1]
end

local function original_wall(col, y, h)
  for row = math.floor(y / 32), math.floor((y + h - 1) / 32) do
    local height = original_height(col, row)
    if height == -2 then return nil end -- unsupported original handler: legacy fallback
    if height >= 0 and y + h - 1 >= row * 32 + 32 - height then
      return true, { col = col, row = row, height = height, surface = row * 32 + 32 - height }
    end
  end
  return false
end

local function source_step_y(col, y, h, max_step)
  local bottom = y + h
  local first_row = math.floor((bottom - max_step) / 32)
  local last_row = math.floor(bottom / 32)
  local best
  for row = first_row, last_row do
    local height = original_height(col, row)
    if height == -2 then return nil end
    if height >= 0 then
      local surface = row * 32 + 32 - height
      local rise = bottom - surface
      if rise > 0 and rise <= max_step and (not best or surface < best) then best = surface end
    end
  end
  return best
end

local function original_floor(x, y, w, h, new_y)
  local left = math.floor(x - math.floor((w - 1) * 0.5))
  local right = math.floor(x + math.ceil((w - 1) * 0.5))
  local best, support = nil, nil
  for row = math.floor((y + h) / 32), math.floor((new_y + h) / 32) do
    for col = left, right do
      local height = original_height(col, row)
      if height == -2 then return nil end
      local surface = row * 32 + 32 - height
      if height >= 0 and y + h <= surface + 1 and new_y + h >= surface then
        if not best or surface < best then
          best = surface
          support = { col = col, row = row, height = height, surface = surface }
        end
      end
    end
  end
  return best or false, support
end

function M.load(tilemap_data, w, h)
  original_surfaces = nil
  current_tilemap = tilemap_data
  map_width = w
  map_height = h
end

function M.get_tile(col, row)
  if not current_tilemap then return M.TILE_EMPTY end
  if col < 0 or col >= map_width then
    return M.TILE_SOLID          -- paredes laterais fecham o nivel
  end
  if row < 0 or row >= map_height then
    -- Fora do nivel na vertical nao ha tile. Acima e ceu aberto (antes contava
    -- como solido e dava para ficar "em pe no ar" fora do mapa); abaixo e
    -- buraco -- quem passa de M.get_fall_limit() morre.
    return M.TILE_EMPTY
  end
  return current_tilemap[row + 1] and current_tilemap[row + 1][col + 1] or M.TILE_EMPTY
end

--- Y de mundo a partir do qual a queda e fatal (uma folga abaixo do nivel).
function M.get_fall_limit()
  return (map_height + 4) * M.tile_size
end

function M.world_to_tile(wx, wy)
  local col = math.floor(wx / M.tile_size)
  local row = math.floor(wy / M.tile_size)
  return col, row
end

local function is_solid(tile)
  return tile == M.TILE_SOLID or tile == M.TILE_SLIP or tile == M.TILE_CRACKED
end

local function is_one_way(tile)
  return tile == M.TILE_PLATFORM
end

function M.is_water_tile(tile)
  return tile == M.TILE_WATER
end

function M.is_in_water(px, py, w)
  local col = math.floor(px / M.tile_size)
  local row = math.floor((py + 4) / M.tile_size)
  local tile = M.get_tile(col, row)
  if tile == M.TILE_WATER then return true end
  local col_r = math.floor((px + w) / M.tile_size)
  if col_r ~= col then
    tile = M.get_tile(col_r, row)
    if tile == M.TILE_WATER then return true end
  end
  return false
end

function M.get_water_surface(px)
  local col = math.floor(px / M.tile_size)
  for row = 0, map_height - 1 do
    if M.get_tile(col, row) == M.TILE_WATER then
      return row * M.tile_size
    end
  end
  return nil
end

local function try_source_step(col, pos_y, h, allow_source_step, new_x, wall_info)
  if not allow_source_step then return nil end
  local step_surface = source_step_y(col, pos_y, h, 16)
  if not step_surface then return nil end
  trace_contact("source_slope_step", new_x, pos_y, wall_info.col, wall_info.row,
                wall_info.height, wall_info.surface)
  return new_x, false, step_surface - h
end

local function resolve_original_x(pos_x, pos_y, w, h, vel_x, allow_source_step)
  if not original_surfaces or vel_x == 0 then return nil end
  local new_x = pos_x + vel_x
  local local_left = math.floor((w - 1) * 0.5)
  local local_right = math.ceil((w - 1) * 0.5)
  local col = math.floor(new_x + (vel_x < 0 and -local_left or local_right))
  local wall, wall_info = original_wall(col, pos_y, h)
  if wall == nil then return nil end
  if not wall then return new_x, false end

  -- Only a grounded player may follow a source-profile rise of <=16px.
  local step_x, step_wall, step_y = try_source_step(col, pos_y, h, allow_source_step, new_x, wall_info)
  if step_x ~= nil then return step_x, step_wall, step_y end
  trace_contact("source_wall", pos_x, pos_y, wall_info.col, wall_info.row,
                wall_info.height, wall_info.surface)
  return vel_x < 0 and col + 1 + local_left or col - local_right - 1, true
end

function M.resolve_x(pos_x, pos_y, w, h, vel_x, allow_source_step)
  local source_x, source_wall, step_y = resolve_original_x(pos_x, pos_y, w, h, vel_x, allow_source_step)
  if source_x ~= nil then return source_x, source_wall, step_y end

  local new_x = pos_x + vel_x
  local local_left = math.floor((w - 1) * 0.5)
  local local_right = math.ceil((w - 1) * 0.5)

  if vel_x < 0 then
    local foot_row = math.floor((pos_y + h - 1) / M.tile_size)
    local head_row = math.floor(pos_y / M.tile_size)
    local left_col = math.floor((new_x - local_left) / M.tile_size)

    for r = head_row, foot_row do
      if is_solid(M.get_tile(left_col, r)) then
        trace_contact("legacy_grid_wall", pos_x, pos_y, left_col, r, M.get_tile(left_col, r))
        new_x = (left_col + 1) * M.tile_size + local_left
        return new_x, true
      end
    end

  elseif vel_x > 0 then
    local foot_row = math.floor((pos_y + h - 1) / M.tile_size)
    local head_row = math.floor(pos_y / M.tile_size)
    local right_col = math.floor((new_x + local_right) / M.tile_size)

    for r = head_row, foot_row do
      if is_solid(M.get_tile(right_col, r)) then
        trace_contact("legacy_grid_wall", pos_x, pos_y, right_col, r, M.get_tile(right_col, r))
        -- o -1 e necessario: a borda direita e `pos_x + local_right`, e sem ele
        -- ela cai no primeiro pixel do tile da parede. O resolvedor vertical
        -- entao le a parede como chao e empurra o player 1 tile para cima por
        -- frame, ate ele escalar a parede e sair do nivel.
        new_x = right_col * M.tile_size - local_right - 1
        return new_x, true
      end
    end
  end

  return new_x, false
end

function M.resolve_y(pos_x, pos_y, w, h, vel_y)
  local new_y = pos_y + vel_y
  if original_surfaces and vel_y > 0 then
    local floor, support = original_floor(pos_x, pos_y, w, h, new_y)
    if floor ~= nil then
      if floor then
        trace_contact("source_floor", pos_x, pos_y, support.col, support.row,
                      support.height, support.surface)
        return floor - h, true, "ground"
      end
      return new_y, false, nil
    end
  end

  if vel_y < 0 then
    local left_col = math.floor((pos_x - math.floor((w - 1) * 0.5)) / M.tile_size)
    local right_col = math.floor((pos_x + math.ceil((w - 1) * 0.5)) / M.tile_size)
    local head_row = math.floor(new_y / M.tile_size)

    for c = left_col, right_col do
      if is_solid(M.get_tile(c, head_row)) then
        trace_contact("legacy_grid_ceiling", pos_x, pos_y, c, head_row, M.get_tile(c, head_row))
        new_y = (head_row + 1) * M.tile_size
        return new_y, true, "ceiling"
      end
    end

  elseif vel_y > 0 then
    local left_col = math.floor((pos_x - math.floor((w - 1) * 0.5)) / M.tile_size)
    local right_col = math.floor((pos_x + math.ceil((w - 1) * 0.5)) / M.tile_size)
    local foot_row = math.floor((new_y + h - 1) / M.tile_size)

    for c = left_col, right_col do
      local tile = M.get_tile(c, foot_row)
      if is_solid(tile) then
        trace_contact("legacy_grid_floor", pos_x, pos_y, c, foot_row, tile)
        new_y = foot_row * M.tile_size - h
        return new_y, true, "ground"
      end
      if is_one_way(tile) and pos_y + h <= foot_row * M.tile_size + 2 then
        trace_contact("legacy_grid_platform", pos_x, pos_y, c, foot_row, tile)
        new_y = foot_row * M.tile_size - h
        return new_y, true, "platform"
      end
    end
  end

  return new_y, false, nil
end

--- Floor distance below the feet, like actor $000E read by the camera (B5E652):
-- whole pixels within `range`, or nil when no source floor is in reach.
-- The original writer of $000E is not traced yet; this reuses original_floor.
function M.ground_distance(pos_x, pos_y, w, h, range)
  if not original_surfaces then return nil end
  local floor = original_floor(pos_x, pos_y, w, h, pos_y + range)
  if not floor then return nil end
  return math.max(0, math.floor(floor - (pos_y + h)))
end

--- Topmost original surface in pixel column x with top <= surface <= bottom, or nil.
-- Walker feet follow it (route-bot-walkers.csv; slopes over flat ground at x 0x4FF).
function M.surface_at(x, top, bottom)
  if not original_surfaces then return nil end
  for row = math.floor(top / 32), math.floor(bottom / 32) do
    local height = original_height(x, row)
    if height and height >= 0 then
      local surface = row * 32 + 32 - height
      if surface >= top and surface <= bottom then return surface end
    end
  end
  return nil
end

--- HYPOTHESIS (walker terrain B8D4F8 not translated): the 32 px tile column `tile`
-- in the row holding the pixel above feet_y is a steep slope (a wall for walkers)
-- when two neighbouring columns differ by 3+ px (Pirate Panic x 0xA20-0xA3F: 4 px).
function M.steep_tile(tile, feet_y)
  if not original_surfaces then return false end
  local row = math.floor((feet_y - 1) / 32)
  local previous
  for col = tile * 32, tile * 32 + 31 do
    local height = original_height(col, row)
    if previous and previous >= 0 and height >= 0 and math.abs(height - previous) >= 3 then return true end
    previous = height
  end
  return false
end

function M.is_grounded(pos_x, pos_y, w, h)
  if original_surfaces then
    local floor = original_floor(pos_x, pos_y, w, h, pos_y + 1)
    if floor ~= nil then return floor ~= false end
  end
  local left_col = math.floor((pos_x - math.floor((w - 1) * 0.5)) / M.tile_size)
  local right_col = math.floor((pos_x + math.ceil((w - 1) * 0.5)) / M.tile_size)
  local foot_row = math.floor((pos_y + h) / M.tile_size)

  for c = left_col, right_col do
    local tile = M.get_tile(c, foot_row)
    if is_solid(tile) or is_one_way(tile) then
      return true
    end
  end
  return false
end

function M.check_spike(pos_x, pos_y, w, h)
  local left_col = math.floor((pos_x - math.floor((w - 1) * 0.5)) / M.tile_size)
  local right_col = math.floor((pos_x + math.ceil((w - 1) * 0.5)) / M.tile_size)
  local foot_row = math.floor((pos_y + h - 1) / M.tile_size)

  for c = left_col, right_col do
    if M.get_tile(c, foot_row) == M.TILE_SPIKE then
      return true
    end
  end
  return false
end

function M.break_tile(col, row)
  if not current_tilemap then return false end
  if col < 0 or col >= map_width or row < 0 or row >= map_height then return false end
  if current_tilemap[row + 1] and current_tilemap[row + 1][col + 1] == M.TILE_CRACKED then
    current_tilemap[row + 1][col + 1] = M.TILE_EMPTY
    return true
  end
  return false
end

function M.clear()
  original_surfaces = nil
  current_tilemap = nil
  map_width = 0
  map_height = 0
  trace_events = {}
end

return M
