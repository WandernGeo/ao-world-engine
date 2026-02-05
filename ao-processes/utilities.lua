-- ============================================================================
-- UTILITIES MODULE
-- Power, water, gas, internet for city infrastructure
-- ============================================================================

local Utilities = {}

-- ============================================================================
-- STATE
-- ============================================================================

Utilities.Power = {
    grid_capacity = 1000,
    current_load = 0,
    districts = {},
    bills = {},      -- npc_id -> { balance, due_tick, connected }
    outages = {}     -- district_id -> { start_tick, cause, duration }
}

Utilities.Water = {
    reservoirs = { main = 800000, recycled = 150000 },
    quality = {},    -- district -> quality (0-1)
    rationing = false
}

Utilities.Gas = {
    official_supply = 500,
    black_market_supply = 100,
    shortage = false
}

Utilities.Internet = {
    isps = {
        sacredlink = { subscribers = 0, bandwidth = 1000, status = "online" },
        omniconnect = { subscribers = 0, bandwidth = 800, status = "online" },
        darkwave = { subscribers = 0, bandwidth = 200, status = "unstable" },
        ghostnet = { subscribers = 0, bandwidth = 100, status = "hidden" }
    },
    subscriptions = {}  -- npc_id -> isp_id
}

-- ============================================================================
-- INITIALIZATION
-- ============================================================================

function Utilities.init()
    -- Initialize district power
    local districts = {
        "central_spire", "temple_quarter", "neon_district", "chrome_district",
        "market", "green_zone", "industrial_ring", "undercity", "waterfront", "the_ruins"
    }
    
    local reliability = {
        central_spire = 0.99, temple_quarter = 0.97, neon_district = 0.92,
        chrome_district = 0.90, market = 0.85, green_zone = 0.80,
        industrial_ring = 0.88, undercity = 0.55, waterfront = 0.75, the_ruins = 0.15
    }
    
    local water_quality = {
        central_spire = 0.98, temple_quarter = 0.97, neon_district = 0.85,
        chrome_district = 0.88, market = 0.80, green_zone = 0.75,
        industrial_ring = 0.70, undercity = 0.40, waterfront = 0.60, the_ruins = 0.20
    }
    
    for _, d in ipairs(districts) do
        Utilities.Power.districts[d] = {
            supply = 100,
            demand = 80,
            reliability = reliability[d] or 0.5,
            status = "online"
        }
        Utilities.Water.quality[d] = water_quality[d] or 0.5
    end
end

-- ============================================================================
-- TICK PROCESSING
-- ============================================================================

function Utilities.on_tick(tick, weather, npcs)
    -- Process power grid
    local power_events = Utilities.process_power(tick, weather)
    
    -- Process water
    local water_events = Utilities.process_water(tick, weather)
    
    -- Process bills monthly
    if tick % 30 == 0 then
        Utilities.process_bills(tick, npcs)
    end
    
    -- Process internet
    local internet_events = Utilities.process_internet(tick)
    
    return {
        power = power_events,
        water = water_events,
        internet = internet_events
    }
end

-- ============================================================================
-- POWER GRID
-- ============================================================================

