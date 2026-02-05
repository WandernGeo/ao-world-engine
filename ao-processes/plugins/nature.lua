-- ============================================================================
-- NATURE PLUGIN
-- Wildlife, pets, livestock, and ecosystem simulation
-- ============================================================================

local Nature = {}

-- Animal types from world codec
Nature.ANIMAL_TYPES = {
    domestic_pet = "WT01",
    urban_wildlife = "WT02",
    pest = "WT03",
    livestock = "WT04",
    bird = "WT05",
    aquatic = "WT06"
}

-- Animal registry (subset for simulation)
Nature.Animals = {}

-- Ecosystem state
Nature.Ecosystem = {
    pest_level = 0.2,           -- 0-1, affects disease spread
    wildlife_health = 0.8,      -- 0-1, overall ecosystem health
    livestock_count = 500,      -- Total livestock in city
    pet_population = 1200       -- Pets owned by NPCs
}

-- Initialize nature state
function Nature.init()
    -- Initialize animal populations by habitat
    Nature.Populations = {
        street = { cats = 50, dogs = 30, pigeons = 200, rats = 500 },
        park = { birds = 300, rabbits = 20, bees = 1000 },
        sewer = { rats = 2000, gators = 5, bats = 100 },
        waterfront = { fish = 500, seagulls = 100, crabs = 200 },
        farm = { chickens = 200, cows = 50, pigs = 100, sheep = 80 }
    }
end

-- Process nature tick - called from world.lua CRON
function Nature.on_tick(tick, weather, season)
    -- Update populations based on conditions
    Nature.update_populations(tick, weather, season)
    
    -- Check for pest infestations
    if tick % 24 == 0 then  -- Daily check
        Nature.check_infestations(tick)
    end
    
    -- Breeding seasons
    if tick % 240 == 0 then  -- Monthly check
        Nature.breeding_cycle(tick, season)
    end
    
    -- Livestock production
    if tick % 10 == 0 then  -- Regular production
        Nature.produce_goods(tick)
    end
    
    return Nature.Ecosystem
end

-- Update animal populations
function Nature.update_populations(tick, weather, season)
    -- Weather affects populations
    if weather == "storm" then
        -- Birds take shelter
        Nature.Populations.street.pigeons = math.max(0, Nature.Populations.street.pigeons - 20)
    elseif weather == "clear" then
        -- Populations recover
        Nature.Populations.street.pigeons = math.min(300, Nature.Populations.street.pigeons + 5)
    end
    
    -- Predator-prey dynamics
    local cats = Nature.Populations.street.cats
    local rats = Nature.Populations.sewer.rats
    
    -- Cats eat rats
    local rats_eaten = math.floor(cats * 0.5)
    Nature.Populations.sewer.rats = math.max(100, rats - rats_eaten)
    
    -- More rats means more cats can survive
    if rats > 1000 then
        Nature.Populations.street.cats = math.min(100, cats + 1)
    end
end

-- Check for pest infestations
function Nature.check_infestations(tick)
    local rats = Nature.Populations.sewer.rats
    local threshold = 1500
    
    if rats > threshold then
        -- Infestation event
        Nature.Ecosystem.pest_level = math.min(1.0, Nature.Ecosystem.pest_level + 0.1)
        
        return {
            type = "infestation",
            severity = (rats - threshold) / 1000,
            tick = tick,
            effects = {
                disease_risk = 0.2,
                food_spoilage = 0.1,
                mood_penalty = -0.05
            }
        }
    end
    
    -- Natural pest decline with good sanitation
    Nature.Ecosystem.pest_level = math.max(0.1, Nature.Ecosystem.pest_level - 0.02)
    return nil
end

-- Breeding cycles
function Nature.breeding_cycle(tick, season)
    local breeding_multiplier = 1.0
    
    if season == "spring" then
        breeding_multiplier = 1.5
    elseif season == "winter" then
        breeding_multiplier = 0.5
    end
    
    -- Increase populations
    for habitat, animals in pairs(Nature.Populations) do
        for species, count in pairs(animals) do
            local growth = math.floor(count * 0.1 * breeding_multiplier)
            local max_capacity = Nature.get_carrying_capacity(habitat, species)
            Nature.Populations[habitat][species] = math.min(max_capacity, count + growth)
        end
    end
end

-- Get carrying capacity for a species in a habitat
function Nature.get_carrying_capacity(habitat, species)
    local capacities = {
        street = { cats = 100, dogs = 50, pigeons = 500, rats = 1000 },
        park = { birds = 500, rabbits = 50, bees = 5000 },
        sewer = { rats = 5000, gators = 10, bats = 200 },
        waterfront = { fish = 1000, seagulls = 200, crabs = 500 },
        farm = { chickens = 500, cows = 100, pigs = 200, sheep = 150 }
    }
    
    return capacities[habitat] and capacities[habitat][species] or 100
end

-- Produce goods from livestock
function Nature.produce_goods(tick)
    local production = {
        eggs = Nature.Populations.farm.chickens * 0.8,      -- 80% laying rate
        milk = Nature.Populations.farm.cows * 10,           -- 10L per cow
        wool = 0,  -- Only during shearing season
        meat = 0,  -- Only during slaughter
        honey = Nature.Populations.park.bees * 0.001        -- Tiny per bee but many bees
    }
    
    -- Seasonal wool production
    if tick % (240 * 3) == 0 then  -- Every 3 months
        production.wool = Nature.Populations.farm.sheep * 5  -- 5kg per sheep
    end
    
    return production
end

-- NPC pet adoption
function Nature.adopt_pet(npc_id, pet_type)
    if pet_type == "cat" and Nature.Populations.street.cats > 10 then
        Nature.Populations.street.cats = Nature.Populations.street.cats - 1
        Nature.Ecosystem.pet_population = Nature.Ecosystem.pet_population + 1
        return { success = true, pet_id = "PET_" .. npc_id .. "_cat", type = "cat" }
    elseif pet_type == "dog" and Nature.Populations.street.dogs > 5 then
        Nature.Populations.street.dogs = Nature.Populations.street.dogs - 1
        Nature.Ecosystem.pet_population = Nature.Ecosystem.pet_population + 1
        return { success = true, pet_id = "PET_" .. npc_id .. "_dog", type = "dog" }
    end
    
    return { success = false, reason = "no_available_animals" }
end

-- Slaughter livestock for meat
function Nature.slaughter(animal_type, quantity)
    local meat_per_animal = {
        cows = 200,    -- 200kg per cow
        pigs = 80,     -- 80kg per pig
        chickens = 2,  -- 2kg per chicken
        sheep = 40     -- 40kg per sheep
    }
    
    local available = Nature.Populations.farm[animal_type] or 0
    local to_slaughter = math.min(quantity, available)
    
    Nature.Populations.farm[animal_type] = available - to_slaughter
    
    local meat_produced = to_slaughter * (meat_per_animal[animal_type] or 10)
    
    return {
        animal_type = animal_type,
        quantity = to_slaughter,
        meat_kg = meat_produced
    }
end

-- Export module
return Nature
