--[[
  AO World Engine - Occupation & Jobs Registry
  
  Pluggable system for:
  - Register any job/occupation dynamically
  - Schedules and routines
  - City services (police, security, maintenance)
  - Job-specific behaviors
]]--

local json = require("json")

-- =============================================================================
-- OCCUPATION REGISTRY (Pluggable)
-- =============================================================================

OCCUPATIONS = {}

-- Register a new occupation
function register_occupation(occupation_id, definition)
    OCCUPATIONS[occupation_id] = {
        id = occupation_id,
        name = definition.name,
        category = definition.category,  -- "service", "creative", "criminal", etc.
        
        -- Schedule template
        schedule = definition.schedule or {
            work_start = 9,
            work_end = 17,
            work_days = {1, 2, 3, 4, 5}  -- Mon-Fri
        },
        
        -- Locations
        typical_workplaces = definition.workplaces or {},
        hangout_spots = definition.hangouts or {},
        
        -- Faction affinity
        faction_affinity = definition.faction_affinity,
        
        -- Behaviors
        behaviors = definition.behaviors or {},
        
        -- Pay/economy
        base_wage = definition.wage or 100,
        wage_variance = definition.wage_variance or 0.2,
        
        -- Encounter modifiers
        encounter_modifiers = definition.encounter_modifiers or {},
        
        -- Requirements
        requires_cybernetics = definition.requires_cybernetics or false,
        requires_faction = definition.requires_faction,
        
        -- Active workers
        workers = {}
    }
    
    return OCCUPATIONS[occupation_id]
end

-- =============================================================================
-- DEFAULT CITY OCCUPATIONS
-- =============================================================================

