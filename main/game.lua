local input = require("main.input")
local player = require("main.player")
local camera = require("main.camera")
local collision = require("main.collision")
local level_loader = require("main.level_loader")
local objects = require("main.objects")
local hud = require("main.hud")
local sound = require("main.sound")
local original_motion = require("main.original_motion")
local menu = require("main.menu")
local level_select = require("main.level_select")
local player_render = require("main.player_render")
local renderer = require("main.renderer")
local perf = require("main.perf")
local hud_render = require("main.hud_render")
local autopilot = require("main.dev_autopilot")
local original_animation = require("main.original_animation")
local original_bananas = require("main.original_bananas")
local original_hud = require("main.original_hud")
local original_items = require("main.original_items")
local original_walkers = require("main.original_walkers")
local original_klobber = require("main.original_klobber")
local opening = require("main.opening")
local original_areas = require("main.original_areas")
local original_rambi = require("main.original_rambi")
local original_effects = require("main.original_effects")
local original_goal = require("main.original_goal")
local original_coin_hud = require("main.original_coin_hud")
local original_menu = require("main.original_menu")
local original_carry = require("main.original_carry")
local original_partner = require("main.original_partner")
local original_kong_hud = require("main.original_kong_hud")
local save_manager = require("main.save_manager")
local boss = require("main.boss")
local scrapbook = require("main.scrapbook")
local time_attack = require("main.time_attack")
local game_over = require("main.game_over")
local shop = require("main.shop")

local M = {}

M.PHASE = {
  TITLE        = 9,
  LOADING      = 10,
  GAMEPLAY     = 11,
  PAUSE        = 12,
  DEATH        = 13,
  LEVEL_SELECT = 14,
  BOSS_INTRO   = 15,
  LEVEL_COMPLETE = 16,
  BONUS          = 17,
  SCRAPBOOK      = 18,
  TIME_ATTACK    = 19,
  GAME_OVER      = 20,
  SHOP           = 21,
}

M.phase = M.PHASE.TITLE
M.frame_index = 0
M.level_loaded = false
M.transition_timer = 0
M.game_over = false
M.current_level_module = nil
M.current_boss = nil
M.level_complete_timer = 0
M.dk_coin_collected = false
M.secret_exit_taken = false

function M.init()
  save_manager.init()
  sound.init()
  hud.init()
  menu.init()
  level_select.init()
  scrapbook.init()
  time_attack.init()
  game_over.init()
  shop.hide()
  renderer.hide()
  hud_render.hide()
  player_render.destroy()
  autopilot.init()
  player.set_objects(objects)
  M.phase = M.PHASE.TITLE
  opening.init(false)
  M.frame_index = 0
  M.level_loaded = false
  M.transition_timer = 0
  M.game_over = false
  M.dk_coin_collected = false
  hud.lives = save_manager.get_lives()
  hud.bananas = save_manager.get_bananas()
  hud.dk_coins = save_manager.get_dk_coins()
  hud.score = save_manager.get_score()

  -- atalho de desenvolvimento: `dkc2.start_level` em game.project entra direto
  -- num nivel, sem passar pelo titulo. Vazio em producao.
  local get_config = sys.get_config_string or sys.get_config
  local start_level = get_config("dkc2.start_level", "")
  -- QA only: enemy contacts never hurt (lets the route bot reach the level end).
  M.qa_invulnerable = get_config("dkc2.qa_invulnerable", "0") == "1"
  -- QA only: start the first loaded level at a given position (route checks).
  M.qa_spawn = tonumber(get_config("dkc2.qa_spawn_x", "")) and {
    x = tonumber(get_config("dkc2.qa_spawn_x", "")), feet = tonumber(get_config("dkc2.qa_spawn_feet", "209")),
    ride = get_config("dkc2.qa_ride_rambi", "0") == "1",  -- QA only: start mounted on Rambi
    partner = get_config("dkc2.qa_partner", "0") == "1" }  -- QA only: start with the partner
  -- Instrumentacao opt-in: [dkc2] perf_log=1 liga p50/p95 CPU Lua (sem GPU).
  local perf_log = get_config("dkc2.perf_log", "0")
  renderer.set_perf_enabled(perf_log == "1")
  if start_level ~= "" then
    M._load_level(start_level)
  end
end

function M._load_level(level_module, keep_visit)
  M.current_level_module = level_module
  level_loader.load(level_module)
  sound.set_original_semantics(level_loader.original_semantics())

  M.jump_peak = nil  -- $0935 restarts with the level
  M.cannon, player.hidden, M.door_walk, player.door_clip = nil, false, nil, nil
  player.throw_freeze, player.throw_release = nil, nil
  local spawn_x, spawn_y = level_loader.get_player_spawn()
  local qa_ride = M.qa_spawn and M.qa_spawn.ride
  local qa_partner = M.qa_spawn and M.qa_spawn.partner
  if M.qa_spawn then  -- QA only, first load
    spawn_x, spawn_y, M.qa_spawn = M.qa_spawn.x, M.qa_spawn.feet - 24, nil
  end
  player.spawn(spawn_x, spawn_y)
  original_animation.init(level_loader.original_semantics(), player)
  original_partner.init(keep_visit)
  if qa_partner then original_partner.release(spawn_x, spawn_y + 24) end
  if not keep_visit then original_kong_hud.init(); original_areas.revealed = nil end
  original_coin_hud.init(not keep_visit and 0 or original_coin_hud.count)  -- the count stays, the flight does not
  player_render.spawn()

  local bound_x, bound_y = level_loader.get_camera_bounds()
  camera.set_boundaries(bound_x, bound_y)
  camera.set_original_profile(level_loader.get_original_camera())
  camera.snap_to(spawn_x, spawn_y)
  -- Subareas carry their own original objects; banana formations are main-area data.
  local area_objects = level_loader.get_original_objects()
  original_bananas.init(level_loader.original_semantics(), level_loader.get_subarea())
  original_areas.init(level_loader.get_subarea(), area_objects)
  original_effects.init()
  original_goal.init()
  original_carry.init(M.visit_taken)
  original_rambi.init(level_loader.original_semantics(), area_objects, function(x, top, bottom)
    return collision.surface_at(x, top, bottom)
  end)
  if qa_ride then original_rambi.ride(player) end
  M.visit_taken = M.visit_taken or {}
  original_items.set_taken(M.visit_taken)
  original_items.init(level_loader.original_semantics(),
                      area_objects and original_areas.initial_items(area_objects))
  original_hud.on_life = function()  -- extra life balloon: GainLife $38 as the count goes up (BEC79E)
    hud.lives = hud.lives + 1
    sound.play("gain_life")
  end
  original_hud.init(hud.lives)  -- BB9210 arms both HUD timers on area entry; lives from $08C0

  local parallax = level_loader.get_parallax_speeds()
  camera.set_parallax_layers(parallax)

  objects.spawn_from_level(level_loader.get_objects())
  original_walkers.init(level_loader.original_semantics(), collision.surface_at, collision.steep_tile,
                        area_objects)
  original_klobber.init(level_loader.original_semantics(), function(x, top, bottom)
    return collision.surface_at(x, top, bottom)
  end, area_objects)
  if original_walkers.active then
    -- Neek/Klomp run in main/original_walkers.lua; retire the legacy placeholders.
    for _, obj in ipairs(objects.get_objects()) do
      local sprite = obj.type == objects.OBJ_ORIGINAL_STATIC and obj.params and obj.params.sprite
      if sprite == "Neek" or sprite == "Klomp" then
        obj.flags = bit.bor(obj.flags, objects.FLAG_COLLECTED)
      end
    end
  end
  if not keep_visit then
    hud.reset_kong()
    M.dk_coin_collected = false
    M.secret_exit_taken = false
  end

  if level_loader.is_boss_level() then
    local w, h = level_loader.get_dimensions()
    local boss_type_map = {
      boss_krow   = boss.BOSS_KROW,
      boss_kleaver = boss.BOSS_KLEAVER,
      boss_zing   = boss.BOSS_KING_ZING,
      boss_kreep  = boss.BOSS_KREEP,
      boss_krool1 = boss.BOSS_KROOL_P1,
      boss_krool2 = boss.BOSS_KROOL_P2,
    }
    local boss_type = boss_type_map[level_module] or boss.BOSS_KROW
    M.current_boss = boss.create_boss(boss_type, w, h)
    M.phase = M.PHASE.BOSS_INTRO
    M.boss_intro_timer = 2.0
  else
    M.current_boss = nil
    M.phase = M.PHASE.GAMEPLAY
  end

  M.level_loaded = true
