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

local json = json or require("json")

-- Crypto module optional (not available in all AOS environments)
local crypto_available, crypto = pcall(require, "crypto")
if not crypto_available then crypto = nil end

-- Utilities module (optional - handles power, water, internet)
local utilities_available, Utilities = pcall(require, "utilities")
if utilities_available then
    Utilities.init()
    print("✅ Utilities module loaded")
else
    Utilities = nil
    print("⚠️ Utilities module not available")
end

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

-- =============================================================================
-- SIMULATION CONTROL (Kill Switch / Pause / Freeze)
-- =============================================================================

-- Status: "running" | "paused" | "frozen" | "terminated"
SimulationStatus = SimulationStatus or "running"

-- Owner address (set on first Initialize, can pause/stop)
OwnerAddress = OwnerAddress or nil

-- Kill switch passphrase (set via secure message)
KillSwitchHash = KillSwitchHash or nil

-- Configuration
TICKS_PER_DAY = 240      -- 10 ticks/hour * 24 hours
TICKS_PER_YEAR = 87600   -- 365 days
TAX_COLLECTION_INTERVAL = TICKS_PER_DAY  -- Daily

-- Pending events that need world-level coordination
PendingEvents = PendingEvents or {}
ProcessedEvents = ProcessedEvents or {}

-- =============================================================================
-- CHAT MEMORY (Persisted on Arweave - survives restarts!)
-- =============================================================================

-- User memory: { user_id: { name: string, first_seen_tick: number } }
UserMemory = UserMemory or {}

-- NPC conversations: { npc_id: { user_id: { messages: [...], last_tick: number } } }
NPCConversations = NPCConversations or {}

-- Conversation limit per NPC-user pair (older messages trimmed)
MAX_MESSAGES_PER_CONVERSATION = 50

-- =============================================================================
-- NPC LOCATIONS & SCHEDULES (Persisted - enables movement behaviors)
-- =============================================================================

-- NPC schedules: { npc_id: { home: "B001", work: "B002", social: ["B010"] } }
NPCSchedules = NPCSchedules or {}

-- Current NPC locations: { npc_id: { location: "B001", state: "working", since_tick: 100 } }
NPCLocations = NPCLocations or {}

-- Movement log for the last day (240 ticks)
MovementLog = MovementLog or {}
MAX_MOVEMENT_LOG = 1000

-- Social locations for evening hangouts
SOCIAL_LOCATIONS = SOCIAL_LOCATIONS or { 
    "L001", "L003", "L050", "L051", "L032", "L033", "L026" 
}

-- =============================================================================
-- NPC SOCIAL INTERACTIONS (Persisted - tracks NPC relationships)
-- =============================================================================

-- Social interaction history: { "npc1_npc2": { met_count: 5, last_tick: 100, relationship: 0.5 } }
NPCSocialHistory = NPCSocialHistory or {}

-- Recent interaction log: [ { tick, npc1, npc2, location, type, mood_delta } ]
InteractionLog = InteractionLog or {}
MAX_INTERACTION_LOG = 500

-- =============================================================================
-- NPC ECONOMY (Persisted - tracks NPC wealth and transactions)
-- =============================================================================

-- NPC wallets: { npc_id: { balance: 1000, income_tick: 0, spending_tick: 0 } }
NPCWallets = NPCWallets or {}

-- NPC economic transactions log
NPCTransactionLog = NPCTransactionLog or {}
MAX_TRANSACTION_LOG = 500

-- Base wages per shift (paid once per day at shift end)
-- Values in GEP (game currency)
ARCHETYPE_WAGES = {
    -- High earners
    ["doctor"] = 500,
    ["executive"] = 600,
    ["manager"] = 400,
    ["biotech scientist"] = 550,
    ["faction leader"] = 700,
    
    -- Medium earners
    ["security guard"] = 200,
    ["noir detective"] = 250,
    ["bartender"] = 180,
    ["street medic"] = 300,
    ["pilot/explorer"] = 350,
    
    -- Low earners
    ["artist/performer"] = 150,
    ["hacker"] = 200,
    ["street oracle"] = 100,
    ["matriarch/healer"] = 120,
    ["religious oracle"] = 80,
    
    -- Default
    ["default"] = 150
}

-- Archetype-to-shift mapping for auto-assignment
-- When loading schedules without explicit shift, derive from archetype/role
ARCHETYPE_SHIFTS = {
    -- Day shift (9-17)
    ["office worker"] = "day",
    ["manager"] = "day",
    ["executive"] = "day",
    ["teacher"] = "day",
    ["accountant"] = "day",
    ["lawyer"] = "day",
    ["banker"] = "day",
    ["clerk"] = "day",
    ["receptionist"] = "day",
    
    -- Night shift (22-6)  
    ["security guard"] = "night",
    ["night watchman"] = "night",
    ["club owner"] = "night",
    ["bouncer"] = "night",
    ["dj"] = "night",
    ["bartender night"] = "night",
    ["prostitute"] = "night",
    ["smuggler"] = "night",
    
    -- Graveyard shift (0-8)
    ["night nurse"] = "graveyard",
    ["hospital orderly"] = "graveyard",
    ["24h store clerk"] = "graveyard",
    ["factory night shift"] = "graveyard",
    ["security overnight"] = "graveyard",
    
    -- Evening shift (16-24)
    ["waiter"] = "evening",
    ["waitress"] = "evening",
    ["bartender"] = "evening",
    ["host"] = "evening",
    ["server"] = "evening",
    ["cook"] = "evening",
    ["performer"] = "evening",
    ["musician"] = "evening",
    ["dancer"] = "evening",
    
    -- Morning shift (4-12)
    ["baker"] = "morning",
    ["garbage collector"] = "morning",
    ["delivery driver"] = "morning",
    ["newspaper vendor"] = "morning",
    ["breakfast cook"] = "morning",
    ["milk delivery"] = "morning",
    ["street cleaner"] = "morning",
    
    -- Flexible (10-18)
    ["artist"] = "flexible",
    ["writer"] = "flexible",
    ["freelancer"] = "flexible",
    ["hacker"] = "flexible",
    ["netrunner"] = "flexible",
    ["fixer"] = "flexible",
    ["information broker"] = "flexible",
    
    -- Always on / rotating (emergency services)
    ["doctor"] = "always_on",
    ["nurse"] = "always_on",
    ["paramedic"] = "always_on",
    ["firefighter"] = "always_on",
    ["emergency responder"] = "always_on",
    ["police officer"] = "always_on",
    
    -- Split shift (restaurant)
    ["restaurant manager"] = "split",
    ["chef"] = "split",
    ["maitre d"] = "split"
}

