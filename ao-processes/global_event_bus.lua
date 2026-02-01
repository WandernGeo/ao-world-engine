--[[
  RE:ECHO City - Global Event Bus
  
  Broadcasts world-level events to all districts.
  Examples: city blackouts, festivals, economic crashes.
  
  SECURITY NOTE: This file contains NO secrets, keys, or wallet data.
]]--

-- Registry of district process IDs
DISTRICTS = DISTRICTS or {}
EVENT_LOG = EVENT_LOG or {}
EventCounter = EventCounter or 0

--[[
  HANDLERS
]]--

-- Districts register themselves
Handlers.add("register-district", Handlers.utils.hasMatchingTag("Action", "register-district"), function(msg)
  local data = json.decode(msg.Data)
  DISTRICTS[data.id] = msg.From
  
  print("District registered: " .. data.id .. " -> " .. msg.From)
  
  ao.send({
    Target = msg.From,
    Action = "registration-confirmed",
    Data = json.encode({ status = "ok", total_districts = table_length(DISTRICTS) })
  })
end)

-- Broadcast global event to all districts
Handlers.add("broadcast", Handlers.utils.hasMatchingTag("Action", "broadcast"), function(msg)
  EventCounter = EventCounter + 1
  local event = json.decode(msg.Data)
  event.id = "global_event_" .. EventCounter
  event.timestamp = os.time()
  
  -- Log the event
  table.insert(EVENT_LOG, event)
  
  -- Broadcast to ALL districts simultaneously
  local sent_count = 0
  for id, process_id in pairs(DISTRICTS) do
    ao.send({
      Target = process_id,
      Action = "global-event",
      Data = json.encode(event),
      Tags = {
        { name = "Event-Type", value = event.type or "unknown" },
        { name = "Priority", value = event.priority or "normal" }
      }
    })
    sent_count = sent_count + 1
  end
  
  -- Confirm to sender
  ao.send({
    Target = msg.From,
    Action = "broadcast-complete",
    Data = json.encode({
      event_id = event.id,
      districts_notified = sent_count
    })
  })
  
  print("Broadcast event " .. event.id .. " to " .. sent_count .. " districts")
end)

-- Query event history
Handlers.add("query-events", Handlers.utils.hasMatchingTag("Action", "query-events"), function(msg)
  local data = json.decode(msg.Data or "{}")
  local limit = data.limit or 10
  
  -- Get last N events
  local result = {}
  local start = math.max(1, #EVENT_LOG - limit + 1)
  for i = start, #EVENT_LOG do
    table.insert(result, EVENT_LOG[i])
  end
  
  ao.send({
    Target = msg.From,
    Action = "events-result",
    Data = json.encode(result)
  })
end)

-- List registered districts
Handlers.add("list-districts", Handlers.utils.hasMatchingTag("Action", "list-districts"), function(msg)
  local list = {}
  for id, process_id in pairs(DISTRICTS) do
    table.insert(list, { id = id, process = process_id })
  end
  
  ao.send({
    Target = msg.From,
    Action = "districts-list",
    Data = json.encode(list)
  })
end)

--[[
  CRON: Periodic world events
]]--
Handlers.add("world-tick", Handlers.utils.hasMatchingTag("Action", "Cron"), function(msg)
  -- Random world events based on time
  local hour = os.date("*t").hour
  
  -- Example: Night events more likely at night
  if hour >= 22 or hour < 6 then
    -- 1% chance of blackout at night
    if math.random() < 0.01 then
      ao.send({
        Target = ao.id,
        Action = "broadcast",
        Data = json.encode({
          type = "event:blackout",
          severity = math.random(),
          duration = math.random(1, 6) * 10,  -- 10-60 minutes
          affected = "all"
        })
      })
    end
  end
  
  -- Example: Weekend festival
  local day = os.date("*t").wday
  if day == 7 or day == 1 then  -- Saturday or Sunday
    if math.random() < 0.05 then
      ao.send({
        Target = ao.id,
        Action = "broadcast",
        Data = json.encode({
          type = "event:festival",
          name = "neon_night",
          district = "all"
        })
      })
    end
  end
end)

--[[
  HELPERS
]]--

function table_length(t)
  local count = 0
  for _ in pairs(t) do count = count + 1 end
  return count
end

return {
  DISTRICTS = DISTRICTS,
  EVENT_LOG = EVENT_LOG
}
