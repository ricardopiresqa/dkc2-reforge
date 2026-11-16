local collision = require("main.collision")
local sound = require("main.sound")

local M = {}

M.current_level = nil

local level_modules = {
  level_1_1 = require("data.levels.level_1_1"),
  -- Pirate Panic subareas (tools/replay-compare/export_subareas.py)
  pirate_bonus_1 = require("data.levels.pirate_bonus_1"),
  pirate_bonus_2 = require("data.levels.pirate_bonus_2"),
  pirate_warp = require("data.levels.pirate_warp"),
  pirate_kabin = require("data.levels.pirate_kabin"),
  level_1_2 = require("data.levels.level_1_2"),
  level_forest = require("data.levels.level_forest"),
  test_water = require("data.levels.test_water"),
  level_2_1 = require("data.levels.level_2_1"),
  level_2_2 = require("data.levels.level_2_2"),
  level_3_1 = require("data.levels.level_3_1"),
  level_1_3 = require("data.levels.level_1_3"),
  level_1_4 = require("data.levels.level_1_4"),
  level_1_5 = require("data.levels.level_1_5"),
  boss_krow = require("data.levels.boss_krow"),
  -- World 2
  level_2_3 = require("data.levels.level_2_3"),
  level_2_4 = require("data.levels.level_2_4"),
  level_2_5 = require("data.levels.level_2_5"),
  -- World 3
  level_3_2 = require("data.levels.level_3_2"),
  level_3_3 = require("data.levels.level_3_3"),
  level_3_4 = require("data.levels.level_3_4"),
  level_3_5 = require("data.levels.level_3_5"),
  -- World 4
  level_4_1 = require("data.levels.level_4_1"),
  level_4_2 = require("data.levels.level_4_2"),
  level_4_3 = require("data.levels.level_4_3"),
  level_4_4 = require("data.levels.level_4_4"),
  level_4_5 = require("data.levels.level_4_5"),
  -- World 5
  level_5_1 = require("data.levels.level_5_1"),
  level_5_2 = require("data.levels.level_5_2"),
  level_5_3 = require("data.levels.level_5_3"),
  level_5_4 = require("data.levels.level_5_4"),
  level_5_5 = require("data.levels.level_5_5"),
  -- World 6 (Lost World)
  level_6_1 = require("data.levels.level_6_1"),
  level_6_2 = require("data.levels.level_6_2"),
  level_6_3 = require("data.levels.level_6_3"),
  level_6_4 = require("data.levels.level_6_4"),
  level_6_5 = require("data.levels.level_6_5"),
  -- Bosses
  boss_kleaver = require("data.levels.boss_kleaver"),
  boss_zing    = require("data.levels.boss_zing"),
  boss_kreep   = require("data.levels.boss_kreep"),
  boss_krool1  = require("data.levels.boss_krool1"),
  boss_krool2  = require("data.levels.boss_krool2"),
}

function M.load(level_module)
  local level_data = level_modules[level_module]
  if not level_data then
    level_data = require(level_module)
  end
  M.current_level = level_data

  collision.load(level_data.tiles, level_data.width, level_data.height)
  collision.load_original_surfaces(level_data.flat_surfaces)
  sound.play_music()

  return level_data
end

function M.get_player_spawn()
  if not M.current_level then return 64, 128 end
  return M.current_level.player_spawn.x, M.current_level.player_spawn.y
end

function M.get_camera_bounds()
  if not M.current_level then return 2560, 1440 end
  return M.current_level.camera.bound_x, M.current_level.camera.bound_y
end

function M.get_parallax_speeds()
  if not M.current_level then return { bg = 0.25, far = 0.5, mid = 0.75 } end
  return M.current_level.parallax
end

function M.get_objects()
  if not M.current_level then return {} end
  return M.current_level.objects or {}
end

function M.get_id()
  if not M.current_level then return "unknown" end
  return M.current_level.id
end

function M.get_name()
  if not M.current_level then return "Unknown" end
  return M.current_level.name
end

function M.get_dimensions()
  if not M.current_level then return 96, 24 end
  return M.current_level.width, M.current_level.height
end

function M.is_boss_level()
  if not M.current_level then return false end
  return M.current_level.is_boss or false
end

--- Semantica do nivel: `original_semantics=true` quando o layout vier de
-- fonte declarada (disasm local); `false` = prototipo (mecanicas genericas
-- preservadas: double jump, HP 3, breath drenando). Quando o parser de dados
-- originais entregar o layout real e a Tifa substituir o wrapper, este flag
-- vira true e os gates em player.lua mudam o comportamento.
function M.original_semantics()
  if not M.current_level then return false end
  return M.current_level.original_semantics == true
end

function M.get_player_render_info()
  return M.current_level and M.current_level.player_render_info
end

--- Original level objects of a subarea (nil in the main area: modules use their default).
function M.get_original_objects()
  return M.current_level and M.current_level.original_objects
end

function M.get_subarea()
  return M.current_level and M.current_level.subarea
end

function M.get_original_camera()
  return M.current_level and M.current_level.original_camera
end

function M.is_prototype()
  if not M.current_level then return false end
  return M.current_level.prototype == true
      or M.current_level.original_semantics ~= true
end

--- Objetivo do nivel (x do fim), quando a fonte original declara um.
function M.get_goal()
  if not M.current_level then return nil end
  return M.current_level.goal
end

--- Chunks estaticos de fundo do nivel (imagens largas, sem sprite por tile).
function M.get_chunks()
  if not M.current_level then return nil end
  return M.current_level.chunks
end

function M.unload()
  M.current_level = nil
  collision.clear()
end

return M