-- Helper to derive shift from archetype/role
function get_shift_for_archetype(archetype, role)
    local lower_archetype = string.lower(archetype or "")
    local lower_role = string.lower(role or "")
    
    -- Check direct matches first
    if ARCHETYPE_SHIFTS[lower_archetype] then
        return ARCHETYPE_SHIFTS[lower_archetype]
    end
    if ARCHETYPE_SHIFTS[lower_role] then
        return ARCHETYPE_SHIFTS[lower_role]
    end
    
    -- Check partial matches
    for pattern, shift in pairs(ARCHETYPE_SHIFTS) do
        if string.find(lower_archetype, pattern) or string.find(lower_role, pattern) then
            return shift
        end
    end
    
    -- Default to day shift
    return "day"
end

-- =============================================================================
-- DETERMINISTIC UTILITIES
-- =============================================================================

function hash_to_number(str, max)
    -- Use crypto.digest if available, otherwise use simple Lua hash
    if crypto and crypto.digest then
        local hash = crypto.digest.sha256(str)
        return tonumber(hash:sub(1, 8), 16) % max
    else
        -- Fallback: simple deterministic hash
        local hash = 0
        for i = 1, #str do
            hash = (hash * 31 + string.byte(str, i)) % 2147483647
        end
        return hash % max
    end
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
-- NPC MOVEMENT BEHAVIORS
-- =============================================================================

-- Shift definitions: each shift defines work hours
-- Shift types: day, night, graveyard, evening, flexible, always_on
SHIFT_DEFINITIONS = {
    day = { start = 9, finish = 17 },           -- Standard office hours
    night = { start = 22, finish = 6 },          -- Night security, bars
    graveyard = { start = 0, finish = 8 },       -- Hospital night, 24h stores
    evening = { start = 16, finish = 24 },       -- Restaurants, entertainment
    morning = { start = 4, finish = 12 },        -- Bakery, garbage, delivery
    flexible = { start = 10, finish = 18 },      -- Creative, freelance
    always_on = { start = 0, finish = 24 },      -- Emergency services
    split = { start = 11, finish = 14, start2 = 18, finish2 = 23 }  -- Restaurant
}

function is_work_hours(hour, shift_type)
    local shift = SHIFT_DEFINITIONS[shift_type or "day"]
    if not shift then return false end
    
    -- Handle split shifts
    if shift.start2 then
        return (hour >= shift.start and hour < shift.finish) or
               (hour >= shift.start2 and hour < shift.finish2)
    end
    
    -- Handle overnight shifts (night, graveyard)
    if shift.start > shift.finish then
        return hour >= shift.start or hour < shift.finish
    end
    
    -- Normal daytime shifts
    return hour >= shift.start and hour < shift.finish
end

function get_commute_hour(shift_type, is_going_to_work)
    local shift = SHIFT_DEFINITIONS[shift_type or "day"]
    if not shift then return 8 end  -- default
    
    if is_going_to_work then
        return shift.start - 1  -- commute 1 hour before work
    else
        return shift.finish     -- commute right after work
    end
end

