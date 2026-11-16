local W, H = 80, 24
local tiles = {}
for row = 0, H - 1 do
  tiles[row + 1] = {}
  for col = 0, W - 1 do
    if row == H - 1 then
      tiles[row + 1][col + 1] = 1
    elseif row == H - 2 then
      if (col >= 14 and col <= 17) or (col >= 32 and col <= 35) or (col >= 62 and col <= 65) then
        tiles[row + 1][col + 1] = 0
      else
        tiles[row + 1][col + 1] = 1
      end
    elseif row >= 19 and row <= 20 and col >= 42 and col <= 48 then
      tiles[row + 1][col + 1] = 5
    elseif row == 19 and col >= 24 and col <= 26 then
      tiles[row + 1][col + 1] = 3
    elseif row >= 18 and row <= 19 and col >= 52 and col <= 54 then
      tiles[row + 1][col + 1] = 6
    elseif row == 14 and col >= 22 and col <= 26 then
      tiles[row + 1][col + 1] = 2
    elseif row == 10 and col >= 44 and col <= 47 then
      tiles[row + 1][col + 1] = 2
    elseif row == 7 and col >= 60 and col <= 64 then
      tiles[row + 1][col + 1] = 2
    elseif row == 5 and col >= 30 and col <= 33 then
      tiles[row + 1][col + 1] = 2
    elseif col == 0 or col == W - 1 then
      tiles[row + 1][col + 1] = 1
    else
      tiles[row + 1][col + 1] = 0
    end
  end
end

return {
  id = '1-2',
  name = "Krock's Quarry",
  width = W,
  height = H,
  tile_size = 16,
  player_spawn = { x = 80, y = 128 },
  camera = { bound_x = 1280, bound_y = 384 },
  parallax = {
    bg = 0.2,
    far = 0.45,
    mid = 0.7,
  },
  tiles = tiles,
  objects = {
    { type = 'banana', x = 160, y = 192 },
    { type = 'banana', x = 192, y = 192 },
    { type = 'banana', x = 224, y = 192 },
    { type = 'banana', x = 300, y = 240 },
    { type = 'banana', x = 332, y = 240 },
    { type = 'banana_bunch', x = 380, y = 256 },
    { type = 'kritter', x = 450, y = 225 },
    { type = 'kritter', x = 720, y = 225 },
    { type = 'zinger', x = 550, y = 320, params = { patrol_min = 480, patrol_max = 620 } },
    { type = 'dk_coin', x = 900, y = 240 },
    { type = 'life_balloon', x = 1050, y = 192 },
    { type = 'barrel', x = 820, y = 225 },
    { type = 'letter_k', x = 200, y = 320 },
    { type = 'letter_o', x = 500, y = 240 },
    { type = 'letter_n', x = 680, y = 220 },
    { type = 'letter_g', x = 1000, y = 240 },
  },
}
