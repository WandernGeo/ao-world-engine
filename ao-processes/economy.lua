--[[
  AO World Engine - Economy Process
  
  Handles city-wide economics:
  - Tax collection from NPCs
  - City budget management
  - Service funding (police, sanitation, etc.)
  - Wealth tracking and distribution
  
  Works with world.lua for coordinated economy simulation.
]]--

local json = require("json")
local crypto = require("crypto")

-- =============================================================================
-- GLOBAL STATE
-- =============================================================================

-- City treasury
CityBudget = CityBudget or 1000000  -- Starting GEP
TotalTaxesCollected = TotalTaxesCollected or 0
TotalExpenses = TotalExpenses or 0

-- Tax rates (from codec_20)
TaxRates = TaxRates or {
    income = 0.10,
    sales = 0.05,
    temple_tithe = 0.05
}

-- Population economics
PopulationWealth = PopulationWealth or {}  -- { npc_id: gep_balance }
DistrictEconomies = DistrictEconomies or {}  -- { district_id: { gdp, employment, etc } }

-- Service levels (0.0 to 1.0)
ServiceLevels = ServiceLevels or {
    police = 1.0,
    sanitation = 1.0,
    infrastructure = 1.0,
    healthcare = 1.0,
    emergency = 1.0
}

-- Economic events in effect
ActiveEconomicEvents = ActiveEconomicEvents or {}

-- Transaction log (for audit/replay)
TransactionLog = TransactionLog or {}

-- Configuration from codec
INCOME_BY_ARCHETYPE = {
    shopkeeper = 120,
    bartender = 80,
    guard = 100,
    street_vendor = 50,
    medic = 150,
    civilian = 75,
    technician = 130,
    laborer = 60,
    smuggler = 200,
    priest = 90
}

SERVICE_COSTS = {
    police = { cost_per_officer = 80, per_1000_pop = 5 },
    sanitation = { cost_per_worker = 40, per_1000_pop = 3 },
    infrastructure = { cost_per_day = 3000 },
    healthcare = { cost_per_bed = 100, per_1000_pop = 10 },
    emergency = { cost_per_unit = 150, per_1000_pop = 2 }
}

CRISIS_THRESHOLDS = {
    warning = 10000,
    critical = 5000,
    collapse = 1000
}

-- =============================================================================
-- DETERMINISTIC UTILITIES
-- =============================================================================

function hash_to_number(str, max)
    local hash = crypto.digest.sha256(str)
    return tonumber(hash:sub(1, 8), 16) % max
end

function seeded_variance(base, variance, seed)
    local roll = hash_to_number(seed, 1000) / 1000  -- 0.0 to 1.0
    local delta = base * variance * (roll * 2 - 1)  -- +/- variance%
    return math.floor(base + delta)
end

-- =============================================================================
-- INCOME CALCULATION
-- =============================================================================

function calculate_npc_income(npc_id, archetype, tick)
    local base = INCOME_BY_ARCHETYPE[archetype] or INCOME_BY_ARCHETYPE.civilian
    local variance = 0.3
    
    -- Apply deterministic variance
    local actual = seeded_variance(base, variance, npc_id .. "_income_" .. tick)
    
    -- Apply economic event modifiers
    for _, event in ipairs(ActiveEconomicEvents) do
        if event.effect.income_modifier then
            actual = math.floor(actual * (1 + event.effect.income_modifier))
        end
    end
    
    return actual
end

function calculate_tax(income)
    return math.floor(income * TaxRates.income)
end

-- =============================================================================
-- TAX COLLECTION
-- =============================================================================

function collect_taxes_from_district(district_id, tick, population)
    local tax_revenue = 0
    local district_gdp = 0
    
    -- Calculate based on district population
    for npc_id, npc_data in pairs(population) do
        local income = calculate_npc_income(npc_id, npc_data.archetype, tick)
        local tax = calculate_tax(income)
        
        tax_revenue = tax_revenue + tax
        district_gdp = district_gdp + income
        
        -- Update NPC wealth (subtract tax)
        if PopulationWealth[npc_id] then
            PopulationWealth[npc_id] = PopulationWealth[npc_id] + income - tax
        else
            PopulationWealth[npc_id] = income - tax
        end
    end
    
    -- Update district economics
    DistrictEconomies[district_id] = {
        gdp = district_gdp,
        tax_revenue = tax_revenue,
        updated_tick = tick
    }
    
    -- Add to city budget
    CityBudget = CityBudget + tax_revenue
    TotalTaxesCollected = TotalTaxesCollected + tax_revenue
    
    -- Log transaction
    table.insert(TransactionLog, {
        type = "tax_collection",
        district = district_id,
        amount = tax_revenue,
        tick = tick
    })
    
    return tax_revenue, district_gdp
end

-- =============================================================================
-- CITY EXPENSES
-- =============================================================================

