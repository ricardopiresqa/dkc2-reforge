local M = {}

-- Shared states
M.STATE_INTRO = 1
M.STATE_ATTACK = 2
M.STATE_ATTACK2 = 3
M.STATE_ENRAGED = 4
M.STATE_DEFEATED = 5
M.STATE_IDLE = 6
M.STATE_TRANSITION = 7
M.STATE_TELEPORT = 8

-- Boss types
M.BOSS_KROW = 1
M.BOSS_KLEAVER = 2
M.BOSS_KING_ZING = 3
M.BOSS_KREEP = 4
M.BOSS_KROOL_P1 = 5
M.BOSS_KROOL_P2 = 6

-- Shared helpers
local function move_toward(b, target_x, target_y, speed, dt)
  local dx = target_x - b.x
  local dy = target_y - b.y
  local dist = math.sqrt(dx * dx + dy * dy)
  if dist > 4 then
    local step = speed * dt
    b.x = b.x + (dx / dist) * step
    b.y = b.y + (dy / dist) * step
    return false
  end
  b.x = target_x
  b.y = target_y
  return true
end

local function set_defaults(b, x, y)
  b.x = x or 160
  b.y = y or 320
  b.start_x = b.x
  b.start_y = b.y
  b.hit_flash_timer = 0
  b.defeated_timer = 0
  b.spawned_reward = false
  b.alive = true
  b.enraged = false
  b.timer = 0
  b.projectiles = nil
end

local function update_hit_flash(b, dt)
  if b.hit_flash_timer > 0 then
    b.hit_flash_timer = b.hit_flash_timer - dt
  end
end

local function spawn_projectile(b, proj_list, px, py, vx, vy, w, h, dmg_type)
  proj_list = proj_list or {}
  proj_list[#proj_list + 1] = {
    x = px, y = py, vx = vx or 0, vy = vy or 0,
    w = w or 8, h = h or 8,
    alive = true, dmg_type = dmg_type or "contact",
  }
  return proj_list
end

local function cleanup_projectiles(proj_list, ground_y)
  if not proj_list then return proj_list end
  for i = #proj_list, 1, -1 do
    local p = proj_list[i]
    if not p.alive then
      table.remove(proj_list, i)
    else
      if p.vy then p.vy = p.vy + 400 * dt end
      if p.vx then p.x = p.x + p.vx * dt end
      if p.vy then p.y = p.y + p.vy * dt end
      if ground_y and p.y >= ground_y then
        p.alive = false
      end
    end
  end
  return proj_list
end

