-- ShipDeck BG2 (sky/sea) per-scanline H-scroll: byte-exact port of 80E540 over
-- the HDMA channel-1 table at $7E8012 initialised by BBA655. State persists across
-- frames like WRAM (some line bytes only ever receive the wave INCs).
-- Screen rows: 0-23, 24-47, 48-103 sky bands; 104+k sea line k (repeat block).
local M = {}

local BASE = 0x8000
local mem = {}

local function w16(address, value)
  value = value % 65536
  mem[address - BASE] = value % 256
  mem[address - BASE + 1] = math.floor(value / 256)
end

local function r16(address)
  return mem[address - BASE] + mem[address - BASE + 1] * 256
end

function M.init()
  for index = 0, 0x13F do mem[index] = 0 end
  -- BBA655: counts $18/$18/$38, repeat block $FF with first line word 1.
  w16(0x8012, 0x18); w16(0x8013, 0); w16(0x8015, 0x18); w16(0x8016, 0)
  w16(0x8018, 0x38); w16(0x8019, 0); w16(0x801B, 0xFF); w16(0x801C, 1)
end

--- One 80E540 pass. l1x = layer-1 pixel X ($17BA), clock = $2A.
function M.update(l1x, clock)
  local value = math.floor(clock / 2)
  w16(0x8013, value)
  value = math.floor(value / 2)
  w16(0x8016, value)
  w16(0x8019, math.floor(value / 4))
  local s = (l1x + clock) % 65536
  local sum = (math.floor(s / 4) + math.floor(s / 2) + s) % 65536
  local carry = sum >= 0x2000 and 1 or 0           -- SEC ; SBC #$2000
  local step = 65535 - ((sum - 0x2000) % 65536)     -- EOR #$FFFF
  local acc = (s % 256) * 256                       -- LDA $35 ; AND #$FF00
  local x = 0x100
  while true do
    for address = 0x802D, 0x801F, -2 do
      w16(address + x, acc)
      local total = acc + step + carry
      carry = total >= 65536 and 1 or 0
      acc = total % 65536
    end
    x = x - 0x10
    carry = 1                                       -- CPX #$0000 always sets C
    if x < 0 then break end
  end
  -- 80E5C2/80E5E7 wave INCs: TAX at loop head keeps the last non-negative X.
  x = (math.floor(clock / 2) % 16 - math.floor(clock / 2) % 2) + 0x90
  while true do
    for _, pair in ipairs({ { 0x807E, 1 }, { 0x8080, 1 }, { 0x8082, 2 }, { 0x8084, 2 },
                            { 0x8086, 1 }, { 0x8088, 1 } }) do
      for _ = 1, pair[2] do w16(pair[1] + x, r16(pair[1] + x) + 1) end
    end
    if x - 0x10 < 0 then break end
    x = x - 0x10
  end
  x = x + 0x50
  while true do
    for address = 0x801E, 0x8024, 2 do w16(address + x, r16(address + x) + 1) end
    if x - 0x10 < 0 then break end
    x = x - 0x10
  end
end

--- BG2 H-scroll (mod 256; the 32x32 BG2 map wraps at 256 px) for screen row y.
function M.line_h(y)
  if y < 24 then return r16(0x8013) % 256 end
  if y < 48 then return r16(0x8016) % 256 end
  if y < 104 then return r16(0x8019) % 256 end
  return r16(0x801C + 2 * (y - 104)) % 256
end

function M.word(address) return r16(address) end

M.init()
return M
