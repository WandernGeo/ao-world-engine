--[[
  AO World Engine - Fashion & Vehicle Choice Module
  
  NPCs make decisions about what to wear and what to drive based on:
  - Economic tier (wealth)
  - Faction affiliation  
  - Cultural background
  - Personality traits
  - Current activity (work vs leisure)
  - Neighborhood norms
  
  Created: 2026-02-05
]]

local json = require("json")

-- ============================================================================
-- CONSTANTS
-- ============================================================================

local ECONOMIC_TIERS = {
    {name = "destitute", min = 0, max = 100},
    {name = "poor", min = 100, max = 500},
    {name = "working", min = 500, max = 2000},
    {name = "middle", min = 2000, max = 10000},
    {name = "upper", min = 10000, max = 50000},
    {name = "elite", min = 50000, max = math.huge}
}

local FORMALITY_CONTEXTS = {
    work = 0.7,
    leisure = 0.2,
    formal_event = 0.9,
    casual = 0.1,
    commute = 0.4
}

-- Faction color palettes
local FACTION_COLORS = {
    resistance = {"black", "dark_gray", "olive", "navy"},
    megacorp = {"charcoal", "navy", "white", "silver"},
    temple = {"white", "gold", "saffron", "burgundy"},
    undercity = {"neon", "black", "chrome"},
    street_gangs = {"red", "blue", "black"},
    special_forces = {"black", "urban_camo", "dark_blue"},
    neutral = {"any"}
}

-- ============================================================================
-- UTILITY FUNCTIONS
-- ============================================================================

--- Get economic tier from wealth
local function get_economic_tier(wealth)
    for _, tier in ipairs(ECONOMIC_TIERS) do
        if wealth >= tier.min and wealth < tier.max then
            return tier.name
        end
    end
    return "destitute"
end

