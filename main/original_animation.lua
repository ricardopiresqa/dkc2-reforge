-- Original F9 bytecode subset. Gameplay-affecting callbacks are not all ported.
-- Holding an object: each movement mode has its "holding" twin ($10/$11/$15-$18,
-- route-bot-trace.csv frames 1072-1230).
local CARRY = { [1] = 0x10, [3] = 0x11, [4] = 0x11, [5] = 0x15, [6] = 0x16, [7] = 0x17, [8] = 0x18 }
local UNCARRY = { [0x10] = 1, [0x11] = 3, [0x15] = 5, [0x16] = 6, [0x17] = 7, [0x18] = 8,
                  [0x1D] = 1, [0x1F] = 3, [0x21] = 5, [0x22] = 6, [0x23] = 7, [0x24] = 8 }
-- Carrying the partner (team-throw-probe.csv: leader $1F/$1D while the partner rides).
local TEAM = { [1] = 0x1D, [3] = 0x1F, [4] = 0x1F, [5] = 0x21, [6] = 0x22, [7] = 0x23, [8] = 0x24 }

local function held_mode(player, mode)
  if player.team_up then return TEAM[mode] or mode end
  return player.carrying and CARRY[mode] or mode
end

-- new(data) builds one VM per Kong (Diddy: this module; the partner: original_partner.lua).
local input = require("main.input")

local function new(data)
local M = { enabled=false, id=0, pose=0, timer=0, pc=0, rate=256, callback=0, returns={} }
local consume, set_mode

local function moving_mode(player)
  local run = player.run_held
  if run == nil then run = input.hold_bit(input.BIT.Y) end
  if player.move_dir == nil then  -- the following partner: no pressed direction
    if math.abs(player.vel_x) < 0.1 then return 1 end
    return run and 4 or 3
  end
  -- B9E12A/B9E0E2: a pressed direction walks/runs; released, the Kong keeps its mode
  -- until |vx| & $FFE0 is 0 (the reference replay poses 287: idle at vx -15, not at vx 0)
  if player.move_dir ~= 0 then return run and 4 or 3 end
  if math.floor(math.abs(player.vel_x) * 256 / 60) < 0x20 then return 1 end
  local id = UNCARRY[M.id] or M.id
  return (id == 3 or id == 4) and id or 1
end

local callbacks = {}
callbacks[0] = function() return false end
-- B9E023: the pressed direction ($26) against the shown facing ($12) starts the turn
-- ($02, $12 holding an object; $1E team-up has no exported script); the Kong is drawn
-- facing the old way (M.turn_dir) until B9E01B flips it (the reference replay poses 219-226).
local TURNS = { [0x02] = true, [0x12] = true }
local function turn(player)
  local dir = player.move_dir
  if not dir or dir == 0 or not M.shown_dir or dir == M.shown_dir or player.team_up then return false end
  local id = player.carrying and 0x12 or 0x02
  if not data.scripts[id] then return false end
  local from = M.shown_dir
  set_mode(id, player)
  M.turn_dir, M.turn_done = from, false
  return true
