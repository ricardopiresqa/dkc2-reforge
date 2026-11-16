-- Banana coin counter ($097D, drawn by BEC92F). Measured on coin-route-t1/t2.csv
-- (coin_probe_capture.lua, coin at 2664/328 raw picked on active frame 2670):
--   * the picked coin becomes the HUD coin ($15C, anim $1C1 = the item's spin) and flies
--     from its screen position to (112, 32), 1/8 of the way per frame (8.8), home on +22;
--   * the count digit (tiles $1CC+d / $1D6+d, 8x16) slides in at x 132 from y -16 at
--     2 px per frame (y 12 on +14) and counts the new coin 3 frames after the coin is home;
--   * both hold, then from +218 slide up 2 px per frame and the display goes away.
-- APPROXIMATIONS: within 1 px of the capture during the flight (start subpixel unknown);
-- the digit leaves one frame earlier than measured (+218, not +219); two-digit counts
-- use the lives layout (x -5 / +3) and a second pick restarts the flight (not captured).
local M = {}

local HOME_X, HOME_Y, DIGIT_X, DIGIT_Y, DIGIT_START, SLIDE = 112, 32, 132, 12, -16, 2
local COUNT_DELAY, OUT_FRAME = 3, 218

function M.init(count)
  M.count, M.shown, M.coin, M.phase, M.frame = count or 0, count or 0, nil, nil, 0
end

--- A banana coin picked at screen (x, y); `frames` = its item animation (spin).
function M.collect(x, y, frames)
  M.count = M.count + 1
  M.coin = { x = x * 256, y = y * 256, home = false, frames = frames }
  M.digit_y = M.phase and M.digit_y or DIGIT_START
  M.phase, M.frame, M.counted = "in", 0, nil
end

local function approach(value, target)  -- as the KONG letters (original_kong_hud.lua)
  local next_value = value + math.floor((target * 256 - value) / 8)
  if math.abs(target * 256 - next_value) < 384 then return target * 256, true end
  return next_value, false
end

function M.update()
  if not M.phase then return end
  M.frame = M.frame + 1
  local coin = M.coin
  if M.frame >= OUT_FRAME then
    M.phase = "out"
    coin.y, M.digit_y = coin.y - SLIDE * 256, M.digit_y - SLIDE
    if coin.y < -16 * 256 and M.digit_y < -16 then M.phase, M.coin = nil, nil end
    return
  end
  M.digit_y = math.min(DIGIT_Y, M.digit_y + SLIDE)
  if not coin.home then
    local home_x, home_y
    coin.x, home_x = approach(coin.x, HOME_X)
    coin.y, home_y = approach(coin.y, HOME_Y)
    if home_x and home_y then coin.home, M.counted = true, M.frame + COUNT_DELAY end
  elseif M.counted and M.frame >= M.counted then
    M.shown, M.counted = M.count, nil
  end
end

--- draw(sprite, left, top, width, height) in screen space.
function M.each_visible(draw, digit_sprites)
  if not M.phase then return end
  local coin = M.coin
  local frame = coin.frames[math.floor(M.frame / 4) % #coin.frames + 1]
  draw(frame.sprite, math.floor(coin.x / 256) - frame.origin_x, math.floor(coin.y / 256) - frame.origin_y,
       frame.width, frame.height)
  local shown = math.min(M.shown, 99)
  if shown >= 10 then
    draw(digit_sprites[math.floor(shown / 10) + 1], DIGIT_X - 5, M.digit_y, 8, 16)
    draw(digit_sprites[shown % 10 + 1], DIGIT_X + 3, M.digit_y, 8, 16)
  else
    draw(digit_sprites[shown + 1], DIGIT_X, M.digit_y, 8, 16)
  end
end

M.init()
return M
