local W, H = 80, 24
local tiles = {}
for row = 0, H - 1 do
  tiles[row + 1] = {}
  for col = 0, W - 1 do
    if row == H - 1 then
      tiles[row + 1][col + 1] = 1
    elseif col == 0 or col == W - 1 then
      tiles[row + 1][col + 1] = 1
    elseif row == 18 and col >= 6 and col <= 10 then
      tiles[row + 1][col + 1] = 2
    elseif row == 15 and col >= 20 and col <= 24 then
      tiles[row + 1][col + 1] = 2
    elseif row == 12 and col >= 36 and col <= 40 then
      tiles[row + 1][col + 1] = 2
    elseif row == 9 and col >= 52 and col <= 56 then
      tiles[row + 1][col + 1] = 2
    elseif row == 6 and col >= 66 and col <= 70 then
      tiles[row + 1][col + 1] = 2
    elseif row >= 20 and row <= 21 and col >= 14 and col <= 16 then
      tiles[row + 1][col + 1] = 5
    elseif row >= 20 and row <= 21 and col >= 28 and col <= 30 then
      tiles[row + 1][col + 1] = 5
    elseif row >= 20 and row <= 21 and col >= 44 and col <= 46 then
      tiles[row + 1][col + 1] = 5
    elseif row == 22 and col >= 20 and col <= 22 then
      tiles[row + 1][col + 1] = 0
    elseif row == 22 and col >= 50 and col <= 52 then
      tiles[row + 1][col + 1] = 0
    elseif row == 19 and col >= 30 and col <= 32 then
      tiles[row + 1][col + 1] = 3
    elseif row == 21 and col >= 58 and col <= 60 then
      tiles[row + 1][col + 1] = 4
    elseif row >= 21 and row <= 22 and col >= 72 and col <= 74 then
      tiles[row + 1][col + 1] = 1
    else
      tiles[row + 1][col + 1] = 0
    end
  end
end

return {
  id = '2-3',
  name = 'Kremtown Part 2',
  width = W,
  height = H,
  tile_size = 16,
  player_spawn = { x = 80, y = 128 },
  camera = { bound_x = 1280, bound_y = 384 },
  parallax = {
    bg = 0.15,
    far = 0.4,
    mid = 0.7,
  },
  tiles = tiles,
  objects = {
    { type = 'banana', x = 130, y = 256 },
    { type = 'banana', x = 160, y = 256 },
    { type = 'banana_bunch', x = 350, y = 320 },
    { type = 'banana_bunch', x = 600, y = 192 },
    { type = 'kritter', x = 300, y = 225 },
    { type = 'klamp', x = 500, y = 225 },
    { type = 'krusha', x = 700, y = 225 },
    { type = 'zinger', x = 420, y = 280, params = { patrol_min = 360, patrol_max = 480 } },
    { type = 'flitter', x = 800, y = 300, params = { patrol_min = 740, patrol_max = 860 } },
    { type = 'dk_coin', x = 1000, y = 180 },
    { type = 'life_balloon', x = 1100, y = 160 },
    { type = 'barrel', x = 250, y = 225 },
    { type = 'bonus_barrel', x = 900, y = 128 },
    { type = 'letter_k', x = 180, y = 280 },
    { type = 'letter_o', x = 450, y = 220 },
    { type = 'letter_n', x = 650, y = 260 },
    { type = 'letter_g', x = 950, y = 200 },
  },
}
