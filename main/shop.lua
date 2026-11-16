local M = {}

M.shops = {
  cranky = {
    name = "Cranky's Potion Shop",
    currency = "banana",
    items = {
      { name = "Banana Juice (1UP)", price = 15, effect = "add_life" },
      { name = "Health Refill", price = 10, effect = "refill_health" },
    },
  },
  funky = {
    name = "Funky's Flights",
    currency = "dk_coin",
    items = {
      { name = "Map Travel", price = 1, effect = "map_travel" },
      { name = "Skip Level", price = 1, effect = "skip_level" },
    },
  },
  swanky = {
    name = "Swanky's Sideshow",
    currency = "banana",
    items = {
      { name = "Bonus Game", price = 20, effect = "bonus_game" },
    },
  },
}

local shop_keys = { "cranky", "funky", "swanky" }
M.current_shop = 1
M.selected_item = 1
M.visible = false
M.should_exit = false
M.message = ""
M.message_timer = 0
M.target_level = nil

local LABEL_IDS = {
  "shop_title", "shop_item1", "shop_item2",
  "shop_price1", "shop_price2", "shop_currency",
  "shop_cursor", "shop_message", "shop_back",
}

local function _is_dk_coin_shop(shop)
  return shop.currency == "dk_coin"
end

local function _module_id_to_level_id(level_id)
  local mapped = {
    level_forest = "F-1",
    test_water = "T-1",
    boss_krow = "B-1",
    boss_kleaver = "B-2",
    boss_zing = "B-3",
    boss_kreep = "B-4",
    boss_krool1 = "B-5",
    boss_krool2 = "B-6",
  }

  if mapped[level_id] then
    return mapped[level_id]
  end

  local world, stage = level_id:match("^level_(%d+)_(%d+)$")
  if world and stage then
    return world .. "-" .. stage
  end

  return level_id
end

function M.show(shop_index, target_level)
  M.current_shop = shop_index or 1
  M.selected_item = 1
  M.visible = true
  M.should_exit = false
  M.message = ""
  M.message_timer = 0
  M.target_level = target_level
  for _, id in ipairs(LABEL_IDS) do
    msg.post("#" .. id, "enable")
  end
  M._update_display()
  msg.post("#shop_cursor", "enable")
end

function M.hide()
  M.visible = false
  for _, id in ipairs(LABEL_IDS) do
    msg.post("#" .. id, "disable")
  end
end

function M._update_display()
  local shop = M.shops[shop_keys[M.current_shop]]
  msg.post("#shop_title", "set_text", { text = shop.name })

  local items = shop.items
  for i = 1, 2 do
    local item = items[i]
    if item then
      msg.post("#shop_item" .. i, "set_text", { text = item.name })
      msg.post("#shop_price" .. i, "set_text", { text = tostring(item.price) })
    else
      msg.post("#shop_item" .. i, "set_text", { text = "" })
      msg.post("#shop_price" .. i, "set_text", { text = "" })
    end
  end

  local currency_text = shop.currency == "banana" and "BANANAS" or "DK COINS"
  msg.post("#shop_currency", "set_text", { text = currency_text })
  msg.post("#shop_cursor", "set_text", { text = ">" })

  for i = 1, 2 do
    local prefix = (i == M.selected_item) and "> " or "  "
    msg.post("#shop_item" .. i, "set_text", { text = prefix .. (items[i] and items[i].name or "") })
  end
end

function M._show_message(text, duration)
  M.message = text
  M.message_timer = duration or 2.0
  msg.post("#shop_message", "set_text", { text = text })
  msg.post("#shop_message", "enable")
end

function M.update(dt)
  if not M.visible then return end
  if M.message_timer > 0 then
    M.message_timer = M.message_timer - dt
    if M.message_timer <= 0 then
      msg.post("#shop_message", "disable")
    end
    return
  end
end

function M.on_up()
  if not M.visible then return end
  M.selected_item = M.selected_item - 1
  if M.selected_item < 1 then M.selected_item = #M.shops[shop_keys[M.current_shop]].items end
  M._update_display()
end

function M.on_down()
  if not M.visible then return end
  M.selected_item = M.selected_item + 1
  if M.selected_item > #M.shops[shop_keys[M.current_shop]].items then M.selected_item = 1 end
  M._update_display()
end

function M.on_left()
  if not M.visible then return end
  M.current_shop = M.current_shop - 1
  if M.current_shop < 1 then M.current_shop = #shop_keys end
  M.selected_item = 1
  M._update_display()
end

function M.on_right()
  if not M.visible then return end
  M.current_shop = M.current_shop + 1
  if M.current_shop > #shop_keys then M.current_shop = 1 end
  M.selected_item = 1
  M._update_display()
end

function M.on_confirm()
  if not M.visible then return end
  local shop = M.shops[shop_keys[M.current_shop]]
  local item = shop.items[M.selected_item]
  if not item then return end

  if item.effect == "skip_level" and not M.target_level then
    M._show_message("No selected level to skip", 1.5)
    return
  end

  local save_manager = require("main.save_manager")
  local hud = require("main.hud")

  if _is_dk_coin_shop(shop) then
    if save_manager.get_spendable_dk_coins() < item.price then
      M._show_message("Not enough DK Coins!", 2.0)
      return
    end
    for i = 1, item.price do
      save_manager.spend_dk_coin()
    end
  else
    if hud.bananas < item.price then
      M._show_message("Not enough bananas!", 2.0)
      return
    end
    hud.bananas = hud.bananas - item.price
  end

  local should_exit, message = M._apply_effect(item.effect)
  save_manager.save_runtime(hud.lives, hud.bananas, hud.dk_coins, hud.score)
  if should_exit then return end

  M._show_message(message or "Purchased!", 1.5)
end

function M._apply_effect(effect)
  if effect == "add_life" then
    local hud = require("main.hud")
    hud.add_life()
    return false, "Purchased!"
  elseif effect == "refill_health" then
    local player = require("main.player")
    player.health = 3
    return false, "Purchased!"
  elseif effect == "map_travel" then
    M.should_exit = true
    return true, "Choose destination in level select"
  elseif effect == "skip_level" then
    local save_manager = require("main.save_manager")
    local level_id = M.target_level
    if not level_id then
      return true, "No selected level to skip"
    end
    local mapped_level_id = _module_id_to_level_id(level_id)
    save_manager.complete_level(mapped_level_id, false, false)
    M.should_exit = true
    return true, "Level skipped"
  elseif effect == "bonus_game" then
    local player = require("main.player")
    player.health = math.min(3, player.health + 1)
    return false, "Bonus: Health +1"
  end

  return false, "Purchased!"
end

function M.on_back()
  if not M.visible then return end
  M.should_exit = true
end

return M
