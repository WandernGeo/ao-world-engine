--[[
  AO World Engine - City Services Process (v1.0)
  
  Municipal services simulation with budget-efficiency curves:
  - 12 service categories with budget-efficiency curves
  - Service fees affecting citizen happiness + company efficiency  
  - Capacity tracking, outage effects, and repair cycles
  - District-level service quality variance
  
  Config loaded from:
  - world_codec_28_city_services.json → budgets, fees, capacity, weights
  
  Integrates with: economy.lua (budget), district.lua (zones), agent_needs.lua (citizen needs)
]]--

local json = json or require("json")
local codec = require("codec_loader")

-- =============================================================================
-- GLOBAL STATE
-- =============================================================================

-- Service budget allocation (defaults — overridden by codec_28 when loaded)
ServiceBudgets = ServiceBudgets or {
    electricity = 100,
    water_sewage = 100,
    healthcare = 100,
    deathcare = 80,
    garbage = 100,
    education = 100,
    fire_rescue = 100,
    police = 100,
    transport = 100,
    communications = 90,
    parks = 80,
    administration = 100
}

-- Service fee multipliers (defaults — overridden by codec_28 when loaded)
ServiceFees = ServiceFees or {
    electricity = 100,
    water_sewage = 100,
    healthcare = 100,
    garbage = 100,
    education = 100,
    transport = 100,
    roads_parking = 100
}

-- Service capacity and utilization (defaults — overridden by codec_28 when loaded)
ServiceCapacity = ServiceCapacity or {
    electricity = { capacity_mw = 800, demand_mw = 650, surplus_pct = 0.23 },
    water = { capacity_m3 = 50000, demand_m3 = 42000, quality = 0.85 },
    sewage = { capacity_m3 = 45000, demand_m3 = 38000, treatment_quality = 0.70 },
    healthcare = { beds = 1200, patients = 850, ambulances = 45 },
    garbage = { trucks = 80, capacity_tons = 5000, collected_today = 0 },
    education = { elementary_seats = 5000, high_school_seats = 3000, university_seats = 1500 },
    fire = { engines = 30, helicopters = 4, active_fires = 0 },
    police = { officers = 400, patrol_cars = 80, prisoners = 120, prison_capacity = 500 },
    transport = { bus_lines = 12, subway_lines = 4, tram_lines = 6, daily_riders = 45000 }
}

-- Service quality per district (0.0-1.0)
DistrictServiceQuality = DistrictServiceQuality or {}

-- Active incidents (outages, fires, crimes)
ActiveIncidents = ActiveIncidents or {}

-- Service history for trend tracking
ServiceHistory = ServiceHistory or {}

-- =============================================================================
-- BUDGET-EFFICIENCY CURVE (from CS2 wiki)
-- =============================================================================

-- Non-linear: 50% budget → 25% efficiency, 150% budget → 125% efficiency
local function get_budget_efficiency(budget_pct)
    if budget_pct <= 50 then return 0.25 end
    if budget_pct <= 75 then 
        -- Linear interpolation 50→75: 0.25→0.60
        return 0.25 + (budget_pct - 50) / 25 * 0.35
    end
    if budget_pct <= 100 then
        -- Linear interpolation 75→100: 0.60→1.00
        return 0.60 + (budget_pct - 75) / 25 * 0.40
    end
    if budget_pct <= 125 then
        -- Diminishing returns 100→125: 1.00→1.15
        return 1.00 + (budget_pct - 100) / 25 * 0.15
    end
    -- 125→150: 1.15→1.25
    return 1.15 + (budget_pct - 125) / 25 * 0.10
end

-- =============================================================================
-- SERVICE FEE EFFECTS (from CS2 wiki)
-- =============================================================================

