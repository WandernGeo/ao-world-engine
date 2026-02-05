--[[
  AO World Engine - Vehicle & Transportation System
  
  Pluggable vehicle registry:
  - Add car JSON → cars start appearing
  - Bus routes and schedules
  - Vehicle specifications
  - NPC transportation between locations
]]--

local json = require("json")

-- =============================================================================
-- VEHICLE TYPE REGISTRY (Pluggable)
-- =============================================================================

VEHICLE_TYPES = {}

-- Register a vehicle type (add JSON → appears in world)
function register_vehicle_type(type_id, spec)
    VEHICLE_TYPES[type_id] = {
        id = type_id,
        name = spec.name,
        category = spec.category,  -- "car", "bus", "bike", "hover", "truck"
        
        -- Appearance
        make = spec.make,
        model = spec.model,
        year = spec.year,
        color_options = spec.colors or {"black", "white", "gray"},
        
        -- Visual description
        visual = spec.visual,
        
        -- Specifications
        capacity = spec.capacity or 4,
        speed = spec.speed or 60,  -- km/h
        range = spec.range or 500,  -- km
        
        -- Technology
        fuel_type = spec.fuel_type or "electric",  -- "electric", "hydrogen", "hybrid", "gas"
        autonomous = spec.autonomous or false,
        cybernetic_interface = spec.cybernetic_interface or false,
        
        -- Rarity (affects spawn rate)
        rarity = spec.rarity or 0.5,  -- 0 = never, 1 = common
        
        -- Faction/District preferences
        faction_preference = spec.faction_preference,
        district_preference = spec.district_preference,
        
        -- Markers (for NPC interaction)
        markers = spec.markers or {},
        
        -- Cost
        purchase_price = spec.price or 10000,
        rental_cost = spec.rental or 50,
        
        -- State
        active = true,
        registered_at = os.time()
    }
    
    return VEHICLE_TYPES[type_id]
end

-- =============================================================================
-- DEFAULT VEHICLES
-- =============================================================================

function init_default_vehicles()
    -- Standard cars
    register_vehicle_type("sedan_standard", {
        name = "City Sedan",
        category = "car",
        make = "Kuro Motors",
        model = "Commuter",
        colors = {"black", "white", "silver", "blue"},
        capacity = 4,
        speed = 80,
        rarity = 0.8,
        price = 15000
    })
    
    register_vehicle_type("sports_coupe", {
        name = "Sports Coupe",
        category = "car",
        make = "Velocity",
        model = "Phantom",
        colors = {"red", "black", "midnight_blue"},
        capacity = 2,
        speed = 180,
        rarity = 0.2,
        faction_preference = "echo_corp",
        price = 80000
    })
    
    register_vehicle_type("cyber_racer", {
        name = "Cyber Racer",
        category = "car",
        make = "Neon Drift",
        model = "X-9",
        visual = "Sleek black chassis with neon trim, holographic displays",
        colors = {"chrome", "neon_pink", "electric_blue"},
        capacity = 2,
        speed = 220,
        autonomous = true,
        cybernetic_interface = true,
        rarity = 0.05,
        faction_preference = "cyber_collective",
        markers = {"high_tech", "cybernetic_compatible"},
        price = 200000
    })
    
    register_vehicle_type("hover_taxi", {
        name = "Hover Taxi",
        category = "hover",
        make = "SkyLift",
        model = "Urban",
        colors = {"yellow", "yellow_black"},
        capacity = 4,
        speed = 150,
        autonomous = true,
        rarity = 0.4,
        rental = 20
    })
    
    -- Buses
    register_vehicle_type("city_bus", {
        name = "City Bus",
        category = "bus",
        make = "Transit Corp",
        model = "Metro 2050",
        colors = {"transit_blue", "transit_white"},
        capacity = 50,
        speed = 50,
        rarity = 0.9,  -- Very common
        price = 500000
    })
    
    register_vehicle_type("express_bus", {
        name = "Express Bus",
        category = "bus",
        make = "Transit Corp",
        model = "Express X",
        capacity = 30,
        speed = 80,
        autonomous = true,
        rarity = 0.6
    })
    
    -- Underground vehicles
    register_vehicle_type("smuggler_van", {
        name = "Smuggler's Van",
        category = "truck",
        make = "Unknown",
        model = "Modified",
        colors = {"matte_black", "rust"},
        capacity = 8,
        speed = 100,
        rarity = 0.1,
        faction_preference = "underground",
        markers = {"underground_connected", "smuggling_capable"},
        price = 25000
    })
    
    -- Mutant district
    register_vehicle_type("bio_crawler", {
        name = "Bio-Crawler",
        category = "bio",
        make = "Vivid Labs",
        model = "Organic Transport",
        visual = "Living vehicle with bioluminescent skin, organic wheels",
        colors = {"flesh", "bio_green", "mutant_purple"},
        capacity = 6,
        speed = 40,
        fuel_type = "organic",
        rarity = 0.1,
        faction_preference = "vivid_mutants",
        district_preference = "mutant_quarter",
        markers = {"mutation_friendly", "organic"},
        price = 35000
    })