end

-- fases em que o mundo (tiles/objetos/player) fica na tela
local WORLD_PHASES = {
  [M.PHASE.GAMEPLAY]       = true,
  [M.PHASE.PAUSE]          = true,
  [M.PHASE.DEATH]          = true,
  [M.PHASE.BOSS_INTRO]     = true,
  [M.PHASE.LEVEL_COMPLETE] = true,
}

local BANNERS = {
  [M.PHASE.PAUSE]          = "PAUSED",
  [M.PHASE.BOSS_INTRO]     = "BOSS",
  [M.PHASE.LEVEL_COMPLETE] = "LEVEL COMPLETE",
}

--- Liga/desliga o mundo e o HUD conforme a fase, e desenha o frame.
function M._sync_view()
  local world = WORLD_PHASES[M.phase] or false
  if world and not renderer.visible then
    menu.hide()
    renderer.show()
    hud_render.show()
  elseif not world and renderer.visible then
    renderer.hide()
    hud_render.hide()
  end
  if not world then return end

  local banner = BANNERS[M.phase]
  if banner then
    hud_render.banner(banner)
  else
    hud_render.clear_banner()
  end

  renderer.update(camera, M.current_boss)
  hud_render.update()
end

function M.update(dt)
  autopilot.update(M.frame_index, M.phase)
  input.post_update()
  sound.update(dt)
  -- dt real do engine p/ perf opt-in (frames/dt CPU Lua, nunca FPS GPU)
  perf.note_dt(dt)

  M.frame_index = M.frame_index + 1
  local current_phase = M.phase
  if level_loader.original_semantics() and
      (current_phase == M.PHASE.GAMEPLAY or current_phase == M.PHASE.BOSS_INTRO) then
    -- SNES gameplay advances in per-frame 8.8 units. I/O/render stalls must not
    -- multiply one controller frame into extra simulation time. perf keeps real dt.
    dt = 1 / 60
  end

  if current_phase == M.PHASE.TITLE then
    -- Opening (original boot frames) -> title screen -> NOVO JOGO -> Pirate Panic.
    opening.update()
    -- boot music (menu-sound.csv): Opening (id 17) plays from frame 145, MAIN THEME (id 2)
    -- from 766, with the title on screen
    if not original_menu.active and original_menu.available() then
      sound.play_track(opening.frame >= 766 and 2 or 17)
    end
    local pressed = input.edge_bit(input.BIT.START) or input.edge_bit(input.BIT.B)
    if original_menu.active then  -- the original screens after the title (main/original_menu.lua)
      original_menu.play_music = sound.play_track
      local result = original_menu.update(function(name) return input.edge_bit(input.BIT[name:upper()]) end)
      if original_menu.sound then sound.play(original_menu.sound); original_menu.sound = nil end
      -- menu music: SELECT on the file/mode screens, ISLAND MAP on the island and card
      -- (APPROXIMATION: switched at the screen change, not with the original fade)
      if original_menu.screen == "island" or original_menu.screen == "card" then sound.play_track(1)
      elseif (original_menu.screen == "select" or original_menu.screen == "mode")
          and not (original_menu.mode == 4 and original_menu.track > 0) then sound.play_track(24) end
      renderer.draw_layers(original_menu.layers())
      if result == "start_game" then
        sound.play_track(nil)
        hud.lives = original_menu.cheats.fifty_lives and 50 or 4  -- $08BE/$08C0 (CODE_808F7F)
        original_items.no_dk_barrels = original_menu.cheats.no_dk_barrels
        sound.play("start")
        M.checkpoint, M.visit_taken = nil, {}
        M._load_level("level_1_1")  -- Pirate Panic
      end
      M._sync_view()
      return
    end
    if not opening.at_title() then
      if pressed then opening.skip() end
    elseif original_menu.available() then  -- the original title has no prompt
      if input.edge_bit(input.BIT.START) then
        sound.play("menu_select")  -- $34 on the title START (menu-sound.csv frame 960)
        original_menu.start((opening.layers()))
      end
    else
      menu.ready = true
      if pressed then menu.on_start() end
      if menu.show_menu then
        if input.edge_bit(input.BIT.UP) then menu.on_up() end
        if input.edge_bit(input.BIT.DOWN) then menu.on_down() end
      end
    end

    menu.update(dt)
    renderer.draw_layers(opening.layers())

    if menu.should_start then
      menu.should_start = false
      menu.ready = false
      sound.play_track(nil)
      sound.play("start")
      M.checkpoint, M.visit_taken = nil, {}
      M._load_level("level_1_1")  -- Pirate Panic
    end

  elseif current_phase == M.PHASE.LEVEL_SELECT then
    level_select.update(dt)

    if input.edge_bit(input.BIT.UP) then level_select.on_up() end
    if input.edge_bit(input.BIT.DOWN) then level_select.on_down() end
    if input.edge_bit(input.BIT.START) then level_select.on_confirm() end
    if input.edge_bit(input.BIT.B) then level_select.on_back() end
    if input.edge_bit(input.BIT.Y) then
      local selected = nil
      if level_select.levels and level_select.selection then
        selected = level_select.levels[level_select.selection]
      end

      if selected and not selected.locked then
        local target_level = selected.id
        level_select.hide()
        shop.show(1, target_level)
        M.phase = M.PHASE.SHOP
      end
    end

    if level_select.should_load then
      level_select.should_load = false
      level_select.hide()
      M._load_level(level_select.selected_level)
    end

    if level_select.should_back then
      level_select.should_back = false
      level_select.hide()
      menu.init()
      M.phase = M.PHASE.TITLE
    end

    if level_select.should_scrapbook then
      level_select.should_scrapbook = false
      level_select.hide()
      scrapbook.show()
      M.phase = M.PHASE.SCRAPBOOK
    end

    if level_select.should_time_attack then
      level_select.should_time_attack = false
      level_select.hide()
      time_attack.show()
      M.phase = M.PHASE.TIME_ATTACK
    end

  elseif current_phase == M.PHASE.SCRAPBOOK then
    scrapbook.update(dt)

    if input.edge_bit(input.BIT.UP) then scrapbook.on_up() end
    if input.edge_bit(input.BIT.DOWN) then scrapbook.on_down() end
    if input.edge_bit(input.BIT.START) or input.edge_bit(input.BIT.B) then scrapbook.on_confirm() end

    if scrapbook.should_exit then
      scrapbook.should_exit = false
      scrapbook.hide()
      level_select.show()
      M.phase = M.PHASE.LEVEL_SELECT
    end

  elseif current_phase == M.PHASE.TIME_ATTACK then
    time_attack.update(dt)

    if input.edge_bit(input.BIT.UP) then time_attack.on_up() end
    if input.edge_bit(input.BIT.DOWN) then time_attack.on_down() end
    if input.edge_bit(input.BIT.START) or input.edge_bit(input.BIT.B) then time_attack.on_confirm() end

    if time_attack.should_exit then
      time_attack.should_exit = false
      time_attack.hide()
      level_select.show()
      M.phase = M.PHASE.LEVEL_SELECT
    end

  elseif current_phase == M.PHASE.BOSS_INTRO then
    M.boss_intro_timer = M.boss_intro_timer - dt
    if M.current_boss then
      local lw, lh = level_loader.get_dimensions()
      boss.update(M.current_boss, dt, player.pos_x, player.pos_y, 0, lw, lh)
    end
    player.update(dt)
    M.contact_pose = original_animation.snapshot().pose  -- contact uses the pre-step pose
    original_animation.update(player)
    objects.update(dt, camera.pos_x, camera.viewport_w, level_loader.original_semantics())
    local px, py = player.pos_x, player.pos_y
    camera.follow(px, py, camera.viewport_w, camera.viewport_h, dt)
    player_render.update(dt, camera)
    if M.boss_intro_timer <= 0 then
      M.phase = M.PHASE.GAMEPLAY
    end

  elseif current_phase == M.PHASE.LEVEL_COMPLETE then
    local event, entity
    if original_goal.active then
      event, entity = original_goal.update(player)
      original_items.update(camera.pos_x, camera.pos_y, false)
      original_effects.update(false)
      original_hud.update(require("main.original_camera").clock or 0)
      if event == "collect_bunch" then M._collect_bunch(entity) end
      original_hud.move_flying()
      original_coin_hud.update()
      camera.follow(player.pos_x, player.pos_y, camera.viewport_w, camera.viewport_h, dt)
      player_render.update(dt, camera)
    else
      M.level_complete_timer = M.level_complete_timer - dt
    end
    if original_animation.forced then original_animation.update(player) end
    if event == "done" or (not original_goal.active and M.level_complete_timer <= 0) then
      local level_id = level_loader.get_id()
      save_manager.complete_level(level_id, M.dk_coin_collected, M.secret_exit_taken)
      level_loader.unload()
      M._to_title()
    end

  elseif current_phase == M.PHASE.SHOP then
    shop.update(dt)

    if input.edge_bit(input.BIT.UP) then shop.on_up() end
    if input.edge_bit(input.BIT.DOWN) then shop.on_down() end
    if input.edge_bit(input.BIT.LEFT) then shop.on_left() end
    if input.edge_bit(input.BIT.RIGHT) then shop.on_right() end
    if input.edge_bit(input.BIT.START) or input.edge_bit(input.BIT.B) then shop.on_confirm() end
    if input.edge_bit(input.BIT.Y) then shop.on_back() end

    if shop.should_exit then
      shop.should_exit = false
      shop.hide()
      level_select.show()
      M.phase = M.PHASE.LEVEL_SELECT
    end

  elseif current_phase == M.PHASE.GAME_OVER then
    game_over.update(dt)

    if input.edge_bit(input.BIT.UP) then game_over.on_up() end
    if input.edge_bit(input.BIT.DOWN) then game_over.on_down() end
    if input.edge_bit(input.BIT.START) then game_over.on_confirm() end

    if game_over.should_continue then
      game_over.should_continue = false
      game_over.hide()
      hud.lives = 3
      hud.bananas = 0
      hud.dk_coins = save_manager.get_dk_coins()
      hud.score = 0
      save_manager.save_runtime(3, 0, hud.dk_coins, 0)
      M.game_over = false
      M._restart_level()
    end

    if game_over.should_quit then
      game_over.should_quit = false
      game_over.hide()
      level_loader.unload()
      M._to_title()
    end

  elseif M.phase == M.PHASE.GAMEPLAY then
    if M.game_over then
      M.transition_timer = M.transition_timer + dt
      if M.transition_timer > 2 then
        M.transition_timer = 0
        M.phase = M.PHASE.GAME_OVER
        game_over.show()
      end
      M._sync_view()
      return
    end

    if M.transition_timer > 0 then
      M.transition_timer = M.transition_timer - dt
      if M.transition_timer <= 0 then end
    end

    M.actor_frozen = (player.hitpause_frames or 0) > 0  -- stomp hit-stop holds sprites too
    if M.cannon then  -- inside a barrel cannon: the cannon drives the Kong
      M._update_cannon()
    elseif M.door_walk then  -- walking through a door
      M._update_door_walk()
    elseif player.throw_freeze and original_animation.forced == 0x14 then  -- throw wind-up: held, vx/vy kept
    elseif original_partner.busy() or original_partner.hanging() or original_partner.tagging() then
      -- hand-over / throwing / SELECT swap: the leader is held
      player.vel_x, player.vel_y = 0, 0
    else
      player.update(dt)
    end
    -- $0935: the feet y while grounded, the highest one while airborne (goal-route-t5.csv)
    local feet = player.pos_y + 24
    M.jump_peak = (player.grounded or not M.jump_peak) and feet or math.min(M.jump_peak, feet)

    M.contact_pose = original_animation.snapshot().pose  -- contact uses the pre-step pose
    -- the stomp hit-stop holds the Kong's frame too (reference-poses.csv 566-569)
    if not M.actor_frozen then original_animation.update(player) end
    if original_animation.forced ~= 0x14 then player.throw_freeze = nil end  -- wind-up cut short
    if not M.cannon and not M.door_walk then  -- inside a cannon / walking a door: no buttons
      if input.edge_bit(input.BIT.SELECT) then original_partner.swap(player) end
      if input.edge_bit(input.BIT.A) and not original_rambi.mounted() then  -- on Rambi, A charges
        original_partner.team_up(player)
      end
      if input.edge_bit(input.BIT.Y) then original_partner.throw(player, input.hold_bit(input.BIT.UP)) end
    end
    original_partner.update(player, M._thrown_kong_hit)
    objects.update(dt, camera.pos_x, camera.viewport_w, level_loader.original_semantics())

    hud.breath = player.breath
    hud.is_swimming = player.state == player.STATE.SWIM or player.state == player.STATE.ENGUARDE_RIDING
    hud.mount_type = player.state == player.STATE.MOUNTED and player.mount_type or nil

    local px, py = player.pos_x, player.pos_y

    if M.current_boss then
      local w, h = level_loader.get_dimensions()
      boss.update(M.current_boss, dt, px, py, 368, w, h, function(type_id, tile_col, tile_row)
        return objects.spawn(type_id, tile_col * 16, tile_row * 16)
      end)
    end

    local hx, hy, hw, hh = player.get_hitbox()
    local events = objects.check_player_collision(hx, hy, hw, hh)

    for _, ev in ipairs(events) do
      if ev.type == "collect_banana" then
        hud.add_bananas(ev.count)
        sound.play("collect")
      elseif ev.type == "collect_dk_coin" then
        hud.add_dk_coin()
        M.dk_coin_collected = true
        sound.play("collect")
      elseif ev.type == "collect_letter" then
        hud.collect_letter(ev.letter)
        sound.play("collect")
      elseif ev.type == "collect_life" then
        hud.add_life()
        sound.play("collect")
      elseif ev.type == "enemy_hit" then
        local obj = ev.object
        local is_mounted = player.state == player.STATE.RAMBI_RIDING or player.state == player.STATE.MOUNTED
        if obj.type == objects.OBJ_KLAMP and not is_mounted then
          local dead = player.take_damage()
          sound.play("damage")
          if dead then M._player_died() end
        elseif is_mounted then
          local result, bounce_type = objects.stomp_enemy(obj)
          if result == "kill" then hud.add_score(100) end
          sound.play("stomp")
        elseif player.vel_y > 0 and not player.grounded then
          local result, bounce_type = objects.stomp_enemy(obj)
          if result == "kill" or result == "hit" then
            if bounce_type == "neek_bounce" then
              -- Original Diddy bounce is raw $F7C8 with two frozen update frames after impact.
              player.bounce(original_motion.jump_velocity(), 2)
            else
              player.bounce()
            end
            if result == "kill" then hud.add_score(100) end
            sound.play("stomp")
          else
            local dead = player.take_damage()
            sound.play("damage")
            if dead then M._player_died() end
          end
        else
          local dead = player.take_damage()
          sound.play("damage")
          if dead then M._player_died() end
        end
      elseif ev.type == "projectile_hit" then
        local dead = player.take_damage()
        sound.play("damage")
        if dead then M._player_died() end
      elseif ev.type == "barrel" and input.hold_bit(input.BIT.UP) then
        player.state = player.STATE.BARREL
        player.vel_x = 0
        player.vel_y = 0
        player.barrel_angle = 3
      elseif ev.type == "mount_rambi" then
        ev.object.flags = bit.bor(ev.object.flags, objects.FLAG_COLLECTED)
        player.state = player.STATE.RAMBI_RIDING
        player.mount_type = "rambi"
        player.vel_x = 0
        player.vel_y = 0
        sound.play("collect")
      elseif ev.type == "mount_enguarde" then
        ev.object.flags = bit.bor(ev.object.flags, objects.FLAG_COLLECTED)
        player.state = player.STATE.ENGUARDE_RIDING
        player.mount_type = "enguarde"
        player.vel_x = 0
        player.vel_y = 0
        player.breath = 100
        sound.play("collect")
      elseif ev.type == "mount_animal" then
        ev.object.flags = bit.bor(ev.object.flags, objects.FLAG_COLLECTED)
        player.state = player.STATE.MOUNTED
        player.mount_type = ev.animal
        player.vel_x = 0
        player.vel_y = 0
        local animals = require("main.animals")
        local animal = animals.get(ev.animal)
        if animal and animal.on_mount then
          animal.on_mount(player)
        end
        sound.play("collect")
      elseif ev.type == "bonus_barrel" and input.hold_bit(input.BIT.UP) then
        M._enter_bonus_stage()
      elseif ev.type == "animal_crate" then
        local animal_names = { "squitter", "rattly", "squawks", "expresso" }
        local idx = math.random(#animal_names)
        player.state = player.STATE.MOUNTED
        player.mount_type = animal_names[idx]
        player.vel_x = 0
        player.vel_y = 0
        sound.play("collect")
      end
    end
    if original_walkers.active and not M.cannon then  -- no contacts inside a barrel cannon
      -- Walker contact (main/original_walkers.lua): player position after its move,
      -- pose before this frame's animation step, as in the original sprite pass.
      local contacts = original_walkers.contact(player.pos_x, player.pos_y + 24, M.contact_pose or 0,
                                                player.direction < 0, player.vel_y * 256 / 60,
                                                not player.grounded)
      -- BurstEffect at the contact (route-bot-trace.csv 566/938/1260): centre of the box
      -- overlap in x, 3 px above the player's feet.
      local function contact_burst(walker)
        local pl, _, pr = original_walkers.box(M.contact_pose or 0, player.pos_x, player.pos_y + 24,
                                               player.direction < 0)
        local el, _, er = original_walkers.box(walker.pose, bit.rshift(walker.x, 8) - 256,
                                               bit.rshift(walker.y, 8) - 256, bit.band(walker.attributes, 0x4000) ~= 0)
        local cx = (pl and el) and (math.max(pl, el) + math.min(pr, er)) * 0.5 or player.pos_x
        original_effects.spawn("burst", cx, player.pos_y + 24 - 3)
      end
      for _, contact in ipairs(contacts) do
        if autopilot.enabled then  -- QA log only (qa-runtime.json)
          M.qa_contacts = M.qa_contacts or {}
          M.qa_contacts[#M.qa_contacts + 1] = { frame = M.frame_index, kind = contact.kind,
            x = player.pos_x, feet = player.pos_y + 24, vy_raw = player.vel_y * 256 / 60,
            pose = M.contact_pose or 0, grounded = player.grounded,
            walker_x = bit.rshift(contact.walker.x, 8) - 256, walker_y = bit.rshift(contact.walker.y, 8) - 256,
            walker_pose = contact.walker.pose }
        end
        if contact.kind == "stomp" then
          contact_burst(contact.walker)
          original_walkers.defeat(contact.walker, player.direction < 0)
          original_areas.on_defeat(original_items.add)
          sound.play("kill_neek")
          -- Player action $1B: Diddy bounce is raw $F7C8 with two frozen update frames.
          player.bounce(original_motion.jump_velocity(), 2)
          hud.add_score(100)
          sound.play("stomp")
        elseif original_rambi.mounted() or player.rolling then  -- Rambi / cartwheel knock walkers out
          original_walkers.defeat(contact.walker, player.direction < 0)
          original_areas.on_defeat(original_items.add)
          sound.play("stomp")
        elseif not M.qa_invulnerable then
          contact_burst(contact.walker)
          local dead = player.take_damage()
          sound.play("damage")
          if dead then M._player_died() end
          break
        end
      end
    end
    if original_klobber.active then
      local pl, pt, pr, pb = original_walkers.box(M.contact_pose or 0, player.pos_x, player.pos_y + 24,
                                                  player.direction < 0)
      local klobber = pl and original_klobber.stomp_check(nil, pl, pt, pr, pb, not player.grounded,
                                                          player.vel_y * 256 / 60)
      if klobber then  -- contact word $020F: stomp breaks the barrel; touching is harmless
        original_klobber.defeat(klobber)
        original_effects.spawn_break(klobber.x, klobber.y - 16)
        original_areas.on_defeat(original_items.add)
        sound.play("barrel_break")
        player.bounce(original_motion.jump_velocity(), 2)
        hud.add_score(100)
        sound.play("stomp")
      end
    end
    if level_loader.original_semantics() then  -- also rooms without walkers (Kabin, bonus 1)
      M._check_original_goal()
      M._update_original_carry()
      M._check_original_items()
      M._check_original_areas()
    end
    autopilot.record_neek_interaction(M.frame_index - 1, events, player,
                                      objects.get_objects(), input.get_hold(), input.get_edge())

    -- Source order: the HUD pass (BEC68A) runs before the banana pickup (B5F928).
    if level_loader.original_semantics() then
      original_hud.update(require("main.original_camera").clock or 0)
      local bananas_taken, positions = 0, nil
      if original_bananas.active then
        bananas_taken, positions = original_bananas.collect(original_bananas.player_box(
          original_animation.snapshot().id, player.direction < 0, player.pos_x, player.pos_y + 24))
      end
      if bananas_taken > 0 then
        -- Flight starts from the banana's screen position; the camera has not moved yet
        -- this frame (B5E4ED runs after the actors), as in the source.
        local screen = {}
        for index, position in ipairs(positions) do
          screen[index] = { position[1] - camera.pos_x, position[2] - camera.pos_y }
        end
        original_hud.collect_banana(screen)
        hud.add_bananas(bananas_taken)
        sound.play("collect")
      end
      original_hud.move_flying()
      original_kong_hud.update()
      original_coin_hud.update()
      original_items.update(camera.pos_x, camera.pos_y, M.actor_frozen)
      -- The walker lifecycle reads the camera one frame older than camera.pos_x here
      -- (measured: reference replay, 2nd Neek spawns on 864 not 863; with this the
      -- trajectory is 1034/1034 within 1 px and the stomps land on 566/938).
      original_walkers.update(M.walker_camera_x or camera.pos_x, M.actor_frozen,
                              require("main.original_camera").clock or 0)
      M.walker_camera_x = camera.pos_x
      original_klobber.update(camera.pos_x, player.pos_x, player.pos_y + 24, M.actor_frozen)
      original_effects.update(M.actor_frozen)
    end

    -- Source order: the camera (B5E4ED) runs after contact handling, so a stomp
    -- hit-stop already freezes it on the impact frame (reference frames 566/938).
    camera.follow(player.pos_x, player.pos_y, camera.viewport_w, camera.viewport_h, dt)
    player_render.update(dt, camera)

    -- Prototype levels may use a simple X end marker. Pirate Panic must not:
    -- the SNES LevelEndGoal is an actual stateful sprite/collision interaction,
    -- not “player crossed header coordinate”. Its complete handler is pending.
    local goal = level_loader.get_goal()
    if not level_loader.original_semantics() and goal and goal.x and goal.x > 0
        and player.pos_x >= goal.x then
      M._complete_level()
    end

    if M.current_boss then
      local bh = boss.get_hitbox(M.current_boss)
      if bh and hx and hy then
        if hx < bh.x + bh.w and hx + hw > bh.x and hy < bh.y + bh.h and hy + hh > bh.y then
          if player.state == player.STATE.RAMBI_RIDING or player.state == player.STATE.MOUNTED then
            boss.take_damage(M.current_boss)
            sound.play("stomp")
            player.bounce()
          elseif player.vel_y > 0 and not player.grounded then
            local hit = boss.take_damage(M.current_boss)
            if hit then
              player.bounce()
              sound.play("stomp")
            end
          else
            local dead = player.take_damage()
            sound.play("damage")
            if dead then M._player_died() end
          end
        end
      end
      local projs = boss.get_projectile_hitboxes(M.current_boss)
      for _, proj in ipairs(projs) do
        if proj then
          if hx < proj.x + proj.w and hx + hw > proj.x and hy < proj.y + proj.h and hy + hh > proj.y then
            local dead = player.take_damage()
            sound.play("damage")
            if dead then M._player_died() end
          end
        end
      end
      if not M.current_boss.alive then
        boss.cleanup(M.current_boss)
        M.current_boss = nil
        M._complete_level()
      end
    end

    if player.health <= 0 and player.invincible_timer <= 0 then
      M._player_died()
    end

  elseif M.phase == M.PHASE.DEATH and M.death then
    M._update_original_death()
    -- the camera keeps following the falling Kong (route-bot-trace.csv 1260-1335: the
    -- Kong backs 56 px, the camera 59 px)
    camera.follow(player.pos_x, player.pos_y, camera.viewport_w, camera.viewport_h, dt)
    player_render.update(dt, camera)
  elseif M.phase == M.PHASE.DEATH then
    M.transition_timer = M.transition_timer - dt
    if M.transition_timer <= 0 then
      local game_over = hud.lose_life()
      if game_over then
        M.game_over = true
        M.phase = M.PHASE.GAMEPLAY
        M.transition_timer = 0
      else
        M._restart_level()
      end
    end
  end

  if current_phase == M.PHASE.PAUSE then
    if input.edge_bit(input.BIT.START) then
      M.phase = M.PHASE.GAMEPLAY
    end

  elseif current_phase == M.PHASE.BONUS then
    local result = bonus.update(dt, input)
    if result == "complete" then
      hud.add_dk_coin()
      sound.play("collect")
      M._exit_bonus_stage(true)
    elseif result == "timeout" then
      M._exit_bonus_stage(false)
    end

  elseif current_phase == M.PHASE.GAMEPLAY then
    if input.edge_bit(input.BIT.START) then
      M.phase = M.PHASE.PAUSE
    end
  end

  M._sync_view()
end

--- Back to the title screen (skipping the logos), menu closed.
function M._to_title()
  sound.stop_original_music()
  menu.init()
  opening.init(true)
  M.phase = M.PHASE.TITLE
end

-- LevelEndGoal ($160, B3A275): the player, airborne and falling ($1E & $101 = 0,
-- $24 >= 0), touches the goal's pose box -> level end (main/original_goal.lua).
-- APPROXIMATION: the end fade is not ported.
function M._check_original_goal()
  if player.grounded or player.vel_y < 0 or M.phase ~= M.PHASE.GAMEPLAY then return end
  local pl, pt, pr, pb = original_walkers.box(M.contact_pose or 0, player.pos_x, player.pos_y + 24,
                                              player.direction < 0)
  if not pl then return end
  original_items.each_alive("level_end_goal", function(goal, pose)
    local gl, gt, gr, gb = original_walkers.box(pose, goal.x, goal.feet_y, false)
    if gl and pr >= gl and gr >= pl and gb >= pt and pb >= gt and M.phase == M.PHASE.GAMEPLAY then
      original_goal.start(goal, player, M.jump_peak or player.pos_y + 24)
      sound.play_victory()  -- the level song jumps to its victory part ($FB 3, goal-route-t8.csv 4916)
      M._complete_level()
    end
  end)
end

function M._collect_bunch(entity)
  local screen = {}
  for index = 1, 10 do screen[index] = { entity.x - camera.pos_x, entity.feet_y - 12 - camera.pos_y } end
  original_hud.collect_banana(screen)
  hud.add_bananas(10)
  sound.play("collect")
end

-- Collectibles and barrels by pose-box overlap (APPROXIMATION: their own sprite
-- routines are not translated; boxes are the original DATA_BCB600 ones).
local LETTERS = { kong_k = "K", kong_o = "O", kong_n = "N", kong_g = "G" }
local LETTER_INDEX = { K = 1, O = 2, N = 3, G = 4 }
function M._check_original_items()
  local pl, pt, pr, pb = original_walkers.box(M.contact_pose or 0, player.pos_x, player.pos_y + 24,
                                              player.direction < 0)
  if not pl then return end
  local function touching(entity, pose)
    local l, t, r, b = original_walkers.box(pose, entity.x, entity.feet_y, false)
    return l and pr >= l and r >= pl and b >= pt and pb >= t
  end
  for kind, letter in pairs(LETTERS) do
    original_items.each_alive(kind, function(entity, pose)
      if touching(entity, pose) then
        original_items.remove(entity)
        hud.collect_letter(letter)
        original_kong_hud.collect(LETTER_INDEX[letter], entity.x - camera.pos_x, entity.feet_y - camera.pos_y,
                                  entity.frames[entity.index])
        sound.play("collect_" .. letter:lower())
      end
    end)
  end
  -- Banana bunch ($170 at 1504/384): 10 bananas. APPROXIMATION: never picked on the
  -- captured routes, so the count flies as 10 bananas from its screen position.
  -- K. Rool's note (Kabin, kabin-route-t5.csv): walking into it shows his message at
  -- once, for the rest of the visit (original_areas.note_shown, drawn with the HUD).
  original_items.each_alive("krool_note", function(entity, pose)
    if touching(entity, pose) and not original_areas.note_shown then
      original_areas.note_shown = true
      sound.play("read_note")  -- ReadKRoolNote $2E (kabin-route-t6.csv 826)
    end
  end)
  -- Extra life balloon ($178, in the Kabin): flies to the lives panel (main/original_hud.lua).
  original_items.each_alive("extra_life_balloon", function(entity, pose)
    if touching(entity, pose) then
      original_items.remove(entity)
      original_hud.collect_balloon(entity.x - camera.pos_x, entity.feet_y - camera.pos_y, entity.frames)
      sound.play("collect_balloon")  -- CollectBalloon $2C (NorSpr0178)
      sound.play("collect")
    end
  end)
  original_items.each_alive("banana_bunch", function(entity, pose)
    if touching(entity, pose) then
      original_items.remove(entity)
      M._collect_bunch(entity)
    end
  end)
  for _, kind in ipairs({ "banana_coin", "kremkoin", "dk_coin" }) do
    original_items.each_alive(kind, function(entity, pose)
      if touching(entity, pose) then
        original_items.remove(entity)
        if kind == "dk_coin" then
          hud.add_dk_coin()
          M.dk_coin_collected = true
          sound.play("collect_dk_coin")
        elseif kind == "kremkoin" then
          hud.kremkoins = (hud.kremkoins or 0) + 1
          original_areas.on_kremkoin()
        else
          hud.banana_coins = (hud.banana_coins or 0) + 1
          original_coin_hud.collect(entity.x - camera.pos_x, entity.feet_y - camera.pos_y, entity.frames)
          sound.play("collect_banana_coin")
        end
      end
    end)
  end
  -- Animal buddy crate: stomped open, Rambi steps out (main/original_rambi.lua).
  original_items.each_alive("animal_buddy_box", function(entity, pose)
    if touching(entity, pose) and not player.grounded and player.vel_y > 0 then
      original_items.remove(entity)
      original_rambi.free(entity.x, entity.feet_y)
      original_effects.spawn_break(entity.x, entity.feet_y - 16)
      player.bounce(original_motion.jump_velocity(), 2)
      sound.play("open_buddy_box")
    end
  end)
  -- No Animal sign: the ride ends.
  if original_rambi.mounted() then
    original_items.each_alive("no_animal_sign", function(entity, pose)
      if touching(entity, pose) then original_rambi.dismount() end
    end)
  end
  -- Star barrel: breaks and becomes the respawn point for this level visit.
  original_items.each_alive("star_barrel", function(entity, pose)
    if touching(entity, pose) then
      original_items.remove(entity)
      M.checkpoint = { x = entity.x, y = entity.feet_y - 24 }
      original_effects.spawn_break(entity.x, entity.feet_y - 16)
      sound.play("barrel_break")
    end
  end)
  -- DK barrel: breaks when landed on and releases the partner (it can also be carried and
  -- thrown: main/original_carry.lua).
  original_items.each_alive("dk_barrel", function(entity, pose)
    if touching(entity, pose) and not player.grounded and player.vel_y > 0 then
      original_items.remove(entity)
      original_partner.release(entity.x, entity.feet_y)
      original_effects.spawn_break(entity.x, entity.feet_y - 16)
      sound.play("dk_barrel")
    end
  end)
end

-- Area changes (main/original_areas.lua): portal cannons into the bonus/warp rooms and
-- the way back to the main area at the linked header record.
function M._enter_area(dest, return_record)
  M.area_return = return_record
  local riding = dest == "bonus_2" and original_rambi.mounted()  -- only the Rambi wall is measured
  M._load_level("pirate_" .. dest, true)
  if riding then original_rambi.ride(player) end
end

function M._exit_area()
  local record = M.area_return
  M._load_level("level_1_1", true)
  local x, feet = original_areas.return_point(record or 0)
  if x then
    player.spawn(x, feet - 24)
    player.grounded = false
    camera.snap_to(x, math.max(feet - 24, 0))
  end
end

local function drain_sound(module)
  if module.sound_request then
    sound.play(module.sound_request)
    module.sound_request = nil
  end
end

-- A thrown partner Kong knocks out the enemy it touches (main/original_partner.lua).
-- APPROXIMATION: the thrown Kong's box for cannons is x -8..+8, feet -33..0 (the warp
-- took the partner with its feet at 283, the cannon box bottom at 250: upthrow-route-t6).
function M._thrown_kong_hit(x, feet)
  if not M.cannon and level_loader.original_semantics() and not level_loader.get_subarea() then
    local dest, return_record, portal = original_areas.portal(x - 8, feet - 33, x + 8, feet)
    if dest then
      original_partner.enter_cannon(portal.x, portal.feet_y)
      original_areas.reveal(portal)
      M.cannon = { frame = 0, pull = 0, x = portal.x, feet = portal.feet_y, dest = dest,
                   return_record = return_record, portal = portal }
      original_animation.force(0x40, player)
      sound.play("load_cannon")
      return "cannon"
    end
  end
  local walker = original_carry.hit_walker(original_walkers, { x - 8, feet - 24, x + 8, feet })
  if walker then
    original_walkers.defeat(walker, x < bit.rshift(walker.x, 8) - 256)
    original_areas.on_defeat(original_items.add)
    sound.play("stomp")
  end
