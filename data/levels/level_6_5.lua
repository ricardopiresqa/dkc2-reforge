local W, H = 80, 24
local tiles = {}
for row = 0, H - 1 do
  tiles[row + 1] = {}
  for col = 0, W - 1 do
    if row == H - 1 then
      tiles[row + 1][col + 1] = 1
    elseif col == 0 or col == W - 1 then
      tiles[row + 1][col + 1] = 1
    elseif row >= 22 and col >= 2 and col <= 8 then
      tiles[row + 1][col + 1] = 1
    elseif row >= 20 and row <= 21 and col >= 12 and col <= 18 then
      tiles[row + 1][col + 1] = 1
    elseif row >= 22 and col >= 22 and col <= 28 then
      tiles[row + 1][col + 1] = 1
    elseif row >= 20 and row <= 21 and col >= 32 and col <= 38 then
      tiles[row + 1][col + 1] = 1
    elseif row >= 22 and col >= 42 and col <= 48 then
      tiles[row + 1][col + 1] = 1
    elseif row >= 20 and row <= 21 and col >= 52 and col <= 58 then
      tiles[row + 1][col + 1] = 1
    elseif row >= 22 and col >= 62 and col <= 68 then
      tiles[row + 1][col + 1] = 1
    elseif row >= 20 and row <= 21 and col >= 72 and col <= 78 then
      tiles[row + 1][col + 1] = 1
    elseif row >= 16 and row <= 17 and col >= 6 and col <= 8 then
      tiles[row + 1][col + 1] = 2
    elseif row >= 12 and row <= 13 and col >= 16 and col <= 18 then
      tiles[row + 1][col + 1] = 2
    elseif row >= 8 and row <= 9 and col >= 26 and col <= 28 then
      tiles[row + 1][col + 1] = 2
    elseif row >= 4 and row <= 5 and col >= 36 and col <= 38 then
      tiles[row + 1][col + 1] = 2
    elseif row >= 2 and row <= 3 and col >= 46 and col <= 50 then
      tiles[row + 1][col + 1] = 2
    elseif row >= 2 and row <= 3 and col >= 56 and col <= 60 then
      tiles[row + 1][col + 1] = 2
    elseif row >= 14 and row <= 18 and col >= 38 and col <= 40 then
      tiles[row + 1][col + 1] = 0
    elseif row >= 6 and row <= 10 and col >= 52 and col <= 54 then
      tiles[row + 1][col + 1] = 0
    elseif row >= 8 and row <= 9 and col >= 42 and col <= 44 then
      tiles[row + 1][col + 1] = 5
    elseif row >= 2 and row <= 3 and col >= 34 and col <= 36 then
      tiles[row + 1][col + 1] = 5
    elseif row >= 20 and col >= 28 and col <= 30 then
      tiles[row + 1][col + 1] = 5
    elseif row >= 22 and col >= 50 and col <= 52 then
      tiles[row + 1][col + 1] = 3
    else
      tiles[row + 1][col + 1] = 0
    end
  end
end

return {
  id = '6-5',
  name = "The Final Frontier",
  width = W, height = H, tile_size = 16,
  player_spawn = { x = 80, y = 128 },
  camera = { bound_x = 1280, bound_y = 384 },
  parallax = { bg = 0.05, far = 0.2, mid = 0.45 },
  tiles = tiles,
  objects = {
    { type = 'banana', x = 80, y = 320 }, { type = 'banana', x = 100, y = 320 },
    { type = 'banana_bunch', x = 180, y = 200 },
    { type = 'banana_bunch', x = 500, y = 160 },
    { type = 'banana_bunch', x = 900, y = 224 },
    { type = 'kritter', x = 160, y = 192 }, { type = 'kritter', x = 180, y = 192 },
    { type = 'klamp', x = 300, y = 160 }, { type = 'klamp', x = 320, y = 160 },
    { type = 'zinger', x = 380, y = 240, params = { patrol_min = 320, patrol_max = 440 } },
    { type = 'klobber', x = 450, y = 304 },
    { type = 'zinger', x = 550, y = 128, params = { patrol_min = 500, patrol_max = 620 } },
    { type = 'flitter', x = 650, y = 176, params = { patrol_min = 580, patrol_max = 700 } },
    { type = 'kopter', x = 750, y = 208, params = { patrol_min = 700, patrol_max = 800 } },
    { type = 'krusha', x = 850, y = 128 },
    { type = 'zinger', x = 950, y = 288, params = { patrol_min = 900, patrol_max = 1000 } },
    { type = 'kritter', x = 1050, y = 304 }, { type = 'kritter', x = 1070, y = 304 },
    { type = 'klobber', x = 1120, y = 304 },
    { type = 'dk_coin', x = 700, y = 256 },
    { type = 'life_balloon', x = 200, y = 288 },
    { type = 'barrel', x = 280, y = 288 }, { type = 'barrel', x = 600, y = 240 },
    { type = 'bonus_barrel', x = 960, y = 352 },
  },
}