function calculate_daily_expenses(population_count)
    local expenses = {}
    local total = 0
    
    for service, config in pairs(SERVICE_COSTS) do
        local cost = 0
        
        if config.cost_per_day then
            cost = config.cost_per_day
        elseif config.per_1000_pop then
            local units = math.floor(population_count / 1000) * config.per_1000_pop
            local unit_cost = config.cost_per_officer or config.cost_per_worker or 
                             config.cost_per_bed or config.cost_per_unit or 50
            cost = units * unit_cost
        end
        
        -- Apply service level (reduced service = reduced cost but deterioration)
        cost = math.floor(cost * ServiceLevels[service])
        
        expenses[service] = cost
        total = total + cost
    end
    
    expenses.total = total
    return expenses
end

function pay_city_expenses(tick, population_count)
    local expenses = calculate_daily_expenses(population_count)
    
    if CityBudget >= expenses.total then
        -- Full payment
        CityBudget = CityBudget - expenses.total
        TotalExpenses = TotalExpenses + expenses.total
        
        -- Log transaction
        table.insert(TransactionLog, {
            type = "city_expenses",
            breakdown = expenses,
            tick = tick
        })
        
        return true, expenses
    else
        -- Budget crisis - reduce services proportionally
        local available = CityBudget
        local ratio = available / expenses.total
        
        for service, _ in pairs(ServiceLevels) do
            ServiceLevels[service] = ServiceLevels[service] * ratio
            ServiceLevels[service] = math.max(0.1, ServiceLevels[service])  -- Min 10%
        end
        
        CityBudget = 0
        TotalExpenses = TotalExpenses + available
        
        -- Log crisis
        table.insert(TransactionLog, {
            type = "budget_crisis",
            shortfall = expenses.total - available,
            service_cuts = ServiceLevels,
            tick = tick
        })
        
        return false, { total = available, crisis = true }
    end
end

-- =============================================================================
-- WEALTH CLASSIFICATION
-- =============================================================================

function get_wealth_level(gep)
    if gep < 100 then return "destitute"
    elseif gep < 500 then return "poor"
    elseif gep < 2000 then return "working"
    elseif gep < 10000 then return "comfortable"
    elseif gep < 100000 then return "wealthy"
    else return "elite" end
end

function get_city_wealth_distribution()
    local distribution = {
        destitute = 0,
        poor = 0,
        working = 0,
        comfortable = 0,
        wealthy = 0,
        elite = 0
    }
    
    for _, gep in pairs(PopulationWealth) do
        local level = get_wealth_level(gep)
        distribution[level] = distribution[level] + 1
    end
    
    return distribution
end

-- =============================================================================
-- ECONOMIC EVENTS
-- =============================================================================

function trigger_economic_event(event_type, tick, duration_days)
    local events = {
        market_crash = {
            effect = { income_modifier = -0.3, job_loss_chance = 0.1 },
            duration_ticks = duration_days * 240
        },
        price_surge = {
            effect = { price_modifier = 0.5 },
            duration_ticks = duration_days * 240
        },
        tax_increase = {
            effect = { income_tax_delta = 0.05 },
            duration_ticks = duration_days * 240
        },
        boom = {
            effect = { income_modifier = 0.2 },
            duration_ticks = duration_days * 240
        }
    }
    
    local event = events[event_type]
    if event then
        event.type = event_type
        event.start_tick = tick
        event.end_tick = tick + event.duration_ticks
        table.insert(ActiveEconomicEvents, event)
        
        -- Apply immediate effects
        if event.effect.income_tax_delta then
            TaxRates.income = TaxRates.income + event.effect.income_tax_delta
        end
        
        return true
    end
    return false
end

function update_economic_events(tick)
    local still_active = {}
    
    for _, event in ipairs(ActiveEconomicEvents) do
        if tick < event.end_tick then
            table.insert(still_active, event)
        else
            -- Revert effects
            if event.effect.income_tax_delta then
                TaxRates.income = TaxRates.income - event.effect.income_tax_delta
            end
        end
    end
    
    ActiveEconomicEvents = still_active
end

-- =============================================================================
-- HANDLERS
-- =============================================================================

-- Initialize economy
Handlers.add("init", Handlers.utils.hasMatchingTag("Action", "Init"), function(msg)
    local data = json.decode(msg.Data)
    
    if data.initial_budget then CityBudget = data.initial_budget end
    if data.tax_rates then 
        TaxRates.income = data.tax_rates.income or TaxRates.income
        TaxRates.sales = data.tax_rates.sales or TaxRates.sales
    end
    
    ao.send({
        Target = msg.From,
        Action = "init-complete",
        Data = json.encode({
            budget = CityBudget,
            tax_rates = TaxRates
        })
    })
end)