end
callbacks[0xE023] = turn
callbacks[0xE103] = turn  -- walk: turn check first (the walk/run switch is E0E2's)
-- B9DA32 (run): B9E071 turns with rate $180, else rate |vx|/4 + |vx|/8, at least $100.
callbacks[0xDA32] = function(player)
  if turn(player) then M.rate = 0x180; return true end
  local speed = math.floor(math.abs(player.vel_x) * 256 / 60)
  M.rate = math.max(math.floor(speed / 4) + math.floor(speed / 8), 0x100)
  return false
end
callbacks[0xE0AA] = function(player)
  local id = held_mode(player, moving_mode(player))
  if id == M.id then return false end
  set_mode(id, player)
  -- the new script's per-frame hook runs this frame too: idle -> turn on the press
  -- frame (the reference replay poses 417)
  local hook = M.callback ~= 0xE0AA and M.callback ~= 0xE0E2 and callbacks[M.callback]
  if hook then hook(player) end
  return true
end
callbacks[0xE0E2] = callbacks[0xE0AA]
callbacks[0xD707] = callbacks[0xE0AA]
callbacks[0xDFE3] = callbacks[0xE0AA] -- rendering transition; sound/landing hook remains separate
callbacks[0xDA5D] = callbacks[0] -- original routine is RTS
callbacks[0xDEC3] = function(player)
  if player.vel_y >= 0 then M.rate = 512 end
  return false
end
callbacks[0xDECE] = function(player)
  if player.grounded then M.rate = 512 end
  return false
end
callbacks[0xDEF1] = function(player) set_mode(8, player); return true end
callbacks[0xDF53] = function(player) set_mode(6, player); return true end

-- Cartwheel (animation $09, cartwheel-probe.csv): B9DEB0 starts it, B9DE45 stops the Kong
-- (state 4: vx = 0, x held), B9DFE7 hands control back; B9D676 = grounded ($1E & $1001).
callbacks[0xDEB0] = function() return false end
callbacks[0xDE45] = function(player) player.roll_stop, player.vel_x = true, 0; return false end
callbacks[0xDFE7] = function(player)
  player.roll_done, M.unduck_done, M.turn_done = true, true, true
  return false
end
-- Ducking: $0C ends in B9DEE9 (-> $0D, the held duck); $0E (stand up) ends in B9DFE7.
callbacks[0xDEE9] = function(player) set_mode(0x0D, player); return true end

-- Dixie's movement hooks. B9DCB7/B9DCCC: animation rate = |vx| ($20) at least $E0/$140
-- (B9DCCC first runs B9E071: $180 while turning, not ported); B9DCE4: rate $100;
-- B9E07C: idle/walk/run dispatch (same choice as E0AA); B9E01B flips $12 (facing comes
-- from the player here).
local function speed_rate(player, minimum)
  return math.max(math.floor(math.abs(player.vel_x) * 256 / 60), minimum)
end
callbacks[0xDCB7] = function(player) M.rate = speed_rate(player, 0xE0); return false end
callbacks[0xDCCC] = function(player) M.rate = speed_rate(player, 0x140); return false end
callbacks[0xDCE4] = function() M.rate = 0x100; return false end
callbacks[0xE07C] = callbacks[0xE0AA]
callbacks[0xE01B] = function() M.turn_dir = nil; return false end
-- Throw ($14): B9D8AC holds the Kong (state $0F), B9D967 lets the object go (state $3F),
-- B9DFD5 hands control back (carry-route-t2.csv 1150-1169).
callbacks[0xD8AC] = function(player) player.throw_freeze = true; return false end
callbacks[0xD967] = function(player) player.throw_freeze, player.throw_release = false, true; return false end
callbacks[0xDFD5] = function() if M.forced == 0x14 then M.forced = nil end; return false end

local function callback(address, player)
  local fn = callbacks[address]
  if fn then return fn(player) end
  M.status = string.format("unimplemented-callback-%04x", address)
  return false
end

local conditions = {}
conditions[0xD5A6] = function(player) return player.grounded end
conditions[0xD55C] = function(player) return player.vel_y >= 0 end  -- B9D55C: $24 >= 0
conditions[0xD566] = function(player) return player.vel_y < 0 end   -- B9D566: $24 < 0
conditions[0xD676] = function(player) return player.grounded end      -- B9D676: $1E & $1001
-- B9D12B (follower jump $3E, death $0A) clears $38 and re-reads the script: continue.
conditions[0xD12B] = function() return true end
-- B9D570: on the ground ($1E & $1000) or the floor below ($0C - $0A) under $48 px: the
-- landing frames start ~9 frames before touchdown (the reference replay poses 191 vs 200).
conditions[0xD570] = function(player)
  if player.grounded then return true end
  if not player.get_hitbox then return false end
  local _, top, w, h = player.get_hitbox()
  local distance = top and require("main.collision").ground_distance(player.pos_x, top, w, h, 0x48)
  return distance ~= nil and distance < 0x48
end

local handlers = {}
handlers[0x80] = function(entry, player) M.pc = data.scripts[M.id].start end
handlers[0x81] = function(entry, player)
  M.pc = entry.next
  return callback(entry.arg, player)
end
handlers[0x82] = function(entry, player) M.pc = entry.arg end
handlers[0x83] = function(entry, player)
  local fn = conditions[entry.arg]
  if not fn then M.status = "unsupported-condition" end
  if not fn or not fn(player) then M.timer = 0; return true end
  M.pc = entry.next
end
handlers[0x84] = function(entry, player) M.callback, M.pc = entry.arg, entry.next end
-- $91 slot,addr: B9D240 stores the return pc in sprite field `slot` and jumps; $92 slot:
-- B9D259 returns to it.
handlers[0x91] = function(entry) M.returns[entry.slot], M.pc = entry.next, entry.arg end
handlers[0x92] = function(entry) M.pc = M.returns[entry.slot] or data.scripts[M.id].start end
handlers[0x8E] = function(entry, player)
  M.pending_sfx = entry.arg -- original sound ID retained; audio component not yet delivered
  M.pc = entry.next
end

-- $8B dur,pose,dx,dy: frame with the held-object offset; $89 dur,pose,pose2: frame with a
-- second sprite (level-end prize). Timer semantics as for op < $80.
local function frame(entry, duration)
  M.timer = M.timer + duration * 256
  M.pc = entry.next
  if M.timer < 0 then return false end
  assert(data.poses[entry.arg], string.format("missing original pose resource %04x", entry.arg))
  M.pose, M.held_dx, M.held_dy = entry.arg, entry.dx, entry.dy
  M.pose2 = (entry.op == 0x89 or entry.op == 0x8A) and entry.arg2 or nil
  return true
end
handlers[0x8B] = function(entry) return frame(entry, entry.dur) end
handlers[0x89] = handlers[0x8B]
-- $8A dur,pose,pose2,dx,dy (B9D3CA): team-up frame; pose2/dx/dy drive the carried Kong.
handlers[0x8A] = handlers[0x8B]
-- $8F cb,dst: branch to dst when the callback sets carry. Untranslated conditions do not
-- branch (M.status records them).
handlers[0x8F] = function(entry, player)
  local fn = conditions[entry.arg]
  if not fn then M.status = string.format("unimplemented-branch-%04x", entry.arg) end
  M.pc = (fn and fn(player)) and entry.arg2 or entry.next
end
-- $90 cb,anim: call, then switch animation.
handlers[0x90] = function(entry, player)
  callback(entry.arg, player)
  set_mode(entry.arg2, player)
  return true
end

local function step(entry, player)
  if entry.op < 128 then
    M.timer = M.timer + entry.op * 256
    M.pc = entry.next
    if M.timer < 0 then return false end
    assert(data.poses[entry.arg], string.format("missing original pose resource %04x", entry.arg))
    M.pose, M.pose2 = entry.arg, nil
    return true
  end
  local handler = handlers[entry.op]
  if not handler then M.status = "unsupported-bytecode"; return true end
  return handler(entry, player)
end

consume = function(player)
  for _ = 1, 64 do
    local entry = data.scripts[M.id].code[M.pc]
    if not entry then M.status = "unexported-bytecode"; return end
    if step(entry, player) then return end
  end
  error("original animation instruction budget exceeded")
end

set_mode = function(id, player)
  assert(data.scripts[id], "original animation script missing")
  M.id, M.pc, M.pose2 = id, data.scripts[id].start, nil
  if not TURNS[id] then M.turn_dir = nil end
  M.timer, M.rate, M.callback = 0, 256, 0
  consume(player)
end

function M.init(enabled, player)
  M.enabled, M.boot, M.status, M.forced = enabled, true, "supported-rendering-subset", nil
  M.turn_dir, M.shown_dir = nil, nil
  if enabled then set_mode(4, player) end
end

--- Play a scripted animation (death $0A, bounce $1C, level end $45/$46, ...) until
-- M.release(); the movement-driven modes resume afterwards.
function M.force(id, player)
  if not M.enabled or not data.scripts[id] then return end
  M.forced = id
  set_mode(id, player)
end

function M.bounce(player)
  if M.enabled and not M.forced and not player.carrying and data.scripts[0x1C] then set_mode(0x1C, player) end
end

function M.release()
  M.forced = nil
end

--- Switch Kong (partner swap): the next update restarts from the boot pose.
function M.set_data(new_data)
  if new_data == data then return end
  data, M.forced, M.boot, M.returns = new_data, nil, M.enabled, {}
  M.turn_dir, M.shown_dir = nil, nil
end


local function requested_mode(player)
  if M.forced then return M.forced end
  local ducking = player.STATE and player.state == player.STATE.CROUCH
  if ducking then return (M.id == 0x0C or M.id == 0x0D) and M.id or 0x0C end
  if M.id == 0x0C or M.id == 0x0D then M.unduck_done = false; return 0x0E end
  if M.id == 0x0E and not M.unduck_done then return 0x0E end
  local id = UNCARRY[M.id] or M.id
  local mode
  if player.jump_windup > 0 then mode = 5
  elseif TURNS[M.id] and not M.turn_done and player.grounded then mode = M.id
  -- stomp bounce: $1C loops until touchdown, then straight to walk/idle (the reference replay poses
  -- 566-607; no landing frames)
  elseif player.bounced and not player.grounded and not player.carrying and data.scripts[0x1C] then mode = 0x1C
  elseif id == 5 or id == 6 or id == 7 or id == 8 then mode = id
  elseif not player.grounded then mode = player.vel_y < 0 and 6 or 7
  -- idle/walk/run switch at the scripts' own points (E0AA per frame, E0E2 between poses)
  elseif player.move_dir ~= nil and (id == 1 or id == 3 or id == 4) then mode = id
  else mode = moving_mode(player) end
  return held_mode(player, mode)
end

function M.update(player)
  if not M.enabled then return end
  if M.boot then
    M.boot = false
    set_mode(7, player)
    return
  else
    local mode = requested_mode(player)
    if mode ~= M.id then
      set_mode(mode, player)
      if mode ~= 5 then return end
    end
  end
  M.timer = M.timer - M.rate
  if M.timer <= 0 then consume(player) end
  callback(M.callback, player)
  if not M.turn_dir then M.shown_dir = player.direction end
end

function M.get_animation()
  local pose = data.poses[M.pose]
  return M.enabled and pose and pose.animation or nil
end

--- The $89 frame's second sprite (the level-end boombox), drawn with the Kong.
function M.get_animation2()
  local pose = M.pose2 and data.poses[M.pose2]
  return M.enabled and pose and pose.animation or nil
end

function M.snapshot()
  local pose = data.poses[M.pose]
  return { id=M.id, pose=M.pose, gfx=pose and pose.gfx,
           timer=M.timer, pc=M.pc, status=M.status }
end

return M
end

local M = new(require("data.original.pirate.animation_scripts"))
M.new = new
return M
