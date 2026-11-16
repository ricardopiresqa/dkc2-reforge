local M = {}

local SAVE_FILE = "dkc2_save.dat"
local SAVE_KEY = "save_data"

local function encode_value(v)
  if type(v) == "nil" then return "null" end
  if type(v) == "boolean" then return v and "true" or "false" end
  if type(v) == "number" then
    if v == math.floor(v) then return tostring(v) end
    return string.format("%.6f", v)
  end
  if type(v) == "string" then
    local escaped = v:gsub('\\', '\\\\'):gsub('"', '\\"'):gsub('\n', '\\n'):gsub('\r', '\\r'):gsub('\t', '\\t')
    return '"' .. escaped .. '"'
  end
  if type(v) == "table" then
    local is_array = true
    for k in pairs(v) do
      if type(k) ~= "number" or k < 1 or math.floor(k) ~= k then
        is_array = false
        break
      end
    end
    if is_array then
      local parts = {}
      for i = 1, #v do
        parts[i] = encode_value(v[i])
      end
      return "[" .. table.concat(parts, ",") .. "]"
    else
      local parts = {}
      for k, val in pairs(v) do
        parts[#parts + 1] = encode_value(k) .. ":" .. encode_value(val)
      end
      return "{" .. table.concat(parts, ",") .. "}"
    end
  end
  return "null"
end

function M.encode(t)
  return encode_value(t)
end

local function decode_value(s, pos)
  if pos > #s then return nil, pos end
  local c = s:sub(pos, pos)
  while c == ' ' or c == '\n' or c == '\r' or c == '\t' do
    pos = pos + 1
    c = s:sub(pos, pos)
  end
  if c == 'n' and s:sub(pos, pos + 3) == 'null' then
    return nil, pos + 4
  elseif c == 't' and s:sub(pos, pos + 3) == 'true' then
    return true, pos + 4
  elseif c == 'f' and s:sub(pos, pos + 4) == 'false' then
    return false, pos + 5
  elseif c == '"' then
    local end_pos = pos + 1
    local val = {}
    while end_pos <= #s do
      local ch = s:sub(end_pos, end_pos)
      if ch == '\\' then
        local next_ch = s:sub(end_pos + 1, end_pos + 1)
        if next_ch == '"' then val[#val + 1] = '"'; end_pos = end_pos + 2
        elseif next_ch == '\\' then val[#val + 1] = '\\'; end_pos = end_pos + 2
        elseif next_ch == 'n' then val[#val + 1] = '\n'; end_pos = end_pos + 2
        elseif next_ch == 'r' then val[#val + 1] = '\r'; end_pos = end_pos + 2
        elseif next_ch == 't' then val[#val + 1] = '\t'; end_pos = end_pos + 2
        else val[#val + 1] = next_ch; end_pos = end_pos + 2
        end
      elseif ch == '"' then
        end_pos = end_pos + 1
        break
      else
        val[#val + 1] = ch
        end_pos = end_pos + 1
      end
    end
    return table.concat(val), end_pos
  elseif c == '-' or (c >= '0' and c <= '9') then
    local end_pos = pos + 1
    while end_pos <= #s do
      local nc = s:sub(end_pos, end_pos)
      if (nc >= '0' and nc <= '9') or nc == '.' or nc == '-' or nc == 'e' or nc == 'E' or nc == '+' then
        end_pos = end_pos + 1
      else
        break
      end
    end
    local num_str = s:sub(pos, end_pos - 1)
    local num = tonumber(num_str)
    return num, end_pos
  elseif c == '[' then
    local result = {}
    pos = pos + 1
    c = s:sub(pos, pos)
    while c == ' ' or c == '\n' do c = s:sub(pos + 1, pos + 1) end
    if s:sub(pos, pos) == ']' then return result, pos + 1 end
    local idx = 1
    while pos <= #s do
      local val, new_pos = decode_value(s, pos)
      if val ~= nil then result[idx] = val end
      idx = idx + 1
      pos = new_pos
      c = s:sub(pos, pos)
      while c == ' ' or c == '\n' or c == '\r' or c == '\t' do
        pos = pos + 1
        c = s:sub(pos, pos)
      end
      if s:sub(pos, pos) == ']' then
        pos = pos + 1
        break
      elseif s:sub(pos, pos) == ',' then
        pos = pos + 1
      end
    end
    return result, pos
  elseif c == '{' then
    local result = {}
    pos = pos + 1
    if s:sub(pos, pos) == '}' then return result, pos + 1 end
    while pos <= #s do
      local key, new_pos = decode_value(s, pos)
      pos = new_pos
      c = s:sub(pos, pos)
      while c == ' ' or c == '\n' or c == '\r' or c == '\t' do
        pos = pos + 1
        c = s:sub(pos, pos)
      end
      if s:sub(pos, pos) == ':' then pos = pos + 1 end
      local val, new_pos2 = decode_value(s, pos)
      if key ~= nil then result[key] = val end
      pos = new_pos2
      c = s:sub(pos, pos)
      while c == ' ' or c == '\n' or c == '\r' or c == '\t' do
        pos = pos + 1
        c = s:sub(pos, pos)
      end
      if s:sub(pos, pos) == '}' then
        pos = pos + 1
        break
      elseif s:sub(pos, pos) == ',' then
        pos = pos + 1
      end
    end
    return result, pos
  end
  return nil, pos + 1
end

function M.decode(s)
  local val, _ = decode_value(s, 1)
  return val
end

local default_data = {
  levels = {},
  lives = 3,
  bananas = 0,
  dk_coins = 0,
  score = 0,
}

M.data = nil

function M.init()
  local ok, raw = pcall(sys.load, SAVE_FILE)
  if ok and raw then
    if type(raw) == "table" then
      M.data = raw
    elseif type(raw) == "string" then
      -- Keep compatibility with early JSON-string saves.
      local decoded, data = pcall(M.decode, raw)
      if decoded then M.data = data end
    end
  end
  if not M.data or type(M.data) ~= "table" then
    M.data = {}
    for k, v in pairs(default_data) do
      M.data[k] = v
    end
  end
  if not M.data.levels then M.data.levels = {} end
end

function M.save()
  -- Defold persists Lua tables natively. Passing encoded JSON string raises
  -- "table expected, got string" and silently loses deaths/progress.
  local ok, err = pcall(sys.save, SAVE_FILE, M.data)
  if not ok then
    print("Save failed: " .. tostring(err))
  end
end

function M.is_level_completed(level_id)
  if M.data.levels[level_id] then
    return M.data.levels[level_id].completed or false
  end
  return false
end

function M.has_dk_coin(level_id)
  if M.data.levels[level_id] then
    return M.data.levels[level_id].dk_coin or false
  end
  return false
end

function M.complete_level(level_id, dk_coin_collected, secret_exit)
  M.data.levels[level_id] = M.data.levels[level_id] or {}
  M.data.levels[level_id].completed = true
  if dk_coin_collected then
    M.data.levels[level_id].dk_coin = true
  end
  if secret_exit then
    M.data.levels[level_id].secret_exit = true
    M.data.levels[level_id].completed = true
  end
  M.data.lives = M.data.lives or 3
  M.data.bananas = M.data.bananas or 0
  M.data.dk_coins = M.data.dk_coins or 0
  M.data.score = M.data.score or 0
  M.save()
end

function M.has_secret_exit(level_id)
  if M.data.levels[level_id] then
    return M.data.levels[level_id].secret_exit or false
  end
  return false
end

function M.save_runtime(lives, bananas, dk_coins, score)
  M.data.lives = lives
  M.data.bananas = bananas
  M.data.dk_coins = dk_coins
  M.data.score = score
  M.save()
end

function M.get_lives()
  return M.data.lives or 3
end

function M.get_bananas()
  return M.data.bananas or 0
end

function M.get_dk_coins()
  local collected = 0
  if M.data.levels then
    for _, ld in pairs(M.data.levels) do
      if ld.dk_coin then collected = collected + 1 end
    end
  end
  return collected
end

function M.get_spendable_dk_coins()
  return M.get_dk_coins() - (M.data.spent_dk_coins or 0)
end

function M.get_levels()
  return M.data.levels or {}
end

function M.spend_dk_coin()
  M.data.spent_dk_coins = (M.data.spent_dk_coins or 0) + 1
  M.save()
end

function M.get_total_dk_coins_possible()
  return 27
end

function M.get_score()
  return M.data.score or 0
end

return M
