-- Pirate Panic walkers (Neek, Klomp): the shared walker routine B3A436 translated from
-- the disassembly and checked field by field against route-bot-walkers.csv.
-- Data (spawn fields, species table, F9 animation ops, poses): data/original/pirate/walkers.lua
-- (tools/replay-compare/export_walkers.py). Positions are source WRAM units: x/y in
-- 1/256 px; port coordinates = source - 256.
-- Per frame: animation (callbacks, per-frame routine $3E) -> controller ($52: Neek $22
-- turns at walls BEF812, Klomp $23 patrols origin $42 +/- range $46 BEF848) -> physics
-- BEF7CE (move, level bounds BEF7A3, accel BEFB68, gravity BEFB72, ground).
-- Ground: the feet follow the original column surfaces (collision.surface_at); the
-- terrain routine B8D4F8 itself (walls, edges) is not translated yet.
-- Defeat (stomp, B3A539): faces the player, vx = -/+$100 against the player's facing,
-- vy = -$800, move type 4 (no ground, no accel, gravity without cap).
local M = { active = false }

local SOURCE = 256
local FLIP = 0x4000
-- Defeated (move type 4: BEF0CB + BEFB68 + BEFB72): the fall cap comes from the table at
-- [$8E]+2; observed $0C00 in route-bot-walkers.csv (frames 614-617), table not traced.
local DEFEAT_MAX_FALL = 0x0C00
local data
local walkers = {}
local groups = {}  -- level `type` -> members, while its controller ($8C) lives

local function signed(value)
  return value >= 0x8000 and value - 0x10000 or value
end

function M.init(enabled, surface_at, steep_tile, objects)
  local ok_boxes, hitboxes = pcall(function() return require("data.original.pirate.hitboxes") end)
  M.hitboxes = ok_boxes and hitboxes or nil
  M.active, walkers, groups, M.surface_at, M.steep_tile = false, {}, {}, surface_at, steep_tile
  if not enabled then return end
  local ok, walker_data = pcall(function() return require("data.original.pirate.walkers") end)
  local ok_level, level = pcall(function() return require("data.original.pirate.pirate_panic_level") end)
  if not (ok and ok_level) or type(walker_data) ~= "table" or type(level) ~= "table" then return end
  data = walker_data
  for _, object in ipairs(objects or level.objects or {}) do
    local spawn = data.spawns[object.param]
    if spawn and object.script == 1 then
      walkers[#walkers + 1] = { spawn = spawn, species = data.species[spawn.species],
                                home_x = object.x, feet_y = object.feet_y, group = object.type,
                                alive = false, defeated = false }
    end
  end
  M.active = #walkers > 0
end

local call

local function set_animation(walker, number)
  walker.animation, walker.pc, walker.per_frame = number, 1, nil
  M._run_ops(walker)
end

-- Execute ops from pc until a pose is shown (or the script holds). The frame counter
-- $38 accumulates (B9D115 adds the duration): after a hold it is -1, so that pose
-- lasts one frame less (route-bot-walkers.csv frames 582-583).
function M._run_ops(walker, carry)
  local script = data.animations[walker.animation]
  for _ = 1, 64 do
    local op = script[walker.pc]
    walker.pc = walker.pc + 1
    local kind = op[1]
    if kind == "frame" then
      walker.pose, walker.timer = op[3], op[2] + (carry or 0)
      return
    elseif kind == "loop" then
      walker.pc = 1
    elseif kind == "switch" then
      return set_animation(walker, op[3])
    elseif kind == "per_frame" then
      walker.per_frame = op[2]
      call(walker, op[2])
    elseif kind == "call" then
      call(walker, op[2])
    elseif kind == "wait" then
      if call(walker, op[2]) then  -- hold: re-evaluate on the next frame
        walker.pc, walker.timer = walker.pc - 1, 0
        return
      end
    elseif kind == "sound" then
      walker.sound = op[2]
    end
  end
  error("walker animation without pose: " .. tostring(walker.animation))
end

local function facing_mismatch(walker)  -- B9E566
  return walker.target ~= 0 and bit.band(bit.bxor(bit.rshift(bit.band(walker.target, 0xFFFF), 1),
                                                  walker.attributes), FLIP) ~= 0
end

