-- Partner Kong: release from a broken DK barrel, follow, swap (SELECT) and the lost-Kong
-- hand-over. Measured on route-bot-trace.csv (slot 1, sprite 232 = Dixie):
--   * release (frames 2042-2074): the Kong pops out where the carried barrel broke with
--     the jump arc RELEASE_DY (animation $06) and lands;
--   * follow (2078-2174): the follower stands on the leader's position 31 frames earlier
--     (100/210 frames within 1 px, single peak), with the follower animations $3B walk,
--     $3D run, $3E jump;
--   * hit (2174-2240): the leader plays $29 for 30 frames, then runs off at 4 px/frame
--     ($3D); the follower holds 36 frames, runs to the hit spot and becomes the leader.
-- SELECT swap (swap-route-t1.csv, SELECT on S): the follower leads at once from its own
-- spot playing $49; the old leader holds its spot, then on S+45 hops from 59 px above the
-- new leader (vy -624, gravity $50, anim $4B) and lands behind it; from S+58 the new
-- leader walks to the old spot at 1.75 px/frame, plays $4A there and control returns.
-- APPROXIMATIONS: the release drifts toward the leader at 12/32 px per frame; catching
-- up moves 3 px/frame; the swap timing was measured Dixie -> Diddy only (the reverse
-- reuses it); the hop lands on the floor under the new leader's spot;
-- after a death the level restarts with Diddy alone.
-- Team throw (team-throw-probe.csv, team_throw_capture.lua): A makes the partner jump on
-- ($40, 17 frames) and ride at the leader's position + the $8A frame's dx/dy with the
-- frame's pose2; Y plays $26 and 19 frames later launches it ($27) 16 px above the
-- feet at vx 3000/256 (x 15/16 per frame), vy -400/256, gravity 112/256; it lands ($28)
-- and waits. APPROXIMATIONS: the mount arc is a 20 px parabola; after landing it waits
-- 30 frames, then catches up and follows again; a thrown Kong defeats enemies it touches.
-- Up-throw (upthrow-route-t2..t6.csv, UP held on Y): launched 24 px above the leader's
-- feet at vx 0, vy $F880, gravity $40; the leader hangs in the air while the partner is
-- thrown (t5/t6). A thrown partner touching a barrel cannon gets in (enter_cannon).
-- APPROXIMATIONS: the leader also hangs on the forward throw (only up-throws were taken
-- in the air); the partner stays hidden in the cannon until the area changes (the
-- original shoots it one frame behind the leader).
local original_animation = require("main.original_animation")
local original_motion = require("main.original_motion")
local collision = require("main.collision")

local M = { present = false, leader = "diddy" }

local DELAY, CATCH_SPEED = 31, 3
local RELEASE_DY = { 0, -12, -17, -22, -25, -29, -33, -37, -38, -42, -43, -44, -46, -47, -47, -47, -47, -47,
                     -45, -44, -42, -40, -37, -35, -31, -28, -23, -19, -15, -9, -3, 2, 9 }
local HURT_FRAMES, HOLD_FRAMES, RUN_SPEED, RUNNER_LIFE = 30, 36, 4, 150
local TAG_HOP, TAG_HOP_DY, TAG_HOP_VY, TAG_HOP_GRAVITY = 45, 59, -624 / 256, 80 / 256
local TAG_WALK, TAG_WALK_SPEED, TAG_END_HOLD = 58, 448 / 256, 3

local function merged(base, extra)
  local scripts, poses = {}, {}
  for _, source in ipairs({ base, extra }) do
    for key, value in pairs(source.scripts) do scripts[key] = value end
    for key, value in pairs(source.poses) do poses[key] = value end
  end
  return { scripts = scripts, poses = poses }
end

local DATA = {
  diddy = merged(require("data.original.pirate.animation_scripts"),
                 require("data.original.pirate.diddy_follower_animation")),
  dixie = require("data.original.pirate.dixie_animation"),
}

local function other(kong) return kong == "diddy" and "dixie" or "diddy" end

