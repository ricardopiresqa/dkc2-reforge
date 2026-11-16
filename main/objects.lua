local bit = require("bit")

local M = {}

local TILE_SIZE = 16
local NEEK_SOURCE_SPEED = -60 -- source $FF00: -1 pixel per 60 Hz frame

M.FLAG_ACTIVE    = bit.lshift(1, 0)
M.FLAG_COLLECTED = bit.lshift(1, 1)
M.FLAG_DAMAGE    = bit.lshift(1, 2)

M.OBJ_BANANA       = 1
M.OBJ_BANANA_BUNCH = 2
M.OBJ_DK_COIN      = 3
M.OBJ_LIFE         = 4
M.OBJ_KRITTER      = 5
M.OBJ_ZINGER       = 6
M.OBJ_KRUSHA       = 7
M.OBJ_BARREL       = 8
M.OBJ_RAMBI        = 9
M.OBJ_ENGUARDE     = 10
M.OBJ_FLITTER      = 11
M.OBJ_KLAMP        = 12
M.OBJ_KLOBBER      = 13
M.OBJ_KANNON       = 14
M.OBJ_MININECKY    = 15
M.OBJ_PROJECTILE   = 16
M.OBJ_KABOOM       = 17
M.OBJ_KUTLASS      = 18
M.OBJ_KLUDGE       = 19
M.OBJ_SQUITTER     = 20
M.OBJ_RATTLY       = 21
M.OBJ_SQUAWKS      = 22
M.OBJ_EXPRESSO     = 23
M.OBJ_BONUS_BARREL = 24
M.OBJ_ANIMAL_CRATE = 25
M.OBJ_LETTER_K    = 26
M.OBJ_LETTER_O    = 27
M.OBJ_LETTER_N    = 28
M.OBJ_LETTER_G    = 29
M.OBJ_ROPE        = 30
M.OBJ_ORIGINAL_STATIC = 31 -- source identity retained while its native handler is unported

local objects = {}
local next_id = 1
local last_neek_player_bottom = nil

local function neek_top_crossing(obj, px, pw, player_bottom, previous_player_bottom)
  local previous_top = obj.source_neek_previous_y
  if not obj.source_neek_active or not obj.source_neek_supported
      or previous_top == nil or previous_player_bottom == nil then
    return false
  end

  local previous_x = obj.source_neek_previous_x or obj.x
  local left = previous_x - obj.width * 0.5
  return previous_player_bottom <= previous_top
      and player_bottom > obj.y
      and player_bottom > previous_player_bottom
      and px < left + obj.width
      and px + pw > left
end

local function new_id()
  local id = next_id
  next_id = next_id + 1
  return id
end

