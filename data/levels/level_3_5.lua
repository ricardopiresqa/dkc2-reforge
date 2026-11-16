local W, H = 80, 24
local tiles = {}
for row = 0, H - 1 do
  tiles[row + 1] = {}
  for col = 0, W - 1 do
    if row == H - 1 then
      tiles[row + 1][col + 1] = 1
    elseif col == 0 or col == W - 1 then
      tiles[row + 1][col + 1] = 1
    elseif row >= 18 and row <= 19 and col >= 6 and col <= 14 then
      tiles[row + 1][col + 1] = 1
    elseif row >= 15 and row <= 16 and col >= 20 and col <= 26 then
      tiles[row + 1][col + 1] = 1
    elseif row >= 12 and row <= 13 and col >= 34 and col <= 40 then
      tiles[row + 1][col + 1] = 1
    elseif row >= 9 and row <= 10 and col >= 48 and col <= 54 then
      tiles[row + 1][col + 1] = 1
    elseif row >= 6 and row <= 7 and col >= 60 and col <= 68 then
      tiles[row + 1][col + 1] = 1
    elseif row == 3 and col >= 44 and col <= 54 then
      tiles[row + 1][col + 1] = 2
    elseif row == 1 and col >= 12 and col <= 22 then
      tiles[row + 1][col + 1] = 2
    elseif row == 22 and col >= 10 and col <= 12 then
      tiles[row + 1][col + 1] = 0
    elseif row == 22 and col >= 24 and col <= 26 then
      tiles[row + 1][col + 1] = 0
    elseif row == 22 and col >= 38 and col <= 40 then
      tiles[row + 1][col + 1] = 0
    elseif row == 22 and col >= 52 and col <= 54 then
      tiles[row + 1][col + 1] = 0
    elseif row == 4 and col >= 18 and col <= 22 then
      tiles[row + 1][col + 1] = 5
    elseif row >= 22 and row <= 23 and col >= 74 and col <= 78 then
      tiles[row + 1][col + 1] = 1
    else
      tiles[row + 1][col + 1] = 0
    end
  end
end

return {
  id = '3-5',
  name = "King Zing's Hive",
  width = W,
  height = H,
  tile_size = 16,
  player_spawn = { x = 80, y = 128 },
  camera = { bound_x = 1280, bound_y = 384 },
  parallax = {
    bg = 0.1,
    far = 0.3,
    mid = 0.6,
  },
  tiles = tiles,
  objects = {
    { type = 'banana', x = 180, y = 320 },
    { type = 'banana_bunch', x = 350, y = 224 },
    { type = 'banana_bunch', x = 600, y = 176 },
    { type = 'kritter', x = 200, y = 256 },
    { type = 'klamp', x = 450, y = 192 },
    { type = 'klobber', x = 550, y = 304 },
    { type = 'zinger', x = 300, y = 320, params = { patrol_min = 240, patrol_max = 360 } },
    { type = 'zinger', x = 700, y = 160, params = { patrol_min = 640, patrol_max = 760 } },
    { type = 'flitter', x = 850, y = 272, params = { patrol_min = 800, patrol_max = 920 } },
    { type = 'krusha', x = 800, y = 128 },
    { type = 'dk_coin', x = 950, y = 128 },
    { type = 'life_balloon', x = 1000, y = 256 },
    { type = 'barrel', x = 250, y = 288 },
    { type = 'bonus_barrel', x = 900, y = 208 },
  },
}
