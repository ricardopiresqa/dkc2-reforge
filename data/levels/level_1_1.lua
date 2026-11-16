-- 1-1 Pirate Panic (DKC2) — WRAPPER sobre o layout ORIGINAL decodificado.
--
-- Fonte declarada (read-only): tools/vendor/DKC2-disasm/DKC2 —
-- LevelData/ShipDeckLevels.bin + Tilemaps/Map32 + Graphics/Compressed +
-- LevelData/SpriteData/PiratePanic_Main.bin + Palettes/FGBG_Level_PiratePanic.
-- O parser e tools/import_pirate_panic.py; o contrato gerado esta em
-- data/original/pirate/pirate_panic_level.lua (generated, local ROM source).
--
-- `original_semantics = true` selects the non-prototype input/HUD gates.
-- It is NOT a fidelity certificate: room slice is RAM-verified; collision,
-- region interpolation, entity behavior and composition remain partial.
-- Invencoes do prototipo (double jump, HP numerico, breath) ficam DESLIGADAS
-- por causa deste flag (main/player.lua / main/level_loader.lua).
--
-- LACUNAS DECLARADAS (nao e "completo"):
--   * Native AI/Dixie/bonus remain unimplemented.
--   * Neek/Klomp preserve original pixels but are static-only; other source IDs
--     are retained without unrelated prototype gameplay.
--   * Source collision covers interpreted floor profiles; ceilings, dynamic
--     and some inverted-flag cases remain incomplete.
--   * The header goal marker is not the original LevelEndGoal interaction.
--     Original mode does not complete merely by crossing X.

local data = require("data.original.pirate.pirate_panic_level")
local render_info = require("data.original.pirate.render_info")

local TILE = data.tile_px or 16

-- ---------------------------------------------------------------------------
-- grade de colisao: RLE -> tiles[row][col] (1-based; row 1 = topo)
-- ---------------------------------------------------------------------------
local function decode_rle(s, n)
  local out = {}
  local idx, i = 1, 1
  local len = #s
  while idx <= n and i <= len do
    local colon = s:find(":", i, true)
    if not colon then break end
    local comma = s:find(",", colon + 1, true)
    local last = comma and (comma - 1) or len
    local v = tonumber(s:sub(i, colon - 1)) or 0
    local cnt = tonumber(s:sub(colon + 1, last)) or 0
    for _ = 1, cnt do
      out[idx] = v
      idx = idx + 1
    end
    i = (comma and (comma + 1)) or (len + 1)
  end
  while idx <= n do
    out[idx] = 0
    idx = idx + 1
  end
  return out
end

local COLS = data.grid_cols
local ROWS = data.grid_rows
local flat = decode_rle(data.grid_rle or "", COLS * ROWS)

local tiles = {}
for r = 0, ROWS - 1 do
  local row = {}
  for c = 0, COLS - 1 do
    row[c + 1] = flat[r * COLS + c + 1] or 0
  end
  tiles[r + 1] = row
end

-- ---------------------------------------------------------------------------
-- Entidades originales permanecem IDs originales; runtime não as faz passar
-- por um inimigo/barrel/colecionável de outro tipo.
-- ---------------------------------------------------------------------------
local SPRITE_TO_TYPE = {
  Neek              = "original_static",
  Klomp             = "original_static",
  Klobber           = "original_static",
  DKBarrel          = "original_static",
  WoodenBox         = "original_static",
  KongLetters       = "original_static",
  AnimalBuddyBox    = "original_static",
  -- Unsupported original scripts are preserved in data, NOT replaced with
  -- bonus barrels, ropes, collectible bananas, bosses or unrelated enemies.
}

local OBJECT_H = 24

local objects = {}
for _, o in ipairs(data.objects or {}) do
  local t = SPRITE_TO_TYPE[o.sprite or ""]
  if t then
    objects[#objects + 1] = {
      type = t,
      -- Static render anchor only; entity hitbox/behavior remains unimplemented.
      x = o.x,
      y = (o.feet_y or 0) - OBJECT_H,
      params = { script = o.script, sprite = o.sprite, param = o.param,
                 original_render = render_info[o.sprite] },
    }
  end
end

local SPAWN_H = 24   -- PLAYER_H em main/player.lua

return {
  id = "1-1",
  name = "Pirate Panic",
  original_semantics = true,
  fidelity_status = "partial",
  prototype = false,
  source = "USA v1.0 disassembly; hash/provenance manifest is development-only and excluded from game bundles",
  gaps = {
    "Handlers/IA original pendentes; Neek/Klomp são sprites OAM reais em modo imóvel, não AI faithful",
    "Klobber/DKBarrel/WoodenBox/KONG letters/AnimalBuddyBox retained original IDs, no unrelated placeholder mechanics",
    "timings e ancoras das animacoes nao comparados ao SNES",
    "recorte da sala verificado contra RAM; regras dinâmicas de câmera nao completas",
    "BG2 source pixels available; framebuffer diverges; BG3 draw withheld pending faithful stream",
    "HUD original pendente; contadores ingleses provisórios ocultos neste modo",
    "BarrelCannon/BreakableWall/NoAnimalBuddySign/unresolved scripts nao representados por mecanicas inventadas; handlers pendentes",
    "unsupported slope/ceiling collision handlers remain conservative/partial",
    "header goal marker is not the original LevelEndGoal state machine",
  },
  width = COLS,
  height = ROWS,
  tile_size = TILE,
  player_render_info = render_info.player,
  flat_surfaces = {
    cols = data.surface_cols, rows = data.surface_rows,
    heights = decode_rle(data.surface_rle, data.surface_cols * data.surface_rows),
  },
  player_spawn = {
    x = data.spawn.x,
    y = (data.spawn.feet_y or 0) - SPAWN_H,
  },
  goal = {
    x = (data.goal and data.goal.x) or 0,
    y = (data.goal and data.goal.feet_y) or 0,
    status = "header-marker-only; original LevelEndGoal collision/state machine is not ported",
  },
  camera = {
    bound_x = data.limits.x_max,
    bound_y = data.limits.y_max,
  },
  original_camera = {
    max_x = data.original_camera_max.x - 256,
    max_y = data.original_camera_max.y - 256,
    anchor_x = 128, anchor_y = 164,
    status = "capture-derived; wave/scroll rules not fully ported",
  },
  parallax = data.parallax or { bg = 0.25, far = 0.5, mid = 0.75 },
  chunks = data.chunks or {},
  tiles = tiles,
  objects = objects,
}