function M.spawn(type_id, x, y, params)
  params = params or {}
  local obj = {
    id = new_id(),
    type = type_id,
    x = x, y = y,
    vel_x = 0, vel_y = 0,
    flags = M.FLAG_ACTIVE,
    timer = 0,
    anim_frame = 0,
    anim_timer = 0,
    width = 12, height = 12,
    direction = 1,
    float_offset = math.random() * math.pi * 2,
    params = params,
  }

  if type_id == M.OBJ_BANANA then
    obj.width = 10; obj.height = 14
    obj.collect_radius = 20
  elseif type_id == M.OBJ_BANANA_BUNCH then
    obj.width = 16; obj.height = 16
    obj.collect_radius = 24
  elseif type_id == M.OBJ_DK_COIN then
    obj.width = 14; obj.height = 14
    obj.collect_radius = 20
  elseif type_id == M.OBJ_LIFE then
    obj.width = 16; obj.height = 16
    obj.collect_radius = 24
  elseif type_id == M.OBJ_KRITTER then
    obj.width = 20; obj.height = 24
    obj.vel_x = -40
    obj.direction = -1
  elseif type_id == M.OBJ_ZINGER then
    obj.width = 20; obj.height = 20
    obj.vel_x = 30
    obj.patrol_min = params.patrol_min or (x - 80)
    obj.patrol_max = params.patrol_max or (x + 80)
  elseif type_id == M.OBJ_KRUSHA then
    obj.width = 28; obj.height = 36
    obj.vel_x = -25
    obj.direction = -1
    obj.hp = 2
  elseif type_id == M.OBJ_BARREL then
    obj.width = 20; obj.height = 24
  elseif type_id == M.OBJ_RAMBI then
    obj.width = 28; obj.height = 28
  elseif type_id == M.OBJ_ENGUARDE then
    obj.width = 24; obj.height = 20
  elseif type_id == M.OBJ_FLITTER then
    obj.width = 18; obj.height = 16
    obj.vel_x = 25
    obj.direction = 1
    obj.patrol_min = params.patrol_min or (x - 64)
    obj.patrol_max = params.patrol_max or (x + 64)
  elseif type_id == M.OBJ_KLAMP then
    obj.width = 24; obj.height = 20
    obj.vel_x = -30
    obj.direction = -1
  elseif type_id == M.OBJ_KLOBBER then
    obj.width = 28; obj.height = 36
    obj.vel_x = -20
    obj.direction = -1
    obj.throw_timer = 0
    obj.hp = 3
  elseif type_id == M.OBJ_KANNON then
    obj.width = 24; obj.height = 24
    obj.vel_x = 0
    obj.direction = -1
    obj.shoot_timer = 0
  elseif type_id == M.OBJ_MININECKY then
    obj.width = 16; obj.height = 16
    obj.vel_x = 20
    obj.direction = 1
    obj.hp = 2
    obj.patrol_min = params.patrol_min or (x - 96)
    obj.patrol_max = params.patrol_max or (x + 96)
  elseif type_id == M.OBJ_PROJECTILE then
    obj.width = 8; obj.height = 8
  elseif type_id == M.OBJ_KABOOM then
    obj.width = 16; obj.height = 16
    obj.vel_x = 0
    obj.vel_y = 0
    obj.patrol_min = params.patrol_min or (x - 120)
    obj.patrol_max = params.patrol_max or (x + 120)
    obj.hp = 1
  elseif type_id == M.OBJ_KUTLASS then
    obj.width = 22; obj.height = 28
    obj.vel_x = -30
    obj.direction = -1
    obj.hp = 1
    obj.attack_cooldown = 0
  elseif type_id == M.OBJ_KLUDGE then
    obj.width = 30; obj.height = 38
    obj.vel_x = 0
    obj.direction = -1
    obj.hp = 3
    obj.throw_timer = 0
  elseif type_id == M.OBJ_SQUITTER then
    obj.width = 24; obj.height = 20
  elseif type_id == M.OBJ_RATTLY then
    obj.width = 28; obj.height = 18
  elseif type_id == M.OBJ_SQUAWKS then
    obj.width = 22; obj.height = 20
  elseif type_id == M.OBJ_EXPRESSO then
    obj.width = 28; obj.height = 28
  elseif type_id == M.OBJ_BONUS_BARREL then
    obj.width = 20; obj.height = 24
  elseif type_id == M.OBJ_ANIMAL_CRATE then
    obj.width = 16; obj.height = 16
  elseif type_id == M.OBJ_LETTER_K or type_id == M.OBJ_LETTER_O or type_id == M.OBJ_LETTER_N or type_id == M.OBJ_LETTER_G then
    obj.width = 14; obj.height = 16
    obj.collect_radius = 24
  elseif type_id == M.OBJ_ROPE then
    obj.width = 16
    obj.height = params.height or 128
    obj.rope_top = params.top or y
    obj.rope_bottom = params.bottom or (y + obj.height)
  elseif type_id == M.OBJ_ORIGINAL_STATIC then
    obj.width = 24
    obj.height = 24
    if params.sprite == "Neek" then
      obj.source_x = x
      obj.source_neek_active = false
      obj.source_neek_supported = false
      obj.vel_x = NEEK_SOURCE_SPEED
    end
  end

  table.insert(objects, obj)
  return obj.id
end

function M.spawn_from_level(object_defs)
  for _, def in ipairs(object_defs) do
    local type_map = {
      banana = M.OBJ_BANANA,
      banana_bunch = M.OBJ_BANANA_BUNCH,
      dk_coin = M.OBJ_DK_COIN,
      life_balloon = M.OBJ_LIFE,
      kritter = M.OBJ_KRITTER,
      zinger = M.OBJ_ZINGER,
      krusha = M.OBJ_KRUSHA,
      barrel = M.OBJ_BARREL,
      rambi = M.OBJ_RAMBI,
      enguarde = M.OBJ_ENGUARDE,
      flitter = M.OBJ_FLITTER,
      klamp = M.OBJ_KLAMP,
      klobber = M.OBJ_KLOBBER,
      kannon = M.OBJ_KANNON,
      mininecky = M.OBJ_MININECKY,
      kaboom = M.OBJ_KABOOM,
      kutlass = M.OBJ_KUTLASS,
      kludge = M.OBJ_KLUDGE,
      squitter = M.OBJ_SQUITTER,
      rattly = M.OBJ_RATTLY,
      squawks = M.OBJ_SQUAWKS,
      expresso = M.OBJ_EXPRESSO,
      bonus_barrel = M.OBJ_BONUS_BARREL,
      animal_crate = M.OBJ_ANIMAL_CRATE,
      letter_k = M.OBJ_LETTER_K,
      letter_o = M.OBJ_LETTER_O,
      letter_n = M.OBJ_LETTER_N,
      letter_g = M.OBJ_LETTER_G,
      rope = M.OBJ_ROPE,
      original_static = M.OBJ_ORIGINAL_STATIC,
    }
    local type_id = type_map[def.type]
    if type_id then
      M.spawn(type_id, def.x, def.y, def.params)
    end
  end
