--[[
  AO World Engine - Initialization Bootstrap
  
  This script bootstraps the entire simulation on AO.
  Run this after spawning the world process to initialize
  all subsystems with default configuration.
  
  Usage:
    .load ao-processes/init_bootstrap.lua
    
  Then call:
    Initialize({ population = 10000, districts = 5 })
]]--

local json = require("json")

-- =============================================================================
-- DEFAULT CONFIGURATION
-- =============================================================================

local DEFAULT_CONFIG = {
    -- World settings
    world = {
        initial_budget = 1000000,  -- Starting city treasury (GEP)
        tax_rate = 0.10,           -- 10% income tax
        population = 10000         -- Starting population
    },
    
    -- District configuration
    districts = {
        {
            id = "neon_district",
            name = "Neon District",
            population = 2500,
            danger_level = 3,
            archetypes = {"shopkeeper", "bartender", "civilian", "street_vendor"}
        },
        {
            id = "temple_quarter",
            name = "Temple Quarter",
            population = 2000,
            danger_level = 4,
            archetypes = {"guard", "priest", "civilian"}
        },
        {
            id = "industrial_ring",
            name = "Industrial Ring",
            population = 3000,
            danger_level = 4,
            archetypes = {"laborer", "technician", "civilian"}
        },
        {
            id = "residential_core",
            name = "Residential Core",
            population = 2000,
            danger_level = 3,
            archetypes = {"civilian", "shopkeeper", "medic"}
        },
        {
            id = "undercity",
            name = "Undercity",
            population = 500,
            danger_level = 6,
            archetypes = {"smuggler", "civilian", "street_vendor"}
        }
    },
    
    -- Economy settings
    economy = {
        income_variance = 0.3,
        service_levels = {
            police = 1.0,
            sanitation = 1.0,
            infrastructure = 1.0,
            healthcare = 1.0,
            emergency = 1.0
        }
    },
    
    -- Social settings
    social = {
        trust_base = 0.1,
        trust_decay_days = 7,
        gossip_decay_ticks = 720
    }
}

-- =============================================================================
-- ARCHETYPE TEMPLATES
-- =============================================================================

local ARCHETYPE_TEMPLATES = {
    shopkeeper = {
        code = "ARCH001",
        income = 120,
        schedule = "shopkeeper_day",
        behaviors = {"BHV001", "BHV002", "BHV005"},
        personality = {
            friendliness = 0.7,
            suspicion = 0.3,
            greed = 0.5
        }
    },
    bartender = {
        code = "ARCH002",
        income = 80,
        schedule = "bartender_day",
        behaviors = {"BHV001", "BHV003", "BHV006"},
        personality = {
            friendliness = 0.6,
            discretion = 0.8,
            empathy = 0.6
        }
    },
    guard = {
        code = "ARCH003",
        income = 100,
        schedule = "temple_patrol",
        behaviors = {"BHV004", "BHV007", "BHV008"},
        personality = {
            aggression = 0.6,
            obedience = 0.7,
            suspicion = 0.7
        }
    },
    street_vendor = {
        code = "ARCH004",
        income = 50,
        schedule = "street_vendor",
        behaviors = {"BHV001", "BHV009"},
        personality = {
            friendliness = 0.5,
            desperation = 0.6,
            cunning = 0.5
        }
    },
    medic = {
        code = "ARCH005",
        income = 150,
        schedule = "worker_day",
        behaviors = {"BHV010", "BHV011"},
        personality = {
            empathy = 0.8,
            professionalism = 0.7,
            hope = 0.4
        }
    },
    civilian = {
        code = "ARCH006",
        income = 75,
        schedule = "worker_day",
        behaviors = {"BHV005", "BHV012"},
        personality = {
            fear = 0.5,
            curiosity = 0.4,
            friendliness = 0.5
        }
    },
    technician = {
        code = "ARCH007",
        income = 130,
        schedule = "worker_day",
        behaviors = {"BHV001", "BHV013"},
        personality = {
            focus = 0.7,
            curiosity = 0.6,
            caution = 0.5
        }
    },
    laborer = {
        code = "ARCH008",
        income = 60,
        schedule = "worker_day",
        behaviors = {"BHV001", "BHV014"},
        personality = {
            endurance = 0.7,
            resignation = 0.5,
            solidarity = 0.6
        }
    },
    smuggler = {
        code = "ARCH009",
        income = 200,
        schedule = "criminal",
        behaviors = {"BHV015", "BHV016"},
        personality = {
            cunning = 0.8,
            paranoia = 0.7,
            greed = 0.6
        }
    },
    priest = {
        code = "ARCH010",
        income = 90,
        schedule = "temple_patrol",
        behaviors = {"BHV017", "BHV018"},
        personality = {
            faith = 0.9,
            authority = 0.6,
            compassion = 0.5
        }
    }
}

-- =============================================================================
-- NPC GENERATION
-- =============================================================================

function generate_npc_id(district_id, index)
    return "NPC_" .. district_id:sub(1, 3):upper() .. "_" .. string.format("%05d", index)
end