end

-- =============================================================================
-- VEHICLE INSTANCES (Active vehicles in world)
-- =============================================================================

VEHICLES = {}
VEHICLE_COUNTER = 0

-- Spawn a vehicle instance
function spawn_vehicle(type_id, config)
    local vtype = VEHICLE_TYPES[type_id]
    if not vtype then return nil end
    
    config = config or {}
    VEHICLE_COUNTER = VEHICLE_COUNTER + 1
    
    local vehicle = {
        id = "VEH_" .. VEHICLE_COUNTER,
        type_id = type_id,
        type = vtype,
        
        -- Instance details
        color = config.color or vtype.color_options[math.random(#vtype.color_options)],
        plate = config.plate or generate_plate(),
        
        -- Owner
        owner_npc = config.owner,
        owner_faction = config.faction,
        
        -- Location
        current_location = config.location,
        current_district = config.district,
        
        -- Status
        status = "parked",  -- "parked", "moving", "in_use"
        passengers = {},
        
        -- For buses: route info
        route_id = config.route_id,
        
        -- Spawned at
        spawned_at = os.time(),
        spawned_tick = WorldTick or 0
    }
    
    VEHICLES[vehicle.id] = vehicle
    return vehicle
end

-- Generate random license plate
function generate_plate()
    local chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    local nums = "0123456789"
    
    local plate = ""
    for i = 1, 3 do
        local idx = math.random(#chars)
        plate = plate .. chars:sub(idx, idx)
    end
    plate = plate .. "-"
    for i = 1, 3 do
        local idx = math.random(#nums)
        plate = plate .. nums:sub(idx, idx)
    end
    
    return plate
end

-- =============================================================================
-- ROUTES (Bus/Transit lines)
-- =============================================================================

ROUTES = {}

function register_route(route_id, config)
    ROUTES[route_id] = {
        id = route_id,
        name = config.name,
        type = config.type or "bus",  -- "bus", "train", "ferry"
        
        -- Stops (ordered list of location IDs)
        stops = config.stops or {},
        
        -- Schedule
        frequency_minutes = config.frequency or 15,
        operating_hours = config.hours or {6, 22},  -- 6 AM to 10 PM
        
        -- Assigned vehicles
        assigned_vehicles = {},
        
        -- District coverage
        districts = config.districts or {},
        
        -- Cost per ride
        fare = config.fare or 5
    }
    
    return ROUTES[route_id]
end

-- Default routes
function init_default_routes()
    register_route("line_1", {
        name = "Downtown Express",
        stops = {"central_station", "corporate_plaza", "tech_district", "neon_alley"},
        frequency = 10,
        fare = 10
    })
    
    register_route("line_2", {
        name = "Outer Ring",
        stops = {"port_district", "mutant_quarter", "old_chinatown", "industrial_zone"},
        frequency = 20,
        fare = 5
    })
    
    register_route("line_3", {
        name = "Temple Loop",
        stops = {"temple_district", "pilgrim_plaza", "meditation_gardens", "central_station"},
        frequency = 30,
        fare = 3
    })
    
    register_route("underground_shuttle", {
        name = "Underground Shuttle",
        type = "shuttle",
        stops = {"undercity_hub", "smuggler_dock", "black_market"},
        frequency = 60,
        hours = {22, 4},  -- Night only
        fare = 0  -- Free for underground members
    })
end

-- =============================================================================
-- GRADUAL SPAWNING SYSTEM
-- =============================================================================

SPAWN_QUEUE = {}

-- Add vehicle type to spawn queue (gradual appearance)
function queue_vehicle_spawns(type_id, count, over_ticks)
    local per_tick = count / over_ticks
    
    table.insert(SPAWN_QUEUE, {
        type_id = type_id,
        remaining = count,
        per_tick = per_tick,
        accumulator = 0
    })
end

-- Process spawn queue (call on tick)
function process_spawn_queue()
    local spawned = {}
    
    for i, entry in ipairs(SPAWN_QUEUE) do
        if entry.remaining > 0 then
            entry.accumulator = entry.accumulator + entry.per_tick
            
            while entry.accumulator >= 1 and entry.remaining > 0 do
                local vehicle = spawn_vehicle(entry.type_id, {
                    district = get_preferred_district(entry.type_id)
                })
                if vehicle then
                    table.insert(spawned, vehicle)
                end
                entry.accumulator = entry.accumulator - 1
                entry.remaining = entry.remaining - 1
            end
        end
    end
    
    -- Clean up completed entries
    local i = 1
    while i <= #SPAWN_QUEUE do
        if SPAWN_QUEUE[i].remaining <= 0 then
            table.remove(SPAWN_QUEUE, i)
        else
            i = i + 1
        end
    end
    
    return spawned
end

-- Get preferred district for vehicle type
function get_preferred_district(type_id)
    local vtype = VEHICLE_TYPES[type_id]
    if vtype and vtype.district_preference then
        return vtype.district_preference
    end
    -- Random district
    return nil
end

-- =============================================================================
-- NPC TRANSPORTATION
-- =============================================================================

-- Check if NPC can use vehicle (marker compatibility)
function can_use_vehicle(npc_id, vehicle_id)
    local vehicle = VEHICLES[vehicle_id]
    if not vehicle then return false end
    
    local vtype = vehicle.type
    if not vtype.markers or #vtype.markers == 0 then
        return true  -- No restrictions
    end
    
    -- Check NPC markers
    local npc_markers = get_npc_markers and get_npc_markers(npc_id) or {}
    
    for _, required_marker in ipairs(vtype.markers) do
        local has_marker = false
        for _, npc_marker in ipairs(npc_markers) do
            if npc_marker == required_marker then
                has_marker = true
                break
            end
        end
        if not has_marker then
            return false
        end
    end
    
    return true
end

-- Board NPC onto vehicle
function board_vehicle(npc_id, vehicle_id)
    local vehicle = VEHICLES[vehicle_id]
    if not vehicle then return false end
    
    if not can_use_vehicle(npc_id, vehicle_id) then
        return false
    end
    
    if #vehicle.passengers >= vehicle.type.capacity then
        return false
    end
    
    table.insert(vehicle.passengers, npc_id)
    vehicle.status = "in_use"
    
    return true
end

-- Exit NPC from vehicle
function exit_vehicle(npc_id, vehicle_id)
    local vehicle = VEHICLES[vehicle_id]
    if not vehicle then return false end
    
    for i, id in ipairs(vehicle.passengers) do
        if id == npc_id then
            table.remove(vehicle.passengers, i)
            break
        end
    end
    
    if #vehicle.passengers == 0 then
        vehicle.status = "parked"
    end
    
    return true
end

-- =============================================================================
-- IMPORT FROM JSON
-- =============================================================================

-- Import vehicles from JSON (add JSON → appear in world)
function import_vehicles_json(json_string)
    local data = json.decode(json_string)
    local imported = {types = 0, instances = 0}
    
    -- Import types
    if data.vehicle_types then
        for type_id, spec in pairs(data.vehicle_types) do
            register_vehicle_type(type_id, spec)
            imported.types = imported.types + 1
            
            -- Gradual spawn if count specified
            if spec.spawn_count and spec.spawn_over_ticks then
                queue_vehicle_spawns(type_id, spec.spawn_count, spec.spawn_over_ticks)
            end
        end
    end
    
    -- Import instances
    if data.vehicles then
        for _, v in ipairs(data.vehicles) do
            spawn_vehicle(v.type_id, v)
            imported.instances = imported.instances + 1
        end
    end
    
    -- Import routes
    if data.routes then
        for route_id, config in pairs(data.routes) do
            register_route(route_id, config)
        end
    end
    
    return imported
end

-- =============================================================================
-- AO MESSAGE HANDLERS
-- =============================================================================

Handlers.add("RegisterVehicleType", Handlers.utils.hasMatchingTag("Action", "RegisterVehicleType"),
    function(msg)
        local type_id = msg.Tags["TypeId"]
        local spec = json.decode(msg.Data or "{}")
        
        local vtype = register_vehicle_type(type_id, spec)
        
        ao.send({
            Target = msg.From,
            Data = json.encode(vtype)
        })
    end
)

Handlers.add("SpawnVehicle", Handlers.utils.hasMatchingTag("Action", "SpawnVehicle"),
    function(msg)
        local type_id = msg.Tags["TypeId"]
        local config = json.decode(msg.Data or "{}")
        
        local vehicle = spawn_vehicle(type_id, config)
        
        ao.send({
            Target = msg.From,
            Data = json.encode(vehicle or {error = "spawn_failed"})
        })
    end
)

Handlers.add("ImportVehicles", Handlers.utils.hasMatchingTag("Action", "ImportVehicles"),
    function(msg)
        local imported = import_vehicles_json(msg.Data or "{}")
        
        ao.send({
            Target = msg.From,
            Data = json.encode(imported)
        })
    end
)

Handlers.add("GetVehicleTypes", Handlers.utils.hasMatchingTag("Action", "GetVehicleTypes"),
    function(msg)
        ao.send({
            Target = msg.From,
            Data = json.encode(VEHICLE_TYPES)
        })
    end
)

Handlers.add("ProcessSpawnQueue", Handlers.utils.hasMatchingTag("Action", "ProcessSpawnQueue"),
    function(msg)
        local spawned = process_spawn_queue()
        
        ao.send({
            Target = msg.From,
            Data = json.encode({spawned_count = #spawned})
        })
    end
)

-- =============================================================================
-- EXPORT
-- =============================================================================

return {
    -- Types
    VEHICLE_TYPES = VEHICLE_TYPES,
    register_vehicle_type = register_vehicle_type,
    init_default_vehicles = init_default_vehicles,
    
    -- Instances
    VEHICLES = VEHICLES,
    spawn_vehicle = spawn_vehicle,
    
    -- Routes
    ROUTES = ROUTES,
    register_route = register_route,
    init_default_routes = init_default_routes,
    
    -- Gradual spawning
    SPAWN_QUEUE = SPAWN_QUEUE,
    queue_vehicle_spawns = queue_vehicle_spawns,
    process_spawn_queue = process_spawn_queue,
    
    -- NPC interaction
    can_use_vehicle = can_use_vehicle,
    board_vehicle = board_vehicle,
    exit_vehicle = exit_vehicle,
    
    -- Import
    import_vehicles_json = import_vehicles_json
}