end

-- Wooden box carry/throw (main/original_carry.lua).
function M._update_original_carry()
  local team = original_partner.carried()
  local events = original_carry.update(player, original_items, original_walkers, collision.surface_at,
                                       input.hold_bit(input.BIT.Y) and not original_partner.owns_y())
  for _, event in ipairs(events) do
    if event.kind == "pickup" then
      if player.rolling then player.rolling = false end  -- Y at a box picks it up
      original_animation.force(0x0F, player)
    elseif event.kind == "throw_start" then
      original_animation.force(0x14, player)
      if original_animation.forced ~= 0x14 then player.throw_release = true end  -- no script: at once
    elseif event.kind == "break" then
      original_effects.spawn_break(event.x, event.y)
      sound.play(event.item == "dk_barrel" and "dk_barrel" or "barrel_break")
      if event.item == "dk_barrel" then original_partner.release(event.x, event.feet) end
      if event.walker then
        original_walkers.defeat(event.walker, player.direction < 0)
        original_areas.on_defeat(original_items.add)
      end
    end
  end
  if original_animation.forced == 0x0F and not original_carry.picking_up() then original_animation.release() end
  player.carrying = original_carry.carrying() or team
  player.team_up = team
  player.roll_blocked = original_partner.owns_y()
end

function M._check_original_areas()
  if M.just_moved then M.just_moved = false; return end  -- the area changed earlier this frame
  drain_sound(original_walkers)
  drain_sound(original_klobber)
  drain_sound(original_rambi)
  if original_rambi.break_at then
    original_effects.spawn_break(original_rambi.break_at[1], original_rambi.break_at[2], false)
    original_rambi.break_at = nil
  end
  drain_sound(original_areas)
  if M.phase ~= M.PHASE.GAMEPLAY then return end
  if original_rambi.update(player, input.hold_bit(input.BIT.A)) == "enter_bonus" then
    local dest, return_record = original_rambi.wall_link()
    M._enter_area(dest, return_record)  -- the Kong arrives on Rambi
    return
  end
  -- Doors are walked through: holding toward one within reach starts the door walk.
  local held = input.hold_bit(input.BIT.LEFT) and -1 or input.hold_bit(input.BIT.RIGHT) and 1 or 0
  if not M.door_walk and player.grounded and held ~= 0 then
    local action, door_dest, door_return, dir = original_areas.door(player.pos_x, player.pos_y + 24, held)
    if action then
      M.door_walk = { frame = 0, dir = dir, action = action, dest = door_dest, return_record = door_return }
      return
    end
  end
  if level_loader.get_subarea() then
    if original_areas.update(player.pos_x) == "exit" then M._exit_area() end
    return
  end
  local pl, pt, pr, pb = original_walkers.box(M.contact_pose or 0, player.pos_x, player.pos_y + 24,
                                              player.direction < 0)
  local dest, return_record, portal
  if pl then dest, return_record, portal = original_areas.portal(pl, pt, pr, pb) end
  if dest and not M.cannon then
    original_areas.reveal(portal)
    M.cannon = { frame = 0, x = portal.x, feet = portal.feet_y, dest = dest, return_record = return_record }
    player.pos_x, player.pos_y, player.vel_x, player.vel_y = portal.x, portal.feet_y - 24, 0, 0
    player.hidden = true
    original_effects.spawn("burst", portal.x + 6, portal.feet_y - 20)
    sound.play("load_cannon")
  end
