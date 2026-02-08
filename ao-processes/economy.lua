--[[
  AO World Engine - Economy Process (v2)
  
  Comprehensive city economy:
  - Zoning and land value
  - Production chains and supply/demand
  - Megacorporation influence
  - Multi-layered taxation
  - Progressive tax brackets
  - Employment and unemployment
  - Economic events and crises
  - Black market economy
  
  Config loaded from:
  - world_codec_20_economy.json → taxes, zones, wages, megacorps
  - world_codec_27_city_finance.json → budget allocation, UBI
  - world_codec_35_trade_diplomacy.json → trade, price volatility
  
  Designed for millions of NPCs across thousands of job types.
]]--

local json = json or require("json")
local crypto = crypto or require("crypto")
local codec = require("codec_loader")

-- =============================================================================
-- GLOBAL STATE
-- =============================================================================

-- City Treasury
CityBudget = CityBudget or 1000000
TotalTaxRevenue = TotalTaxRevenue or 0
TotalExpenses = TotalExpenses or 0
ReserveTarget = ReserveTarget or 100000

-- Economic Indicators
EconomicIndicators = EconomicIndicators or {
    gdp = 0,
    gdp_growth = 0.02,
    inflation = 0.02,
    unemployment_rate = 0.12,
    gini_coefficient = 0.72,
    black_market_share = 0.25
}

-- Tax Configuration (defaults — overridden by codec_20 when loaded)
TaxConfig = TaxConfig or {
    income_brackets = {
        { min = 0, max = 500, rate = 0.00 },
        { min = 500, max = 2000, rate = 0.05 },
        { min = 2000, max = 10000, rate = 0.10 },
        { min = 10000, max = 50000, rate = 0.15 },
        { min = 50000, max = math.huge, rate = 0.20 }
    },
    property_tax_rate = 0.02,
    sales_tax_rate = 0.05,
    corporate_tax_rate = 0.12,
    corporate_effective_rate = 0.03,  -- After loopholes
    temple_tithe = 0.05
}

-- Budget Allocation (percentages)
BudgetAllocation = BudgetAllocation or {
    law_enforcement = 0.25,
    infrastructure = 0.20,
    healthcare = 0.15,
    sanitation = 0.10,
    education = 0.10,
    social_services = 0.10,
    administration = 0.05,
    emergency_fund = 0.05
}

-- Service Levels (0.0 to 1.0, affects city quality)
ServiceLevels = ServiceLevels or {
    law_enforcement = 1.0,
    infrastructure = 1.0,
    healthcare = 1.0,
    sanitation = 1.0,
    education = 1.0,
    social_services = 1.0
}

-- District Economies
DistrictEconomies = DistrictEconomies or {}

-- Zones (defaults — overridden by codec_20 when loaded)
Zones = Zones or {}

-- Production Chain Status
ProductionChains = ProductionChains or {
    raw_materials = {},
    processed_goods = {},
    finished_goods = {}
}

-- Megacorporations
Megacorps = Megacorps or {
    NexGen = { sector = "cybernetics", market_share = 0.4, employees = 15000 },
    Omnicorp = { sector = "infrastructure", market_share = 0.6, employees = 25000 },
    Synthetica = { sector = "biotech", market_share = 0.35, employees = 8000 },
    DataVault = { sector = "information", market_share = 0.5, employees = 5000 }
}

-- Employment Statistics
Employment = Employment or {
    total_jobs = 0,
    filled_jobs = 0,
    unemployed = 0,
    by_category = {},
    by_skill_level = {
        automated = 0,
        low_skill = 0,
        mid_skill = 0,
        high_skill = 0,
        elite = 0
    }
}

-- Wealth Distribution
WealthDistribution = WealthDistribution or {
    destitute = 0.15,
    poor = 0.30,
    working = 0.35,
    comfortable = 0.12,
    wealthy = 0.06,
    elite = 0.02
}

-- Active Economic Events
ActiveEconomicEvents = ActiveEconomicEvents or {}

-- UBI (Universal Basic Income)
UBI = UBI or {
    enabled = true,
    amount = 30,
    recipients = 0,
    total_cost = 0
}

-- Transaction Log
TransactionLog = TransactionLog or {}