function Utilities.process_power(tick, weather)
    local events = {}
    
    -- Weather affects demand
    local weather_mod = 1.0
    if weather == "storm" then
        weather_mod = 1.3
    elseif weather == "clear" and tick % 240 < 120 then  -- Daytime
        weather_mod = 0.9
    end
    
    -- Calculate total load
    local total_load = 0
    for district_id, district in pairs(Utilities.Power.districts) do
        district.demand = district.demand * weather_mod
        total_load = total_load + district.demand
    end
    Utilities.Power.current_load = total_load
    
    -- Check for overload
    if total_load > Utilities.Power.grid_capacity * 0.95 then
        -- Brownout - cut power to lowest priority
        local brownout_district = Utilities.find_lowest_priority_district()
        if brownout_district then
            Utilities.trigger_brownout(brownout_district, tick)
            table.insert(events, {
                type = "brownout",
                district = brownout_district,
                tick = tick
            })
        end
    end
    
    -- Storm can cause outages
    if weather == "storm" then
        local storm_chance = 0.1
        if math.random() < storm_chance then
            local districts = {"neon_district", "market", "green_zone", "waterfront"}
            local hit = districts[math.random(#districts)]
            Utilities.trigger_outage(hit, tick, "lightning")
            table.insert(events, {
                type = "storm_outage",
                district = hit,
                cause = "lightning",
                tick = tick
            })
        end
    end
    
    -- Resolve outages
    for district_id, outage in pairs(Utilities.Power.outages) do
        if tick >= outage.start_tick + outage.duration then
            Utilities.Power.districts[district_id].status = "online"
            Utilities.Power.outages[district_id] = nil
        end
    end
    
    return events
end

function Utilities.find_lowest_priority_district()
    local priority_order = {
        "the_ruins", "undercity", "waterfront", "green_zone",
        "market", "neon_district", "chrome_district", "industrial_ring",
        "temple_quarter", "central_spire"
    }
    
    for _, d in ipairs(priority_order) do
        if Utilities.Power.districts[d] and Utilities.Power.districts[d].status == "online" then
            return d
        end
    end
    return nil
end

function Utilities.trigger_brownout(district_id, tick)
    Utilities.Power.districts[district_id].status = "brownout"
    Utilities.Power.outages[district_id] = {
        start_tick = tick,
        cause = "overload",
        duration = 10  -- 10 ticks = ~1 hour
    }
end

function Utilities.trigger_outage(district_id, tick, cause)
    Utilities.Power.districts[district_id].status = "offline"
    Utilities.Power.outages[district_id] = {
        start_tick = tick,
        cause = cause,
        duration = cause == "lightning" and 24 or 48  -- Lightning = 1 day, sabotage = 2 days
    }
end

-- ============================================================================
-- WATER SYSTEM
-- ============================================================================

function Utilities.process_water(tick, weather)
    local events = {}
    
    -- Rain replenishes reservoirs
    if weather == "rain" or weather == "storm" then
        Utilities.Water.reservoirs.main = math.min(1000000, Utilities.Water.reservoirs.main + 10000)
    end
    
    -- Daily consumption
    if tick % 24 == 0 then
        Utilities.Water.reservoirs.main = math.max(0, Utilities.Water.reservoirs.main - 50000)
        Utilities.Water.reservoirs.recycled = math.max(0, Utilities.Water.reservoirs.recycled - 20000)
        
        -- Check for drought
        local total_water = Utilities.Water.reservoirs.main + Utilities.Water.reservoirs.recycled
        if total_water < 300000 then
            Utilities.Water.rationing = true
            table.insert(events, {
                type = "water_rationing",
                level = total_water < 150000 and "severe" or "moderate",
                tick = tick
            })
        else
            Utilities.Water.rationing = false
        end
    end
    
    return events
end

-- ============================================================================
-- BILLS PROCESSING
-- ============================================================================

function Utilities.process_bills(tick, npcs)
    local disconnections = {}
    
    for npc_id, npc in pairs(npcs) do
        local bill = Utilities.calculate_monthly_bill(npc_id, npc)
        local existing = Utilities.Power.bills[npc_id] or { balance = 0, connected = true }
        
        existing.balance = existing.balance + bill.total
        existing.due_tick = tick + 30  -- Due in 30 ticks
        
        -- Check if NPC can pay
        local npc_money = npc.money or npc.wealth or 0
        
        if npc_money >= existing.balance then
            -- Pay bills
            npc.money = npc_money - existing.balance
            existing.balance = 0
        else
            -- Partial payment or none
            local payment = math.min(npc_money, existing.balance)
            npc.money = npc_money - payment
            existing.balance = existing.balance - payment
            
            -- Disconnect if overdue by 7+ days
            if existing.balance > 0 and tick > (existing.due_tick or 0) + 7 then
                existing.connected = false
                table.insert(disconnections, npc_id)
            end
        end
        
        Utilities.Power.bills[npc_id] = existing
    end
    
    return disconnections
end

function Utilities.calculate_monthly_bill(npc_id, npc)
    local district = npc.district or "neon_district"
    local wealth_tier = (npc.occupation and npc.occupation.income) or 100
    
    -- Base rates
    local power_rate = 5
    local water_rate = 2
    local gas_rate = 8
    local internet_rate = 50
    
    -- Adjust for wealth (larger homes = more usage)
    local usage_modifier = wealth_tier > 200 and 1.5 or (wealth_tier < 50 and 0.7 or 1.0)
    
    return {
        power = math.floor(30 * usage_modifier * power_rate / power_rate),
        water = math.floor(20 * usage_modifier),
        gas = npc.has_heating and math.floor(40 * usage_modifier) or 0,
        internet = Utilities.get_internet_cost(npc_id),
        total = math.floor((30 + 20 + 40) * usage_modifier) + Utilities.get_internet_cost(npc_id)
    }
end

-- ============================================================================
-- INTERNET
-- ============================================================================

function Utilities.process_internet(tick)
    local events = {}
    
    -- DarkWave has intermittent connectivity
    if math.random() < 0.3 then
        Utilities.Internet.isps.darkwave.status = "offline"
    else
        Utilities.Internet.isps.darkwave.status = "unstable"
    end
    
    -- GhostNet occasionally goes dark for safety
    if tick % 100 == 0 then
        Utilities.Internet.isps.ghostnet.status = "dark"
        table.insert(events, { type = "ghostnet_dark", tick = tick })
    elseif tick % 100 == 10 then
        Utilities.Internet.isps.ghostnet.status = "hidden"
    end
    
    return events
end

function Utilities.get_internet_cost(npc_id)
    local isp = Utilities.Internet.subscriptions[npc_id]
    if not isp then return 0 end
    
    local costs = {
        sacredlink = 50,
        omniconnect = 100,
        darkwave = 0,
        ghostnet = 25
    }
    
    return costs[isp] or 50
end

function Utilities.has_internet(npc_id)
    local isp = Utilities.Internet.subscriptions[npc_id]
    if not isp then return false end
    
    local isp_data = Utilities.Internet.isps[isp]
    return isp_data and isp_data.status ~= "offline"
end

function Utilities.subscribe_internet(npc_id, isp_id)
    Utilities.Internet.subscriptions[npc_id] = isp_id
    Utilities.Internet.isps[isp_id].subscribers = 
        (Utilities.Internet.isps[isp_id].subscribers or 0) + 1
end

-- ============================================================================
-- PUBLIC API
-- ============================================================================

function Utilities.get_power_status(district_id)
    return Utilities.Power.districts[district_id] or { status = "unknown" }
end

function Utilities.get_water_quality(district_id)
    return Utilities.Water.quality[district_id] or 0.5
end

function Utilities.is_rationing()
    return Utilities.Water.rationing
end

function Utilities.get_npc_utility_status(npc_id)
    local bill = Utilities.Power.bills[npc_id] or { connected = true, balance = 0 }
    return {
        power_connected = bill.connected,
        water_connected = true,  -- Water rarely disconnected
        gas_connected = not Utilities.Gas.shortage,
        internet_connected = Utilities.has_internet(npc_id),
        outstanding_balance = bill.balance
    }
end

-- Export module
return Utilities
