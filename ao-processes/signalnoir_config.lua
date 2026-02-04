--[[
  SignalNoir.1 - Test Configuration
  
  First live test of the AO World Engine autonomous simulation.
  Deploy with: aos SignalNoir1 --load signalnoir_config.lua --cron 1-minute
]]--

local json = json or require("json")

-- =============================================================================
-- WORLD IDENTITY
-- =============================================================================

WORLD_NAME = "SignalNoir.1"
WORLD_VERSION = "0.1.0-alpha"
WORLD_DESCRIPTION = "First live test - autonomous city simulation on AO"
WORLD_FORK_ID = "signalnoir_test_001"

-- =============================================================================
-- TIME CONFIGURATION
-- =============================================================================

-- Time compression: 10x speed (1 real minute = 10 game minutes)
TIME_COMPRESSION = 10

-- Tick timing
TICKS_PER_HOUR = 10           -- 10 ticks per in-game hour
TICKS_PER_DAY = 240           -- 24 in-game hours
TICKS_PER_YEAR = 87600        -- 365 days

-- Starting state
START_TICK = 0
START_DAY = 1
START_YEAR = 2087             -- RE:ECHO timeline
START_TIME_PERIOD = "T01"     -- Dawn

-- =============================================================================
-- FOUNDING NPCS (12 from Arweave)
-- =============================================================================

FOUNDING_NPCS = {
    {
        id = "C01",
        arweave_tx = "splQGmMK8Din4l3apKcIbyX3R_OEqG4L3WlRhzan9X4",
        name = "Charlie",
        role = "detective",
        job_code = "JOB0222",
        district = "neon_district",
        home = "L026",
        archetype = "ARCH001"
    },
    {
        id = "C02",
        arweave_tx = "Y4OkevLSSgLGhOT7QFKFNsT59rW8_m_rLBdiSCA-tJ4",
        name = "Kai Vance",
        role = "tech_specialist",
        job_code = "JOB0301",
        district = "neon_district",
        home = "L004",
        archetype = "ARCH003"
    },
    {
        id = "C03",
        arweave_tx = "PIYlaUAKk44yCvX2cNTU8rowB2wfcQSqGY_EkvJmXfk",
        name = "Orion Thane",
        role = "bartender",
        job_code = "JOB0400",
        district = "neon_district",
        workplace = "L003",
        archetype = "ARCH002"
    },
    {
        id = "C04",
        arweave_tx = "BVyyBUHRX-_L0fCR9uLrrzIdC3RxMoyhHCPBq2kicjI",
        name = "Felix",
        role = "street_vendor",
        job_code = "JOB0412",
        district = "neon_district",
        archetype = "ARCH001"
    },
    {
        id = "C05",
        arweave_tx = "xgHlkq0PtCOBhx5SKNsLHAY-kfpFLThSbxXJEA5HFl0",
        name = "Nova Chen",
        role = "street_medic",
        job_code = "JOB0102",
        district = "temple_quarter",
        archetype = "ARCH003"
    },
    {
        id = "C06",
        arweave_tx = "Ad-A1Ww3wN79ZFYLexzmucl7N3tTvRKR1h58ca-omFI",
        name = "Selene Voss",
        role = "smuggler",
        job_code = "JOB0500",
        district = "undercity",
        archetype = "ARCH004"
    },
    {
        id = "C07",
        arweave_tx = "rAFAlFK6Zp9nyiL1Ebj1iHEbAe8cMWtgp2DPxyf4Opo",
        name = "Sister Mira",
        role = "temple_priest",
        job_code = "JOB0600",
        district = "temple_quarter",
        faction = "temple",
        archetype = "ARCH006"
    },
    {
        id = "C08",
        arweave_tx = "ojQnWrkCax2TyY-gBvned-0ibF-40P3yI0wl32QJU_A",
        name = "Mama Indira",
        role = "shop_owner",
        job_code = "JOB0401",
        district = "neon_district",
        archetype = "ARCH001"
    },
    {
        id = "C09",
        arweave_tx = "5traiA6R0JU0cFQXJcqqkNm64o7hcYLsW_7rugnwxvo",
        name = "Aiche",
        role = "ai_companion",
        job_code = nil,
        district = "neon_district",
        archetype = "ARCH005"
    },
    {
        id = "C10",
        arweave_tx = "-GVQ7zmPfs3C1B1HblfupvzHMgvoVVyiXNvq0hwCkmY",
        name = "Pixel",
        role = "hacker",
        job_code = "JOB0510",
        district = "undercity",
        archetype = "ARCH004"
    },
    {
        id = "C11",
        arweave_tx = "Hi61YpGfVNatwCVkv2yJB54sDEX1pX8iT9mD5k8Zyms",
        name = "Cipher",
        role = "info_broker",
        job_code = "JOB0512",
        district = "neon_district",
        archetype = "ARCH004"
    },
    {
        id = "C12",
        arweave_tx = "RT2GXhdYw1h5E1WC7PSN11ORfFF0nIiED5K6mF_fnQY",
        name = "Zero Chen",
        role = "journalist",
        job_code = "JOB0703",
        district = "temple_quarter",
        faction = "resistance",
        archetype = "ARCH004"
    }
}

-- =============================================================================
-- DISTRICTS
-- =============================================================================

