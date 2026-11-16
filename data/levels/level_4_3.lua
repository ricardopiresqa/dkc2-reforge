local W, H = 80, 24
local tiles = {}
for row = 0, H - 1 do
  tiles[row + 1] = {}
  for col = 0, W - 1 do
    if row == H - 1 then
      tiles[row + 1][col + 1] = 1
    elseif col == 0 or col == W - 1 then
      tiles[row + 1][col + 1] = 1
    elseif row >= 20 and row <= 21 and col >= 6 and col <= 12 then
      tiles[row + 1][col + 1] = 1
    elseif row >= 17 and row <= 18 and col >= 16 and col <= 22 then
      tiles[row + 1][col + 1] = 1
    elseif row >= 14 and row <= 15 and col >= 26 and col <= 32 then
      tiles[row + 1][col + 1] = 1
    elseif row >= 11 and row <= 12 and col >= 36 and col <= 42 then
      tiles[row + 1][col + 1] = 1
    elseif row >= 8 and row <= 9 and col >= 46 and col <= 52 then
      tiles[row + 1][col + 1] = 1
    elseif row >= 5 and row <= 6 and col >= 56 and col <= 62 then
      tiles[row + 1][col + 1] = 1
    elseif row == 3 and col >= 20 and col <= 30 then
      tiles[row + 1][col + 1] = 2
    elseif row == 1 and col >= 50 and col <= 60 then
      tiles[row + 1][col + 1] = 2
    elseif row == 22 and col >= 10 and col <= 12 then
      tiles[row + 1][col + 1] = 0
    elseif row == 22 and col >= 20 and col <= 22 then
      tiles[row + 1][col + 1] = 0
    elseif row == 22 and col >= 30 and col <= 32 then
      tiles[row + 1][col + 1] = 0
    elseif row == 18 and col >= 24 and col <= 26 then
      tiles[row + 1][col + 1] = 5
    elseif row == 12 and col >= 34 and col <= 36 then
      tiles[row + 1][col + 1] = 5
    elseif row == 8 and col >= 44 and col <= 46 then
      tiles[row + 1][col + 1] = 5
    elseif row >= 22 and row <= 23 and col >= 74 and col <= 78 then
      tiles[row + 1][col + 1] = 1
    else
      tiles[row + 1][col + 1] = 0
    end
  end
end

return {
  id = '4-3',
  name = 'Kreepy Keep',
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
    { type = 'banana', x = 140, y = 320 },
    { type = 'banana_bunch', x = 320, y = 240 },
    { type = 'banana_bunch', x = 650, y = 192 },
    { type = 'kritter', x = 250, y = 224 },
    { type = 'klamp', x = 450, y = 176 },
    { type = 'zinger', x = 400, y = 352, params = { patrol_min = 340, patrol_max = 460 } },
    { type = 'zinger', x = 700, y = 288, params = { patrol_min = 640, patrol_max = 760 } },
    { type = 'flitter', x = 850, y = 176, params = { patrol_min = 800, patrol_max = 920 } },
    { type = 'krusha', x = 600, y = 112 },
    { type = 'klobber', x = 750, y = 240 },
    { type = 'dk_coin', x = 900, y = 128 },
    { type = 'life_balloon', x = 1000, y = 288 },
    { type = 'barrel', x = 500, y = 304 },
    { type = 'bonus_barrel', x = 1100, y = 224 },
  },
}
