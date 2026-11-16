local W, H = 80, 24
local tiles = {}
for row = 0, H - 1 do
  tiles[row + 1] = {}
  for col = 0, W - 1 do
    if row == 0 or row == H - 1 then
      tiles[row + 1][col + 1] = 1
    elseif col == 0 or col == W - 1 then
      tiles[row + 1][col + 1] = 1
    elseif row >= 19 and row <= 20 and col >= 14 and col <= 18 then
      tiles[row + 1][col + 1] = 5
    elseif row >= 19 and row <= 20 and col >= 38 and col <= 44 then
      tiles[row + 1][col + 1] = 5
    elseif row >= 19 and row <= 20 and col >= 60 and col <= 64 then
      tiles[row + 1][col + 1] = 5
    elseif row >= 21 and row <= 22 then
      if (col >= 20 and col <= 22) or (col >= 50 and col <= 52) or (col >= 68 and col <= 70) then
        tiles[row + 1][col + 1] = 0
      else
        tiles[row + 1][col + 1] = 1
      end
    elseif row == 16 and col >= 10 and col <= 15 then
      tiles[row + 1][col + 1] = 2
    elseif row == 13 and col >= 25 and col <= 29 then
      tiles[row + 1][col + 1] = 2
    elseif row == 10 and col >= 42 and col <= 46 then
      tiles[row + 1][col + 1] = 2
    elseif row == 7 and col >= 55 and col <= 60 then
      tiles[row + 1][col + 1] = 2
    elseif row == 5 and col >= 20 and col <= 24 then
      tiles[row + 1][col + 1] = 2
    elseif row == 17 and col >= 35 and col <= 37 then
      tiles[row + 1][col + 1] = 3
    elseif col >= 8 and col <= 11 and row >= 14 and row <= 18 then
      tiles[row + 1][col + 1] = 1
    elseif col >= 65 and col <= 68 and row >= 14 and row <= 18 then
      tiles[row + 1][col + 1] = 1
    else
      tiles[row + 1][col + 1] = 0
    end
  end
end

return {
  id = 'forest',
  name = 'Kremwood Forest',
  width = W,
  height = H,
  tile_size = 16,
  player_spawn = { x = 64, y = 128 },
  camera = { bound_x = 1280, bound_y = 384 },
  parallax = {
    bg = 0.15,
    far = 0.4,
    mid = 0.7,
  },
  tiles = tiles,
  objects = {
    { type = 'banana', x = 120, y = 192 },
    { type = 'banana', x = 152, y = 192 },
    { type = 'banana', x = 320, y = 240 },
    { type = 'banana', x = 352, y = 240 },
    { type = 'banana_bunch', x = 200, y = 256 },
    { type = 'banana_bunch', x = 400, y = 240 },
    { type = 'kritter', x = 280, y = 225 },
    { type = 'kritter', x = 500, y = 225 },
    { type = 'kritter', x = 700, y = 225 },
    { type = 'zinger', x = 600, y = 320, params = { patrol_min = 540, patrol_max = 660 } },
    { type = 'zinger', x = 800, y = 256, params = { patrol_min = 740, patrol_max = 860 } },
    { type = 'dk_coin', x = 850, y = 200 },
    { type = 'life_balloon', x = 950, y = 192 },
    { type = 'barrel', x = 150, y = 225 },
    { type = 'rambi', x = 500, y = 320 },
  },
}