-- Black Market Economy
BlackMarket = BlackMarket or {
    estimated_gdp = 0,
    protection_fee_rate = 0.15,
    active_sectors = {"drugs", "weapons", "stolen_goods", "data", "services"}
}

-- =============================================================================
-- UTILITY FUNCTIONS
-- =============================================================================

function hash_to_number(str, max)
    local hash = crypto.digest.sha256(str)
    return tonumber(hash:sub(1, 8), 16) % max
end

function seeded_variance(base, variance, seed)
    local roll = hash_to_number(seed, 1000) / 1000
    local delta = base * variance * (roll * 2 - 1)
    return math.floor(base + delta)
end

function clamp(value, min_val, max_val)
    return math.max(min_val, math.min(max_val, value))
end

-- =============================================================================
-- TAX CALCULATION (Progressive Brackets)
-- =============================================================================

function calculate_income_tax(income)
    local total_tax = 0
    local remaining_income = income
    
    for _, bracket in ipairs(TaxConfig.income_brackets) do
        if remaining_income <= 0 then break end
        
        local taxable_in_bracket = math.min(remaining_income, bracket.max - bracket.min)
        if income > bracket.min then
            total_tax = total_tax + (taxable_in_bracket * bracket.rate)
            remaining_income = remaining_income - taxable_in_bracket
        end
    end
    
    return math.floor(total_tax)
end

function calculate_property_tax(land_value)
    return math.floor(land_value * TaxConfig.property_tax_rate)
end

function calculate_sales_tax(transaction_amount, exempt)
    if exempt then return 0 end
    return math.floor(transaction_amount * TaxConfig.sales_tax_rate)
end

function calculate_temple_tithe(income)
    return math.floor(income * TaxConfig.temple_tithe)
end

-- =============================================================================
-- LAND VALUE CALCULATION
-- =============================================================================

-- Land Value Zone Multipliers (defaults — overridden by codec_20 when loaded)
local ZONE_MULTIPLIERS = {
    ZONE_R4 = 5.0,  -- Luxury Arcology
    ZONE_C3 = 4.0,  -- Corporate Plaza
    ZONE_IT = 3.0,  -- Tech Park
    ZONE_R1 = 2.0,  -- Low-Density Hab
    ZONE_C2 = 1.5,  -- Commercial District
    ZONE_R2 = 1.0,  -- Medium-Density Hab
    ZONE_C1 = 0.8,  -- Street-Level Commerce
    ZONE_I1 = 0.6,  -- Light Industry
    ZONE_R3 = 0.5,  -- High-Density Megablock
    ZONE_I2 = 0.3,  -- Heavy Industry
    ZONE_I3 = 0.1,  -- Hazardous Processing
    ZONE_U = 0.05   -- Undercity
}

-- Wage Ranges (defaults — overridden by codec_20 when loaded)
WAGE_RANGES = {
    low_skill = { min = 40, max = 80 },
    mid_skill = { min = 80, max = 150 },
    high_skill = { min = 150, max = 300 },
    elite = { min = 300, max = 1000 }
}

-- Price Volatility (from codec_35 when loaded)
PRICE_VOLATILITY = {
    base_inflation_per_tick = 0.00001,
    overproduction_threshold = 2.0,
    scarcity_threshold = 0.5
}

function calculate_land_value(parcel)
    local base_value = parcel.base_value or 1000
    local zone_mult = ZONE_MULTIPLIERS[parcel.zone] or 1.0
    
    -- Positive modifiers
    local positive = 0
    if parcel.near_transit then positive = positive + 0.3 end
    if parcel.near_healthcare then positive = positive + 0.1 end
    if parcel.near_education then positive = positive + 0.15 end
    if parcel.near_green_space then positive = positive + 0.2 end
    
    -- Negative modifiers
    local negative = 0
    if parcel.pollution then negative = negative - (parcel.pollution * 0.3) end
    if parcel.noise then negative = negative - (parcel.noise * 0.2) end
    if parcel.crime then negative = negative - (parcel.crime * 0.4) end
    
    local final_value = base_value * zone_mult * (1 + positive) * (1 + negative)
    return math.floor(math.max(10, final_value))
