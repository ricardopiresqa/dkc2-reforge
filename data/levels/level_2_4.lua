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
      tiles[row + 1][col + 1] = 4
    elseif row >= 20 and row <= 21 and col >= 20 and col <= 30 then
      tiles[row + 1][col + 1] = 4
    elseif row >= 20 and row <= 21 and col >= 36 and col <= 44 then
      tiles[row + 1][col + 1] = 4
    elseif row >= 20 and row <= 21 and col >= 52 and col <= 60 then
      tiles[row + 1][col + 1] = 4
    elseif row >= 20 and row <= 21 and col >= 68 and col <= 78 then
      tiles[row + 1][col + 1] = 4
    elseif row == 17 and col >= 10 and col <= 14 then
      tiles[row + 1][col + 1] = 2
    elseif row == 14 and col >= 24 and col <= 28 then
      tiles[row + 1][col + 1] = 2
    elseif row == 12 and col >= 40 and col <= 44 then
      tiles[row + 1][col + 1] = 2
    elseif row == 9 and col >= 56 and col <= 60 then
      tiles[row + 1][col + 1] = 2
    elseif row == 7 and col >= 70 and col <= 74 then
      tiles[row + 1][col + 1] = 2
    elseif row == 22 and col >= 10 and col <= 12 then
      tiles[row + 1][col + 1] = 0
    elseif row == 22 and col >= 32 and col <= 34 then
      tiles[row + 1][col + 1] = 0
    elseif row == 22 and col >= 48 and col <= 50 then
      tiles[row + 1][col + 1] = 0
    elseif row == 22 and col >= 64 and col <= 66 then
      tiles[row + 1][col + 1] = 0
    elseif row == 19 and col >= 18 and col <= 20 then
      tiles[row + 1][col + 1] = 3
    elseif row == 16 and col >= 30 and col <= 32 then
      tiles[row + 1][col + 1] = 3
    elseif row >= 18 and row <= 19 and col >= 46 and col <= 48 then
      tiles[row + 1][col + 1] = 5
    elseif row >= 21 and row <= 22 and col >= 75 and col <= 78 then
      tiles[row + 1][col + 1] = 1
    else
      tiles[row + 1][col + 1] = 0
    end
  end
end

return {
  id = '2-4',
  name = 'Hot Head Hop',
  width = W,
  height = H,
  tile_size = 16,
  player_spawn = { x = 80, y = 128 },
  camera = { bound_x = 1280, bound_y = 384 },
  parallax = {
    bg = 0.1,
    far = 0.35,
    mid = 0.65,
  },
  tiles = tiles,
  objects = {
    { type = 'banana', x = 150, y = 288 },
    { type = 'banana_bunch', x = 400, y = 224 },
    { type = 'banana_bunch', x = 700, y = 352 },
    { type = 'kritter', x = 250, y = 320 },
    { type = 'klamp', x = 550, y = 320 },
    { type = 'zinger', x = 320, y = 192, params = { patrol_min = 280, patrol_max = 400 } },
    { type = 'zinger', x = 650, y = 224, params = { patrol_min = 600, patrol_max = 720 } },
    { type = 'krusha', x = 850, y = 192 },
    { type = 'flitter', x = 950, y = 280, params = { patrol_min = 900, patrol_max = 1020 } },
    { type = 'dk_coin', x = 800, y = 320 },
    { type = 'life_balloon', x = 1000, y = 224 },
    { type = 'barrel', x = 450, y = 192 },
    { type = 'bonus_barrel', x = 1150, y = 240 },
  },
}
