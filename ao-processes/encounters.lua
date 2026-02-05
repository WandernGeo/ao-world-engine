--[[
  AO World Engine - Encounter & Mission System
  
  Marker-based encounters with probability triggers:
  - JSON markers on NPCs determine encounter chances
  - Location-based faction hangouts
  - Mission templates (spy, rob, deliver, recruit)
  - Real city life scheduling
]]--

local json = require("json")

-- =============================================================================
-- ENCOUNTER MARKERS
-- =============================================================================

--[[
  Markers are tags on NPCs that affect encounter probabilities.
  Format in NPC JSON:
  {
    "markers": ["code_xyz", "marker_a3802", "faction_4491a"]
  }
  
  Marker rules define what happens when markers match.
]]--

ENCOUNTER_MARKERS = {}

-- Register an encounter marker rule
function register_marker_rule(marker_id, rule)
    ENCOUNTER_MARKERS[marker_id] = {
        id = marker_id,
        description = rule.description,
        
        -- Base chance when NPC has this marker
        base_chance = rule.base_chance or 0.05,  -- 5% default
        
        -- Modifier when other NPC also has certain markers
        marker_modifiers = rule.marker_modifiers or {},
        
        -- Locations where this marker increases encounters
        location_modifiers = rule.location_modifiers or {},
        
        -- Faction hangouts
        faction_hangouts = rule.faction_hangouts or {},
        
        -- Time modifiers (hour of day)
        time_modifiers = rule.time_modifiers or {},
        
        -- What triggers on encounter
        triggers = rule.triggers or {}
    }
    
    return ENCOUNTER_MARKERS[marker_id]
end

-- =============================================================================
-- DEFAULT MARKER RULES
-- =============================================================================

function init_default_markers()
    -- Story markers
    register_marker_rule("story_charlie_intro", {
        description = "Charlie's introduction storyline",
        base_chance = 0.9,  -- 90% chance if conditions met
        marker_modifiers = {
            resistance_member = 1.5
        },
        location_modifiers = {
            back_alley = 2.0,
            cantina = 1.5
        }
    })
    
    -- Faction encounter markers
    register_marker_rule("resistance_affiliated", {
        description = "Resistance affiliation",
        base_chance = 0.1,
        marker_modifiers = {
            resistance_affiliated = 1.5,  -- Resistance members find each other
            echo_agent = 0.2  -- Avoid ECHO
        },
        faction_hangouts = {
            resistance = {"safehouse_7", "back_alley_cantina", "old_chinatown"}
        }
    })
    
    register_marker_rule("underground_connected", {
        description = "Underground connections",
        base_chance = 0.15,
        marker_modifiers = {
            underground_connected = 1.8,
            police = 0.1
        },
        faction_hangouts = {
            underground = {"undercity_bar", "fence_shop", "smuggler_dock"}
        }
    })
    
    register_marker_rule("temple_faithful", {
        description = "Temple of Signal believer",
        base_chance = 0.2,
        location_modifiers = {
            temple_of_signal = 3.0,
            temple_district = 2.0
        }
    })
    
    register_marker_rule("echo_agent", {
        description = "ECHO Corp agent",
        base_chance = 0.05,
        marker_modifiers = {
            resistance_affiliated = 0.3,
            underground_connected = 0.3
        },
        location_modifiers = {
            corporate_tower = 2.0,
            surveillance_hub = 2.5
        }
    })
    
    -- Random encounter markers
    register_marker_rule("common_citizen", {
        description = "Regular city resident",
        base_chance = 0.03,
        time_modifiers = {
            morning_commute = 1.5,  -- 7-9 AM
            lunch_rush = 1.3,       -- 12-1 PM
            evening_commute = 1.5   -- 5-7 PM
        }
    })
    
    register_marker_rule("night_owl", {
        description = "Active at night",
        base_chance = 0.1,
        time_modifiers = {
            night = 2.0,  -- 10 PM - 4 AM
            day = 0.3
        }
    })
end

-- =============================================================================
-- ENCOUNTER CALCULATION
-- =============================================================================

-- NPC markers cache
NPC_MARKERS = {}  -- npc_id -> list of markers

-- Set markers for NPC
function set_npc_markers(npc_id, markers)
    NPC_MARKERS[npc_id] = markers or {}
end

-- Get NPC markers
function get_npc_markers(npc_id)
    return NPC_MARKERS[npc_id] or {}
end

-- Add marker to NPC
function add_marker(npc_id, marker_id)
    if not NPC_MARKERS[npc_id] then
        NPC_MARKERS[npc_id] = {}
    end
    table.insert(NPC_MARKERS[npc_id], marker_id)
end

