--[[
  RE:ECHO City - Layer Event Bus
  
  Handles cross-layer "echo" events and bleed-through between dimensions.
  The multiverse backbone for the Echo Layers system.
  
  SECURITY NOTE: This file contains NO secrets, keys, or wallet data.
]]--

-- Layer Registry
LAYERS = LAYERS or {}
LAYER_EVENTS = LAYER_EVENTS or {}
BLEED_LOG = BLEED_LOG or {}
LayerCounter = LayerCounter or 0

-- Bleed probability (0.1% chance per tick per NPC)
BLEED_PROBABILITY = 0.001

-- Manifestation types when layers bleed through
BLEED_TYPES = {
  "dream_vision",      -- NPC dreams of alternate self
  "deja_vu",           -- Moment feels familiar from elsewhere
  "echo_whisper",      -- Hears voice from another layer
  "glitched_memory",   -- Memory that didn't happen in this layer
  "parallel_glimpse",  -- Brief vision of other layer
  "watcher_sense"      -- Feeling of being observed from above
}

--[[
  LAYER REGISTRATION
]]--

-- Register a new layer (fork/branch)
Handlers.add("register-layer", Handlers.utils.hasMatchingTag("Action", "register-layer"), function(msg)
  local data = json.decode(msg.Data)
  LayerCounter = LayerCounter + 1
  
  local layer_id = data.layer_id or ("layer_" .. LayerCounter)
  
  LAYERS[layer_id] = {
    id = layer_id,
    layer_number = data.layer_number or LayerCounter,
    parent_layer = data.parent_layer or "prime",
    branch_point = data.branch_point or 0,
    status = data.status or "community",
    description = data.description or "",
    process_id = msg.From,
    created_at = os.time(),
    districts = data.districts or {}
  }
  
  ao.send({
    Target = msg.From,
    Action = "layer-registered",
    Data = json.encode({
      layer_id = layer_id,
      layer_number = LAYERS[layer_id].layer_number,
      total_layers = table_length(LAYERS)
    })
  })
  
  print("Layer registered: " .. layer_id .. " (child of " .. LAYERS[layer_id].parent_layer .. ")")
end)

--[[
  CROSS-LAYER BLEED EVENTS
  
  When the Veil thins, NPCs can sense other layers.
  These are rare, mysterious events that fuel the multiverse lore.
]]--

