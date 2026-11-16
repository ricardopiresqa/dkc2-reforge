-- Pirate Panic items (banana/DK coins, wooden box, star and DK barrels) drawn from their
-- original spawn + F9 animation scripts (tools/replay-compare/export_items.py).
-- Origin = the level object's (x, feet_y) in port coordinates (WoodenBox in WRAM).
-- Only `script = 1` objects are created in the main area (reference-sprites-trace.csv:
-- the script-10 Kremkoins never spawn). A sprite spawns the frame after the camera
-- reaches x - $120, runs its first animation step on that frame, and despawns once it
-- is $28 px behind the camera (static objects in the trace) or ~$12C px ahead.
-- The DK barrel emblem ($11C) is a companion sprite with its own animation.
-- Behaviour (pickup, break, checkpoint, partner) is pending.
local M = { active = false }

local SPAWN_AHEAD, DESPAWN_BEHIND, DESPAWN_AHEAD = 0x120, 0x28, 0x12C
-- The banana bunch leaves with the sprite box (0x28 + 0x150 = 0x128 ahead, as the
-- walkers): reference-sprites-trace.csv frame 987 (one data point).
local AHEAD_BY_KIND = { banana_bunch = 0x128 }
local SOURCE_OFFSET = 256
-- Level-end goal children (B3A22A spawns them with the goal; goal-route-t1.csv): the pole
-- ($168, anim $2C1), the prize on top ($16C, anim $2B2 = banana bunch, its pose held: the
-- prize table of this level has one entry) and the barrel ($164, anim $2C2) at the foot.
local GOAL_CHILDREN = { { "pole", 0x2C1, 21, -66 }, { "prize", 0x2B2, 21, -110 }, { "barrel", 0x2C2, 21, 0 } }
local entities = {}

function M.init(enabled, objects)
  M.active, entities = false, {}
  if not enabled then return end
  local ok, items = pcall(function() return require("data.original.pirate.items") end)
  local ok_level, level = pcall(function() return require("data.original.pirate.pirate_panic_level") end)
  if not (ok and ok_level) or type(items) ~= "table" or type(level) ~= "table" then return end
  M.items_data = items
  for _, object in ipairs(objects or level.objects or {}) do M.add(object) end
  M.active = true
end

--- Taken/broken items persist across area changes within one level visit (set by game.lua).
M.taken = {}
function M.set_taken(taken) M.taken = taken or {} end

--- Add one level object (also used for the bonus Kremkoin that appears later).
function M.add(object)
  local items = M.items_data
  local item = items and items.items[object.param]
  local frames = item and items.animations[item.animation]
  if item and item.kind == "dk_barrel" and M.no_dk_barrels then return end  -- cheat ($060B bit 0)
  if frames and #frames > 0 and object.script == 1 then
    local companion = item.companion and items.animations[item.companion]
    local key = object.x .. ":" .. object.feet_y .. ":" .. object.param
    entities[#entities + 1] = { kind = item.kind, x = object.x, feet_y = object.feet_y, key = key,
                                spawn_range = item.spawn_range or 0, gone = M.taken[key] == true,
                                frames = frames, alive = false, index = 1, timer = 0,
                                companion = companion and { frames = companion, index = 1, timer = 0 } }
    if item.kind == "level_end_goal" then
      local goal = entities[#entities]
      goal.children = {}
      for _, child in ipairs(GOAL_CHILDREN) do
        local child_frames = items.animations[child[2]]
        if child_frames then
          entities[#entities + 1] = { kind = "goal_" .. child[1], x = object.x + child[3], feet_y = object.feet_y + child[4],
                                      spawn_range = 0, frames = child_frames, alive = false, index = 1, timer = 0,
                                      held = true, parent = goal }
          goal.children[child[1]] = entities[#entities]
        end
      end
    end
  end
end

--- Swap an entity's animation (the struck goal: $2B4, played once then held).
function M.play(entity, number, once)
  local frames = M.items_data and M.items_data.animations[number]
  if frames then entity.frames, entity.index, entity.timer, entity.once = frames, 1, frames[1].frames, once end
end

local function step(animation)
  if animation.held then return end
  animation.timer = animation.timer - 1
  if animation.timer <= 0 and animation.once and animation.index == #animation.frames then
    animation.held = true
  elseif animation.timer <= 0 then
    animation.index = animation.index % #animation.frames + 1
    animation.timer = animation.frames[animation.index].frames
  end
end

local function restart(animation)  -- spawn: first animation step runs on that frame
  if animation.once then animation.index = #animation.frames return end  -- played out: hold the end
  animation.index, animation.timer = 1, animation.frames[1].frames
  step(animation)
end

-- HYPOTHESIS (one data point): spawn field $5C (coins: $78) bounds the vertical
-- distance from the screen centre; the rigging banana coin at (808, 59) never spawns
-- along the reference route although it passes the horizontal window.
local function in_vertical_range(entity, camera_y)
  return entity.spawn_range == 0 or math.abs(entity.feet_y - (camera_y + 112)) <= entity.spawn_range
end

--- One game frame. camera_x/camera_y: port camera of the previous frame (source - 256).
-- frozen: sprites hold during the stomp hit-stop together with the actor (one frame
-- after the camera freeze: trace frames 567-568 and 939-940).
function M.update(camera_x, camera_y, frozen)
  if frozen then return end
  for _, entity in ipairs(entities) do
    if entity.parent then  -- goal children live with the goal
      entity.alive = entity.parent.alive and not entity.gone
    elseif entity.alive then
      local relative = entity.x - camera_x
      if relative <= -DESPAWN_BEHIND or relative > (AHEAD_BY_KIND[entity.kind] or DESPAWN_AHEAD) then
        entity.alive = false
      else
        step(entity)
        if entity.companion then step(entity.companion) end
      end
    elseif not entity.gone and camera_x >= entity.x - SPAWN_AHEAD and entity.x - camera_x > -DESPAWN_BEHIND
        and in_vertical_range(entity, camera_y) then
      entity.alive = true
      restart(entity)
      if entity.companion then restart(entity.companion) end
    end
  end
end

-- Pose sprites land one pixel left of their pose origin on the real screen: DK barrel,
-- emblem and wooden box match items-frame-*.ppm 100% only with this -1 (5 frames).
local POSE_X_BIAS = -1

--- draw(sprite, left, top, width, height) in port world coordinates for live items.
function M.each_visible(draw)
  for _, entity in ipairs(entities) do
    if entity.alive then
      local frame = entity.frames[entity.index]
      draw(frame.sprite, entity.x - frame.origin_x + POSE_X_BIAS, entity.feet_y - frame.origin_y,
           frame.width, frame.height)
      if entity.companion then  -- DK barrel emblem ($11C), drawn over the barrel
        local top = entity.companion.frames[entity.companion.index]
        draw(top.sprite, entity.x - top.origin_x + POSE_X_BIAS, entity.feet_y - top.origin_y,
             top.width, top.height)
      end
    end
  end
end

--- Live items of `kind`: fn(entity, pose) with the current pose offset (hitboxes.lua).
function M.each_alive(kind, fn)
  for _, entity in ipairs(entities) do
    if entity.alive and entity.kind == kind then fn(entity, entity.frames[entity.index].pose) end
  end
end

--- Taken/broken for good: never respawns in this level visit.
function M.remove(entity)
  entity.alive, entity.gone = false, true
  if entity.key then M.taken[entity.key] = true end
end

function M.count() return #entities end

return M