-- Calculate encounter probability between two NPCs
function calculate_encounter_chance(npc_a_id, npc_b_id, context)
    context = context or {}
    local location = context.location
    local hour = context.hour or 12
    local building = context.building
    
    local markers_a = get_npc_markers(npc_a_id)
    local markers_b = get_npc_markers(npc_b_id)
    
    local total_chance = 0
    local max_chance = 0
    
    -- Check each marker on NPC A
    for _, marker_id in ipairs(markers_a) do
        local rule = ENCOUNTER_MARKERS[marker_id]
        if rule then
            local chance = rule.base_chance
            
            -- Apply marker modifiers from NPC B
            for _, other_marker in ipairs(markers_b) do
                if rule.marker_modifiers[other_marker] then
                    chance = chance * rule.marker_modifiers[other_marker]
                end
            end
            
            -- Apply location modifiers
            if location and rule.location_modifiers[location] then
                chance = chance * rule.location_modifiers[location]
            end
            if building and rule.location_modifiers[building] then
                chance = chance * rule.location_modifiers[building]
            end
            
            -- Apply time modifiers
            local time_period = get_time_period(hour)
            if rule.time_modifiers[time_period] then
                chance = chance * rule.time_modifiers[time_period]
            end
            
            max_chance = math.max(max_chance, chance)
            total_chance = total_chance + chance
        end
    end
    
    -- Use max rather than sum to avoid exceeding 1.0
    return math.min(1.0, max_chance)
end

-- Get time period from hour
function get_time_period(hour)
    if hour >= 7 and hour < 9 then return "morning_commute"
    elseif hour >= 12 and hour < 13 then return "lunch_rush"
    elseif hour >= 17 and hour < 19 then return "evening_commute"
    elseif hour >= 22 or hour < 4 then return "night"
    else return "day"
    end
end

-- Check if encounter happens
function check_encounter(npc_a_id, npc_b_id, context)
    local chance = calculate_encounter_chance(npc_a_id, npc_b_id, context)
    return math.random() < chance, chance
end

-- =============================================================================
-- LOCATION ENCOUNTERS
-- =============================================================================

LOCATION_OCCUPATION = {}  -- location_id -> list of npc_ids currently there

-- Place NPC in location
function enter_location(npc_id, location_id)
    if not LOCATION_OCCUPATION[location_id] then
        LOCATION_OCCUPATION[location_id] = {}
    end
    table.insert(LOCATION_OCCUPATION[location_id], npc_id)
end

-- Remove NPC from location
function leave_location(npc_id, location_id)
    local npcs = LOCATION_OCCUPATION[location_id]
    if not npcs then return end
    
    for i, id in ipairs(npcs) do
        if id == npc_id then
            table.remove(npcs, i)
            break
        end
    end
end

-- Get all NPCs in a location
function get_npcs_in_location(location_id)
    return LOCATION_OCCUPATION[location_id] or {}
end

-- Process all possible encounters in a location
function process_location_encounters(location_id, context)
    local npcs = get_npcs_in_location(location_id)
    local encounters = {}
    
    context = context or {}
    context.location = location_id
    
    for i = 1, #npcs do
        for j = i + 1, #npcs do
            local happened, chance = check_encounter(npcs[i], npcs[j], context)
            if happened then
                table.insert(encounters, {
                    npc_a = npcs[i],
                    npc_b = npcs[j],
                    location = location_id,
                    chance = chance,
                    timestamp = os.time()
                })
            end
        end
    end
    
    return encounters
end

-- =============================================================================
-- MISSION TEMPLATES (Pluggable)
-- =============================================================================

MISSION_TEMPLATES = {}

function register_mission_template(template_id, definition)
    MISSION_TEMPLATES[template_id] = {
        id = template_id,
        name = definition.name,
        category = definition.category,  -- "espionage", "theft", "delivery", "recruitment"
        
        -- Faction associations
        source_factions = definition.source_factions,
        target_factions = definition.target_factions,
        
        -- Requirements
        required_occupation = definition.required_occupation,
        required_markers = definition.required_markers or {},
        
        -- Parameters
        difficulty = definition.difficulty or 0.5,
        duration_ticks = definition.duration or 10,
        reward = definition.reward or { credits = 100 },
        
        -- Locations
        origin_locations = definition.origins or {},
        target_locations = definition.targets or {},
        
        -- Outcomes
        success_effects = definition.on_success or {},
        failure_effects = definition.on_failure or {},
        
        -- Description template
        description = definition.description
    }
    
    return MISSION_TEMPLATES[template_id]
end

-- =============================================================================
-- DEFAULT MISSION TEMPLATES
-- =============================================================================

