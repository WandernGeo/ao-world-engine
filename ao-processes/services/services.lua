-- ============================================================================
-- MAIL AND DELIVERY SERVICES
-- Postal, courier, and drone delivery systems
-- ============================================================================

local Services = {}

-- ============================================================================
-- MAIL SYSTEM
-- ============================================================================

Services.Mail = {
    queue = {},          -- Pending mail items
    delivered = {},      -- Delivered mail history (last 100)
    carriers = {},       -- Active mail carriers
    post_offices = {}    -- Post office states
}

-- Mail types from codec
Services.MAIL_TYPES = {
    letter = "ML01",
    package = "ML02",
    bill = "ML03",
    summons = "ML04",
    propaganda = "ML05",
    contraband = "ML06"
}

-- Initialize mail system
function Services.Mail.init()
    Services.Mail.post_offices = {
        PO01 = { district = "central_spire", capacity = 1000, queue_size = 0, workers = 20 },
        PO02 = { district = "market", capacity = 500, queue_size = 0, workers = 10 },
        PO03 = { district = "neon_district", capacity = 400, queue_size = 0, workers = 8 },
        PO04 = { district = "temple_quarter", capacity = 300, queue_size = 0, workers = 6 },
        PO05 = { district = "undercity", capacity = 100, queue_size = 0, workers = 3, contraband = true }
    }
end

-- Queue new mail
function Services.Mail.send(from_npc, to_npc, mail_type, contents, tick)
    local mail = {
        id = "MAIL_" .. tick .. "_" .. #Services.Mail.queue,
        from = from_npc,
        to = to_npc,
        type = mail_type,
        contents = contents,
        queued_tick = tick,
        status = "pending",
        delivery_method = Services.Mail.assign_delivery_method(to_npc)
    }
    
    table.insert(Services.Mail.queue, mail)
    
    -- Assign to post office
    local from_district = Services.get_npc_district(from_npc)
    local po = Services.Mail.find_nearest_post_office(from_district)
    if po then
        Services.Mail.post_offices[po].queue_size = 
            Services.Mail.post_offices[po].queue_size + 1
    end
    
    return mail.id
end

-- Assign delivery method based on destination
function Services.Mail.assign_delivery_method(to_npc)
    local district = Services.get_npc_district(to_npc)
    
    local premium = { central_spire = true, temple_quarter = true }
    local restricted = { undercity = true, the_ruins = true }
    
    if premium[district] then
        return "D02"  -- drone_express
    elseif restricted[district] then
        return "D03"  -- courier_foot
    else
        return "D05"  -- mail_postal
    end
end

-- Process mail deliveries each tick
function Services.Mail.process(tick)
    local deliveries = {}
    local i = 1
    
    while i <= #Services.Mail.queue do
        local mail = Services.Mail.queue[i]
        local delivery_time = Services.Mail.get_delivery_time(mail.delivery_method)
        
        if tick >= mail.queued_tick + delivery_time then
            -- Deliver mail
            mail.status = "delivered"
            mail.delivered_tick = tick
            
            table.insert(deliveries, {
                type = "mail_delivered",
                mail_id = mail.id,
                to = mail.to,
                mail_type = mail.type,
                tick = tick
            })
            
            -- Add to delivered history
            table.insert(Services.Mail.delivered, mail)
            if #Services.Mail.delivered > 100 then
                table.remove(Services.Mail.delivered, 1)
            end
            
            -- Remove from queue
            table.remove(Services.Mail.queue, i)
        else
            i = i + 1
        end
    end
    
    return deliveries
end

function Services.Mail.get_delivery_time(method)
    local times = {
        D01 = 5,   -- drone_standard: 5 ticks (~30 min)
        D02 = 2,   -- drone_express: 2 ticks (~12 min)  
        D03 = 10,  -- courier_foot: 10 ticks (~1 hour)
        D04 = 6,   -- courier_vehicle: 6 ticks (~36 min)
        D05 = 24   -- mail_postal: 24 ticks (~1 day)
    }
    return times[method] or 24
