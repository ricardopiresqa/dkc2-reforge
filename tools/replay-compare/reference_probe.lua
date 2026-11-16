-- Proves only that the headless reference can load a Lua script.
emu.log("REFERENCE_SCRIPT_LOADED")
local stop = emu.exit or emu.stop
stop(0)