function process_npc_movements(tick)
    local time = get_time_info(tick)
    local hour = time.hour
    local movements = 0
    
    -- Process each NPC with a schedule
    for npc_id, schedule in pairs(NPCSchedules) do
        local current = NPCLocations[npc_id] or { location = schedule.home, state = "idle", since_tick = 0 }
        local target_location = nil
        local new_state = nil
        
        local shift_type = schedule.shift or "day"
        local is_working = is_work_hours(hour, shift_type)
        local commute_to_work = get_commute_hour(shift_type, true)
        local commute_from_work = get_commute_hour(shift_type, false)
        
        -- Determine what this NPC should be doing based on their shift
        if is_working then
            -- Working hours for this NPC
            target_location = schedule.work or schedule.home
            new_state = "working"
        elseif hour == commute_to_work then
            -- Commuting to work
            target_location = schedule.work or schedule.home
            new_state = "commuting_to_work"
        elseif hour == commute_from_work or hour == (commute_from_work % 24) then
            -- Commuting from work
            target_location = schedule.home
            new_state = "commuting_home"
        else
            -- Off work - determine activity based on time of day
            local off_work_hour = hour
            
            -- Adjust for night workers (their "evening" is morning)
            local is_night_worker = (shift_type == "night" or shift_type == "graveyard")
            
            if is_night_worker then
                -- Night workers sleep during the day
                if hour >= 8 and hour < 16 then
                    target_location = schedule.home
                    new_state = "sleeping"
                elseif hour >= 16 and hour < 20 then
                    -- Their "evening" - wake up, socialize
                    if seeded_chance(0.3, npc_id .. tostring(WorldDay)) then
                        target_location = seeded_choice(SOCIAL_LOCATIONS, npc_id .. tostring(tick))
                        new_state = "socializing"
                    else
                        target_location = schedule.home
                        new_state = "relaxing"
                    end
                elseif hour >= 20 and hour < commute_to_work then
                    -- Getting ready for work
                    target_location = schedule.home
                    new_state = "preparing"
                else
                    target_location = schedule.home
                    new_state = "resting"
                end
            else
                -- Day workers - normal pattern
                if hour >= 0 and hour < 6 then
                    -- Night: sleeping
                    target_location = schedule.home
                    new_state = "sleeping"
                elseif hour >= 6 and hour < commute_to_work then
                    -- Morning: waking up
                    target_location = schedule.home
                    new_state = "waking"
                elseif hour >= commute_from_work and hour < 22 then
                    -- Evening: home or social
                    if seeded_chance(0.3, npc_id .. tostring(WorldDay)) then
                        target_location = seeded_choice(SOCIAL_LOCATIONS, npc_id .. tostring(tick))
                        new_state = "socializing"
                    else
                        target_location = schedule.home
                        new_state = "relaxing"
                    end
                else
                    -- Late night: going to sleep
                    target_location = schedule.home
                    new_state = "going_home"
                end
            end
        end
        
        -- Check if movement occurred
        if target_location and target_location ~= current.location then
            -- Log the movement
            table.insert(MovementLog, {
                tick = tick,
                npc_id = npc_id,
                from = current.location,
                to = target_location,
                state = new_state,
                hour = hour,
                shift = shift_type
            })
            movements = movements + 1
            
            -- Update location
            NPCLocations[npc_id] = {
                location = target_location,
                state = new_state,
                since_tick = tick
            }
        elseif new_state and new_state ~= current.state then
            -- State change without location change
            NPCLocations[npc_id] = {
                location = current.location,
                state = new_state,
                since_tick = current.since_tick
            }
        end
    end
    
    -- Trim movement log to keep it manageable
    while #MovementLog > MAX_MOVEMENT_LOG do
        table.remove(MovementLog, 1)
    end
    
    if movements > 0 then
        print("🚶 Processed " .. movements .. " NPC movements at tick " .. tick)
    end
    
    return movements
end

-- =============================================================================
-- NPC SOCIAL INTERACTIONS
-- =============================================================================

-- Create a unique key for NPC pairs (always alphabetically ordered)
function get_social_key(npc1, npc2)
    if npc1 < npc2 then
        return npc1 .. "_" .. npc2
    else
        return npc2 .. "_" .. npc1
    end
end

