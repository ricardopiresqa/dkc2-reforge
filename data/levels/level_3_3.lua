local W, H = 80, 24
local tiles = {}
for row = 0, H - 1 do
  tiles[row + 1] = {}
  for col = 0, W - 1 do
    if row == H - 1 then
      tiles[row + 1][col + 1] = 1
    elseif col == 0 or col == W - 1 then
      tiles[row + 1][col + 1] = 1
    elseif row >= 16 and row <= 17 and col >= 8 and col <= 16 then
      tiles[row + 1][col + 1] = 1
    elseif row >= 12 and row <= 13 and col >= 22 and col <= 30 then
      tiles[row + 1][col + 1] = 1
    elseif row >= 8 and row <= 9 and col >= 36 and col <= 44 then
      tiles[row + 1][col + 1] = 1
    elseif row >= 4 and row <= 5 and col >= 50 and col <= 58 then
      tiles[row + 1][col + 1] = 1
    elseif row >= 20 and row <= 21 and col >= 39 and col <= 50 then
      tiles[row + 1][col + 1] = 4
    elseif row >= 20 and row <= 21 and col >= 58 and col <= 68 then
      tiles[row + 1][col + 1] = 4
    elseif row == 22 and col >= 12 and col <= 14 then
      tiles[row + 1][col + 1] = 0
    elseif row == 22 and col >= 26 and col <= 28 then
      tiles[row + 1][col + 1] = 0
    elseif row == 1 and col >= 60 and col <= 70 then
      tiles[row + 1][col + 1] = 2
    elseif row >= 22 and row <= 23 and col >= 76 and col <= 78 then
      tiles[row + 1][col + 1] = 1
    else
      tiles[row + 1][col + 1] = 0
    end
  end
end

return {
  id = '3-3',
  name = "Screech's Spring",
  width = W,
  height = H,
  tile_size = 16,
  player_spawn = { x = 80, y = 128 },
  camera = { bound_x = 1280, bound_y = 384 },
  parallax = {
    bg = 0.15,
    far = 0.4,
    mid = 0.65,
  },
  tiles = tiles,
  objects = {
    { type = 'banana_bunch', x = 250, y = 304 },
    { type = 'kritter', x = 200, y = 208 },
    { type = 'klobber', x = 350, y = 176 },
    { type = 'klamp', x = 500, y = 144 },
    { type = 'zinger', x = 650, y = 240, params = { patrol_min = 600, patrol_max = 700 } },
    { type = 'banana', x = 400, y = 352 },
    { type = 'banana', x = 600, y = 352 },
    { type = 'krusha', x = 700, y = 128 },
    { type = 'dk_coin', x = 850, y = 160 },
    { type = 'life_balloon', x = 950, y = 128 },
    { type = 'barrel', x = 300, y = 240 },
    { type = 'bonus_barrel', x = 1000, y = 272 },
  },
}