call = function(walker, name)
  if name == "turn_check_161" then
    if facing_mismatch(walker) then set_animation(walker, 0x161) end
  elseif name == "squeak_turn_check_170" then
    if bit.band(M.clock or 0, 0x3F) == 0 then walker.sound = "neek_squeek" end
    if facing_mismatch(walker) then set_animation(walker, 0x170) end
  elseif name == "stop" then
    walker.vx = 0
  elseif name == "quarter_speed" then
    walker.vx = bit.arshift(walker.vx, 2)
  elseif name == "boost_speed" then
    walker.vx = walker.vx + bit.arshift(walker.vx, 1)
  elseif name == "flip" then
    walker.attributes = bit.bxor(walker.attributes, FLIP)
  elseif name == "hold_while_rising" then  -- B9E553: hold while vy < -$200
    return walker.vy < -0x200
  elseif name == "hold" then              -- B9D12B
    return true
  end
  return false
end

local function animate(walker)
  if walker.timer > 0 then
    walker.timer = walker.timer - 1
    if walker.timer == 0 then M._run_ops(walker) end
  else
    M._run_ops(walker, -1)  -- held by a wait op
  end
  if walker.per_frame and walker.timer > 0 then call(walker, walker.per_frame) end
end

local function accelerate(walker)  -- BEFB68 -> B8CF2C, step d/16 + d/64 (k = 8)
  local diff = walker.target - walker.vx
  local magnitude = math.abs(diff)
  local step = bit.rshift(magnitude, 4) + bit.rshift(magnitude, 6)
  if step == 0 then
    walker.vx = walker.target
  else
    walker.vx = walker.vx + (diff < 0 and -step or step)
  end
end

local function flip_patrol(walker)
  walker.target = -walker.target
  walker.last_target = walker.target  -- $48
end

local function patrol(walker)  -- BEF848 ($52 = $23, substate 1)
  local x = bit.rshift(walker.x, 8)
  if walker.wall then  -- BEF8B5: re-centre the range on the wall and walk away from it
    walker.wall = false
    if walker.last_target < 0 then
      walker.origin = math.max(x + bit.rshift(walker.range, 8), 0x100)
    else
      walker.origin = x - bit.band(walker.range, 0xFF)
    end
    walker.target = -walker.last_target
    walker.last_target = walker.target
    return
  end
  if walker.target < 0 then
    if not (walker.origin - bit.rshift(walker.range, 8) < x) then flip_patrol(walker) end
  elseif walker.origin + bit.band(walker.range, 0xFF) < x then
    flip_patrol(walker)
  end
end

-- Terrain (B8D4F8 not translated; behaviour from route-bot-walkers.csv): airborne, the
-- walker lands once its pixel row reached the surface before the move (frames
-- 1187-1188: y 254.20 -> 254.00), then vy = $0370 and $1E bit 0 is set; grounded, the
-- feet follow the column surface. Without a surface in reach it falls again.
local GROUND_VY, STEP_UP, STEP_DOWN = 0x0370, 8, 3

local function surface(walker, above, below)
  local x, y = bit.rshift(walker.x, 8) - SOURCE, bit.rshift(walker.y, 8) - SOURCE
  local feet = M.surface_at and M.surface_at(x, y - above, y + below)
  return feet and feet + SOURCE
end

local function ground(walker)
  if walker.grounded then
    local feet = surface(walker, STEP_UP, STEP_DOWN)
    if feet then
      walker.y, walker.vy = feet * 256, GROUND_VY
      return
    end
    walker.grounded = false
  else
    local feet = surface(walker, STEP_UP, 0)
    if feet then
      walker.y, walker.vy, walker.grounded = feet * 256, GROUND_VY, true
      return
    end
  end
  walker.y = walker.y + walker.vy
  walker.vy = math.min(walker.vy + walker.species.gravity, walker.species.max_fall)
end

-- HYPOTHESIS (B8D4F8 not translated): crossing into a 32 px terrain tile that is a
-- steep slope blocks the walker at the tile edge: x = edge.00, vx = $26 = 0 and the
-- wall flag ($1E bit 1) is set (Klomp, frame 2903: x B40.97 -> B40.00).
local function blocked(walker, before)
  local x_before, x_after = bit.rshift(before, 8) - SOURCE, bit.rshift(walker.x, 8) - SOURCE
  local tile_before, tile_after = math.floor(x_before / 32), math.floor(x_after / 32)
  if tile_before == tile_after or not M.steep_tile then return false end
  if not M.steep_tile(tile_after, bit.rshift(walker.y, 8) - SOURCE) then return false end
  local edge = (tile_after < tile_before and tile_before * 32 or tile_after * 32 - 1) + SOURCE
  walker.x, walker.vx, walker.target, walker.wall = edge * 256, 0, 0, true
  return true
end

local function physics(walker)  -- BEF7CE
  local before = walker.x
  walker.x = walker.x + walker.vx
  blocked(walker, before)
  local x = bit.rshift(walker.x, 8)
  if x < 0x108 then  -- BEF7A3: level left bound (right bound $0AFC + $F8 not reached here)
    walker.x, walker.vx = 0x108 * 256 + bit.band(walker.x, 0xFF), 0
  end
  accelerate(walker)
  ground(walker)
