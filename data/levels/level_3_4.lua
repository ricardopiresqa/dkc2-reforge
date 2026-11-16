local W, H = 80, 24
local tiles = {}
for row = 0, H - 1 do
  tiles[row + 1] = {}
  for col = 0, W - 1 do
    if row == H - 1 then
      tiles[row + 1][col + 1] = 1
    elseif col == 0 or col == W - 1 then
      tiles[row + 1][col + 1] = 1
    elseif row >= 17 and row <= 18 and col >= 8 and col <= 16 then
      tiles[row + 1][col + 1] = 1
    elseif row >= 13 and row <= 14 and col >= 22 and col <= 30 then
      tiles[row + 1][col + 1] = 1
    elseif row >= 9 and row <= 10 and col >= 36 and col <= 44 then
      tiles[row + 1][col + 1] = 1
    elseif row >= 5 and row <= 6 and col >= 50 and col <= 58 then
      tiles[row + 1][col + 1] = 1
    elseif row >= 20 and row <= 21 and col >= 20 and col <= 26 then
      tiles[row + 1][col + 1] = 3
    elseif row >= 20 and row <= 21 and col >= 32 and col <= 38 then
      tiles[row + 1][col + 1] = 3
    elseif row >= 20 and row <= 21 and col >= 44 and col <= 52 then
      tiles[row + 1][col + 1] = 3
    elseif row >= 20 and row <= 21 and col >= 58 and col <= 66 then
      tiles[row + 1][col + 1] = 3
    elseif row == 22 and col >= 10 and col <= 12 then
      tiles[row + 1][col + 1] = 0
    elseif row == 22 and col >= 20 and col <= 22 then
      tiles[row + 1][col + 1] = 0
    elseif row == 22 and col >= 40 and col <= 42 then
      tiles[row + 1][col + 1] = 0
    elseif row == 2 and col >= 28 and col <= 38 then
      tiles[row + 1][col + 1] = 2
    elseif row >= 22 and row <= 23 and col >= 72 and col <= 78 then
      tiles[row + 1][col + 1] = 1
    else
      tiles[row + 1][col + 1] = 0
    end
  end
end

return {
  id = '3-4',
  name = 'Krack Shot Krome',
  width = W,
  height = H,
  tile_size = 16,
  player_spawn = { x = 80, y = 128 },
  camera = { bound_x = 1280, bound_y = 384 },
  parallax = {
    bg = 0.18,
    far = 0.45,
    mid = 0.72,
  },
  tiles = tiles,
  objects = {
    { type = 'banana', x = 150, y = 320 },
    { type = 'banana_bunch', x = 400, y = 240 },
    { type = 'banana_bunch', x = 750, y = 208 },
    { type = 'kritter', x = 300, y = 208 },
    { type = 'klamp', x = 500, y = 176 },
    { type = 'klobber', x = 600, y = 288 },
    { type = 'zinger', x = 450, y = 160, params = { patrol_min = 400, patrol_max = 520 } },
    { type = 'zinger', x = 800, y = 224, params = { patrol_min = 740, patrol_max = 860 } },
    { type = 'flitter', x = 950, y = 320, params = { patrol_min = 900, patrol_max = 1000 } },
    { type = 'krusha', x = 900, y = 160 },
    { type = 'dk_coin', x = 850, y = 304 },
    { type = 'life_balloon', x = 1000, y = 248 },
    { type = 'barrel', x = 350, y = 272 },
    { type = 'bonus_barrel', x = 700, y = 144 },
  },
}
