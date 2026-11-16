local W, H = 80, 24
local tiles = {}
for row = 0, H - 1 do
  tiles[row + 1] = {}
  for col = 0, W - 1 do
    if row == H - 1 then
      tiles[row + 1][col + 1] = 1
    elseif col == 0 or col == W - 1 then
      tiles[row + 1][col + 1] = 1
    elseif row >= 22 and row <= 23 and col >= 72 and col <= 78 then
      tiles[row + 1][col + 1] = 1
    elseif row >= 20 and row <= 21 and col >= 8 and col <= 14 then
      tiles[row + 1][col + 1] = 1
    elseif row >= 20 and row <= 21 and col >= 18 and col <= 24 then
      tiles[row + 1][col + 1] = 1
    elseif row >= 20 and row <= 21 and col >= 30 and col <= 38 then
      tiles[row + 1][col + 1] = 1
    elseif row >= 20 and row <= 21 and col >= 44 and col <= 50 then
      tiles[row + 1][col + 1] = 1
    elseif row >= 20 and row <= 21 and col >= 56 and col <= 64 then
      tiles[row + 1][col + 1] = 1
    elseif row >= 17 and row <= 18 and col >= 12 and col <= 16 then
      tiles[row + 1][col + 1] = 2
    elseif row >= 14 and row <= 15 and col >= 22 and col <= 26 then
      tiles[row + 1][col + 1] = 2
    elseif row == 11 and col >= 34 and col <= 38 then
      tiles[row + 1][col + 1] = 2
    elseif row >= 7 and row <= 8 and col >= 48 and col <= 52 then
      tiles[row + 1][col + 1] = 2
    elseif row >= 4 and row <= 5 and col >= 60 and col <= 64 then
      tiles[row + 1][col + 1] = 2
    elseif row >= 1 and row <= 2 and col >= 30 and col <= 40 then
      tiles[row + 1][col + 1] = 2
    elseif row == 22 and col >= 16 and col <= 18 then
      tiles[row + 1][col + 1] = 0
    elseif row == 22 and col >= 28 and col <= 30 then
      tiles[row + 1][col + 1] = 0
    elseif row == 22 and col >= 42 and col <= 44 then
      tiles[row + 1][col + 1] = 0
    elseif row == 22 and col >= 54 and col <= 56 then
      tiles[row + 1][col + 1] = 0
    elseif row >= 20 and row <= 21 and col >= 66 and col <= 74 then
      tiles[row + 1][col + 1] = 3
    elseif row == 12 and col >= 28 and col <= 30 then
      tiles[row + 1][col + 1] = 5
    elseif row == 6 and col >= 54 and col <= 56 then
      tiles[row + 1][col + 1] = 5
    else
      tiles[row + 1][col + 1] = 0
    end
  end
end

return {
  id = '5-4',
  name = "Krool's Krown",
  width = W,
  height = H,
  tile_size = 16,
  player_spawn = { x = 80, y = 128 },
  camera = { bound_x = 1280, bound_y = 384 },
  parallax = {
    bg = 0.05,
    far = 0.2,
    mid = 0.45,
  },
  tiles = tiles,
  objects = {
    { type = 'banana', x = 160, y = 320 },
    { type = 'banana_bunch', x = 400, y = 224 },
    { type = 'banana_bunch', x = 700, y = 144 },
    { type = 'kritter', x = 300, y = 192 },
    { type = 'klamp', x = 500, y = 160 },
    { type = 'klobber', x = 600, y = 304 },
    { type = 'zinger', x = 450, y = 272, params = { patrol_min = 380, patrol_max = 500 } },
    { type = 'zinger', x = 800, y = 352, params = { patrol_min = 740, patrol_max = 860 } },
    { type = 'flitter', x = 950, y = 208, params = { patrol_min = 880, patrol_max = 1000 } },
    { type = 'krusha', x = 850, y = 128 },
    { type = 'dk_coin', x = 1050, y = 256 },
    { type = 'life_balloon', x = 1100, y = 192 },
    { type = 'barrel', x = 350, y = 288 },
    { type = 'bonus_barrel', x = 1000, y = 352 },
  },
}
