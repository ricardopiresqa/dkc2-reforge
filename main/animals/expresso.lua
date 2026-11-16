local M = {}

M.name = "Expresso"
M.label = "E"
M.color = { 0.2, 0.6, 1.0, 1.0 }

local GRAVITY = 2000
local RUN_SPEED = 450
local JUMP_VEL = -500
local TERMINAL_VEL = 900

function M.on_mount(pl)
end

function M.on_dismount(pl)
end

function M.update(pl, dt, input, collision)
  local left = input.hold_bit(input.BIT.LEFT)
  local right = input.hold_bit(input.BIT.RIGHT)
  local up = input.edge_bit(input.BIT.UP)
  local b_jump = input.edge_bit(input.BIT.B)

  local move_dir = 0
  if left then move_dir = -1 end
  if right then move_dir = 1 end

  if up then
    local dir = 0
    if left then dir = -1 elseif right then dir = 1 else dir = pl.direction end
    pl.vel_x = 120 * dir
    pl.vel_y = -200
    pl.grounded = false
    pl.mount_type = nil
    pl.state = pl.STATE.FALL
    return
  end

  if move_dir ~= 0 then
    pl.direction = move_dir
    local accel = RUN_SPEED * 4
    pl.vel_x = pl.vel_x + accel * move_dir * dt
    if math.abs(pl.vel_x) > RUN_SPEED then
      pl.vel_x = RUN_SPEED * move_dir
    end
  else
    local sign = pl.vel_x > 0 and 1 or -1
    pl.vel_x = pl.vel_x - sign * 600 * dt
    if math.abs(pl.vel_x) < 5 then pl.vel_x = 0 end
  end

  pl.vel_y = pl.vel_y + GRAVITY * dt
  if pl.vel_y > TERMINAL_VEL then
    pl.vel_y = TERMINAL_VEL
  end

  if b_jump and pl.grounded then
    pl.vel_y = JUMP_VEL
    pl.grounded = false
  end
end

function M.get_hitbox(pl)
  return pl.pos_x - 14, pl.pos_y, 28, 28
end

return M