function generate_npc(npc_id, archetype, district_id, home_location)
    local template = ARCHETYPE_TEMPLATES[archetype] or ARCHETYPE_TEMPLATES.civilian
    
    return {
        id = npc_id,
        archetype = archetype,
        archetype_code = template.code,
        district = district_id,
        home_location = home_location,
        schedule = template.schedule,
        income = template.income,
        behaviors = template.behaviors,
        personality = template.personality,
        needs = {
            hunger = 0.8,
            sleep = 0.9,
            safety = 1.0,
            social = 0.7,
            hygiene = 0.8,
            comfort = 0.6,
            income = 0.5,
            purpose = 0.5
        },
        wealth = math.random(100, 2000),  -- Initial GEP
        relationships = {},
        created_tick = 0
    }
end

function generate_district_npcs(district_config)
    local npcs = {}
    local archetype_count = #district_config.archetypes
    
    for i = 1, district_config.population do
        local npc_id = generate_npc_id(district_config.id, i)
        local archetype_idx = ((i - 1) % archetype_count) + 1
        local archetype = district_config.archetypes[archetype_idx]
        local home = "home_" .. npc_id
        
        npcs[npc_id] = generate_npc(npc_id, archetype, district_config.id, home)
    end
    
    return npcs
end

-- =============================================================================
-- INITIALIZATION FUNCTIONS
-- =============================================================================

function Initialize(custom_config)
    local config = custom_config or DEFAULT_CONFIG
    
    -- Merge with defaults
    config.world = config.world or DEFAULT_CONFIG.world
    config.districts = config.districts or DEFAULT_CONFIG.districts
    config.economy = config.economy or DEFAULT_CONFIG.economy
    config.social = config.social or DEFAULT_CONFIG.social
    
    print("==============================================")
    print("  AO World Engine - Initialization")
    print("==============================================")
    print("")
    
    -- Initialize world state
    print("1. Initializing World State...")
    WorldTick = 0
    WorldDay = 0
    WorldYear = 0
    CityBudget = config.world.initial_budget
    TaxRate = config.world.tax_rate
    PopulationCount = config.world.population
    
    print("   - Budget: " .. CityBudget .. " GEP")
    print("   - Tax Rate: " .. (TaxRate * 100) .. "%")
    print("   - Population: " .. PopulationCount)
    print("")
    
    -- Initialize districts
    print("2. Initializing Districts...")
    Districts = {}
    local total_npcs = 0
    
    for _, district in ipairs(config.districts) do
        print("   - " .. district.name .. " (" .. district.population .. " NPCs)")
        Districts[district.id] = {
            name = district.name,
            population = district.population,
            danger_level = district.danger_level,
            archetypes = district.archetypes,
            process_id = nil  -- Set when district process is spawned
        }
        total_npcs = total_npcs + district.population
    end
    print("   Total NPCs: " .. total_npcs)
    print("")
    
    -- Initialize economy
    print("3. Initializing Economy...")
    TaxRates = {
        income = TaxRate,
        sales = 0.05,
        temple_tithe = 0.05
    }
    ServiceLevels = config.economy.service_levels
    print("   - Service Levels: All at 100%")
    print("")
    
    -- Initialize social
    print("4. Initializing Social Systems...")
    Relationships = {}
    Reputation = {}
    Groups = {}
    ActiveGossip = {}
    print("   - Ready for relationship tracking")
    print("")
    
    print("==============================================")
    print("  Initialization Complete!")
    print("  ")
    print("  Next steps:")
    print("  1. Spawn district processes")
    print("  2. Register districts with world")
    print("  3. Start CRON for tick advancement")
    print("==============================================")
    
    return {
        world_tick = WorldTick,
        budget = CityBudget,
        districts = #config.districts,
        population = total_npcs
    }
end

-- =============================================================================
-- SPAWN HELPERS
-- =============================================================================

function SpawnDistrict(district_id, module_id)
    local district = Districts[district_id]
    if not district then
        print("Error: District " .. district_id .. " not found")
        return nil
    end
    
    -- Generate NPCs for this district
    local npcs = generate_district_npcs({
        id = district_id,
        population = district.population,
        archetypes = district.archetypes
    })
    
    print("Spawning district: " .. district.name)
    print("  - NPCs generated: " .. district.population)
    
    -- In actual AO, this would spawn a new process
    -- For now, just return the config
    return {
        district_id = district_id,
        npc_count = district.population,
        init_data = json.encode({
            district_id = district_id,
            npcs = npcs,
            archetypes = district.archetypes
        })
    }
end

function RegisterAllDistricts(world_process_id)
    print("Registering all districts with world process...")
    
    for district_id, district in pairs(Districts) do
        print("  - Registering: " .. district_id)
        
        -- In actual AO:
        -- ao.send({
        --     Target = world_process_id,
        --     Action = "register-district",
        --     Data = json.encode({ district_id = district_id })
        -- })
    end
    
    print("Done!")
end

-- =============================================================================
-- EXPORTS
-- =============================================================================

return {
    Initialize = Initialize,
    SpawnDistrict = SpawnDistrict,
    RegisterAllDistricts = RegisterAllDistricts,
    DEFAULT_CONFIG = DEFAULT_CONFIG,
    ARCHETYPE_TEMPLATES = ARCHETYPE_TEMPLATES,
    generate_npc = generate_npc
}