end

-- =============================================================================
-- EMPLOYMENT SYSTEM
-- =============================================================================



function calculate_npc_income(job_code, skill_level, tick)
    local range = WAGE_RANGES[skill_level] or WAGE_RANGES.low_skill
    local base = (range.min + range.max) / 2
    
    -- Apply variance based on job and tick
    local seed = job_code .. "_income_" .. tick
    local actual = seeded_variance(base, 0.3, seed)
    
    -- Apply economic modifiers
    if EconomicIndicators.gdp_growth < 0 then
        actual = actual * (1 + EconomicIndicators.gdp_growth)
    end
    
    return math.floor(actual)
end

function update_employment_stats(population_count)
    -- Calculate unemployment based on economic conditions
    local base_unemployment = 0.05  -- Natural rate
    local structural = 0.07  -- Due to automation
    
    -- Economic factors
    local economic_factor = 0
    if EconomicIndicators.gdp_growth < 0 then
        economic_factor = math.abs(EconomicIndicators.gdp_growth) * 0.5
    end
    
    EconomicIndicators.unemployment_rate = clamp(
        base_unemployment + structural + economic_factor,
        0.02, 0.40
    )
    
    Employment.total_jobs = math.floor(population_count * 0.6)  -- ~60% working age
    Employment.filled_jobs = math.floor(Employment.total_jobs * (1 - EconomicIndicators.unemployment_rate))
    Employment.unemployed = Employment.total_jobs - Employment.filled_jobs
    
    -- Calculate UBI cost
    if UBI.enabled then
        UBI.recipients = Employment.unemployed
        UBI.total_cost = UBI.recipients * UBI.amount
    end
end

-- =============================================================================
-- CITY BUDGET MANAGEMENT
-- =============================================================================

function calculate_budget_expenses(population_count)
    local total_budget_needed = 0
    local expenses = {}
    
    -- Base costs scale with population
    local per_capita_cost = 15  -- GEP per person per day
    total_budget_needed = population_count * per_capita_cost
    
    -- Allocate by category
    for category, percentage in pairs(BudgetAllocation) do
        expenses[category] = math.floor(total_budget_needed * percentage)
    end
    
    -- Add UBI if enabled
    if UBI.enabled then
        expenses.ubi = UBI.total_cost
        total_budget_needed = total_budget_needed + UBI.total_cost
    end
    
    expenses.total = total_budget_needed
    return expenses
end

function pay_city_expenses(tick, population_count, tax_revenue)
    local expenses = calculate_budget_expenses(population_count)
    local available = CityBudget + tax_revenue
    
    -- Record tax revenue
    CityBudget = CityBudget + tax_revenue
    TotalTaxRevenue = TotalTaxRevenue + tax_revenue
    
    if available >= expenses.total then
        -- Full payment - all services funded
        CityBudget = CityBudget - expenses.total
        TotalExpenses = TotalExpenses + expenses.total
        
        -- Restore/maintain service levels
        for service, _ in pairs(ServiceLevels) do
            ServiceLevels[service] = clamp(ServiceLevels[service] + 0.01, 0, 1.0)
        end
        
        log_transaction("city_expenses", tick, expenses)
        return true, expenses, get_crisis_level()
    else
        -- Budget crisis - must cut services
        local ratio = available / expenses.total
        local actual_spending = {}
        
        for category, amount in pairs(expenses) do
            if category ~= "total" then
                actual_spending[category] = math.floor(amount * ratio)
            end
        end
        
        -- Reduce service levels
        for service, _ in pairs(ServiceLevels) do
            local cut = (1 - ratio) * 0.1  -- 10% reduction per funding shortfall
            ServiceLevels[service] = clamp(ServiceLevels[service] - cut, 0.1, 1.0)
        end
        
        CityBudget = 0
        TotalExpenses = TotalExpenses + available
        
        log_transaction("budget_crisis", tick, {
            shortfall = expenses.total - available,
            service_levels = ServiceLevels
        })
        
        return false, actual_spending, get_crisis_level()
    end
end

function get_crisis_level()
    if CityBudget >= 50000 then return "healthy"
    elseif CityBudget >= 20000 then return "strained"
    elseif CityBudget >= 5000 then return "crisis"
    else return "collapse"
    end
