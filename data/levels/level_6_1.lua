local W, H = 80, 24
local tiles = {}
for row = 0, H - 1 do
  tiles[row + 1] = {}
  for col = 0, W - 1 do
    if row == H - 1 then
      tiles[row + 1][col + 1] = 1
    elseif col == 0 or col == W - 1 then
      tiles[row + 1][col + 1] = 1
    elseif row >= 22 and col >= 10 and col <= 18 then
      tiles[row + 1][col + 1] = 1
    elseif row >= 20 and row <= 21 and col >= 24 and col <= 32 then
      tiles[row + 1][col + 1] = 1
    elseif row >= 22 and col >= 38 and col <= 46 then
      tiles[row + 1][col + 1] = 1
    elseif row >= 20 and row <= 21 and col >= 52 and col <= 60 then
      tiles[row + 1][col + 1] = 1
    elseif row >= 22 and col >= 66 and col <= 74 then
      tiles[row + 1][col + 1] = 1
    elseif row >= 17 and row <= 18 and col >= 14 and col <= 18 then
      tiles[row + 1][col + 1] = 2
    elseif row >= 13 and row <= 14 and col >= 28 and col <= 32 then
      tiles[row + 1][col + 1] = 2
    elseif row >= 8 and row <= 9 and col >= 42 and col <= 46 then
      tiles[row + 1][col + 1] = 2
    elseif row >= 4 and row <= 5 and col >= 56 and col <= 60 then
      tiles[row + 1][col + 1] = 2
    elseif row >= 18 and row <= 19 and col >= 46 and col <= 50 then
      tiles[row + 1][col + 1] = 2
    elseif row >= 10 and row <= 11 and col >= 4 and col <= 8 then
      tiles[row + 1][col + 1] = 2
    elseif row >= 2 and row <= 3 and col >= 64 and col <= 74 then
      tiles[row + 1][col + 1] = 2
    elseif row == 22 and col >= 20 and col <= 22 then
      tiles[row + 1][col + 1] = 0
    elseif row == 22 and col >= 34 and col <= 36 then
      tiles[row + 1][col + 1] = 0
    elseif row == 22 and col >= 48 and col <= 50 then
      tiles[row + 1][col + 1] = 0
    elseif row == 22 and col >= 62 and col <= 64 then
      tiles[row + 1][col + 1] = 0
    elseif row >= 12 and row <= 16 and col >= 20 and col <= 22 then
      tiles[row + 1][col + 1] = 5
    elseif row >= 6 and row <= 10 and col >= 36 and col <= 38 then
      tiles[row + 1][col + 1] = 5
    elseif row >= 1 and row <= 3 and col >= 50 and col <= 52 then
      tiles[row + 1][col + 1] = 5
    else
      tiles[row + 1][col + 1] = 0
    end
  end
end

return {
  id = '6-1',
  name = "Kremling Krusade",
  width = W, height = H, tile_size = 16,
  player_spawn = { x = 80, y = 128 },
  camera = { bound_x = 1280, bound_y = 384 },
  parallax = { bg = 0.05, far = 0.2, mid = 0.45 },
  tiles = tiles,
  objects = {
    { type = 'banana', x = 120, y = 320 }, { type = 'banana', x = 140, y = 320 },
    { type = 'banana_bunch', x = 200, y = 200 },
    { type = 'kritter', x = 250, y = 192 }, { type = 'kritter', x = 280, y = 192 },
    { type = 'klamp', x = 400, y = 160 }, { type = 'klamp', x = 420, y = 160 },
    { type = 'zinger', x = 350, y = 240, params = { patrol_min = 300, patrol_max = 420 } },
    { type = 'zinger', x = 500, y = 128, params = { patrol_min = 460, patrol_max = 560 } },
    { type = 'klobber', x = 320, y = 304 },
    { type = 'klobber', x = 520, y = 304 },
    { type = 'flitter', x = 600, y = 160, params = { patrol_min = 540, patrol_max = 660 } },
    { type = 'krusha', x = 700, y = 128 },
    { type = 'kopter', x = 780, y = 192, params = { patrol_min = 740, patrol_max = 840 } },
    { type = 'zinger', x = 900, y = 288, params = { patrol_min = 860, patrol_max = 960 } },
    { type = 'dk_coin', x = 640, y = 256 },
    { type = 'life_balloon', x = 1100, y = 192 },
    { type = 'barrel', x = 160, y = 288 }, { type = 'barrel', x = 500, y = 240 },
    { type = 'bonus_barrel', x = 880, y = 352 },
  },
}
