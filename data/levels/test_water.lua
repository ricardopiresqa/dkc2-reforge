local W, H = 40, 20
local tiles = {}
for row = 0, H - 1 do
  tiles[row + 1] = {}
  for col = 0, W - 1 do
    if row == 0 or row == H - 1 then
      tiles[row + 1][col + 1] = 1
    elseif col == 0 or col == W - 1 then
      tiles[row + 1][col + 1] = 1
    elseif row >= 8 and row <= 17 and col >= 11 and col <= 28 then
      tiles[row + 1][col + 1] = 5
    elseif row >= 8 then
      tiles[row + 1][col + 1] = 1
    else
      tiles[row + 1][col + 1] = 0
    end
  end
end

return {
  id = "test_water",
  name = "Water Test",
  width = W,
  height = H,
  tile_size = 16,
  player_spawn = { x = 64, y = 96 },
  camera = { bound_x = 640, bound_y = 320 },
  parallax = {
    bg = 0.25,
    far = 0.5,
    mid = 0.75,
  },
  tiles = tiles,
  objects = {
    { type = "banana", x = 80, y = 160 },
    { type = "banana", x = 112, y = 160 },
    { type = "banana", x = 144, y = 160 },
    { type = "banana", x = 200, y = 128 },
    { type = "banana", x = 232, y = 128 },
    { type = "banana_bunch", x = 280, y = 256 },
    { type = "rambi", x = 120, y = 136 },
    { type = "enguarde", x = 320, y = 248 },
    { type = "kritter", x = 576, y = 144 },
    { type = "zinger", x = 400, y = 192, params = { patrol_min = 340, patrol_max = 460 } },
  },
}
