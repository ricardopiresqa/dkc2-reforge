local W, H = 80, 24
local tiles = {}
for row = 0, H - 1 do
  tiles[row + 1] = {}
  for col = 0, W - 1 do
    if row == H - 1 then
      tiles[row + 1][col + 1] = 1
    elseif col == 0 or col == W - 1 then
      tiles[row + 1][col + 1] = 1
    elseif row == 18 and col >= 6 and col <= 12 then
      tiles[row + 1][col + 1] = 2
    elseif row == 15 and col >= 20 and col <= 26 then
      tiles[row + 1][col + 1] = 2
    elseif row == 13 and col >= 38 and col <= 44 then
      tiles[row + 1][col + 1] = 2
    elseif row == 20 and col >= 50 and col <= 56 then
      tiles[row + 1][col + 1] = 2
    elseif row == 10 and col >= 56 and col <= 62 then
      tiles[row + 1][col + 1] = 2
    elseif row == 7 and col >= 30 and col <= 36 then
      tiles[row + 1][col + 1] = 2
    elseif row >= 16 and row <= 17 and col >= 12 and col <= 16 then
      tiles[row + 1][col + 1] = 5
    elseif row >= 14 and row <= 15 and col >= 50 and col <= 54 then
      tiles[row + 1][col + 1] = 5
    elseif row >= 18 and row <= 19 and col >= 34 and col <= 38 then
      tiles[row + 1][col + 1] = 5
    elseif row >= 20 and row <= 22 and col >= 40 and col <= 42 then
      tiles[row + 1][col + 1] = 1
    elseif row >= 5 and row <= 6 and col >= 18 and col <= 20 then
      tiles[row + 1][col + 1] = 6
    elseif row == 10 and col >= 6 and col <= 8 then
      tiles[row + 1][col + 1] = 3
    elseif row == 21 and col >= 46 and col <= 48 then
      tiles[row + 1][col + 1] = 0
    else
      tiles[row + 1][col + 1] = 0
    end
  end
end

return {
  id = '2-2',
  name = 'Kremtown',
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
    { type = 'banana', x = 150, y = 192 },
    { type = 'banana', x = 180, y = 192 },
    { type = 'banana', x = 300, y = 256 },
    { type = 'banana_bunch', x = 420, y = 320 },
    { type = 'banana_bunch', x = 650, y = 192 },
    { type = 'kritter', x = 320, y = 225 },
    { type = 'kritter', x = 520, y = 225 },
    { type = 'zinger', x = 700, y = 280, params = { patrol_min = 640, patrol_max = 780 } },
    { type = 'flitter', x = 450, y = 320, params = { patrol_min = 400, patrol_max = 500 } },
    { type = 'mininecky', x = 850, y = 240, params = { patrol_min = 780, patrol_max = 920 } },
    { type = 'dk_coin', x = 950, y = 180 },
    { type = 'life_balloon', x = 1050, y = 160 },
    { type = 'barrel', x = 250, y = 225 },
    { type = 'enguarde', x = 600, y = 340 },
    { type = 'letter_k', x = 180, y = 280 },
    { type = 'letter_o', x = 450, y = 220 },
    { type = 'letter_n', x = 650, y = 300 },
    { type = 'letter_g', x = 880, y = 240 },
  },
}
