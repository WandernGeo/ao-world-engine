-- ============================================================================
-- EVENT LOGGER PLUGIN
-- Comprehensive simulation event recording and analytics
-- Plugin 2 of 3 for AO World Engine audit
-- ============================================================================

local EventLogger = {}

-- Event categories
EventLogger.CATEGORIES = {
    WORLD    = "world",
    NPC      = "npc",
    ECONOMY  = "economy",
    BUILDING = "building",
    SOCIAL   = "social",
    COMBAT   = "combat",
    WEATHER  = "weather",
    PLUGIN   = "plugin"
}

-- Severity levels
EventLogger.SEVERITY = {
    DEBUG    = 0,
    INFO     = 1,
    WARNING  = 2,
    CRITICAL = 3,
    FATAL    = 4
}

-- State
EventLogger.State = {
    events = {},           -- Ring buffer of recent events
    max_events = 2000,     -- Max events in buffer
    write_index = 0,       -- Current write position
    total_logged = 0,      -- Lifetime event count
    stats = {},            -- Per-category stats
    alerts = {},           -- Active alerts (severity >= WARNING)
    max_alerts = 100,
    filters = {},          -- Active filters for selective logging
    started_at_tick = 0
}

-- Initialize logger
function EventLogger.init(tick)
    EventLogger.State.started_at_tick = tick or 0
    EventLogger.State.events = {}
    EventLogger.State.total_logged = 0
    EventLogger.State.stats = {}

    for _, category in pairs(EventLogger.CATEGORIES) do
        EventLogger.State.stats[category] = {
            count = 0,
            last_tick = 0,
            per_day_avg = 0,
            severity_counts = { [0] = 0, [1] = 0, [2] = 0, [3] = 0, [4] = 0 }
        }
    end
end

-- Log an event
function EventLogger.log(tick, category, event_type, data, severity)
    severity = severity or EventLogger.SEVERITY.INFO
    category = category or EventLogger.CATEGORIES.WORLD

    -- Check filters
    if EventLogger.State.filters[category] == false then
        return nil  -- Filtered out
    end

    local event = {
        id = EventLogger.State.total_logged + 1,
        tick = tick,
        category = category,
        type = event_type,
        severity = severity,
        data = data or {},
        timestamp = tick  -- In AO, tick is our timestamp
    }

    -- Add to ring buffer
    EventLogger.State.write_index = (EventLogger.State.write_index % EventLogger.State.max_events) + 1
    EventLogger.State.events[EventLogger.State.write_index] = event
    EventLogger.State.total_logged = EventLogger.State.total_logged + 1

    -- Update stats
    local stat = EventLogger.State.stats[category]
    if stat then
        stat.count = stat.count + 1
        stat.last_tick = tick
        stat.severity_counts[severity] = (stat.severity_counts[severity] or 0) + 1

        -- Calculate rolling per-day average
        local ticks_elapsed = math.max(1, tick - EventLogger.State.started_at_tick)
        local days_elapsed = math.max(1, ticks_elapsed / 240)
        stat.per_day_avg = math.floor(stat.count / days_elapsed)
    end

    -- Create alert for high-severity events
    if severity >= EventLogger.SEVERITY.WARNING then
        EventLogger.add_alert(event)
    end

    return event
end

-- Convenience methods for each category
function EventLogger.log_world(tick, event_type, data, severity)
    return EventLogger.log(tick, EventLogger.CATEGORIES.WORLD, event_type, data, severity)
end

function EventLogger.log_npc(tick, event_type, npc_id, data, severity)
    data = data or {}
    data.npc_id = npc_id
    return EventLogger.log(tick, EventLogger.CATEGORIES.NPC, event_type, data, severity)
end

function EventLogger.log_economy(tick, event_type, data, severity)
    return EventLogger.log(tick, EventLogger.CATEGORIES.ECONOMY, event_type, data, severity)
end

function EventLogger.log_social(tick, npc1, npc2, interaction_type, data)
    data = data or {}
    data.npc1 = npc1
    data.npc2 = npc2
    data.interaction_type = interaction_type
    return EventLogger.log(tick, EventLogger.CATEGORIES.SOCIAL, "interaction", data, EventLogger.SEVERITY.INFO)