function init_mission_templates()
    -- ESPIONAGE
    register_mission_template("spy_on_faction", {
        name = "Faction Infiltration",
        category = "espionage",
        source_factions = {"resistance", "echo_corp", "underground"},
        target_factions = {"resistance", "echo_corp", "underground", "temple_of_signal"},
        required_markers = {"infiltrator", "spy_trained"},
        difficulty = 0.7,
        duration = 20,
        reward = { credits = 500, reputation = 10 },
        origins = {"safehouse", "hq"},
        targets = {"enemy_hq", "meeting_point"},
        on_success = {
            gain_intel = true,
            reputation_boost = 10
        },
        on_failure = {
            captured_chance = 0.5,
            reputation_loss = 20
        }
    })
    
    -- THEFT
    register_mission_template("rob_building", {
        name = "Building Heist",
        category = "theft",
        source_factions = {"underground", "resistance"},
        required_occupation = "thief",
        difficulty = 0.6,
        duration = 5,
        reward = { credits = 1000 },
        targets = {"corporate_tower", "warehouse", "bank"},
        on_success = {
            gain_credits = true,
            alert_level_increase = 5
        },
        on_failure = {
            arrested_chance = 0.4,
            injured_chance = 0.3
        }
    })
    
    register_mission_template("pickpocket", {
        name = "Pickpocket Target",
        category = "theft",
        source_factions = {"underground"},
        required_occupation = "thief",
        difficulty = 0.3,
        duration = 1,
        reward = { credits = 50 },
        on_success = {
            gain_credits = true
        },
        on_failure = {
            caught_chance = 0.6
        }
    })
    
    -- DELIVERY
    register_mission_template("smuggle_goods", {
        name = "Smuggle Contraband",
        category = "delivery",
        source_factions = {"underground"},
        required_occupation = "smuggler",
        difficulty = 0.5,
        duration = 8,
        reward = { credits = 300 },
        origins = {"port_district", "undercity"},
        targets = {"distribution_point", "buyer_location"},
        on_success = {
            gain_credits = true,
            faction_standing = 5
        },
        on_failure = {
            goods_seized = true,
            fine = 200
        }
    })
    
    register_mission_template("deliver_message", {
        name = "Courier Mission",
        category = "delivery",
        difficulty = 0.2,
        duration = 3,
        reward = { credits = 50 },
        on_success = {
            message_delivered = true
        }
    })
    
    -- RECRUITMENT
    register_mission_template("recruit_member", {
        name = "Faction Recruitment",
        category = "recruitment",
        source_factions = {"resistance", "temple_of_signal", "cyber_collective"},
        required_markers = {"charismatic", "recruiter"},
        difficulty = 0.4,
        duration = 5,
        reward = { reputation = 15 },
        on_success = {
            new_member = true,
            faction_growth = 1
        }
    })
    
    -- SABOTAGE
    register_mission_template("sabotage_facility", {
        name = "Facility Sabotage",
        category = "sabotage",
        source_factions = {"resistance", "cyber_collective"},
        target_factions = {"echo_corp"},
        required_markers = {"tech_skilled"},
        difficulty = 0.8,
        duration = 15,
        reward = { credits = 300, reputation = 20 },
        targets = {"power_station", "surveillance_hub", "factory"},
        on_success = {
            facility_disabled = true,
            faction_reputation_boost = 15
        },
        on_failure = {
            arrested_chance = 0.6,
            faction_reputation_loss = 10
        }
    })
    
    -- PROTECTION
    register_mission_template("protect_target", {
        name = "VIP Protection",
        category = "protection",
        required_occupation = "security",
        difficulty = 0.5,
        duration = 10,
        reward = { credits = 200 },
        on_success = {
            target_safe = true
        },
        on_failure = {
            target_harmed = true,
            reputation_loss = 30
        }
    })
    
    -- INVESTIGATION
    register_mission_template("investigate_lead", {
        name = "Investigation",
        category = "investigation",
        required_occupation = "reporter",
        difficulty = 0.4,
        duration = 12,
        reward = { credits = 150, news_story = true },
        on_success = {
            intel_gained = true,
            publish_option = true
        }
    })
end

-- =============================================================================
-- ACTIVE MISSIONS
-- =============================================================================

ACTIVE_MISSIONS = {}
MISSION_COUNTER = 0

-- Create a mission from template
function create_mission(template_id, config)
    local template = MISSION_TEMPLATES[template_id]
    if not template then return nil end
    
    MISSION_COUNTER = MISSION_COUNTER + 1
    
    local mission = {
        id = "MISSION_" .. MISSION_COUNTER,
        template_id = template_id,
        template = template,
        
        -- Assignment
        assigned_npc = config.assigned_npc,
        source_faction = config.source_faction,
        target_faction = config.target_faction,
        
        -- Locations
        origin = config.origin,
        target = config.target,
        
        -- State
        status = "active",  -- "active", "completed", "failed", "abandoned"
        progress = 0,
        started_at = os.time(),
        started_tick = WorldTick or 0,
        
        -- Custom parameters
        custom_reward = config.reward,
        custom_difficulty = config.difficulty
    }
    
    ACTIVE_MISSIONS[mission.id] = mission
    return mission
