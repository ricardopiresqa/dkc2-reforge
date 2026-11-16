-- Pirate Panic green Klobbers: barrel $1AC + body $1E8 (data: data/original/pirate/klobber.lua,
-- tools/replay-compare/export_klobber.py). Positions in port pixels (source - 256).
-- Translated: wake rules (BEF50B: |dx| < x range and |dy| < y range, then $53 frames of
-- shaking; BEF4C8: a plain $04 countdown), the F9 scripts (emerge $1F4 -> run $1F5 ->
-- turn $1F6 -> hop/return $1F7, `$8D` frames drive body and barrel poses), run speed
-- DATA_FF0260+6 = $400 with the facing sign (B9E616), hop vy -$380 (B9E630), contact word
-- $020F: harmless on the ground, stomped from above (BEC15E -> barrel breaks, B3AB2B).
-- APPROXIMATIONS (route-bot-klobber.csv): the body's own movement routine is not
-- translated; the run lasts 147 frames, turns toward the player when it is behind, and the
-- barrel re-arms with the $22 = $96 countdown where it stopped.
local M = { active = false }

local RUN_SPEED, RUN_FRAMES, HOP_VY, GRAVITY, MAX_FALL = 0x400 / 256, 147, -0x380 / 256, 0x70 / 256, 0x800 / 256
local REARM_DELAY = 0x96
local FLIP = 0x4000
local data
local klobbers = {}

local WAKE = {  -- level object param -> wake rule (spawn fields $04 / $52)
  [216] = { x_range = 0xA0, y_range = 0x60, shake = 0x0F },  -- $04 = $A060, $52 = $0F0E
  [206] = { delay = 0x1E },                                  -- $04 = $1E, $52 = $0C
}

function M.init(enabled, surface_at, objects)
  M.active, klobbers, M.surface_at = false, {}, surface_at
  if not enabled then return end
  local ok, klobber_data = pcall(function() return require("data.original.pirate.klobber") end)
  local ok_level, level = pcall(function() return require("data.original.pirate.pirate_panic_level") end)
  if not (ok and ok_level) or type(klobber_data) ~= "table" then return end
  data = klobber_data
  for _, object in ipairs(objects or level.objects or {}) do
    if object.sprite == "Klobber" and WAKE[object.param] and object.script == 1 then
      klobbers[#klobbers + 1] = { wake = WAKE[object.param], home_x = object.x, feet_y = object.feet_y,
                                  alive = false, gone = false }
    end
  end
  M.active = #klobbers > 0
end

local function set_animation(k, number)
  k.animation, k.pc, k.per_frame = number, data.animations[number].start, nil
  M._run(k)
end

local calls = {}
calls.is_tnt = function() return false end  -- B9E5F0: $4E = 1 (plain barrel)
calls.emerged = function(k)                  -- B9E603: state >= 3 -> hop/return
  if k.state == "return" and k.animation ~= 0x1F7 then set_animation(k, 0x1F7); return true end
  return false
end
calls.run_frame = function(k)                -- B9E5F6: E603, then turn when $26 disagrees
  if calls.emerged(k) then return true end
  if (k.target < 0) ~= k.flipped and k.animation ~= 0x1F6 then set_animation(k, 0x1F6); return true end
  return false
end
calls.sound = function(k)                    -- B9E630 (hop): vy = -$380
  k.vy = HOP_VY
end
calls.flip = function(k) k.flipped = not k.flipped end

function M._run(k)
  local code = data.animations[k.animation].code
  for _ = 1, 64 do
    local op = code[k.pc]
    k.pc = op.next
    local kind = op.op
    if kind < 0x80 then
      k.barrel_pose, k.body_pose, k.timer = op.arg, nil, kind
      return
    elseif kind == 0x8D then
      k.body_pose, k.barrel_pose, k.timer = op.arg, op.arg2, op.dur
      return
    elseif kind == 0x80 then
      k.pc = data.animations[k.animation].start
    elseif kind == 0x82 then
      if k.animation == 0x1F7 then  -- body back inside: the barrel takes over (state 0)
        k.state, k.body_pose, k.returned = "barrel", nil, true
        return set_animation(k, 0x2E2)
      end
      k.pc = op.arg
    elseif kind == 0x83 then  -- B9D12B: hold this pose
      k.pc, k.timer = k.pc - 3, 0
      return
    elseif kind == 0x84 then
      k.per_frame = op.call
    elseif kind == 0x81 then
      local fn = calls[op.call == "unknown_e01b" and "flip" or op.call]
      if fn and fn(k) then return end
    elseif kind == 0x8F then
      local fn = calls[op.call]
      if fn and fn(k) then k.pc = op.arg2 end
    elseif kind == 0x90 then  -- B9E616 then switch: run toward the facing
      if op.arg2 == 0x1F5 then
        k.target = k.flipped and -RUN_SPEED or RUN_SPEED
        if k.state ~= "run" then k.state, k.run_timer = "run", RUN_FRAMES end
      elseif op.arg2 == 0x2E2 then
        k.state = "barrel"
      end
      return set_animation(k, op.arg2)
    end
  end