end

function Services.Mail.find_nearest_post_office(district)
    local district_to_po = {
        central_spire = "PO01",
        temple_quarter = "PO04",
        neon_district = "PO03",
        chrome_district = "PO02",
        market = "PO02",
        green_zone = "PO02",
        industrial_ring = "PO02",
        undercity = "PO05",
        waterfront = "PO02",
        the_ruins = "PO05"
    }
    return district_to_po[district] or "PO02"
end

-- ============================================================================
-- DELIVERY SYSTEM (DRONES AND COURIERS)
-- ============================================================================

Services.Delivery = {
    active_deliveries = {},
    drones = {},
    couriers = {}
}

-- Initialize delivery system
function Services.Delivery.init()
    Services.Delivery.drones = {
        DD01 = { depot = "central_spire", available = 50, in_use = 0, range = 5 },
        DD02 = { depot = "market", available = 30, in_use = 0, range = 3 },
        DD03 = { depot = "industrial_ring", available = 20, in_use = 0, range = 4 }
    }
    
    Services.Delivery.couriers = {
        swift_feet = { type = "foot", available = 100, in_use = 0 },
        wheel_rush = { type = "vehicle", available = 50, in_use = 0 },
        shadow_runners = { type = "foot", available = 30, in_use = 0, illegal_ok = true }
    }
end

-- Request delivery
function Services.Delivery.request(from_npc, to_npc, item, method, tick)
    local delivery = {
        id = "DEL_" .. tick .. "_" .. #Services.Delivery.active_deliveries,
        from = from_npc,
        to = to_npc,
        item = item,
        method = method,
        start_tick = tick,
        eta_tick = tick + Services.Delivery.get_eta(method),
        status = "in_transit"
    }
    
    -- Allocate resource
    if method == "D01" or method == "D02" then
        -- Drone
        local depot = Services.Delivery.find_available_drone(from_npc)
        if depot then
            Services.Delivery.drones[depot].available = 
                Services.Delivery.drones[depot].available - 1
            Services.Delivery.drones[depot].in_use = 
                Services.Delivery.drones[depot].in_use + 1
            delivery.drone_depot = depot
        else
            return nil, "no_drones_available"
        end
    else
        -- Courier
        local company = Services.Delivery.find_available_courier(method)
        if company then
            Services.Delivery.couriers[company].available = 
                Services.Delivery.couriers[company].available - 1
            Services.Delivery.couriers[company].in_use = 
                Services.Delivery.couriers[company].in_use + 1
            delivery.courier_company = company
        else
            return nil, "no_couriers_available"
        end
    end
    
    table.insert(Services.Delivery.active_deliveries, delivery)
    return delivery.id
end

function Services.Delivery.get_eta(method)
    local etas = {
        D01 = 5,   -- drone_standard
        D02 = 2,   -- drone_express
        D03 = 15,  -- courier_foot
        D04 = 8,   -- courier_vehicle
        D05 = 30   -- mail_postal
    }
    return etas[method] or 15
end

function Services.Delivery.find_available_drone(from_npc)
    local district = Services.get_npc_district(from_npc)
    
    -- Find depot with available drones
    for depot_id, depot in pairs(Services.Delivery.drones) do
        if depot.available > 0 then
            return depot_id
        end
    end
    return nil
end

function Services.Delivery.find_available_courier(method)
    for company_id, company in pairs(Services.Delivery.couriers) do
        if company.available > 0 then
            return company_id
        end
    end
    return nil
end