end

-- State 0 (B3A47C): animation B3B8A7, then movement BEF05C. State 1, defeated
-- (B3A50B): movement first, then animation.
local function step(walker)
  if walker.defeated then
    walker.x, walker.y = walker.x + walker.vx, walker.y + walker.vy
    walker.vy = math.min(walker.vy + walker.species.gravity, DEFEAT_MAX_FALL)
    animate(walker)
    return
  end
  animate(walker)
  if walker.spawn.move == 0x23 then
    patrol(walker)
    physics(walker)
  else  -- BEF812 ($52 = $22): a wall reverses the target saved before the physics
    local target = walker.target
    physics(walker)
    if walker.wall then walker.wall, walker.target = false, -target end
  end
end

local function spawn(walker)
  local s = walker.spawn
  walker.alive, walker.defeated = true, false
  walker.x, walker.y = (walker.home_x + SOURCE) * 256 + 0x80, (walker.feet_y + SOURCE) * 256 + 0x80
  walker.vx, walker.vy, walker.target, walker.grounded = 0, 0, signed(s.target), false
  walker.attributes, walker.range = s.attributes, s.range
  walker.origin = walker.home_x + SOURCE  -- BEF838 latches $42 and $48 on the first frame
  walker.last_target, walker.wall = walker.target, false
  set_animation(walker, s.animation)
  animate(walker)  -- spawn frame: first animation step (trace: counter 3 of 4)
  if s.move == 0x23 then patrol(walker) end
  physics(walker)  -- the first frame runs the controller (origin latch + one accel step)
end

-- Sprite lifecycle (BBBB8C / spawner BBB622 / group controller BBBC96), x axis only
-- (the vertical half of each box needs camera y, not in the route-bot captures).
-- BBBB07 box test: inside when cam - lo < p <= cam - lo + span (DATA_BBB92F).
local HOME_BOX = { 0x20, 0x140 }    -- box 0: level object position (spawn, keep alive)
local SPRITE_BOX = { 0x28, 0x150 }  -- box 0 + 8: sprite position ($58 type 1 / $F)

local function inside(position, camera_x, box)
  return position > camera_x - box[1] and position <= camera_x - box[1] + box[2]
end

local function in_range(walker, camera_x)  -- BBBAAB ($58 type 1): sprite or home
  return inside(bit.rshift(walker.x, 8) - SOURCE, camera_x, SPRITE_BOX)
      or (not walker.defeated and inside(walker.home_x, camera_x, HOME_BOX))
end

