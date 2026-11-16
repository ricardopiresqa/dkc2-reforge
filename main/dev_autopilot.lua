--- Piloto automatico de desenvolvimento (desligado por padrao).
--
-- Ligue com `dkc2.autopilot = 1` em game.project para o jogo se controlar
-- sozinho: serve para smoke test do loop de gameplay (andar, pular, frear,
-- colidir) sem precisar injetar teclas pelo sistema operacional.
--
-- Nao substitui teste manual; so garante que o estado do player evolui.

local bit = require("bit")
local input = require("main.input")

local M = {}
M.viewport_info = nil

M.enabled = false
local qa_frames = 0
local qa_samples = {}
local input_check = false
local reference = nil
local idle_qa = false
local route_qa = false
local qa_trace = {}
local route_completed = false
local collision_walk_qa = false
local checkpoints = {}
local neek_interaction_samples = {}
local checkpoint_groups = {
  [0] = "ground_walk", [40] = "ground_walk", [60] = "ground_walk",
  [100] = "ground_walk", [140] = "ground_walk", [153] = "short_jump",
  [158] = "short_jump", [165] = "short_jump", [173] = "short_jump", [180] = "short_jump",
}
local camera_checkpoints = { [0]=true,[40]=true,[60]=true,[100]=true,[140]=true,
  [153]=true,[158]=true,[165]=true,[173]=true,[180]=true }

local B     = bit.lshift(1, input.BIT.B)
local RIGHT = bit.lshift(1, input.BIT.RIGHT)
local LEFT  = bit.lshift(1, input.BIT.LEFT)

-- { frames, mascara } -- repetido em ciclo
-- START fica de fora de proposito: em GAMEPLAY ele pausa o jogo. Para testar os
-- menus, rode uma vez com um passo START no inicio e `dkc2.start_level` vazio.
local SCRIPT = {
  { 40,  0 },                    -- parado
  { 110, RIGHT },                -- corre para a direita
  { 8,   bit.bor(RIGHT, B) },    -- pula correndo
  { 60,  RIGHT },
  { 40,  LEFT },                 -- freia / inverte (exercita o SKID)
  { 60,  0 },
  { 8,   B },                    -- pulo parado
  { 50,  0 },
}

local total = 0
for _, step in ipairs(SCRIPT) do total = total + step[1] end