-- Every 1% below 100: +0.2% electricity consumption, +0.2% company efficiency, +0.05 happiness
-- Every 1% above 100: -0.4% electricity consumption, -0.4% company efficiency, -0.1 happiness  
local function calculate_fee_effects(service_name, fee_pct)
    local effects = { happiness = 0, company_efficiency = 0, consumption_modifier = 0 }
    local delta = fee_pct - 100
    
    if delta < 0 then
        -- Below 100%: citizens happier, companies more efficient, but more consumption
        effects.happiness = math.abs(delta) * 0.05
        effects.company_efficiency = math.abs(delta) * 0.002
        effects.consumption_modifier = math.abs(delta) * 0.002
    else
        -- Above 100%: citizens unhappy, companies less efficient, but less consumption
        effects.happiness = -delta * 0.1
        effects.company_efficiency = -delta * 0.004
        effects.consumption_modifier = -delta * 0.004
    end
    
    return effects
end


-- =============================================================================
-- CORE SERVICE SIMULATION
-- =============================================================================

local function simulate_electricity(tick, districts)
    local budget_eff = get_budget_efficiency(ServiceBudgets.electricity)
    local cap = ServiceCapacity.electricity
    
    -- Adjust capacity by budget efficiency
    local effective_capacity = cap.capacity_mw * budget_eff
    
    -- Calculate demand (grows with population and industry)
    local base_demand = cap.demand_mw
    
    -- Check for outage
    local surplus = effective_capacity - base_demand
    local surplus_pct = surplus / effective_capacity
    cap.surplus_pct = surplus_pct
    
    local outage = surplus < 0
    
    if outage then
        -- Blackout event
        table.insert(ActiveIncidents, {
            type = "blackout",
            severity = math.abs(surplus) / effective_capacity,
            tick = tick,
            message = "Power grid overloaded. Rolling blackouts in lower districts.",
            effects = {
                business_efficiency = -0.85,
                citizen_happiness = -0.4,
                crime_modifier = 1.3
            }
        })
    end
    
    -- Fee effects
    local fee_fx = calculate_fee_effects("electricity", ServiceFees.electricity)
    
    return {
        operational = not outage,
        efficiency = budget_eff,
        surplus_pct = surplus_pct,
        fee_effects = fee_fx,
        outage = outage
    }
end

local function simulate_water(tick, districts)
    local budget_eff = get_budget_efficiency(ServiceBudgets.water_sewage)
    local water = ServiceCapacity.water
    local sewage = ServiceCapacity.sewage
    
    local effective_water = water.capacity_m3 * budget_eff
    local effective_sewage = sewage.capacity_m3 * budget_eff
    
    local water_deficit = water.demand_m3 > effective_water
    local sewage_overflow = sewage.demand_m3 > effective_sewage
    
    if water_deficit then
        table.insert(ActiveIncidents, {
            type = "water_shortage",
            severity = (water.demand_m3 - effective_water) / water.demand_m3,
            tick = tick,
            message = "Water pressure dropping. Rationing in effect for lower districts."
        })
    end
    
    if sewage_overflow then
        table.insert(ActiveIncidents, {
            type = "sewage_overflow",
            severity = 0.3,
            tick = tick,
            message = "Sewage treatment at capacity. Overflow being dumped downriver."
        })
    end
    
    return {
        water_operational = not water_deficit,
        sewage_operational = not sewage_overflow,
        water_quality = water.quality * budget_eff,
        efficiency = budget_eff
    }
end

local function simulate_healthcare(tick, districts)
    local budget_eff = get_budget_efficiency(ServiceBudgets.healthcare)
    local hc = ServiceCapacity.healthcare
    
    local effective_beds = math.floor(hc.beds * budget_eff)
    local occupancy_rate = hc.patients / effective_beds
    
    -- Ambulance response time affected by budget
    local ambulance_response = 5 / budget_eff  -- minutes (baseline 5 min)
    
    local overwhelmed = occupancy_rate > 0.95
    
    if overwhelmed then
        table.insert(ActiveIncidents, {
            type = "healthcare_overwhelmed",
            severity = occupancy_rate - 0.95,
            tick = tick,
            message = "Hospitals at capacity. Non-critical patients being turned away."
        })
    end
    
    return {
        operational = true,
        efficiency = budget_eff,
        occupancy_rate = occupancy_rate,
        ambulance_response_min = ambulance_response,
        overwhelmed = overwhelmed,
        health_bonus = budget_eff * 0.15  -- Passive health bonus from healthcare presence
    }