end

function M.update(dt, camera_x, viewport_w, original_semantics)
  local time = os.clock()
  for i = #objects, 1, -1 do
    local obj = objects[i]
    if bit.band(obj.flags, M.FLAG_ACTIVE) == 0 then
      table.remove(objects, i)
    else
      M._update_object(obj, dt, time, camera_x, viewport_w, original_semantics)
    end
  end
end

function M._update_object(obj, dt, time, camera_x, viewport_w, original_semantics)
  if obj.type == M.OBJ_ORIGINAL_STATIC then
    if obj.params and obj.params.sprite == "Neek" and original_semantics
        and bit.band(obj.flags, M.FLAG_COLLECTED) == 0 then
      local visible_right = camera_x and camera_x + (viewport_w or 256)
      if visible_right and visible_right >= obj.source_x then
        obj.source_neek_active = true
      end
      if obj.source_neek_active then
        obj.source_neek_previous_x = obj.x
        obj.source_neek_previous_y = obj.y
        obj.x = obj.x + obj.vel_x * dt
        local collision = require("main.collision")
        local floor_y, supported = collision.resolve_y(
          obj.x, obj.y - TILE_SIZE, 1, obj.height, TILE_SIZE * 2)
        obj.source_neek_supported = supported == true
        if obj.source_neek_supported then obj.y = floor_y end
      end
    end

  elseif obj.type == M.OBJ_BANANA or obj.type == M.OBJ_BANANA_BUNCH then
    local float_y = math.sin(time * 2 + obj.float_offset) * 4
    obj.y = obj.y + float_y * dt
    obj.anim_timer = obj.anim_timer + dt
    if obj.anim_timer > 0.15 then
      obj.anim_frame = (obj.anim_frame + 1) % 4
      obj.anim_timer = 0
    end

  elseif obj.type == M.OBJ_DK_COIN then
    obj.anim_timer = obj.anim_timer + dt
    if obj.anim_timer > 0.2 then
      obj.anim_frame = (obj.anim_frame + 1) % 4
      obj.anim_timer = 0
    end

  elseif obj.type == M.OBJ_LIFE then
    local float_y = math.sin(time * 3 + obj.float_offset) * 3
    obj.y = obj.y + float_y * dt

  elseif obj.type == M.OBJ_LETTER_K or obj.type == M.OBJ_LETTER_O or obj.type == M.OBJ_LETTER_N or obj.type == M.OBJ_LETTER_G then
    local float_y = math.sin(time * 2.5 + obj.float_offset) * 5
    obj.y = obj.y + float_y * dt
    obj.anim_timer = obj.anim_timer + dt
    if obj.anim_timer > 0.4 then
      obj.anim_frame = (obj.anim_frame + 1) % 4
      obj.anim_timer = 0
    end

  elseif obj.type == M.OBJ_KRITTER then
    obj.anim_timer = obj.anim_timer + dt
    if obj.anim_timer > 0.2 then
      obj.anim_frame = (obj.anim_frame + 1) % 2
      obj.anim_timer = 0
    end
    local new_x = obj.x + obj.vel_x * dt
    local collision = require("main.collision")
    local check_x = new_x + obj.direction * (obj.width * 0.5 + 1)
    local foot_y = obj.y + obj.height
    local col, row = collision.world_to_tile(check_x, foot_y - 1)
    local tile = collision.get_tile(col, row)
    if tile == collision.TILE_SOLID or tile == collision.TILE_SLIP then
      obj.direction = -obj.direction
      obj.vel_x = -obj.vel_x
    else
      obj.x = new_x
    end

  elseif obj.type == M.OBJ_ZINGER then
    obj.anim_timer = obj.anim_timer + dt
    if obj.anim_timer > 0.1 then
      obj.anim_frame = (obj.anim_frame + 1) % 3
      obj.anim_timer = 0
    end
    if obj.x <= obj.patrol_min then
      obj.vel_x = 30; obj.direction = 1
    elseif obj.x >= obj.patrol_max then
      obj.vel_x = -30; obj.direction = -1
    end
    obj.x = obj.x + obj.vel_x * dt
    obj.y = obj.y + math.sin(time * 4 + obj.float_offset) * 30 * dt

  elseif obj.type == M.OBJ_KRUSHA then
    obj.anim_timer = obj.anim_timer + dt
    if obj.anim_timer > 0.3 then
      obj.anim_frame = (obj.anim_frame + 1) % 2
      obj.anim_timer = 0
    end
    local new_x = obj.x + obj.vel_x * dt
    local collision = require("main.collision")
    local check_x = new_x + obj.direction * (obj.width * 0.5 + 1)
    local foot_y = obj.y + obj.height
    local col, row = collision.world_to_tile(check_x, foot_y - 1)
    local tile = collision.get_tile(col, row)
    if tile == collision.TILE_SOLID or tile == collision.TILE_SLIP then
      obj.direction = -obj.direction
      obj.vel_x = -obj.vel_x
    else
      obj.x = new_x
    end

  elseif obj.type == M.OBJ_BARREL then
    obj.barrel_angle = obj.barrel_angle or 3
    local player_mod = require("main.player")
    if player_mod.state == player_mod.STATE.BARREL then
      obj.barrel_angle = player_mod.barrel_angle
    end

  elseif obj.type == M.OBJ_FLITTER then
    obj.anim_timer = obj.anim_timer + dt
    if obj.anim_timer > 0.12 then
      obj.anim_frame = (obj.anim_frame + 1) % 2
      obj.anim_timer = 0
    end
    if obj.x <= obj.patrol_min then
      obj.vel_x = 25; obj.direction = 1
    elseif obj.x >= obj.patrol_max then
      obj.vel_x = -25; obj.direction = -1
    end
    obj.x = obj.x + obj.vel_x * dt
    obj.y = obj.y + math.sin(time * 3 + obj.float_offset) * 20 * dt

  elseif obj.type == M.OBJ_KLAMP then
    obj.anim_timer = obj.anim_timer + dt
    if obj.anim_timer > 0.25 then
      obj.anim_frame = (obj.anim_frame + 1) % 2
      obj.anim_timer = 0
    end
    local new_x = obj.x + obj.vel_x * dt
    local collision = require("main.collision")
    local check_x = new_x + obj.direction * (obj.width * 0.5 + 1)
    local foot_y = obj.y + obj.height
    local col, row = collision.world_to_tile(check_x, foot_y - 1)
    local tile = collision.get_tile(col, row)
    if tile == collision.TILE_SOLID or tile == collision.TILE_SLIP then
      obj.direction = -obj.direction
      obj.vel_x = -obj.vel_x
    else
      obj.x = new_x
    end

  elseif obj.type == M.OBJ_KLOBBER then
    obj.anim_timer = obj.anim_timer + dt
    obj.throw_timer = obj.throw_timer + dt
    if obj.throw_timer > 2.5 then
      obj.throw_timer = 0
      local dir = obj.direction
      local cx = obj.x + dir * 20
      M.spawn(M.OBJ_PROJECTILE, cx, obj.y - 4, {
        vel_x = 80 * dir,
        vel_y = -180,
        gravity = true,
      })
    end
    if obj.anim_timer > 0.3 then
      obj.anim_frame = (obj.anim_frame + 1) % 2
      obj.anim_timer = 0
    end
    local new_x = obj.x + obj.vel_x * dt
    local collision = require("main.collision")
    local check_x = new_x + obj.direction * (obj.width * 0.5 + 1)
    local foot_y = obj.y + obj.height
    local col, row = collision.world_to_tile(check_x, foot_y - 1)
    local tile = collision.get_tile(col, row)
    if tile == collision.TILE_SOLID or tile == collision.TILE_SLIP then
      obj.direction = -obj.direction
      obj.vel_x = -obj.vel_x
    else
      obj.x = new_x
    end

  elseif obj.type == M.OBJ_KANNON then
    obj.anim_timer = obj.anim_timer + dt
    obj.shoot_timer = obj.shoot_timer + dt
    if obj.anim_timer > 0.2 then
      obj.anim_frame = (obj.anim_frame + 1) % 2
      obj.anim_timer = 0
    end
    if obj.shoot_timer > 2.0 then
      obj.shoot_timer = 0
      local dir = obj.direction
      M.spawn(M.OBJ_PROJECTILE, obj.x + dir * 16, obj.y, {
        vel_x = 160 * dir,
        vel_y = 0,
        gravity = false,
      })
    end

  elseif obj.type == M.OBJ_MININECKY then
    obj.anim_timer = obj.anim_timer + dt
    if obj.anim_timer > 0.15 then
      obj.anim_frame = (obj.anim_frame + 1) % 3
      obj.anim_timer = 0
    end
    if obj.x <= obj.patrol_min then
      obj.vel_x = 20; obj.direction = 1
    elseif obj.x >= obj.patrol_max then
      obj.vel_x = -20; obj.direction = -1
    end
    obj.x = obj.x + obj.vel_x * dt
    obj.y = obj.y + math.sin(time * 2.5 + obj.float_offset) * 40 * dt

  elseif obj.type == M.OBJ_PROJECTILE then
    if obj.params and obj.params.gravity then
      obj.vel_y = obj.vel_y + 500 * dt
    end
    obj.x = obj.x + obj.vel_x * dt
    obj.y = obj.y + obj.vel_y * dt
    local collision = require("main.collision")
    local col, row = collision.world_to_tile(obj.x, obj.y)
    local tile = collision.get_tile(col, row)
    if tile == collision.TILE_SOLID or tile == collision.TILE_SLIP then
      obj.flags = bit.band(obj.flags, bit.bnot(M.FLAG_ACTIVE))
    end
    local w, h = 1280, 720
    if obj.x < -64 or obj.x > w + 64 or obj.y < -64 or obj.y > h + 64 then
      obj.flags = bit.band(obj.flags, bit.bnot(M.FLAG_ACTIVE))
    end
  end

  if bit.band(obj.flags, M.FLAG_COLLECTED) ~= 0 then
    obj.timer = obj.timer + dt
    if obj.timer > 0.3 then
      obj.flags = bit.band(obj.flags, bit.bnot(M.FLAG_ACTIVE))
    end
  end
