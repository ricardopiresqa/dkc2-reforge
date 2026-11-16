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
    elseif row >= 19 and row <= 20 and col >= 8 and col <= 14 then
      tiles[row + 1][col + 1] = 1
    elseif row >= 16 and row <= 17 and col >= 20 and col <= 26 then
      tiles[row + 1][col + 1] = 1
    elseif row >= 13 and row <= 14 and col >= 32 and col <= 38 then
      tiles[row + 1][col + 1] = 1
    elseif row >= 10 and row <= 11 and col >= 44 and col <= 50 then
      tiles[row + 1][col + 1] = 1
    elseif row >= 7 and row <= 8 and col >= 56 and col <= 62 then
      tiles[row + 1][col + 1] = 1
    elseif row >= 4 and row <= 5 and col >= 66 and col <= 72 then
      tiles[row + 1][col + 1] = 1
    elseif row == 2 and col >= 20 and col <= 30 then
      tiles[row + 1][col + 1] = 2
    elseif row == 22 and col >= 16 and col <= 18 then
      tiles[row + 1][col + 1] = 0
    elseif row == 22 and col >= 28 and col <= 30 then
      tiles[row + 1][col + 1] = 0
    elseif row == 22 and col >= 40 and col <= 42 then
      tiles[row + 1][col + 1] = 0
    elseif row == 22 and col >= 52 and col <= 54 then
      tiles[row + 1][col + 1] = 0
    elseif row == 11 and col >= 52 and col <= 54 then
      tiles[row + 1][col + 1] = 5
    elseif row == 9 and col >= 40 and col <= 42 then
      tiles[row + 1][col + 1] = 5
    else
      tiles[row + 1][col + 1] = 0
    end
  end
end

return {
  id = '5-2',
  name = "Krock's Krypt",
  width = W,
  height = H,
  tile_size = 16,
  player_spawn = { x = 80, y = 128 },
  camera = { bound_x = 1280, bound_y = 400 },
  parallax = {
    bg = 0.1,
    far = 0.3,
    mid = 0.55,
  },
  tiles = tiles,
  objects = {
    { type = 'banana', x = 140, y = 320 },
    { type = 'banana_bunch', x = 400, y = 240 },
    { type = 'banana_bunch', x = 700, y = 176 },
    { type = 'kritter', x = 300, y = 192 },
    { type = 'klamp', x = 500, y = 160 },
    { type = 'klobber', x = 650, y = 288 },
    { type = 'zinger', x = 450, y = 352, params = { patrol_min = 380, patrol_max = 500 } },
    { type = 'zinger', x = 800, y = 256, params = { patrol_min = 740, patrol_max = 860 } },
    { type = 'flitter', x = 950, y = 192, params = { patrol_min = 880, patrol_max = 1000 } },
    { type = 'krusha', x = 750, y = 128 },
    { type = 'dk_coin', x = 1050, y = 256 },
    { type = 'life_balloon', x = 1100, y = 144 },
    { type = 'barrel', x = 350, y = 304 },
    { type = 'bonus_barrel', x = 1000, y = 352 },
  },
}
