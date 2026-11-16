local W, H = 80, 24
local tiles = {}
for row = 0, H - 1 do
  tiles[row + 1] = {}
  for col = 0, W - 1 do
    if row == H - 1 then
      tiles[row + 1][col + 1] = 1
    elseif col == 0 or col == W - 1 then
      tiles[row + 1][col + 1] = 1
    elseif row >= 22 and col >= 4 and col <= 14 then
      tiles[row + 1][col + 1] = 1
    elseif row >= 21 and col >= 18 and col <= 28 then
      tiles[row + 1][col + 1] = 1
    elseif row >= 22 and col >= 32 and col <= 42 then
      tiles[row + 1][col + 1] = 1
    elseif row >= 20 and row <= 21 and col >= 46 and col <= 56 then
      tiles[row + 1][col + 1] = 1
    elseif row >= 22 and col >= 60 and col <= 70 then
      tiles[row + 1][col + 1] = 1
    elseif row >= 20 and row <= 21 and col >= 74 and col <= 78 then
      tiles[row + 1][col + 1] = 1
    elseif row >= 16 and row <= 17 and col >= 8 and col <= 12 then
      tiles[row + 1][col + 1] = 2
    elseif row >= 12 and row <= 13 and col >= 22 and col <= 26 then
      tiles[row + 1][col + 1] = 2
    elseif row >= 8 and row <= 9 and col >= 36 and col <= 40 then
      tiles[row + 1][col + 1] = 2
    elseif row >= 4 and row <= 5 and col >= 50 and col <= 54 then
      tiles[row + 1][col + 1] = 2
    elseif row >= 14 and row <= 18 and col >= 42 and col <= 44 then
      tiles[row + 1][col + 1] = 0
    elseif row >= 8 and row <= 12 and col >= 56 and col <= 58 then
      tiles[row + 1][col + 1] = 0
    elseif row >= 2 and row <= 6 and col >= 70 and col <= 72 then
      tiles[row + 1][col + 1] = 0
    elseif row >= 20 and col >= 30 and col <= 32 then
      tiles[row + 1][col + 1] = 5
    elseif row >= 14 and row <= 15 and col >= 14 and col <= 16 then
      tiles[row + 1][col + 1] = 5
    elseif row >= 8 and row <= 9 and col >= 28 and col <= 30 then
      tiles[row + 1][col + 1] = 5
    elseif row >= 2 and row <= 3 and col >= 44 and col <= 46 then
      tiles[row + 1][col + 1] = 5
    elseif row >= 22 and col >= 44 and col <= 46 then
      tiles[row + 1][col + 1] = 3
    else
      tiles[row + 1][col + 1] = 0
    end
  end
end

return {
  id = '6-3',
  name = "Cavern of Chaos",
  width = W, height = H, tile_size = 16,
  player_spawn = { x = 80, y = 128 },
  camera = { bound_x = 1280, bound_y = 384 },
  parallax = { bg = 0.05, far = 0.2, mid = 0.45 },
  tiles = tiles,
  objects = {
    { type = 'banana', x = 100, y = 320 }, { type = 'banana', x = 120, y = 320 },
    { type = 'banana_bunch', x = 280, y = 200 },
    { type = 'banana_bunch', x = 800, y = 160 },
    { type = 'kritter', x = 180, y = 192 },
    { type = 'klamp', x = 300, y = 160 }, { type = 'klamp', x = 320, y = 160 },
    { type = 'zinger', x = 400, y = 240, params = { patrol_min = 340, patrol_max = 460 } },
    { type = 'zinger', x = 550, y = 128, params = { patrol_min = 500, patrol_max = 620 } },
    { type = 'klobber', x = 480, y = 304 },
    { type = 'flitter', x = 650, y = 176, params = { patrol_min = 580, patrol_max = 700 } },
    { type = 'kopter', x = 750, y = 208, params = { patrol_min = 700, patrol_max = 800 } },
    { type = 'krusha', x = 880, y = 128 },
    { type = 'kritter', x = 950, y = 304 }, { type = 'kritter', x = 970, y = 304 },
    { type = 'zinger', x = 1050, y = 176, params = { patrol_min = 1000, patrol_max = 1100 } },
    { type = 'dk_coin', x = 600, y = 256 },
    { type = 'life_balloon', x = 350, y = 240 },
    { type = 'barrel', x = 220, y = 240 }, { type = 'barrel', x = 700, y = 288 },
    { type = 'bonus_barrel', x = 920, y = 352 },
  },
}
