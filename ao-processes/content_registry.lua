--[[
  AO World Engine - Content Registry
  
  The master registry for adding:
  - New NPCs and characters
  - New lore and storylines
  - New locations and buildings
  - New factions
  
  All content is pluggable and can be added dynamically.
]]--

local json = require("json")

-- =============================================================================
-- CONTENT REGISTRIES
-- =============================================================================

-- Main content store
CONTENT_REGISTRY = {
    npcs = {},
    lore = {},
    locations = {},
    storylines = {},
    items = {},
    dialogues = {}
}

-- =============================================================================
-- NPC REGISTRATION
-- =============================================================================

function register_npc(npc_id, definition)
    local npc = {
        id = npc_id,
        code = definition.code or npc_id,
        name = definition.name,
        
        -- Identity
        gender = definition.gender,
        age = definition.age,
        generation = definition.generation or 1,
        archetype = definition.archetype,
        
        -- Affiliation
        faction = definition.faction,
        occupation = definition.occupation,
        
        -- Location
        home_district = definition.home_district,
        home_building = definition.home_building,
        work_location = definition.work_location,
        
        -- Markers for encounters
        markers = definition.markers or {},
        
        -- Relationships (NPC_ID -> relationship type)
        relationships = definition.relationships or {},
        
        -- Personality (Big Five)
        personality = definition.personality or {
            openness = 0.5,
            conscientiousness = 0.5,
            extraversion = 0.5,
            agreeableness = 0.5,
            neuroticism = 0.5
        },
        
        -- Visual description
        visual = definition.visual,
        catchphrases = definition.catchphrases or {},
        backstory = definition.backstory,
        
        -- Cybernetics
        cybernetics = definition.cybernetics or {},
        
        -- Skills
        skills = definition.skills or {},
        
        -- State
        active = true,
        created_at = os.time()
    }
    
    CONTENT_REGISTRY.npcs[npc_id] = npc
    
    -- Auto-set markers based on faction
    if npc.faction then
        table.insert(npc.markers, npc.faction .. "_affiliated")
    end
    if npc.occupation then
        table.insert(npc.markers, "occupation_" .. npc.occupation)
    end
    
    return npc
end

-- Get NPC
function get_npc(npc_id)
    return CONTENT_REGISTRY.npcs[npc_id]
end

-- Search NPCs
function search_npcs(filter)
    local results = {}
    
    for id, npc in pairs(CONTENT_REGISTRY.npcs) do
        local match = true
        
        if filter.faction and npc.faction ~= filter.faction then
            match = false
        end
        if filter.occupation and npc.occupation ~= filter.occupation then
            match = false
        end
        if filter.district and npc.home_district ~= filter.district then
            match = false
        end
        if filter.marker then
            local has_marker = false
            for _, m in ipairs(npc.markers) do
                if m == filter.marker then
                    has_marker = true
                    break
                end
            end
            if not has_marker then match = false end
        end
        
        if match then
            table.insert(results, npc)
        end
    end
    
    return results
end

-- =============================================================================
-- LORE REGISTRATION
-- =============================================================================

function register_lore(lore_id, definition)
    local lore = {
        id = lore_id,
        title = definition.title,
        category = definition.category,  -- "history", "faction", "location", "character"
        
        -- Content
        content = definition.content,
        summary = definition.summary,
        
        -- References
        related_npcs = definition.related_npcs or {},
        related_locations = definition.related_locations or {},
        related_factions = definition.related_factions or {},
        
        -- Timeline placement
        year = definition.year,
        era = definition.era,  -- "pre_echo", "echo_rise", "current"
        
        -- Discovery
        discoverable = definition.discoverable ~= false,
        discovery_markers = definition.discovery_markers or {},  -- Markers needed to find this
        
        -- State
        created_at = os.time()
    }
    
    CONTENT_REGISTRY.lore[lore_id] = lore
    return lore
end

-- Get lore
function get_lore(lore_id)
    return CONTENT_REGISTRY.lore[lore_id]
end

-- =============================================================================
-- LOCATION REGISTRATION
-- =============================================================================

function register_location(location_id, definition)
    local location = {
        id = location_id,
        name = definition.name,
        type = definition.type,  -- "building", "district", "landmark", "hidden"
        
        -- Geography
        district = definition.district,
        coordinates = definition.coordinates,
        
        -- Ownership
        owner_faction = definition.owner_faction,
        owner_npc = definition.owner_npc,
        
        -- Activity
        activities = definition.activities or {},
        typical_occupations = definition.typical_occupations or {},
        
        -- Faction hangout
        faction_hangout = definition.faction_hangout,  -- Which faction hangs out here
        
        -- Access
        public = definition.public ~= false,
        required_faction = definition.required_faction,
        required_markers = definition.required_markers or {},
        
        -- Schedule
        open_hours = definition.open_hours or {0, 24},  -- 24/7 by default
        
        -- Capacity
        capacity = definition.capacity or 50,
        
        -- State
        created_at = os.time()
    }
    
    CONTENT_REGISTRY.locations[location_id] = location
    return location
