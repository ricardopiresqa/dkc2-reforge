local input = require("main.input")
local M = {}

function M.run()
  -- Defold delivers on_input before update: exercise that exact order.
  input.set_synthetic(nil)
  input.on_input(hash("b"), { pressed = true })
  input.update()
  input.post_update()
  assert(input.hold_bit(input.BIT.B) and input.edge_bit(input.BIT.B), "manual jump edge lost")
  input.update()
  input.post_update()
  assert(input.hold_bit(input.BIT.B) and not input.edge_bit(input.BIT.B), "held jump repeated edge")
  input.on_input(hash("b"), { released = true })
  input.update()
  input.post_update()
  assert(not input.hold_bit(input.BIT.B), "jump release lost")
  input.set_synthetic(1)
  input.update()
  input.post_update()
  assert(input.edge_bit(input.BIT.B), "synthetic edge lost")
  input.set_synthetic(0)
  input.update()
  input.post_update()
  input.set_synthetic(nil)
  return true
end

return M
