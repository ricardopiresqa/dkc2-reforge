local W, H = 80, 24
local tiles = {}
for row = 0, H - 1 do
  tiles[row + 1] = {}
  for col = 0, W - 1 do
    if row == H - 1 then
      tiles[row + 1][col + 1] = 1
    elseif col == 0 or col == W - 1 then
      tiles[row + 1][col + 1] = 1
    elseif row >= 18 and row <= 19 and col >= 6 and col <= 12 then
      tiles[row + 1][col + 1] = 1
    elseif row >= 18 and row <= 19 and col >= 18 and col <= 24 then
      tiles[row + 1][col + 1] = 1
    elseif row >= 18 and row <= 19 and col >= 30 and col <= 36 then
      tiles[row + 1][col + 1] = 1
    elseif row >= 18 and row <= 19 and col >= 42 and col <= 48 then
      tiles[row + 1][col + 1] = 1
    elseif row >= 18 and row <= 19 and col >= 54 and col <= 60 then
      tiles[row + 1][col + 1] = 1
    elseif row >= 14 and row <= 15 and col >= 10 and col <= 14 then
      tiles[row + 1][col + 1] = 2
    elseif row >= 10 and row <= 11 and col >= 22 and col <= 26 then
      tiles[row + 1][col + 1] = 2
    elseif row >= 6 and row <= 7 and col >= 34 and col <= 38 then
      tiles[row + 1][col + 1] = 2
    elseif row >= 2 and row <= 3 and col >= 46 and col <= 50 then
      tiles[row + 1][col + 1] = 2
    elseif row >= 12 and row <= 13 and col >= 52 and col <= 56 then
      tiles[row + 1][col + 1] = 2
    else
      tiles[row + 1][col + 1] = 0
    end
  end
end

return {
  id = '5-5',
  name = "Kremling's End",
  width = W,
  height = H,
  tile_size = 16,
  player_spawn = { x = 80, y = 128 },
  camera = { bound_x = 1280, bound_y = 384 },
  parallax = {
    bg = 0.08,
    far = 0.25,
    mid = 0.5,
  },
  tiles = tiles,
  objects = {
    { type = 'banana', x = 160, y = 320 },
    { type = 'banana', x = 200, y = 320 },
    { type = 'banana', x = 240, y = 320 },
    { type = 'banana_bunch', x = 400, y = 160 },
    { type = 'banana_bunch', x = 700, y = 80 },
    { type = 'kritter', x = 300, y = 208 },
    { type = 'kritter', x = 450, y = 208 },
    { type = 'zinger', x = 350, y = 352, params = { patrol_min = 300, patrol_max = 420 } },
    { type = 'klamp', x = 550, y = 176 },
    { type = 'zinger', x = 650, y = 272, params = { patrol_min = 580, patrol_max = 700 } },
    { type = 'kritter', x = 750, y = 208 },
    { type = 'dk_coin', x = 850, y = 240 },
    { type = 'barrel', x = 500, y = 272 },
    { type = 'life_balloon', x = 900, y = 320 },
  },
}