end

local function simulate_police(tick, districts)
    local budget_eff = get_budget_efficiency(ServiceBudgets.police)
    local police = ServiceCapacity.police
    
    -- Patrol coverage affects crime probability
    local patrol_coverage = (police.patrol_cars * budget_eff) / 100  -- Normalize
    
    -- Crime modifier: lower budget = higher crime
    local crime_modifier = 1.0 + (1.0 - budget_eff) * 0.5
    
    -- Prison capacity check
    local prison_pct = police.prisoners / police.prison_capacity
    if prison_pct > 0.9 then
        table.insert(ActiveIncidents, {
            type = "prison_overcrowding",
            severity = prison_pct - 0.9,
            tick = tick,
            message = "Prisons at " .. math.floor(prison_pct * 100) .. "% capacity. Early releases being considered."
        })
    end
    
    return {
        efficiency = budget_eff,
        patrol_coverage = patrol_coverage,
        crime_modifier = crime_modifier,
        prison_utilization = prison_pct
    }
end

local function simulate_education(tick, districts)
    local budget_eff = get_budget_efficiency(ServiceBudgets.education)
    local edu = ServiceCapacity.education
    
    -- Budget affects student capacity
    local effective_elementary = math.floor(edu.elementary_seats * budget_eff)
    local effective_high_school = math.floor(edu.high_school_seats * budget_eff)
    local effective_university = math.floor(edu.university_seats * budget_eff)
    
    return {
        efficiency = budget_eff,
        elementary_capacity = effective_elementary,
        high_school_capacity = effective_high_school,
        university_capacity = effective_university,
        education_quality = budget_eff * 0.8 + 0.2  -- Minimum 20% quality even at minimum budget
    }
end

local function simulate_garbage(tick, districts)
    local budget_eff = get_budget_efficiency(ServiceBudgets.garbage)
    local garb = ServiceCapacity.garbage
    
    local effective_trucks = math.floor(garb.trucks * budget_eff)
    -- Each truck can collect ~50 tons/day
    local daily_capacity = effective_trucks * 50
    
    -- Generate garbage (increases with population, decreases with education)
    local daily_generation = garb.capacity_tons * 0.8  -- 80% of max capacity as baseline
    
    local uncollected = daily_generation - daily_capacity
    if uncollected > 0 then
        table.insert(ActiveIncidents, {
            type = "garbage_overflow",
            severity = uncollected / daily_generation,
            tick = tick,
            message = "Garbage piling up. " .. math.floor(uncollected) .. " tons uncollected."
        })
    end
    
    return {
        efficiency = budget_eff,
        trucks_active = effective_trucks,
        daily_capacity = daily_capacity,
        uncollected_pct = math.max(0, uncollected / daily_generation),
        pollution_modifier = uncollected > 0 and 1.0 + (uncollected / daily_generation) * 0.3 or 1.0
    }
end

local function simulate_fire(tick, districts)
    local budget_eff = get_budget_efficiency(ServiceBudgets.fire_rescue)
    local fire = ServiceCapacity.fire
    
    -- Fire hazard reduction based on coverage
    local hazard_reduction = budget_eff * 0.7
    
    -- Response time
    local response_time = 8 / budget_eff  -- minutes
    
    return {
        efficiency = budget_eff,
        engines_available = math.floor(fire.engines * budget_eff),
        helicopters_available = math.floor(fire.helicopters * budget_eff),
        fire_hazard_reduction = hazard_reduction,
        response_time_min = response_time,
        active_fires = fire.active_fires
    }
end