local history, follower, vm, runner, release, swap, team, tag
local MOUNT_FRAMES, LAUNCH_FRAME, THROW_END, LANDED_WAIT = 17, 19, 35, 30
local THROW_VX, THROW_VY, THROW_GRAVITY = 3000 / 256, -400 / 256, 112 / 256
local UP_VY, UP_GRAVITY, UP_LAUNCH_DY, FLY_LIMIT = -1920 / 256, 64 / 256, 24, 180
local function still() return { vel_x = 0, vel_y = 0, grounded = true, jump_windup = 0, run_held = false } end
local function set_mode(machine, mode)
  if machine.forced ~= mode then machine.force(mode, still()) end
end

-- `keep` = same visit (area change): the partner stays.
function M.init(keep)
  if not keep then M.present, M.leader = false, "diddy" end
  M.hidden = false
  history, follower, runner, release, swap, team, tag = {}, nil, nil, nil, nil, nil, nil
  original_animation.set_data(DATA[M.leader]); original_motion.set_kong(M.leader)
  if M.present then
    vm = original_animation.new(DATA[other(M.leader)])
    vm.init(true, still())
  end
end

--- Data for the leader's VM (main/original_animation.lua starts with Diddy's).
function M.leader_data() return DATA[M.leader] end

local function new_vm(kong, mode)
  local machine = original_animation.new(DATA[kong])
  machine.init(true, still())
  machine.force(mode, still())
  return machine
end

--- A DK barrel broke at (x, feet): the missing Kong pops out.
function M.release(x, feet)
  if M.present then return false end
  M.present = true
  vm = new_vm(other(M.leader), 0x06)
  follower = { x = x, feet = feet, dir = 1, catching = true }
  release = { frame = 1, x = x, feet = feet }
  return true
end

--- Leader hit with a partner: starts the hand-over. Returns false when there is none.
function M.lose(player)
  if not M.present or swap then return false end
  release, team, tag = nil, nil, nil  -- hit while the partner drops in, rides, flies or tags
  runner = { vm = new_vm(M.leader, 0x29), x = player.pos_x, feet = player.pos_y + 24, dir = player.direction,
             frame = 0 }
  swap = { frame = 0, x = player.pos_x, feet = player.pos_y + 24 }
  return true
end

--- A: the partner jumps on the leader's back.
function M.team_up(player)
  if not M.present or swap or release or team or tag or not follower or not player.grounded or player.carrying then
    return
  end
  team = { phase = "mount", frame = 0, x0 = follower.x, feet0 = follower.feet }
  set_mode(vm, 0x40)
end

--- Y while carrying the partner: throw it. Returns true when the press was used.
function M.throw(player, up)
  if not team or team.phase ~= "carried" then return false end
  team.phase, team.frame, team.thrown, team.up = "throw", 0, 0, up
  original_animation.force(0x26, player)
  return true
end

--- Leader carries the partner (team-up leader animations).
function M.carried() return team ~= nil and (team.phase == "mount" or team.phase == "carried" or team.phase == "throw") end

--- Any team-throw phase or the hand-over: Y belongs to the team, not to boxes/cartwheels.
function M.owns_y() return team ~= nil or swap ~= nil end

--- True while the hand-over runs (player input and physics frozen).
function M.busy() return swap ~= nil end

--- True while the leader hangs in the air throwing (the partner not yet landed).
function M.hanging() return team ~= nil and (team.phase == "throw" or team.phase == "flying") end

--- A thrown partner got into a barrel cannon at (x, feet): it waits there, hidden.
function M.enter_cannon(x, feet)
  if original_animation.forced == 0x26 then original_animation.release() end
  team, M.hidden, history = nil, true, {}
  follower.x, follower.feet, follower.catching = x, feet, false
end

--- SELECT: the follower takes the lead from its spot (the tag sequence, see the header).
function M.swap(player)
  if not M.present or swap or release or team or tag then return end
  local old_x, old_feet, old_dir = player.pos_x, player.pos_y + 24, player.direction
  M.leader = other(M.leader)
  original_animation.set_data(DATA[M.leader]); original_motion.set_kong(M.leader)
  player.pos_x, player.pos_y, player.vel_x, player.vel_y = follower.x, follower.feet - 24, 0, 0
  original_animation.force(0x49, player)
  original_animation.update(player)  -- no frame with the other Kong's pose id
  vm = new_vm(other(M.leader), 1)
  tag = { frame = 0, old_x = old_x }
  follower = { x = old_x, feet = old_feet, dir = old_dir, catching = false }
  history = {}
end

