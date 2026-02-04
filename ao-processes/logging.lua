--[[
  AO World Engine - Logging System
  
  Comprehensive logging for SignalNoir.1 simulation.
  Every NPC action, building event, transaction, and system tick is logged.
  
  Logs are emitted as AO messages and stored permanently on Arweave.
]]--

local json = require("json")

-- =============================================================================
-- LOG STORAGE
-- =============================================================================

-- In-memory log buffers (last N entries per category)
LogBuffers = LogBuffers or {
    npc_action = {},
    npc_meeting = {},
    economy_tx = {},
    building_event = {},
    world_event = {},
    system_tick = {}
}

-- Buffer sizes per category
LOG_BUFFER_SIZES = {
    npc_action = 500,
    npc_meeting = 200,
    economy_tx = 300,
    building_event = 200,
    world_event = 100,
    system_tick = 1000
}

-- Statistics counters
LogStats = LogStats or {
    total_logs = 0,
    logs_by_type = {},
    first_log_tick = 0,
    last_log_tick = 0
}

-- =============================================================================
-- CORE LOGGING FUNCTION
-- =============================================================================

function log_event(log_type, tick, data)
    local entry = {
        tick = tick,
        type = log_type,
        timestamp = tick,
        data = data
    }
    
    -- Add to buffer
    local buffer = LogBuffers[log_type]
    if buffer then
        table.insert(buffer, entry)
        
        -- Trim buffer if too large
        local max_size = LOG_BUFFER_SIZES[log_type] or 100
        while #buffer > max_size do
            table.remove(buffer, 1)
        end
    end
    
    -- Update stats
    LogStats.total_logs = LogStats.total_logs + 1
    LogStats.logs_by_type[log_type] = (LogStats.logs_by_type[log_type] or 0) + 1
    LogStats.last_log_tick = tick
    if LogStats.first_log_tick == 0 then
        LogStats.first_log_tick = tick
    end
    
    -- Emit as AO message (stored on Arweave)
    ao.send({
        Target = ao.id,
        Action = "Log",
        Tags = {
            { name = "Log-Type", value = log_type },
            { name = "Tick", value = tostring(tick) },
            { name = "World", value = WORLD_NAME or "SignalNoir.1" }
        },
        Data = json.encode(entry)
    })
    
    return entry
end

-- =============================================================================
-- NPC LOGGING
-- =============================================================================

function log_npc_action(npc_id, action_code, verb_code, location, tick, details)
    return log_event("npc_action", tick, {
        npc_id = npc_id,
        action = action_code,
        verb = verb_code,
        location = location,
        details = details or {}
    })
end

function log_npc_movement(npc_id, from_location, to_location, tick, reason)
    return log_event("npc_action", tick, {
        npc_id = npc_id,
        action = "move",
        from = from_location,
        to = to_location,
        reason = reason or "schedule"
    })
end

function log_npc_meeting(tick, npc1_id, npc2_id, location, interaction_type, outcome)
    return log_event("npc_meeting", tick, {
        participants = { npc1_id, npc2_id },
        location = location,
        interaction = interaction_type,
        outcome = outcome or {}
    })
end

function log_npc_conversation(tick, npc1_id, npc2_id, location, dialogue_summary, trust_change)
    return log_event("npc_meeting", tick, {
        participants = { npc1_id, npc2_id },
        location = location,
        type = "conversation",
        summary = dialogue_summary,
        trust_delta = trust_change
    })
end

function log_npc_state_change(npc_id, tick, field, old_value, new_value, reason)
    return log_event("npc_action", tick, {
        npc_id = npc_id,
        action = "state_change",
        field = field,
        old_value = old_value,
        new_value = new_value,
        reason = reason
    })
end

-- =============================================================================
-- BUILDING LOGGING
-- =============================================================================

function log_building_entry(tick, building_id, npc_id, entry_type)
    return log_event("building_event", tick, {
        building_id = building_id,
        npc_id = npc_id,
        event = "entry",
        entry_type = entry_type or "standard"  -- standard, work, residence, visit
    })
end