-- CRON: Daily economy processing
Handlers.add("cron-economy", Handlers.utils.hasMatchingTag("Action", "Cron"), function(msg)
    local data = json.decode(msg.Data) or {}
    local tick = data.tick or 0
    
    -- Only process on day boundaries (every 240 ticks)
    if tick % 240 ~= 0 then return end
    
    local population_count = data.population or 1000
    
    -- Update economic events
    update_economic_events(tick)
    
    -- Pay city expenses
    local success, expenses = pay_city_expenses(tick, population_count)
    
    -- Check crisis thresholds
    local crisis_level = nil
    if CityBudget < CRISIS_THRESHOLDS.collapse then
        crisis_level = "collapse"
    elseif CityBudget < CRISIS_THRESHOLDS.critical then
        crisis_level = "critical"
    elseif CityBudget < CRISIS_THRESHOLDS.warning then
        crisis_level = "warning"
    end
    
    -- Broadcast economy update
    ao.send({
        Target = ao.id,
        Action = "economy-update",
        Data = json.encode({
            tick = tick,
            budget = CityBudget,
            expenses = expenses,
            services_healthy = success,
            crisis_level = crisis_level
        })
    })
end)

-- Receive tax from district
Handlers.add("tax-deposit", Handlers.utils.hasMatchingTag("Action", "tax-deposit"), function(msg)
    local data = json.decode(msg.Data)
    local amount = data.amount or 0
    
    CityBudget = CityBudget + amount
    TotalTaxesCollected = TotalTaxesCollected + amount
    
    table.insert(TransactionLog, {
        type = "tax_deposit",
        from = msg.From,
        amount = amount,
        tick = data.tick
    })
    
    ao.send({
        Target = msg.From,
        Action = "tax-received",
        Data = json.encode({ new_budget = CityBudget })
    })
end)

-- Query economy state
Handlers.add("get-economy", Handlers.utils.hasMatchingTag("Action", "get-economy"), function(msg)
    ao.send({
        Target = msg.From,
        Action = "economy-response",
        Data = json.encode({
            budget = CityBudget,
            total_taxes = TotalTaxesCollected,
            total_expenses = TotalExpenses,
            tax_rates = TaxRates,
            service_levels = ServiceLevels,
            active_events = ActiveEconomicEvents,
            wealth_distribution = get_city_wealth_distribution()
        })
    })
end)

-- Trigger economic event (admin only)
Handlers.add("trigger-event", Handlers.utils.hasMatchingTag("Action", "trigger-event"), function(msg)
    local data = json.decode(msg.Data)
    local success = trigger_economic_event(data.event_type, data.tick, data.duration_days or 7)
    
    ao.send({
        Target = msg.From,
        Action = "event-response",
        Data = json.encode({ success = success, active_events = ActiveEconomicEvents })
    })
end)

-- Adjust service levels
Handlers.add("set-service-level", Handlers.utils.hasMatchingTag("Action", "set-service-level"), function(msg)
    local data = json.decode(msg.Data)
    
    if ServiceLevels[data.service] then
        ServiceLevels[data.service] = math.max(0, math.min(1, data.level))
        
        ao.send({
            Target = msg.From,
            Action = "service-updated",
            Data = json.encode({ service_levels = ServiceLevels })
        })
    end
end)

-- =============================================================================
-- NPC TRANSACTIONS
-- =============================================================================

-- Record a trade between NPCs
Handlers.add("record-trade", Handlers.utils.hasMatchingTag("Action", "record-trade"), function(msg)
    local data = json.decode(msg.Data)
    
    local buyer_id = data.buyer
    local seller_id = data.seller
    local amount = data.amount
    local tax = math.floor(amount * TaxRates.sales)
    
    -- Update wealth
    PopulationWealth[buyer_id] = (PopulationWealth[buyer_id] or 0) - amount
    PopulationWealth[seller_id] = (PopulationWealth[seller_id] or 0) + (amount - tax)
    
    -- City gets sales tax
    CityBudget = CityBudget + tax
    
    table.insert(TransactionLog, {
        type = "trade",
        buyer = buyer_id,
        seller = seller_id,
        amount = amount,
        tax = tax,
        tick = data.tick
    })
    
    ao.send({
        Target = msg.From,
        Action = "trade-recorded",
        Data = json.encode({ 
            buyer_balance = PopulationWealth[buyer_id],
            seller_balance = PopulationWealth[seller_id],
            tax_collected = tax
        })
    })
end)

-- =============================================================================
-- HELPERS
-- =============================================================================

function table_length(t)
    local count = 0
    for _ in pairs(t) do count = count + 1 end
    return count
end

-- Trim transaction log (keep last 1000)
function trim_transaction_log()
    while #TransactionLog > 1000 do
        table.remove(TransactionLog, 1)
    end
end

-- =============================================================================
-- MODULE EXPORT
-- =============================================================================

return {
    calculate_npc_income = calculate_npc_income,
    calculate_tax = calculate_tax,
    get_wealth_level = get_wealth_level,
    trigger_economic_event = trigger_economic_event
}
