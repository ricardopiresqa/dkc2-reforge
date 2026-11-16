local M = {}

M.name = "Squitter"
M.label = "H"
M.color = { 0.6, 0.0, 0.6, 1.0 }

local GRAVITY = 2000
local RUN_SPEED = 200
local JUMP_VEL = -480
local TERMINAL_VEL = 900

M.climbing = false

function M.on_mount(pl)
  M.climbing = false
end

function M.on_dismount(pl)
  M.climbing = false
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
    M.climbing = false
    pl.state = pl.STATE.FALL
    return
  end

  local hx = pl.pos_x - 6
  local hy = pl.pos_y + pl.height - 1
  local check_col, check_row = collision.world_to_tile(hx, hy)
  local wall_l = collision.get_tile(check_col - 1, check_row)
  local wall_r = collision.get_tile(check_col + 1, check_row)

  if move_dir ~= 0 then
    pl.direction = move_dir
    pl.vel_x = RUN_SPEED * move_dir
  else
    pl.vel_x = 0
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
  return pl.pos_x - 12, pl.pos_y, 24, 20
end

return M
