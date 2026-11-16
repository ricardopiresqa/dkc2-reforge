local M = {}

M.stages = {
  -- Beginner (1-3)
  {
    id = "bonus_1",  name = "BANANA BONANZA",
    time_limit = 20, target_bananas = 8,
  },
  {
    id = "bonus_2",  name = "QUICK PICK",
    time_limit = 15, target_bananas = 6,
  },
  {
    id = "bonus_3",  name = "FRENZY",
    time_limit = 25, target_bananas = 10,
  },
  -- Intermediate (4-7)
  {
    id = "bonus_4",  name = "SPEED RUN",
    time_limit = 10, target_bananas = 5,
  },
  {
    id = "bonus_5",  name = "BUNCH HUNTER",
    time_limit = 18, target_bananas = 7,
  },
  {
    id = "bonus_6",  name = "TIGHT SQUEEZE",
    time_limit = 12, target_bananas = 4,
  },
  {
    id = "bonus_7",  name = "COIN RUSH",
    time_limit = 15, target_bananas = 10,
  },
  -- Advanced (8-11)
  {
    id = "bonus_8",  name = "TWITCH REFLEX",
    time_limit = 8,  target_bananas = 6,
  },
  {
    id = "bonus_9",  name = "BANANA DELUGE",
    time_limit = 30, target_bananas = 15,
  },
  {
    id = "bonus_10", name = "PRECISION PICK",
    time_limit = 20, target_bananas = 12,
  },
  {
    id = "bonus_11", name = "HARVEST MOON",
    time_limit = 12, target_bananas = 8,
  },
  -- Expert (12-15)
  {
    id = "bonus_12", name = "LIGHTNING ROUND",
    time_limit = 6,  target_bananas = 5,
  },
  {
    id = "bonus_13", name = "BANANA BLITZ",
    time_limit = 25, target_bananas = 18,
  },
  {
    id = "bonus_14", name = "SUPREME CHALLENGE",
    time_limit = 15, target_bananas = 14,
  },
  {
    id = "bonus_15", name = "DK'S FAVORITE",
    time_limit = 20, target_bananas = 20,
  },
}

function M.get_random()
  return M.stages[math.random(#M.stages)]
end

function M.get(id)
  for _, s in ipairs(M.stages) do
    if s.id == id then return s end
  end
  return M.stages[1]
end

return M
