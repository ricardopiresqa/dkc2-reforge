local W, H = 20, 24
local tiles = {}
for row = 0, H - 1 do
  tiles[row + 1] = {}
  for col = 0, W - 1 do
    if row == H - 1 then
      tiles[row + 1][col + 1] = 1
    elseif col == 0 or col == W - 1 then
      tiles[row + 1][col + 1] = 1
    elseif row == 22 and col >= 4 and col <= 15 then
      tiles[row + 1][col + 1] = 1
    elseif row == 17 and col >= 2 and col <= 17 then
      tiles[row + 1][col + 1] = 2
    elseif row == 12 and col >= 4 and col <= 15 then
      tiles[row + 1][col + 1] = 2
    elseif row == 8 and col >= 6 and col <= 13 then
      tiles[row + 1][col + 1] = 2
    elseif row == 4 and col >= 8 and col <= 11 then
      tiles[row + 1][col + 1] = 2
    elseif row == 21 and col >= 10 and col <= 12 then
      tiles[row + 1][col + 1] = 0
    elseif row == 16 and col >= 10 and col <= 12 then
      tiles[row + 1][col + 1] = 0
    elseif row == 11 and col >= 10 and col <= 12 then
      tiles[row + 1][col + 1] = 0
    else
      tiles[row + 1][col + 1] = 0
    end
  end
end

return {
  id = 'boss_kreep',
  name = "Kreep's Krypt",
  width = W,
  height = H,
  tile_size = 16,
  player_spawn = { x = 160, y = 320 },
  camera = { bound_x = 320, bound_y = 384 },
  is_boss = true,
  parallax = {
    bg = 0.05,
    far = 0.2,
    mid = 0.4,
  },
  tiles = tiles,
  objects = {
    { type = 'banana', x = 80, y = 80 },
    { type = 'banana', x = 100, y = 80 },
    { type = 'banana', x = 220, y = 80 },
    { type = 'banana', x = 240, y = 80 },
    { type = 'banana_bunch', x = 160, y = 240 },
    { type = 'life_balloon', x = 160, y = 48 },
    { type = 'barrel', x = 70, y = 320 },
    { type = 'barrel', x = 250, y = 320 },
  },
}