function init_city_occupations()
    -- SERVICE SECTOR
    register_occupation("police", {
        name = "Police Officer",
        category = "service",
        schedule = { work_start = 6, work_end = 18, work_days = {1,2,3,4,5,6} },
        workplaces = {"precinct_7", "precinct_12", "police_hq"},
        hangouts = {"donut_shop", "cantina", "coffee_stand"},
        faction_affinity = "echo_corp",
        behaviors = {"patrol", "investigate", "arrest"},
        wage = 300,
        encounter_modifiers = {
            criminal = 2.0,  -- 2x chance to encounter criminals
            resistance = 1.5
        }
    })
    
    register_occupation("security", {
        name = "Security Guard",
        category = "service",
        schedule = { work_start = 20, work_end = 6, work_days = {1,2,3,4,5,6,7} },
        workplaces = {"corporate_tower", "warehouse_district", "shopping_plaza"},
        behaviors = {"guard", "patrol_building", "check_id"},
        wage = 150,
        encounter_modifiers = {
            thief = 2.5
        }
    })
    
    register_occupation("maintenance", {
        name = "Maintenance Worker",
        category = "service",
        schedule = { work_start = 7, work_end = 15, work_days = {1,2,3,4,5} },
        workplaces = {"utility_hub", "water_plant", "power_station"},
        hangouts = {"worker_bar", "diner"},
        behaviors = {"repair", "maintain", "inspect"},
        wage = 120
    })
    
    -- MEDIA & INFORMATION
    register_occupation("reporter", {
        name = "Reporter",
        category = "creative",
        schedule = { work_start = 10, work_end = 22, work_days = {1,2,3,4,5,6} },
        workplaces = {"news_station", "press_office", "field"},
        hangouts = {"press_club", "rooftop_bar"},
        behaviors = {"investigate", "interview", "publish"},
        wage = 200,
        encounter_modifiers = {
            public_figure = 1.8,
            criminal = 0.3  -- Criminals avoid reporters
        }
    })
    
    register_occupation("newscaster", {
        name = "Newscaster",
        category = "creative",
        schedule = { work_start = 5, work_end = 14, work_days = {1,2,3,4,5,6} },
        workplaces = {"news_station", "broadcast_tower"},
        behaviors = {"broadcast", "anchor"},
        wage = 400
    })
    
    -- CRIMINAL
    register_occupation("thief", {
        name = "Thief",
        category = "criminal",
        schedule = { work_start = 22, work_end = 4, work_days = {1,2,3,4,5,6,7} },
        workplaces = {"streets", "warehouse_district", "residential"},
        hangouts = {"underground_bar", "fence_shop"},
        faction_affinity = "underground",
        behaviors = {"steal", "scout", "fence"},
        wage = 0,  -- Variable income
        encounter_modifiers = {
            police = 0.3,
            security = 0.3,
            rich = 1.5
        }
    })
    
    register_occupation("smuggler", {
        name = "Smuggler",
        category = "criminal",
        schedule = { work_start = 1, work_end = 5, work_days = {2,4,6} },
        workplaces = {"port_district", "undercity", "warehouse"},
        faction_affinity = "underground",
        behaviors = {"transport", "bribe", "evade"},
        wage = 0,
        encounter_modifiers = {
            customs = 0.2,
            underground = 1.5
        }
    })
    
    -- TECH
    register_occupation("hacker", {
        name = "Hacker",
        category = "tech",
        schedule = { work_start = 22, work_end = 6, work_days = {1,2,3,4,5,6,7} },
        workplaces = {"hackerspace", "home", "cafe"},
        hangouts = {"neon_bar", "cyber_cafe"},
        faction_affinity = "cyber_collective",
        requires_cybernetics = true,
        behaviors = {"hack", "research", "code"},
        wage = 250
    })
    
    register_occupation("tech_surgeon", {
        name = "Tech Surgeon",
        category = "tech",
        schedule = { work_start = 10, work_end = 20, work_days = {1,2,3,4,5,6} },
        workplaces = {"clinic", "back_alley_clinic", "hospital"},
        faction_affinity = "cyber_collective",
        behaviors = {"surgery", "install_implant", "repair_cybernetics"},
        wage = 500
    })
    
    -- FAITH
    register_occupation("temple_priest", {
        name = "Temple Priest",
        category = "faith",
        schedule = { work_start = 6, work_end = 21, work_days = {1,2,3,4,5,6,7} },
        workplaces = {"temple_of_signal", "shrine"},
        faction_affinity = "temple_of_signal",
        behaviors = {"preach", "convert", "heal"},
        wage = 50  -- Donations
    })
    
    -- HOSPITALITY
    register_occupation("bartender", {
        name = "Bartender",
        category = "hospitality",
        schedule = { work_start = 18, work_end = 3, work_days = {1,2,3,4,5,6} },
        workplaces = {"bar", "cantina", "nightclub"},
        behaviors = {"serve", "listen", "gossip"},
        wage = 100,
        encounter_modifiers = {
            all = 1.3  -- Bartenders meet everyone
        }
    })
    
    register_occupation("cook", {
        name = "Cook",
        category = "hospitality",
        schedule = { work_start = 6, work_end = 14, work_days = {1,2,3,4,5,6} },
        workplaces = {"restaurant", "cantina", "food_stall"},
        behaviors = {"cook", "serve"},
        wage = 80
    })
    
    -- RESISTANCE
    register_occupation("resistance_operative", {
        name = "Resistance Operative",
        category = "underground",
        schedule = { work_start = 0, work_end = 24, work_days = {1,2,3,4,5,6,7} },
        workplaces = {"safehouse", "hidden_base"},
        hangouts = {"underground_meeting"},
        faction_affinity = "resistance",
        requires_faction = "resistance",
        behaviors = {"spy", "sabotage", "recruit", "protect"},
        wage = 0,
        encounter_modifiers = {
            echo_corp = 0.2,
            police = 0.2
        }
    })
    
    -- CORPORATE
    register_occupation("corporate_exec", {
        name = "Corporate Executive",
        category = "corporate",
        schedule = { work_start = 8, work_end = 20, work_days = {1,2,3,4,5} },
        workplaces = {"corporate_tower", "echo_hq"},
        hangouts = {"rooftop_bar", "golf_club"},
        faction_affinity = "echo_corp",
        behaviors = {"manage", "negotiate", "exploit"},
        wage = 2000,
        encounter_modifiers = {
            criminal = 0.2,
            resistance = 0.3
        }
    })
end

-- =============================================================================
-- WORKER MANAGEMENT
-- =============================================================================

-- Assign NPC to occupation
function assign_occupation(npc_id, occupation_id)
    local occupation = OCCUPATIONS[occupation_id]
    if not occupation then return false end
    
    -- Remove from previous occupation
    for oid, occ in pairs(OCCUPATIONS) do
        occ.workers[npc_id] = nil
    end
    
    occupation.workers[npc_id] = {
        npc_id = npc_id,
        started = os.time(),
        performance = 0.5 + math.random() * 0.5,
        wage = occupation.base_wage * (1 + (math.random() - 0.5) * occupation.wage_variance)
    }
    
    return true
