--[[
  AO World Engine - Master World Process
  
  The central coordinator for the RE:ECHO City simulation.
  Runs autonomously via CRON messages, advancing ticks and 
  coordinating all district processes.
  
  CRON SETUP:
  - Spawned with Cron-Interval: "1-minute" (or "10-minutes" for prod)
  - Each cron message advances WorldTick
  - Broadcasts tick to all registered districts
  
  SECURITY: No secrets. State is holographic (reconstructible from logs).
]]--

local json = require("json")
local crypto = require("crypto")

-- =============================================================================
-- GLOBAL STATE (Uppercase = persisted on Arweave)
-- =============================================================================

WorldTick = WorldTick or 0
WorldDay = WorldDay or 0
WorldYear = WorldYear or 0

-- Registered processes
Districts = Districts or {}  -- { district_id: process_id }
EventBus = EventBus or nil
AiOracle = AiOracle or nil
Economy = Economy or nil

-- City state
CityBudget = CityBudget or 1000000  -- Starting GEP
TaxRate = TaxRate or 0.10           -- 10% income tax
PopulationCount = PopulationCount or 0
ActiveNpcCount = ActiveNpcCount or 0

-- Configuration
TICKS_PER_DAY = 240      -- 10 ticks/hour * 24 hours
TICKS_PER_YEAR = 87600   -- 365 days
TAX_COLLECTION_INTERVAL = TICKS_PER_DAY  -- Daily

-- Pending events that need world-level coordination
PendingEvents = PendingEvents or {}
ProcessedEvents = ProcessedEvents or {}

-- =============================================================================
-- DETERMINISTIC UTILITIES
-- =============================================================================

function hash_to_number(str, max)
    local hash = crypto.digest.sha256(str)
    return tonumber(hash:sub(1, 8), 16) % max
end

