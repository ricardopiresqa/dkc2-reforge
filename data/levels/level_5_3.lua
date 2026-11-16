local W, H = 80, 24
local tiles = {}
for row = 0, H - 1 do
  tiles[row + 1] = {}
  for col = 0, W - 1 do
    if row == H - 1 then
      tiles[row + 1][col + 1] = 1
    elseif col == 0 or col == W - 1 then
      tiles[row + 1][col + 1] = 1
    elseif row >= 22 and row <= 23 and col >= 74 and col <= 78 then
      tiles[row + 1][col + 1] = 1
    elseif row >= 20 and row <= 21 and col >= 8 and col <= 16 then
      tiles[row + 1][col + 1] = 1
    elseif row >= 17 and row <= 18 and col >= 22 and col <= 28 then
      tiles[row + 1][col + 1] = 1
    elseif row >= 14 and row <= 15 and col >= 36 and col <= 42 then
      tiles[row + 1][col + 1] = 1
    elseif row >= 11 and row <= 12 and col >= 48 and col <= 54 then
      tiles[row + 1][col + 1] = 1
    elseif row >= 8 and row <= 9 and col >= 58 and col <= 64 then
      tiles[row + 1][col + 1] = 1
    elseif row >= 5 and row <= 6 and col >= 50 and col <= 58 then
      tiles[row + 1][col + 1] = 2
    elseif row >= 2 and row <= 3 and col >= 20 and col <= 30 then
      tiles[row + 1][col + 1] = 2
    elseif row == 22 and col >= 18 and col <= 20 then
      tiles[row + 1][col + 1] = 0
    elseif row == 22 and col >= 30 and col <= 32 then
      tiles[row + 1][col + 1] = 0
    elseif row == 22 and col >= 44 and col <= 46 then
      tiles[row + 1][col + 1] = 0
    elseif row == 22 and col >= 56 and col <= 58 then
      tiles[row + 1][col + 1] = 0
    elseif row >= 18 and row <= 19 and col >= 16 and col <= 18 then
      tiles[row + 1][col + 1] = 5
    elseif row >= 16 and row <= 17 and col >= 30 and col <= 32 then
      tiles[row + 1][col + 1] = 5
    elseif row >= 10 and row <= 11 and col >= 56 and col <= 58 then
      tiles[row + 1][col + 1] = 5
    elseif row == 4 and col >= 32 and col <= 34 then
      tiles[row + 1][col + 1] = 5
    else
      tiles[row + 1][col + 1] = 0
    end
  end
end

return {
  id = '5-3',
  name = 'Krazy Korridor',
  width = W,
  height = H,
  tile_size = 16,
  player_spawn = { x = 80, y = 128 },
  camera = { bound_x = 1280, bound_y = 384 },
  parallax = {
    bg = 0.06,
    far = 0.22,
    mid = 0.48,
  },
  tiles = tiles,
  objects = {
    { type = 'banana', x = 180, y = 320 },
    { type = 'banana_bunch', x = 380, y = 240 },
    { type = 'banana_bunch', x = 750, y = 176 },
    { type = 'kritter', x = 250, y = 176 },
    { type = 'klamp', x = 500, y = 144 },
    { type = 'klobber', x = 600, y = 288 },
    { type = 'zinger', x = 400, y = 336, params = { patrol_min = 340, patrol_max = 460 } },
    { type = 'zinger', x = 800, y = 240, params = { patrol_min = 740, patrol_max = 860 } },
    { type = 'flitter', x = 920, y = 320, params = { patrol_min = 860, patrol_max = 980 } },
    { type = 'krusha', x = 700, y = 128 },
    { type = 'dk_coin', x = 1050, y = 192 },
    { type = 'life_balloon', x = 900, y = 112 },
    { type = 'barrel', x = 550, y = 256 },
    { type = 'bonus_barrel', x = 1100, y = 288 },
  },
}