function log_building_exit(tick, building_id, npc_id, duration_ticks)
    return log_event("building_event", tick, {
        building_id = building_id,
        npc_id = npc_id,
        event = "exit",
        duration = duration_ticks
    })
end

function log_building_state_change(tick, building_id, field, old_value, new_value)
    return log_event("building_event", tick, {
        building_id = building_id,
        event = "state_change",
        field = field,
        old_value = old_value,
        new_value = new_value
    })
end

-- =============================================================================
-- ECONOMY LOGGING
-- =============================================================================

function log_transaction(tick, tx_type, amount, from_entity, to_entity, details)
    return log_event("economy_tx", tick, {
        tx_type = tx_type,  -- tax, trade, salary, ubi, expense
        amount = amount,
        from = from_entity,
        to = to_entity,
        details = details or {}
    })
end

function log_tax_collection(tick, npc_id, tax_type, amount, balance_after)
    return log_event("economy_tx", tick, {
        tx_type = "tax",
        tax_type = tax_type,  -- income, property, sales, temple_tithe
        npc_id = npc_id,
        amount = amount,
        balance_after = balance_after
    })
end

function log_salary_payment(tick, npc_id, employer_id, job_code, amount)
    return log_event("economy_tx", tick, {
        tx_type = "salary",
        npc_id = npc_id,
        employer = employer_id,
        job = job_code,
        amount = amount
    })
end

function log_budget_change(tick, category, old_amount, new_amount, reason)
    return log_event("economy_tx", tick, {
        tx_type = "budget",
        category = category,
        old_amount = old_amount,
        new_amount = new_amount,
        reason = reason
    })
end

-- =============================================================================
-- WORLD EVENT LOGGING
-- =============================================================================

function log_world_event(tick, event_type, event_name, affected_entities, details)
    return log_event("world_event", tick, {
        event_type = event_type,
        event_name = event_name,
        affected = affected_entities or {},
        details = details or {}
    })
end

function log_economic_event(tick, event_type, duration_days, effects)
    return log_event("world_event", tick, {
        event_type = "economic",
        event_name = event_type,
        duration_days = duration_days,
        effects = effects
    })
end

function log_day_transition(tick, day_number, year_number, summary)
    return log_event("world_event", tick, {
        event_type = "day_transition",
        day = day_number,
        year = year_number,
        summary = summary or {}
    })
end

-- =============================================================================
-- SYSTEM TICK LOGGING
-- =============================================================================

function log_tick(tick, day, year, time_period, stats)
    return log_event("system_tick", tick, {
        day = day,
        year = year,
        time_period = time_period,
        population = stats.population or 0,
        budget = stats.budget or 0,
        active_npcs = stats.active_npcs or 0,
        pending_events = stats.pending_events or 0
    })
end

-- =============================================================================
-- LOG RETRIEVAL
-- =============================================================================

function get_logs(log_type, limit, since_tick)
    local buffer = LogBuffers[log_type]
    if not buffer then return {} end
    
    local result = {}
    local count = 0
    local max_count = limit or 100
    
    -- Iterate backwards (most recent first)
    for i = #buffer, 1, -1 do
        local entry = buffer[i]
        if not since_tick or entry.tick >= since_tick then
            table.insert(result, entry)
            count = count + 1
            if count >= max_count then break end
        end
    end
    
    return result
end

function get_npc_history(npc_id, limit)
    local result = {}
    local count = 0
    local max_count = limit or 50
    
    -- Search all relevant buffers
    for _, buffer in pairs({ LogBuffers.npc_action, LogBuffers.npc_meeting }) do
        for i = #buffer, 1, -1 do
            local entry = buffer[i]
            local data = entry.data
            
            -- Check if NPC is involved
            local involved = false
            if data.npc_id == npc_id then
                involved = true
            elseif data.participants then
                for _, p in ipairs(data.participants) do
                    if p == npc_id then 
                        involved = true 
                        break 
                    end
                end
            end
            
            if involved then
                table.insert(result, entry)
                count = count + 1
                if count >= max_count then break end
            end
        end
        if count >= max_count then break end
    end
    
    -- Sort by tick descending
    table.sort(result, function(a, b) return a.tick > b.tick end)
    
    return result