function seeded_choice(items, seed)
    if not items or #items == 0 then return nil end
    local idx = hash_to_number(seed, #items) + 1
    return items[idx]
end

function seeded_chance(probability, seed)
    local roll = hash_to_number(seed, 10000) / 10000
    return roll < probability
end

-- =============================================================================
-- TIME UTILITIES
-- =============================================================================

function get_time_info(tick)
    local day_tick = tick % TICKS_PER_DAY
    local hour = math.floor(day_tick / 10)
    local minute = (day_tick % 10) * 6
    
    local period
    if day_tick < 24 then period = "T01"        -- 00:00-02:24
    elseif day_tick < 72 then period = "T02"    -- 02:24-07:12
    elseif day_tick < 100 then period = "T03"   -- 07:12-10:00
    elseif day_tick < 140 then period = "T04"   -- 10:00-14:00
    elseif day_tick < 170 then period = "T05"   -- 14:00-17:00
    elseif day_tick < 190 then period = "T06"   -- 17:00-19:00
    elseif day_tick < 210 then period = "T07"   -- 19:00-21:00
    elseif day_tick < 230 then period = "T08"   -- 21:00-23:00
    else period = "T09" end                      -- 23:00-00:00
    
    return {
        tick = tick,
        day = WorldDay,
        year = WorldYear,
        hour = hour,
        minute = minute,
        period = period,
        is_night = period == "T01" or period == "T02" or period == "T09"
    }
end

-- =============================================================================
-- ECONOMY FUNCTIONS
-- =============================================================================

function collect_taxes()
    -- Calculate expected tax revenue based on population
    local estimated_income = PopulationCount * 75  -- Average income
    local tax_revenue = math.floor(estimated_income * TaxRate)
    
    CityBudget = CityBudget + tax_revenue
    
    -- Record transaction
    table.insert(ProcessedEvents, {
        type = "tax_collection",
        tick = WorldTick,
        day = WorldDay,
        amount = tax_revenue,
        new_budget = CityBudget
    })
    
    return tax_revenue
end

function pay_city_workers()
    -- City expenses (police, sanitation, infrastructure)
    local police_cost = 5000
    local sanitation_cost = 2000
    local infrastructure_cost = 3000
    local total_cost = police_cost + sanitation_cost + infrastructure_cost
    
    if CityBudget >= total_cost then
        CityBudget = CityBudget - total_cost
        
        table.insert(ProcessedEvents, {
            type = "city_expenses",
            tick = WorldTick,
            day = WorldDay,
            amount = total_cost,
            breakdown = {
                police = police_cost,
                sanitation = sanitation_cost,
                infrastructure = infrastructure_cost
            },
            new_budget = CityBudget
        })
        
        return true
    else
        -- Budget crisis - reduce services
        table.insert(ProcessedEvents, {
            type = "budget_crisis",
            tick = WorldTick,
            day = WorldDay,
            shortfall = total_cost - CityBudget
        })
        return false
    end
end

-- =============================================================================
-- WORLD EVENTS
-- =============================================================================

function check_world_events(tick)
    local events = {}
    local time = get_time_info(tick)
    
    -- Daily events
    if tick % TICKS_PER_DAY == 120 then  -- Noon
        -- Market activity peak
        table.insert(events, {
            type = "market_peak",
            tick = tick,
            scope = "city"
        })
    end
    
    -- Random city-wide events
    if seeded_chance(0.001, "blackout_" .. tick) then
        table.insert(events, {
            type = "power_fluctuation",
            tick = tick,
            scope = "city",
            severity = seeded_choice({"minor", "major", "critical"}, "blackout_sev_" .. tick)
        })
    end
    
    if seeded_chance(0.0005, "protest_" .. tick) and time.period == "T04" then
        table.insert(events, {
            type = "protest",
            tick = tick,
            scope = "district",
            location = seeded_choice({"temple_district", "market_district", "hab_blocks"}, "protest_loc_" .. tick)
        })
    end
    
    -- Weather (changes every 100 ticks)
    if tick % 100 == 0 then
        table.insert(events, {
            type = "weather_change",
            tick = tick,
            weather = seeded_choice({"rain", "heavy_rain", "fog", "clear", "smog"}, "weather_" .. tick)
        })
    end
    
    return events
end

function broadcast_event(event)
    -- Send event to all registered districts
    for district_id, process_id in pairs(Districts) do
        ao.send({
            Target = process_id,
            Action = "world-event",
            Data = json.encode(event)
        })
    end
    
    -- Notify event bus if registered
    if EventBus then
        ao.send({
            Target = EventBus,
            Action = "publish",
            Data = json.encode(event)
        })
    end
end

-- =============================================================================
-- HANDLERS
-- =============================================================================

-- Initialize world
Handlers.add("init", Handlers.utils.hasMatchingTag("Action", "Init"), function(msg)
    local data = json.decode(msg.Data)
    
    -- Set initial configuration
    if data.tax_rate then TaxRate = data.tax_rate end
    if data.initial_budget then CityBudget = data.initial_budget end
    if data.population then PopulationCount = data.population end
    
    -- Register initial districts
    if data.districts then
        for _, d in ipairs(data.districts) do
            Districts[d.id] = d.process_id
        end
    end
    
    ao.send({
        Target = msg.From,
        Action = "init-complete",
        Data = json.encode({
            world_tick = WorldTick,
            districts = table_length(Districts),
            population = PopulationCount,
            budget = CityBudget
        })
    })
end)

-- Register a district process
Handlers.add("register-district", Handlers.utils.hasMatchingTag("Action", "register-district"), function(msg)
    local data = json.decode(msg.Data)
    Districts[data.district_id] = msg.From
    
    ao.send({
        Target = msg.From,
        Action = "registered",
        Data = json.encode({ world_tick = WorldTick })
    })
end)

-- Register event bus
Handlers.add("register-event-bus", Handlers.utils.hasMatchingTag("Action", "register-event-bus"), function(msg)
    EventBus = msg.From
    ao.send({
        Target = msg.From,
        Action = "registered",
        Data = json.encode({ role = "event_bus", world_tick = WorldTick })
    })
end)

-- Register AI oracle
Handlers.add("register-oracle", Handlers.utils.hasMatchingTag("Action", "register-oracle"), function(msg)
    AiOracle = msg.From
    ao.send({
        Target = msg.From,
        Action = "registered",
        Data = json.encode({ role = "ai_oracle", world_tick = WorldTick })
    })
end)

-- =============================================================================
-- CRON: MASTER TICK ADVANCEMENT
-- 
-- This is the heartbeat of the simulation.
-- Set Cron-Interval when spawning this process.
-- =============================================================================

Handlers.add("cron-tick", Handlers.utils.hasMatchingTag("Action", "Cron"), function(msg)
    -- Advance world tick
    WorldTick = WorldTick + 1
    
    -- Day/year advancement
    if WorldTick % TICKS_PER_DAY == 0 then
        WorldDay = WorldDay + 1
    end
    if WorldTick % TICKS_PER_YEAR == 0 then
        WorldYear = WorldYear + 1
    end
    
    local time = get_time_info(WorldTick)
    
    -- 1. Check for world events
    local events = check_world_events(WorldTick)
    for _, event in ipairs(events) do
        broadcast_event(event)
        table.insert(ProcessedEvents, event)
    end
    
    -- 2. Broadcast tick to all districts
    for district_id, process_id in pairs(Districts) do
        ao.send({
            Target = process_id,
            Action = "Cron",
            Tags = {
                { name = "World-Tick", value = tostring(WorldTick) },
                { name = "Time-Period", value = time.period }
            },
            Data = json.encode({
                tick = WorldTick,
                time = time,
                events = events
            })
        })
    end
    
    -- 3. Notify AI oracle (may generate dialogue for active NPCs)
    if AiOracle and WorldTick % 10 == 0 then  -- Every 10 ticks
        ao.send({
            Target = AiOracle,
            Action = "Cron",
            Data = json.encode({ tick = WorldTick, time = time })
        })
    end
    
    -- 4. Economy processing (daily)
    if WorldTick % TAX_COLLECTION_INTERVAL == 0 then
        local tax_revenue = collect_taxes()
        local services_paid = pay_city_workers()
        
        -- Broadcast economy update
        broadcast_event({
            type = "economy_update",
            tick = WorldTick,
            day = WorldDay,
            tax_revenue = tax_revenue,
            budget = CityBudget,
            services_paid = services_paid
        })
    end
    
    -- 5. Persist state snapshot every 100 ticks
    if WorldTick % 100 == 0 then
        persist_state_snapshot()
    end
    
    -- Trim processed events (keep last 1000)
    while #ProcessedEvents > 1000 do
        table.remove(ProcessedEvents, 1)
    end
end)

-- =============================================================================
-- QUERY HANDLERS
-- =============================================================================

-- Get world state
Handlers.add("get-state", Handlers.utils.hasMatchingTag("Action", "get-state"), function(msg)
    ao.send({
        Target = msg.From,
        Action = "state-response",
        Data = json.encode({
            tick = WorldTick,
            day = WorldDay,
            year = WorldYear,
            time = get_time_info(WorldTick),
            budget = CityBudget,
            tax_rate = TaxRate,
            population = PopulationCount,
            districts = table_length(Districts),
            recent_events = #ProcessedEvents > 10 and {table.unpack(ProcessedEvents, #ProcessedEvents - 9)} or ProcessedEvents
        })
    })
end)

-- Get economy stats
Handlers.add("get-economy", Handlers.utils.hasMatchingTag("Action", "get-economy"), function(msg)
    ao.send({
        Target = msg.From,
        Action = "economy-response",
        Data = json.encode({
            budget = CityBudget,
            tax_rate = TaxRate,
            population = PopulationCount,
            estimated_daily_revenue = math.floor(PopulationCount * 75 * TaxRate),
            estimated_daily_expenses = 10000,
            last_events = {}
        })
    })
end)

-- =============================================================================
-- PERSISTENCE
-- =============================================================================

function persist_state_snapshot()
    -- State automatically persists via Arweave message log
    -- This explicitly sends a snapshot for faster reconstruction
    ao.send({
        Target = ao.id,
        Action = "state-snapshot",
        Data = json.encode({
            tick = WorldTick,
            day = WorldDay,
            year = WorldYear,
            budget = CityBudget,
            population = PopulationCount,
            districts = Districts,
            timestamp = os.time()
        })
    })
end

-- =============================================================================
-- HELPERS
-- =============================================================================

function table_length(t)
    local count = 0
    for _ in pairs(t) do count = count + 1 end
    return count
end

-- =============================================================================
-- MODULE EXPORT (for testing)
-- =============================================================================

return {
    get_time_info = get_time_info,
    check_world_events = check_world_events,
    collect_taxes = collect_taxes,
    hash_to_number = hash_to_number,
    seeded_choice = seeded_choice
}
