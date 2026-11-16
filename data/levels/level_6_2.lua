local W, H = 80, 24
local tiles = {}
for row = 0, H - 1 do
  tiles[row + 1] = {}
  for col = 0, W - 1 do
    if row == H - 1 then
      tiles[row + 1][col + 1] = 1
    elseif col == 0 or col == W - 1 then
      tiles[row + 1][col + 1] = 1
    elseif row >= 22 and col >= 6 and col <= 16 then
      tiles[row + 1][col + 1] = 1
    elseif row >= 21 and col >= 22 and col <= 32 then
      tiles[row + 1][col + 1] = 3
    elseif row >= 22 and col >= 38 and col <= 48 then
      tiles[row + 1][col + 1] = 1
    elseif row >= 21 and col >= 54 and col <= 64 then
      tiles[row + 1][col + 1] = 3
    elseif row >= 22 and col >= 70 and col <= 78 then
      tiles[row + 1][col + 1] = 1
    elseif row >= 18 and row <= 19 and col >= 10 and col <= 14 then
      tiles[row + 1][col + 1] = 2
    elseif row >= 14 and row <= 15 and col >= 28 and col <= 32 then
      tiles[row + 1][col + 1] = 2
    elseif row >= 12 and col >= 38 and col <= 42 then
      tiles[row + 1][col + 1] = 2
    elseif row >= 8 and row <= 9 and col >= 56 and col <= 60 then
      tiles[row + 1][col + 1] = 2
    elseif row >= 4 and row <= 5 and col >= 72 and col <= 76 then
      tiles[row + 1][col + 1] = 2
    elseif row >= 6 and row <= 10 and col >= 16 and col <= 18 then
      tiles[row + 1][col + 1] = 3
    elseif row >= 6 and row <= 12 and col >= 46 and col <= 48 then
      tiles[row + 1][col + 1] = 3
    elseif row >= 1 and row <= 3 and col >= 62 and col <= 64 then
      tiles[row + 1][col + 1] = 3
    elseif row >= 18 and row <= 20 and col >= 50 and col <= 52 then
      tiles[row + 1][col + 1] = 5
    elseif row >= 14 and row <= 16 and col >= 18 and col <= 20 then
      tiles[row + 1][col + 1] = 5
    elseif row >= 8 and row <= 10 and col >= 34 and col <= 36 then
      tiles[row + 1][col + 1] = 5
    elseif row >= 2 and row <= 4 and col >= 68 and col <= 70 then
      tiles[row + 1][col + 1] = 5
    else
      tiles[row + 1][col + 1] = 0
    end
  end
end

return {
  id = '6-2',
  name = "Abyssal Abyss",
  width = W, height = H, tile_size = 16,
  player_spawn = { x = 80, y = 128 },
  camera = { bound_x = 1280, bound_y = 384 },
  parallax = { bg = 0.05, far = 0.2, mid = 0.45 },
  tiles = tiles,
  objects = {
    { type = 'banana', x = 160, y = 320 }, { type = 'banana', x = 180, y = 320 },
    { type = 'banana_bunch', x = 240, y = 200 },
    { type = 'zinger', x = 200, y = 128, params = { patrol_min = 160, patrol_max = 280 } },
    { type = 'kritter', x = 400, y = 304 },
    { type = 'klamp', x = 350, y = 160 },
    { type = 'zinger', x = 500, y = 240, params = { patrol_min = 440, patrol_max = 560 } },
    { type = 'klobber', x = 450, y = 304 },
    { type = 'flitter', x = 600, y = 176, params = { patrol_min = 540, patrol_max = 660 } },
    { type = 'kopter', x = 700, y = 208, params = { patrol_min = 660, patrol_max = 760 } },
    { type = 'krusha', x = 800, y = 128 },
    { type = 'zinger', x = 900, y = 160, params = { patrol_min = 860, patrol_max = 960 } },
    { type = 'kritter', x = 1000, y = 304 }, { type = 'kritter', x = 1020, y = 304 },
    { type = 'dk_coin', x = 750, y = 256 },
    { type = 'life_balloon', x = 1150, y = 160 },
    { type = 'barrel', x = 300, y = 288 }, { type = 'barrel', x = 650, y = 240 },
    { type = 'bonus_barrel', x = 520, y = 352 },
  },
}