--- Get random element from array
local function random_choice(arr)
    if not arr or #arr == 0 then return nil end
    return arr[math.random(1, #arr)]
end

--- Check if item is in array
local function contains(arr, item)
    for _, v in ipairs(arr) do
        if v == item then return true end
    end
    return false
end

-- ============================================================================
-- CLOTHING SELECTION
-- ============================================================================

local ClothingSystem = {}

--- Select outfit for NPC based on their attributes
-- @param npc table with wealth, faction, personality, activity
-- @param clothing_data table from codec_22_fashion
-- @return table with selected outfit items
function ClothingSystem.select_outfit(npc, clothing_data)
    local wealth = npc.wealth or 0
    local faction = npc.faction or "neutral"
    local personality = npc.personality or {}
    local activity = npc.current_activity or "leisure"
    local district = npc.district or "residential_lower"
    
    -- Determine economic tier
    local tier = get_economic_tier(wealth)
    
    -- Get target formality
    local base_formality = FORMALITY_CONTEXTS[activity] or 0.4
    
    -- Apply personality modifiers
    if personality.vain then
        tier = ClothingSystem.upgrade_tier(tier)
        base_formality = base_formality + 0.1
    end
    if personality.rebellious then
        base_formality = base_formality - 0.2
    end
    if personality.practical then
        base_formality = base_formality - 0.1
    end
    
    -- Clamp formality
    base_formality = math.max(0, math.min(1, base_formality))
    
    -- Get faction style
    local faction_style = clothing_data.faction_styles[faction] or {}
    local preferred_colors = faction_style.colors or FACTION_COLORS[faction] or {"gray"}
    
    -- Select items for each category
    local outfit = {
        top = ClothingSystem.select_item("tops", tier, base_formality, faction_style, clothing_data),
        bottom = ClothingSystem.select_item("bottoms", tier, base_formality, faction_style, clothing_data),
        footwear = ClothingSystem.select_item("footwear", tier, base_formality, faction_style, clothing_data),
        headwear = nil,  -- Optional
        accessories = {}
    }
    
    -- Add headwear based on faction/personality (30% chance)
    if math.random() < 0.3 or faction == "temple" or personality.rebellious then
        outfit.headwear = ClothingSystem.select_item("headwear", tier, base_formality, faction_style, clothing_data)
    end
    
    -- Add accessories based on personality
    local accessory_count = 1
    if personality.extrovert then accessory_count = accessory_count + 1 end
    if personality.vain then accessory_count = accessory_count + 1 end
    if personality.introvert then accessory_count = math.max(0, accessory_count - 1) end
    
    for i = 1, accessory_count do
        local acc = ClothingSystem.select_item("accessories", tier, base_formality, faction_style, clothing_data)
        if acc then
            table.insert(outfit.accessories, acc)
        end
    end
    
    -- Add color
    outfit.primary_color = random_choice(preferred_colors)
    
    return outfit
end

--- Select a single clothing item
function ClothingSystem.select_item(category, tier, formality, faction_style, clothing_data)
    local items = clothing_data.clothing_categories[category]
    if not items or not items.items then return nil end
    
    local eligible = {}
    
    for _, item in ipairs(items.items) do
        -- Check tier compatibility (can wear own tier or lower)
        if ClothingSystem.tier_accessible(item.tier, tier) then
            -- Check formality match (within ±0.3)
            if math.abs(item.formality - formality) <= 0.3 then
                -- Check faction preferences
                local avoided = faction_style.avoid or {}
                local item_name_lower = string.lower(item.name)
                local is_avoided = false
                
                for _, av in ipairs(avoided) do
                    if string.find(item_name_lower, string.lower(av)) then
                        is_avoided = true
                        break
                    end
                end
                
                if not is_avoided then
                    table.insert(eligible, item)
                end
            end
        end
    end
    
    return random_choice(eligible)
end

--- Check if a tier is accessible given NPC's tier
function ClothingSystem.tier_accessible(item_tier, npc_tier)
    local tier_order = {"destitute", "poor", "working", "middle", "upper", "elite"}
    local item_idx = 1
    local npc_idx = 1
    
    for i, t in ipairs(tier_order) do
        if t == item_tier then item_idx = i end
        if t == npc_tier then npc_idx = i end
    end
    
    -- Can access own tier and one below
    return item_idx <= npc_idx + 1
end

--- Upgrade tier by one level
function ClothingSystem.upgrade_tier(tier)
    local upgrades = {
        destitute = "poor",
        poor = "working",
        working = "middle",
        middle = "upper",
        upper = "elite",
        elite = "elite"
    }
    return upgrades[tier] or tier
end

-- ============================================================================
-- VEHICLE SELECTION
-- ============================================================================

local VehicleSystem = {}

--- Select vehicle for NPC based on their attributes
-- @param npc table with wealth, faction, personality
-- @param vehicle_data table from codec_23_vehicles
-- @return table with selected vehicle
function VehicleSystem.select_vehicle(npc, vehicle_data)
    local wealth = npc.wealth or 0
    local faction = npc.faction or "neutral"
    local personality = npc.personality or {}
    local district = npc.district or "residential_lower"
    
    -- Get affordable tier
    local tier = VehicleSystem.get_affordable_tier(wealth, vehicle_data)
    
    -- Apply personality modifiers
    if personality.vain then
        -- Stretch budget - try one tier higher
        tier = VehicleSystem.upgrade_vehicle_tier(tier, vehicle_data)
    end
    if personality.practical then
        -- Might go one tier lower to save money
        if math.random() < 0.3 then
            tier = VehicleSystem.downgrade_vehicle_tier(tier, vehicle_data)
        end
    end
    
    -- Get faction preferences
    local faction_prefs = vehicle_data.faction_vehicle_preferences[faction] or {}
    
    -- Get eligible vehicles
    local eligible = {}
    for _, vehicle in ipairs(vehicle_data.vehicles) do
        if vehicle.tier == tier then
            -- Check faction avoidance
            local avoided = faction_prefs.avoid or {}
            local is_avoided = false
            local veh_name_lower = string.lower(vehicle.name)
            
            for _, av in ipairs(avoided) do
                if string.find(veh_name_lower, string.lower(av)) then
                    is_avoided = true
                    break
                end
            end
            
            if not is_avoided then
                table.insert(eligible, vehicle)
            end
        end
    end
    
    -- If no eligible, try any in tier
    if #eligible == 0 then
        for _, vehicle in ipairs(vehicle_data.vehicles) do
            if vehicle.tier == tier then
                table.insert(eligible, vehicle)
            end
        end
    end
    
    local selected = random_choice(eligible)
    
    -- Apply modifications based on faction/personality
    if selected then
        selected.modifications = VehicleSystem.get_modifications(faction_prefs, personality)
    end
    
    return selected
end

--- Get affordable vehicle tier from wealth
function VehicleSystem.get_affordable_tier(wealth, vehicle_data)
    local tiers = vehicle_data.vehicle_tiers
    local affordable = "pedestrian"
    
    for name, tier_info in pairs(tiers) do
        local min_w = tier_info.wealth_range[1]
        local max_w = tier_info.wealth_range[2] or math.huge
        
        if wealth >= min_w and wealth < max_w then
            affordable = name
            break
        end
    end
    
    return affordable
end

--- Upgrade vehicle tier
function VehicleSystem.upgrade_vehicle_tier(tier, vehicle_data)
    local order = {"pedestrian", "budget", "economy", "standard", "premium", "elite"}
    for i, t in ipairs(order) do
        if t == tier and i < #order then
            return order[i + 1]
        end
    end
    return tier
end

--- Downgrade vehicle tier
function VehicleSystem.downgrade_vehicle_tier(tier, vehicle_data)
    local order = {"pedestrian", "budget", "economy", "standard", "premium", "elite"}
    for i, t in ipairs(order) do
        if t == tier and i > 1 then
            return order[i - 1]
        end
    end
    return tier
end

--- Get vehicle modifications based on faction/personality
function VehicleSystem.get_modifications(faction_prefs, personality)
    local mods = {}
    
    -- Faction modifications
    local faction_mods = faction_prefs.modifications or {}
    for _, mod in ipairs(faction_mods) do
        if math.random() < 0.5 then
            table.insert(mods, mod)
        end
    end
    
    -- Personality modifications
    if personality.rebellious and math.random() < 0.8 then
        table.insert(mods, "custom_paint")
    end
    if personality.vain then
        table.insert(mods, "chrome_accents")
    end
    
    return mods
end

-- ============================================================================
-- DRIVING OUTFIT CORRELATION
-- ============================================================================

--- Get outfit that matches vehicle
function ClothingSystem.outfit_for_vehicle(vehicle, base_outfit, clothing_data)
    if not vehicle then return base_outfit end
    
    local veh_tier = vehicle.tier
    local veh_name = string.lower(vehicle.name)
    
    -- Adjust outfit based on vehicle
    if string.find(veh_name, "motor") or string.find(veh_name, "bike") then
        -- Motorcycle requires specific gear
        base_outfit.top = ClothingSystem.find_item_by_name("Synth-Leather Jacket", clothing_data) or base_outfit.top
        base_outfit.footwear = ClothingSystem.find_item_by_name("Combat Boots", clothing_data) or base_outfit.footwear
    elseif veh_tier == "elite" or veh_tier == "premium" then
        -- Luxury vehicle → upscale outfit
        base_outfit.top = ClothingSystem.find_item_by_name("Blazer", clothing_data) or base_outfit.top
        base_outfit.footwear = ClothingSystem.find_item_by_name("Dress Shoes", clothing_data) or base_outfit.footwear
    end
    
    return base_outfit
end

--- Find item by name
function ClothingSystem.find_item_by_name(name, clothing_data)
    for cat_name, cat in pairs(clothing_data.clothing_categories) do
        for _, item in ipairs(cat.items or {}) do
            if item.name == name then
                return item
            end
        end
    end
    return nil
end

-- ============================================================================
-- AO HANDLERS
-- ============================================================================

-- Handler: Select outfit for NPC
Handlers.add(
    "SelectOutfit",
    Handlers.utils.hasMatchingTag("Action", "SelectOutfit"),
    function(msg)
        local npc = json.decode(msg.Tags.NPC or "{}")
        local clothing_data = json.decode(msg.Tags.ClothingData or "{}")
        
        local outfit = ClothingSystem.select_outfit(npc, clothing_data)
        
        ao.send({
            Target = msg.From,
            Action = "OutfitSelected",
            Data = json.encode(outfit)
        })
    end
)

-- Handler: Select vehicle for NPC
Handlers.add(
    "SelectVehicle",
    Handlers.utils.hasMatchingTag("Action", "SelectVehicle"),
    function(msg)
        local npc = json.decode(msg.Tags.NPC or "{}")
        local vehicle_data = json.decode(msg.Tags.VehicleData or "{}")
        
        local vehicle = VehicleSystem.select_vehicle(npc, vehicle_data)
        
        ao.send({
            Target = msg.From,
            Action = "VehicleSelected",
            Data = json.encode(vehicle)
        })
    end
)

-- Handler: Get complete appearance (outfit + vehicle)
Handlers.add(
    "GetAppearance",
    Handlers.utils.hasMatchingTag("Action", "GetAppearance"),
    function(msg)
        local npc = json.decode(msg.Tags.NPC or "{}")
        local clothing_data = json.decode(msg.Tags.ClothingData or "{}")
        local vehicle_data = json.decode(msg.Tags.VehicleData or "{}")
        
        local outfit = ClothingSystem.select_outfit(npc, clothing_data)
        local vehicle = VehicleSystem.select_vehicle(npc, vehicle_data)
        
        -- Correlate outfit with vehicle
        outfit = ClothingSystem.outfit_for_vehicle(vehicle, outfit, clothing_data)
        
        ao.send({
            Target = msg.From,
            Action = "AppearanceGenerated",
            Data = json.encode({
                outfit = outfit,
                vehicle = vehicle,
                npc_id = npc.id
            })
        })
    end
)

-- ============================================================================
-- EXPORTS
-- ============================================================================

return {
    ClothingSystem = ClothingSystem,
    VehicleSystem = VehicleSystem,
    get_economic_tier = get_economic_tier,
    ECONOMIC_TIERS = ECONOMIC_TIERS,
    FACTION_COLORS = FACTION_COLORS
}
