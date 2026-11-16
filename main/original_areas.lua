-- Pirate Panic area links: barrel-cannon portals in the main area, bonus rules and the
-- warp room exit (data: data/original/pirate/area_links.lua, export_subareas.py).
-- Translated data: portal destinations/returns (cannon data $0203 / $0405), the main
-- header return records, bonus controllers (type, count, seconds: sub-script D354).
-- The cannon blast itself is in game.lua (M._update_cannon). APPROXIMATIONS: the
-- return drops the Kong from the record position; bonus type 0 = take the Kremkoin
-- before time runs out, type 1 = defeat `count` enemies, then the Kremkoin appears;
-- the warp room exits once the Kong reaches its exit object (x >= 200).
local M = { active = false }

local links
local area            -- nil = main area, else "bonus_1" | "bonus_2" | "warp"
local state = {}

function M.init(subarea, objects)
  local ok, data = pcall(function() return require("data.original.pirate.area_links") end)
  links = ok and data or nil
  area, state = subarea, {}
  M.note_shown = false  -- K. Rool's message (Kabin), shown once the note is touched
  M.active = links ~= nil
  if not M.active or not subarea then return end
  for _, object in ipairs(objects or {}) do
    local controller = links.controllers[object.param]
    if controller then
      state.kind, state.count, state.frames = controller.kind, controller.count, controller.seconds * 60
    end
    if object.script == 10 and object.sprite == "Coins" then state.coin = object end
  end
  state.defeated = 0
end

--- Objects the item module should spawn now in this area (Kremkoin of a find bonus).
function M.initial_items(objects)
  if not area or state.kind ~= 0 or not state.coin then return objects end
  local list = {}
  for _, object in ipairs(objects or {}) do list[#list + 1] = object end
  local coin = {}
  for key, value in pairs(state.coin) do coin[key] = value end
  coin.script = 1
  list[#list + 1] = coin
  return list
end

--- Main area: cannon portal touched by the player box -> dest, return_record, portal.
function M.portal(pl, pt, pr, pb)
  if not M.active or area then return nil end
  local box = links.cannon.box
  for _, portal in ipairs(links.portals) do
    local left, top = portal.x + box[1], portal.feet_y + box[2]
    if pr >= left and left + box[3] >= pl and top + box[4] >= pt and pb >= top then
      return portal.dest, portal.return_record, portal
    end
  end
  return nil
end

-- Doors: the deck's ExitDoor (param 2220: $42 = 1 Captain's Kabin, $44 = 2 return
-- record) and the Kabin's way out (param 2240 at x 238). Walk-through, not UP
-- (kabin-route-t1..t3.csv): walking toward a door within 21 px of it starts the door walk
-- (game.lua). APPROXIMATION: feet within 24 px of the door's.
local DOORS = {
  main = { x = 308, feet_y = 276, dest = "kabin", return_record = 2, dir = -1 },
  kabin = { x = 238, feet_y = 192, exit = true, dir = 1 },
}
local DOOR_REACH = 21

--- Walking `dir` (-1 | 1) at a door: returns "enter", dest, return_record, dir | "exit", dir | nil.
function M.door(x, feet, dir)
  local door = DOORS[area or "main"]
  if not M.active or not door or dir ~= door.dir then return nil end
  local ahead = (door.x - x) * dir  -- distance still to walk toward the door
  if ahead >= 0 and ahead <= DOOR_REACH and math.abs(feet - door.feet_y) < 24 then
    if door.exit then return "exit", nil, nil, dir end
    return "enter", door.dest, door.return_record, dir
  end
  return nil
end

-- The door frame in front of a Kong walking through (BG1 priority over the sprite):
-- kabin-route-t6.csv 600-624, the deck door hides x < 298 (door x - 10). APPROXIMATION:
-- the Kabin's exit is assumed the mirror (hides x > door x + 10); not captured.
function M.door_clip(dir)
  local door = DOORS[area or "main"]
  if not door then return nil end
  if dir < 0 then return { door.x - 10, 100000 } end
  return { -100000, door.x + 10 }
end

--- A Kong got into a hidden cannon (the warp): it shows from now on (this visit).
function M.reveal(portal) M.revealed = M.revealed or {}; M.revealed[portal.param] = true end

function M.each_cannon(draw)
  if not M.active or area then return end
  local cannon = links.cannon
  for _, portal in ipairs(links.portals) do
    if not portal.hidden or (M.revealed and M.revealed[portal.param]) then
      draw(cannon.sprite, portal.x - cannon.origin_x, portal.feet_y - cannon.origin_y, cannon.width, cannon.height)
    end
  end
end

function M.return_point(record)
  local point = links and links.main_records[record]
  return point and point.x, point and point.feet_y
end

function M.on_defeat(add_item)
  if not area or state.kind ~= 1 or state.won then return end
  state.defeated = state.defeated + 1
  if state.defeated >= state.count and state.coin and not state.coin_shown then
    state.coin_shown = true
    M.sound_request = "spawn_kremcoin"
    local coin = {}
    for key, value in pairs(state.coin) do coin[key] = value end
    coin.script = 1
    add_item(coin)
  end
end

function M.on_kremkoin()
  if area and area ~= "warp" then state.won, state.exit_timer = true, 90 end
end

--- One frame in a subarea. Returns "exit" when the Kong must go back to the main area.
function M.update(player_x)
  if not area then return nil end
  if area == "warp" then
    return player_x >= 200 and "exit" or nil
  end
  if state.won then
    state.exit_timer = state.exit_timer - 1
    return state.exit_timer <= 0 and "exit" or nil
  end
  if state.frames then
    state.frames = state.frames - 1
    if state.frames % 60 == 0 and state.frames > 0 then M.sound_request = "timer_tick" end
    if state.frames <= 0 then return "exit" end
  end
  return nil
end

function M.seconds_left()
  if not area or area == "warp" or not state.frames or state.won then return nil end
  return math.max(0, math.ceil(state.frames / 60))
end

function M.area() return area end

return M