end

local function aabb(ax, ay, aw, ah, bx, by, bw, bh)
  return ax < bx + bw and ax + aw > bx and ay < by + bh and ay + ah > by
end

function M.get_rope_at(px, py, pw, ph)
  for _, obj in ipairs(objects) do
    if obj.type == M.OBJ_ROPE and bit.band(obj.flags, M.FLAG_ACTIVE) ~= 0 then
      local ox = obj.x - obj.width * 0.5
      local oy = obj.rope_top or obj.y
      local oh = (obj.rope_bottom or (obj.y + obj.height)) - oy
      if aabb(px, py, pw, ph, ox, oy, obj.width, oh) then
        return obj
      end
    end
  end
  return nil
end

function M.check_player_collision(px, py, pw, ph)
  local events = {}
  local previous_player_bottom = last_neek_player_bottom
  local player_bottom = py + ph
  for _, obj in ipairs(objects) do
    if bit.band(obj.flags, M.FLAG_ACTIVE) ~= 0 and bit.band(obj.flags, M.FLAG_COLLECTED) == 0 then
      if obj.type == M.OBJ_ORIGINAL_STATIC then
        local sprite = obj.params and obj.params.sprite
        -- Only Neek has source-backed collision/stomp; other original_static remain passive.
        if sprite == "Neek" and neek_top_crossing(
            obj, px, pw, player_bottom, previous_player_bottom) then
          obj.x = obj.source_neek_previous_x or obj.x
          table.insert(events, { type = "enemy_hit", object = obj })
        end
      else
        local ox = obj.x - obj.width * 0.5
        local oy = obj.y
        if aabb(px, py, pw, ph, ox, oy, obj.width, obj.height) then
          if obj.type == M.OBJ_LETTER_K then
            obj.flags = bit.bor(obj.flags, M.FLAG_COLLECTED)
            table.insert(events, { type = "collect_letter", letter = "K" })
          elseif obj.type == M.OBJ_LETTER_O then
            obj.flags = bit.bor(obj.flags, M.FLAG_COLLECTED)
            table.insert(events, { type = "collect_letter", letter = "O" })
          elseif obj.type == M.OBJ_LETTER_N then
            obj.flags = bit.bor(obj.flags, M.FLAG_COLLECTED)
            table.insert(events, { type = "collect_letter", letter = "N" })
          elseif obj.type == M.OBJ_LETTER_G then
            obj.flags = bit.bor(obj.flags, M.FLAG_COLLECTED)
            table.insert(events, { type = "collect_letter", letter = "G" })
          elseif obj.type == M.OBJ_BANANA then
            obj.flags = bit.bor(obj.flags, M.FLAG_COLLECTED)
            table.insert(events, { type = "collect_banana", count = 1 })
          elseif obj.type == M.OBJ_BANANA_BUNCH then
            obj.flags = bit.bor(obj.flags, M.FLAG_COLLECTED)
            table.insert(events, { type = "collect_banana", count = 10 })
          elseif obj.type == M.OBJ_DK_COIN then
            obj.flags = bit.bor(obj.flags, M.FLAG_COLLECTED)
            table.insert(events, { type = "collect_dk_coin" })
          elseif obj.type == M.OBJ_LIFE then
            obj.flags = bit.bor(obj.flags, M.FLAG_COLLECTED)
            table.insert(events, { type = "collect_life" })
          elseif obj.type == M.OBJ_KRITTER or obj.type == M.OBJ_ZINGER or obj.type == M.OBJ_KRUSHA then
            table.insert(events, { type = "enemy_hit", object = obj })
          elseif obj.type == M.OBJ_BARREL then
            table.insert(events, { type = "barrel", object = obj })
          elseif obj.type == M.OBJ_RAMBI then
            table.insert(events, { type = "mount_rambi", object = obj })
          elseif obj.type == M.OBJ_ENGUARDE then
            table.insert(events, { type = "mount_enguarde", object = obj })
          elseif obj.type == M.OBJ_FLITTER then
            table.insert(events, { type = "enemy_hit", object = obj })
          elseif obj.type == M.OBJ_KLAMP then
            table.insert(events, { type = "enemy_hit", object = obj })
          elseif obj.type == M.OBJ_KLOBBER then
            table.insert(events, { type = "enemy_hit", object = obj })
          elseif obj.type == M.OBJ_KANNON then
            table.insert(events, { type = "enemy_hit", object = obj })
          elseif obj.type == M.OBJ_MININECKY then
            table.insert(events, { type = "enemy_hit", object = obj })
          end  -- closes the if aabb(...) then ... object type if
        end  -- closes the if aabb(...) then
      end  -- closes the if obj.type == M.OBJ_ORIGINAL_STATIC then ... else ... end
  end  -- closes the flags check
  end  -- closes the for loop
  last_neek_player_bottom = player_bottom
  return events