end

-- Portal barrel cannon (cannon-route-t1.csv, bonus-1 cannon): the Kong snaps into the
-- cannon (burst at +6/-20), waits 22 frames, then is shot straight up at vy -1976 (8.8,
-- no gravity) with anim $19 and a smoke puff rising 1 px per frame from the mouth; the
-- area changes 49 frames after the shot (the Kong is off screen by then).
-- APPROXIMATIONS: the shot is always straight up (both Pirate Panic cannons point up?
-- only the bonus-1 one is captured); the ~45-frame fade before the new area is not ported.
-- Door walk (kabin-route-t1.csv 448-494 / t3 596-638): the Kong walks on through the
-- door at 1.5 px per frame (state $33, anim $3C) for 46 frames, then the area changes.
-- APPROXIMATION: the fade before the new room (45-130 frames) is not ported.
local DOOR_WALK_SPEED, DOOR_WALK_FRAMES = 1.5, 46
function M._update_door_walk()
  local walk = M.door_walk
  walk.frame = walk.frame + 1
  player.vel_x, player.vel_y, player.direction = 0, 0, walk.dir
  player.pos_x = player.pos_x + DOOR_WALK_SPEED * walk.dir
  if walk.frame == 1 then
    original_animation.force(0x3C, player)
    player.door_clip = original_areas.door_clip(walk.dir)
  end
  if walk.frame >= DOOR_WALK_FRAMES then
    M.door_walk, M.just_moved, player.door_clip = nil, true, nil
    if original_animation.forced == 0x3C then original_animation.release() end
    if walk.action == "enter" then M._enter_area(walk.dest, walk.return_record) else M._exit_area() end
  end