DISTRICTS = {
    {
        id = "neon_district",
        name = "Neon District",
        zone = "ZONE_C1",
        population_cap = 5000,
        danger_level = 3,
        wealth_level = "working",
        buildings = { "L001", "L002", "L003", "L004", "L005" }
    },
    {
        id = "temple_quarter",
        name = "Temple Quarter",
        zone = "ZONE_R2",
        population_cap = 3000,
        danger_level = 2,
        wealth_level = "comfortable",
        faction = "temple",
        buildings = { "L031", "L032", "L033" }
    },
    {
        id = "undercity",
        name = "The Undercity",
        zone = "ZONE_U",
        population_cap = 8000,
        danger_level = 7,
        wealth_level = "poor",
        is_underground = true,
        buildings = { "L050", "L051", "L052" }
    }
}

-- =============================================================================
-- INITIAL ECONOMY
-- =============================================================================

INITIAL_ECONOMY = {
    city_budget = 100000,          -- GEP
    reserve_target = 20000,
    tax_rate = 0.12,              -- 12% base
    ubi_enabled = true,
    ubi_amount = 30,              -- GEP per day for unemployed
    inflation_rate = 0.02,
    black_market_share = 0.20
}

-- =============================================================================
-- TEST PARAMETERS
-- =============================================================================

TEST_CONFIG = {
    -- Phase 1: 12 NPCs
    phase1_duration_hours = 1,     -- Real-time hours
    phase1_npc_count = 12,
    
    -- Phase 2: Scale to 100 NPCs
    phase2_enabled = false,        -- Manual trigger
    phase2_npc_count = 100,
    
    -- Logging
    log_every_tick = true,
    log_all_movements = true,
    log_all_meetings = true,
    log_all_transactions = true,
    
    -- Snapshots
    snapshot_interval_ticks = 60,  -- Every hour in-game
    
    -- Validation checks
    validate_economy = true,
    validate_social = true,
    validate_schedules = true
}

-- =============================================================================
-- INITIALIZATION FUNCTION
-- =============================================================================

function InitializeSignalNoir()
    print("╔═══════════════════════════════════════════╗")
    print("║       SignalNoir.1 - Initializing         ║")
    print("╠═══════════════════════════════════════════╣")
    print("║  World: " .. WORLD_NAME)
    print("║  Version: " .. WORLD_VERSION)
    print("║  NPCs: " .. #FOUNDING_NPCS)
    print("║  Districts: " .. #DISTRICTS)
    print("║  Time Compression: " .. TIME_COMPRESSION .. "x")
    print("╚═══════════════════════════════════════════╝")
    
    -- Set global state
    WorldTick = START_TICK
    WorldDay = START_DAY
    WorldYear = START_YEAR
    CityBudget = INITIAL_ECONOMY.city_budget
    
    -- Initialize NPC registry
    NPCs = {}
    for _, npc in ipairs(FOUNDING_NPCS) do
        NPCs[npc.id] = {
            id = npc.id,
            name = npc.name,
            role = npc.role,
            job_code = npc.job_code,
            district = npc.district,
            arweave_tx = npc.arweave_tx,
            state = "idle",
            location = npc.home or npc.workplace or "L001",
            mood = 0.5,
            energy = 1.0,
            wealth = 100,
            initialized_at = 0
        }
    end
    
    -- Initialize district registry
    DistrictRegistry = {}
    for _, district in ipairs(DISTRICTS) do
        DistrictRegistry[district.id] = district
    end
    
    -- Log initialization
    if log_world_event then
        log_world_event(0, "initialization", "SignalNoir.1 Started", 
            { npc_count = #FOUNDING_NPCS, district_count = #DISTRICTS },
            { economy = INITIAL_ECONOMY, config = TEST_CONFIG }
        )
    end
    
    print("[SignalNoir.1] ✓ Initialized with " .. #FOUNDING_NPCS .. " NPCs")
    print("[SignalNoir.1] ✓ Budget: " .. CityBudget .. " GEP")
    print("[SignalNoir.1] ⏱ Waiting for CRON tick...")
    
    return {
        success = true,
        world_name = WORLD_NAME,
        npc_count = #FOUNDING_NPCS,
        district_count = #DISTRICTS,
        budget = CityBudget
    }
end

-- =============================================================================
-- STATUS QUERY
-- =============================================================================

function GetSignalNoirStatus()
    local active_npcs = 0
    for id, npc in pairs(NPCs or {}) do
        if npc.state ~= "sleeping" then
            active_npcs = active_npcs + 1
        end
    end
    
    return {
        world_name = WORLD_NAME,
        version = WORLD_VERSION,
        tick = WorldTick or 0,
        day = WorldDay or 1,
        year = WorldYear or 2087,
        population = #FOUNDING_NPCS,
        active_npcs = active_npcs,
        budget = CityBudget or 0,
        districts = #DISTRICTS,
        uptime_ticks = WorldTick or 0
    }
end

-- =============================================================================
-- HANDLER: Get Status
-- =============================================================================

Handlers.add("get-signalnoir-status", 
    Handlers.utils.hasMatchingTag("Action", "get-signalnoir-status"), 
    function(msg)
        local status = GetSignalNoirStatus()
        
        ao.send({
            Target = msg.From,
            Action = "signalnoir-status",
            Data = json.encode(status)
        })
    end
)

-- =============================================================================
-- AUTO-INITIALIZE ON LOAD
-- =============================================================================

-- Run initialization when this file is loaded
local init_result = InitializeSignalNoir()

print("")
print("Ready. To check status: Send { Action = 'get-signalnoir-status' }")
print("")
