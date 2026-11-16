--- Instrumentacao opt-in de CPU Lua por frame (frames/dt).
--
-- NAO e garantia de FPS nem medida de GPU: registra dt entregue pelo engine
-- (main.script -> game.update), sprite_count do renderer e pool_drops.
-- Ativo via [dkc2] perf_log=1 em game.project. Loga p50/p95 a cada 300 frames.
-- Sem dependencias: ring buffer puro Lua.

local M = {}

local N = 300
local dts = {}
local sprites = {}
local cpus = {}
local drops0 = nil
local count = 0

local function sorted_copy(t, n)
  local c = {}
  for i = 1, n do
    if t[i] ~= nil then c[#c + 1] = t[i] end
  end
  table.sort(c)
  return c
end

local function percentile(sorted, n, p)
  if n == 0 then return 0 end
  local k = math.max(1, math.min(n, math.ceil(p * n)))
  return sorted[k]
end

function M.reset()
  dts, sprites, cpus, count, drops0 = {}, {}, {}, 0, nil
end

--- dt em segundos, draws = cursor do renderer, drops = pool_drops acumulado.
function M.record_dt(dt, draws, drops)
  if drops0 == nil then drops0 = drops or 0 end
  count = count + 1
  local i = ((count - 1) % N) + 1
  dts[i] = dt
  sprites[i] = draws or 0
  cpus[i] = M._last_cpu
  local n = math.min(count, N)
  if count % N == 0 then
    local sd = sorted_copy(dts, n)
    local ss = sorted_copy(sprites, n)
    local sc = sorted_copy(cpus, n)
    local p50 = percentile(sd, n, 0.50) * 1000
    local p95 = percentile(sd, n, 0.95) * 1000
    local s50 = percentile(ss, n, 0.50)
    local s95 = percentile(ss, n, 0.95)
    print(string.format(
      "[perf] frames=%d dt_ms p50=%.2f p95=%.2f lua_cpu_ms p50=%.3f p95=%.3f sprites p50=%d p95=%d pool_drops=%d gpu=unavailable",
      count, p50, p95, percentile(sc, #sc, 0.50) * 1000,
      percentile(sc, #sc, 0.95) * 1000, s50, s95, (drops or 0) - drops0))
  end
end

--- Variante chamada pelo renderer (sem dt): usa ultimo dt visto ou ignora.
function M.record(draws, drops)
  if M._last_dt then
    M.record_dt(M._last_dt, draws, drops)
  end
end

function M.note_dt(dt)
  M._last_dt = dt
end

function M.note_cpu(seconds)
  M._last_cpu = seconds
end

return M