end

function M.stomp_enemy(obj)
  if obj.type == M.OBJ_KLAMP then
    return "invulnerable"
  end
  if obj.type == M.OBJ_ORIGINAL_STATIC then
    local sprite = obj.params and obj.params.sprite
    -- Neek: source-backed stomp with original $F7C8 bounce velocity.
    if sprite == "Neek" then
      obj.flags = bit.bor(obj.flags, M.FLAG_COLLECTED)
      obj.timer = 0
      return "kill", "neek_bounce"
    end
    -- Other original sprites remain unhandled until their native scripts are traced.
    return "none"
  end
  if obj.type == M.OBJ_KABOOM then
    obj.flags = bit.bor(obj.flags, M.FLAG_COLLECTED)
    obj.timer = 0
    return "kill"
  end
  if obj.type == M.OBJ_KRUSHA or obj.type == M.OBJ_MININECKY then
    obj.hp = obj.hp - 1
    if obj.hp > 0 then
      return "hit"
    end
  end
  if obj.type == M.OBJ_KLOBBER then
    obj.hp = obj.hp - 1
    if obj.hp > 0 then
      obj.throw_timer = 0
      return "hit"
    end
  end
  if obj.type == M.OBJ_KUTLASS then
    obj.flags = bit.bor(obj.flags, M.FLAG_COLLECTED)
    obj.timer = 0
    return "kill"
  end
  if obj.type == M.OBJ_KLUDGE then
    obj.hp = obj.hp - 1
    if obj.hp > 0 then
      obj.throw_timer = 0
      return "hit"
    end
  end
  obj.flags = bit.bor(obj.flags, M.FLAG_COLLECTED)
  obj.timer = 0
  return "kill"
end

function M.get_objects()
  return objects
end

function M.clear()
  objects = {}
  next_id = 1
  last_neek_player_bottom = nil
end

return M
