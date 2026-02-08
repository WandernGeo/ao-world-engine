-- ============================================================================
-- ECONOMY MODIFIER PLUGIN
-- Dynamic economic policies, subsidies, and market interventions
-- Plugin 3 of 3 for AO World Engine audit
-- ============================================================================

local EconMod = {}

-- Policy types
EconMod.POLICIES = {
    -- Tax policies
    tax_holiday      = { id = "P01", duration = 240 * 7,   budget_impact = -0.15, growth_impact = 0.03, approval_impact = 0.10 },
    luxury_tax       = { id = "P02", duration = 240 * 30,  budget_impact = 0.05,  growth_impact = -0.01, approval_impact = -0.05 },
    corporate_relief = { id = "P03", duration = 240 * 14,  budget_impact = -0.08, growth_impact = 0.02, approval_impact = -0.03 },

    -- Spending policies
    infrastructure   = { id = "P04", duration = 240 * 60,  budget_impact = -0.20, growth_impact = 0.04, approval_impact = 0.05 },
    education_boost  = { id = "P05", duration = 240 * 90,  budget_impact = -0.10, growth_impact = 0.02, approval_impact = 0.08 },
    military_buildup = { id = "P06", duration = 240 * 30,  budget_impact = -0.25, growth_impact = -0.02, approval_impact = -0.08 },

    -- Market interventions
    price_controls   = { id = "P07", duration = 240 * 14,  budget_impact = -0.05, growth_impact = -0.03, approval_impact = 0.05 },
    subsidy_food     = { id = "P08", duration = 240 * 30,  budget_impact = -0.08, growth_impact = 0.01, approval_impact = 0.12 },
    subsidy_housing  = { id = "P09", duration = 240 * 60,  budget_impact = -0.12, growth_impact = 0.01, approval_impact = 0.15 },

    -- Emergency measures
    austerity        = { id = "P10", duration = 240 * 30,  budget_impact = 0.20,  growth_impact = -0.05, approval_impact = -0.20 },
    stimulus         = { id = "P11", duration = 240 * 14,  budget_impact = -0.30, growth_impact = 0.06, approval_impact = 0.05 },
    ubi_increase     = { id = "P12", duration = 240 * 30,  budget_impact = -0.10, growth_impact = 0.01, approval_impact = 0.18 },
}

-- State
EconMod.State = {
    active_policies = {},      -- Currently active policies
    policy_history = {},       -- Past policies
    max_history = 100,
    public_approval = 0.50,    -- 0-1 approval rating
    corruption_index = 0.30,   -- 0-1, higher = more corrupt (RE:ECHO noir)
    subsidy_pool = 0,          -- Available subsidy funds
    market_interventions = {}, -- Active price controls
    economic_zones = {},       -- Special economic zones
    total_policies_enacted = 0
}

-- Initialize
function EconMod.init()
    EconMod.State.active_policies = {}
    EconMod.State.public_approval = 0.50
    EconMod.State.corruption_index = 0.30
end

-- Enact a policy
function EconMod.enact_policy(policy_name, tick, params)
    local policy_template = EconMod.POLICIES[policy_name]
    if not policy_template then
        return { success = false, reason = "unknown_policy" }
    end

    -- Check for conflicting policies
    for _, active in ipairs(EconMod.State.active_policies) do
        if active.name == policy_name then
            return { success = false, reason = "already_active" }
        end
    end

    -- Max 3 active policies
    if #EconMod.State.active_policies >= 3 then
        return { success = false, reason = "max_policies_reached" }
    end

    local policy = {
        name = policy_name,
        id = policy_template.id,
        start_tick = tick,
        end_tick = tick + policy_template.duration,
        budget_impact = policy_template.budget_impact,
        growth_impact = policy_template.growth_impact,
        approval_impact = policy_template.approval_impact,
        params = params or {},
        ticks_active = 0
    }

    table.insert(EconMod.State.active_policies, policy)
    EconMod.State.total_policies_enacted = EconMod.State.total_policies_enacted + 1

    -- Immediate approval impact
    EconMod.State.public_approval = math.max(0, math.min(1.0,
        EconMod.State.public_approval + policy_template.approval_impact * 0.5
    ))

    return {
        success = true,
        policy = policy,
        approval = EconMod.State.public_approval
    }
end

