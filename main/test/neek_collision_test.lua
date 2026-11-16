-- Focused test for Neek collision/stomp vs other original_static objects
local objects = require("main.objects")
local original_motion = require("main.original_motion")
local collision = require("main.collision")
local pirate_panic = require("data.levels.level_1_1")
local bit = require("bit")

local M = {}

local function has_neek_hit(events, neek)
  for _, event in ipairs(events) do
    if event.type == "enemy_hit" and event.object == neek then return true end
  end
  return false
end

function M.test_neek_collision_and_stomp()
  objects.clear()
  collision.load(pirate_panic.tiles, pirate_panic.width, pirate_panic.height)
  collision.load_original_surfaces(pirate_panic.flat_surfaces)

  -- Spawn a Neek at world x=1024, feet_y=288 (from pirate_panic_level.lua line 45)
  local neek_id = objects.spawn(objects.OBJ_ORIGINAL_STATIC, 1024, 288 - 24, {
    script = 1, sprite = "Neek", param = 0
  })
  local neek = objects.get_objects()[1]
  assert(neek.params.sprite == "Neek", "Neek sprite param not preserved")

  -- Spawn a Klomp at x=1248, feet_y=209 (line 48)
  local klomp_id = objects.spawn(objects.OBJ_ORIGINAL_STATIC, 1248, 209 - 24, {
    script = 1, sprite = "Klomp", param = 0
  })
  local klomp = objects.get_objects()[2]
  assert(klomp.params.sprite == "Klomp", "Klomp sprite param not preserved")

  -- Spawn a DKBarrel (other original_static)
  local barrel_id = objects.spawn(objects.OBJ_ORIGINAL_STATIC, 1500, 200 - 24, {
    script = 1, sprite = "DKBarrel", param = 0
  })
  local barrel = objects.get_objects()[3]
  assert(barrel.params.sprite == "DKBarrel", "DKBarrel sprite param not preserved")

  -- Source sprite enters the 256px viewport at the right edge and walks left
  -- at one 8.8 pixel per frame; frame 512 camera evidence starts Neek x=752.
  objects.update(1 / 60, 768, 256, false)
  assert(not neek.source_neek_active and neek.x == 1024,
         "source Neek motion must stay gated outside original semantics")
  objects.update(1 / 60, 768 - 1, 256, true)
  assert(not neek.source_neek_active and neek.x == 1024,
         "Neek must stay dormant before entering the source viewport")
  local events = objects.check_player_collision(1012, 264, 24, 24)
  assert(#events == 0, "a not-yet-streamed Neek must not collide before viewport entry")
  objects.update(1 / 60, 768, 256, true)
  assert(neek.source_neek_active and neek.x == 1023,
          "Neek must begin source-paced movement at viewport entry")
  for _ = 1, 52 do objects.update(1 / 60, 768, 256, true) end
  assert(math.floor(neek.x + 0.5) == 971 and neek.y + neek.height == 315,
         string.format("Neek source floor x=971 mismatch: x=%.3f feet_y=%.3f supported=%s",
                       neek.x, neek.y + neek.height, tostring(neek.source_neek_supported)))
  for _ = 1, 6 do objects.update(1 / 60, 768, 256, true) end
  assert(math.floor(neek.x + 0.5) == 965 and neek.y + neek.height == 318,
         string.format("Neek source floor x=965 mismatch: x=%.3f feet_y=%.3f supported=%s",
                       neek.x, neek.y + neek.height, tostring(neek.source_neek_supported)))

  -- Side and ascending overlaps cannot masquerade as source Neek top contacts.
  local px, pw, ph = neek.x + neek.width * 0.5, 24, 24
  local py = neek.y - 20
  events = objects.check_player_collision(px, py, pw, ph) -- just outside right edge
  events = objects.check_player_collision(px - 1, py, pw, ph) -- side overlap
  assert(not has_neek_hit(events, neek), "Neek side overlap must not register a top hit")
  events = objects.check_player_collision(neek.x - 12, neek.y - 19, pw, ph)
  events = objects.check_player_collision(neek.x - 12, neek.y - 22, pw, ph)
  assert(not has_neek_hit(events, neek), "ascending Neek overlap must not register a top hit")

  -- Contact uses the source position from before its one-pixel movement that tick.
  local source_impact_x = neek.x
  local edge_px = source_impact_x + neek.width * 0.5 - 0.5
  py = neek.y - ph - 1
  events = objects.check_player_collision(edge_px, py, 16, ph)
  assert(not has_neek_hit(events, neek), "Neek must not hit before the top crossing")
  objects.update(1 / 60, 768, 256, true)
  events = objects.check_player_collision(edge_px, neek.y - ph + 2, 16, ph)
  assert(has_neek_hit(events, neek), "descending top crossing must register Neek hit")
  assert(math.abs(neek.x - source_impact_x) < 0.001,
         "Neek must keep its source X on the impact tick")

  -- Other original sprites remain passive until their own source handlers are ported.
  px, py = 1236, 185  -- Klomp: x=1248, y=185 (209-24), hitbox ox=1236
  events = objects.check_player_collision(px, py, pw, ph)

  local klomp_hit = false
  for _, ev in ipairs(events) do
    if ev.type == "enemy_hit" and ev.object == klomp then
      klomp_hit = true
    end
  end
  assert(not klomp_hit, "Klomp should NOT register enemy_hit collision")

  -- Player hitbox at DKBarrel position (should NOT collide, only skip event)
  px, py = 1488, 176  -- DKBarrel: x=1500, y=176 (200-24), hitbox ox=1488
  events = objects.check_player_collision(px, py, pw, ph)

  local barrel_hit = false
  for _, ev in ipairs(events) do
    if ev.type == "enemy_hit" and ev.object == barrel then
      barrel_hit = true
    end
  end
  assert(not barrel_hit, "DKBarrel should NOT register enemy_hit collision")

  -- Neek's source handler returns the dedicated original-velocity bounce.
  local result, bounce_type = objects.stomp_enemy(neek)
  assert(result == "kill", "Neek stomp should return kill")
  assert(bounce_type == "neek_bounce", "Neek stomp should return neek_bounce")
  assert(bit.band(neek.flags, objects.FLAG_COLLECTED) ~= 0, "Neek should be marked collected")

  -- Unported originals remain untouched by this narrowly scoped Neek handler.
  result, bounce_type = objects.stomp_enemy(klomp)
  assert(result == "none", "Klomp stomp should return none")
  assert(bounce_type == nil, "Klomp stomp should not return bounce_type")

  -- Test stomp_enemy: DKBarrel should return "none"
  result, bounce_type = objects.stomp_enemy(barrel)
  assert(result == "none", "DKBarrel stomp should return none")

  -- Verify original_motion.jump_velocity() matches source $F7C8 (-2104 * 60 / 256)
  local expected_vy = -2104 * 60 / 256  -- ~ -493.125 px/s
  assert(math.abs(original_motion.jump_velocity() - expected_vy) < 0.01,
    "jump_velocity must match source $F7C8 equivalent")

  objects.clear()
  collision.clear()
  return true
end

function M.test_neek_bounce_velocity_applied()
  -- This tests that player.bounce() accepts the velocity parameter
  local player = require("main.player")
  player.set_objects(objects)
  objects.clear()

  -- Set up minimal player state
  player.set_z(100, 100)
  player.vel_y = 100
  player.grounded = true
  player.state = player.STATE.RUN

  -- Call bounce with Neek velocity
  local neek_vy = original_motion.jump_velocity()
  player.bounce(neek_vy, 2)

  assert(math.abs(player.vel_y - neek_vy) < 0.01, "player.bounce(vel_y) should set exact velocity")
  assert(player.grounded == false, "player.bounce should set grounded=false")
  assert(player.state == player.STATE.FALL, "player.bounce should set state=FALL")
  assert(player.hitpause_frames == 2, "source stomp should pause two updates after contact")
  local paused_y = player.pos_y
  player.update(1 / 60)
  assert(player.pos_y == paused_y and player.hitpause_frames == 1,
         "source hitpause must hold player position while the timer remains")

  -- Default bounce (backward compat) should still work
  player.bounce()
  assert(player.vel_y == -350, "player.bounce() default should be -350")

  objects.clear()
  return true
end

function M.run()
  M.test_neek_collision_and_stomp()
  M.test_neek_bounce_velocity_applied()
  print("All Neek collision/stomp tests passed")
  return true
end

return M