function M.init()
  local get_config = sys.get_config_string or sys.get_config
  M.enabled = get_config("dkc2.autopilot", "0") == "1"
  qa_frames = math.max(0, math.min(6000, tonumber(get_config("dkc2.qa_frames", "0")) or 0))
  qa_samples = {}
  checkpoints = {}
  neek_interaction_samples = {}
  idle_qa = get_config("dkc2.idle_qa", "0") == "1"
  route_qa = get_config("dkc2.route_qa", "0") == "1"
  -- QA only: replace the reference input from this frame on with a single RIGHT+Y tap
  -- then RIGHT (same as tools/replay-compare/cartwheel_capture.lua).
  M.tap_y_frame = tonumber(get_config("dkc2.qa_tap_y_frame", ""))
  -- QA only: scripted pad masks "frame=mask,frame=mask" (mask held until the next entry).
  M.qa_script = nil
  for frame, mask in string.gmatch(get_config("dkc2.qa_script", ""), "(%d+)=(%d+)") do
    M.qa_script = M.qa_script or {}
    M.qa_script[#M.qa_script + 1] = { tonumber(frame), tonumber(mask) }
  end
  collision_walk_qa = get_config("dkc2.collision_walk_qa", "0") == "1"
  route_completed = false
  require("main.collision").set_collision_trace(collision_walk_qa)
  if get_config("dkc2.reference_replay", "0") == "1" then
    reference = require("data.original.pirate.reference_inputs")
  end
  if qa_frames > 0 then
    input_check = require("main.test.input_check").run()
    assert(require("main.original_motion").check())
    assert(require("main.test.collision_check").run())
    assert(require("main.test.neek_collision_test").run())
    assert(require("main.original_camera").check_damping())
  end
  if reference then
    input.set_synthetic(reference.initial_input or 0)
    input.post_update()
    input.set_synthetic(nil)
  end
  if M.enabled then
    print("[autopilot] ligado -- dkc2.autopilot=1 em game.project")
  end
end

local function has_neek_hit(events)
  for _, event in ipairs(events) do
    if event.type == "enemy_hit" and event.object.params
        and event.object.params.sprite == "Neek" then return true end
  end
  return false
end

local function snapshot_neeks(object_list)
  local neeks = {}
  local objects = require("main.objects")
  for _, object in ipairs(object_list) do
    if object.params and object.params.sprite == "Neek" then
      neeks[#neeks + 1] = {
        x = object.x, y = object.y, source_x = object.source_x,
        source_neek_active = object.source_neek_active,
        vel_x = object.vel_x,
        active = bit.band(object.flags, objects.FLAG_ACTIVE) ~= 0,
        collected = bit.band(object.flags, objects.FLAG_COLLECTED) ~= 0,
      }
    end
  end
  return neeks
end

function M.record_neek_interaction(frame, events, player, object_list, input_hold, input_edge)
  local first_window = frame >= 550 and frame <= 615
  local second_window = frame >= 900 and frame <= 950
  if not collision_walk_qa or not (first_window or second_window) then return end
  neek_interaction_samples[#neek_interaction_samples + 1] = {
    frame = frame, input_hold = input_hold, input_edge = input_edge,
    neek_hit = has_neek_hit(events),
    player = { x = player.pos_x, y = player.pos_y, feet_y = player.pos_y + 24,
      vel_x = player.vel_x, vel_y = player.vel_y, grounded = player.grounded,
      state = player.state, hitpause_frames = player.hitpause_frames },
    neeks = snapshot_neeks(object_list),
  }
end

--- QA route bot (not production AI, not an SNES recording): run right with jump bursts.
local function route_mask(tail)
  local mask = bit.bor(RIGHT, bit.lshift(1, input.BIT.Y))
  local route_player = require("main.player")
  local player_x, player_y = route_player.pos_x, route_player.pos_y
  -- QA-only repeated held-jump bursts near decoded collision geometry.
  -- A continuous hold only creates one edge-triggered jump. This tests a
  -- possible mixed-input route; it is not production AI or an SNES recording.
  local hazard_region = player_x >= 3000 and player_x <= 4200
  if (hazard_region and tail % 48 < 22) or (not hazard_region and tail % 120 < 36) then
    mask = bit.bor(mask, B)
  end
  -- The decoded ship-deck slice ends near source X=3207; probe a held jump
  -- at the approaching ledge without disabling collision or moving the player.
  if player_x >= 2850 and player_x <= 3150 then
    if player_x >= 3020 and player_x <= 3070 then
      mask = bit.band(mask, bit.bnot(B))
    elseif player_y >= 240 and tail % 40 < 26 then
      mask = bit.bor(mask, B)
    end
  end
  -- Level-end goal (x 6984): stop on it and hop so Diddy falls onto its box.
  if player_x >= 6950 and player_x <= 7000 then
    mask = tail % 40 < 20 and B or 0
  elseif player_x > 7000 then
    mask = bit.lshift(1, input.BIT.LEFT)
  end
  return mask
end

--- Mascara de entrada sintetica para o frame informado.
function M.update(frame_index, phase)
  if not M.enabled then return end
  if collision_walk_qa then
    local collision = require("main.collision")
    collision.set_collision_trace_frame(frame_index)
  end
  if idle_qa then input.set_synthetic(0) end
  if reference then
    local player = require("main.player")
    local group = checkpoint_groups[frame_index]
    if group or camera_checkpoints[frame_index] then
      local camera_snapshot = require("main.original_camera").snapshot()
      checkpoints[#checkpoints + 1] = {
        id = (group or "ground_walk") .. "_" .. frame_index, frame = frame_index,
        x = math.floor(player.pos_x), y = math.floor(player.pos_y + 24),
        state = (player.state == player.STATE.IDLE or player.state == player.STATE.RUN
                 or player.state == player.STATE.SKID) and "ground" or "air",
        original_animation = require("main.original_animation").snapshot(),
        camera = { x = require("main.camera").pos_x, y = require("main.camera").pos_y,
                   context = camera_snapshot },
      }
    end
    if collision_walk_qa and frame_index >= #reference.inputs then
      input.set_synthetic(RIGHT) -- walk only; stop at source-authored pits/walls
    elseif route_qa and frame_index >= #reference.inputs then
      input.set_synthetic(route_mask(frame_index - #reference.inputs))
    elseif M.tap_y_frame and frame_index >= M.tap_y_frame then
      input.set_synthetic(frame_index == M.tap_y_frame and bit.bor(RIGHT, bit.lshift(1, input.BIT.Y)) or RIGHT)
    else
      input.set_synthetic(reference.inputs[frame_index + 1] or 0)
    end
  elseif M.qa_script then
    local mask = 0
    for _, entry in ipairs(M.qa_script) do
      if frame_index >= entry[1] then mask = entry[2] end
    end
    input.set_synthetic(mask)
  elseif collision_walk_qa then
    input.set_synthetic(RIGHT)
  elseif route_qa and package.loaded["main.game"] and phase == package.loaded["main.game"].PHASE.GAMEPLAY then
    input.set_synthetic(route_mask(frame_index))  -- route bot without reference inputs
  end

  if (reference or M.qa_script) and qa_frames > 0 then  -- per-frame player trace (QA only)
    local trace_player = require("main.player")
    qa_trace[#qa_trace + 1] = { frame_index, trace_player.pos_x, trace_player.pos_y + 24,
                                trace_player.grounded and 1 or 0, trace_player.vel_x * 256 / 60,
                                trace_player.state, trace_player.landing_hold and 1 or 0,
                                trace_player.bounced and 1 or 0, trace_player.carrying and 1 or 0,
                                require("main.original_animation").forced or 0,
                                require("main.original_partner").debug() or -1,
                                select(2, require("main.original_partner").debug()),
                                require("main.original_kong_hud").phase or "-", require("main.hud").bananas,
                                (function()  -- live walkers: raw x/y (QA only)
                                  local list = {}
                                  for _, w in ipairs(require("main.original_walkers").walkers() or {}) do
                                    if w.alive then list[#list + 1] = { bit.rshift(w.x, 8), bit.rshift(w.y, 8) } end
                                  end
                                  return list
                                end)(), require("main.camera").pos_x,
                                require("main.original_goal").debug() or false,
                                require("main.original_animation").pose or 0 }
  end
  if frame_index % 60 == 0 then
    local player = require("main.player")
    local camera = require("main.camera")
    if qa_frames > 0 then
      local renderer = require("main.renderer")
      local perf = require("main.perf")
      qa_samples[#qa_samples + 1] = {
        frame = frame_index, phase = phase, x = player.pos_x, y = player.pos_y,
        state = player.state, health = player.health,
        original_animation = require("main.original_animation").snapshot(),
        sprites = renderer.sprite_count(), pool_drops = renderer.pool_drops,
        frame_dt = perf._last_dt,
        lua_cpu_ms = perf._last_cpu and perf._last_cpu * 1000,
      }
    end
    print(string.format(
      "[autopilot] f=%d phase=%s pos=(%.0f,%.0f) vel=(%.0f,%.0f) state=%d hp=%d cam=(%.0f,%.0f)",
      frame_index, tostring(phase), player.pos_x, player.pos_y, player.vel_x, player.vel_y,
      player.state, player.health, camera.pos_x, camera.pos_y))
  end

  if qa_frames > 0 and frame_index >= qa_frames then
    -- Bounded QA writes only beside the task-owned executable. Never enabled in production.
    local file, error_message = io.open("qa-runtime.json", "w")
    assert(file, error_message)
    local game_module = package.loaded["main.game"]
    file:write(json.encode({ frames = frame_index, samples = qa_samples,
                            contacts = game_module and game_module.qa_contacts or {},
                            player_trace = qa_trace,
                            input_check = input_check,
                            qa_version = route_qa and "bounded-mixed-route-v1" or "room-slice-oam-input-v2",
                             route_qa = route_qa,
                             collision_walk_qa = collision_walk_qa,
                             collision_events = collision_walk_qa and require("main.collision").collision_trace_snapshot() or nil,
                             neek_interaction_samples = collision_walk_qa and neek_interaction_samples or nil,
                            level_complete = route_completed,
                            viewport = M.viewport_info,
                            scope = "autopilot smoke; not original-fidelity proof" }))
    file:close()
    if reference and not route_qa then
      local capture = assert(io.open("port-checkpoints.json", "w"))
      capture:write(json.encode({ input_sha256 = reference.input_sha256,
                                 initial_input = reference.initial_input or 0,
                                 rom_sha256 = reference.rom_sha256,
                                 checkpoints = checkpoints,
                                 scope = "quantized original sprite origins; initial walk and first short jump only; not full physics or camera fidelity" }))
      capture:close()
    end
    sys.exit(0)
    return
  end

  if reference or idle_qa or M.qa_script or route_qa then return end

  local t = frame_index % total
  for _, step in ipairs(SCRIPT) do
    if t < step[1] then
      input.set_synthetic(step[2])
      return
    end
    t = t - step[1]
  end
end

function M.mark_level_completed()
  route_completed = true
end

return M
