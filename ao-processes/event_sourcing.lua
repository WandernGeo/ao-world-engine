--[[
  AO World Engine - Event Sourcing System
  
  CSM-inspired event sourcing for simulation state persistence.
  All state changes are recorded as events for Arweave persistence
  and time-travel debugging.
  
  Source: Cities Skylines Multiplayer (CSM) - https://github.com/CitiesSkylinesMultiplayer/CSM
  See: docs/CITY_SIMULATION_RESEARCH.md
]]--

local json = require("json")

-- =============================================================================
-- EVENT LOG
-- =============================================================================

-- All events that have occurred
EVENT_LOG = {}

-- Current event index (for time-travel)
CURRENT_EVENT_INDEX = 0

-- Event types
EVENT_TYPES = {
    -- World events
    WORLD_TICK = "world_tick",
    WORLD_INIT = "world_init",
    
    -- NPC events
    NPC_SPAWNED = "npc_spawned",
    NPC_MOVED = "npc_moved",
    NPC_ACTION = "npc_action",
    NPC_MOOD_CHANGED = "npc_mood_changed",
    NPC_INTERACTION = "npc_interaction",
    
    -- Economy events
    TRANSACTION = "transaction",
    WAGE_PAID = "wage_paid",
    TAX_COLLECTED = "tax_collected",
    
    -- Social events
    RELATIONSHIP_CHANGED = "relationship_changed",
    GOSSIP_SPREAD = "gossip_spread",
    
    -- District events
    BUILDING_ACTIVITY = "building_activity",
    DISTRICT_UPDATE = "district_update",
    
    -- System events
    SNAPSHOT_CREATED = "snapshot_created",
    CRON_EXECUTED = "cron_executed"
}

-- =============================================================================
-- EVENT CREATION
-- =============================================================================

-- Create and log an event
function log_event(event_type, payload, actor_id)
    local event = {
        id = #EVENT_LOG + 1,
        type = event_type,
        timestamp = os.time(),
        tick = WorldTick or 0,
        actor = actor_id,
        payload = payload
    }
    
    table.insert(EVENT_LOG, event)
    CURRENT_EVENT_INDEX = #EVENT_LOG
    
    return event
end

-- Create event without adding to log (for preview)
function create_event(event_type, payload, actor_id)
    return {
        id = nil,
        type = event_type,
        timestamp = os.time(),
        tick = WorldTick or 0,
        actor = actor_id,
        payload = payload
    }
end

-- =============================================================================
-- EVENT QUERIES
-- =============================================================================

-- Get events by type
function get_events_by_type(event_type, limit)
    limit = limit or 100
    local results = {}
    
    for i = #EVENT_LOG, 1, -1 do
        if EVENT_LOG[i].type == event_type then
            table.insert(results, EVENT_LOG[i])
            if #results >= limit then
                break
            end
        end
    end
    
    return results
end

-- Get events by actor
function get_events_by_actor(actor_id, limit)
    limit = limit or 100
    local results = {}
    
    for i = #EVENT_LOG, 1, -1 do
        if EVENT_LOG[i].actor == actor_id then
            table.insert(results, EVENT_LOG[i])
            if #results >= limit then
                break
            end
        end
    end
    
    return results
end

-- Get events in time range
function get_events_in_range(start_tick, end_tick)
    local results = {}
    
    for _, event in ipairs(EVENT_LOG) do
        if event.tick >= start_tick and event.tick <= end_tick then
            table.insert(results, event)
        end
    end
    
    return results
end

