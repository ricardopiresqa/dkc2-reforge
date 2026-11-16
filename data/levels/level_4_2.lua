local W, H = 80, 24
local tiles = {}
for row = 0, H - 1 do
  tiles[row + 1] = {}
  for col = 0, W - 1 do
    if row == H - 1 then
      tiles[row + 1][col + 1] = 1
    elseif col == 0 or col == W - 1 then
      tiles[row + 1][col + 1] = 1
    elseif row >= 20 and row <= 21 and col >= 8 and col <= 16 then
      tiles[row + 1][col + 1] = 1
    elseif row >= 20 and row <= 21 and col >= 22 and col <= 30 then
      tiles[row + 1][col + 1] = 1
    elseif row >= 20 and row <= 21 and col >= 36 and col <= 44 then
      tiles[row + 1][col + 1] = 1
    elseif row >= 20 and row <= 21 and col >= 50 and col <= 58 then
      tiles[row + 1][col + 1] = 1
    elseif row >= 20 and row <= 21 and col >= 64 and col <= 74 then
      tiles[row + 1][col + 1] = 1
    elseif row == 17 and col >= 12 and col <= 16 then
      tiles[row + 1][col + 1] = 2
    elseif row == 14 and col >= 26 and col <= 30 then
      tiles[row + 1][col + 1] = 2
    elseif row == 11 and col >= 40 and col <= 44 then
      tiles[row + 1][col + 1] = 2
    elseif row == 8 and col >= 54 and col <= 58 then
      tiles[row + 1][col + 1] = 2
    elseif row == 5 and col >= 68 and col <= 72 then
      tiles[row + 1][col + 1] = 2
    elseif row == 22 and col >= 12 and col <= 14 then
      tiles[row + 1][col + 1] = 0
    elseif row == 22 and col >= 26 and col <= 28 then
      tiles[row + 1][col + 1] = 0
    elseif row == 22 and col >= 40 and col <= 42 then
      tiles[row + 1][col + 1] = 0
    elseif row == 22 and col >= 54 and col <= 56 then
      tiles[row + 1][col + 1] = 0
    elseif row == 22 and col >= 68 and col <= 70 then
      tiles[row + 1][col + 1] = 0
    elseif row == 19 and col >= 18 and col <= 20 then
      tiles[row + 1][col + 1] = 5
    elseif row == 15 and col >= 32 and col <= 34 then
      tiles[row + 1][col + 1] = 5
    elseif row == 12 and col >= 46 and col <= 48 then
      tiles[row + 1][col + 1] = 5
    elseif row == 9 and col >= 60 and col <= 62 then
      tiles[row + 1][col + 1] = 5
    else
      tiles[row + 1][col + 1] = 0
    end
  end
end

return {
  id = '4-2',
  name = "Kannon's Alley",
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
    { type = 'banana_bunch', x = 300, y = 256 },
    { type = 'banana_bunch', x = 600, y = 192 },
    { type = 'banana', x = 200, y = 352 },
    { type = 'banana', x = 450, y = 352 },
    { type = 'kritter', x = 350, y = 208 },
    { type = 'klamp', x = 550, y = 160 },
    { type = 'klobber', x = 700, y = 288 },
    { type = 'zinger', x = 500, y = 352, params = { patrol_min = 440, patrol_max = 560 } },
    { type = 'zinger', x = 800, y = 224, params = { patrol_min = 740, patrol_max = 860 } },
    { type = 'krusha', x = 900, y = 128 },
    { type = 'flitter', x = 1000, y = 320, params = { patrol_min = 940, patrol_max = 1060 } },
    { type = 'dk_coin', x = 750, y = 112 },
    { type = 'life_balloon', x = 1050, y = 224 },
    { type = 'barrel', x = 400, y = 304 },
    { type = 'bonus_barrel', x = 950, y = 144 },
  },
}
