local W, H = 80, 24
local tiles = {}
for row = 0, H - 1 do
  tiles[row + 1] = {}
  for col = 0, W - 1 do
    if row == H - 1 then
      tiles[row + 1][col + 1] = 1
    elseif col == 0 or col == W - 1 then
      tiles[row + 1][col + 1] = 1
    elseif row >= 21 and row <= 22 and col >= 10 and col <= 15 then
      tiles[row + 1][col + 1] = 4
    elseif row >= 21 and row <= 22 and col >= 30 and col <= 35 then
      tiles[row + 1][col + 1] = 4
    elseif row >= 21 and row <= 22 and col >= 55 and col <= 60 then
      tiles[row + 1][col + 1] = 4
    elseif row == 19 and col >= 6 and col <= 9 then
      tiles[row + 1][col + 1] = 2
    elseif row == 17 and col >= 18 and col <= 22 then
      tiles[row + 1][col + 1] = 2
    elseif row == 14 and col >= 32 and col <= 36 then
      tiles[row + 1][col + 1] = 2
    elseif row == 12 and col >= 48 and col <= 52 then
      tiles[row + 1][col + 1] = 2
    elseif row == 10 and col >= 62 and col <= 66 then
      tiles[row + 1][col + 1] = 2
    elseif row == 8 and col >= 40 and col <= 43 then
      tiles[row + 1][col + 1] = 2
    elseif row == 6 and col >= 20 and col <= 24 then
      tiles[row + 1][col + 1] = 2
    elseif row == 22 and col >= 40 and col <= 42 then
      tiles[row + 1][col + 1] = 0
    elseif row == 22 and col >= 58 and col <= 60 then
      tiles[row + 1][col + 1] = 0
    elseif row == 20 and col >= 42 and col <= 44 then
      tiles[row + 1][col + 1] = 3
    elseif row == 15 and col >= 50 and col <= 52 then
      tiles[row + 1][col + 1] = 3
    elseif row == 21 and col >= 26 and col <= 28 then
      tiles[row + 1][col + 1] = 5
    elseif row == 21 and col >= 46 and col <= 48 then
      tiles[row + 1][col + 1] = 5
    elseif row >= 20 and row <= 22 and col >= 68 and col <= 70 then
      tiles[row + 1][col + 1] = 1
    elseif row >= 20 and row <= 21 and col >= 12 and col <= 14 then
      tiles[row + 1][col + 1] = 1
    else
      tiles[row + 1][col + 1] = 0
    end
  end
end

return {
  id = '2-1',
  name = 'Crocodile Cauldron',
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
    { type = 'banana', x = 130, y = 320 },
    { type = 'banana', x = 160, y = 320 },
    { type = 'banana', x = 320, y = 256 },
    { type = 'banana', x = 350, y = 256 },
    { type = 'banana_bunch', x = 500, y = 320 },
    { type = 'banana_bunch', x = 700, y = 192 },
    { type = 'kritter', x = 250, y = 225 },
    { type = 'kritter', x = 450, y = 225 },
    { type = 'zinger', x = 600, y = 300, params = { patrol_min = 540, patrol_max = 660 } },
    { type = 'flitter', x = 800, y = 288, params = { patrol_min = 740, patrol_max = 860 } },
    { type = 'klamp', x = 380, y = 225 },
    { type = 'dk_coin', x = 1000, y = 200 },
    { type = 'life_balloon', x = 1100, y = 160 },
    { type = 'barrel', x = 200, y = 225 },
    { type = 'letter_k', x = 180, y = 320 },
    { type = 'letter_o', x = 400, y = 240 },
    { type = 'letter_n', x = 650, y = 260 },
    { type = 'letter_g', x = 850, y = 220 },
  },
}
