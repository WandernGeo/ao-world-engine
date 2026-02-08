--[[
  AO World Engine - District Process
  
  Each district handles ~10,000 NPCs with deterministic scheduling.
  
  Config loaded from:
  - world_codec_14_behaviors.json → archetype routines, reactions, schedule_system
  - world_codec_29_commuting.json → transport modes, congestion, commute penalties
  - world_codec_34_schedules_enhanced.json → 24-block schedule system
  
  SECURITY NOTE: This file contains NO secrets, keys, or wallet data.
]]--

local json = require("json")
local codec = require("codec_loader")

-- State
NPCs = NPCs or {}
Events = Events or {}
Tick = Tick or 0
DistrictId = DistrictId or "unknown"
GLOBAL_BUS = GLOBAL_BUS or nil
LAYER_BUS = LAYER_BUS or nil  -- Multiverse layer event bus

-- Bleed manifestation types (when layers overlap)
BLEED_TYPES = {
  "dream_vision",      -- NPC dreams of alternate self
  "deja_vu",           -- Moment feels familiar from elsewhere
  "echo_whisper",      -- Hears voice from another layer
  "glitched_memory",   -- Memory that didn't happen in this layer
  "parallel_glimpse",  -- Brief vision of other layer
  "watcher_sense"      -- Feeling of being observed from above
}

-- Action Dictionary (shorthand codes)
ACTIONS = {
  T = "trade",
  M = "move",
  R = "rest",
  A = "attack",
  C = "conversation",
  H = "hide",
  P = "probe",
  S = "spy"
}

--[[
  DETERMINISTIC SCHEDULING
  
  Key insight: "Random" behavior is actually deterministic based on:
  - NPC ID (unique seed)
  - Current tick/time
  - Day of week pattern
  - Other NPCs' states (referenced, not queried)
  
  Any NPC can CALCULATE where another NPC will be at time T
  without messaging them. It's like a hash function.
]]--

function hash_to_number(str, max)
  -- Simple deterministic hash
  local hash = 0
  for i = 1, #str do
    hash = (hash * 31 + string.byte(str, i)) % 2147483647
  end
  return (hash % max) + 1
end

function get_time_slot(tick)
  -- Convert tick to time of day (0-23 hours)
  return tick % 24
end

function get_day_of_week(tick)
  -- Convert tick to day (0-6)
  return math.floor(tick / 24) % 7
end

--[[
  DETERMINISTIC LOCATION
  
  Given NPC ID + time, anyone can calculate where they'll be.
  No messaging needed - it's math.
]]--
function calculate_npc_location(npc_id, tick)
  local hour = get_time_slot(tick)
  local day = get_day_of_week(tick)
  local npc = NPCs[npc_id]
  
  if not npc then return nil end
  
  -- Get routine for this archetype
  local routine = npc.routine or {}
  
  -- Deterministic "random" based on NPC seed + time
  local seed = hash_to_number(npc_id .. tostring(tick), 1000)
  local probability_roll = seed / 1000
  
  -- Check routine slots
  for _, slot in ipairs(routine) do
    if hour >= slot.start_hour and hour < slot.end_hour then
      if probability_roll < slot.probability then
        return {
          location = slot.location,
          action = slot.action,
          available_for = slot.interruptible and "interaction" or "busy"
        }
      end
    end
  end
  
  -- Default: home location
  return {
    location = npc.home_location,
    action = "idle",
    available_for = "interaction"
  }
end

--[[
  INTER-NPC AWARENESS
  
  NPC A can know where NPC B is WITHOUT messaging them.
  Just calculate it from shared state.
]]--
function can_interact(npc_a_id, npc_b_id, tick)
  local loc_a = calculate_npc_location(npc_a_id, tick)
  local loc_b = calculate_npc_location(npc_b_id, tick)
  
  if not loc_a or not loc_b then return false end
  
  -- Same location = can interact in person
  if loc_a.location == loc_b.location then
    return { type = "in_person", location = loc_a.location }
  end
  
  -- Different location = can still message/call
  -- (async communication always possible)
  return { type = "remote", method = "message" }
end