local function simulate_transport(tick, districts)
    local budget_eff = get_budget_efficiency(ServiceBudgets.transport)
    local trans = ServiceCapacity.transport
    
    -- Budget affects frequency and capacity
    local effective_riders = math.floor(trans.daily_riders * budget_eff)
    
    -- Ticket fee effect on ridership
    local fee_modifier = 1.0
    if ServiceFees.transport > 100 then
        -- Higher fees = fewer riders = more cars = more traffic
        fee_modifier = 1.0 - (ServiceFees.transport - 100) * 0.007
    elseif ServiceFees.transport < 100 then
        -- Lower fees = more riders = less traffic
        fee_modifier = 1.0 + (100 - ServiceFees.transport) * 0.005
    end
    
    return {
        efficiency = budget_eff,
        ridership = math.floor(effective_riders * fee_modifier),
        traffic_modifier = 1.0 / fee_modifier,  -- Inverse: more riders = less traffic
        bus_lines = trans.bus_lines,
        subway_lines = trans.subway_lines
    }
end


-- =============================================================================
-- AGGREGATE CITY SERVICE SCORE
-- =============================================================================

local function calculate_city_service_score()
    local scores = {}
    for service, budget in pairs(ServiceBudgets) do
        scores[service] = get_budget_efficiency(budget)
    end
    
    -- Weighted average (some services matter more)
    local weights = {
        electricity = 1.5,
        water_sewage = 1.5,
        healthcare = 1.2,
        police = 1.2,
        education = 1.0,
        garbage = 1.0,
        fire_rescue = 0.8,
        transport = 1.0,
        communications = 0.6,
        parks = 0.5,
        deathcare = 0.4,
        administration = 0.5
    }
    
    local total_score = 0
    local total_weight = 0
    for service, eff in pairs(scores) do
        local w = weights[service] or 0.5
        total_score = total_score + eff * w
        total_weight = total_weight + w
    end
    
    return {
        overall = total_score / total_weight,
        per_service = scores,
        citizen_happiness_modifier = (total_score / total_weight - 0.5) * 0.4,  -- ±0.2
        land_value_modifier = (total_score / total_weight - 0.5) * 0.6  -- ±0.3
    }
end


-- =============================================================================
-- HANDLERS
-- =============================================================================

-- Cron handler: run full service simulation each tick
Handlers.add("Cron-Tick-Services", "Cron-Tick-Services", function(msg)
    local tick = tonumber(msg.Tags.Tick) or 0
    local districts = {} -- Would come from district.lua state
    
    -- Clear previous tick incidents
    ActiveIncidents = {}
    
    -- Run all service simulations
    local results = {
        tick = tick,
        electricity = simulate_electricity(tick, districts),
        water = simulate_water(tick, districts),
        healthcare = simulate_healthcare(tick, districts),
        police = simulate_police(tick, districts),
        education = simulate_education(tick, districts),
        garbage = simulate_garbage(tick, districts),
        fire = simulate_fire(tick, districts),
        transport = simulate_transport(tick, districts),
        incidents = ActiveIncidents,
        overall = calculate_city_service_score()
    }
    
    -- Store in history (keep last 100 ticks)
    table.insert(ServiceHistory, {tick = tick, score = results.overall.overall})
    if #ServiceHistory > 100 then
        table.remove(ServiceHistory, 1)
    end
    
    -- Broadcast results to other processes
    ao.send({
        Target = ao.id,
        Action = "ServiceSimulation-Result",
        Data = json.encode(results)
    })
    
    msg.reply({
        Action = "Service-Tick-Complete",
        Data = json.encode({
            tick = tick,
            overall_score = results.overall.overall,
            incidents = #ActiveIncidents,
            happiness_modifier = results.overall.citizen_happiness_modifier
        })
    })
end)