end

-- =============================================================================
-- PRODUCTION CHAINS
-- =============================================================================

function update_production_chains(tick)
    -- Calculate supply/demand for production chain components
    -- This affects prices and employment
    
    local chains = {
        raw_materials = { "scrap_metal", "petrochemicals", "rare_earth", "organic_matter", "water" },
        processed = { "alloy_sheets", "polymers", "electronics", "nutrient_paste" },
        finished = { "consumer_electronics", "cybernetics", "weapons", "medical" }
    }
    
    -- Simulate supply chain status
    for category, items in pairs(chains) do
        ProductionChains[category] = ProductionChains[category] or {}
        for _, item in ipairs(items) do
            -- Deterministic supply level based on tick
            local seed = item .. "_supply_" .. tick
            local supply = 0.5 + (hash_to_number(seed, 100) / 200)  -- 0.5 to 1.0
            ProductionChains[category][item] = supply
        end
    end
    
    return ProductionChains
end

function get_production_modifier(finished_good)
    -- Check if production chain is healthy
    local chain_health = 1.0
    
    -- Finished goods depend on processed goods
    if ProductionChains.processed then
        for _, supply in pairs(ProductionChains.processed) do
            chain_health = chain_health * supply
        end
    end
    
    return chain_health
end

-- =============================================================================
-- MEGACORPORATION INFLUENCE
-- =============================================================================

function update_megacorp_stats(tick)
    for name, corp in pairs(Megacorps) do
        -- Corps grow or shrink based on market conditions
        local seed = name .. "_growth_" .. tick
        local growth = (hash_to_number(seed, 100) - 50) / 1000  -- -5% to +5%
        
        corp.market_share = clamp(corp.market_share + growth, 0.1, 0.9)
        corp.employees = math.floor(corp.employees * (1 + growth))
    end
end

function get_sector_jobs(sector)
    local corp_jobs = 0
    for _, corp in pairs(Megacorps) do
        if corp.sector == sector then
            corp_jobs = corp_jobs + corp.employees
        end
    end
    return corp_jobs
end

-- =============================================================================
-- ECONOMIC EVENTS
-- =============================================================================

function check_economic_events(tick)
    local events_triggered = {}
    
    -- Check for recession
    if EconomicIndicators.gdp_growth < -0.02 then
        if not has_active_event("recession") then
            trigger_economic_event("recession", tick, 90)
            table.insert(events_triggered, "recession")
        end
    end
    
    -- Check for boom
    if EconomicIndicators.gdp_growth > 0.05 then
        if not has_active_event("boom") then
            trigger_economic_event("boom", tick, 60)
            table.insert(events_triggered, "boom")
        end
    end
    
    -- Random events (deterministic)
    local seed = "random_event_" .. tick
    local roll = hash_to_number(seed, 10000)
    
    if roll < 5 then  -- 0.05% chance
        trigger_economic_event("supply_shortage", tick, 14)
        table.insert(events_triggered, "supply_shortage")
    elseif roll < 10 then  -- 0.05% chance
        trigger_economic_event("corp_merger", tick, 1)
        table.insert(events_triggered, "corp_merger")
    end
    
    return events_triggered
end

function has_active_event(event_type)
    for _, event in ipairs(ActiveEconomicEvents) do
        if event.type == event_type then return true end
    end
    return false
end