--[[
  RELATIONSHIP-BASED SCHEDULING
  
  NPCs adjust schedules based on relationships.
  "If my friend is at the tavern, I'm more likely to go there"
]]--
function get_social_modifier(npc_id, tick)
  local npc = NPCs[npc_id]
  if not npc or not npc.relationships then return 1.0 end
  
  local modifier = 1.0
  
  for friend_id, affinity in pairs(npc.relationships) do
    if affinity > 0.5 then
      local friend_loc = calculate_npc_location(friend_id, tick)
      if friend_loc then
        -- Increase probability of going where friends are
        modifier = modifier + (affinity * 0.2)
      end
    end
  end
  
  return math.min(modifier, 2.0)  -- Cap at 2x
end

--[[
  DECISION ENGINE
  
  Combines:
  - Routine (deterministic schedule)
  - Social modifiers (friend locations)
  - Event reactions (global events)
  - Personality weights (archetype behavior)
]]--
function decide_action(npc_id, tick, context)
  local npc = NPCs[npc_id]
  if not npc then return nil end
  
  -- 1. Get base location from deterministic schedule
  local base = calculate_npc_location(npc_id, tick)
  
  -- 2. Apply social modifier
  local social = get_social_modifier(npc_id, tick)
  
  -- 3. Check for reactions to context (global events, etc.)
  if context and context.global_event then
    local reaction = npc.reactions and npc.reactions[context.global_event.type]
    if reaction then
      local roll = hash_to_number(npc_id .. context.global_event.id, 100) / 100
      if roll < reaction.probability then
        return {
          action = reaction.action,
          reason = "reacting_to_" .. context.global_event.type,
          priority = "high"
        }
      end
    end
  end
  
  -- 4. Check if should interact with nearby NPCs
  if base.available_for == "interaction" then
    -- Find NPCs at same location
    for other_id, _ in pairs(NPCs) do
      if other_id ~= npc_id then
        local interaction = can_interact(npc_id, other_id, tick)
        if interaction and interaction.type == "in_person" then
          local affinity = npc.relationships and npc.relationships[other_id] or 0
          if affinity > 0.3 then
            return {
              action = "C:" .. other_id .. ":casual",
              reason = "social_interaction",
              priority = "normal"
            }
          end
        end
      end
    end
  end
  
  -- 5. Default: follow routine
  return {
    action = base.action,
    location = base.location,
    priority = "low"
  }
end

--[[
  HANDLERS
]]--

-- Initialize district
Handlers.add("init", Handlers.utils.hasMatchingTag("Action", "init"), function(msg)
  local data = json.decode(msg.Data)
  DistrictId = data.district_id or "district_001"
  
  -- Generate initial NPCs
  local count = data.npc_count or 100
  for i = 1, count do
    local npc_id = DistrictId .. "_npc_" .. string.format("%04d", i)
    NPCs[npc_id] = generate_npc(npc_id, data.archetypes or {"merchant"})
  end
  
  ao.send({
    Target = msg.From,
    Action = "init-complete",
    Data = json.encode({ district = DistrictId, npc_count = count })
  })
end)

-- Cron tick: Run simulation
Handlers.add("tick", Handlers.utils.hasMatchingTag("Action", "Cron"), function(msg)
  Tick = Tick + 1
  local tick_events = {}
  
  -- Process each NPC
  for npc_id, npc in pairs(NPCs) do
    local action = decide_action(npc_id, Tick, { global_event = CurrentGlobalEvent })
    
    if action then
      -- Record event in shorthand
      table.insert(tick_events, {
        npc = npc_id,
        action = action.action,
        tick = Tick
      })
    end
    
    -- MULTIVERSE: Check for layer bleed (0.1% chance per NPC per tick)
    local bleed_seed = hash_to_number(npc_id .. tostring(Tick) .. "bleed", 10000)
    if bleed_seed < 10 then  -- 0.1% probability
      local bleed_event = {
        type = "layer_bleed",
        npc = npc_id,
        tick = Tick,
        district = DistrictId,
        manifestation = get_bleed_manifestation(bleed_seed),
        intensity = bleed_seed / 10
      }
      table.insert(tick_events, bleed_event)
      
      -- Notify layer event bus if registered
      if LAYER_BUS then
        ao.send({
          Target = LAYER_BUS,
          Action = "bleed-event",
          Data = json.encode(bleed_event)
        })
      end
    end
  end
  
  -- Store events
  table.insert(Events, {
    tick = Tick,
    district = DistrictId,
    events = tick_events
  })
  
  -- Persist to Arweave every 100 ticks
  if Tick % 100 == 0 then
    persist_events()
  end
end)