-- Get recent events
function get_recent_events(count)
    count = count or 50
    local results = {}
    
    local start = math.max(1, #EVENT_LOG - count + 1)
    for i = start, #EVENT_LOG do
        table.insert(results, EVENT_LOG[i])
    end
    
    return results
end

-- =============================================================================
-- TIME TRAVEL
-- =============================================================================

-- Get event at specific index
function get_event_at(index)
    if index < 1 or index > #EVENT_LOG then
        return nil
    end
    return EVENT_LOG[index]
end

-- Get state snapshot at tick
function get_events_up_to_tick(tick)
    local results = {}
    
    for _, event in ipairs(EVENT_LOG) do
        if event.tick <= tick then
            table.insert(results, event)
        end
    end
    
    return results
end

-- =============================================================================
-- SNAPSHOTS (For Arweave persistence)
-- =============================================================================

SNAPSHOTS = {}

-- Create a snapshot of current state
function create_snapshot(state_data)
    local snapshot = {
        id = #SNAPSHOTS + 1,
        timestamp = os.time(),
        tick = WorldTick or 0,
        event_index = #EVENT_LOG,
        state = state_data
    }
    
    table.insert(SNAPSHOTS, snapshot)
    
    -- Log snapshot creation
    log_event(EVENT_TYPES.SNAPSHOT_CREATED, {
        snapshot_id = snapshot.id,
        event_index = snapshot.event_index
    })
    
    return snapshot
end

-- Get latest snapshot
function get_latest_snapshot()
    if #SNAPSHOTS == 0 then
        return nil
    end
    return SNAPSHOTS[#SNAPSHOTS]
end

-- Get events since last snapshot
function get_events_since_snapshot()
    local latest = get_latest_snapshot()
    local start_index = latest and (latest.event_index + 1) or 1
    
    local results = {}
    for i = start_index, #EVENT_LOG do
        table.insert(results, EVENT_LOG[i])
    end
    
    return results
end

-- =============================================================================
-- ARWEAVE BUNDLE FORMAT
-- =============================================================================

-- Create Arweave-ready bundle
function create_arweave_bundle(include_full_log)
    local latest_snapshot = get_latest_snapshot()
    local events_since = get_events_since_snapshot()
    
    local bundle = {
        schema_version = "2.0.0",
        bundle_type = "simulation_events",
        timestamp = os.time(),
        tick = WorldTick or 0,
        
        -- Metadata
        event_count = #EVENT_LOG,
        snapshot_count = #SNAPSHOTS,
        events_since_snapshot = #events_since,
        
        -- Recent events (always included)
        recent_events = events_since,
        
        -- Optional full log
        full_log = include_full_log and EVENT_LOG or nil,
        
        -- Latest snapshot reference
        latest_snapshot = latest_snapshot
    }
    
    return bundle
end

-- =============================================================================
-- EVENT STATISTICS
-- =============================================================================

function get_event_stats()
    local stats = {
        total_events = #EVENT_LOG,
        total_snapshots = #SNAPSHOTS,
        by_type = {}
    }
    
    for _, event in ipairs(EVENT_LOG) do
        local t = event.type
        stats.by_type[t] = (stats.by_type[t] or 0) + 1
    end
    
    return stats
end

-- Get activity summary for a time period
function get_activity_summary(tick_range)
    tick_range = tick_range or 100
    local current_tick = WorldTick or 0
    local start_tick = math.max(0, current_tick - tick_range)
    
    local events = get_events_in_range(start_tick, current_tick)
    
    local summary = {
        tick_range = {start_tick, current_tick},
        event_count = #events,
        npc_actions = 0,
        transactions = 0,
        social_events = 0
    }
    
    for _, event in ipairs(events) do
        if event.type == EVENT_TYPES.NPC_ACTION then
            summary.npc_actions = summary.npc_actions + 1
        elseif event.type == EVENT_TYPES.TRANSACTION then
            summary.transactions = summary.transactions + 1
        elseif event.type == EVENT_TYPES.NPC_INTERACTION then
            summary.social_events = summary.social_events + 1
        end
    end
    
    return summary
end

-- =============================================================================
-- CLEANUP
-- =============================================================================

-- Compact old events (keep recent, archive old)
function compact_events(keep_count)
    keep_count = keep_count or 1000
    
    if #EVENT_LOG <= keep_count then
        return 0
    end
    
    -- Create snapshot before compacting
    create_snapshot({
        compaction_reason = "size_limit",
        events_archived = #EVENT_LOG - keep_count
    })
    
    -- Keep only recent events
    local archived = {}
    local keep_start = #EVENT_LOG - keep_count + 1
    
    for i = 1, keep_start - 1 do
        table.insert(archived, EVENT_LOG[i])
    end
    
    local new_log = {}
    for i = keep_start, #EVENT_LOG do
        table.insert(new_log, EVENT_LOG[i])
    end
    
    local archived_count = #archived
    EVENT_LOG = new_log
    CURRENT_EVENT_INDEX = #EVENT_LOG
    
    return archived_count
end

-- Clear all events (for testing)
function clear_events()
    EVENT_LOG = {}
    SNAPSHOTS = {}
    CURRENT_EVENT_INDEX = 0
end

-- =============================================================================
-- AO MESSAGE HANDLERS
-- =============================================================================

-- Handler: Log event
Handlers.add("LogEvent", Handlers.utils.hasMatchingTag("Action", "LogEvent"),
    function(msg)
        local data = json.decode(msg.Data or "{}")
        local event = log_event(
            data.event_type or "custom",
            data.payload or {},
            data.actor_id
        )
        
        ao.send({
            Target = msg.From,
            Data = json.encode(event)
        })
    end
)

-- Handler: Get recent events
Handlers.add("GetRecentEvents", Handlers.utils.hasMatchingTag("Action", "GetRecentEvents"),
    function(msg)
        local count = tonumber(msg.Tags["Count"]) or 50
        local events = get_recent_events(count)
        
        ao.send({
            Target = msg.From,
            Data = json.encode(events)
        })
    end
)

-- Handler: Get events by actor
Handlers.add("GetActorEvents", Handlers.utils.hasMatchingTag("Action", "GetActorEvents"),
    function(msg)
        local actor_id = msg.Tags["ActorId"]
        local limit = tonumber(msg.Tags["Limit"]) or 100
        local events = get_events_by_actor(actor_id, limit)
        
        ao.send({
            Target = msg.From,
            Data = json.encode(events)
        })
    end
)

-- Handler: Create snapshot
Handlers.add("CreateSnapshot", Handlers.utils.hasMatchingTag("Action", "CreateSnapshot"),
    function(msg)
        local state_data = msg.Data and json.decode(msg.Data) or {}
        local snapshot = create_snapshot(state_data)
        
        ao.send({
            Target = msg.From,
            Data = json.encode(snapshot)
        })
    end
)

-- Handler: Get Arweave bundle
Handlers.add("GetArweaveBundle", Handlers.utils.hasMatchingTag("Action", "GetArweaveBundle"),
    function(msg)
        local include_full = msg.Tags["IncludeFull"] == "true"
        local bundle = create_arweave_bundle(include_full)
        
        ao.send({
            Target = msg.From,
            Data = json.encode(bundle)
        })
    end
)

-- Handler: Get event stats
Handlers.add("GetEventStats", Handlers.utils.hasMatchingTag("Action", "GetEventStats"),
    function(msg)
        local stats = get_event_stats()
        
        ao.send({
            Target = msg.From,
            Data = json.encode(stats)
        })
    end
)

-- =============================================================================
-- EXPORT
-- =============================================================================

return {
    -- Constants
    EVENT_TYPES = EVENT_TYPES,
    
    -- State
    EVENT_LOG = EVENT_LOG,
    SNAPSHOTS = SNAPSHOTS,
    
    -- Event creation
    log_event = log_event,
    create_event = create_event,
    
    -- Queries
    get_events_by_type = get_events_by_type,
    get_events_by_actor = get_events_by_actor,
    get_events_in_range = get_events_in_range,
    get_recent_events = get_recent_events,
    
    -- Time travel
    get_event_at = get_event_at,
    get_events_up_to_tick = get_events_up_to_tick,
    
    -- Snapshots
    create_snapshot = create_snapshot,
    get_latest_snapshot = get_latest_snapshot,
    get_events_since_snapshot = get_events_since_snapshot,
    
    -- Arweave
    create_arweave_bundle = create_arweave_bundle,
    
    -- Stats
    get_event_stats = get_event_stats,
    get_activity_summary = get_activity_summary,
    
    -- Maintenance
    compact_events = compact_events,
    clear_events = clear_events
}