function trigger_economic_event(event_type, tick, duration_days)
    local event_effects = {
        recession = {
            unemployment_delta = 0.05,
            wage_modifier = -0.1,
            crime_modifier = 0.1
        },
        boom = {
            wage_modifier = 0.1,
            land_value_modifier = 0.15,
            inflation_delta = 0.02
        },
        supply_shortage = {
            price_modifier = 0.5,
            unrest_modifier = 0.2
        },
        corp_merger = {
            job_loss = 2000,
            market_concentration = 0.05
        },
        automation_wave = {
            low_skill_jobs_delta = -0.1,
            productivity_modifier = 0.15
        }
    }
    
    local effects = event_effects[event_type]
    if effects then
        table.insert(ActiveEconomicEvents, {
            type = event_type,
            start_tick = tick,
            end_tick = tick + (duration_days * 240),
            effects = effects
        })
        
        -- Apply immediate effects
        if effects.unemployment_delta then
            EconomicIndicators.unemployment_rate = clamp(
                EconomicIndicators.unemployment_rate + effects.unemployment_delta,
                0.01, 0.50
            )
        end
        if effects.inflation_delta then
            EconomicIndicators.inflation = clamp(
                EconomicIndicators.inflation + effects.inflation_delta,
                -0.05, 0.20
            )
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
            -- Revert effects on expiry
            if event.type == "recession" then
                EconomicIndicators.unemployment_rate = clamp(
                    EconomicIndicators.unemployment_rate - 0.03,
                    0.05, 0.50
                )
            end
        end
    end
    
    ActiveEconomicEvents = still_active
end

-- =============================================================================
-- BLACK MARKET
-- =============================================================================

function update_black_market(tick, formal_gdp)
    -- Black market grows when formal economy struggles
    local base_share = 0.20
    
    -- Higher unemployment = larger black market
    local unemployment_factor = EconomicIndicators.unemployment_rate * 0.5
    
    -- Lower service levels = larger black market
    local service_factor = 0
    for _, level in pairs(ServiceLevels) do
        service_factor = service_factor + (1 - level)
    end
    service_factor = service_factor / 6 * 0.3
    
    EconomicIndicators.black_market_share = clamp(
        base_share + unemployment_factor + service_factor,
        0.10, 0.50
    )
    
    BlackMarket.estimated_gdp = math.floor(formal_gdp * EconomicIndicators.black_market_share)
end

-- =============================================================================
-- WEALTH DISTRIBUTION
-- =============================================================================

function update_wealth_distribution(tick)
    -- Gini coefficient changes slowly based on policies and events
    local base_gini = 0.72  -- RE:ECHO is highly unequal
    
    -- Progressive taxes reduce inequality
    local tax_effect = -0.02  -- Mild reduction
    
    -- Economic events affect inequality
    for _, event in ipairs(ActiveEconomicEvents) do
        if event.type == "recession" then
            base_gini = base_gini + 0.02  -- Recessions increase inequality
        elseif event.type == "boom" then
            base_gini = base_gini - 0.01  -- Booms help slightly
        end
    end
    
    EconomicIndicators.gini_coefficient = clamp(base_gini + tax_effect, 0.3, 0.9)
    
    -- Update wealth class distribution based on Gini
    -- Higher Gini = more at extremes
    local inequality_factor = EconomicIndicators.gini_coefficient
    WealthDistribution.destitute = 0.10 + (inequality_factor * 0.1)
    WealthDistribution.poor = 0.25 + (inequality_factor * 0.1)
    WealthDistribution.working = 0.40 - (inequality_factor * 0.1)
    WealthDistribution.comfortable = 0.15 - (inequality_factor * 0.05)
    WealthDistribution.wealthy = 0.07
    WealthDistribution.elite = 0.03
end

-- =============================================================================
-- LOGGING
-- =============================================================================

function log_transaction(tx_type, tick, data)
    table.insert(TransactionLog, {
        type = tx_type,
        tick = tick,
        timestamp = tick,
        data = data
    })
    
    -- Keep last 1000 transactions
    while #TransactionLog > 1000 do
        table.remove(TransactionLog, 1)
    end
end

-- =============================================================================
-- HANDLERS
-- =============================================================================

-- Initialize economy with configuration
Handlers.add("init", Handlers.utils.hasMatchingTag("Action", "Init"), function(msg)
    local data = json.decode(msg.Data) or {}
    
    if data.initial_budget then CityBudget = data.initial_budget end
    if data.tax_config then TaxConfig = data.tax_config end
    if data.budget_allocation then BudgetAllocation = data.budget_allocation end
    if data.ubi_amount then UBI.amount = data.ubi_amount end
    
    ao.send({
        Target = msg.From,
        Action = "init-complete",
        Data = json.encode({
            budget = CityBudget,
            tax_config = TaxConfig,
            ubi = UBI
        })
    })
end)

