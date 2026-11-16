-- Level-end goal sequence (LevelEndGoal $160, B3A275). Measured on goal-route-t4.csv (low
-- hit) and goal-route-t6.csv (high hit), frames counted from the hit H:
--   * the hit is "high" when the jump peaked at least $68 px above the goal (B3A2F6:
--     goal y - $0935 >= $68; $0935 = the highest feet y of the jump);
--   * H..H+7 everything holds; the target plays $2B4 once;
--   * the barrel at the pole's foot ($164) rises at vy -9 (high) / -7 (low) px, gravity
--     $50 per frame up to $800, never below its start; 96 px up it breaks (B39742: smoke
--     puff + the four shards) and frees the prize -- only the high hit gets that far (the
--     low one peaks ~75 px up and falls back, goal-route-t4.csv);
--   * the Kong bounces off at vx 392 (high) / 416 (low), vy -1536, gravity 112 (8.8),
--     then: low -> walks right at 3 px (anim $46) to goal x + 144, high -> stands (anim $45);
--   * the prize ($16C) falls from H+23 at vy 768, +80 per frame up to 2048, lands, becomes
--     the banana bunch at H+44 and is collected at H+81 (10 bananas);
--   * the level ends at H+127 (low) / H+411 (high).
-- APPROXIMATIONS: vx 392/416 are single measurements, always to the right, and the
-- bounce/walk-off ignore walls (flat stern deck here; the routine is not translated);
-- the partner Kong holds still; the $1CC sprite at the Kong (H+72..H+306) is not ported.
local collision = require("main.collision")
local original_items = require("main.original_items")
local original_effects = require("main.original_effects")
local original_animation = require("main.original_animation")

local M = { active = false }

local HOLD, HIGH_PEAK, BREAK_RISE = 8, 0x68, 96
local BARREL_GRAVITY, BARREL_MAX = 0x50 / 256, 0x800 / 256
local KONG_VY, KONG_GRAVITY, WALK_SPEED, WALK_TO = -1536 / 256, 112 / 256, 3, 144
local PRIZE_FALL, PRIZE_VY, PRIZE_GRAVITY, PRIZE_MAX = 23, 768 / 256, 80 / 256, 2048 / 256
local BUNCH_FRAME, COLLECT_FRAME = 44, 81
local END_LOW, END_HIGH = 127, 411

local state

function M.init()
  M.active, state = false, nil
end

--- The goal was hit by `player` (falling onto it); `peak_feet` = the jump's highest feet y.
function M.start(goal, player, peak_feet)
  local high = goal.feet_y - peak_feet >= HIGH_PEAK
  local children = goal.children or {}
  state = { goal = goal, high = high, frame = 0, children = children,
            barrel_start = children.barrel and children.barrel.feet_y,
            barrel_vy = high and -9 or -7, kong_vx = (high and 392 or 416) / 256 }
  M.active = true
  original_items.play(goal, 0x2B4, true)
  player.vel_x, player.vel_y = 0, 0
end

local function update_barrel(barrel)
  if not barrel or barrel.gone then return end
  state.barrel_vy = math.min(state.barrel_vy + BARREL_GRAVITY, BARREL_MAX)
  barrel.feet_y = math.min(barrel.feet_y + state.barrel_vy, state.barrel_start)
  if state.barrel_start - barrel.feet_y >= BREAK_RISE then
    original_items.remove(barrel)
    original_effects.spawn("smoke", barrel.x, barrel.feet_y)
    original_effects.spawn_shards(barrel.x, barrel.feet_y - 2)
    state.prize_free = true
  end
end

local function update_kong(player)
  if state.landed then
    if not state.high and player.pos_x < state.goal.x + WALK_TO then
      player.pos_x = math.min(player.pos_x + WALK_SPEED, state.goal.x + WALK_TO)
    end
    return
  end
  state.kong_vy = (state.kong_vy or KONG_VY) + KONG_GRAVITY
  player.pos_x, player.pos_y = player.pos_x + state.kong_vx, player.pos_y + state.kong_vy
  local feet = player.pos_y + 24
  local floor = state.kong_vy > 0 and collision.surface_at(math.floor(player.pos_x), feet - 8, feet + 8)
  if floor then
    player.pos_y, player.grounded, state.landed = floor - 24, true, true
    original_animation.force(state.high and 0x45 or 0x46, player)
  end
end

local function update_prize(prize)
  if not (prize and state.prize_free) or prize.gone then return end
  if state.frame > PRIZE_FALL and not state.prize_landed then
    prize.feet_y = prize.feet_y + (state.prize_vy or PRIZE_VY)
    state.prize_vy = math.min((state.prize_vy or PRIZE_VY) + PRIZE_GRAVITY, PRIZE_MAX)
    if prize.feet_y >= state.goal.feet_y then prize.feet_y, state.prize_landed = state.goal.feet_y, true end
  end
end

--- One frame. Returns "collect_bunch", entity at the collection frame, "done" at the end.
function M.update(player)
  if not M.active then return nil end
  state.frame = state.frame + 1
  if state.frame < HOLD then return nil end
  if state.frame == HOLD then original_animation.force(0x06, player) end
  update_kong(player)
  update_barrel(state.children.barrel)
  update_prize(state.children.prize)
  local prize = state.children.prize
  if state.prize_landed and state.frame == BUNCH_FRAME then
    original_items.play(prize, 0x2B2)
    prize.held = true
  elseif state.prize_landed and state.frame == COLLECT_FRAME and not prize.gone then
    original_items.remove(prize)
    return "collect_bunch", prize
  end
  if state.frame >= (state.high and END_HIGH or END_LOW) then
    M.active = false
    return "done"
  end
  return nil
end

--- QA: sequence frame, barrel feet y, prize feet y (nil when inactive).
function M.debug()
  if not state then return nil end
  local barrel, prize = state.children.barrel, state.children.prize
  return { state.frame, state.high and 1 or 0, barrel and not barrel.gone and barrel.feet_y or -1,
           prize and not prize.gone and prize.feet_y or -1 }
end

return M
