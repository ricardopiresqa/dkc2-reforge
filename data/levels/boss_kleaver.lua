local W, H = 20, 24
local tiles = {}
for row = 0, H - 1 do
  tiles[row + 1] = {}
  for col = 0, W - 1 do
    if row == H - 1 then
      tiles[row + 1][col + 1] = 1
    elseif col == 0 or col == W - 1 then
      tiles[row + 1][col + 1] = 1
    elseif row == 18 and col >= 4 and col <= 15 then
      tiles[row + 1][col + 1] = 1
    elseif row == 13 and col >= 2 and col <= 17 then
      tiles[row + 1][col + 1] = 2
    elseif row == 9 and col >= 6 and col <= 13 then
      tiles[row + 1][col + 1] = 2
    elseif row == 5 and col >= 8 and col <= 11 then
      tiles[row + 1][col + 1] = 2
    elseif row >= 19 and row <= 20 and col >= 8 and col <= 11 then
      tiles[row + 1][col + 1] = 0
    else
      tiles[row + 1][col + 1] = 0
    end
  end
end

return {
  id = 'boss_kleaver',
  name = "Kleaver's Airship",
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
    { type = 'banana', x = 80, y = 160 },
    { type = 'banana', x = 100, y = 160 },
    { type = 'banana', x = 220, y = 160 },
    { type = 'banana', x = 240, y = 160 },
    { type = 'banana_bunch', x = 160, y = 80 },
    { type = 'life_balloon', x = 160, y = 300 },
    { type = 'barrel', x = 60, y = 240 },
    { type = 'barrel', x = 260, y = 240 },
  },
}