end

-- Progress a mission
function progress_mission(mission_id, amount)
    local mission = ACTIVE_MISSIONS[mission_id]
    if not mission or mission.status ~= "active" then return nil end
    
    mission.progress = mission.progress + (amount or 1)
    
    local template = mission.template
    if mission.progress >= template.duration_ticks then
        -- Check success
        local difficulty = mission.custom_difficulty or template.difficulty
        if math.random() > difficulty then
            complete_mission(mission_id, true)
        else
            complete_mission(mission_id, false)
        end
    end
    
    return mission
end

-- Complete a mission
function complete_mission(mission_id, success)
    local mission = ACTIVE_MISSIONS[mission_id]
    if not mission then return nil end
    
    mission.status = success and "completed" or "failed"
    mission.completed_at = os.time()
    
    -- Apply effects
    local effects = success and mission.template.success_effects or mission.template.failure_effects
    -- TODO: Apply effects to NPCs/factions
    
    return mission
end

-- Get missions for NPC
function get_npc_missions(npc_id)
    local missions = {}
    for id, mission in pairs(ACTIVE_MISSIONS) do
        if mission.assigned_npc == npc_id and mission.status == "active" then
            table.insert(missions, mission)
        end
    end
    return missions
end

-- =============================================================================
-- AO MESSAGE HANDLERS
-- =============================================================================

Handlers.add("SetNpcMarkers", Handlers.utils.hasMatchingTag("Action", "SetNpcMarkers"),
    function(msg)
        local npc_id = msg.Tags["NpcId"]
        local markers = json.decode(msg.Data or "[]")
        
        set_npc_markers(npc_id, markers)
        
        ao.send({
            Target = msg.From,
            Data = json.encode({success = true})
        })
    end
)

Handlers.add("CheckEncounter", Handlers.utils.hasMatchingTag("Action", "CheckEncounter"),
    function(msg)
        local npc_a = msg.Tags["NpcA"]
        local npc_b = msg.Tags["NpcB"]
        local context = json.decode(msg.Data or "{}")
        
        local happened, chance = check_encounter(npc_a, npc_b, context)
        
        ao.send({
            Target = msg.From,
            Data = json.encode({
                encounter = happened,
                chance = chance
            })
        })
    end
)

Handlers.add("ProcessLocationEncounters", Handlers.utils.hasMatchingTag("Action", "ProcessLocationEncounters"),
    function(msg)
        local location_id = msg.Tags["LocationId"]
        local context = json.decode(msg.Data or "{}")
        
        local encounters = process_location_encounters(location_id, context)
        
        ao.send({
            Target = msg.From,
            Data = json.encode(encounters)
        })
    end
)

Handlers.add("CreateMission", Handlers.utils.hasMatchingTag("Action", "CreateMission"),
    function(msg)
        local template_id = msg.Tags["TemplateId"]
        local config = json.decode(msg.Data or "{}")
        
        local mission = create_mission(template_id, config)
        
        ao.send({
            Target = msg.From,
            Data = json.encode(mission)
        })
    end
)

Handlers.add("ProgressMission", Handlers.utils.hasMatchingTag("Action", "ProgressMission"),
    function(msg)
        local mission_id = msg.Tags["MissionId"]
        local amount = tonumber(msg.Tags["Amount"]) or 1
        
        local mission = progress_mission(mission_id, amount)
        
        ao.send({
            Target = msg.From,
            Data = json.encode(mission or {error = "not_found"})
        })
    end
)

-- =============================================================================
-- EXPORT
-- =============================================================================

return {
    -- Markers
    ENCOUNTER_MARKERS = ENCOUNTER_MARKERS,
    register_marker_rule = register_marker_rule,
    init_default_markers = init_default_markers,
    
    -- NPC markers
    NPC_MARKERS = NPC_MARKERS,
    set_npc_markers = set_npc_markers,
    get_npc_markers = get_npc_markers,
    add_marker = add_marker,
    
    -- Encounters
    calculate_encounter_chance = calculate_encounter_chance,
    check_encounter = check_encounter,
    
    -- Locations
    LOCATION_OCCUPATION = LOCATION_OCCUPATION,
    enter_location = enter_location,
    leave_location = leave_location,
    get_npcs_in_location = get_npcs_in_location,
    process_location_encounters = process_location_encounters,
    
    -- Missions
    MISSION_TEMPLATES = MISSION_TEMPLATES,
    register_mission_template = register_mission_template,
    init_mission_templates = init_mission_templates,
    
    ACTIVE_MISSIONS = ACTIVE_MISSIONS,
    create_mission = create_mission,
    progress_mission = progress_mission,
    complete_mission = complete_mission,
    get_npc_missions = get_npc_missions
}