end

-- Get NPC's occupation
function get_npc_occupation(npc_id)
    for occupation_id, occupation in pairs(OCCUPATIONS) do
        if occupation.workers[npc_id] then
            return occupation_id, occupation
        end
    end
    return nil, nil
end

-- Check if NPC is working right now
function is_working(npc_id, current_hour, current_day)
    current_day = current_day or 1
    
    local occupation_id, occupation = get_npc_occupation(npc_id)
    if not occupation then return false end
    
    local schedule = occupation.schedule
    
    -- Check work day
    local is_work_day = false
    for _, day in ipairs(schedule.work_days) do
        if day == current_day then
            is_work_day = true
            break
        end
    end
    if not is_work_day then return false end
    
    -- Check work hours (handle overnight shifts)
    if schedule.work_start < schedule.work_end then
        return current_hour >= schedule.work_start and current_hour < schedule.work_end
    else
        -- Overnight shift
        return current_hour >= schedule.work_start or current_hour < schedule.work_end
    end
end

-- Get NPCs currently working a specific job
function get_active_workers(occupation_id, current_hour, current_day)
    local occupation = OCCUPATIONS[occupation_id]
    if not occupation then return {} end
    
    local active = {}
    for npc_id, worker in pairs(occupation.workers) do
        if is_working(npc_id, current_hour, current_day) then
            table.insert(active, npc_id)
        end
    end
    return active
end

-- =============================================================================
-- ENCOUNTER MODIFIERS BY OCCUPATION
-- =============================================================================

-- Get encounter chance modifier between two NPCs based on jobs
function get_occupation_encounter_modifier(npc_a_id, npc_b_id)
    local occ_a_id = get_npc_occupation(npc_a_id)
    local occ_b_id, occ_b = get_npc_occupation(npc_b_id)
    
    if not occ_a_id then return 1.0 end
    
    local occ_a = OCCUPATIONS[occ_a_id]
    local modifiers = occ_a.encounter_modifiers or {}
    
    -- Check for "all" modifier
    if modifiers.all then
        return modifiers.all
    end
    
    -- Check for specific occupation modifier
    if occ_b_id and modifiers[occ_b_id] then
        return modifiers[occ_b_id]
    end
    
    return 1.0
end

-- =============================================================================
-- AO MESSAGE HANDLERS
-- =============================================================================

Handlers.add("RegisterOccupation", Handlers.utils.hasMatchingTag("Action", "RegisterOccupation"),
    function(msg)
        local data = json.decode(msg.Data or "{}")
        local occupation = register_occupation(data.id, data)
        
        ao.send({
            Target = msg.From,
            Data = json.encode(occupation)
        })
    end
)

Handlers.add("AssignOccupation", Handlers.utils.hasMatchingTag("Action", "AssignOccupation"),
    function(msg)
        local npc_id = msg.Tags["NpcId"]
        local occupation_id = msg.Tags["OccupationId"]
        
        local success = assign_occupation(npc_id, occupation_id)
        
        ao.send({
            Target = msg.From,
            Data = json.encode({success = success})
        })
    end
)

Handlers.add("GetOccupation", Handlers.utils.hasMatchingTag("Action", "GetOccupation"),
    function(msg)
        local npc_id = msg.Tags["NpcId"]
        local occupation_id, occupation = get_npc_occupation(npc_id)
        
        ao.send({
            Target = msg.From,
            Data = json.encode({
                occupation_id = occupation_id,
                occupation = occupation
            })
        })
    end
)

Handlers.add("GetAllOccupations", Handlers.utils.hasMatchingTag("Action", "GetAllOccupations"),
    function(msg)
        ao.send({
            Target = msg.From,
            Data = json.encode(OCCUPATIONS)
        })
    end
)

-- =============================================================================
-- EXPORT
-- =============================================================================

return {
    -- Registry
    OCCUPATIONS = OCCUPATIONS,
    register_occupation = register_occupation,
    init_city_occupations = init_city_occupations,
    
    -- Workers
    assign_occupation = assign_occupation,
    get_npc_occupation = get_npc_occupation,
    is_working = is_working,
    get_active_workers = get_active_workers,
    
    -- Encounters
    get_occupation_encounter_modifier = get_occupation_encounter_modifier
}
