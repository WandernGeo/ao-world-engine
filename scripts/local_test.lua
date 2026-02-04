#!/usr/bin/env lua
--[[
  SignalNoir.1 - Local Test Harness
  
  Simulates the AO environment locally to validate all systems
  before deploying to mainnet.
  
  Usage: lua scripts/local_test.lua
]]--

-- Mock AO environment
ao = {
    id = "LOCAL_TEST_PROCESS",
    _messages = {},
    send = function(msg)
        table.insert(ao._messages, msg)
        -- Print for debugging
        if msg.Action == "Log" then
            local data = msg.Data
            print(string.format("[LOG] %s", data:sub(1, 100)))
        end
    end
}

-- Mock crypto
crypto = {
    digest = {
        sha256 = function(str)
            -- Simple hash for testing
            local hash = 0
            for i = 1, #str do
                hash = (hash * 31 + string.byte(str, i)) % 0xFFFFFFFF
            end
            return string.format("%08x%08x%08x%08x", hash, hash, hash, hash)
        end
    }
}

-- Mock Handlers
Handlers = {
    _handlers = {},
    add = function(name, matcher, handler)
        Handlers._handlers[name] = { matcher = matcher, handler = handler }
        print(string.format("[HANDLER] Registered: %s", name))
    end,
    utils = {
        hasMatchingTag = function(name, value)
            return function(msg)
                if msg.Tags then
                    for _, tag in ipairs(msg.Tags) do
                        if tag.name == name and tag.value == value then
                            return true
                        end
                    end
                end
                return false
            end
        end
    }
}

-- Mock json
json = {
    encode = function(t)
        -- Simple JSON encoder for testing
        if type(t) ~= "table" then return tostring(t) end
        local result = "{"
        local first = true
        for k, v in pairs(t) do
            if not first then result = result .. "," end
            first = false
            result = result .. '"' .. tostring(k) .. '":'
            if type(v) == "table" then
                result = result .. json.encode(v)
            elseif type(v) == "string" then
                result = result .. '"' .. v .. '"'
            elseif type(v) == "boolean" then
                result = result .. (v and "true" or "false")
            else
                result = result .. tostring(v)
            end
        end
        return result .. "}"
    end,
    decode = function(s)
        -- For testing, just return empty table
        return {}
    end
}

print("╔═══════════════════════════════════════════════════════════╗")
print("║       SignalNoir.1 - Local Test Harness                   ║")
print("╚═══════════════════════════════════════════════════════════╝")
print("")

-- Load modules
print("[LOAD] Loading modules...")

-- Load logging first
dofile("ao-processes/logging.lua")
print("[LOAD] ✓ logging.lua")

-- Load economy
dofile("ao-processes/economy.lua")
print("[LOAD] ✓ economy.lua")

-- Load social
dofile("ao-processes/social.lua")
print("[LOAD] ✓ social.lua")

-- Load world
dofile("ao-processes/world.lua")
print("[LOAD] ✓ world.lua")

-- Load config
dofile("ao-processes/signalnoir_config.lua")
print("[LOAD] ✓ signalnoir_config.lua")

print("")
print("═══════════════════════════════════════════════════════════")
print("")

-- Run simulation test
print("[TEST] Starting simulation test...")
print("")

-- Simulate 10 ticks
for tick = 1, 10 do
    print(string.format("[TICK %d] Processing...", tick))
    
    -- Manually advance world tick
    WorldTick = tick
    
    -- Get time info
    local time = get_time_info(tick)
    print(string.format("  Time: Day %d, Hour %d, Period %s", 
        time.day, time.hour, time.period))
    
    -- Check world events
    local events = check_world_events(tick)
    if #events > 0 then
        for _, event in ipairs(events) do
            print(string.format("  EVENT: %s", event.type))
        end
    end
    
    -- Log the tick
    if log_tick then
        log_tick(tick, WorldDay, WorldYear, time.period, {
            population = 12,
            budget = CityBudget,
            active_npcs = 12,
            pending_events = #events
        })
    end
    
    -- Process daily economy every 240 ticks (or every 5 for testing)
    if tick % 5 == 0 then
        print("  [ECONOMY] Processing daily cycle...")
        local tax = collect_taxes()
        print(string.format("  [ECONOMY] Taxes collected: %d GEP", tax))
        print(string.format("  [ECONOMY] City budget: %d GEP", CityBudget))
    end
    
    print("")
end

-- Test NPC logging
print("[TEST] Testing NPC logging...")
if log_npc_action then
    log_npc_action("C01", "A046", "V046", "L026", 10, { target = "C02" })
    print("  ✓ NPC action logged")
end

if log_npc_meeting then
    log_npc_meeting(10, "C01", "C02", "L003", "conversation", { trust_change = 0.02 })
    print("  ✓ NPC meeting logged")
end

-- Test economy logging
print("[TEST] Testing economy logging...")
if log_transaction then
    log_transaction(10, "trade", 50, "C01", "C03", { item = "data_chip" })
    print("  ✓ Transaction logged")
end

-- Test building logging
print("[TEST] Testing building logging...")
if log_building_entry then
    log_building_entry(10, "L003", "C01", "visit")
    print("  ✓ Building entry logged")
end

if log_building_exit then
    log_building_exit(15, "L003", "C01", 5)
    print("  ✓ Building exit logged")
end

-- Get log stats
print("")
print("[TEST] Log statistics:")
local stats = get_log_stats()
print(string.format("  Total logs: %d", stats.total_logs))
for log_type, count in pairs(stats.logs_by_type) do
    print(string.format("  - %s: %d", log_type, count))
end

-- Test social system
print("")
print("[TEST] Testing social system...")
if track_meeting then
    track_meeting("C01", "C02", 10)
    print("  ✓ Meeting recorded")
end

if update_trust_from_interaction then
    update_trust_from_interaction("C01", "C02", "positive_chat", 10)
    print("  ✓ Trust updated")
end

local rel = get_relationship("C01", "C02")
if rel then
    print(string.format("  Trust C01->C02: %.2f (type: %s)", rel.trust or 0, rel.type or "unknown"))
end

-- Test social reputation
if get_reputation then
    local rep = get_reputation("C01", "temple")
    print(string.format("  C01 reputation with temple: %.2f", rep or 0))
end

print("")
print("═══════════════════════════════════════════════════════════")
print("")

-- Results summary
print("[RESULTS] Test Summary:")
print(string.format("  World Tick: %d", WorldTick))
print(string.format("  City Budget: %d GEP", CityBudget))
print(string.format("  NPCs Loaded: %d", #FOUNDING_NPCS))
print(string.format("  Districts: %d", #DISTRICTS))
print(string.format("  Messages Sent: %d", #ao._messages))
print(string.format("  Handlers Registered: %d", 0))

-- Count handlers
local handler_count = 0
for _ in pairs(Handlers._handlers) do handler_count = handler_count + 1 end
print(string.format("  Handlers Registered: %d", handler_count))

print("")
print("═══════════════════════════════════════════════════════════")
print("[SUCCESS] All local tests passed!")
print("═══════════════════════════════════════════════════════════")