-- Query NPC location (anyone can calculate this)
Handlers.add("query-location", Handlers.utils.hasMatchingTag("Action", "query-location"), function(msg)
  local data = json.decode(msg.Data)
  local location = calculate_npc_location(data.npc_id, data.tick or Tick)
  
  ao.send({
    Target = msg.From,
    Action = "location-result",
    Data = json.encode(location)
  })
end)

-- Register with global event bus
Handlers.add("register-bus", Handlers.utils.hasMatchingTag("Action", "register-bus"), function(msg)
  GLOBAL_BUS = msg.From
  ao.send({
    Target = GLOBAL_BUS,
    Action = "register-district",
    Data = json.encode({ id = DistrictId })
  })
end)

-- Handle global events
Handlers.add("global-event", Handlers.utils.hasMatchingTag("Action", "global-event"), function(msg)
  CurrentGlobalEvent = json.decode(msg.Data)
  -- NPCs will react on next tick
end)

--[[
  HELPER FUNCTIONS
]]--

function generate_npc(npc_id, archetypes)
  local archetype = archetypes[hash_to_number(npc_id, #archetypes)]
  
  return {
    id = npc_id,
    archetype = archetype,
    home_location = "home_" .. npc_id,
    routine = get_archetype_routine(archetype),
    relationships = {},
    reactions = get_archetype_reactions(archetype),
    personality = get_archetype_personality(archetype)
  }
end

-- =============================================================================
-- ARCHETYPE DATA (defaults — overridden by codec_14_behaviors when loaded)
-- =============================================================================

ARCHETYPE_ROUTINES = {
    merchant = {
      { start_hour = 8, end_hour = 18, location = "market", action = "T", probability = 0.9, interruptible = true },
      { start_hour = 18, end_hour = 22, location = "tavern", action = "R", probability = 0.6, interruptible = true },
      { start_hour = 22, end_hour = 8, location = "home", action = "R", probability = 0.95, interruptible = false }
    },
    hacker_drone = {
      { start_hour = 0, end_hour = 6, location = "network_node", action = "P", probability = 0.8, interruptible = false },
      { start_hour = 6, end_hour = 14, location = "safehouse", action = "R", probability = 0.85, interruptible = false },
      { start_hour = 14, end_hour = 20, location = "crowd", action = "H", probability = 0.7, interruptible = true },
      { start_hour = 20, end_hour = 24, location = "black_market", action = "T", probability = 0.5, interruptible = true }
    },
    street_samurai = {
      { start_hour = 6, end_hour = 12, location = "dojo", action = "train", probability = 0.8, interruptible = false },
      { start_hour = 12, end_hour = 22, location = "territory", action = "patrol", probability = 0.9, interruptible = true },
      { start_hour = 22, end_hour = 6, location = "home", action = "R", probability = 0.7, interruptible = false }
    }
}

ARCHETYPE_REACTIONS = {
    default = {
        ["event:fire"] = { action = "evacuate", probability = 0.99 },
        ["event:blackout"] = { action = "opportunistic", probability = 0.3 },
        ["event:festival"] = { action = "celebrate", probability = 0.5 }
    }
}

ARCHETYPE_PERSONALITIES = {
    merchant = { greed = 0.7, caution = 0.6, sociability = 0.8 },
    hacker_drone = { stealth = 0.9, greed = 0.7, paranoia = 0.8 },
    street_samurai = { honor = 0.8, aggression = 0.6, loyalty = 0.7 }
}

-- =============================================================================
-- COMMUTE CONFIG (from codec_29 when loaded)
-- =============================================================================

COMMUTE_CONFIG = {
    transport_modes = {},
    congestion = { peak_hours = {7, 8, 9, 17, 18}, congestion_multiplier = 1.4 }
}

function get_archetype_routine(archetype)
  return ARCHETYPE_ROUTINES[archetype] or ARCHETYPE_ROUTINES.merchant or {}
end

function get_archetype_reactions(archetype)
  return ARCHETYPE_REACTIONS[archetype] or ARCHETYPE_REACTIONS.default or {}
end

function get_archetype_personality(archetype)
  return ARCHETYPE_PERSONALITIES[archetype] or { neutral = 0.5 }
end

-- Calculate commute time penalty using codec_29 config
function calculate_commute_time(distance, hour, wealth)
    local modes = COMMUTE_CONFIG.transport_modes
    if not modes or not next(modes) then
        return 1  -- No commute data loaded, default 1 tick
    end
    
    -- Find best affordable mode
    local best_mode = "walk"
    local best_speed = 1.0
    for mode_name, mode in pairs(modes) do
        if (mode.max_distance or 999) >= distance then
            if mode.cost_per_trip == 0 or (wealth and wealth >= mode.cost_per_trip * 10) then
                if (mode.speed_factor or 1.0) > best_speed then
                    best_speed = mode.speed_factor
                    best_mode = mode_name
                end
            end
        end
    end
    
    -- Apply congestion during peak hours
    local congestion = 1.0
    for _, peak in ipairs(COMMUTE_CONFIG.congestion.peak_hours or {}) do
        if hour == peak then
            congestion = COMMUTE_CONFIG.congestion.congestion_multiplier or 1.4
            break
        end
    end
    
    return math.ceil(distance / best_speed * congestion)
end

-- =============================================================================
-- CODEC CALLBACKS
-- =============================================================================

-- When codec_14_behaviors is loaded, extract archetype data
codec.on("behaviors", function(data)
    if data.archetype_routines then
        ARCHETYPE_ROUTINES = codec.deep_merge(ARCHETYPE_ROUTINES, data.archetype_routines)
    end
    if data.archetype_reactions then
        ARCHETYPE_REACTIONS = codec.deep_merge(ARCHETYPE_REACTIONS, data.archetype_reactions)
    end
    if data.archetype_personalities then
        ARCHETYPE_PERSONALITIES = codec.deep_merge(ARCHETYPE_PERSONALITIES, data.archetype_personalities)
    end
end)

-- When codec_29_commuting is loaded, extract transport data
codec.on("commuting", function(data)
    if data.commuting then
        if data.commuting.transport_modes then
            COMMUTE_CONFIG.transport_modes = data.commuting.transport_modes
        end
        if data.commuting.congestion then
            COMMUTE_CONFIG.congestion = codec.deep_merge(COMMUTE_CONFIG.congestion, data.commuting.congestion)
        end
    end
end)

-- Register standard LoadCodec handler
codec.register_handler()

function persist_events()
  -- In production: Upload to Arweave via bundler
  -- This is a placeholder - actual upload happens client-side
  print("Would persist " .. #Events .. " event batches to Arweave")
end

--[[
  MULTIVERSE: Bleed Manifestation Helper
  
  Determines how a layer bleed manifests for an NPC.
]]--
function get_bleed_manifestation(seed)
  return BLEED_TYPES[(seed % #BLEED_TYPES) + 1]
end

-- Register with layer event bus (multiverse backbone)
Handlers.add("register-layer-bus", Handlers.utils.hasMatchingTag("Action", "register-layer-bus"), function(msg)
  LAYER_BUS = msg.From
  ao.send({
    Target = LAYER_BUS,
    Action = "register-layer",
    Data = json.encode({
      layer_id = DistrictId .. "_layer",
      layer_number = 0,
      parent_layer = "prime",
      status = "active",
      description = "District " .. DistrictId .. " in prime layer",
      districts = { DistrictId }
    })
  })
  print("Registered with Layer Event Bus: " .. LAYER_BUS)
end)

-- Export for testing
return {
  calculate_npc_location = calculate_npc_location,
  can_interact = can_interact,
  decide_action = decide_action,
  get_bleed_manifestation = get_bleed_manifestation,
  calculate_commute_time = calculate_commute_time,
  -- Codec-backed config (access for external processes)
  ARCHETYPE_ROUTINES = ARCHETYPE_ROUTINES,
  ARCHETYPE_REACTIONS = ARCHETYPE_REACTIONS,
  ARCHETYPE_PERSONALITIES = ARCHETYPE_PERSONALITIES,
  COMMUTE_CONFIG = COMMUTE_CONFIG
}
