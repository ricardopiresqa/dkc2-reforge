-- Mesen headless smoke only. Does not claim that Pirate Panic was played.
local frames = 0
emu.addEventCallback(function()
  frames = frames + 1
  if frames >= 120 then
    emu.log("REFERENCE_SMOKE_120_FRAMES")
    local stop = emu.exit or emu.stop
    stop(0)
  end
end, emu.eventType.endFrame)