end

-- Get location
function get_location(location_id)
    return CONTENT_REGISTRY.locations[location_id]
end

-- Get faction hangouts
function get_faction_hangouts(faction_id)
    local hangouts = {}
    for id, loc in pairs(CONTENT_REGISTRY.locations) do
        if loc.faction_hangout == faction_id then
            table.insert(hangouts, loc)
        end
    end
    return hangouts
end

-- =============================================================================
-- STORYLINE REGISTRATION
-- =============================================================================

function register_storyline(storyline_id, definition)
    local storyline = {
        id = storyline_id,
        name = definition.name,
        description = definition.description,
        
        -- Triggers
        trigger_markers = definition.trigger_markers or {},
        trigger_location = definition.trigger_location,
        trigger_faction = definition.trigger_faction,
        trigger_chance = definition.trigger_chance or 0.1,
        
        -- NPCs involved
        main_npcs = definition.main_npcs or {},
        supporting_npcs = definition.supporting_npcs or {},
        
        -- Locations
        locations = definition.locations or {},
        
        -- Steps
        steps = definition.steps or {},
        
        -- Prerequisites
        required_storylines = definition.required_storylines or {},
        required_lore = definition.required_lore or {},
        
        -- Outcomes
        outcomes = definition.outcomes or {},
        
        -- State
        active = false,
        completed = false,
        current_step = 0,
        created_at = os.time()
    }
    
    CONTENT_REGISTRY.storylines[storyline_id] = storyline
    return storyline
end

-- Progress storyline
function progress_storyline(storyline_id)
    local storyline = CONTENT_REGISTRY.storylines[storyline_id]
    if not storyline then return nil end
    
    storyline.current_step = storyline.current_step + 1
    
    if storyline.current_step >= #storyline.steps then
        storyline.completed = true
        storyline.active = false
    end
    
    return storyline
end

-- =============================================================================
-- DIALOGUE REGISTRATION
-- =============================================================================

function register_dialogue(dialogue_id, definition)
    local dialogue = {
        id = dialogue_id,
        npc_id = definition.npc_id,
        
        -- Trigger conditions
        trigger_markers = definition.trigger_markers or {},
        trigger_location = definition.trigger_location,
        trigger_storyline = definition.trigger_storyline,
        trigger_time = definition.trigger_time,  -- {min_hour, max_hour}
        
        -- Priority (higher = shown first)
        priority = definition.priority or 50,
        
        -- Content
        lines = definition.lines or {},  -- Array of dialogue lines
        
        -- Responses (player choices)
        responses = definition.responses or {},
        
        -- Effects
        effects = definition.effects or {},  -- Markers to add, reputation changes, etc.
        
        -- One-time or repeatable
        once = definition.once or false,
        delivered = false,
        
        -- State
        created_at = os.time()
    }
    
    CONTENT_REGISTRY.dialogues[dialogue_id] = dialogue
    return dialogue
end

-- Get available dialogues for NPC
function get_available_dialogues(npc_id, context)
    local dialogues = {}
    
    for id, dialogue in pairs(CONTENT_REGISTRY.dialogues) do
        if dialogue.npc_id == npc_id and not (dialogue.once and dialogue.delivered) then
            -- Check context conditions
            local available = true
            
            -- TODO: Check markers, location, storyline, time
            
            if available then
                table.insert(dialogues, dialogue)
            end
        end
    end
    
    -- Sort by priority
    table.sort(dialogues, function(a, b) return a.priority > b.priority end)
    
    return dialogues
end

-- =============================================================================
-- BULK IMPORT
-- =============================================================================

-- Import content from JSON
function import_content(content_json)
    local content = json.decode(content_json)
    local counts = {npcs = 0, lore = 0, locations = 0, storylines = 0, dialogues = 0}
    
    if content.npcs then
        for id, def in pairs(content.npcs) do
            register_npc(id, def)
            counts.npcs = counts.npcs + 1
        end
    end
    
    if content.lore then
        for id, def in pairs(content.lore) do
            register_lore(id, def)
            counts.lore = counts.lore + 1
        end
    end
    
    if content.locations then
        for id, def in pairs(content.locations) do
            register_location(id, def)
            counts.locations = counts.locations + 1
        end
    end
    
    if content.storylines then
        for id, def in pairs(content.storylines) do
            register_storyline(id, def)
            counts.storylines = counts.storylines + 1
        end
    end
    
    if content.dialogues then
        for id, def in pairs(content.dialogues) do
            register_dialogue(id, def)
            counts.dialogues = counts.dialogues + 1
        end
    end
    
    return counts