end

local function animate(k)
  if k.timer > 0 then
    k.timer = k.timer - 1
    if k.timer == 0 then M._run(k) end
  else
    M._run(k)
  end
  if k.per_frame and calls[k.per_frame] then calls[k.per_frame](k) end
end

local function physics(k)
  if k.state == "run" then
    if k.vx ~= k.target then k.vx = k.vx + (k.target - k.vx) * 0.5 end  -- k = 2: 2 then 4 px
    if math.abs(k.target - k.vx) < 0.05 then k.vx = k.target end
  end
  k.x = k.x + k.vx
  k.y = k.y + k.vy
  k.vy = math.min(k.vy + GRAVITY, MAX_FALL)
  local feet = M.surface_at and M.surface_at(math.floor(k.x), math.floor(k.y) - 8, math.floor(k.y) + 4)
  if feet and k.vy >= 0 then k.y, k.vy = feet, 0 end
end

local function reset(k)
  k.alive, k.state, k.x, k.y, k.vx, k.vy = true, "barrel", k.home_x, k.feet_y, 0, 0
  k.flipped, k.target, k.wait = true, 0, k.wake.delay  -- spawn attributes $6000: facing left
  set_animation(k, 0x2E2)
end

local function wake(k, player_x, player_y)
  if k.wait then
    k.wait = k.wait - 1
    return k.wait < 0
  end
  if math.abs(k.x - player_x) < k.wake.x_range and math.abs(k.y - player_y) < k.wake.y_range then
    k.wait = k.wake.shake
  end
  return false
end

--- One frame. camera_x as for the walkers; player position in port pixels (feet).
function M.update(camera_x, player_x, player_y, frozen)
  if not M.active or frozen then return end
  for _, k in ipairs(klobbers) do
    if not k.alive and not k.gone and k.home_x - camera_x <= 0x120 and k.home_x - camera_x > -0x20 then
      reset(k)
    elseif k.alive then
      if k.state == "barrel" then
        if wake(k, player_x, player_y) then
          M.sound_request = "klobber_emerge"
          k.state, k.flipped = "emerge", player_x < k.x
          set_animation(k, 0x1F4)
        end
      elseif k.state == "run" then
        k.run_timer = k.run_timer - 1
        -- APPROXIMATION: turn toward the player once it is 32 px behind (body routine untranslated)
        if math.abs(player_x - k.x) > 32 and (player_x < k.x) ~= (k.target < 0) and k.animation == 0x1F5 then
          k.target = -k.target
          M.sound_request = "klobber_turn"
        end
        if k.run_timer <= 0 then k.state, k.target, k.vx = "return", 0, 0 end
      end
      animate(k)
      physics(k)
      if k.returned then  -- re-arm where it stopped ($22 = $96 countdown)
        k.home_x, k.wait, k.returned = k.x, REARM_DELAY, false
      end
      local relative = k.x - camera_x
      local behind = k.state == "barrel" and -0x28 or -0x100
      if relative <= behind or relative > 0x228 then k.alive = false; k.home_x = k.x end
    end
  end
end

--- Stomps this frame (box of the body pose, else the barrel pose). Returns the klobber.
function M.stomp_check(box_fn, pl, pt, pr, pb, airborne, vy_raw)
  if not M.active then return nil end
  for _, k in ipairs(klobbers) do
    if k.alive then
      local pose = data.poses[k.body_pose or k.barrel_pose]
      if pose then
        local hit = pose.box
        local left = k.flipped and k.x - hit[1] - hit[3] or k.x + hit[1]
        local top = k.y + hit[2]
        local right, bottom = left + hit[3], top + hit[4]
        if pr >= left and right >= pl and bottom >= pt and pb >= top and airborne
            and pb - top - 0x20 < 0 and vy_raw + 0x140 >= 0 then
          return k
        end
      end
    end
  end
  return nil
end

function M.defeat(k)  -- B3AB2B: barrel breaks, Klobber removed
  k.alive, k.gone = false, true
end

--- draw(sprite, left, top, width, height, flipped) for the barrel then the body.
function M.each_visible(draw)
  if not M.active then return end
  for _, k in ipairs(klobbers) do
    if k.alive then
      for layer = 1, 2 do
        local pose_id
        if layer == 1 then pose_id = k.body_pose else pose_id = k.barrel_pose end
        local pose = pose_id and data.poses[pose_id]
        if pose then
          local x, y = math.floor(k.x), math.floor(k.y)
          local left = k.flipped and x - (pose.width - pose.origin_x) + 1 or x - pose.origin_x
          draw(pose.sprite, left - 1, y - pose.origin_y, pose.width, pose.height, k.flipped)
        end
      end
    end
  end
end

return M
