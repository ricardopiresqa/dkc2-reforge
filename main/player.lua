local input = require("main.input")
local collision = require("main.collision")
local sound = require("main.sound")
local original_motion = require("main.original_motion")
local objects = nil

local M = {}

function M.set_objects(mod) objects = mod end

M.STATE = {
  IDLE            = 1,
  RUN             = 2,
  JUMP            = 3,
  FALL            = 4,
  ROLL            = 5,
  CROUCH          = 6,
  SKID            = 7,
  CLIMB           = 8,
  SWIM            = 9,
  BARREL          = 10,
  TEAM_THROW      = 11,
  DAMAGE          = 12,
  DEATH           = 13,
  RAMBI_RIDING    = 14,
  ENGUARDE_RIDING = 15,
  MOUNTED         = 16,
}

local WALK_SPEED      = 160
local RUN_SPEED       = 300
local ROLL_SPEED      = 450
local GRAVITY         = 2000
local JUMP_VEL        = -480
local JUMP_HOLD_FORCE = -900
local JUMP_HOLD_TIME  = 0.10
local DOUBLE_JUMP     = -360
local TERMINAL_VEL    = 900
local FRICTION        = 600
local SKID_DECEL      = 1200
local AIR_FRICTION    = 150
local AIR_SPEED       = 100

local BARREL_SPEED    = 600

local RAMBI_SPEED     = 400
local RAMBI_JUMP      = -550

local ENGUARDE_SPEED  = 250
local ENGUARDE_LUNGE  = 500
local LUNGE_DURATION  = 0.3

local SWIM_SPEED       = 120
local SWIM_BOOST       = -200
local WATER_GRAVITY    = 200
local BREATH_MAX       = 100
local BREATH_DRAIN     = 25
local BREATH_REFILL    = 60

local CLIMB_SPEED_UP   = 60
local CLIMB_SPEED_DOWN = 90

local DIR_N  = 1
local DIR_NE = 2
local DIR_E  = 3
local DIR_SE = 4
local DIR_S  = 5
local DIR_SW = 6
local DIR_W  = 7
local DIR_NW = 8

M.pos_x = 0
M.pos_y = 0
M.vel_x = 0
M.vel_y = 0
M.state = M.STATE.IDLE
M.direction = 1
M.grounded = false
M.jumps = 0
-- Gate de semantica: prototipo permite double jump (mecanica generica);
-- nivel com `original_semantics` (dado original provado) desliga.
-- Leitura lazy de level_loader para nao criar ciclo require.
M.can_double_jump = false
M._semantics_checked = false
M.roll_timer = 0
M.jump_hold_timer = 0
M.jump_holding = false
M.health = 3
M.invincible_timer = 0
M.barrel_angle = 1
M.barrel_timer = 0
M.breath = BREATH_MAX
M.water_surface_y = nil
M.was_in_water = false
M.mount_type = nil
M.is_charging = false
M.lunge_timer = 0
M.current_rope = nil
M.rope_snap_x = nil

local PLAYER_W = 16
local PLAYER_H = 24
local CROUCH_H = 16

local barrel_angle_vectors = {
  [DIR_N]  = { x = 0, y = -1 },
  [DIR_NE] = { x = 0.707, y = -0.707 },
  [DIR_E]  = { x = 1, y = 0 },
  [DIR_SE] = { x = 0.707, y = 0.707 },
  [DIR_S]  = { x = 0, y = 1 },
  [DIR_SW] = { x = -0.707, y = 0.707 },
  [DIR_W]  = { x = -1, y = 0 },
  [DIR_NW] = { x = -0.707, y = -0.707 },
}

local function update_air_horizontal(move_dir, dt, running, idle_friction)
  if M.original_ground_motion then
    return  -- applied before the move (see M.update)
  elseif move_dir ~= 0 then
    M.vel_x = M.vel_x + AIR_SPEED * move_dir * dt
    if math.abs(M.vel_x) > RUN_SPEED then
      M.vel_x = RUN_SPEED * move_dir
    end
    M.direction = move_dir
  elseif idle_friction then
    local sign = M.vel_x > 0 and 1 or -1
    M.vel_x = M.vel_x - sign * AIR_FRICTION * dt
    if math.abs(M.vel_x) < 5 then M.vel_x = 0 end
  end