-- CRON: Daily economy processing
Handlers.add("cron-economy", Handlers.utils.hasMatchingTag("Action", "Cron"), function(msg)
    local data = json.decode(msg.Data) or {}
    local tick = data.tick or 0
    
    -- Only process on day boundaries (every 240 ticks)
    if tick % 240 ~= 0 then return end
    
    local population = data.population or 10000
    local tax_revenue = data.tax_revenue or 0
    
    -- 1. Update employment stats
    update_employment_stats(population)
    
    -- 2. Update production chains
    update_production_chains(tick)
    
    -- 3. Update megacorp stats
    update_megacorp_stats(tick)
    
    -- 4. Check for economic events
    local new_events = check_economic_events(tick)
    update_economic_events(tick)
    
    -- 5. Pay city expenses
    local success, expenses, crisis = pay_city_expenses(tick, population, tax_revenue)
    
    -- 6. Update GDP
    local formal_gdp = population * 75 * (1 + EconomicIndicators.gdp_growth)
    EconomicIndicators.gdp = math.floor(formal_gdp)
    
    -- 7. Update black market
    update_black_market(tick, formal_gdp)
    
    -- 8. Update wealth distribution
    update_wealth_distribution(tick)
    
    -- 9. Broadcast economy update
    ao.send({
        Target = ao.id,
        Action = "economy-update",
        Data = json.encode({
            tick = tick,
            budget = CityBudget,
            crisis_level = crisis,
            indicators = EconomicIndicators,
            employment = Employment,
            events = new_events,
            service_levels = ServiceLevels
        })
    })
end)

-- Query full economy state
Handlers.add("get-economy", Handlers.utils.hasMatchingTag("Action", "get-economy"), function(msg)
    ao.send({
        Target = msg.From,
        Action = "economy-response",
        Data = json.encode({
            budget = CityBudget,
            reserve_target = ReserveTarget,
            crisis_level = get_crisis_level(),
            indicators = EconomicIndicators,
            tax_config = TaxConfig,
            budget_allocation = BudgetAllocation,
            service_levels = ServiceLevels,
            employment = Employment,
            wealth_distribution = WealthDistribution,
            megacorps = Megacorps,
            black_market = BlackMarket,
            active_events = ActiveEconomicEvents,
            ubi = UBI
        })
    })
end)

-- Calculate tax for an NPC
Handlers.add("calculate-tax", Handlers.utils.hasMatchingTag("Action", "calculate-tax"), function(msg)
    local data = json.decode(msg.Data)
    
    local income_tax = calculate_income_tax(data.income or 0)
    local property_tax = calculate_property_tax(data.land_value or 0)
    local temple_tithe = calculate_temple_tithe(data.income or 0)
    
    local total = income_tax + property_tax + temple_tithe
    
    ao.send({
        Target = msg.From,
        Action = "tax-calculated",
        Data = json.encode({
            income_tax = income_tax,
            property_tax = property_tax,
            temple_tithe = temple_tithe,
            total = total
        })
    })
end)

-- Receive tax deposit from district
Handlers.add("tax-deposit", Handlers.utils.hasMatchingTag("Action", "tax-deposit"), function(msg)
    local data = json.decode(msg.Data)
    local amount = data.amount or 0
    local source = data.source or "unknown"
    
    CityBudget = CityBudget + amount
    TotalTaxRevenue = TotalTaxRevenue + amount
    
    log_transaction("tax_deposit", data.tick, {
        amount = amount,
        source = source,
        new_budget = CityBudget
    })
    
    ao.send({
        Target = msg.From,
        Action = "tax-received",
        Data = json.encode({ new_budget = CityBudget })
    })
end)

-- Record a trade/transaction
Handlers.add("record-trade", Handlers.utils.hasMatchingTag("Action", "record-trade"), function(msg)
    local data = json.decode(msg.Data)
    local amount = data.amount or 0
    local is_exempt = data.exempt or false
    local is_black_market = data.black_market or false
    
    local sales_tax = 0
    if not is_black_market then
        sales_tax = calculate_sales_tax(amount, is_exempt)
        CityBudget = CityBudget + sales_tax
        TotalTaxRevenue = TotalTaxRevenue + sales_tax
    end
    
    log_transaction("trade", data.tick, {
        amount = amount,
        tax = sales_tax,
        black_market = is_black_market
    })
    
    ao.send({
        Target = msg.From,
        Action = "trade-recorded",
        Data = json.encode({ tax_collected = sales_tax })
    })
end)