-- Process deliveries each tick
function Services.Delivery.process(tick)
    local completed = {}
    local i = 1
    
    while i <= #Services.Delivery.active_deliveries do
        local delivery = Services.Delivery.active_deliveries[i]
        
        if tick >= delivery.eta_tick then
            delivery.status = "delivered"
            
            -- Return resource
            if delivery.drone_depot then
                Services.Delivery.drones[delivery.drone_depot].available = 
                    Services.Delivery.drones[delivery.drone_depot].available + 1
                Services.Delivery.drones[delivery.drone_depot].in_use = 
                    Services.Delivery.drones[delivery.drone_depot].in_use - 1
            end
            if delivery.courier_company then
                Services.Delivery.couriers[delivery.courier_company].available = 
                    Services.Delivery.couriers[delivery.courier_company].available + 1
                Services.Delivery.couriers[delivery.courier_company].in_use = 
                    Services.Delivery.couriers[delivery.courier_company].in_use - 1
            end
            
            table.insert(completed, {
                type = "delivery_complete",
                delivery_id = delivery.id,
                to = delivery.to,
                item = delivery.item,
                tick = tick
            })
            
            table.remove(Services.Delivery.active_deliveries, i)
        else
            i = i + 1
        end
    end
    
    return completed
end

-- ============================================================================
-- FOOD DELIVERY
-- ============================================================================

Services.Food = {
    active_orders = {},
    restaurants = {}
}

-- Initialize restaurants
function Services.Food.init()
    Services.Food.restaurants = {
        R01 = { name = "Neon Noodles", district = "neon_district", prep_time = 10, delivery = true },
        R02 = { name = "Temple Garden", district = "temple_quarter", prep_time = 20, delivery = true },
        R03 = { name = "Street Bites", district = "market", prep_time = 5, delivery = true },
        R04 = { name = "Mama's Kitchen", district = "green_zone", prep_time = 15, delivery = true },
        R05 = { name = "Spire Dining", district = "central_spire", prep_time = 30, delivery = true }
    }
end

-- Order food
function Services.Food.order(npc_id, restaurant_id, items, tick)
    local restaurant = Services.Food.restaurants[restaurant_id]
    if not restaurant or not restaurant.delivery then
        return nil, "restaurant_unavailable"
    end
    
    local order = {
        id = "FOOD_" .. tick .. "_" .. #Services.Food.active_orders,
        npc = npc_id,
        restaurant = restaurant_id,
        items = items,
        ordered_tick = tick,
        ready_tick = tick + restaurant.prep_time,
        eta_tick = tick + restaurant.prep_time + 10,  -- +10 for delivery
        status = "preparing"
    }
    
    table.insert(Services.Food.active_orders, order)
    return order.id
end

-- Process food orders
function Services.Food.process(tick)
    local events = {}
    local i = 1
    
    while i <= #Services.Food.active_orders do
        local order = Services.Food.active_orders[i]
        
        if order.status == "preparing" and tick >= order.ready_tick then
            order.status = "delivering"
        end
        
        if tick >= order.eta_tick then
            order.status = "delivered"
            
            table.insert(events, {
                type = "food_delivered",
                order_id = order.id,
                npc = order.npc,
                restaurant = order.restaurant,
                tick = tick
            })
            
            table.remove(Services.Food.active_orders, i)
        else
            i = i + 1
        end
    end
    
    return events
end

-- ============================================================================
-- HELPER FUNCTIONS
-- ============================================================================

function Services.get_npc_district(npc_id)
    -- This would normally look up NPC data
    -- For now, return a default
    return "neon_district"
end

-- ============================================================================
-- MAIN TICK PROCESSOR
-- ============================================================================

function Services.on_tick(tick)
    local events = {}
    
    -- Process mail
    local mail_events = Services.Mail.process(tick)
    for _, e in ipairs(mail_events) do
        table.insert(events, e)
    end
    
    -- Process deliveries
    local delivery_events = Services.Delivery.process(tick)
    for _, e in ipairs(delivery_events) do
        table.insert(events, e)
    end
    
    -- Process food orders
    local food_events = Services.Food.process(tick)
    for _, e in ipairs(food_events) do
        table.insert(events, e)
    end
    
    return events
end

-- Initialize all services
function Services.init()
    Services.Mail.init()
    Services.Delivery.init()
    Services.Food.init()
end

-- Export module
return Services
