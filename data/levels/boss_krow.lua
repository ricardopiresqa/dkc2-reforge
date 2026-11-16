local W, H = 20, 24
local tiles = {}
for row = 0, H - 1 do
  tiles[row + 1] = {}
  for col = 0, W - 1 do
    if row == H - 1 then
      tiles[row + 1][col + 1] = 1
    elseif col == 0 or col == W - 1 then
      tiles[row + 1][col + 1] = 1
    elseif row == 17 and col >= 6 and col <= 13 then
      tiles[row + 1][col + 1] = 1
    elseif row == 12 and col >= 3 and col <= 16 then
      tiles[row + 1][col + 1] = 2
    elseif row == 8 and col >= 6 and col <= 13 then
      tiles[row + 1][col + 1] = 2
    elseif row == 5 and col >= 8 and col <= 11 then
      tiles[row + 1][col + 1] = 2
    elseif row == 13 and col >= 0 and col <= 2 then
      tiles[row + 1][col + 1] = 1
    elseif row == 4 and col >= 0 and col <= 2 then
      tiles[row + 1][col + 1] = 1
    elseif row == 4 and col >= 17 and col <= 19 then
      tiles[row + 1][col + 1] = 1
    else
      tiles[row + 1][col + 1] = 0
    end
  end
end

return {
  id = 'boss_krow',
  name = "Krow's Nest",
  width = W,
  height = H,
  tile_size = 16,
  player_spawn = { x = 160, y = 320 },
  camera = { bound_x = 320, bound_y = 384 },
  is_boss = true,
  parallax = {
    bg = 0.1,
    far = 0.3,
    mid = 0.5,
  },
  tiles = tiles,
  objects = {
    { type = 'banana', x = 120, y = 448 },
    { type = 'banana', x = 140, y = 448 },
    { type = 'banana', x = 180, y = 448 },
    { type = 'banana', x = 200, y = 448 },
    { type = 'life_balloon', x = 160, y = 80 },
    { type = 'banana_bunch', x = 72, y = 240 },
    { type = 'banana_bunch', x = 248, y = 240 },
    { type = 'barrel', x = 80, y = 288 },
    { type = 'barrel', x = 240, y = 288 },
  },
}