-- Trigger economic event (admin)
Handlers.add("trigger-event", Handlers.utils.hasMatchingTag("Action", "trigger-event"), function(msg)
    local data = json.decode(msg.Data)
    local success = trigger_economic_event(
        data.event_type,
        data.tick or 0,
        data.duration_days or 7
    )
    
    ao.send({
        Target = msg.From,
        Action = "event-triggered",
        Data = json.encode({
            success = success,
            active_events = ActiveEconomicEvents
        })
    })
end)

-- Adjust budget allocation
Handlers.add("set-budget-allocation", Handlers.utils.hasMatchingTag("Action", "set-budget-allocation"), function(msg)
    local data = json.decode(msg.Data)
    
    if data.allocations then
        for category, percentage in pairs(data.allocations) do
            if BudgetAllocation[category] then
                BudgetAllocation[category] = clamp(percentage, 0.01, 0.50)
            end
        end
    end
    
    ao.send({
        Target = msg.From,
        Action = "allocation-updated",
        Data = json.encode({ budget_allocation = BudgetAllocation })
    })
end)

-- Get NPC income based on job
Handlers.add("get-npc-income", Handlers.utils.hasMatchingTag("Action", "get-npc-income"), function(msg)
    local data = json.decode(msg.Data)
    local income = calculate_npc_income(
        data.job_code or "JOB0000",
        data.skill_level or "low_skill",
        data.tick or 0
    )
    
    ao.send({
        Target = msg.From,
        Action = "npc-income",
        Data = json.encode({ income = income })
    })
end)

-- =============================================================================
-- CODEC CALLBACKS
-- =============================================================================

-- When codec_20_economy is loaded, extract config
codec.on("economy", function(data)
    if data.taxation then
        TaxConfig = codec.deep_merge(TaxConfig, data.taxation)
    end
    if data.land_value and data.land_value.base_factors and data.land_value.base_factors.zone_type_multiplier then
        ZONE_MULTIPLIERS = codec.deep_merge(ZONE_MULTIPLIERS, data.land_value.base_factors.zone_type_multiplier)
    end
    if data.wages then
        WAGE_RANGES = codec.deep_merge(WAGE_RANGES, data.wages)
    end
    if data.megacorporations then
        Megacorps = codec.deep_merge(Megacorps, data.megacorporations)
    end
    if data.zoning then
        Zones = codec.deep_merge(Zones, data.zoning)
    end
end)

-- When codec_27_city_finance is loaded, extract budget allocation
codec.on("city_finance", function(data)
    if data.city_finance and data.city_finance.budget_allocation then
        BudgetAllocation = codec.deep_merge(BudgetAllocation, data.city_finance.budget_allocation)
    end
    if data.city_finance and data.city_finance.ubi then
        UBI = codec.deep_merge(UBI, data.city_finance.ubi)
    end
end)

-- When codec_35_trade_diplomacy is loaded, extract price volatility
codec.on("trade_diplomacy", function(data)
    if data.trade_system and data.trade_system.price_volatility then
        PRICE_VOLATILITY = codec.deep_merge(PRICE_VOLATILITY, data.trade_system.price_volatility)
    end
end)

-- Register standard LoadCodec handler
codec.register_handler()

-- =============================================================================
-- MODULE EXPORT
-- =============================================================================

return {
    calculate_income_tax = calculate_income_tax,
    calculate_property_tax = calculate_property_tax,
    calculate_sales_tax = calculate_sales_tax,
    calculate_land_value = calculate_land_value,
    calculate_npc_income = calculate_npc_income,
    trigger_economic_event = trigger_economic_event,
    get_crisis_level = get_crisis_level,
    -- Codec-backed config
    TaxConfig = TaxConfig,
    ZONE_MULTIPLIERS = ZONE_MULTIPLIERS,
    WAGE_RANGES = WAGE_RANGES,
    PRICE_VOLATILITY = PRICE_VOLATILITY
}
