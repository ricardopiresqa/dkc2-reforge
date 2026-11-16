-- KONG letters display ($097B, drawn by BEC8ED). Measured on hud-sprites-trace.csv
-- (hud_sprites_capture.lua, route-bot frames 2430-3461):
--   * a picked letter becomes the display sprite ($174, the letter item's sprite id) and
--     flies from its screen position to its slot, 1/8 of the way per frame (8.8);
--   * slots are x 93 + 18 * index, y 24 (the $42-$48 words, high byte y, low byte x);
--   * letters picked earlier slide in from y -6 at 2 px per frame;
--   * once the new letter is home they hold, then all slide up 2 px per frame and the
--     display goes away.
-- APPROXIMATIONS: the hold is 125 frames (121/130 measured on O/N); letters are drawn
-- with the first frame of their item animation (the HUD tiles are not exported).
local M = {}

local SLOT_X, SLOT_Y, SLOT_STEP, HIDDEN_Y, SLIDE, HOLD = 93, 24, 18, -6, 2, 125

function M.init()
  M.letters, M.flying, M.phase, M.timer = {}, nil, nil, 0
end

--- Letter `index` (1 K .. 4 G) picked at screen (x, y); `frame` = its item frame.
function M.collect(index, x, y, frame)
  if M.flying then  -- a second pick while one flies: the first lands at once
    local landed = M.letters[M.flying.index]
    landed.hidden, landed.y = false, SLOT_Y
  end
  M.letters[index] = { x = SLOT_X + SLOT_STEP * (index - 1), y = HIDDEN_Y, frame = frame, settled = false }
  for other, letter in pairs(M.letters) do
    if other ~= index and not M.phase then letter.y = HIDDEN_Y end  -- "out": slide back from where they are
  end
  M.flying = { index = index, x = x * 256, y = y * 256 }
  M.letters[index].hidden = true
  M.phase = "fly"
end

local function approach(value, target)  -- 8.8, 1/8 of the remaining distance
  local next_value = value + math.floor((target * 256 - value) / 8)
  if math.abs(target * 256 - next_value) < 384 then return target * 256, true end  -- fitted: home on frame 20
  return next_value, false
end

function M.update()
  if not M.phase then return end
  local all_home = true
  for _, letter in pairs(M.letters) do
    if M.phase == "out" then
      letter.y = letter.y - SLIDE
    elseif letter.y < SLOT_Y then
      letter.y = math.min(SLOT_Y, letter.y + SLIDE)
      all_home = false
    end
  end
  if M.flying then
    local letter = M.letters[M.flying.index]
    local home_x, home_y
    M.flying.x, home_x = approach(M.flying.x, letter.x)
    M.flying.y, home_y = approach(M.flying.y, SLOT_Y)
    if home_x and home_y then
      letter.hidden, letter.y, M.flying = false, SLOT_Y, nil
    else
      all_home = false
    end
  end
  if M.phase == "fly" and all_home then M.phase, M.timer = "hold", HOLD
  elseif M.phase == "hold" then
    M.timer = M.timer - 1
    if M.timer <= 0 then M.phase = "out" end
  elseif M.phase == "out" then
    local visible = false
    for _, letter in pairs(M.letters) do if letter.y > HIDDEN_Y then visible = true end end
    if not visible then M.phase = nil end
  end
end

--- draw(sprite, left, top, width, height) in screen space (origin = letter position).
function M.each_visible(draw)
  if not M.phase then return end
  local function one(frame, x, y)
    draw(frame.sprite, x - frame.origin_x, y - frame.origin_y, frame.width, frame.height)
  end
  for _, letter in pairs(M.letters) do
    if not letter.hidden then one(letter.frame, letter.x, letter.y) end
  end
  if M.flying then
    one(M.letters[M.flying.index].frame, math.floor(M.flying.x / 256), math.floor(M.flying.y / 256))
  end
end

M.init()
return M