-- Process social interactions between NPCs at same location
function process_social_interactions(tick)
    local interactions = 0
    local time = get_time_info(tick)
    
    -- Group NPCs by location
    local location_groups = {}
    for npc_id, loc_data in pairs(NPCLocations) do
        local location = loc_data.location
        if not location_groups[location] then
            location_groups[location] = {}
        end
        table.insert(location_groups[location], {
            id = npc_id,
            state = loc_data.state
        })
    end
    
    -- Find interactions where 2+ NPCs are at same location
    for location, npcs in pairs(location_groups) do
        if #npcs >= 2 then
            -- Create interactions between each pair (limited to first 5 NPCs per location)
            local max_npcs = math.min(#npcs, 5)
            for i = 1, max_npcs do
                for j = i + 1, max_npcs do
                    local npc1 = npcs[i]
                    local npc2 = npcs[j]
                    
                    -- Only interact if both are in active states (not sleeping)
                    if npc1.state ~= "sleeping" and npc2.state ~= "sleeping" then
                        local social_key = get_social_key(npc1.id, npc2.id)
                        
                        -- Get or create relationship history
                        local history = NPCSocialHistory[social_key] or {
                            met_count = 0,
                            last_tick = 0,
                            relationship = 0.5  -- Neutral starting point
                        }
                        
                        -- Only process if haven't met recently (cooldown of 10 ticks)
                        if tick - history.last_tick >= 10 then
                            history.met_count = history.met_count + 1
                            history.last_tick = tick
                            
                            -- Determine interaction type based on states
                            local interaction_type = "casual"
                            local mood_delta = 0.01  -- Small positive by default
                            
                            if npc1.state == "socializing" or npc2.state == "socializing" then
                                interaction_type = "social"
                                mood_delta = 0.03
                            elseif npc1.state == "working" and npc2.state == "working" then
                                interaction_type = "professional"
                                mood_delta = 0.01
                            end
                            
                            -- Update relationship (bounded 0-1)
                            history.relationship = math.min(1.0, math.max(0, history.relationship + mood_delta))
                            
                            -- Store updated history
                            NPCSocialHistory[social_key] = history
                            
                            -- Log the interaction
                            table.insert(InteractionLog, {
                                tick = tick,
                                npc1 = npc1.id,
                                npc2 = npc2.id,
                                location = location,
                                type = interaction_type,
                                relationship = history.relationship,
                                met_count = history.met_count
                            })
                            
                            interactions = interactions + 1
                        end
                    end
                end
            end
        end
    end
    
    -- Trim interaction log
    while #InteractionLog > MAX_INTERACTION_LOG do
        table.remove(InteractionLog, 1)
    end
    
    if interactions > 0 then
        print("💬 Processed " .. interactions .. " NPC interactions at tick " .. tick)
    end
    
    return interactions
end

-- =============================================================================
-- NPC ECONOMY PROCESSING
-- =============================================================================

-- Get wage for an archetype (case-insensitive lookup)
function get_wage_for_archetype(archetype)
    if not archetype then return ARCHETYPE_WAGES["default"] end
    local lower = string.lower(archetype)
    return ARCHETYPE_WAGES[lower] or ARCHETYPE_WAGES["default"]
end

-- Process NPC economy: wages at shift end, spending at social locations
function process_npc_economy(tick)
    local time = get_time_info(tick)
    local hour = time.hour
    local transactions = 0
    
    for npc_id, loc_data in pairs(NPCLocations) do
        local schedule = NPCSchedules[npc_id]
        if not schedule then goto continue end
        
        -- Initialize wallet if needed
        if not NPCWallets[npc_id] then
            NPCWallets[npc_id] = {
                balance = 500,  -- Starting balance
                income_tick = 0,
                spending_tick = 0
            }
        end
        
        local wallet = NPCWallets[npc_id]
        local shift_type = schedule.shift or "day"
        local shift = SHIFT_DEFINITIONS[shift_type]
        
        -- Pay wages at shift end (only once per day)
        local wage_hour = shift.finish or 17
        if hour == wage_hour and tick - wallet.income_tick >= TICKS_PER_DAY then
            local archetype = schedule.archetype or schedule.role or ""
            local wage = get_wage_for_archetype(archetype)
            
            wallet.balance = wallet.balance + wage
            wallet.income_tick = tick
            
            table.insert(NPCTransactionLog, {
                tick = tick,
                npc_id = npc_id,
                type = "wage",
                amount = wage,
                balance = wallet.balance
            })
            transactions = transactions + 1
        end
        
        -- Spend at social locations (30% chance when socializing)
        if loc_data.state == "socializing" and tick - wallet.spending_tick >= 10 then
            if seeded_chance(0.3, npc_id .. tostring(tick)) then
                local spending = math.min(wallet.balance, math.floor(20 + math.random() * 30))
                if spending > 0 then
                    wallet.balance = wallet.balance - spending
                    wallet.spending_tick = tick
                    
                    -- Add to city budget (businesses pay taxes)
                    CityBudget = CityBudget + math.floor(spending * TaxRate)
                    
                    table.insert(NPCTransactionLog, {
                        tick = tick,
                        npc_id = npc_id,
                        type = "spending",
                        amount = -spending,
                        location = loc_data.location,
                        balance = wallet.balance
                    })
                    transactions = transactions + 1
                end
            end
        end
        
        ::continue::
    end
    
    -- Trim transaction log
    while #NPCTransactionLog > MAX_TRANSACTION_LOG do
        table.remove(NPCTransactionLog, 1)
    end
    
    if transactions > 0 then
        print("💰 Processed " .. transactions .. " NPC economic transactions at tick " .. tick)
    end
    
    return transactions
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
    -- Skip if simulation is not running
    if SimulationStatus ~= "running" then
        -- Still respond but don't process
        return
    end
    
    -- Error recovery: wrap tick processing in pcall
    local success, error_msg = pcall(function()
        -- Advance world tick (with time compression if configured)
        local ticks_to_advance = TIME_COMPRESSION or 1
        for i = 1, ticks_to_advance do
            WorldTick = WorldTick + 1
            
            -- Day/year advancement
            if WorldTick % TICKS_PER_DAY == 0 then
                WorldDay = WorldDay + 1
                
                -- Log day transition
                if log_day_transition then
                    log_day_transition(WorldTick, WorldDay, WorldYear, {
                        population = PopulationCount,
                        budget = CityBudget,
                        active_npcs = ActiveNpcCount
                    })
                end
            end
            if WorldTick % TICKS_PER_YEAR == 0 then
                WorldYear = WorldYear + 1
            end
        end
        
        local time = get_time_info(WorldTick)
        
        -- 1. Check for world events
        local events = check_world_events(WorldTick)
        for _, event in ipairs(events) do
            broadcast_event(event)
            table.insert(ProcessedEvents, event)
            
            -- Log world events
            if log_world_event then
                log_world_event(WorldTick, event.type, event.type, {}, event)
            end
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
            
            -- Log economy update
            if log_budget_change then
                log_budget_change(WorldTick, "daily_cycle", 
                    CityBudget - tax_revenue + 10000, CityBudget, 
                    "tax_collection_and_expenses")
            end
            
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
        
        -- 5. Process utilities (power, water, internet)
        if Utilities then
            local utility_events = Utilities.on_tick(WorldTick, time.weather or "clear", {})
            if utility_events then
                for _, event in ipairs(utility_events.power or {}) do
                    broadcast_event(event)
                end
                for _, event in ipairs(utility_events.water or {}) do
                    broadcast_event(event)
                end
            end
        end
        
        -- 6. Log system tick
        if log_tick then
            log_tick(WorldTick, WorldDay, WorldYear, time.period, {
                population = PopulationCount,
                budget = CityBudget,
                active_npcs = ActiveNpcCount,
                pending_events = #events
            })
        end
        
        -- 7. Process NPC movements based on time of day
        local npc_movements = process_npc_movements(WorldTick)
        if npc_movements > 0 then
            broadcast_event({
                type = "npc_movements",
                tick = WorldTick,
                movements = npc_movements
            })
        end
        
        -- 8. Process NPC social interactions (when 2+ NPCs at same location)
        local npc_interactions = process_social_interactions(WorldTick)
        if npc_interactions > 0 then
            broadcast_event({
                type = "npc_interactions",
                tick = WorldTick,
                interactions = npc_interactions
            })
        end
        
        -- 9. Process NPC economy (wages and spending)
        local npc_transactions = process_npc_economy(WorldTick)
        if npc_transactions > 0 then
            broadcast_event({
                type = "npc_economy",
                tick = WorldTick,
                transactions = npc_transactions
            })
        end
        
        -- 7. Persist state snapshot every 60 ticks (1 hour in-game)
        if WorldTick % 60 == 0 then
            persist_state_snapshot()
        end
        
        -- Trim processed events (keep last 1000)
        while #ProcessedEvents > 1000 do
            table.remove(ProcessedEvents, 1)
        end
    end)
    
    -- Error handling: log error but don't crash
    if not success then
        -- Record error for health monitoring
        LastTickError = {
            tick = WorldTick,
            error = error_msg,
            timestamp = os.time and os.time() or WorldTick
        }
        TickErrorCount = (TickErrorCount or 0) + 1
        print("⚠️  TICK ERROR at " .. WorldTick .. ": " .. tostring(error_msg))
        
        -- If too many consecutive errors, pause for safety
        if TickErrorCount > 10 then
            SimulationStatus = "paused"
            print("🛑 SIMULATION PAUSED due to repeated errors")
        end
    else
        -- Reset error count on success
        TickErrorCount = 0
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

-- Get current time info
Handlers.add("get-time", Handlers.utils.hasMatchingTag("Action", "get-time"), function(msg)
    local time = get_time_info(WorldTick)
    ao.send({
        Target = msg.From,
        Action = "time-response",
        Data = json.encode({
            tick = WorldTick,
            day = WorldDay,
            year = WorldYear,
            hour = time.hour,
            period = time.period
        })
    })
end)

-- =============================================================================
-- MANUAL TICK ADVANCE (For Testing & Fast-Forward)
-- =============================================================================

Handlers.add("advance-tick", Handlers.utils.hasMatchingTag("Action", "advance-tick"), function(msg)
    local data = json.decode(msg.Data or "{}")
    local ticks = tonumber(data.ticks) or 1
    
    -- Safety limits: owner can advance 1000+, others limited to 100
    local is_owner = (msg.From == OwnerAddress)
    local max_ticks = is_owner and 10000 or 100
    
    if ticks < 1 then ticks = 1 end
    if ticks > max_ticks then ticks = max_ticks end
    
    -- Skip if paused (unless owner)
    if SimulationStatus ~= "running" and not is_owner then
        ao.send({
            Target = msg.From,
            Action = "advance-response",
            Data = json.encode({
                success = false,
                error = "Simulation is " .. SimulationStatus,
                tick = WorldTick
            })
        })
        return
    end
    
    local start_tick = WorldTick
    local start_day = WorldDay
    
    -- Fast-forward simulation
    for i = 1, ticks do
        WorldTick = WorldTick + 1
        
        -- Day/year transitions
        if WorldTick % TICKS_PER_DAY == 0 then
            WorldDay = WorldDay + 1
        end
        if WorldTick % TICKS_PER_YEAR == 0 then
            WorldYear = WorldYear + 1
        end
        -- Process NPC movements
        process_npc_movements(WorldTick)
        -- Process social interactions
        process_social_interactions(WorldTick)
        -- Process NPC economy
        process_npc_economy(WorldTick)
    end
    
    local time = get_time_info(WorldTick)
    
    ao.send({
        Target = msg.From,
        Action = "advance-response",
        Data = json.encode({
            success = true,
            previous_tick = start_tick,
            new_tick = WorldTick,
            advanced = ticks,
            previous_day = start_day,
            new_day = WorldDay,
            time = time
        })
    })
    
    print("⏩ Advanced " .. ticks .. " ticks: " .. start_tick .. " -> " .. WorldTick)
end)

-- =============================================================================
-- NPC LOCATION HANDLERS
-- =============================================================================

-- Get current NPC locations
Handlers.add("get-npc-locations", Handlers.utils.hasMatchingTag("Action", "get-npc-locations"), function(msg)
    local data = json.decode(msg.Data or "{}")
    local location_filter = data.location
    
    local result = {}
    for npc_id, loc_data in pairs(NPCLocations) do
        if not location_filter or loc_data.location == location_filter then
            result[npc_id] = loc_data
        end
    end
    
    ao.send({
        Target = msg.From,
        Action = "npc-locations-response",
        Data = json.encode({
            count = table_length(result),
            locations = result,
            tick = WorldTick,
            time = get_time_info(WorldTick)
        })
    })
end)

-- Get movement log
Handlers.add("get-movement-log", Handlers.utils.hasMatchingTag("Action", "get-movement-log"), function(msg)
    local data = json.decode(msg.Data or "{}")
    local limit = data.limit or 50
    local npc_filter = data.npc_id
    
    local result = {}
    for i = #MovementLog, math.max(1, #MovementLog - limit + 1), -1 do
        local entry = MovementLog[i]
        if not npc_filter or entry.npc_id == npc_filter then
            table.insert(result, entry)
        end
    end
    
    ao.send({
        Target = msg.From,
        Action = "movement-log-response",
        Data = json.encode({
            count = #result,
            movements = result
        })
    })
end)

-- Get NPC wallets and transaction log
Handlers.add("get-npc-wallets", Handlers.utils.hasMatchingTag("Action", "get-npc-wallets"), function(msg)
    local data = json.decode(msg.Data or "{}")
    local limit = data.limit or 20
    
    -- Get recent transactions
    local recent_transactions = {}
    local start_idx = math.max(1, #NPCTransactionLog - limit + 1)
    for i = start_idx, #NPCTransactionLog do
        table.insert(recent_transactions, NPCTransactionLog[i])
    end
    
    -- Get top wallets by balance
    local wallets = {}
    for npc_id, wallet in pairs(NPCWallets) do
        table.insert(wallets, {
            npc_id = npc_id,
            balance = wallet.balance,
            income_tick = wallet.income_tick,
            spending_tick = wallet.spending_tick
        })
    end
    
    -- Sort by balance (descending)
    table.sort(wallets, function(a, b) return a.balance > b.balance end)
    
    -- Return top 20
    local top_wallets = {}
    for i = 1, math.min(20, #wallets) do
        table.insert(top_wallets, wallets[i])
    end
    
    ao.send({
        Target = msg.From,
        Action = "npc-wallets-response",
        Data = json.encode({
            tick = WorldTick,
            total_wallets = table_length(NPCWallets),
            total_transactions = #NPCTransactionLog,
            top_wallets = top_wallets,
            recent_transactions = recent_transactions
        })
    })
end)

-- Load NPC schedules (call once to initialize from codec)
Handlers.add("load-npc-schedules", Handlers.utils.hasMatchingTag("Action", "load-npc-schedules"), function(msg)
    local data = json.decode(msg.Data or "{}")
    local schedules = data.schedules or {}
    local loaded = 0
    
    for _, npc in ipairs(schedules) do
        if npc.id then
            -- Auto-derive shift from archetype/role if not provided
            local derived_shift = npc.shift
            if not derived_shift and (npc.archetype or npc.role) then
                derived_shift = get_shift_for_archetype(npc.archetype, npc.role)
            end
            
            NPCSchedules[npc.id] = {
                home = npc.home or npc.location_home or "L001",
                work = npc.work or npc.workplace or npc.location_work or npc.home or "L001",
                social = npc.social or npc.location_frequent or {},
                shift = derived_shift or "day"  -- day, night, graveyard, evening, morning, flexible, always_on, split
            }
            -- Initialize location if not set
            if not NPCLocations[npc.id] then
                NPCLocations[npc.id] = {
                    location = npc.home or npc.location_home or "L001",
                    state = "idle",
                    since_tick = WorldTick
                }
            end
            loaded = loaded + 1
        end
    end
    
    ao.send({
        Target = msg.From,
        Action = "load-schedules-response",
        Data = json.encode({
            success = true,
            loaded = loaded,
            total_scheduled = table_length(NPCSchedules)
        })
    })
    
    print("📋 Loaded " .. loaded .. " NPC schedules")
end)

-- Get NPC social interactions and relationships
Handlers.add("get-interactions", Handlers.utils.hasMatchingTag("Action", "get-interactions"), function(msg)
    local data = json.decode(msg.Data or "{}")
    local limit = data.limit or 50
    
    -- Get recent interactions
    local recent = {}
    local start_idx = math.max(1, #InteractionLog - limit + 1)
    for i = start_idx, #InteractionLog do
        table.insert(recent, InteractionLog[i])
    end
    
    -- Get top relationships (sorted by relationship strength)
    local relationships = {}
    for key, history in pairs(NPCSocialHistory) do
        table.insert(relationships, {
            key = key,
            met_count = history.met_count,
            relationship = history.relationship,
            last_tick = history.last_tick
        })
    end
    
    -- Sort by relationship strength (descending)
    table.sort(relationships, function(a, b) return a.relationship > b.relationship end)
    
    -- Return top 20 relationships
    local top_relationships = {}
    for i = 1, math.min(20, #relationships) do
        table.insert(top_relationships, relationships[i])
    end
    
    ao.send({
        Target = msg.From,
        Action = "interactions-response",
        Data = json.encode({
            tick = WorldTick,
            total_relationships = table_length(NPCSocialHistory),
            total_interactions = #InteractionLog,
            recent_interactions = recent,
            top_relationships = top_relationships
        })
    })
end)

-- =============================================================================
-- CHAT MEMORY HANDLERS (Persisted)
-- =============================================================================

-- Store a chat message
Handlers.add("store-chat", Handlers.utils.hasMatchingTag("Action", "store-chat"), function(msg)
    local data = json.decode(msg.Data or "{}")
    local user_id = data.user_id
    local npc_id = data.npc_id
    local message = data.message or ""
    local response = data.response or ""
    
    if not user_id or not npc_id then
        ao.send({
            Target = msg.From,
            Action = "store-chat-response",
            Data = json.encode({ success = false, error = "Missing user_id or npc_id" })
        })
        return
    end
    
    -- Initialize conversation storage
    NPCConversations[npc_id] = NPCConversations[npc_id] or {}
    NPCConversations[npc_id][user_id] = NPCConversations[npc_id][user_id] or { messages = {} }
    
    -- Store the message
    table.insert(NPCConversations[npc_id][user_id].messages, {
        tick = WorldTick,
        user = message,
        npc = response,
        timestamp = os.time and os.time() or WorldTick
    })
    
    -- Trim old messages if over limit
    local conv = NPCConversations[npc_id][user_id].messages
    while #conv > MAX_MESSAGES_PER_CONVERSATION do
        table.remove(conv, 1)
    end
    
    NPCConversations[npc_id][user_id].last_tick = WorldTick
    
    -- Remember user name if provided
    if data.user_name and data.user_name ~= "" then
        UserMemory[user_id] = UserMemory[user_id] or {}
        UserMemory[user_id].name = data.user_name
        UserMemory[user_id].last_seen = WorldTick
        if not UserMemory[user_id].first_seen then
            UserMemory[user_id].first_seen = WorldTick
        end
    end
    
    ao.send({
        Target = msg.From,
        Action = "store-chat-response",
        Data = json.encode({ 
            success = true, 
            messages_stored = #NPCConversations[npc_id][user_id].messages,
            tick = WorldTick
        })
    })
    
    print("💬 Stored chat: " .. npc_id .. " <-> " .. user_id)
end)

-- Get chat history for a user-NPC pair
Handlers.add("get-chat-history", Handlers.utils.hasMatchingTag("Action", "get-chat-history"), function(msg)
    local data = json.decode(msg.Data or "{}")
    local user_id = data.user_id
    local npc_id = data.npc_id
    
    local history = {}
    local user_name = nil
    
    if user_id and npc_id and NPCConversations[npc_id] and NPCConversations[npc_id][user_id] then
        history = NPCConversations[npc_id][user_id].messages or {}
    end
    
    if user_id and UserMemory[user_id] then
        user_name = UserMemory[user_id].name
    end
    
    ao.send({
        Target = msg.From,
        Action = "chat-history-response",
        Data = json.encode({
            npc_id = npc_id,
            user_id = user_id,
            user_name = user_name,
            message_count = #history,
            messages = history
        })
    })
end)

-- Remember user name
Handlers.add("remember-user", Handlers.utils.hasMatchingTag("Action", "remember-user"), function(msg)
    local data = json.decode(msg.Data or "{}")
    local user_id = data.user_id
    local user_name = data.name
    
    if not user_id then
        ao.send({
            Target = msg.From,
            Action = "remember-user-response",
            Data = json.encode({ success = false, error = "Missing user_id" })
        })
        return
    end
    
    UserMemory[user_id] = UserMemory[user_id] or {}
    if user_name and user_name ~= "" then
        UserMemory[user_id].name = user_name
    end
    UserMemory[user_id].last_seen = WorldTick
    if not UserMemory[user_id].first_seen then
        UserMemory[user_id].first_seen = WorldTick
    end
    
    ao.send({
        Target = msg.From,
        Action = "remember-user-response",
        Data = json.encode({ 
            success = true, 
            user_id = user_id,
            name = UserMemory[user_id].name,
            first_seen = UserMemory[user_id].first_seen
        })
    })
end)

-- Get user info
Handlers.add("get-user", Handlers.utils.hasMatchingTag("Action", "get-user"), function(msg)
    local data = json.decode(msg.Data or "{}")
    local user_id = data.user_id
    
    local user_info = UserMemory[user_id] or {}
    
    ao.send({
        Target = msg.From,
        Action = "user-response",
        Data = json.encode({
            user_id = user_id,
            name = user_info.name,
            first_seen = user_info.first_seen,
            last_seen = user_info.last_seen,
            known = (user_info.name ~= nil)
        })
    })
end)

-- Get all NPCs
Handlers.add("get-all-npcs", Handlers.utils.hasMatchingTag("Action", "get-all-npcs"), function(msg)
    ao.send({
        Target = msg.From,
        Action = "npcs-response",
        Data = json.encode(ALL_NPCS or {})
    })
end)

-- Get specific NPC by ID
Handlers.add("get-npc", Handlers.utils.hasMatchingTag("Action", "get-npc"), function(msg)
    local data = json.decode(msg.Data or "{}")
    local npc_id = data.npc_id
    local npc = ALL_NPCS and ALL_NPCS[npc_id] or nil
    ao.send({
        Target = msg.From,
        Action = "npc-response",
        Data = json.encode(npc or {error = "NPC not found"})
    })
end)

-- Get NPCs by district
Handlers.add("get-district-npcs", Handlers.utils.hasMatchingTag("Action", "get-district-npcs"), function(msg)
    local data = json.decode(msg.Data or "{}")
    local district_id = data.district_id
    local result = {}
    
    if ALL_NPCS then
        for id, npc in pairs(ALL_NPCS) do
            if npc.home == district_id or npc.workplace == district_id then
                table.insert(result, npc)
            end
        end
    end
    
    ao.send({
        Target = msg.From,
        Action = "district-npcs-response",
        Data = json.encode(result)
    })
end)

-- Get founding NPCs (the 12 canonical characters)
Handlers.add("get-founding-npcs", Handlers.utils.hasMatchingTag("Action", "get-founding-npcs"), function(msg)
    ao.send({
        Target = msg.From,
        Action = "founding-npcs-response",
        Data = json.encode(FOUNDING_NPCS or {})
    })
end)

-- Get all districts
Handlers.add("get-districts", Handlers.utils.hasMatchingTag("Action", "get-districts"), function(msg)
    ao.send({
        Target = msg.From,
        Action = "districts-response",
        Data = json.encode(Districts or {})
    })
end)

-- Get layer info (for multiverse)
Handlers.add("get-layer-info", Handlers.utils.hasMatchingTag("Action", "get-layer-info"), function(msg)
    ao.send({
        Target = msg.From,
        Action = "layer-info-response",
        Data = json.encode({
            layer_id = LAYER_ID or "layer_00_testnet",
            name = LAYER_NAME or "RE:ECHO City Testnet",
            population = PopulationCount,
            status = "active"
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
-- SIMULATION CONTROL HANDLERS (Kill Switch / Pause / Freeze)
-- =============================================================================

-- Check if sender is owner
function is_owner(sender)
    return OwnerAddress == nil or sender == OwnerAddress
end

-- Pause simulation (can be resumed)
Handlers.add("pause-simulation", Handlers.utils.hasMatchingTag("Action", "pause-simulation"), function(msg)
    if not is_owner(msg.From) then
        ao.send({ Target = msg.From, Action = "error", Data = "Unauthorized" })
        return
    end
    SimulationStatus = "paused"
    ao.send({
        Target = msg.From,
        Action = "simulation-paused",
        Data = json.encode({ status = "paused", tick = WorldTick })
    })
    print("⏸️  Simulation PAUSED at tick " .. WorldTick)
end)

-- Resume simulation
Handlers.add("resume-simulation", Handlers.utils.hasMatchingTag("Action", "resume-simulation"), function(msg)
    if not is_owner(msg.From) then
        ao.send({ Target = msg.From, Action = "error", Data = "Unauthorized" })
        return
    end
    if SimulationStatus == "terminated" then
        ao.send({ Target = msg.From, Action = "error", Data = "Cannot resume terminated simulation" })
        return
    end
    SimulationStatus = "running"
    ao.send({
        Target = msg.From,
        Action = "simulation-resumed",
        Data = json.encode({ status = "running", tick = WorldTick })
    })
    print("▶️  Simulation RESUMED at tick " .. WorldTick)
end)

-- Freeze simulation (permanent pause, queries still work)
Handlers.add("freeze-simulation", Handlers.utils.hasMatchingTag("Action", "freeze-simulation"), function(msg)
    if not is_owner(msg.From) then
        ao.send({ Target = msg.From, Action = "error", Data = "Unauthorized" })
        return
    end
    SimulationStatus = "frozen"
    ao.send({
        Target = msg.From,
        Action = "simulation-frozen",
        Data = json.encode({ status = "frozen", tick = WorldTick })
    })
    print("❄️  Simulation FROZEN at tick " .. WorldTick)
end)

-- KILL SWITCH - Terminate simulation permanently (password only)
-- Send: { Action = "terminate-simulation", Data = json.encode({key = "your_password"}) }
Handlers.add("terminate-simulation", Handlers.utils.hasMatchingTag("Action", "terminate-simulation"), function(msg)
    -- Password-only verification (no wallet required)
    local data = json.decode(msg.Data or "{}")
    local secret_hash = 1879975284  -- Hashed password (safe to commit)
    
    if not data.key then
        ao.send({ Target = msg.From, Action = "error", Data = "Password required" })
        return
    end
    
    -- Hash the provided password
    local hash = 0
    for i = 1, #data.key do
        hash = (hash * 31 + string.byte(data.key, i)) % 2147483647
    end
    
    if hash ~= secret_hash then
        ao.send({ Target = msg.From, Action = "error", Data = "Invalid password" })
        return
    end
    
    SimulationStatus = "terminated"
    ao.send({
        Target = msg.From,
        Action = "simulation-terminated",
        Data = json.encode({ 
            status = "terminated", 
            final_tick = WorldTick,
            message = "Layer archived permanently."
        })
    })
    print("☠️  SIMULATION TERMINATED at tick " .. WorldTick)
end)

-- Get simulation status
Handlers.add("get-simulation-status", Handlers.utils.hasMatchingTag("Action", "get-simulation-status"), function(msg)
    ao.send({
        Target = msg.From,
        Action = "simulation-status",
        Data = json.encode({
            status = SimulationStatus,
            tick = WorldTick,
            day = WorldDay,
            population = PopulationCount
        })
    })
end)

-- Get simulation health (comprehensive monitoring)
Handlers.add("get-health", Handlers.utils.hasMatchingTag("Action", "get-health"), function(msg)
    local time = get_time_info(WorldTick)
    local district_count = 0
    for _ in pairs(Districts) do district_count = district_count + 1 end
    
    ao.send({
        Target = msg.From,
        Action = "health-response",
        Data = json.encode({
            -- Status
            status = SimulationStatus,
            healthy = SimulationStatus == "running" and (TickErrorCount or 0) == 0,
            
            -- Timing
            tick = WorldTick,
            day = WorldDay,
            year = WorldYear,
            time_period = time.period,
            
            -- Population
            population = PopulationCount,
            active_npcs = ActiveNpcCount,
            
            -- Economy
            city_budget = CityBudget,
            tax_rate = TaxRate,
            
            -- Infrastructure
            districts_registered = district_count,
            has_ai_oracle = AiOracle ~= nil,
            has_event_bus = EventBus ~= nil,
            has_utilities = Utilities ~= nil,
            
            -- Utilities (if available)
            utilities = Utilities and {
                power_load = Utilities.Power.current_load,
                grid_capacity = Utilities.Power.grid_capacity,
                water_rationing = Utilities.Water.rationing,
                water_main = Utilities.Water.reservoirs.main,
                water_recycled = Utilities.Water.reservoirs.recycled,
                isps = {
                    sacredlink = Utilities.Internet.isps.sacredlink.status,
                    omniconnect = Utilities.Internet.isps.omniconnect.status,
                    darkwave = Utilities.Internet.isps.darkwave.status,
                    ghostnet = Utilities.Internet.isps.ghostnet.status
                }
            } or nil,
            
            -- Errors
            error_count = TickErrorCount or 0,
            last_error = LastTickError,
            
            -- Events
            pending_events = #PendingEvents,
            processed_events = #ProcessedEvents
        })
    })
end)

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
    seeded_choice = seeded_choice,
    is_owner = is_owner
}