--- One game frame. camera_x: port camera of the previous frame. frozen: hit-stop.
-- A level object spawns when its home is in box 0. Objects sharing a non-zero level
-- `type` form a group: the first member in range creates the controller (sprite $8C)
-- and every member spawns; members are not range-checked on their own while the
-- controller lives, and the controller despawns them all once no live member is in
-- range. A walker removed by the range test respawns later; a defeated one is
-- marked dead in $7E7A12 (bit 13) until the level restarts (M.init).
function M.update(camera_x, frozen, clock)
  if not M.active or frozen then return end
  M.clock = clock
  for _, walker in ipairs(walkers) do
    if walker.alive then
      if walker.stomped then
        walker.stomped = false  -- the contact frame runs no movement (B3A4C2)
      else
        step(walker)
      end
      if walker.sound == "neek_squeek" then  -- B9E5AD every 64 frames; only on screen
        local screen_x = bit.rshift(walker.x, 8) - SOURCE - camera_x
        if screen_x > 0 and screen_x < 256 then M.sound_request = "neek_squeek" end
      end
      walker.sound = nil
      if (walker.group == 0 or walker.defeated) and not in_range(walker, camera_x) then
        walker.alive = false
      end
    end
  end
  for group, members in pairs(groups) do
    local keep = false
    for _, walker in ipairs(members) do
      if walker.alive and not walker.defeated and in_range(walker, camera_x) then keep = true end
    end
    if not keep then
      for _, walker in ipairs(members) do
        if not walker.defeated then walker.alive = false end
      end
      groups[group] = nil
    end
  end
  for _, walker in ipairs(walkers) do
    if not walker.alive and not walker.defeated and inside(walker.home_x, camera_x, HOME_BOX) then
      if walker.group == 0 then
        spawn(walker)
      elseif not groups[walker.group] then
        local members = {}
        for _, member in ipairs(walkers) do
          if member.group == walker.group then
            members[#members + 1] = member
            if not member.alive and not member.defeated then spawn(member) end
          end
        end
        groups[walker.group] = members
      end
    end
  end
end

--- Stomp from above (B3A539). player_facing_left: player's $12 bit $4000.
function M.defeat(walker, player_facing_left)
  walker.defeated, walker.stomped = true, true
  walker.attributes = bit.bor(bit.band(walker.attributes, bit.bnot(FLIP)), player_facing_left and 0 or FLIP)
  walker.vx = player_facing_left and 0x100 or -0x100
  walker.target, walker.vy = walker.vx, -0x800
  set_animation(walker, walker.species.defeat)
end

-- Player contact, translated from the walker state-0 pass (B3A464 -> BCFB58 -> BEBE80):
-- boxes from the pose hitbox table DATA_BCB600 (BCFC4D: {dx, dy, w, h}, mirrored by $12
-- bit $4000), overlap test BCFD61 (inclusive edges; without an attack box the player's
-- outer box is its body box, so a touch sets $09F5 bit 4), dispatch BEBF18 by the
-- player's class ($41 >> 5: 0 on the ground -> BEC01F, 1 airborne -> BEC15E) with the
-- species contact word $5528 (DATA_FF027E/0294 +8):
--   airborne and bottom - enemy top < $20 and vy >= -$140 -> stomp (player action $1B,
--   walker defeated, B3A4C2); otherwise BEC01F: $5528 & 7 = 0 with bits 2/4 -> hurt
--   (BEC447; skipped while the player is invulnerable, $30 bit $80).
-- Evidence: route-bot-contact.csv / route-bot-contact2.csv (enemy boxes 35/35, player
-- box at 565/937, actions $1B at the stomps and hurt at 1259/2172/2759).
-- Not translated: the BEBE42 player-state gate ($20 flag of DATA_B8961E) and attack
-- boxes (roll/cartwheel, $09AB).
local CONTACT_WORD = 0x5528

local function box(pose, x, y, flipped)  -- BCFC4D: left, top, right, bottom
  local hit = M.hitboxes and M.hitboxes[pose]
  if not hit then return nil end
  local left = flipped and x - hit[1] - hit[3] or x + hit[1]
  return left, y + hit[2], left + hit[3], y + hit[2] + hit[4]
end

M.box = box

--- BCFD61 + BEBF18 for one player box (pl, pt, pr, pb) and one enemy box: nil (no
-- touch), "stomp" or "hurt".
function M.decide(pl, pt, pr, pb, el, et, er, eb, airborne, vy_raw)
  if not (pr >= el and er >= pl and eb >= pt and pb >= et) then return nil end
  if airborne and pb - et - 0x20 < 0 and vy_raw + 0x140 >= 0 and bit.band(CONTACT_WORD, 0x18) == 0x08 then
    return "stomp"
  end
  if bit.band(CONTACT_WORD, 7) == 0 then return "hurt" end
  return nil
end

--- Contacts this frame, before the walkers move (call ahead of M.update).
-- x, feet: player position after its move (port pixels: source - 256); pose: the
-- player's pose before this frame's animation step; vy_raw: source units (1/256 px).
-- Returns a list of { walker = w, kind = "stomp" | "hurt" } in slot order.
function M.contact(x, feet, pose, facing_left, vy_raw, airborne)
  local events = {}
  if not M.active then return events end
  local pl, pt, pr, pb = box(pose, x, feet, facing_left)
  if not pl then return events end
  for _, walker in ipairs(walkers) do
    if walker.alive and not walker.defeated then
      local el, et, er, eb = box(walker.pose, bit.rshift(walker.x, 8) - SOURCE,
                                 bit.rshift(walker.y, 8) - SOURCE, bit.band(walker.attributes, FLIP) ~= 0)
      local kind = el and M.decide(pl, pt, pr, pb, el, et, er, eb, airborne, vy_raw)
      if kind then events[#events + 1] = { walker = walker, kind = kind } end
    end
  end
  return events
end

--- Calls draw(sprite, left, top, width, height, flipped, walker) per live walker.
function M.each_visible(draw)
  if not M.active then return end
  for _, walker in ipairs(walkers) do
    if walker.alive then
      local pose = data.poses[walker.pose]
      local x, y = bit.rshift(walker.x, 8) - SOURCE, bit.rshift(walker.y, 8) - SOURCE
      local flipped = bit.band(walker.attributes, FLIP) ~= 0
      local left = flipped and x - (pose.width - pose.origin_x) + 1 or x - pose.origin_x
      draw(pose.sprite, left - 1, y - pose.origin_y, pose.width, pose.height, flipped, walker)
    end
  end
end

function M.walkers() return walkers end

return M
