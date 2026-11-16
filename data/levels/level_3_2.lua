local W, H = 80, 24
local tiles = {}
for row = 0, H - 1 do
  tiles[row + 1] = {}
  for col = 0, W - 1 do
    if row == H - 1 then
      tiles[row + 1][col + 1] = 1
    elseif col == 0 or col == W - 1 then
      tiles[row + 1][col + 1] = 1
    elseif row >= 20 and row <= 21 and col >= 6 and col <= 14 then
      tiles[row + 1][col + 1] = 1
    elseif row >= 18 and row <= 19 and col >= 18 and col <= 24 then
      tiles[row + 1][col + 1] = 1
    elseif row >= 15 and row <= 16 and col >= 30 and col <= 36 then
      tiles[row + 1][col + 1] = 1
    elseif row >= 12 and row <= 13 and col >= 44 and col <= 50 then
      tiles[row + 1][col + 1] = 1
    elseif row >= 9 and row <= 10 and col >= 56 and col <= 62 then
      tiles[row + 1][col + 1] = 1
    elseif row >= 6 and row <= 7 and col >= 66 and col <= 74 then
      tiles[row + 1][col + 1] = 1
    elseif row == 3 and col >= 40 and col <= 50 then
      tiles[row + 1][col + 1] = 2
    elseif row == 1 and col >= 10 and col <= 20 then
      tiles[row + 1][col + 1] = 2
    elseif row == 22 and col >= 16 and col <= 18 then
      tiles[row + 1][col + 1] = 0
    elseif row == 22 and col >= 28 and col <= 30 then
      tiles[row + 1][col + 1] = 0
    elseif row == 22 and col >= 42 and col <= 44 then
      tiles[row + 1][col + 1] = 0
    elseif row >= 22 and row <= 23 and col >= 76 and col <= 78 then
      tiles[row + 1][col + 1] = 1
    else
      tiles[row + 1][col + 1] = 0
    end
  end
end

return {
  id = '3-2',
  name = "Spiders' Web",
  width = W,
  height = H,
  tile_size = 16,
  player_spawn = { x = 80, y = 128 },
  camera = { bound_x = 1280, bound_y = 400 },
  parallax = {
    bg = 0.2,
    far = 0.5,
    mid = 0.75,
  },
  tiles = tiles,
  objects = {
    { type = 'banana', x = 120, y = 320 },
    { type = 'banana_bunch', x = 300, y = 272 },
    { type = 'kritter', x = 250, y = 304 },
    { type = 'zinger', x = 400, y = 240, params = { patrol_min = 360, patrol_max = 440 } },
    { type = 'zinger', x = 600, y = 192, params = { patrol_min = 560, patrol_max = 660 } },
    { type = 'flitter', x = 700, y = 320, params = { patrol_min = 660, patrol_max = 760 } },
    { type = 'banana_bunch', x = 850, y = 208 },
    { type = 'klamp', x = 480, y = 256 },
    { type = 'krusha', x = 750, y = 176 },
    { type = 'barrel', x = 320, y = 240 },
    { type = 'dk_coin', x = 1000, y = 144 },
    { type = 'life_balloon', x = 1050, y = 288 },
    { type = 'bonus_barrel', x = 1100, y = 192 },
  },
}