--- True while the SELECT swap plays (the leader's input and physics are held).
function M.tagging() return tag ~= nil end

local function update_tag(player)
  tag.frame = tag.frame + 1
  if tag.frame == TAG_HOP then  -- the old leader hops over to the new one's spot
    follower.x, follower.feet, tag.vy = player.pos_x, player.pos_y + 24 - TAG_HOP_DY, TAG_HOP_VY
    tag.ground = player.pos_y + 24
    set_mode(vm, 0x4B)
  elseif tag.vy then
    follower.feet, tag.vy = follower.feet + tag.vy, tag.vy + TAG_HOP_GRAVITY
    if tag.vy > 0 and follower.feet >= tag.ground then
      follower.feet, tag.vy = tag.ground, nil
      set_mode(vm, 1)
    end
  end
  if tag.frame >= TAG_WALK and not tag.arrived then
    local dx = tag.old_x - player.pos_x
    player.direction = dx < 0 and -1 or 1
    player.pos_x = player.pos_x + math.max(-TAG_WALK_SPEED, math.min(TAG_WALK_SPEED, dx))
    if math.abs(dx) <= TAG_WALK_SPEED then
      tag.arrived = tag.frame
      original_animation.force(0x4A, player)
    end
  elseif tag.arrived and tag.frame >= tag.arrived + TAG_END_HOLD and not tag.vy then
    original_animation.release()
    history, tag = { { x = follower.x, feet = follower.feet, dir = follower.dir, grounded = true } }, nil
  end
  vm.update(still())
end

-- One team-throw frame; returns true when it owns the follower this frame.
local function update_team(player, hit)
  team.frame = team.frame + 1
  if team.thrown then  -- the leader's $26 lasts THROW_END frames, landing or not
    team.thrown = team.thrown + 1
    if team.thrown >= THROW_END and original_animation.forced == 0x26 then original_animation.release() end
  end
  local feet = player.pos_y + 24
  if team.phase == "mount" then
    local t = math.min(1, team.frame / MOUNT_FRAMES)
    follower.x = team.x0 + (player.pos_x - team.x0) * t
    follower.feet = team.feet0 + (feet - team.feet0) * t - 80 * t * (1 - t)
    if team.frame >= MOUNT_FRAMES then team.phase = "mount_done" end
  end
  if team.phase == "mount_done" then team.phase = "carried" end
  if team.phase == "carried" or (team.phase == "throw" and team.frame < LAUNCH_FRAME) then
    follower.x = player.pos_x + (original_animation.held_dx or 0) * player.direction
    follower.feet = feet + (original_animation.held_dy or 0)
    follower.dir = player.direction
  elseif team.phase == "throw" then
    team.phase = "flying"
    if team.up then
      team.vx, team.vy = 0, UP_VY
      follower.feet = feet - UP_LAUNCH_DY
    else
      team.vx, team.vy = THROW_VX * player.direction, THROW_VY
      follower.feet = feet - 16
    end
    set_mode(vm, 0x27)
  end
  if team.phase == "throw" and team.frame == LAUNCH_FRAME then return true end
  if team.phase == "flying" then
    local new_x, wall = collision.resolve_x(follower.x, follower.feet - 24, 12, 24, team.vx)
    follower.x = new_x
    local next_feet = follower.feet + team.vy
    local floor = team.vy > 0 and collision.surface_at(math.floor(follower.x), math.floor(follower.feet),
                                                       math.floor(next_feet) + 1)
    follower.feet = floor or next_feet
    team.vx, team.vy = team.vx * 15 / 16, team.vy + (team.up and UP_GRAVITY or THROW_GRAVITY)
    if hit and hit(follower.x, follower.feet) == "cannon" then return true end
    -- shortcut: a throw into a pit ends after FLY_LIMIT frames or below the level (the
    -- original's pit handling is not captured), so the hanging leader is never stuck.
    local lost = team.frame > LAUNCH_FRAME + FLY_LIMIT or follower.feet > (collision.get_fall_limit() or math.huge)
    if floor or wall or lost then
      team.phase, team.frame = "landed", 0
      set_mode(vm, 0x28)
    end
  elseif team.phase == "landed" then
    if team.frame >= LANDED_WAIT then
      if original_animation.forced == 0x26 then original_animation.release() end
      team, history, follower.catching = nil, { history[#history] }, true
      return false
    end
  end
  return true
end

local function follow_mode(dx, dy, grounded)
  if not grounded or math.abs(dy) > 0.5 then return 0x3E end
  if math.abs(dx) > 2.5 then return 0x3D end
  if math.abs(dx) > 0.05 then return 0x3B end
  return 1
end

local function update_runner()
  if not runner then return end
  runner.frame = runner.frame + 1
  if runner.frame == HURT_FRAMES then runner.vm.force(0x3D, still()) end
  if runner.frame > HURT_FRAMES then runner.x = runner.x + RUN_SPEED * runner.dir end
  runner.vm.update(still())
  if runner.frame >= RUNNER_LIFE then runner = nil end
end

--- `hit(x, feet)`: optional, called each frame a thrown partner flies (enemy contact).
function M.update(player, hit)
  update_runner()
  if not M.present then return end
  if not follower then  -- area change with a partner: it arrives with the leader
    follower = { x = player.pos_x, feet = player.pos_y + 24, dir = player.direction, catching = false }
  end
  local entry = { x = player.pos_x, feet = player.pos_y + 24, dir = player.direction, grounded = player.grounded }
  history[#history + 1] = entry
  if #history > DELAY + 1 then table.remove(history, 1) end
  local x0, feet0 = follower.x, follower.feet
  if tag then update_tag(player); return end
  if team and update_team(player, hit) then
    if team and team.phase ~= "carried" and team.phase ~= "throw" then
      vm.update({ vel_x = 0, vel_y = 0, grounded = team.phase == "landed", jump_windup = 0, run_held = false })
    end
    return
  end
  if release then
    local dy = RELEASE_DY[release.frame]
    follower.x = follower.x + (player.pos_x > follower.x and 0.375 or -0.375)
    if dy then follower.feet = release.feet + dy end
    release.frame = release.frame + 1
    if not dy or release.frame > #RELEASE_DY then release = nil end
  elseif swap then
    swap.frame = swap.frame + 1
    if swap.frame > HOLD_FRAMES then
      local dx = swap.x - follower.x
      follower.x = follower.x + math.max(-RUN_SPEED, math.min(RUN_SPEED, dx))
      follower.dir = dx < 0 and -1 or 1
      if math.abs(dx) <= RUN_SPEED then  -- reached the hit spot: the partner leads
        M.leader, M.present, swap = other(M.leader), false, nil
        original_animation.set_data(DATA[M.leader]); original_motion.set_kong(M.leader)
        player.direction = follower.dir
        original_animation.update(player)
        return
      end
    end
  else
    local target = history[1]
    if follower.catching then
      local dx = target.x - follower.x
      follower.x = follower.x + math.max(-CATCH_SPEED, math.min(CATCH_SPEED, dx))
      follower.feet = target.feet
      if math.abs(dx) <= 1 then follower.catching = false end
      if dx ~= 0 then follower.dir = dx < 0 and -1 or 1 end
    else
      follower.x, follower.feet, follower.dir = target.x, target.feet, target.dir
    end
  end
  local dx, dy = follower.x - x0, follower.feet - feet0
  if not release and not (swap and swap.frame <= HOLD_FRAMES) then
    set_mode(vm, follow_mode(dx, dy, history[1].grounded or follower.catching))
  end
  vm.update({ vel_x = dx * 60, vel_y = dy * 60, grounded = not release, jump_windup = 0, run_held = false })
end

--- QA trace: follower x (nil when absent) and the leader's name.
function M.debug() return M.present and follower and follower.x or nil, M.leader end

--- draw(animation, x, feet, direction) for the follower and a Kong running off.
function M.each_visible(draw)
  if runner then
    local animation = runner.vm.get_animation()
    if animation then draw(animation, runner.x, runner.feet, runner.dir) end
  end
  if M.present and follower and not M.hidden then
    local animation = vm.get_animation()
    if team and (team.phase == "carried" or (team.phase == "throw" and team.frame < LAUNCH_FRAME)) then
      local pose = DATA[other(M.leader)].poses[original_animation.pose2 or -1]
      animation = pose and pose.animation  -- the leader's $8A frame picks the rider's pose
    end
    if animation then draw(animation, follower.x, follower.feet, follower.dir) end
  end
end

return M