-- Generate a bleed event (called deterministically from district tick)
function generate_bleed_event(npc_id, tick, source_layer)
  local seed = hash_to_number(npc_id .. tostring(tick) .. "bleed", 1000000)
  
  -- Get a random target layer (not the source)
  local target_layers = {}
  for layer_id, _ in pairs(LAYERS) do
    if layer_id ~= source_layer then
      table.insert(target_layers, layer_id)
    end
  end
  
  if #target_layers == 0 then
    -- Only one layer exists, bleed into "theoretical" layers
    target_layers = {"shadow_echo", "utopia_fork", "war_timeline"}
  end
  
  local target_layer = target_layers[(seed % #target_layers) + 1]
  local bleed_type = BLEED_TYPES[(seed % #BLEED_TYPES) + 1]
  
  return {
    type = "layer_bleed",
    npc_id = npc_id,
    tick = tick,
    source_layer = source_layer,
    target_layer = target_layer,
    manifestation = bleed_type,
    intensity = (seed % 100) / 100,  -- 0.0 to 1.0
    event_id = "bleed_" .. npc_id .. "_" .. tick
  }
end

-- Broadcast a bleed event
Handlers.add("bleed-event", Handlers.utils.hasMatchingTag("Action", "bleed-event"), function(msg)
  local data = json.decode(msg.Data)
  
  -- Log the bleed
  table.insert(BLEED_LOG, {
    event = data,
    reported_by = msg.From,
    timestamp = os.time()
  })
  
  -- Broadcast to all layers for awareness
  for layer_id, layer in pairs(LAYERS) do
    if layer.process_id then
      ao.send({
        Target = layer.process_id,
        Action = "layer-bleed-occurred",
        Data = json.encode(data),
        Tags = {
          { name = "Bleed-Type", value = data.manifestation or "unknown" },
          { name = "Source-Layer", value = data.source_layer or "unknown" },
          { name = "Target-Layer", value = data.target_layer or "unknown" }
        }
      })
    end
  end
  
  ao.send({
    Target = msg.From,
    Action = "bleed-logged",
    Data = json.encode({ event_id = data.event_id, logged = true })
  })
end)

--[[
  WATCHER OBSERVATION API
  
  For the Wandern app to "tune in" to layers and watch events.
  Users are "Watchers" observing the simulation.
]]--

-- Query recent events in a layer
Handlers.add("watch-layer", Handlers.utils.hasMatchingTag("Action", "watch-layer"), function(msg)
  local data = json.decode(msg.Data or "{}")
  local layer_id = data.layer_id or "prime"
  local tick_start = data.tick_start or 0
  local tick_end = data.tick_end or 999999999
  local limit = data.limit or 50
  
  -- Collect events for this layer
  local events = {}
  for _, event in ipairs(LAYER_EVENTS) do
    if event.layer == layer_id and 
       event.tick >= tick_start and 
       event.tick <= tick_end then
      table.insert(events, event)
      if #events >= limit then break end
    end
  end
  
  ao.send({
    Target = msg.From,
    Action = "layer-events",
    Data = json.encode({
      layer = layer_id,
      count = #events,
      events = events
    })
  })
end)

-- Query bleed events (cross-layer anomalies)
Handlers.add("watch-bleeds", Handlers.utils.hasMatchingTag("Action", "watch-bleeds"), function(msg)
  local data = json.decode(msg.Data or "{}")
  local limit = data.limit or 20
  
  -- Get recent bleeds
  local result = {}
  local start = math.max(1, #BLEED_LOG - limit + 1)
  for i = start, #BLEED_LOG do
    table.insert(result, BLEED_LOG[i])
  end
  
  ao.send({
    Target = msg.From,
    Action = "bleed-events",
    Data = json.encode(result)
  })
end)

-- List all registered layers
Handlers.add("list-layers", Handlers.utils.hasMatchingTag("Action", "list-layers"), function(msg)
  local layers = {}
  for id, layer in pairs(LAYERS) do
    table.insert(layers, {
      id = id,
      layer_number = layer.layer_number,
      parent_layer = layer.parent_layer,
      status = layer.status,
      description = layer.description,
      created_at = layer.created_at
    })
  end
  
  -- Sort by layer number
  table.sort(layers, function(a, b) return a.layer_number < b.layer_number end)
  
  ao.send({
    Target = msg.From,
    Action = "layers-list",
    Data = json.encode(layers)
  })
end)

--[[
  SCENE RECONSTRUCTION API
  
  Generate narrative from event logs for visualization.
  Returns structured data for RE:ECHO animation pipeline.
]]--

Handlers.add("reconstruct-scene", Handlers.utils.hasMatchingTag("Action", "reconstruct-scene"), function(msg)
  local data = json.decode(msg.Data)
  
  local scene = {
    layer = data.layer or "prime",
    location = data.location or "unknown",
    tick_start = data.tick_start,
    tick_end = data.tick_end,
    events = {},
    npcs_present = {},
    dialogue_seeds = {},
    atmosphere = get_atmosphere(data.tick_start),
    has_bleed = false,
    bleed_details = nil
  }
  
  -- Collect events in range
  for _, event in ipairs(LAYER_EVENTS) do
    if event.layer == scene.layer and
       event.tick >= scene.tick_start and
       event.tick <= scene.tick_end then
      table.insert(scene.events, event)
      
      -- Track NPCs
      if event.npc_id then
        scene.npcs_present[event.npc_id] = true
      end
    end
  end
  
  -- Check for bleed events
  for _, bleed in ipairs(BLEED_LOG) do
    local e = bleed.event
    if e.tick >= scene.tick_start and e.tick <= scene.tick_end then
      scene.has_bleed = true
      scene.bleed_details = e
      break
    end
  end
  
  -- Add dialogue seeds based on scene context
  if scene.has_bleed then
    scene.dialogue_seeds = {
      "The air shimmered wrong. A glitch in the city's breath.",
      "For a moment, I saw... something else. Another market. Burning.",
      "Did you feel that? Like static behind your eyes."
    }
  end
  
  ao.send({
    Target = msg.From,
    Action = "scene-data",
    Data = json.encode(scene)
  })
end)

--[[
  HELPERS
]]--

function hash_to_number(str, max)
  local hash = 0
  for i = 1, #str do
    hash = (hash * 31 + string.byte(str, i)) % 2147483647
  end
  return (hash % max) + 1
end

function table_length(t)
  local count = 0
  for _ in pairs(t) do count = count + 1 end
  return count
end

function get_atmosphere(tick)
  local hour = tick % 24
  if hour >= 22 or hour < 5 then
    return { 
      time = "night", 
      weather = "rain", 
      mood = "noir",
      description = "Rain-slicked alleys flicker under failing neon"
    }
  elseif hour >= 5 and hour < 8 then
    return { 
      time = "dawn", 
      weather = "fog", 
      mood = "liminal",
      description = "Morning fog clings to the towers like memory"
    }
  else
    return { 
      time = "day", 
      weather = "haze", 
      mood = "tense",
      description = "Hazy light filters through the smog"
    }
  end
end

--[[
  CRON: Periodic multiverse events
]]--

Handlers.add("multiverse-tick", Handlers.utils.hasMatchingTag("Action", "Cron"), function(msg)
  -- Rare cross-layer events (1% chance per tick)
  if math.random() < 0.01 then
    -- Generate a "veil thinning" event
    local event = {
      type = "veil_thin",
      affected_layers = {},
      intensity = math.random(),
      description = "The Veil thins. Echoes multiply."
    }
    
    -- Affect 1-3 random layers
    local count = math.random(1, 3)
    for layer_id, _ in pairs(LAYERS) do
      if count > 0 then
        table.insert(event.affected_layers, layer_id)
        count = count - 1
      end
    end
    
    table.insert(LAYER_EVENTS, {
      layer = "multiverse",
      tick = os.time(),
      event = event
    })
  end
end)

-- Initialize prime layer
if not LAYERS["prime"] then
  LAYERS["prime"] = {
    id = "prime",
    layer_number = 0,
    parent_layer = nil,
    status = "canonical",
    description = "The Prime Echo - Official RE:ECHO City canon",
    process_id = ao.id,
    created_at = os.time(),
    districts = {}
  }
end

return {
  LAYERS = LAYERS,
  LAYER_EVENTS = LAYER_EVENTS,
  BLEED_LOG = BLEED_LOG,
  generate_bleed_event = generate_bleed_event
}