end

-- A thrown partner in the cannon pulls the leader in first (upthrow-route-t6.csv 2314-2335,
-- anim $40): both axes step (256 + 96 k) / 256 px toward the cannon until the boxes meet.
local CANNON_WAIT, CANNON_VY, CANNON_LEAVE = 22, -1976 / 256, 49
local PULL_SPEED, PULL_ACCEL = 256 / 256, 96 / 256
local function approach(value, target, step)
  if math.abs(target - value) <= step then return target end
  return value + (target > value and step or -step)
end
function M._update_cannon()
  local cannon = M.cannon
  player.vel_x, player.vel_y = 0, 0
  if cannon.pull then
    local step = PULL_SPEED + PULL_ACCEL * cannon.pull
    cannon.pull = cannon.pull + 1
    player.pos_x = approach(player.pos_x, cannon.x, step)
    player.pos_y = approach(player.pos_y, cannon.feet - 24, step)
    local pl, pt, pr, pb = player.pos_x - 8, player.pos_y + 24 - 33, player.pos_x + 8, player.pos_y + 24
    -- shortcut: the 60-frame cap only guards against a pull that never meets the box
    if original_areas.portal(pl, pt, pr, pb) or cannon.pull > 60 then
      cannon.pull = nil
      player.pos_x, player.pos_y, player.hidden = cannon.x, cannon.feet - 24, true
    end
    return
  end
  cannon.frame = cannon.frame + 1
  if cannon.frame == CANNON_WAIT then
    player.hidden = false
    original_animation.force(0x19, player)
    original_effects.spawn("smoke_rise", cannon.x, cannon.feet)
    sound.play("barrel_shoot")
  elseif cannon.frame > CANNON_WAIT then
    player.pos_y = player.pos_y + CANNON_VY
  end
  if cannon.frame >= CANNON_WAIT + CANNON_LEAVE then
    M.cannon, player.hidden, M.just_moved = nil, false, true
    M._enter_area(cannon.dest, cannon.return_record)
  end
