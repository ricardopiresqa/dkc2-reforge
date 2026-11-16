local M = {}

M.registry = {}

function M.register(name, module)
  M.registry[name] = module
end

function M.get(name)
  return M.registry[name]
end

M.registry.squitter = require("main.animals.squitter")
M.registry.rattly = require("main.animals.rattly")
M.registry.squawks = require("main.animals.squawks")
M.registry.expresso = require("main.animals.expresso")

return M