end

-- Add an alert
function EventLogger.add_alert(event)
    table.insert(EventLogger.State.alerts, {
        event_id = event.id,
        tick = event.tick,
        category = event.category,
        type = event.type,
        severity = event.severity,
        message = event.data.message or event.type,
        acknowledged = false
    })

    -- Trim alerts
    while #EventLogger.State.alerts > EventLogger.State.max_alerts do
        table.remove(EventLogger.State.alerts, 1)
    end
end

-- Acknowledge an alert
function EventLogger.acknowledge_alert(alert_id)
    for _, alert in ipairs(EventLogger.State.alerts) do
        if alert.event_id == alert_id then
            alert.acknowledged = true
            return true
        end
    end
    return false
end

-- Query events by category and time range
function EventLogger.query(category, from_tick, to_tick, max_results)
    max_results = max_results or 50
    local results = {}

    for _, event in pairs(EventLogger.State.events) do
        if event then
            local matches = true
            if category and event.category ~= category then matches = false end
            if from_tick and event.tick < from_tick then matches = false end
            if to_tick and event.tick > to_tick then matches = false end

            if matches then
                table.insert(results, event)
                if #results >= max_results then break end
            end
        end
    end

    -- Sort by tick descending
    table.sort(results, function(a, b) return a.tick > b.tick end)
    return results
end

-- Get summary report for a time period
function EventLogger.get_summary(from_tick, to_tick)
    local summary = {
        period = { from = from_tick, to = to_tick },
        total_events = 0,
        by_category = {},
        by_severity = { [0] = 0, [1] = 0, [2] = 0, [3] = 0, [4] = 0 },
        top_event_types = {},
        active_alerts = 0
    }

    local type_counts = {}

    for _, event in pairs(EventLogger.State.events) do
        if event and event.tick >= from_tick and event.tick <= to_tick then
            summary.total_events = summary.total_events + 1
            summary.by_category[event.category] = (summary.by_category[event.category] or 0) + 1
            summary.by_severity[event.severity] = (summary.by_severity[event.severity] or 0) + 1
            type_counts[event.type] = (type_counts[event.type] or 0) + 1
        end
    end

    -- Top event types
    for event_type, count in pairs(type_counts) do
        table.insert(summary.top_event_types, { type = event_type, count = count })
    end
    table.sort(summary.top_event_types, function(a, b) return a.count > b.count end)

    -- Active alerts
    for _, alert in ipairs(EventLogger.State.alerts) do
        if not alert.acknowledged then
            summary.active_alerts = summary.active_alerts + 1
        end
    end

    return summary
end

-- Set a filter (enable/disable logging for a category)
function EventLogger.set_filter(category, enabled)
    EventLogger.State.filters[category] = enabled
end

-- Process tick - auto-log tick milestones
function EventLogger.on_tick(tick)
    -- Log day transitions
    if tick % 240 == 0 then
        EventLogger.log_world(tick, "day_transition", {
            day = math.floor(tick / 240) + 1,
            message = "New day started"
        })
    end

    -- Log year transitions
    if tick % (240 * 365) == 0 then
        EventLogger.log_world(tick, "year_transition", {
            year = math.floor(tick / (240 * 365)) + 1,
            message = "New year started"
        }, EventLogger.SEVERITY.WARNING)
    end

    -- Log significant tick milestones
    if tick % 10000 == 0 and tick > 0 then
        EventLogger.log_world(tick, "milestone", {
            total_ticks = tick,
            total_events_logged = EventLogger.State.total_logged,
            message = "Tick milestone reached: " .. tick
        })
    end
end

-- Get full state for API
function EventLogger.get_state()
    return {
        total_logged = EventLogger.State.total_logged,
        buffer_size = EventLogger.State.max_events,
        stats = EventLogger.State.stats,
        active_alerts = #EventLogger.State.alerts,
        started_at = EventLogger.State.started_at_tick
    }
end

-- Export module
return EventLogger