-- Adjust service budget
Handlers.add("Adjust-Service-Budget", "Adjust-Service-Budget", function(msg)
    local data = json.decode(msg.Data or "{}")
    local service = data.service
    local budget = tonumber(data.budget)
    
    if not service or not budget then
        msg.reply({ Action = "Error", Data = "Missing service or budget" })
        return
    end
    
    if not ServiceBudgets[service] then
        msg.reply({ Action = "Error", Data = "Unknown service: " .. tostring(service) })
        return
    end
    
    -- Clamp to 50-150
    budget = math.max(50, math.min(150, budget))
    ServiceBudgets[service] = budget
    
    local efficiency = get_budget_efficiency(budget)
    
    msg.reply({
        Action = "Budget-Updated",
        Data = json.encode({
            service = service,
            budget_pct = budget,
            efficiency = efficiency,
            message = service .. " budget set to " .. budget .. "% (efficiency: " .. string.format("%.0f%%", efficiency * 100) .. ")"
        })
    })
end)

-- Adjust service fees  
Handlers.add("Adjust-Service-Fee", "Adjust-Service-Fee", function(msg)
    local data = json.decode(msg.Data or "{}")
    local service = data.service
    local fee = tonumber(data.fee)
    
    if not service or not fee then
        msg.reply({ Action = "Error", Data = "Missing service or fee" })
        return
    end
    
    if not ServiceFees[service] then
        msg.reply({ Action = "Error", Data = "Service doesn't have adjustable fees: " .. tostring(service) })
        return
    end
    
    -- Clamp to 50-200
    fee = math.max(50, math.min(200, fee))
    ServiceFees[service] = fee
    
    local effects = calculate_fee_effects(service, fee)
    
    msg.reply({
        Action = "Fee-Updated",
        Data = json.encode({
            service = service,
            fee_pct = fee,
            effects = effects
        })
    })
end)

-- Query service status
Handlers.add("Get-Service-Status", "Get-Service-Status", function(msg)
    local service = msg.Tags.Service or "all"
    
    if service == "all" then
        msg.reply({
            Action = "Service-Status",
            Data = json.encode({
                budgets = ServiceBudgets,
                fees = ServiceFees,
                capacity = ServiceCapacity,
                incidents = ActiveIncidents,
                overall = calculate_city_service_score(),
                history_length = #ServiceHistory
            })
        })
    else
        local budget = ServiceBudgets[service]
        if budget then
            msg.reply({
                Action = "Service-Status",
                Data = json.encode({
                    service = service,
                    budget_pct = budget,
                    efficiency = get_budget_efficiency(budget),
                    fee = ServiceFees[service],
                    capacity = ServiceCapacity[service]
                })
            })
        else
            msg.reply({ Action = "Error", Data = "Unknown service: " .. tostring(service) })
        end
    end
end)

-- Query incident history
Handlers.add("Get-Incidents", "Get-Incidents", function(msg)
    msg.reply({
        Action = "Incidents",
        Data = json.encode(ActiveIncidents)
    })
end)

-- Trigger a manual incident (for events/narrative)
Handlers.add("Trigger-Incident", "Trigger-Incident", function(msg)
    local data = json.decode(msg.Data or "{}")
    
    table.insert(ActiveIncidents, {
        type = data.type or "unknown",
        severity = data.severity or 0.5,
        tick = data.tick or 0,
        message = data.message or "An incident has occurred.",
        effects = data.effects or {},
        manual = true
    })
    
    msg.reply({
        Action = "Incident-Triggered",
        Data = json.encode({
            total_incidents = #ActiveIncidents,
            latest = ActiveIncidents[#ActiveIncidents]
        })
    })
end)

-- =============================================================================
-- CODEC CALLBACKS
-- =============================================================================

-- When codec_28_city_services is loaded, extract budgets/fees/capacity
codec.on("city_services", function(data)
    if data.default_budgets then
        ServiceBudgets = codec.deep_merge(ServiceBudgets, data.default_budgets)
    end
    if data.default_fees then
        ServiceFees = codec.deep_merge(ServiceFees, data.default_fees)
    end
    if data.capacity then
        ServiceCapacity = codec.deep_merge(ServiceCapacity, data.capacity)
    end
end)

-- Register standard LoadCodec handler
codec.register_handler()

print("🏗️ City Services Process loaded. 12 service categories, budget-efficiency curves, fee effects, incident tracking.")