end

function M.spawn(x, y)
  M.gliding = false
  require("main.original_motion").terminal = 0x0800
  M.pos_x = x
  M.pos_y = y
  M.vel_x = 0
  M.vel_y = 0
  M.state = M.STATE.IDLE
  M.direction = 1
  M.grounded = true
  M.jumps = 0
  M.bounced, M.landing_hold = false, false
  M.rolling, M.roll_stop, M.roll_done = false, false, false
  -- Original DKC2 1-1 (Pirate Panic) nao tem double jump, HP 3 nem breath
  -- drenando: sao mecanicas genericas do prototipo. Gate por
  -- `original_semantics` do level; leitura lazy para nao ciclar require
  -- (player <-> level_loader). Prototipo (false/nil) preserva comportamento.
  local original = false
  local ok, ll = pcall(require, "main.level_loader")
  if ok and ll and ll.original_semantics then
    original = ll.original_semantics()
  end
  M.can_double_jump = not original
  M.original_ground_motion = original
  M.jump_windup = 0
  -- semantica original: um golpe com um Kong so = perde a vida (sem HP
  -- numerico; Diddy soh, Dixie/AI sao gap declarado). Prototipo: HP 3.
  M.max_health = original and 1 or 3
  M.no_breath_drain = original
  M.jump_hold_timer = 0
  M.jump_holding = false
  M.roll_timer = 0
  M.health = M.max_health
  M.invincible_timer = 0
  M.barrel_angle = DIR_E
  M.breath = BREATH_MAX
  M.water_surface_y = nil
  M.was_in_water = false
  M.mount_type = nil
  M.is_charging = false
  M.lunge_timer = 0
  M.hitpause_frames = 0
end

