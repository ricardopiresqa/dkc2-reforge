local W, H = 80, 24
local tiles = {}
for row = 0, H - 1 do
  tiles[row + 1] = {}
  for col = 0, W - 1 do
    if row == H - 1 then
      tiles[row + 1][col + 1] = 1
    elseif col == 0 or col == W - 1 then
      tiles[row + 1][col + 1] = 1
    elseif row == 20 and col >= 6 and col <= 10 then
      tiles[row + 1][col + 1] = 1
    elseif row >= 19 and row <= 20 and col >= 34 and col <= 38 then
      tiles[row + 1][col + 1] = 6
    elseif row >= 20 and row <= 21 and col >= 60 and col <= 64 then
      tiles[row + 1][col + 1] = 1
    elseif row == 18 and col >= 14 and col <= 20 then
      tiles[row + 1][col + 1] = 2
    elseif row == 15 and col >= 28 and col <= 34 then
      tiles[row + 1][col + 1] = 2
    elseif row == 12 and col >= 42 and col <= 48 then
      tiles[row + 1][col + 1] = 2
    elseif row == 9 and col >= 56 and col <= 62 then
      tiles[row + 1][col + 1] = 2
    elseif row == 7 and col >= 18 and col <= 24 then
      tiles[row + 1][col + 1] = 2
    elseif row == 5 and col >= 40 and col <= 46 then
      tiles[row + 1][col + 1] = 2
    elseif row == 16 and col >= 46 and col <= 48 then
      tiles[row + 1][col + 1] = 3
    elseif row == 10 and col >= 10 and col <= 12 then
      tiles[row + 1][col + 1] = 3
    elseif row == 21 and col >= 24 and col <= 26 then
      tiles[row + 1][col + 1] = 5
    elseif row == 21 and col >= 50 and col <= 52 then
      tiles[row + 1][col + 1] = 5
    elseif row >= 21 and row <= 22 and col >= 70 and col <= 72 then
      tiles[row + 1][col + 1] = 1
    else
      tiles[row + 1][col + 1] = 0
    end
  end
end

return {
  id = '3-1',
  name = 'Web Woods',
  width = W,
  height = H,
  tile_size = 16,
  player_spawn = { x = 80, y = 128 },
  camera = { bound_x = 1280, bound_y = 384 },
  parallax = {
    bg = 0.2,
    far = 0.45,
    mid = 0.7,
  },
  tiles = tiles,
  objects = {
    { type = 'banana', x = 140, y = 320 },
    { type = 'banana', x = 170, y = 320 },
    { type = 'banana', x = 300, y = 256 },
    { type = 'banana', x = 330, y = 256 },
    { type = 'banana_bunch', x = 480, y = 320 },
    { type = 'banana_bunch', x = 680, y = 192 },
    { type = 'kritter', x = 260, y = 225 },
    { type = 'kritter', x = 480, y = 225 },
    { type = 'zinger', x = 550, y = 280, params = { patrol_min = 480, patrol_max = 620 } },
    { type = 'flitter', x = 750, y = 320, params = { patrol_min = 680, patrol_max = 820 } },
    { type = 'klamp', x = 400, y = 225 },
    { type = 'kannon', x = 600, y = 200 },
    { type = 'mininecky', x = 880, y = 240, params = { patrol_min = 800, patrol_max = 960 } },
    { type = 'dk_coin', x = 1000, y = 200 },
    { type = 'life_balloon', x = 1100, y = 180 },
    { type = 'barrel', x = 200, y = 225 },
    { type = 'rambi', x = 450, y = 320 },
  },
}