end

function M._complete_level()
  autopilot.mark_level_completed()
  M.phase = M.PHASE.LEVEL_COMPLETE
  M.level_complete_timer = 2.0
end

-- Original death (player state 5, animation $0A), measured on route-bot-trace.csv frames
-- 1260-1490 (APPROXIMATION: the state-5 physics routine is not translated): pop 6 px,
-- hold 6 frames, rise at vy -$540 with gravity $40 and vx -$100 away from the facing,
-- one bounce of vy -$290 on landing, life lost 60 frames after the hit, restart at 230.
local DEATH_POP, DEATH_HOLD, DEATH_VY, DEATH_GRAVITY = 6, 6, -0x540 / 256, 0x40 / 256
local DEATH_BOUNCE, DEATH_LIFE_FRAME, DEATH_END_FRAME = -0x290 / 256, 60, 230

function M._update_original_death()
  local death = M.death
  death.frame = death.frame + 1
  if death.frame == DEATH_HOLD + 1 then
    death.vy, death.vx = DEATH_VY, -player.direction
  elseif death.frame > DEATH_HOLD + 1 and not death.resting then
    player.pos_x = player.pos_x + death.vx
    player.pos_y = player.pos_y + death.vy
    death.vy = death.vy + DEATH_GRAVITY
    local feet = player.pos_y + 24
    local floor = collision.surface_at(math.floor(player.pos_x), feet - 8, feet + 8)
    player.grounded = false
    if death.vy > 0 and floor and feet >= floor then
      player.pos_y, player.grounded = floor - 24, true
      death.landings = death.landings + 1
      if death.landings == 1 then
        death.vy, death.vx = DEATH_BOUNCE, death.vx * 0.5
      else
        death.resting = true
      end
    end
  end
  player.vel_y = (death.vy or 0) * 60
  original_animation.update(player)
  if death.frame == DEATH_LIFE_FRAME then
    death.game_over = hud.lose_life()
    sound.play("lost_life")
    save_manager.save_runtime(hud.lives, hud.bananas, hud.dk_coins, hud.score)
  end
  if death.frame >= DEATH_END_FRAME then
    M.death = nil
    if death.game_over then
      M.phase = M.PHASE.GAME_OVER
      game_over.show()
    else
      M._restart_level()
    end
  end