function M.update(dt)
  if M.hitpause_frames > 0 then
    M.hitpause_frames = M.hitpause_frames - 1
    return
  end

  local hold = input.get_hold()
  local edge = input.get_edge()

  local left   = input.hold_bit(input.BIT.LEFT)
  local right  = input.hold_bit(input.BIT.RIGHT)
  local up     = input.hold_bit(input.BIT.UP)
  local down   = input.hold_bit(input.BIT.DOWN)
  local b_jump = input.edge_bit(input.BIT.B)
  local b_hold = input.hold_bit(input.BIT.B)
  local y_roll = input.edge_bit(input.BIT.Y)
  if M.original_ground_motion then
    if b_jump and M.grounded and (M.state == M.STATE.IDLE or M.state == M.STATE.RUN) then
      -- Observed Diddy short-jump trace: pressed frame 151, takeoff frame 153.
      M.jump_windup = 2
      b_jump = false
    elseif M.jump_windup > 0 then
      M.jump_windup = M.jump_windup - 1
      b_jump = M.jump_windup == 0 and M.grounded
    end
  end

  if M.state == M.STATE.DEATH then
    M.vel_y = M.vel_y + GRAVITY * dt
    M.pos_y = M.pos_y + M.vel_y * dt
    return
  end

  if M.invincible_timer > 0 then
    M.invincible_timer = M.invincible_timer - dt
  end

  local move_dir = 0
  if left then move_dir = -1 end
  if right then move_dir = 1 end
  M.move_dir = move_dir  -- the pressed direction ($26 sign): original_animation's turn check

  local original_ground_control = M.original_ground_motion and M.grounded
      and (M.state == M.STATE.IDLE or M.state == M.STATE.RUN or M.state == M.STATE.SKID)
  -- Original cartwheel (cartwheel-probe.csv): a Y press on the ground starts animation $09;
  -- vx eases toward the run speed $360 in the facing direction (same 1/8 rule) until the
  -- script stops it (B9DE45: 14 frames at vx 0) and hands control back (B9DFE7).
  if M.original_ground_motion and y_roll and M.grounded and not M.rolling and not M.carrying and not M.roll_blocked
      and (M.state == M.STATE.IDLE or M.state == M.STATE.RUN or M.state == M.STATE.SKID) then
    M.rolling, M.roll_stop, M.roll_done = true, false, false
    if move_dir ~= 0 then M.direction = move_dir end
    M.state = M.STATE.RUN
    require("main.original_animation").force(0x09, M)
  end
  if M.rolling then
    if M.roll_done or b_jump then
      M.rolling = false
      require("main.original_animation").release()
    end
  end
  local landing_hold = M.landing_hold
  M.landing_hold = false
  M.held_vel_x = landing_hold and M.vel_x or nil  -- restored at the end of the frame
  if landing_hold or M.rolling then
    original_ground_control = false
  end
  if M.rolling then
    M.vel_x = M.roll_stop and 0 or original_motion.ground_velocity(M.vel_x, M.direction, true)
    M.state = M.STATE.RUN
  end
  if original_ground_control then
    M.vel_x = original_motion.ground_velocity(M.vel_x, move_dir, input.hold_bit(input.BIT.Y))
    if move_dir ~= 0 then
      M.state = M.STATE.RUN
      M.direction = move_dir
    elseif math.abs(M.vel_x) < 0.1 then
      M.state = M.STATE.IDLE
    end
  elseif M.original_ground_motion and (M.state == M.STATE.JUMP or M.state == M.STATE.FALL) then
    -- Airborne: same 1/8 approach, applied before this frame's move as on the ground
    -- (reference-gameplay.csv 595-611: the new vx moves the player on the input frame).
    M.vel_x = original_motion.ground_velocity(M.vel_x, move_dir, input.hold_bit(input.BIT.Y))
    if move_dir ~= 0 then M.direction = move_dir end
  end

  local current_h = (M.state == M.STATE.CROUCH) and CROUCH_H or PLAYER_H

  local new_x = M.pos_x
  local new_y = M.pos_y
  local hit_wall = false
  local hit_floor
  local floor_type

  if M.state ~= M.STATE.CLIMB then
    local original_basic = M.original_ground_motion and
      (M.state == M.STATE.IDLE or M.state == M.STATE.RUN or M.state == M.STATE.SKID
       or M.state == M.STATE.JUMP or M.state == M.STATE.FALL)
    -- Dixie's helicopter spin (B8C921: falling in the jump state, B pressed): vy $FF00 and
    -- terminal $0100 from her table (+$30 / +$2E), anim $0B; it lasts while B is held.
    -- APPROXIMATION: the trigger is not reproduced on a capture (three probes pressed B
    -- falling and the spin never started: B8C950's $16F2 timestamp test stayed false), so
    -- the gate is B newly pressed while falling; the 24 px clearance test is not ported.
    if original_basic and original_motion.kong_name == "dixie" then
      if M.gliding and (M.grounded or not b_hold) then
        M.gliding, original_motion.terminal = false, 0x0800
        if require("main.original_animation").forced == 0x0B then require("main.original_animation").release() end
      elseif not M.gliding and not M.grounded and M.vel_y >= 0 and input.edge_bit(input.BIT.B) then
        M.gliding, original_motion.terminal, M.vel_y = true, 0x0100, -0x100 * 60 / 256
        require("main.original_animation").force(0x0B, M)
      end
    elseif M.gliding then
      M.gliding, original_motion.terminal = false, 0x0800
    end
    if original_basic then
      M.vel_y = original_motion.vertical_velocity(M.vel_y,
        M.state == M.STATE.JUMP and M.jump_holding and b_hold and M.jump_hold_timer > 0)
    else
      M.vel_y = M.vel_y + GRAVITY * dt
      if M.vel_y > TERMINAL_VEL then M.vel_y = TERMINAL_VEL end
    end

    local step_y
    local dx = landing_hold and 0 or M.vel_x * dt
    -- the level's left edge stops the Kong at x 16 (raw 272) with vx kept (left-edge-t1.csv)
    if M.original_ground_motion then dx = math.max(dx, math.min(0, 16 - M.pos_x)) end
    new_x, hit_wall, step_y = collision.resolve_x(M.pos_x, M.pos_y, PLAYER_W, current_h, dx, M.grounded)
    local vertical_start_y = step_y or M.pos_y
    new_y, hit_floor, floor_type = collision.resolve_y(new_x, vertical_start_y, PLAYER_W, current_h, M.vel_y * dt)
    if step_y and not hit_floor then new_y = step_y end
    M.grounded = floor_type == "ground" or floor_type == "platform"

    if not M.grounded then
      M.grounded = collision.is_grounded(new_x, new_y, PLAYER_W, current_h)
    end

    -- Original terrain: on the ground the feet sit on the surface of the single pixel
    -- column at x (reference-gameplay.csv: 756/756 grounded frames), not on the highest
    -- surface under the body width.
    if M.original_ground_motion and M.grounded and M.vel_y >= 0 then
      local feet = new_y + current_h
      local surface = collision.surface_at(math.floor(new_x), feet - 8, feet + 8)
      if surface then new_y = surface - current_h end
    end

    -- Parado no chao a gravidade continuava somando ate a velocidade terminal;
    -- o passo vertical passava de 16px por frame e o resolvedor pulava a linha
    -- de tiles do piso (tunelamento). Zerar aqui mantem o passo pequeno.
    if M.grounded and M.vel_y > 0 then
      M.vel_y = M.original_ground_motion and (3 * 60) or 0
    end

    if M.state == M.STATE.JUMP or M.state == M.STATE.FALL then
      if M.grounded then
        M.vel_y = 0
        M.state = M.STATE.IDLE
        -- Landing from the stomp bounce (original state 22) holds x and vx for one
        -- frame; a plain jump landing does not (reference-gameplay.csv 200/608/974).
        if M.original_ground_motion and M.bounced then M.landing_hold = true end
        M.bounced = false
      end
    end

    if not M.grounded then
      if M.state == M.STATE.IDLE or M.state == M.STATE.RUN then
        M.state = M.STATE.FALL
      end
    end
  end

  local in_water = collision.is_in_water(new_x, new_y + current_h * 0.5, PLAYER_W)
  if in_water and M.state ~= M.STATE.SWIM and M.state ~= M.STATE.DEATH and M.state ~= M.STATE.BARREL and M.state ~= M.STATE.ENGUARDE_RIDING then
    M.vel_y = 0
    M.state = M.STATE.SWIM
    M.water_surface_y = collision.get_water_surface(new_x)
    M.breath = M.breath or BREATH_MAX
  end

  local rope = objects.get_rope_at(new_x - PLAYER_W * 0.5, new_y, PLAYER_W, current_h)
  if rope and (up or down) and M.state ~= M.STATE.CLIMB and M.state ~= M.STATE.DEATH and M.state ~= M.STATE.BARREL and M.state ~= M.STATE.SWIM then
    M.state = M.STATE.CLIMB
    M.vel_x = 0
    M.vel_y = 0
    M.current_rope = rope
    M.rope_snap_x = rope.x
  elseif M.state == M.STATE.CLIMB then
    if not rope then
      M.state = M.STATE.FALL
      M.current_rope = nil
    end
  end

  if M.state == M.STATE.IDLE then
    if b_jump and M.grounded then
      M.state = M.STATE.JUMP
      sound.play("jump")
      M.vel_y = M.original_ground_motion and original_motion.jump_velocity() or JUMP_VEL
      M.jump_hold_timer = JUMP_HOLD_TIME
      M.jump_holding = true
      M.grounded = false
      M.jumps = 1
    elseif y_roll and M.grounded and not M.original_ground_motion and not M.carrying then  -- original: cartwheel above
      M.state = M.STATE.ROLL
      M.vel_x = ROLL_SPEED * M.direction
      M.roll_timer = 0.35
    elseif down then
      M.state = M.STATE.CROUCH
    elseif move_dir ~= 0 then
      M.state = M.STATE.RUN
      M.direction = move_dir
    end

  elseif M.state == M.STATE.RUN then
    if M.grounded then
      if not original_ground_control and not M.rolling then
      if move_dir == 0 then
        local sign = M.vel_x > 0 and 1 or -1
        M.vel_x = M.vel_x - sign * FRICTION * dt
        if math.abs(M.vel_x) < 10 then
          M.vel_x = 0
          M.state = M.STATE.IDLE
        end
      elseif move_dir ~= M.direction then
        M.state = M.STATE.SKID
        M.direction = move_dir
      else
        M.direction = move_dir
        local target_speed = RUN_SPEED
        if math.abs(M.vel_x) < target_speed then
          local accel = target_speed * 4
          M.vel_x = M.vel_x + accel * move_dir * dt
          if math.abs(M.vel_x) > target_speed then
            M.vel_x = target_speed * move_dir
          end
        else
          M.vel_x = target_speed * move_dir
        end
      end
      end
    elseif not M.rolling then
      if move_dir ~= 0 then
        M.vel_x = M.vel_x + AIR_SPEED * move_dir * dt
        if math.abs(M.vel_x) > RUN_SPEED then
          M.vel_x = RUN_SPEED * move_dir
        end
        M.direction = move_dir
      else
        local sign = M.vel_x > 0 and 1 or -1
        M.vel_x = M.vel_x - sign * AIR_FRICTION * dt
      end
    end
    if b_jump and M.grounded then
      M.state = M.STATE.JUMP
      sound.play("jump")
      M.vel_y = M.original_ground_motion and original_motion.jump_velocity() or JUMP_VEL
      M.jump_hold_timer = JUMP_HOLD_TIME
      M.jump_holding = true
      M.grounded = false
      M.jumps = 1
    end

  elseif M.state == M.STATE.JUMP then
    if M.jump_holding and b_hold and M.jump_hold_timer > 0 then
      if not M.original_ground_motion then M.vel_y = M.vel_y + JUMP_HOLD_FORCE * dt end
      M.jump_hold_timer = M.jump_hold_timer - dt
    else
      M.jump_holding = false
    end
    if b_jump and M.jumps < 2 and M.can_double_jump then
      M.vel_y = DOUBLE_JUMP
      M.jumps = 2
      M.jump_hold_timer = JUMP_HOLD_TIME * 0.5
      M.jump_holding = true
      sound.play("jump")
    end
    if M.vel_y >= 0 then
      M.state = M.STATE.FALL
    end
    update_air_horizontal(move_dir, dt, input.hold_bit(input.BIT.Y), false)

  elseif M.state == M.STATE.FALL then
    update_air_horizontal(move_dir, dt, input.hold_bit(input.BIT.Y), true)
    if b_jump and M.jumps < 2 and M.can_double_jump then
      M.vel_y = DOUBLE_JUMP
      M.jumps = 2
      M.jump_hold_timer = JUMP_HOLD_TIME * 0.5
      M.jump_holding = true
      sound.play("jump")
    end

  elseif M.state == M.STATE.ROLL then
    M.roll_timer = M.roll_timer - dt
    if M.roll_timer <= 0 then
      M.state = M.STATE.IDLE
    end
    if M.grounded then
      local sign = M.vel_x > 0 and 1 or -1
      M.vel_x = M.vel_x - sign * FRICTION * 0.5 * dt
      if math.abs(M.vel_x) < 10 then M.vel_x = ROLL_SPEED * M.direction end
    end
    if b_jump and M.grounded then
      M.state = M.STATE.JUMP
      M.vel_y = JUMP_VEL
      M.jump_hold_timer = JUMP_HOLD_TIME
      M.jump_holding = true
      M.grounded = false
      M.jumps = 1
    end
    if hit_wall then
      M.state = M.STATE.IDLE
    end

  elseif M.state == M.STATE.CROUCH then
    current_h = CROUCH_H
    -- the box is top-anchored: standing up raises the top so the feet stay on the floor
    -- (each duck sank the Kong 8 px into the deck)
    if not down or (b_jump and M.grounded) then new_y = new_y - (PLAYER_H - CROUCH_H) end
    if not down then
      M.state = M.STATE.IDLE
    end
    if b_jump and M.grounded then
      M.state = M.STATE.JUMP
      sound.play("jump")
      M.vel_y = JUMP_VEL
      M.jump_hold_timer = JUMP_HOLD_TIME
      M.jump_holding = true
      M.grounded = false
      M.jumps = 1
    end

  elseif M.state == M.STATE.SKID then
    -- A frenagem tem que se opor a VELOCIDADE atual. Usando M.direction -- que
    -- ao entrar em SKID ja aponta para o lado NOVO -- o sinal invertia e vel_x
    -- crescia sem limite ate o player sair do mapa.
    local sign = M.vel_x >= 0 and 1 or -1
    M.vel_x = M.vel_x - sign * SKID_DECEL * dt
    if math.abs(M.vel_x) <= 10 or (M.vel_x >= 0) ~= (sign >= 0) then
      M.vel_x = 0
      M.state = M.STATE.IDLE
    end
    if b_jump then
      M.state = M.STATE.JUMP
      sound.play("jump")
      M.vel_y = JUMP_VEL
      M.jump_hold_timer = JUMP_HOLD_TIME
      M.jump_holding = true
      M.grounded = false
      M.jumps = 1
    end

  elseif M.state == M.STATE.SWIM then
    local underwater = collision.is_in_water(new_x, new_y + current_h * 0.5, PLAYER_W)
    if not underwater then
      M.vel_y = M.vel_y + GRAVITY * dt
      M.state = M.STATE.FALL
    else
      M.vel_y = M.vel_y + WATER_GRAVITY * dt
      M.water_surface_y = collision.get_water_surface(new_x)
      local at_surface = M.water_surface_y and (new_y <= M.water_surface_y + 8)

      if at_surface then
        M.breath = math.min(BREATH_MAX, M.breath + BREATH_REFILL * dt)
      elseif not M.no_breath_drain then
        -- Afogamento e mecanica generica do prototipo; no original Pirate
        -- Panic (fase sem secao submersa longa) nao drena.
        M.breath = M.breath - BREATH_DRAIN * dt
        if M.breath <= 0 then
          M.breath = BREATH_MAX
          if M.take_damage() then
            M.state = M.STATE.DEATH
          end
          M.vel_y = -400
          return
        end
      end

      local swim_x = 0
      if left then swim_x = -1 end
      if right then swim_x = 1 end

      local swim_y = 0
      if up then swim_y = -1 end
      if down then swim_y = 1 end

      if swim_x ~= 0 then
        M.vel_x = M.vel_x + SWIM_SPEED * swim_x * dt * 3
        if math.abs(M.vel_x) > SWIM_SPEED then
          M.vel_x = SWIM_SPEED * swim_x
        end
        M.direction = swim_x
      else
        local sign = M.vel_x > 0 and 1 or -1
        M.vel_x = M.vel_x - sign * FRICTION * dt
        if math.abs(M.vel_x) < 5 then M.vel_x = 0 end
      end

      if swim_y ~= 0 then
        M.vel_y = M.vel_y + SWIM_SPEED * swim_y * dt * 3
        if math.abs(M.vel_y) > SWIM_SPEED then
          M.vel_y = SWIM_SPEED * swim_y
        end
      end

      if b_hold and at_surface then
        M.vel_y = SWIM_BOOST
      end

      if down and M.grounded and not underwater then
        M.state = M.STATE.IDLE
      end
    end

  elseif M.state == M.STATE.CLIMB then
    M.vel_x = 0
    M.vel_y = 0

    if up then
      M.vel_y = -CLIMB_SPEED_UP
    elseif down then
      M.vel_y = CLIMB_SPEED_DOWN
    end

    if b_jump then
      M.state = M.STATE.JUMP
      M.vel_y = JUMP_VEL
      M.jump_hold_timer = JUMP_HOLD_TIME
      M.jump_holding = true
      M.grounded = false
      M.jumps = 1
      M.current_rope = nil
      sound.play("jump")
    elseif left then
      M.state = M.STATE.FALL
      M.vel_x = -RUN_SPEED
      M.direction = -1
      M.current_rope = nil
    elseif right then
      M.state = M.STATE.FALL
      M.vel_x = RUN_SPEED
      M.direction = 1
      M.current_rope = nil
    end

    new_x = M.rope_snap_x
    new_y = M.pos_y + M.vel_y * dt

  elseif M.state == M.STATE.BARREL then
    M.vel_x = 0
    M.vel_y = 0
    local aim_x = 0
    local aim_y = 0
    if left then aim_x = -1 end
    if right then aim_x = 1 end
    if up then aim_y = -1 end
    if down then aim_y = 1 end
    if aim_x ~= 0 or aim_y ~= 0 then
      if aim_x == 1 and aim_y == 0 then M.barrel_angle = DIR_E
      elseif aim_x == -1 and aim_y == 0 then M.barrel_angle = DIR_W
      elseif aim_x == 0 and aim_y == -1 then M.barrel_angle = DIR_N
      elseif aim_x == 0 and aim_y == 1 then M.barrel_angle = DIR_S
      elseif aim_x == 1 and aim_y == -1 then M.barrel_angle = DIR_NE
      elseif aim_x == 1 and aim_y == 1 then M.barrel_angle = DIR_SE
      elseif aim_x == -1 and aim_y == -1 then M.barrel_angle = DIR_NW
      elseif aim_x == -1 and aim_y == 1 then M.barrel_angle = DIR_SW
      end
    end
    local shoot = y_roll or b_jump
    if shoot then
      local vec = barrel_angle_vectors[M.barrel_angle]
      M.vel_x = vec.x * BARREL_SPEED
      M.vel_y = vec.y * BARREL_SPEED
      M.state = M.STATE.FALL
      M.grounded = false
      sound.play("barrel_shoot")
      return
    end

  elseif M.state == M.STATE.RAMBI_RIDING then
    local up_edge = input.edge_bit(input.BIT.UP)
    local y_hold = input.hold_bit(input.BIT.Y)
    local y_edge = input.edge_bit(input.BIT.Y)

    if up_edge then
      M.vel_x = 120 * M.direction
      M.vel_y = -200
      M.grounded = false
      M.mount_type = nil
      M.is_charging = false
      M.state = M.STATE.FALL
    else
      M.is_charging = y_hold

      if M.is_charging then
        M.vel_x = RAMBI_SPEED * M.direction
      else
        if move_dir ~= 0 then
          M.direction = move_dir
          local accel = RAMBI_SPEED * 4
          M.vel_x = M.vel_x + accel * move_dir * dt
          if math.abs(M.vel_x) > RAMBI_SPEED then
            M.vel_x = RAMBI_SPEED * move_dir
          end
        else
          local sign = M.vel_x > 0 and 1 or -1
          M.vel_x = M.vel_x - sign * FRICTION * dt
          if math.abs(M.vel_x) < 5 then M.vel_x = 0 end
        end
      end

      if b_jump and M.grounded then
        M.vel_y = RAMBI_JUMP
        M.grounded = false
        sound.play("jump")
      end
    end

    if not M.grounded then
      M.vel_y = M.vel_y + GRAVITY * dt
    end

  elseif M.state == M.STATE.MOUNTED then
    local animals = require("main.animals")
    local animal = animals.get(M.mount_type)
    if animal then
      animal.update(M, dt, input, collision)
    else
      M.state = M.STATE.IDLE
      M.mount_type = nil
    end

  elseif M.state == M.STATE.ENGUARDE_RIDING then
    local up_edge = input.edge_bit(input.BIT.UP)
    local underwater = collision.is_in_water(new_x, new_y + current_h * 0.5, PLAYER_W)

    if up_edge then
      local dir = 0
      if left then dir = -1 elseif right then dir = 1 else dir = M.direction end
      M.vel_x = 80 * dir
      M.vel_y = -120
      M.mount_type = nil
      M.state = M.STATE.SWIM
    elseif not underwater then
      M.state = M.STATE.FALL
      M.mount_type = nil
    else
      M.vel_y = M.vel_y + WATER_GRAVITY * dt

      if M.lunge_timer > 0 then
        M.lunge_timer = M.lunge_timer - dt
      else
        local swim_x = 0
        if left then swim_x = -1 end
        if right then swim_x = 1 end

        local swim_y = 0
        if up then swim_y = -1 end
        if down then swim_y = 1 end

        if swim_x ~= 0 then
          M.vel_x = M.vel_x + ENGUARDE_SPEED * swim_x * dt * 3
          if math.abs(M.vel_x) > ENGUARDE_SPEED then
            M.vel_x = ENGUARDE_SPEED * swim_x
          end
          M.direction = swim_x
        else
          local sign = M.vel_x > 0 and 1 or -1
          M.vel_x = M.vel_x - sign * FRICTION * dt
          if math.abs(M.vel_x) < 5 then M.vel_x = 0 end
        end

        if swim_y ~= 0 then
          M.vel_y = M.vel_y + ENGUARDE_SPEED * swim_y * dt * 3
          if math.abs(M.vel_y) > ENGUARDE_SPEED then
            M.vel_y = ENGUARDE_SPEED * swim_y
          end
        end
      end

      if b_jump and M.lunge_timer <= 0 then
        M.lunge_timer = LUNGE_DURATION
        M.vel_x = ENGUARDE_LUNGE * M.direction
        M.vel_y = 0
      end
    end
  end

  if hit_wall then
    if M.state == M.STATE.RUN and M.grounded then
      M.vel_x = 0
    elseif M.state == M.STATE.RAMBI_RIDING and M.is_charging then
      local check_x = new_x + M.direction * (PLAYER_W * 0.5 + 2)
      local check_y = M.pos_y + current_h * 0.5
      local col, row = collision.world_to_tile(check_x, check_y)
      if collision.break_tile(col, row) then
        M.is_charging = false
        sound.play("stomp")
      end
    end
  end

  M.pos_x = new_x
  M.pos_y = new_y

  if collision.check_spike(M.pos_x, M.pos_y, PLAYER_W, current_h) then
    if M.invincible_timer <= 0 then
      M.health = M.health - 1
      M.invincible_timer = 1.5
      M.vel_y = -300
      M.grounded = false
      M.mount_type = nil
      M.is_charging = false
      M.lunge_timer = 0
      M.state = M.STATE.FALL
      sound.play("damage")
    end
  end

  -- queda em buraco: o limite acompanha a altura do nivel carregado (era fixo
  -- em 1000, inalcancavel para os niveis de 384px)
  if M.pos_y > collision.get_fall_limit() then
    M.health = 0
  end
  if M.held_vel_x then  -- stomp-bounce landing frame: vx untouched
    M.vel_x, M.held_vel_x = M.held_vel_x, nil
  end
end

function M.take_damage()
  if M.invincible_timer > 0 then return false end
  M.health = M.health - 1
  M.invincible_timer = 1.5
  M.vel_y = -300
  M.vel_x = -M.direction * 100
  M.grounded = false
  M.mount_type = nil
  M.is_charging = false
  M.lunge_timer = 0
  M.state = M.STATE.FALL
  return M.health <= 0
end

function M.bounce(vel_y, hitpause_frames)
  M.bounced = true
  M.vel_y = vel_y or -350
  M.grounded = false
  M.state = M.STATE.FALL
  M.hitpause_frames = math.max(0, math.floor(hitpause_frames or 0))
  require("main.original_animation").bounce(M)  -- the bounce frames start on the stomp frame
end

function M.set_z(px, py)
  M.pos_x = px
  M.pos_y = py
end

function M.get_hitbox()
  local h = (M.state == M.STATE.CROUCH) and CROUCH_H or PLAYER_H
  return M.pos_x - PLAYER_W * 0.5, M.pos_y, PLAYER_W, h
end

function M.get_screen_pos(camera)
  return M.pos_x - camera.pos_x, M.pos_y - camera.pos_y
end

return M