function M.get_projectile_hitboxes(boss)
  local boxes = {}
  if not boss or not boss.projectiles then return boxes end
  for _, p in ipairs(boss.projectiles) do
    if p.alive then
      boxes[#boxes + 1] = { x = p.x - p.w/2, y = p.y - p.h/2, w = p.w, h = p.h }
    end
  end
  return boxes
end

--[[ KROW (existing, refactored) ]]
local function new_krow()
  local b = {
    type = M.BOSS_KROW,
    hp = 3, max_hp = 3,
    state = M.STATE_INTRO,
    timer = 0, swoop_count = 0, egg_count = 0,
    x = 160, y = 320, start_y = 320,
    target_x = 160, target_y = 100,
    speed = 120, eggs_to_drop = 4,
    swoops_before_eggs = 2, swoops_done = 0,
    hit_flash_timer = 0, defeated_timer = 0,
    spawned_reward = false, alive = true, enraged = false,
  }
  return b
end

--[[ KLEAVER: plane that dive-bombs and drops bombs, 3 HP ]]
-- States: INTRO → ATTACK (dive) → ATTACK2 (bombs) → ENRAGED → DEFEATED
local function new_kleaver()
  local b = {
    type = M.BOSS_KLEAVER,
    hp = 3, max_hp = 3,
    state = M.STATE_INTRO,
    timer = 0, dive_count = 0, bomb_count = 0,
    x = 300, y = 60, start_y = 60,
    target_x = 160, target_y = 60,
    speed = 200, dive_speed = 350,
    dives_before_bombs = 2, dives_done = 0,
    bombs_to_drop = 4, bombs_dropped = 0,
    bomb_interval = 0,
    hit_flash_timer = 0, defeated_timer = 0,
    spawned_reward = false, alive = true, enraged = false,
    projectiles = {},
    phase = 1, -- 1=dive, 2=bomb
  }
  return b
end

local function update_kleaver_intro(b, dt)
  b.timer = b.timer + dt
  if b.timer > 1.0 then
    b.state = M.STATE_ATTACK
    b.timer = 0
    b.dives_done = 0
    b.target_x = 160
    b.target_y = 300
    b.speed = b.dive_speed
  end
end

local function update_kleaver_dive(b, dt, player_x)
  if b.timer == 0 then
    b.target_x = player_x
    b.target_y = 300
    b.speed = b.dive_speed
  end
  if not move_toward(b, b.target_x, b.target_y, b.speed, dt) then return end
  -- Reached dive target, ascend
  b.target_x = math.random(80, 240)
  b.target_y = 60
  b.speed = 150
  if move_toward(b, b.target_x, b.target_y, b.speed, dt) then
    b.dives_done = b.dives_done + 1
    if b.dives_done >= b.dives_before_bombs or (b.enraged and b.dives_done >= 1) then
      b.state = M.STATE_ATTACK2
      b.timer = 0
      b.bombs_dropped = 0
      b.bomb_interval = 0
    else
      b.timer = 0
    end
  end
end

local function update_kleaver_bombs(b, dt, player_x)
  b.timer = b.timer + dt
  b.bomb_interval = b.bomb_interval + dt
  local interval = b.enraged and 0.25 or 0.5
  local max_bombs = b.enraged and 8 or 4

  if b.bomb_interval >= interval and b.bombs_dropped < max_bombs then
    b.bombs_dropped = b.bombs_dropped + 1
    b.bomb_interval = 0
    -- Move slightly for each bomb
    b.x = b.x + math.random(-30, 30)
    b.y = 60
    b.projectiles = spawn_projectile(b, b.projectiles,
      b.x + math.random(-20, 20), b.y + 20,
      math.random(-30, 30) / 10, 200 + math.random(50),
      10, 10, "bomb")
  end

  if b.bombs_dropped >= max_bombs then
    b.dives_done = 0
    b.state = M.STATE_ATTACK
    b.timer = 0
  end
end

local function update_kleaver_defeated(b, dt, spawn_object_fn, lw, lh)
  b.defeated_timer = b.defeated_timer + dt
  b.y = b.y + 80 * dt
  local exit_floor = (lh or 24) * 16
  if b.y > exit_floor + 64 then b.alive = false end
  if not b.spawned_reward and b.defeated_timer > 0.5 then
    b.spawned_reward = true
    if spawn_object_fn then
      spawn_object_fn(8, math.floor((lw or 20) / 2), math.floor((lh or 24) / 2))
    end
  end
end

--[[ KING ZING: giant bee, circles + spawns zinger minions, 3 HP ]]
local function new_king_zing()
  local b = {
    type = M.BOSS_KING_ZING,
    hp = 3, max_hp = 3,
    state = M.STATE_INTRO,
    timer = 0, orbit_angle = 0, orbit_radius = 100,
    x = 160, y = 160, center_x = 160, center_y = 160,
    speed = 80, spawn_interval = 0,
    zingers_spawned = 0, max_zingers = 4,
    hit_flash_timer = 0, defeated_timer = 0,
    spawned_reward = false, alive = true, enraged = false,
    projectiles = {},
    zinger_list = {},
  }
  return b
end

local function update_zing_intro(b, dt)
  b.timer = b.timer + dt
  b.orbit_angle = b.orbit_angle + dt * 1.5
  b.x = b.center_x + math.cos(b.orbit_angle) * b.orbit_radius
  b.y = b.center_y + math.sin(b.orbit_angle) * b.orbit_radius * 0.6
  if b.timer > 2.0 then
    b.state = M.STATE_ATTACK
    b.timer = 0
  end
end

local function spawn_zinger_minion(b, spawn_object_fn)
  if not spawn_object_fn then return end
  local angle = math.random() * math.pi * 2
  local dist = 60 + math.random(40)
  local zx = b.x + math.cos(angle) * dist
  local zy = b.y + math.sin(angle) * dist
  local zinger = spawn_object_fn(3, math.floor(zx / 16), math.floor(zy / 16))
  if zinger then
    zinger.params = { patrol_min = zx - 40, patrol_max = zx + 40 }
    b.zinger_list = b.zinger_list or {}
    b.zinger_list[#b.zinger_list + 1] = zinger
  end
end

local function update_zing_attack(b, dt, spawn_object_fn)
  b.timer = b.timer + dt
  local orbit_speed = b.enraged and 2.5 or 1.5
  b.orbit_angle = b.orbit_angle + dt * orbit_speed
  b.orbit_radius = b.enraged and 80 or 100
  b.x = b.center_x + math.cos(b.orbit_angle) * b.orbit_radius
  b.y = b.center_y + math.sin(b.orbit_angle) * b.orbit_radius * 0.6

  b.spawn_interval = b.spawn_interval + dt
  local interval = b.enraged and 1.0 or 2.0
  if b.spawn_interval >= interval and b.zingers_spawned < (b.enraged and 8 or 4) then
    b.zingers_spawned = b.zingers_spawned + 1
    b.spawn_interval = 0
    spawn_zinger_minion(b, spawn_object_fn)
  end
end

local function update_zing_defeated(b, dt, spawn_object_fn, lw, lh)
  b.defeated_timer = b.defeated_timer + dt
  b.y = b.y + 60 * dt
  local exit_floor = (lh or 24) * 16
  if b.y > exit_floor + 64 then b.alive = false end
  if not b.spawned_reward and b.defeated_timer > 0.5 then
    b.spawned_reward = true
    if spawn_object_fn then
      spawn_object_fn(8, math.floor((lw or 20) / 2), math.floor((lh or 24) / 2))
    end
  end
end

--[[ KREEP: ghost that teleports + summons souls, 3 phases, 3 HP ]]
local function new_kreep()
  local b = {
    type = M.BOSS_KREEP,
    hp = 3, max_hp = 3,
    state = M.STATE_INTRO,
    timer = 0, teleport_timer = 0,
    x = 160, y = 240, start_x = 160, start_y = 240,
    teleport_positions = {
      { x = 80, y = 160 }, { x = 240, y = 160 },
      { x = 160, y = 240 }, { x = 80, y = 300 },
      { x = 240, y = 300 }, { x = 160, y = 80 },
    },
    current_tp = 1,
    soul_count = 0, max_souls = 3,
    hit_flash_timer = 0, defeated_timer = 0,
    spawned_reward = false, alive = true, enraged = false,
    projectiles = {},
    visible = true,
  }
  return b
end

local function update_kreep_intro(b, dt)
  b.timer = b.timer + dt
  -- Appear gradually
  if b.timer > 1.5 then
    b.state = M.STATE_ATTACK
    b.timer = 0
    b.teleport_timer = 0
  end
end

local function update_kreep_attack(b, dt, spawn_object_fn)
  b.timer = b.timer + dt
  b.teleport_timer = b.teleport_timer + dt

  local teleport_interval = b.enraged and 1.0 or 2.0
  if b.teleport_timer >= teleport_interval then
    b.teleport_timer = 0
    b.current_tp = (b.current_tp % #b.teleport_positions) + 1
    local tp = b.teleport_positions[b.current_tp]
    b.x = tp.x
    b.y = tp.y
    b.visible = true

    -- Spawn soul projectiles
    if b.soul_count < (b.enraged and 6 or 3) then
      b.soul_count = b.soul_count + 1
      b.projectiles = spawn_projectile(b, b.projectiles,
        b.x, b.y,
        math.random(-80, 80) / 10, 100 + math.random(50),
        8, 8, "soul")
    end
  end

  -- Phase 3: also spawn enemies
  if b.hp <= 1 and spawn_object_fn then
    if b.timer > 5.0 then
      b.timer = 0
      spawn_object_fn(5, math.floor(b.x / 16) + math.random(-2, 2), math.floor(b.y / 16) + 2)
    end
  end
end

local function update_kreep_defeated(b, dt, spawn_object_fn, lw, lh)
  b.defeated_timer = b.defeated_timer + dt
  b.y = b.y + 40 * dt
  local exit_floor = (lh or 24) * 16
  if b.y > exit_floor + 64 then b.alive = false end
  if not b.spawned_reward and b.defeated_timer > 0.5 then
    b.spawned_reward = true
    if spawn_object_fn then
      spawn_object_fn(8, math.floor((lw or 20) / 2), math.floor((lh or 24) / 2))
    end
  end
end

--[[ K. ROOL P1: 4 disguises (cowboy/magician/pirate), 4 HP ]]
-- Each disguise is a phase with different attack pattern
local DISGUISE_COWBOY = 1
local DISGUISE_MAGICIAN = 2
local DISGUISE_PIRATE = 3
local DISGUISE_KRUSHER = 4

local function new_krool_p1()
  local b = {
    type = M.BOSS_KROOL_P1,
    hp = 4, max_hp = 4,
    state = M.STATE_INTRO,
    disguise = DISGUISE_COWBOY,
    timer = 0, attack_timer = 0,
    x = 160, y = 160, start_x = 160, start_y = 160,
    target_x = 160, target_y = 160,
    speed = 180, jump_timer = 0,
    crown_projectiles = 0, max_crowns = 3,
    hit_flash_timer = 0, defeated_timer = 0,
    spawned_reward = false, alive = true, enraged = false,
    projectiles = {},
    disguise_changed = false,
  }
  return b
end

local function update_krool_intro(b, dt)
  b.timer = b.timer + dt
  if b.timer > 2.0 then
    b.state = M.STATE_ATTACK
    b.timer = 0
    b.disguise = DISGUISE_COWBOY
    b.disguise_changed = false
  end
end

local function update_krool_cowboy(b, dt, player_x, player_y)
  -- Cowboy: shoots crown projectiles in arc
  b.attack_timer = b.attack_timer + dt
  -- Bob up and down
  b.y = b.start_y + math.sin(b.timer * 3) * 20

  if b.attack_timer > 1.0 and b.crown_projectiles < b.max_crowns then
    b.crown_projectiles = b.crown_projectiles + 1
    b.attack_timer = 0
    local dx = (player_x - b.x) / 200
    local dy = (player_y - b.y) / 200
    b.projectiles = spawn_projectile(b, b.projectiles,
      b.x, b.y - 20,
      dx * 150, dy * 150,
      12, 12, "crown")
  end

  if b.crown_projectiles >= b.max_crowns and (#b.projectiles or 0) == 0 then
    b.state = M.STATE_TRANSITION
    b.timer = 0
  end
end

local function update_krool_magician(b, dt, player_x, player_y)
  -- Magician: teleports and drops energy orbs
  b.attack_timer = b.attack_timer + dt
  if b.attack_timer > 1.5 then
    b.attack_timer = 0
    b.x = math.random(60, 260)
    b.y = math.random(80, 200)
    -- Drop orb at player position
    b.projectiles = spawn_projectile(b, b.projectiles,
      player_x + math.random(-30, 30), 40,
      math.random(-20, 20) / 10, 150 + math.random(50),
      10, 10, "orb")
  end

  if b.timer >= 8.0 then
    b.state = M.STATE_TRANSITION
    b.timer = 0
  end
  b.timer = b.timer + dt
end

local function update_krool_pirate(b, dt, player_x)
  -- Pirate: charges across arena
  b.attack_timer = b.attack_timer + dt
  if b.attack_timer > 0.5 then
    -- Set charge target
    if b.target_x == b.x then
      b.target_x = player_x > b.x and 300 or 20
      b.target_y = b.start_y
    end
    if move_toward(b, b.target_x, b.target_y, 350, dt) then
      b.target_x = b.x
      b.attack_timer = 2.0
    end
  end

  if b.timer >= 8.0 then
    b.state = M.STATE_TRANSITION
    b.timer = 0
  end
  b.timer = b.timer + dt
end

local function update_krool_krusher(b, dt, player_x, ground_y)
  -- Krusher: jumps and slams
  b.attack_timer = b.attack_timer + dt
  if b.attack_timer > 2.0 then
    b.attack_timer = 0
    b.target_x = player_x
    b.target_y = ground_y - 32
    b.speed = 300
  end
  if not move_toward(b, b.target_x, b.target_y, b.speed, dt) then
    -- Jump arc
    b.y = b.y - 200 * dt
  end
end

local function update_krool_transition(b, dt)
  b.timer = b.timer + dt
  if b.timer > 1.0 then
    b.timer = 0
    b.attack_timer = 0
    b.crown_projectiles = 0
    b.projectiles = {}
    b.disguise = b.disguise + 1
    if b.disguise > DISGUISE_KRUSHER then
      b.disguise = DISGUISE_COWBOY
    end
    b.state = M.STATE_ATTACK
  end
end

local function update_krool_defeated(b, dt, spawn_object_fn, lw, lh)
  b.defeated_timer = b.defeated_timer + dt
  b.y = b.y + 50 * dt
  local exit_floor = (lh or 24) * 16
  if b.y > exit_floor + 64 then b.alive = false end
  if not b.spawned_reward and b.defeated_timer > 0.8 then
    b.spawned_reward = true
    if spawn_object_fn then
      spawn_object_fn(8, math.floor((lw or 20) / 2), math.floor((lh or 24) / 2))
    end
  end
end

--[[ K. ROOL P2: Final form, 6 HP, 2 phases ]]
local function new_krool_p2()
  local b = {
    type = M.BOSS_KROOL_P2,
    hp = 6, max_hp = 6,
    state = M.STATE_INTRO,
    timer = 0, attack_timer = 0,
    x = 160, y = 100, start_x = 160, start_y = 100,
    target_x = 160, target_y = 100,
    speed = 200, phase = 1,
    slam_timer = 0, breath_timer = 0,
    hit_flash_timer = 0, defeated_timer = 0,
    spawned_reward = false, alive = true, enraged = false,
    projectiles = {},
  }
  return b
end

local function update_krool2_intro(b, dt)
  b.timer = b.timer + dt
  if b.timer > 2.5 then
    b.state = M.STATE_ATTACK
    b.timer = 0
    b.phase = 1
  end
end

local function update_krool2_phase1(b, dt, player_x, player_y, ground_y)
  b.timer = b.timer + dt
  b.attack_timer = b.attack_timer + dt

  -- Stomp and ground pound
  if b.attack_timer > 2.0 then
    b.attack_timer = 0
    b.target_x = player_x
    b.target_y = ground_y - 32
    b.speed = 400
    -- Shockwave projectile
    for i = -2, 2 do
      b.projectiles = spawn_projectile(b, b.projectiles,
        b.x + i * 20, ground_y - 8,
        i * 80, 0, 12, 8, "shockwave")
    end
  end

  if not move_toward(b, b.target_x, b.target_y, b.speed, dt) then
    b.y = b.y - 300 * dt -- simulate jump
  end

  -- Phase transition at 3 HP
  if b.hp <= 3 and not b.enraged then
    b.enraged = true
    b.state = M.STATE_TRANSITION
    b.timer = 0
    b.phase = 2
  end
end

local function update_krool2_phase2(b, dt, player_x, player_y, ground_y)
  b.timer = b.timer + dt
  b.attack_timer = b.attack_timer + dt
  b.breath_timer = b.breath_timer + dt

  -- Fast charges + fire breath projectiles
  if b.attack_timer > 1.5 then
    b.attack_timer = 0
    b.target_x = player_x > b.x and 300 or 20
    b.target_y = ground_y - 32
    b.speed = 500
  end

  if b.breath_timer > 0.5 then
    b.breath_timer = 0
    local dir = player_x > b.x and 1 or -1
    b.projectiles = spawn_projectile(b, b.projectiles,
      b.x + dir * 20, b.y,
      dir * 200 + math.random(-30, 30), math.random(-50, 50),
      10, 10, "fire")
  end

  if not move_toward(b, b.target_x, b.target_y, b.speed, dt) then
    b.y = b.y - 200 * dt
  end
end

local function update_krool2_transition(b, dt)
  b.timer = b.timer + dt
  -- Flash and change phase
  b.hit_flash_timer = 0.1
  if b.timer > 2.0 then
    b.timer = 0
    b.attack_timer = 0
    b.projectiles = {}
    b.speed = 500
    b.state = M.STATE_ATTACK
  end
end

local function update_krool2_defeated(b, dt, spawn_object_fn, lw, lh)
  b.defeated_timer = b.defeated_timer + dt
  b.y = b.y + 40 * dt
  local exit_floor = (lh or 24) * 16
  if b.y > exit_floor + 96 then b.alive = false end
  if not b.spawned_reward and b.defeated_timer > 1.0 then
    b.spawned_reward = true
    if spawn_object_fn then
      spawn_object_fn(8, math.floor((lw or 20) / 2), math.floor((lh or 24) / 2))
    end
  end
end

--[[ Factory ]]
function M.create_boss(boss_type, level_width, level_height)
  local boss
  if boss_type == M.BOSS_KROW then
    boss = new_krow()
  elseif boss_type == M.BOSS_KLEAVER then
    boss = new_kleaver()
  elseif boss_type == M.BOSS_KING_ZING then
    boss = new_king_zing()
  elseif boss_type == M.BOSS_KREEP then
    boss = new_kreep()
  elseif boss_type == M.BOSS_KROOL_P1 then
    boss = new_krool_p1()
  elseif boss_type == M.BOSS_KROOL_P2 then
    boss = new_krool_p2()
  else
    boss = new_krow()
  end

  if level_width and level_height then
    boss.x = level_width * 16 * 0.5
    boss.y = level_height * 16 - 48
    boss.start_x = boss.x
    boss.start_y = boss.y
    if boss.center_x then
      boss.center_x = boss.x
      boss.center_y = boss.y - 80
    end
    if boss.start_y_orig then
      boss.start_y = boss.y
    end
    if boss.teleport_positions then
      for _, tp in ipairs(boss.teleport_positions) do
        tp.x = boss.x + (tp.x - 160)
        tp.y = boss.y - 80 + (tp.y - 240)
      end
    end
  end
  return boss
end

--[[ Update dispatcher ]]
function M.update(boss, dt, player_x, player_y, ground_y, level_width, level_height, spawn_object_fn)
  if not boss or not boss.alive then return end

  update_hit_flash(boss, dt)

  local bt = boss.type

  if bt == M.BOSS_KROW then
    -- Keep existing Krow logic mostly intact
    if boss.state == M.STATE_INTRO then
      boss.timer = boss.timer + dt
      if boss.timer > 1.5 then
        boss.state = M.STATE_ATTACK
        boss.timer = 0
        boss.swoops_done = 0
      end
    elseif boss.state == M.STATE_ATTACK then
      if boss.timer == 0 then
        boss.target_x = player_x
        boss.target_y = 80
      end
      local dx = boss.target_x - boss.x
      local dy = boss.target_y - boss.y
      local dist = math.sqrt(dx * dx + dy * dy)
      if dist > 4 then
        local step = boss.speed * dt
        boss.x = boss.x + (dx / dist) * step
        boss.y = boss.y + (dy / dist) * step
      else
        boss.x = boss.target_x
        boss.y = boss.target_y
        boss.timer = boss.timer + dt
        if boss.timer > 0.3 then
          if boss.target_y == 80 then
            boss.target_x = boss.x
            boss.target_y = boss.start_y
            boss.speed = 120
          else
            boss.swoops_done = boss.swoops_done + 1
            if boss.swoops_done >= boss.swoops_before_eggs then
              boss.state = M.STATE_ATTACK2
              boss.timer = 0
              boss.egg_count = 0
            else
              boss.timer = 0
            end
          end
        end
      end
    elseif boss.state == M.STATE_ATTACK2 then
      boss.timer = boss.timer + dt
      local interval = boss.enraged and 0.3 or 0.6
      if boss.timer >= interval and boss.egg_count < boss.eggs_to_drop then
        boss.egg_count = boss.egg_count + 1
        boss.timer = 0
        local egg = {
          x = boss.x + math.random(-40, 40),
          y = boss.y - 8,
          vy = -50, alive = true, type = 100,
        }
        boss.projectiles = boss.projectiles or {}
        boss.projectiles[#boss.projectiles + 1] = egg
      end
      if boss.egg_count >= boss.eggs_to_drop and (not boss.projectiles or #boss.projectiles == 0) then
        boss.swoops_done = 0
        boss.state = M.STATE_ATTACK
        boss.timer = 0
      end
    elseif boss.state == M.STATE_ENRAGED then
      boss.enraged = true
      boss.swoops_before_eggs = 1
      boss.eggs_to_drop = 6
      boss.speed = 300
      -- Reuse attack logic
      boss.state = M.STATE_ATTACK
      boss.timer = 0
    elseif boss.state == M.STATE_DEFEATED then
      boss.defeated_timer = boss.defeated_timer + dt
      boss.y = boss.y + 60 * dt
      local exit_floor = (level_height or 24) * 16
      if boss.y > exit_floor + 64 then boss.alive = false end
      if not boss.spawned_reward and boss.defeated_timer > 0.5 then
        boss.spawned_reward = true
        if spawn_object_fn then
          spawn_object_fn(8, math.floor((level_width or 20) / 2), math.floor((level_height or 24) / 2))
        end
      end
    end

    -- Krow egg physics
    if boss.projectiles then
      for i = #boss.projectiles, 1, -1 do
        local egg = boss.projectiles[i]
        if not egg.alive then
          table.remove(boss.projectiles, i)
        else
          egg.vy = egg.vy + 400 * dt
          egg.y = egg.y + egg.vy * dt
          if egg.y >= (level_height or 24) * 16 then
            egg.alive = false
            if spawn_object_fn then
              local kritter = spawn_object_fn(5, math.floor(egg.x / 16), math.floor(((level_height or 24) * 16) / 16) - 1)
              if kritter then kritter.ignore_player = true end
            end
          end
        end
      end
    end

  elseif bt == M.BOSS_KLEAVER then
    if boss.state == M.STATE_INTRO then
      update_kleaver_intro(boss, dt)
    elseif boss.state == M.STATE_ATTACK then
      update_kleaver_dive(boss, dt, player_x)
    elseif boss.state == M.STATE_ATTACK2 then
      update_kleaver_bombs(boss, dt, player_x)
    elseif boss.state == M.STATE_ENRAGED then
      boss.enraged = true
      boss.dives_before_bombs = 1
      boss.bombs_to_drop = 8
      boss.speed = 300
      boss.state = M.STATE_ATTACK
      boss.timer = 0
    elseif boss.state == M.STATE_DEFEATED then
      update_kleaver_defeated(boss, dt, spawn_object_fn, level_width, level_height)
    end

  elseif bt == M.BOSS_KING_ZING then
    if boss.state == M.STATE_INTRO then
      update_zing_intro(boss, dt)
    elseif boss.state == M.STATE_ATTACK then
      update_zing_attack(boss, dt, spawn_object_fn)
    elseif boss.state == M.STATE_ENRAGED then
      boss.enraged = true
      boss.zingers_spawned = 4
      boss.state = M.STATE_ATTACK
      boss.timer = 0
    elseif boss.state == M.STATE_DEFEATED then
      update_zing_defeated(boss, dt, spawn_object_fn, level_width, level_height)
    end

  elseif bt == M.BOSS_KREEP then
    if boss.state == M.STATE_INTRO then
      update_kreep_intro(boss, dt)
    elseif boss.state == M.STATE_ATTACK then
      update_kreep_attack(boss, dt, spawn_object_fn)
    elseif boss.state == M.STATE_ENRAGED then
      boss.enraged = true
      boss.soul_count = 3
      boss.state = M.STATE_ATTACK
      boss.timer = 0
    elseif boss.state == M.STATE_DEFEATED then
      update_kreep_defeated(boss, dt, spawn_object_fn, level_width, level_height)
    end

  elseif bt == M.BOSS_KROOL_P1 then
    if boss.state == M.STATE_INTRO then
      update_krool_intro(boss, dt)
    elseif boss.state == M.STATE_ATTACK then
      if boss.disguise == DISGUISE_COWBOY then
        update_krool_cowboy(boss, dt, player_x, player_y)
      elseif boss.disguise == DISGUISE_MAGICIAN then
        update_krool_magician(boss, dt, player_x, player_y)
      elseif boss.disguise == DISGUISE_PIRATE then
        update_krool_pirate(boss, dt, player_x)
      elseif boss.disguise == DISGUISE_KRUSHER then
        update_krool_krusher(boss, dt, player_x, ground_y or 368)
      end
    elseif boss.state == M.STATE_TRANSITION then
      update_krool_transition(boss, dt)
    elseif boss.state == M.STATE_ENRAGED then
      boss.enraged = true
      boss.state = M.STATE_ATTACK
      boss.timer = 0
    elseif boss.state == M.STATE_DEFEATED then
      update_krool_defeated(boss, dt, spawn_object_fn, level_width, level_height)
    end

  elseif bt == M.BOSS_KROOL_P2 then
    if boss.state == M.STATE_INTRO then
      update_krool2_intro(boss, dt)
    elseif boss.state == M.STATE_ATTACK then
      if boss.phase == 1 then
        update_krool2_phase1(boss, dt, player_x, player_y, ground_y or 368)
      else
        update_krool2_phase2(boss, dt, player_x, player_y, ground_y or 368)
      end
    elseif boss.state == M.STATE_TRANSITION then
      update_krool2_transition(boss, dt)
    elseif boss.state == M.STATE_DEFEATED then
      update_krool2_defeated(boss, dt, spawn_object_fn, level_width, level_height)
    end
  end
end

function M.get_hitbox(boss)
  if not boss or not boss.alive then return nil end
  if boss.state == M.STATE_DEFEATED then return nil end
  return {
    x = boss.x - 16, y = boss.y - 16, w = 32, h = 32,
  }
end

function M.get_projectile_hitboxes(boss)
  local boxes = {}
  if not boss or not boss.projectiles then return boxes end
  for _, p in ipairs(boss.projectiles) do
    if p.alive then
      boxes[#boxes + 1] = { x = p.x - p.w/2, y = p.y - p.h/2, w = p.w, h = p.h }
    end
  end
  return boxes
end

function M.take_damage(boss)
  if not boss or not boss.alive then return false end
  if boss.hit_flash_timer > 0 then return false end
  if boss.state == M.STATE_INTRO or boss.state == M.STATE_DEFEATED then return false end

  boss.hp = boss.hp - 1
  boss.hit_flash_timer = 0.5

  if boss.hp <= 0 then
    boss.state = M.STATE_DEFEATED
    boss.defeated_timer = 0
  elseif boss.hp <= 1 and boss.type ~= M.BOSS_KROOL_P1 and boss.type ~= M.BOSS_KROOL_P2 then
    boss.state = M.STATE_ENRAGED
    boss.enraged = true
    boss.timer = 0
  elseif boss.type ~= M.BOSS_KROW then
    boss.state = M.STATE_ENRAGED
    boss.enraged = true
    boss.timer = 0
  end
  return true
end

function M.get_render_info(boss)
  if not boss then return nil end
  local info = {
    visible = boss.alive and boss.state ~= M.STATE_DEFEATED,
    x = boss.x, y = boss.y,
    state = boss.state, hp = boss.hp, max_hp = boss.max_hp,
    flash = boss.hit_flash_timer > 0,
    enraged = boss.enraged,
    projectiles = {},
    type = boss.type,
    disguise = boss.disguise,
    phase = boss.phase,
  }
  if boss.projectiles then
    for _, p in ipairs(boss.projectiles) do
      if p.alive then
        info.projectiles[#info.projectiles + 1] = { x = p.x, y = p.y, w = p.w or 8, h = p.h or 8 }
      end
    end
  end
  return info
end

function M.cleanup(boss)
  if boss then
    boss.projectiles = nil
  end
end

return M
