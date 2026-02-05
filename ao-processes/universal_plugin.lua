--[[
  AO World Engine - Universal Plugin System
  
  The core architecture for ANY content type:
  - Add JSON → content appears
  - Marker-based interactions
  - Characters seek matching traits
  - Future-proof for unknown plugins
]]--

local json = require("json")

-- =============================================================================
-- UNIVERSAL ENTITY REGISTRY
-- =============================================================================

--[[
  Any content type can be registered here.
  NPCs interact with unknown content via shared markers.
]]--

ENTITY_TYPES = {
    -- Core types (registered by default modules)
    npc = true,
    vehicle = true,
    building = true,
    faction = true,
    occupation = true,
    
    -- Extensible - new types auto-register
}

ENTITIES = {}  -- entity_type -> entity_id -> entity

-- Register a new entity type
function register_entity_type(type_name, config)
    ENTITY_TYPES[type_name] = {
        name = type_name,
        description = config.description,
        
        -- Required fields for entities of this type
        required_fields = config.required or {},
        
        -- Default markers for all entities of this type
        default_markers = config.default_markers or {},
        
        -- Spawn behavior
        gradual_spawn = config.gradual_spawn or false,
        
        -- NPC interaction config
        npc_can_interact = config.npc_can_interact ~= false,
        npc_can_own = config.npc_can_own or false,
        
        -- Created at
        registered_at = os.time()
    }
    
    ENTITIES[type_name] = ENTITIES[type_name] or {}
    
    return ENTITY_TYPES[type_name]
end

-- Register any entity
function register_entity(entity_type, entity_id, definition)
    -- Auto-register unknown types
    if not ENTITY_TYPES[entity_type] then
        register_entity_type(entity_type, {
            description = "Auto-registered type: " .. entity_type
        })
    end
    
    local type_config = ENTITY_TYPES[entity_type]
    
    local entity = {
        id = entity_id,
        entity_type = entity_type,
        name = definition.name,
        
        -- Core identity
        data = definition,
        
        -- Markers for interaction (THE KEY)
        markers = merge_markers(
            type_config.default_markers or {},
            definition.markers or {}
        ),
        
        -- Seekable traits (NPCs look for these)
        seekable_traits = definition.seekable_traits or {},
        
        -- Action triggers (what NPCs can do with this)
        action_triggers = definition.action_triggers or {},
        
        -- Rarity for gradual spawning
        rarity = definition.rarity or 0.5,
        
        -- Location binding
        location = definition.location,
        district = definition.district,
        
        -- Owner
        owner_npc = definition.owner_npc,
        owner_faction = definition.owner_faction,
        
        -- State
        active = true,
        spawned = definition.spawned ~= false,
        registered_at = os.time()
    }
    
    ENTITIES[entity_type][entity_id] = entity
    
    return entity
end

-- Merge marker arrays
function merge_markers(base, additional)
    local result = {}
    local seen = {}
    
    for _, m in ipairs(base) do
        if not seen[m] then
            table.insert(result, m)
            seen[m] = true
        end
    end
    
    for _, m in ipairs(additional) do
        if not seen[m] then
            table.insert(result, m)
            seen[m] = true
        end
    end
    
    return result
end

-- Get entity
function get_entity(entity_type, entity_id)
    if ENTITIES[entity_type] then
        return ENTITIES[entity_type][entity_id]
    end
    return nil
end

-- =============================================================================
-- MARKER-BASED DISCOVERY
-- =============================================================================

--[[
  NPCs automatically discover and interact with content
  based on shared markers.
  
  Example:
  - NPC has marker "tech_enthusiast"
  - New gadget entity has marker "tech_enthusiast"
  → NPC will seek out this gadget
]]--