-- Revoke a policy early
function EconMod.revoke_policy(policy_name, tick)
    for i, policy in ipairs(EconMod.State.active_policies) do
        if policy.name == policy_name then
            policy.end_tick = tick
            policy.revoked = true

            -- Move to history
            table.insert(EconMod.State.policy_history, policy)
            table.remove(EconMod.State.active_policies, i)

            -- Approval hit for inconsistency
            EconMod.State.public_approval = math.max(0,
                EconMod.State.public_approval - 0.05
            )

            -- Trim history
            while #EconMod.State.policy_history > EconMod.State.max_history do
                table.remove(EconMod.State.policy_history, 1)
            end

            return { success = true, revoked = policy_name }
        end
    end

    return { success = false, reason = "policy_not_found" }
end

-- Process tick - apply ongoing policy effects
function EconMod.on_tick(tick, economy_state)
    local modifiers = {
        budget_modifier = 0,
        growth_modifier = 0,
        approval_delta = 0,
        expired_policies = {}
    }

    local still_active = {}

    for _, policy in ipairs(EconMod.State.active_policies) do
        if tick < policy.end_tick then
            policy.ticks_active = policy.ticks_active + 1

            -- Gradual effects (applied per tick, scaled to daily impact)
            local daily_scale = 1 / 240  -- Convert daily impacts to per-tick
            modifiers.budget_modifier = modifiers.budget_modifier + (policy.budget_impact * daily_scale)
            modifiers.growth_modifier = modifiers.growth_modifier + (policy.growth_impact * daily_scale)

            -- Approval drifts slowly
            local approval_drift = policy.approval_impact * 0.001  -- Very slow
            modifiers.approval_delta = modifiers.approval_delta + approval_drift

            table.insert(still_active, policy)
        else
            -- Policy expired
            table.insert(modifiers.expired_policies, policy.name)
            table.insert(EconMod.State.policy_history, policy)
        end
    end

    EconMod.State.active_policies = still_active

    -- Apply approval changes
    EconMod.State.public_approval = math.max(0, math.min(1.0,
        EconMod.State.public_approval + modifiers.approval_delta
    ))

    -- Corruption slowly increases (RE:ECHO noir theme)
    if tick % 240 == 0 then
        local corruption_drift = 0.001
        -- Anti-corruption policies would reduce this
        for _, policy in ipairs(EconMod.State.active_policies) do
            if policy.name == "education_boost" then
                corruption_drift = corruption_drift - 0.002
            end
        end
        EconMod.State.corruption_index = math.max(0, math.min(0.9,
            EconMod.State.corruption_index + corruption_drift
        ))
    end

    -- Corruption siphons budget
    if EconMod.State.corruption_index > 0.5 then
        local siphon = (EconMod.State.corruption_index - 0.5) * 0.001
        modifiers.budget_modifier = modifiers.budget_modifier - siphon
    end

    -- Trim history
    while #EconMod.State.policy_history > EconMod.State.max_history do
        table.remove(EconMod.State.policy_history, 1)
    end

    return modifiers
end

-- Create a special economic zone
function EconMod.create_economic_zone(zone_name, district, bonuses, tick)
    local zone = {
        name = zone_name,
        district = district,
        created_tick = tick,
        bonuses = bonuses or {
            tax_reduction = 0.5,      -- 50% tax reduction
            growth_bonus = 0.10,      -- 10% growth bonus
            employment_bonus = 0.05   -- 5% more jobs
        },
        active = true
    }

    EconMod.State.economic_zones[zone_name] = zone
    return zone
end

-- Get economic modifiers for a district (considering zones)
function EconMod.get_district_modifiers(district)
    local modifiers = { tax = 1.0, growth = 1.0, employment = 1.0 }

    for _, zone in pairs(EconMod.State.economic_zones) do
        if zone.active and zone.district == district then
            modifiers.tax = modifiers.tax - (zone.bonuses.tax_reduction or 0)
            modifiers.growth = modifiers.growth + (zone.bonuses.growth_bonus or 0)
            modifiers.employment = modifiers.employment + (zone.bonuses.employment_bonus or 0)
        end
    end

    return modifiers
end

-- Get full state for API
function EconMod.get_state()
    return {
        active_policies = EconMod.State.active_policies,
        public_approval = EconMod.State.public_approval,
        corruption_index = EconMod.State.corruption_index,
        economic_zones = EconMod.State.economic_zones,
        total_enacted = EconMod.State.total_policies_enacted,
        history_count = #EconMod.State.policy_history
    }
end

-- Export module
return EconMod
