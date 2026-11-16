local W, H = 80, 24
local tiles = {}
for row = 0, H - 1 do
  tiles[row + 1] = {}
  for col = 0, W - 1 do
    if row == H - 1 then
      tiles[row + 1][col + 1] = 1
    elseif col == 0 or col == W - 1 then
      tiles[row + 1][col + 1] = 1
    elseif row >= 21 and row <= 22 and col >= 8 and col <= 16 then
      tiles[row + 1][col + 1] = 1
    elseif row >= 21 and row <= 22 and col >= 25 and col <= 34 then
      tiles[row + 1][col + 1] = 3
    elseif row >= 21 and row <= 22 and col >= 36 and col <= 44 then
      tiles[row + 1][col + 1] = 1
    elseif row >= 21 and row <= 22 and col >= 50 and col <= 56 then
      tiles[row + 1][col + 1] = 3
    elseif row >= 21 and row <= 22 and col >= 60 and col <= 68 then
      tiles[row + 1][col + 1] = 1
    elseif row >= 21 and row <= 22 and col >= 70 and col <= 78 then
      tiles[row + 1][col + 1] = 3
    elseif row == 18 and col >= 10 and col <= 14 then
      tiles[row + 1][col + 1] = 2
    elseif row == 15 and col >= 24 and col <= 28 then
      tiles[row + 1][col + 1] = 2
    elseif row == 12 and col >= 38 and col <= 42 then
      tiles[row + 1][col + 1] = 2
    elseif row == 10 and col >= 52 and col <= 56 then
      tiles[row + 1][col + 1] = 2
    elseif row == 7 and col >= 64 and col <= 68 then
      tiles[row + 1][col + 1] = 2
    elseif row == 19 and col >= 18 and col <= 20 then
      tiles[row + 1][col + 1] = 5
    elseif row == 13 and col >= 30 and col <= 32 then
      tiles[row + 1][col + 1] = 5
    elseif row == 8 and col >= 44 and col <= 46 then
      tiles[row + 1][col + 1] = 5
    else
      tiles[row + 1][col + 1] = 0
    end
  end
end

return {
  id = '4-1',
  name = 'Gloomy Gulch',
  width = W,
  height = H,
  tile_size = 16,
  player_spawn = { x = 80, y = 128 },
  camera = { bound_x = 1280, bound_y = 384 },
  parallax = {
    bg = 0.15,
    far = 0.4,
    mid = 0.7,
  },
  tiles = tiles,
  objects = {
    { type = 'banana', x = 160, y = 320 },
    { type = 'banana_bunch', x = 400, y = 256 },
    { type = 'banana_bunch', x = 700, y = 192 },
    { type = 'kritter', x = 300, y = 224 },
    { type = 'klamp', x = 500, y = 160 },
    { type = 'klobber', x = 600, y = 288 },
    { type = 'zinger', x = 450, y = 352, params = { patrol_min = 400, patrol_max = 520 } },
    { type = 'zinger', x = 800, y = 240, params = { patrol_min = 740, patrol_max = 860 } },
    { type = 'flitter', x = 950, y = 176, params = { patrol_min = 900, patrol_max = 1000 } },
    { type = 'krusha', x = 850, y = 128 },
    { type = 'dk_coin', x = 1050, y = 240 },
    { type = 'life_balloon', x = 1100, y = 160 },
    { type = 'barrel', x = 250, y = 256 },
    { type = 'bonus_barrel', x = 1000, y = 320 },
  },
}
