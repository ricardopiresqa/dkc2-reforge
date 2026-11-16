local W, H = 80, 24
local tiles = {}
for row = 0, H - 1 do
  tiles[row + 1] = {}
  for col = 0, W - 1 do
    if row == H - 1 then
      tiles[row + 1][col + 1] = 1
    elseif col == 0 or col == W - 1 then
      tiles[row + 1][col + 1] = 1
    elseif row >= 22 and col >= 4 and col <= 10 then
      tiles[row + 1][col + 1] = 1
    elseif row >= 20 and row <= 21 and col >= 14 and col <= 20 then
      tiles[row + 1][col + 1] = 1
    elseif row >= 22 and col >= 24 and col <= 30 then
      tiles[row + 1][col + 1] = 1
    elseif row >= 20 and row <= 21 and col >= 34 and col <= 40 then
      tiles[row + 1][col + 1] = 1
    elseif row >= 22 and col >= 44 and col <= 50 then
      tiles[row + 1][col + 1] = 1
    elseif row >= 20 and row <= 21 and col >= 54 and col <= 60 then
      tiles[row + 1][col + 1] = 1
    elseif row >= 22 and col >= 64 and col <= 70 then
      tiles[row + 1][col + 1] = 1
    elseif row >= 20 and row <= 21 and col >= 74 and col <= 78 then
      tiles[row + 1][col + 1] = 1
    elseif row >= 17 and row <= 18 and col >= 8 and col <= 10 then
      tiles[row + 1][col + 1] = 2
    elseif row >= 14 and row <= 15 and col >= 18 and col <= 20 then
      tiles[row + 1][col + 1] = 2
    elseif row >= 11 and row <= 12 and col >= 28 and col <= 30 then
      tiles[row + 1][col + 1] = 2
    elseif row >= 8 and row <= 9 and col >= 38 and col <= 40 then
      tiles[row + 1][col + 1] = 2
    elseif row >= 5 and row <= 6 and col >= 48 and col <= 50 then
      tiles[row + 1][col + 1] = 2
    elseif row >= 2 and row <= 3 and col >= 58 and col <= 60 then
      tiles[row + 1][col + 1] = 2
    elseif row >= 1 and row <= 2 and col >= 68 and col <= 72 then
      tiles[row + 1][col + 1] = 2
    elseif row == 22 and col >= 12 and col <= 14 then
      tiles[row + 1][col + 1] = 0
    elseif row == 22 and col >= 32 and col <= 34 then
      tiles[row + 1][col + 1] = 0
    elseif row == 22 and col >= 52 and col <= 54 then
      tiles[row + 1][col + 1] = 0
    elseif row == 22 and col >= 72 and col <= 74 then
      tiles[row + 1][col + 1] = 0
    elseif row >= 14 and row <= 19 and col >= 12 and col <= 14 then
      tiles[row + 1][col + 1] = 5
    elseif row >= 8 and row <= 13 and col >= 22 and col <= 24 then
      tiles[row + 1][col + 1] = 5
    elseif row >= 2 and row <= 7 and col >= 32 and col <= 34 then
      tiles[row + 1][col + 1] = 5
    else
      tiles[row + 1][col + 1] = 0
    end
  end
end

return {
  id = '6-4',
  name = "Towering Trouble",
  width = W, height = H, tile_size = 16,
  player_spawn = { x = 80, y = 128 },
  camera = { bound_x = 1280, bound_y = 384 },
  parallax = { bg = 0.05, far = 0.2, mid = 0.45 },
  tiles = tiles,
  objects = {
    { type = 'banana', x = 80, y = 320 }, { type = 'banana', x = 100, y = 320 },
    { type = 'banana_bunch', x = 200, y = 240 },
    { type = 'banana_bunch', x = 600, y = 176 },
    { type = 'kritter', x = 180, y = 192 }, { type = 'kritter', x = 200, y = 192 },
    { type = 'klamp', x = 350, y = 160 },
    { type = 'zinger', x = 300, y = 240, params = { patrol_min = 260, patrol_max = 380 } },
    { type = 'zinger', x = 480, y = 128, params = { patrol_min = 420, patrol_max = 540 } },
    { type = 'klobber', x = 420, y = 304 },
    { type = 'flitter', x = 550, y = 176, params = { patrol_min = 500, patrol_max = 620 } },
    { type = 'kopter', x = 680, y = 208, params = { patrol_min = 640, patrol_max = 740 } },
    { type = 'krusha', x = 780, y = 128 },
    { type = 'zinger', x = 880, y = 288, params = { patrol_min = 840, patrol_max = 940 } },
    { type = 'kritter', x = 1020, y = 304 },
    { type = 'dk_coin', x = 450, y = 256 },
    { type = 'life_balloon', x = 300, y = 128 },
    { type = 'barrel', x = 250, y = 288 }, { type = 'barrel', x = 650, y = 240 },
    { type = 'bonus_barrel', x = 750, y = 352 },
  },
}
