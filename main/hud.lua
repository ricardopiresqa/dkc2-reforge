local M = {}

M.lives = 3
M.bananas = 0
M.dk_coins = 0
M.health = 3
M.banana_counter = 0
M.mount_type = nil
M.kong_letters = {}

M.score = 0

function M.init()
  M.lives = 3
  M.bananas = 0
  M.dk_coins = 0
  M.health = 3
  M.score = 0
  M.banana_counter = 0
  M.kong_letters = {}
end

function M.reset_kong()
  M.kong_letters = {}
end

function M.collect_letter(letter)
  if M.kong_letters[letter] then return end
  M.kong_letters[letter] = true
  M.add_score(50)
  if M.kong_letters["K"] and M.kong_letters["O"] and M.kong_letters["N"] and M.kong_letters["G"] then
    M.add_life()
    M.kong_letters = {}
  end
end

function M.add_bananas(count)
  M.banana_counter = M.banana_counter + count
  M.bananas = M.bananas + count

  while M.banana_counter >= 100 do
    M.banana_counter = M.banana_counter - 100
    M.lives = M.lives + 1
  end
end

function M.add_dk_coin()
  M.dk_coins = M.dk_coins + 1
end

function M.add_life()
  M.lives = M.lives + 1
end

function M.take_damage()
  M.health = M.health - 1
  return M.health <= 0
end

function M.heal(amount)
  amount = amount or 1
  M.health = math.min(M.health + amount, 3)
end

function M.lose_life()
  M.lives = M.lives - 1
  M.health = 3
  return M.lives < 0
end

function M.add_score(points)
  M.score = M.score + points
end

function M.reset()
  M.health = 3
end

function M.draw_text(x, y, text)
  if not msg then return end
  msg.post("@system:", "gui", {
    text = text,
    pos = { x = x, y = y },
  })
end

function M.get_hud_data()
  return {
    lives = M.lives,
    bananas = M.bananas,
    dk_coins = M.dk_coins,
    health = M.health,
    score = M.score,
    breath = M.breath,
    is_swimming = M.is_swimming,
    mount_type = M.mount_type,
  }
end

return M
