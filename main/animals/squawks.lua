local M = {}

M.name = "Squawks"
M.label = "P"
M.color = { 0.0, 0.8, 0.4, 1.0 }

local FLY_SPEED = 180
local GLIDE_GRAVITY = 200
local NORMAL_GRAVITY = 2000

function M.on_mount(pl)
end

function M.on_dismount(pl)
end

function M.update(pl, dt, input, collision)
  local left = input.hold_bit(input.BIT.LEFT)
  local right = input.hold_bit(input.BIT.RIGHT)
  local up_edge = input.edge_bit(input.BIT.UP)
  local b_hold = input.hold_bit(input.BIT.B)
  local b_edge = input.edge_bit(input.BIT.B)

  local move_dir = 0
  if left then move_dir = -1 end
  if right then move_dir = 1 end

  if up_edge then
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
    pl.vel_x = FLY_SPEED * move_dir
  else
    local sign = pl.vel_x > 0 and 1 or -1
    pl.vel_x = pl.vel_x - sign * 400 * dt
    if math.abs(pl.vel_x) < 5 then pl.vel_x = 0 end
  end

  if b_hold then
    pl.vel_y = pl.vel_y + GLIDE_GRAVITY * dt
    if pl.vel_y > 100 then pl.vel_y = 100 end
  else
    pl.vel_y = pl.vel_y + NORMAL_GRAVITY * dt
  end

  if b_edge and pl.grounded then
    pl.vel_y = -350
    pl.grounded = false
  end
end

function M.get_hitbox(pl)
  return pl.pos_x - 11, pl.pos_y, 22, 20
end

return M