end

function M._player_died()
  if M.phase == M.PHASE.DEATH then return end  -- a contact and the health check can both fire in one frame
  if level_loader.original_semantics() and original_partner.lose(player) then  -- partner takes over
    player.health = player.max_health
    player.invincible_timer = 2
    return
  end
  if level_loader.original_semantics() then
    M.phase = M.PHASE.DEATH
    M.death = { frame = 0, landings = 0 }
    player.state = player.STATE.DEATH
    -- no hurt blink in the original death: the timer would freeze (player.update stops)
    -- and could leave the Kong invisible for the whole fall (qa-66)
    player.invincible_timer = 0
    player.vel_x, player.vel_y, player.grounded = 0, 0, false
    player.pos_y = player.pos_y - DEATH_POP
    original_animation.force(0x0A, player)
    sound.play("diddy_dead")
    return
  end
  M.phase = M.PHASE.DEATH
  M.transition_timer = 1.5
  save_manager.save_runtime(hud.lives, hud.bananas, hud.dk_coins, hud.score)
  player_render.destroy()
end

function M._restart_level()
  local level_module = M.current_level_module or "level_1_1"
  if level_loader.get_subarea() then level_module = "level_1_1" end  -- died in a bonus/warp room
  local checkpoint = M.checkpoint
  original_partner.present, original_partner.leader = false, "diddy"  -- see original_partner.lua
  objects.clear()
  collision.clear()
  M._load_level(level_module, true)
  if checkpoint then  -- star barrel touched before dying
    M.checkpoint = checkpoint
    player.spawn(checkpoint.x, checkpoint.y)
    camera.snap_to(checkpoint.x, checkpoint.y)
  end
  hud.reset()
  M.transition_timer = 0
end

local bonus = require("main.bonus")
local bonus_stages = require("main.bonus_stages")

function M._enter_bonus_stage()
  if M.phase ~= M.PHASE.GAMEPLAY then return end
  M._saved_phase_state = {
    level_module = M.current_level_module,
    player_x = player.pos_x,
    player_y = player.pos_y,
    player_vel_x = player.vel_x,
    player_vel_y = player.vel_y,
  }
  local stage = bonus_stages.get_random()
  bonus.start(stage)
  M.phase = M.PHASE.BONUS
end

function M._exit_bonus_stage(success)
  if M._saved_phase_state then
    player.pos_x = M._saved_phase_state.player_x
    player.pos_y = M._saved_phase_state.player_y
    player.vel_x = M._saved_phase_state.player_vel_x
    player.vel_y = M._saved_phase_state.player_vel_y
    M._saved_phase_state = nil
  end
  bonus.reset()
  M.phase = M.PHASE.GAMEPLAY
end

function M.on_input(action_id, action)
  input.on_input(action_id, action)
end

function M.get_hud_data()
  return hud.get_hud_data()
end

return M
