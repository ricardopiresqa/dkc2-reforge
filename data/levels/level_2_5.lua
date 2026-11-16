local W, H = 80, 24
local tiles = {}
for row = 0, H - 1 do
  tiles[row + 1] = {}
  for col = 0, W - 1 do
    if row == H - 1 then
      tiles[row + 1][col + 1] = 1
    elseif col == 0 or col == W - 1 then
      tiles[row + 1][col + 1] = 1
    elseif row >= 20 and row <= 21 and col >= 21 and col <= 28 then
      tiles[row + 1][col + 1] = 4
    elseif row >= 20 and row <= 21 and col >= 52 and col <= 60 then
      tiles[row + 1][col + 1] = 4
    elseif row >= 20 and row <= 21 and col >= 34 and col <= 44 then
      tiles[row + 1][col + 1] = 1
    elseif row >= 20 and row <= 21 and col >= 63 and col <= 72 then
      tiles[row + 1][col + 1] = 1
    elseif row == 22 and col >= 46 and col <= 48 then
      tiles[row + 1][col + 1] = 0
    elseif row >= 6 and row <= 7 and col >= 12 and col <= 19 then
      tiles[row + 1][col + 1] = 5
    elseif row == 16 and col >= 30 and col <= 33 then
      tiles[row + 1][col + 1] = 2
    elseif row == 13 and col >= 38 and col <= 42 then
      tiles[row + 1][col + 1] = 2
    elseif row == 9 and col >= 46 and col <= 50 then
      tiles[row + 1][col + 1] = 2
    elseif row == 11 and col >= 56 and col <= 60 then
      tiles[row + 1][col + 1] = 2
    elseif row == 14 and col >= 64 and col <= 68 then
      tiles[row + 1][col + 1] = 2
    elseif row == 12 and col >= 72 and col <= 76 then
      tiles[row + 1][col + 1] = 2
    elseif row >= 17 and row <= 18 and col >= 10 and col <= 14 then
      tiles[row + 1][col + 1] = 1
    elseif row == 4 and col >= 8 and col <= 18 then
      tiles[row + 1][col + 1] = 2
    elseif row == 3 and col >= 46 and col <= 55 then
      tiles[row + 1][col + 1] = 2
    elseif row == 21 and col >= 14 and col <= 18 then
      tiles[row + 1][col + 1] = 3
    elseif row >= 20 and row <= 21 and col >= 74 and col <= 78 then
      tiles[row + 1][col + 1] = 1
    else
      tiles[row + 1][col + 1] = 0
    end
  end
end

return {
  id = '2-5',
  name = "Kannon's Kannon",
  width = W,
  height = H,
  tile_size = 16,
  player_spawn = { x = 80, y = 128 },
  camera = { bound_x = 1280, bound_y = 384 },
  parallax = {
    bg = 0.12,
    far = 0.38,
    mid = 0.68,
  },
  tiles = tiles,
  objects = {
    { type = 'banana', x = 200, y = 304 },
    { type = 'banana_bunch', x = 500, y = 208 },
    { type = 'banana_bunch', x = 800, y = 256 },
    { type = 'kritter', x = 300, y = 320 },
    { type = 'klamp', x = 600, y = 240 },
    { type = 'zinger', x = 400, y = 176, params = { patrol_min = 360, patrol_max = 480 } },
    { type = 'zinger', x = 700, y = 288, params = { patrol_min = 640, patrol_max = 760 } },
    { type = 'flitter', x = 1000, y = 240, params = { patrol_min = 940, patrol_max = 1060 } },
    { type = 'krusha', x = 550, y = 160 },
    { type = 'dk_coin', x = 1050, y = 192 },
    { type = 'life_balloon', x = 900, y = 128 },
    { type = 'barrel', x = 350, y = 176 },
    { type = 'bonus_barrel', x = 750, y = 320 },
  },
}
