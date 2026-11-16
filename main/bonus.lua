local M = {}

M.active = false
M.timer = 0
M.target_bananas = 8
M.collected = 0
M.time_limit = 20
M.golden_token = false
M.completed = false
M.banana_positions = {}
M.player_x = 0
M.player_y = 0
M.player_vel_x = 0
M.player_vel_y = 0

function M.start(stage_data)
  M.active = true
  M.timer = stage_data.time_limit or 20
  M.target_bananas = stage_data.target_bananas or 8
  M.collected = 0
  M.golden_token = false
  M.completed = false
  M.banana_positions = {}
  M.player_x = 64
  M.player_y = 360

  for i = 1, M.target_bananas do
    table.insert(M.banana_positions, {
      x = 100 + math.random(1080),
      y = 100 + math.random(400),
      collected = false,
    })
  end
end

function M.update(dt, input)
  if not M.active then return end
  M.timer = M.timer - dt

  if M.timer <= 0 then
    M.active = false
    M.completed = false
    return "timeout"
  end

  local left = input.hold_bit(input.BIT.LEFT)
  local right = input.hold_bit(input.BIT.RIGHT)
  local up = input.hold_bit(input.BIT.UP)
  local down = input.hold_bit(input.BIT.DOWN)

  local spd = 200
  if left then M.player_x = M.player_x - spd * dt end
  if right then M.player_x = M.player_x + spd * dt end
  if up then M.player_y = M.player_y - spd * dt end
  if down then M.player_y = M.player_y + spd * dt end

  M.player_x = math.max(16, math.min(1264, M.player_x))
  M.player_y = math.max(16, math.min(704, M.player_y))

  for _, pos in ipairs(M.banana_positions) do
    if not pos.collected then
      local dx = M.player_x - pos.x
      local dy = M.player_y - pos.y
      local dist = math.sqrt(dx * dx + dy * dy)
      if dist < 24 then
        pos.collected = true
        M.collected = M.collected + 1
        if M.collected >= M.target_bananas then
          M.golden_token = true
          M.active = false
          M.completed = true
          return "complete"
        end
      end
    end
  end

  return "playing"
end

function M.get_state()
  return {
    active = M.active,
    timer = M.timer,
    collected = M.collected,
    target = M.target_bananas,
    golden_token = M.golden_token,
    completed = M.completed,
    banana_positions = M.banana_positions,
    player_x = M.player_x,
    player_y = M.player_y,
  }
end

function M.reset()
  M.active = false
  M.timer = 0
  M.collected = 0
  M.golden_token = false
  M.completed = false
  M.banana_positions = {}
end

return M
