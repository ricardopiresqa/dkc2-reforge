local W, H = 80, 24
local tiles = {}
for row = 0, H - 1 do
  tiles[row + 1] = {}
  for col = 0, W - 1 do
    if row == H - 1 then
      tiles[row + 1][col + 1] = 1
    elseif col == 0 or col == W - 1 then
      tiles[row + 1][col + 1] = 1
    elseif row >= 22 and row <= 23 and col >= 76 and col <= 78 then
      tiles[row + 1][col + 1] = 1
    elseif row >= 20 and row <= 21 and col >= 8 and col <= 16 then
      tiles[row + 1][col + 1] = 1
    elseif row >= 20 and row <= 21 and col >= 22 and col <= 30 then
      tiles[row + 1][col + 1] = 1
    elseif row >= 20 and row <= 21 and col >= 36 and col <= 44 then
      tiles[row + 1][col + 1] = 1
    elseif row >= 17 and row <= 18 and col >= 12 and col <= 16 then
      tiles[row + 1][col + 1] = 2
    elseif row == 14 and col >= 26 and col <= 30 then
      tiles[row + 1][col + 1] = 2
    elseif row == 11 and col >= 40 and col <= 44 then
      tiles[row + 1][col + 1] = 2
    elseif row >= 6 and row <= 7 and col >= 52 and col <= 60 then
      tiles[row + 1][col + 1] = 1
    elseif row == 3 and col >= 30 and col <= 40 then
      tiles[row + 1][col + 1] = 2
    elseif row == 1 and col >= 10 and col <= 20 then
      tiles[row + 1][col + 1] = 2
    elseif row == 22 and col >= 12 and col <= 14 then
      tiles[row + 1][col + 1] = 0
    elseif row == 22 and col >= 26 and col <= 28 then
      tiles[row + 1][col + 1] = 0
    elseif row == 19 and col >= 18 and col <= 20 then
      tiles[row + 1][col + 1] = 5
    elseif row == 12 and col >= 32 and col <= 34 then
      tiles[row + 1][col + 1] = 5
    elseif row == 8 and col >= 46 and col <= 48 then
      tiles[row + 1][col + 1] = 5
    else
      tiles[row + 1][col + 1] = 0
    end
  end
end

return {
  id = '4-5',
  name = "Kreep's Krypt",
  width = W,
  height = H,
  tile_size = 16,
  player_spawn = { x = 80, y = 128 },
  camera = { bound_x = 1280, bound_y = 384 },
  parallax = {
    bg = 0.14,
    far = 0.36,
    mid = 0.65,
  },
  tiles = tiles,
  objects = {
    { type = 'banana', x = 200, y = 320 },
    { type = 'banana_bunch', x = 500, y = 224 },
    { type = 'banana_bunch', x = 800, y = 176 },
    { type = 'kritter', x = 300, y = 176 },
    { type = 'klamp', x = 550, y = 144 },
    { type = 'klobber', x = 650, y = 288 },
    { type = 'zinger', x = 400, y = 352, params = { patrol_min = 340, patrol_max = 460 } },
    { type = 'zinger', x = 750, y = 256, params = { patrol_min = 680, patrol_max = 800 } },
    { type = 'flitter', x = 900, y = 176, params = { patrol_min = 840, patrol_max = 960 } },
    { type = 'krusha', x = 850, y = 128 },
    { type = 'dk_coin', x = 1000, y = 128 },
    { type = 'life_balloon', x = 1050, y = 272 },
    { type = 'barrel', x = 400, y = 272 },
    { type = 'bonus_barrel', x = 1100, y = 208 },
  },
}