end

function get_building_history(building_id, limit)
    local result = {}
    local count = 0
    local max_count = limit or 50
    
    local buffer = LogBuffers.building_event
    for i = #buffer, 1, -1 do
        local entry = buffer[i]
        if entry.data.building_id == building_id then
            table.insert(result, entry)
            count = count + 1
            if count >= max_count then break end
        end
    end
    
    return result
end

function get_log_stats()
    return {
        total_logs = LogStats.total_logs,
        logs_by_type = LogStats.logs_by_type,
        first_tick = LogStats.first_log_tick,
        last_tick = LogStats.last_log_tick,
        buffer_sizes = {}
    }
end

-- =============================================================================
-- HANDLERS
-- =============================================================================

-- Get logs by type
Handlers.add("get-logs", Handlers.utils.hasMatchingTag("Action", "get-logs"), function(msg)
    local data = json.decode(msg.Data) or {}
    local log_type = data.type or "npc_action"
    local limit = data.limit or 50
    local since_tick = data.since_tick
    
    local logs = get_logs(log_type, limit, since_tick)
    
    ao.send({
        Target = msg.From,
        Action = "logs-response",
        Data = json.encode({
            type = log_type,
            count = #logs,
            logs = logs
        })
    })
end)

-- Get NPC history
Handlers.add("get-npc-history", Handlers.utils.hasMatchingTag("Action", "get-npc-history"), function(msg)
    local data = json.decode(msg.Data) or {}
    local npc_id = data.npc_id
    local limit = data.limit or 50
    
    if not npc_id then
        ao.send({
            Target = msg.From,
            Action = "error",
            Data = json.encode({ error = "npc_id required" })
        })
        return
    end
    
    local history = get_npc_history(npc_id, limit)
    
    ao.send({
        Target = msg.From,
        Action = "npc-history-response",
        Data = json.encode({
            npc_id = npc_id,
            count = #history,
            history = history
        })
    })
end)

-- Get building history
Handlers.add("get-building-history", Handlers.utils.hasMatchingTag("Action", "get-building-history"), function(msg)
    local data = json.decode(msg.Data) or {}
    local building_id = data.building_id
    local limit = data.limit or 50
    
    if not building_id then
        ao.send({
            Target = msg.From,
            Action = "error",
            Data = json.encode({ error = "building_id required" })
        })
        return
    end
    
    local history = get_building_history(building_id, limit)
    
    ao.send({
        Target = msg.From,
        Action = "building-history-response",
        Data = json.encode({
            building_id = building_id,
            count = #history,
            history = history
        })
    })
end)

-- Get log statistics
Handlers.add("get-log-stats", Handlers.utils.hasMatchingTag("Action", "get-log-stats"), function(msg)
    local stats = get_log_stats()
    
    -- Add buffer sizes
    for log_type, buffer in pairs(LogBuffers) do
        stats.buffer_sizes[log_type] = #buffer
    end
    
    ao.send({
        Target = msg.From,
        Action = "log-stats-response",
        Data = json.encode(stats)
    })
end)

-- =============================================================================
-- MODULE EXPORT
-- =============================================================================

return {
    log_event = log_event,
    log_npc_action = log_npc_action,
    log_npc_movement = log_npc_movement,
    log_npc_meeting = log_npc_meeting,
    log_npc_conversation = log_npc_conversation,
    log_npc_state_change = log_npc_state_change,
    log_building_entry = log_building_entry,
    log_building_exit = log_building_exit,
    log_building_state_change = log_building_state_change,
    log_transaction = log_transaction,
    log_tax_collection = log_tax_collection,
    log_salary_payment = log_salary_payment,
    log_budget_change = log_budget_change,
    log_world_event = log_world_event,
    log_economic_event = log_economic_event,
    log_day_transition = log_day_transition,
    log_tick = log_tick,
    get_logs = get_logs,
    get_npc_history = get_npc_history,
    get_building_history = get_building_history,
    get_log_stats = get_log_stats
}