-- Search for entities that match NPC markers
function find_matching_entities(npc_markers, entity_type, max_results)
    max_results = max_results or 10
    local results = {}
    
    local entities = entity_type and ENTITIES[entity_type] or get_all_entities()
    
    for _, entity in pairs(entities) do
        local match_score = calculate_marker_match(npc_markers, entity.markers)
        
        if match_score > 0 then
            table.insert(results, {
                entity = entity,
                score = match_score
            })
        end
    end
    
    -- Sort by score
    table.sort(results, function(a, b) return a.score > b.score end)
    
    -- Limit results
    local limited = {}
    for i = 1, math.min(max_results, #results) do
        table.insert(limited, results[i])
    end
    
    return limited
end

-- Get all entities across types
function get_all_entities()
    local all = {}
    for entity_type, entities in pairs(ENTITIES) do
        for entity_id, entity in pairs(entities) do
            table.insert(all, entity)
        end
    end
    return all
end

-- Calculate match score between NPC markers and entity markers
function calculate_marker_match(npc_markers, entity_markers)
    local matches = 0
    
    for _, nm in ipairs(npc_markers) do
        for _, em in ipairs(entity_markers) do
            if nm == em then
                matches = matches + 1
            end
        end
    end
    
    return matches
end

-- =============================================================================
-- SEEKABLE TRAITS
-- =============================================================================

--[[
  Entities can have seekable_traits that NPCs actively look for.
  
  Example:
  - School entity has seekable_trait "education"
  - NPC with need "purpose" and marker "student" will seek it
]]--

TRAIT_SEEKERS = {}  -- marker -> list of NPC IDs seeking this

-- Register NPC as seeking a trait
function register_trait_seeker(npc_id, trait)
    if not TRAIT_SEEKERS[trait] then
        TRAIT_SEEKERS[trait] = {}
    end
    table.insert(TRAIT_SEEKERS[trait], npc_id)
end

-- Find entities with a seekable trait
function find_by_trait(trait, max_results)
    max_results = max_results or 10
    local results = {}
    
    for entity_type, entities in pairs(ENTITIES) do
        for entity_id, entity in pairs(entities) do
            for _, t in ipairs(entity.seekable_traits or {}) do
                if t == trait then
                    table.insert(results, entity)
                end
            end
        end
    end
    
    return results
end

-- =============================================================================
-- ACTION TRIGGERS
-- =============================================================================

--[[
  Entities can define actions that NPCs with matching markers can perform.
  
  Example:
  - Bar entity has action_trigger "drink" requiring marker "drinker"
  - NPC with marker "drinker" can perform "drink" action at bar
]]--

-- Check if NPC can perform action on entity
function can_perform_action(npc_id, entity, action)
    local triggers = entity.action_triggers or {}
    
    if not triggers[action] then
        return false
    end
    
    local required_markers = triggers[action].required_markers or {}
    local npc_markers = get_npc_markers and get_npc_markers(npc_id) or {}
    
    -- Check all required markers
    for _, required in ipairs(required_markers) do
        local has = false
        for _, nm in ipairs(npc_markers) do
            if nm == required then
                has = true
                break
            end
        end
        if not has then return false end
    end
    
    return true
end

-- Get available actions for NPC on entity
function get_available_actions(npc_id, entity)
    local available = {}
    
    for action, config in pairs(entity.action_triggers or {}) do
        if can_perform_action(npc_id, entity, action) then
            table.insert(available, {
                action = action,
                config = config
            })
        end
    end
    
    return available
end

-- =============================================================================
-- GRADUAL CONTENT APPEARANCE
-- =============================================================================

CONTENT_QUEUE = {}

-- Queue content to appear gradually
function queue_content(entity_type, entities, over_ticks)
    local per_tick = #entities / over_ticks
    
    table.insert(CONTENT_QUEUE, {
        entity_type = entity_type,
        entities = entities,
        remaining = #entities,
        index = 1,
        per_tick = per_tick,
        accumulator = 0
    })
end

-- Process content queue (call on tick)
function process_content_queue()
    local spawned = {}
    
    for i, entry in ipairs(CONTENT_QUEUE) do
        if entry.index <= #entry.entities then
            entry.accumulator = entry.accumulator + entry.per_tick
            
            while entry.accumulator >= 1 and entry.index <= #entry.entities do
                local def = entry.entities[entry.index]
                local entity = register_entity(entry.entity_type, def.id, def)
                entity.spawned = true
                table.insert(spawned, entity)
                
                entry.accumulator = entry.accumulator - 1
                entry.index = entry.index + 1
            end
        end
    end
    
    -- Clean up completed
    local i = 1
    while i <= #CONTENT_QUEUE do
        if CONTENT_QUEUE[i].index > #CONTENT_QUEUE[i].entities then
            table.remove(CONTENT_QUEUE, i)
        else
            i = i + 1
        end
    end
    
    return spawned
end

-- =============================================================================
-- UNIVERSAL IMPORT (Add JSON → content appears)
-- =============================================================================

function import_json(json_string)
    local data = json.decode(json_string)
    local counts = {}
    
    -- Process each entity type in JSON
    for entity_type, entities in pairs(data) do
        counts[entity_type] = 0
        
        if type(entities) == "table" then
            -- Check if gradual spawn is requested
            local gradual = data._gradual or {}
            local spawn_over = gradual[entity_type]
            
            if spawn_over then
                -- Queue for gradual appearance
                local list = {}
                for id, def in pairs(entities) do
                    def.id = def.id or id
                    table.insert(list, def)
                end
                queue_content(entity_type, list, spawn_over)
                counts[entity_type] = #list
            else
                -- Immediate registration
                for id, def in pairs(entities) do
                    register_entity(entity_type, id, def)
                    counts[entity_type] = counts[entity_type] + 1
                end
            end
        end
    end
    
    return counts
end

-- =============================================================================
-- STATS
-- =============================================================================

function get_plugin_stats()
    local stats = {
        entity_types = 0,
        total_entities = 0,
        by_type = {}
    }
    
    for entity_type, _ in pairs(ENTITY_TYPES) do
        stats.entity_types = stats.entity_types + 1
    end
    
    for entity_type, entities in pairs(ENTITIES) do
        local count = 0
        for _ in pairs(entities) do
            count = count + 1
        end
        stats.by_type[entity_type] = count
        stats.total_entities = stats.total_entities + count
    end
    
    return stats
end

-- =============================================================================
-- AO MESSAGE HANDLERS
-- =============================================================================

Handlers.add("RegisterEntityType", Handlers.utils.hasMatchingTag("Action", "RegisterEntityType"),
    function(msg)
        local type_name = msg.Tags["TypeName"]
        local config = json.decode(msg.Data or "{}")
        
        local etype = register_entity_type(type_name, config)
        
        ao.send({
            Target = msg.From,
            Data = json.encode(etype)
        })
    end
)

Handlers.add("RegisterEntity", Handlers.utils.hasMatchingTag("Action", "RegisterEntity"),
    function(msg)
        local entity_type = msg.Tags["EntityType"]
        local entity_id = msg.Tags["EntityId"]
        local definition = json.decode(msg.Data or "{}")
        
        local entity = register_entity(entity_type, entity_id, definition)
        
        ao.send({
            Target = msg.From,
            Data = json.encode(entity)
        })
    end
)

Handlers.add("ImportJson", Handlers.utils.hasMatchingTag("Action", "ImportJson"),
    function(msg)
        local counts = import_json(msg.Data or "{}")
        
        ao.send({
            Target = msg.From,
            Data = json.encode({
                success = true,
                imported = counts
            })
        })
    end
)

Handlers.add("FindMatchingEntities", Handlers.utils.hasMatchingTag("Action", "FindMatchingEntities"),
    function(msg)
        local npc_markers = json.decode(msg.Data or "[]")
        local entity_type = msg.Tags["EntityType"]
        
        local results = find_matching_entities(npc_markers, entity_type)
        
        ao.send({
            Target = msg.From,
            Data = json.encode(results)
        })
    end
)

Handlers.add("GetAvailableActions", Handlers.utils.hasMatchingTag("Action", "GetAvailableActions"),
    function(msg)
        local npc_id = msg.Tags["NpcId"]
        local entity_type = msg.Tags["EntityType"]
        local entity_id = msg.Tags["EntityId"]
        
        local entity = get_entity(entity_type, entity_id)
        local actions = entity and get_available_actions(npc_id, entity) or {}
        
        ao.send({
            Target = msg.From,
            Data = json.encode(actions)
        })
    end
)

Handlers.add("ProcessContentQueue", Handlers.utils.hasMatchingTag("Action", "ProcessContentQueue"),
    function(msg)
        local spawned = process_content_queue()
        
        ao.send({
            Target = msg.From,
            Data = json.encode({spawned_count = #spawned})
        })
    end
)

Handlers.add("GetPluginStats", Handlers.utils.hasMatchingTag("Action", "GetPluginStats"),
    function(msg)
        local stats = get_plugin_stats()
        
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
    -- Types
    ENTITY_TYPES = ENTITY_TYPES,
    register_entity_type = register_entity_type,
    
    -- Entities
    ENTITIES = ENTITIES,
    register_entity = register_entity,
    get_entity = get_entity,
    get_all_entities = get_all_entities,
    
    -- Discovery
    find_matching_entities = find_matching_entities,
    calculate_marker_match = calculate_marker_match,
    
    -- Traits
    TRAIT_SEEKERS = TRAIT_SEEKERS,
    register_trait_seeker = register_trait_seeker,
    find_by_trait = find_by_trait,
    
    -- Actions
    can_perform_action = can_perform_action,
    get_available_actions = get_available_actions,
    
    -- Gradual spawn
    CONTENT_QUEUE = CONTENT_QUEUE,
    queue_content = queue_content,
    process_content_queue = process_content_queue,
    
    -- Import
    import_json = import_json,
    
    -- Stats
    get_plugin_stats = get_plugin_stats
}