end

-- Export all content
function export_content()
    return {
        npcs = CONTENT_REGISTRY.npcs,
        lore = CONTENT_REGISTRY.lore,
        locations = CONTENT_REGISTRY.locations,
        storylines = CONTENT_REGISTRY.storylines,
        dialogues = CONTENT_REGISTRY.dialogues
    }
end

-- =============================================================================
-- STATISTICS
-- =============================================================================

function get_content_stats()
    return {
        npcs = table_count(CONTENT_REGISTRY.npcs),
        lore = table_count(CONTENT_REGISTRY.lore),
        locations = table_count(CONTENT_REGISTRY.locations),
        storylines = table_count(CONTENT_REGISTRY.storylines),
        dialogues = table_count(CONTENT_REGISTRY.dialogues)
    }
end

function table_count(t)
    local count = 0
    for _ in pairs(t) do count = count + 1 end
    return count
end

-- =============================================================================
-- AO MESSAGE HANDLERS
-- =============================================================================

Handlers.add("RegisterNpc", Handlers.utils.hasMatchingTag("Action", "RegisterNpc"),
    function(msg)
        local npc_id = msg.Tags["NpcId"]
        local definition = json.decode(msg.Data or "{}")
        
        local npc = register_npc(npc_id, definition)
        
        ao.send({
            Target = msg.From,
            Data = json.encode(npc)
        })
    end
)

Handlers.add("RegisterLore", Handlers.utils.hasMatchingTag("Action", "RegisterLore"),
    function(msg)
        local lore_id = msg.Tags["LoreId"]
        local definition = json.decode(msg.Data or "{}")
        
        local lore = register_lore(lore_id, definition)
        
        ao.send({
            Target = msg.From,
            Data = json.encode(lore)
        })
    end
)

Handlers.add("RegisterLocation", Handlers.utils.hasMatchingTag("Action", "RegisterLocation"),
    function(msg)
        local location_id = msg.Tags["LocationId"]
        local definition = json.decode(msg.Data or "{}")
        
        local location = register_location(location_id, definition)
        
        ao.send({
            Target = msg.From,
            Data = json.encode(location)
        })
    end
)

Handlers.add("ImportContent", Handlers.utils.hasMatchingTag("Action", "ImportContent"),
    function(msg)
        local counts = import_content(msg.Data or "{}")
        
        ao.send({
            Target = msg.From,
            Data = json.encode({
                success = true,
                imported = counts
            })
        })
    end
)

Handlers.add("ExportContent", Handlers.utils.hasMatchingTag("Action", "ExportContent"),
    function(msg)
        local content = export_content()
        
        ao.send({
            Target = msg.From,
            Data = json.encode(content)
        })
    end
)

Handlers.add("GetContentStats", Handlers.utils.hasMatchingTag("Action", "GetContentStats"),
    function(msg)
        local stats = get_content_stats()
        
        ao.send({
            Target = msg.From,
            Data = json.encode(stats)
        })
    end
)

Handlers.add("SearchNpcs", Handlers.utils.hasMatchingTag("Action", "SearchNpcs"),
    function(msg)
        local filter = json.decode(msg.Data or "{}")
        local results = search_npcs(filter)
        
        ao.send({
            Target = msg.From,
            Data = json.encode(results)
        })
    end
)

-- =============================================================================
-- EXPORT
-- =============================================================================

return {
    -- Registry
    CONTENT_REGISTRY = CONTENT_REGISTRY,
    
    -- NPCs
    register_npc = register_npc,
    get_npc = get_npc,
    search_npcs = search_npcs,
    
    -- Lore
    register_lore = register_lore,
    get_lore = get_lore,
    
    -- Locations
    register_location = register_location,
    get_location = get_location,
    get_faction_hangouts = get_faction_hangouts,
    
    -- Storylines
    register_storyline = register_storyline,
    progress_storyline = progress_storyline,
    
    -- Dialogues
    register_dialogue = register_dialogue,
    get_available_dialogues = get_available_dialogues,
    
    -- Bulk
    import_content = import_content,
    export_content = export_content,
    
    -- Stats
    get_content_stats = get_content_stats
}
