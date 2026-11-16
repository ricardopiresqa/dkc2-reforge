local W, H = 20, 24
local tiles = {}
for row = 0, H - 1 do
  tiles[row + 1] = {}
  for col = 0, W - 1 do
    if row == H - 1 then
      tiles[row + 1][col + 1] = 1
    elseif col == 0 or col == W - 1 then
      tiles[row + 1][col + 1] = 1
    elseif row == 20 and col >= 4 and col <= 15 then
      tiles[row + 1][col + 1] = 1
    elseif row == 15 and col >= 2 and col <= 17 then
      tiles[row + 1][col + 1] = 2
    elseif row == 11 and col >= 5 and col <= 14 then
      tiles[row + 1][col + 1] = 2
    elseif row == 7 and col >= 7 and col <= 12 then
      tiles[row + 1][col + 1] = 2
    elseif row == 3 and col >= 8 and col <= 11 then
      tiles[row + 1][col + 1] = 2
    elseif row >= 19 and row <= 20 and col >= 10 and col <= 13 then
      tiles[row + 1][col + 1] = 5
    else
      tiles[row + 1][col + 1] = 0
    end
  end
end

return {
  id = 'boss_zing',
  name = "King Zing's Hive",
  width = W,
  height = H,
  tile_size = 16,
  player_spawn = { x = 160, y = 320 },
  camera = { bound_x = 320, bound_y = 384 },
  is_boss = true,
  parallax = {
    bg = 0.15,
    far = 0.35,
    mid = 0.55,
  },
  tiles = tiles,
  objects = {
    { type = 'banana', x = 80, y = 240 },
    { type = 'banana', x = 100, y = 240 },
    { type = 'banana', x = 220, y = 240 },
    { type = 'banana', x = 240, y = 240 },
    { type = 'banana_bunch', x = 160, y = 48 },
    { type = 'life_balloon', x = 160, y = 280 },
    { type = 'barrel', x = 60, y = 280 },
    { type = 'barrel', x = 260, y = 280 },
  },
}
