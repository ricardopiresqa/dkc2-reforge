--- Renderizacao do mundo: parallax, tiles, objetos, player e boss.
--
-- Tudo e desenhado em coordenadas de TELA (mundo - camera), num pool de game
-- objects criados por `#entity_factory`. A cada frame o pool e reutilizado na
-- ordem em que os elementos sao desenhados; o que sobra do frame anterior e
-- desabilitado. Nenhuma logica de jogo vive aqui.
--
-- ATENCAO ao eixo Y. O mundo do jogo segue a convencao do SNES: `y` cresce
-- para BAIXO, `pos_y` e o topo do AABB e a gravidade e positiva
-- (collision.resolve_y, player.lua:148). O Defold desenha com Y para cima, entao
-- toda posicao passa por `to_screen_y` antes de virar posicao de sprite.
-- `x` e o centro horizontal da entidade.

local bit = require("bit")
local collision = require("main.collision")
local objects = require("main.objects")
local player = require("main.player")
local original_animation = require("main.original_animation")
local boss = require("main.boss")
local level_loader = require("main.level_loader")
local original_camera = require("main.original_camera")
local original_bg2 = require("main.original_bg2")

-- BG2 strips: sky bands (BBA655 counts $18/$18/$38) then one strip per sea line.
local BG2_STRIPS = {
  { anim = "original_bg2_band_0", top = 0, height = 24 },
  { anim = "original_bg2_band_1", top = 24, height = 24 },
  { anim = "original_bg2_band_2", top = 48, height = 56 },
}
for line = 104, 223 do
  BG2_STRIPS[#BG2_STRIPS + 1] = { anim = string.format("original_bg2_line_%03d", line), top = line, height = 1 }
end
local bg2_clock = nil
local original_bananas = require("main.original_bananas")
local BANANA_FRAMES = {}
for frame = 0, 7 do BANANA_FRAMES[frame + 1] = "original_banana_" .. frame end
local original_hud = require("main.original_hud")
local HUD_DIGITS = {}
for digit = 0, 9 do HUD_DIGITS[digit + 1] = "original_hud_digit_" .. digit end

local M = {}

local FACTORY   = "#entity_factory"
local TILE      = 16
local SCREEN_W  = 256
local SCREEN_H  = 224
local BG_W      = 640            -- largura nativa das camadas de parallax
local BG_SCALE  = 2              -- 640x360 -> 1280x720

-- profundidades (o projetor ortografico padrao cobre -1 .. 1)
local Z_SKY     = -0.95
local Z_FAR     = -0.90
local Z_MID     = -0.85
local Z_TILE    = -0.40
local Z_OBJECT  = -0.20
local Z_BOSS    = -0.15
local Z_PLAYER  = -0.10
local Z_FRONT   = -0.05  -- BG3 priority-1 tiles (Mode 1 BG3 priority bit)
local Z_HUD     = -0.07  -- priority-3 HUD sprites: above all sprites, below BG3 priority 1

-- teto de seguranca: um nivel inteiro solido nao pode explodir o pool
local MAX_SPRITES = 1200

local TILE_ANIM = {
  [collision.TILE_SOLID]    = "tile_solid",
  [collision.TILE_PLATFORM] = "tile_platform",
  [collision.TILE_SPIKE]    = "tile_spike",
  [collision.TILE_SLIP]     = "tile_slip",
  [collision.TILE_WATER]    = "tile_water",
  [collision.TILE_CRACKED]  = "tile_cracked",
}

-- animacao + altura do PNG (para ancorar o sprite pelos pes)
local OBJ_ANIM = {
  [objects.OBJ_BANANA]       = { "obj_banana", 16 },
  [objects.OBJ_BANANA_BUNCH] = { "obj_banana_bunch", 24 },
  [objects.OBJ_DK_COIN]      = { "obj_dk_coin", 20 },
  [objects.OBJ_LIFE]         = { "obj_life", 24 },
  [objects.OBJ_KRITTER]      = { "en_kritter", 32 },
  [objects.OBJ_ZINGER]       = { "en_zinger", 32 },
  [objects.OBJ_KRUSHA]       = { "en_krusha", 32 },
  [objects.OBJ_BARREL]       = { "obj_barrel", 24 },
  [objects.OBJ_RAMBI]        = { "an_rambi", 32 },
  [objects.OBJ_ENGUARDE]     = { "an_enguarde", 32 },
  [objects.OBJ_FLITTER]      = { "en_flitter", 32 },
  [objects.OBJ_KLAMP]        = { "en_klamp", 32 },
  [objects.OBJ_KLOBBER]      = { "en_klobber", 32 },
  [objects.OBJ_KANNON]       = { "en_kannon", 32 },
  [objects.OBJ_MININECKY]    = { "en_mininecky", 32 },
  [objects.OBJ_PROJECTILE]   = { "en_projectile", 12 },
  [objects.OBJ_KABOOM]       = { "en_kaboom", 32 },
  [objects.OBJ_KUTLASS]      = { "en_kutlass", 32 },
  [objects.OBJ_KLUDGE]       = { "en_kludge", 32 },
  [objects.OBJ_SQUITTER]     = { "an_squitter", 32 },
  [objects.OBJ_RATTLY]       = { "an_rattly", 32 },
  [objects.OBJ_SQUAWKS]      = { "an_squawks", 32 },
  [objects.OBJ_EXPRESSO]     = { "an_expresso", 32 },
  [objects.OBJ_BONUS_BARREL] = { "obj_bonus_barrel", 24 },
  [objects.OBJ_ANIMAL_CRATE] = { "obj_animal_crate", 24 },
  [objects.OBJ_LETTER_K]     = { "obj_letter_k", 20 },
  [objects.OBJ_LETTER_O]     = { "obj_letter_o", 20 },
  [objects.OBJ_LETTER_N]     = { "obj_letter_n", 20 },
  [objects.OBJ_LETTER_G]     = { "obj_letter_g", 20 },
  [objects.OBJ_ROPE]         = { "obj_rope", 16 },
}

local PLAYER_ANIM = {
  [player.STATE.IDLE]       = "player_idle",
  [player.STATE.RUN]        = "player_run",
  [player.STATE.JUMP]       = "player_jump",
  [player.STATE.FALL]       = "player_fall",
  [player.STATE.ROLL]       = "player_roll",
  [player.STATE.CROUCH]     = "player_crouch",
  [player.STATE.SKID]       = "player_skid",
  [player.STATE.CLIMB]      = "player_climb",
  [player.STATE.SWIM]       = "player_swim",
  [player.STATE.BARREL]     = "player_barrel",
  [player.STATE.TEAM_THROW] = "player_idle",
  [player.STATE.DAMAGE]     = "player_damage",
  [player.STATE.DEATH]      = "player_death",
  [player.STATE.RAMBI_RIDING]    = "an_rambi",
  [player.STATE.ENGUARDE_RIDING] = "an_enguarde",
}

local MOUNT_ANIM = {
  squitter = "an_squitter",
  rattly   = "an_rattly",
  squawks  = "an_squawks",
  expresso = "an_expresso",
  rambi    = "an_rambi",
  enguarde = "an_enguarde",
}

local BOSS_ANIM = {
  [boss.BOSS_KROW]      = "boss_krow",
  [boss.BOSS_KLEAVER]   = "boss_kleaver",
  [boss.BOSS_KING_ZING] = "boss_zing",
  [boss.BOSS_KREEP]     = "boss_kreep",
  [boss.BOSS_KROOL_P1]  = "boss_krool",
  [boss.BOSS_KROOL_P2]  = "boss_krool",
}

local WHITE = vmath.vector4(1, 1, 1, 1)

-- altura visivel do nivel, recalculada a cada frame por `update`
local view_h = SCREEN_H

--- Converte um Y do mundo (crescendo para baixo) em Y de tela (para cima).
-- Niveis mais baixos que a janela ficam ancorados na base da tela.
local function to_screen_y(world_y, cam_y)
  -- These are game-space coordinates. Raw framebuffer frontend cropping is
  -- handled only by reference comparison, not guessed into game geometry.
  return view_h - (world_y - cam_y)
end

-- pool -----------------------------------------------------------------------
local pool = {}       -- { { id, url, anim, enabled, scale, tint } }
local cursor = 0      -- quantos slots foram consumidos no frame atual
M.visible = false

local function acquire()
  cursor = cursor + 1
  local slot = pool[cursor]
  if not slot then
    if cursor > MAX_SPRITES then
      cursor = cursor - 1
      -- Truncamento do pool: conta e, com perf opt-in, loga (1x/seg max).
      -- Nunca e garantia de FPS: so diagnostico de pressao no pool.
      M.pool_drops = M.pool_drops + 1
      if M.perf_enabled then
        local now = (socket and socket.gettime and socket.gettime()) or os.clock()
        if not M._last_drop_log or (now - M._last_drop_log) > 1.0 then
          M._last_drop_log = now
          print(string.format("[renderer] pool truncado: drops=%d cursor=%d max=%d",
            M.pool_drops, cursor, MAX_SPRITES))
        end
      end
      assert(cursor <= MAX_SPRITES, "renderer pool overflow contido")
      return nil
    end
    local id = factory.create(FACTORY, vmath.vector3(-9999, -9999, 0))
    slot = {
      id = id,
      url = msg.url(nil, id, "sprite"),
      anim = nil,
      enabled = true,
      scale = 1,
      tint = nil,
    }
    pool[cursor] = slot
  end
  if not slot.enabled then
    msg.post(slot.url, "enable")
    slot.enabled = true
  end
  return slot
end

--- Desenha um sprite ja em coordenadas de tela (x = centro, y = centro).
local NO_CLIP = vmath.vector4(-100000, 100000, 0, 0)
local function draw(anim, sx, sy, z, hflip, scale, tint, clip)
  local slot = acquire()
  if not slot then return end

  if slot.anim ~= anim then
    sprite.play_flipbook(slot.url, anim)
    slot.anim = anim
  end

  go.set_position(vmath.vector3(sx, sy, z), slot.id)

  scale = scale or 1
  if slot.scale ~= scale then
    go.set_scale(scale, slot.id)
    slot.scale = scale
  end

  sprite.set_hflip(slot.url, hflip or false)

  if tint then
    go.set(slot.url, "tint", tint)
    slot.tint = tint
  elseif slot.tint then
    go.set(slot.url, "tint", WHITE)
    slot.tint = nil
  end

  -- clip = vector4(min x, max x) on screen: pixels outside are not drawn (clip_sprite.fp)
  if clip then
    go.set(slot.url, "clip", clip)
    slot.clip = true
  elseif slot.clip then
    go.set(slot.url, "clip", NO_CLIP)
    slot.clip = nil
  end
end

local function release_rest()
  for i = cursor + 1, #pool do
    local slot = pool[i]
    if slot.enabled then
      msg.post(slot.url, "disable")
      slot.enabled = false
    end
  end
end

-- camadas --------------------------------------------------------------------
local function draw_parallax(camera)
  if level_loader.original_semantics() then
    -- BG2 per-scanline H from 80E540 (HDMA ch1); strips carry the ch2 COLDATA
    -- color math baked in (export_bg2_strips.py). V is fixed: strip y = screen y.
    local clock = original_camera.clock
    if clock and clock ~= bg2_clock then
      bg2_clock = clock
      original_bg2.update(math.floor(camera.pos_x) + 256, clock)
    end
    for _, band in ipairs(BG2_STRIPS) do
      local h = original_bg2.line_h(band.top)
      local y = SCREEN_H - (band.top + band.height * 0.5)
      draw(band.anim, 128 - h, y, Z_SKY)
      draw(band.anim, 384 - h, y, Z_SKY)
    end
    return
  end
  draw("bg_sky", SCREEN_W * 0.5, SCREEN_H * 0.5, Z_SKY, false, BG_SCALE)

  local layers = {
    { anim = "bg_far", name = "far", z = Z_FAR, tint = vmath.vector4(0.78, 0.82, 0.92, 1) },
    { anim = "bg_mid", name = "mid", z = Z_MID, tint = vmath.vector4(0.58, 0.66, 0.62, 1) },
  }
  for _, layer in ipairs(layers) do
    local off = camera.get_parallax_offset(layer.name) % SCREEN_W
    -- escurecido para o cenario nao competir com tiles e inimigos
    draw(layer.anim, SCREEN_W * 0.5 - off, SCREEN_H * 0.5, layer.z, false, BG_SCALE, layer.tint)
    draw(layer.anim, SCREEN_W * 1.5 - off, SCREEN_H * 0.5, layer.z, false, BG_SCALE, layer.tint)
  end
end

local RIGGING_W, RIGGING_H = 1280, 512
local function draw_original_rigging(camera)
  if not level_loader.original_semantics() or level_loader.get_subarea() then return end
  -- BG3 rigging map assembled from DATA_F526A7/F52087 (export_bg3_rigging.py).
  -- 80E4EB: H = L1X + L1X/4 (map wraps at 1280); rows follow L1Y - 256 (B5AAE6).
  -- Mode 1 + BG3 priority: every visible rigging tile has priority 1 -> above sprites.
  local l1x = math.floor(camera.pos_x) + 256
  local map_x = (l1x + math.floor(l1x / 4)) % RIGGING_W
  local map_y = math.floor(camera.pos_y) % RIGGING_H
  for copy_y = 0, 1 do
    local top = copy_y * RIGGING_H - map_y
    if top < SCREEN_H and top + RIGGING_H > 0 then
      for copy_x = 0, 1 do
        local left = copy_x * RIGGING_W - map_x
        if left < SCREEN_W and left + RIGGING_W > 0 then
          draw("original_bg3_rigging", left + RIGGING_W * 0.5,
               SCREEN_H - (top + RIGGING_H * 0.5), Z_FRONT)
        end
      end
    end
  end
end

-- Cache da faixa visivel de tiles: recomputa col0/col1/row0/row1 so quando
-- a camera cruza fronteira de tile (evita floor/div por frame sem mudar a
-- semantica do renderer). Posicoes com snap inteiro p/ pixel-art.
local tile_band = { col0 = -1, col1 = -1, row0 = -1, row1 = -1,
                    cam_tx = nil, cam_ty = nil, w = nil, h = nil }

--- Contadores de performance do pool (opt-in via M.perf_enabled).
-- pool_drops: truncacoes por teto MAX_SPRITES; sprite_count: consumo do frame.
M.perf_enabled = false
M.pool_drops = 0
M.frames = 0

function M.invalidate_tile_cache()
  tile_band.col0, tile_band.col1 = -1, -1
  tile_band.row0, tile_band.row1 = -1, -1
  tile_band.cam_tx, tile_band.cam_ty = nil, nil
  tile_band.w, tile_band.h = nil, nil
end

local function draw_level_chunks(camera)
  local chunks = level_loader.get_chunks()
  if not chunks or #chunks == 0 then return false end
  local cam_x, cam_y = camera.pos_x, camera.pos_y
  for i = 1, #chunks do
    local ch = chunks[i]
    local sx = ch.x - cam_x
    -- so desenha o chunk quando ele toca a janela visivel
    if sx + ch.w > -8 and sx < SCREEN_W + 8 then
      local half_w = ch.w * 0.5
      local mid_y = ch.h * 0.5
      draw(ch.anim,
           math.floor(sx + half_w + 0.5),
           math.floor(to_screen_y(mid_y, cam_y) + 0.5),
           Z_TILE)
    end
  end
  return true
end

local function draw_tiles(camera)
  if draw_level_chunks(camera) then return end
  local w, h = level_loader.get_dimensions()
  local cam_x, cam_y = camera.pos_x, camera.pos_y

  -- so recomputa a faixa quando a camera muda de tile ou o nivel troca
  local tx, ty = math.floor(cam_x / TILE), math.floor(cam_y / TILE)
  if tx ~= tile_band.cam_tx or ty ~= tile_band.cam_ty
      or w ~= tile_band.w or h ~= tile_band.h then
    tile_band.cam_tx, tile_band.cam_ty = tx, ty
    tile_band.w, tile_band.h = w, h
    tile_band.col0 = math.max(0, math.floor(cam_x / TILE))
    tile_band.col1 = math.min(w - 1, math.floor((cam_x + SCREEN_W) / TILE))
    tile_band.row0 = math.max(0, math.floor(cam_y / TILE))
    tile_band.row1 = math.min(h - 1, math.floor((cam_y + SCREEN_H) / TILE))
  end
  local col0, col1, row0, row1 =
    tile_band.col0, tile_band.col1, tile_band.row0, tile_band.row1

  local half = TILE * 0.5
  for row = row0, row1 do
    for col = col0, col1 do
      local anim = TILE_ANIM[collision.get_tile(col, row)]
      if anim then
        -- snap inteiro: pixel-art sem sub-pixel shimmer
        draw(anim,
             math.floor(col * TILE + half - cam_x + 0.5),
             math.floor(to_screen_y(row * TILE + half, cam_y) + 0.5),
             Z_TILE)
      end
    end
  end
end

local function draw_objects(camera)
  local cam_x, cam_y = camera.pos_x, camera.pos_y
  for _, obj in ipairs(objects.get_objects()) do
    local active = bit.band(obj.flags, objects.FLAG_ACTIVE) ~= 0
    local taken  = bit.band(obj.flags, objects.FLAG_COLLECTED) ~= 0
    local entry  = OBJ_ANIM[obj.type]
    local original_render = obj.params and obj.params.original_render
    if level_loader.original_semantics() and original_render then
      entry = { original_render.animation, original_render.height }
    end
    if active and not taken and entry then
      -- o sprite apoia no chao: base do AABB menos meia altura da imagem
      local sx = obj.x - cam_x
      local sy = to_screen_y(obj.y + obj.height - entry[2] * 0.5, cam_y)
      if sx > -64 and sx < SCREEN_W + 64 and sy > -64 and sy < SCREEN_H + 64 then
        draw(entry[1], sx, sy, Z_OBJECT, obj.direction and obj.direction < 0)
      end
    end
  end
end

local original_items = require("main.original_items")
local function draw_original_items(camera)
  local cam_x, cam_y = camera.pos_x, camera.pos_y
  original_items.each_visible(function(sprite, left, top, width, height)
    local sx = left - cam_x + width * 0.5
    if sx > -width and sx < SCREEN_W + width then
      draw(sprite, sx, to_screen_y(top + height * 0.5, cam_y), Z_OBJECT)
    end
  end)
end

local original_walkers = require("main.original_walkers")
local function draw_original_walkers(camera)
  local cam_x, cam_y = camera.pos_x, camera.pos_y
  original_walkers.each_visible(function(sprite, left, top, width, height, flipped)
    local sx = left - cam_x + width * 0.5
    if sx > -width and sx < SCREEN_W + width then
      draw(sprite, sx, to_screen_y(top + height * 0.5, cam_y), Z_OBJECT, flipped)
    end
  end)
end

local original_klobber = require("main.original_klobber")
local function draw_original_klobber(camera)
  local cam_x, cam_y = camera.pos_x, camera.pos_y
  original_klobber.each_visible(function(sprite, left, top, width, height, flipped)
    local sx = left - cam_x + width * 0.5
    if sx > -width and sx < SCREEN_W + width then
      draw(sprite, sx, to_screen_y(top + height * 0.5, cam_y), Z_OBJECT, flipped)
    end
  end)
end

local original_rambi = require("main.original_rambi")
local function draw_original_rambi(camera)
  local cam_x, cam_y = camera.pos_x, camera.pos_y
  original_rambi.each_visible(function(sprite, left, top, width, height, flipped)
    local sx = left - cam_x + width * 0.5
    if sx > -width and sx < SCREEN_W + width then
      draw(sprite, sx, to_screen_y(top + height * 0.5, cam_y), Z_OBJECT + 0.01, flipped)
    end
  end)
end

local original_partner = require("main.original_partner")
local original_carry = require("main.original_carry")
local function draw_original_carry(camera)
  local cam_x, cam_y = camera.pos_x, camera.pos_y
  original_carry.each_visible(function(sprite, left, top, width, height)
    -- behind the Kong: the front hand covers the held object (carry-t1-frame-1132.ppm)
    draw(sprite, left - cam_x + width * 0.5, to_screen_y(top + height * 0.5, cam_y), Z_PLAYER - 0.01)
  end)
end

local original_effects = require("main.original_effects")
local function draw_original_effects(camera)
  local cam_x, cam_y = camera.pos_x, camera.pos_y
  original_effects.each_visible(function(sprite, left, top, width, height)
    draw(sprite, left - cam_x + width * 0.5, to_screen_y(top + height * 0.5, cam_y), Z_OBJECT + 0.02)
  end)
end

local original_areas = require("main.original_areas")
local function draw_original_areas(camera)
  local cam_x, cam_y = camera.pos_x, camera.pos_y
  original_areas.each_cannon(function(sprite, left, top, width, height)
    local sx = left - cam_x + width * 0.5
    if sx > -width and sx < SCREEN_W + width then
      draw(sprite, sx, to_screen_y(top + height * 0.5, cam_y), Z_OBJECT)
    end
  end)
  -- Bonus countdown (APPROXIMATION: HUD digits centred at the top, not the original layout).
  local seconds = original_areas.seconds_left()
  if seconds then
    local text = tostring(seconds)
    for i = 1, #text do
      local digit = tonumber(text:sub(i, i))
      draw(HUD_DIGITS[digit + 1], SCREEN_W * 0.5 + (i - 1 - #text * 0.5) * 9 + 4, view_h - 16, Z_HUD)
    end
  end
end

local banana_tick = 0
local function draw_original_bananas(camera)
  -- subareas have no original camera profile: their bananas spin on a frame count
  banana_tick = banana_tick + 1
  local clock = camera.original_active and original_camera.clock or banana_tick
  local cam_x, cam_y = camera.pos_x, camera.pos_y
  original_bananas.each_visible(clock, function(frame, x, y)
    local sx = x - cam_x + 8  -- draw() anchors at the 16x16 sprite centre
    if sx > -16 and sx < SCREEN_W + 16 then
      local sy = to_screen_y(y + 8, cam_y)
      if sy > -16 and sy < SCREEN_H + 16 then
        draw(BANANA_FRAMES[frame + 1], sx, sy, Z_OBJECT)
      end
    end
  end)
end

-- Original HUD sprites (BEC89C/BEC814/BEC7BB) at their OAM coordinates; measured
-- against the captured screens: displayed row = OAM Y (the level-banana path folds
-- its DEC back in with SEP #$21 carry). Mode 1 + BG3 priority keeps rigging above.
local function draw_hud_sprite(anim, oam_x, oam_y, width, height)
  draw(anim, oam_x + width * 0.5, SCREEN_H - (oam_y + height * 0.5), Z_HUD)
end

local original_kong_hud = require("main.original_kong_hud")
local original_coin_hud = require("main.original_coin_hud")
local function draw_original_hud()
  -- every original area draws the HUD (the Kabin and the bonus rooms show the lives panel
  -- on entry too: BB9210 arms both timers on area entry), not only the banana main area
  if not level_loader.original_semantics() then return end
  original_kong_hud.each_visible(draw_hud_sprite)
  original_coin_hud.each_visible(draw_hud_sprite, HUD_DIGITS)
  if require("main.original_areas").note_shown then  -- K. Rool's message (export_kabin_note)
    draw_hud_sprite("original_kabin_note_text", 9, 40, 230, 48)
  end
  local balloon = original_hud.balloon
  if balloon then  -- extra life balloon flying to the lives panel
    local frame = balloon.frames[math.floor(balloon.age / 4) % #balloon.frames + 1]
    draw_hud_sprite(frame.sprite, math.floor(balloon.x / 256) - frame.origin_x, math.floor(balloon.y / 256) - frame.origin_y,
                    frame.width, frame.height)
  end
  -- B5F9D1 flying bananas: tile ($2A & $0E) + $0D2C, large sprite at the 8.8 position.
  for _, banana in ipairs(original_hud.flying or {}) do
    local spin = math.floor(((original_hud.clock or 0) % 16) / 2)
    draw_hud_sprite(BANANA_FRAMES[spin + 1], math.floor(banana.x / 256), math.floor(banana.y / 256), 16, 16)
  end
  if original_hud.banana_visible then
    local clock = original_hud.clock or 0
    draw_hud_sprite(BANANA_FRAMES[math.floor(clock / 4) % 8 + 1], 8, 8, 16, 16)
    local x = 0x18
    for _, digit in ipairs(original_hud.banana_digits()) do
      draw_hud_sprite(HUD_DIGITS[digit + 1], x, 8, 8, 16)
      x = x + 8
    end
  end
  if original_hud.lives_visible then
    local lives = math.max(0, math.min(original_hud.lives, 99))
    local y = original_hud.lives_y()
    -- B59CAE head pose GFX_Diddy_LifeIcon: origin (212, digit Y + 16), pieces from (-7, -14).
    draw_hud_sprite("original_hud_diddy_head", 212 - 7, y + 16 - 14, 14, 16)
    if lives >= 10 then
      draw_hud_sprite(HUD_DIGITS[math.floor(lives / 10) + 1], 0xDF, y, 8, 16)
      draw_hud_sprite(HUD_DIGITS[lives % 10 + 1], 0xE7, y, 8, 16)
    else
      draw_hud_sprite(HUD_DIGITS[lives + 1], 0xE4, y, 8, 16)
    end
  end
end

local function draw_boss(camera, current_boss)
  if not current_boss then return end
  local info = boss.get_render_info(current_boss)
  if not info then return end

  local cam_x, cam_y = camera.pos_x, camera.pos_y
  if info.visible then
    -- boss.x / boss.y sao o centro do hitbox (boss.get_hitbox)
    local anim = BOSS_ANIM[info.type] or "boss_krow"
    local tint = info.flash and vmath.vector4(1, 0.4, 0.4, 1) or nil
    draw(anim, info.x - cam_x, to_screen_y(info.y, cam_y), Z_BOSS, false, 1, tint)
  end
  for _, p in ipairs(info.projectiles) do
    draw("en_projectile", p.x - cam_x, to_screen_y(p.y, cam_y), Z_OBJECT)
  end
end

-- Partner Kong (main/original_partner.lua): same origin rules as the player sprite.
local function draw_partner(camera)
  local info = level_loader.original_semantics() and level_loader.get_player_render_info()
  if not info then return end
  original_partner.each_visible(function(animation, x, feet, direction)
    local sx = math.floor(x) - math.floor(camera.pos_x) + info.center_offset_x * direction
    local sy = to_screen_y(math.floor(feet) + info.center_offset_y, math.floor(camera.pos_y))
    draw(animation, sx, sy, Z_PLAYER - 0.005, direction < 0)
  end)
end

local function draw_player(camera)
  if original_rambi.mounted() then return end  -- Diddy is drawn riding (draw_original_rambi)
  local anim = PLAYER_ANIM[player.state]
  local image_height = 32
  local offset_x, offset_y = 0, -16
  if level_loader.original_semantics() then
    -- Original PNGs use a 64px canvas. Never select prototype player art here.
    image_height = 64
    local info = level_loader.get_player_render_info()
    if info then
      image_height = info.height
      offset_x, offset_y = info.center_offset_x, info.center_offset_y
    else
      offset_y = -image_height * 0.5
    end
    if player.state == player.STATE.RUN or player.state == player.STATE.SKID then
      anim = "diddy_run"
    elseif player.state == player.STATE.JUMP or player.state == player.STATE.FALL then
      anim = "diddy_jump"
    else
      anim = "diddy_idle"
    end
  end
  if player.state == player.STATE.MOUNTED then
    anim = MOUNT_ANIM[player.mount_type] or "player_idle"
  end
  anim = original_animation.get_animation() or anim or "player_idle"
  if original_partner.busy() then return end  -- the hand-over draws both Kongs
  if player.hidden then return end  -- inside a barrel cannon

  -- pisca durante a invencibilidade pos-dano
  if player.invincible_timer > 0 and math.floor(player.invincible_timer * 12) % 2 == 0 then
    return
  end

  -- ancora pelos pes: base do hitbox menos meia altura do sprite (32px)
  local _hx, hy, _hw, hh = player.get_hitbox()
  -- a turning Kong still faces the old way (original_animation.turn_dir)
  local direction = require("main.original_animation").turn_dir or player.direction
  local sx = player.pos_x - camera.pos_x + offset_x * direction
  local sy = to_screen_y(hy + hh + offset_y, camera.pos_y)
  if level_loader.original_semantics() then
    -- SNES OAM stores integer screen positions; retain fractional simulation,
    -- but rasterize the original sprite origin rather than subpixel sliding.
    sx = math.floor(player.pos_x) - math.floor(camera.pos_x) + offset_x * direction
    sy = to_screen_y(math.floor(hy + hh) + offset_y, math.floor(camera.pos_y))
  end
  local second = require("main.original_animation").get_animation2()
  if second then draw(second, sx, sy, Z_PLAYER + 0.002, direction < 0) end  -- the boombox
  local clip = player.door_clip  -- walking through a door: the frame hides the Kong
  draw(anim, sx, sy, Z_PLAYER, direction < 0, nil, nil,
       clip and vmath.vector4(clip[1] - math.floor(camera.pos_x), clip[2] - math.floor(camera.pos_x), 0, 0))
end

-- API ------------------------------------------------------------------------

--- Liga a renderizacao do mundo e esconde os sprites de menu.
function M.show()
  M.visible = true
  msg.post("#background", "disable")
  msg.post("#logo", "disable")
end

--- Desliga a renderizacao do mundo e devolve o fundo dos menus.
function M.hide()
  if M.visible then
    M.visible = false
    cursor = 0
    release_rest()
  end
  -- The legacy menu backdrop/logo stay off: the opening (main/opening.lua) draws the
  -- original title screen instead.
  msg.post("#background", "disable")
  msg.post("#logo", "disable")
end

--- Full-screen picture outside gameplay (opening/title), or nothing.
--- Stacked screen pictures { {sprite, x, y, w, h}, ... } (top-left boxes on 256x224),
--- dimmed by `brightness` (0..1: the original's fades).
function M.draw_layers(layers, brightness)
  cursor = 0
  local level = brightness or 1
  local tint = level < 1 and vmath.vector4(level, level, level, 1) or nil
  for index, layer in ipairs(layers) do
    draw(layer[1], layer[2] + layer[4] * 0.5, SCREEN_H - (layer[3] + layer[5] * 0.5), Z_SKY + index * 0.001,
         false, layer[6] or 1, tint)
  end
  release_rest()
end

--- A full screen, or a picture whose top-left box on the 256x224 screen is x, y, w, h.
function M.draw_screen(sprite, x, y, w, h, scale)
  cursor = 0
  if sprite and x then
    draw(sprite, x + w * 0.5, SCREEN_H - (y + h * 0.5), Z_SKY, false, scale)
  elseif sprite then
    draw(sprite, SCREEN_W * 0.5, SCREEN_H * 0.5, Z_SKY)
  end
  release_rest()
end

function M.update(camera, current_boss)
  if not M.visible then return end

  local _w, h = level_loader.get_dimensions()
  view_h = math.min(SCREEN_H, (h or 0) * TILE)

  cursor = 0
  draw_parallax(camera)
  draw_tiles(camera)
  draw_objects(camera)
  draw_original_items(camera)
  draw_original_walkers(camera)
  draw_original_klobber(camera)
  draw_original_areas(camera)
  draw_original_rambi(camera)
  draw_original_effects(camera)
  draw_original_carry(camera)
  draw_original_bananas(camera)
  draw_original_hud()
  draw_boss(camera, current_boss)
  draw_partner(camera)
  draw_player(camera)
  draw_original_rigging(camera)
  release_rest()

  M.frames = M.frames + 1
  -- Instrumentacao opt-in: CPU de Lua por frame (frames/dt), nunca "FPS GPU".
  -- Ativa via game.project [dkc2] perf_log=1; loga p50/p95 a cada 300 frames.
  if M.perf_enabled then
    local ok, perf = pcall(require, "main.perf")
    if ok and perf then perf.record(cursor, M.pool_drops) end
  end
end

--- Numero de sprites desenhados no ultimo frame (diagnostico).
function M.sprite_count()
  return cursor
end

--- Liga/desliga a instrumentacao via config [dkc2] perf_log.
function M.set_perf_enabled(v)
  M.perf_enabled = v and true or false
end

--- Estatisticas de pool: { draws, drops, frames }.
function M.pool_stats()
  return { draws = cursor, drops = M.pool_drops, frames = M.frames }
end

return M
