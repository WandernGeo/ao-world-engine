# Living World Tests (77 tests)

> **Updated:** 2026-02-05T07:20:00-05:00

Tests for the dynamic, breathing world simulation.

---

## World Simulation (9 tests)

| Test Name | What It Validates |
|-----------|------------------|
| Time Tracking Variables | WorldTick, WorldDay, WorldYear |
| Ticks Per Day | TICKS_PER_DAY = 240 |
| Time Periods | T01-T09 defined |
| Night Time Detection | is_night function |
| Simulation Status States | running, paused, frozen, terminated |
| Kill Switch System | Emergency shutdown |
| District Registration | Districts join simulation |
| CRON Tick Processing | Heartbeat loop |
| State Persistence | Checkpoint saving |

### Time System

```lua
TICKS_PER_DAY = 240       -- 6 min real-time = 1 game day
TICKS_PER_YEAR = 87600    -- 365 days
TICKS_PER_HOUR = 10       -- 10 ticks per hour

function get_time_info(tick)
    local day = math.floor(tick / TICKS_PER_DAY) + 1
    local tick_in_day = tick % TICKS_PER_DAY
    local hour = math.floor(tick_in_day / TICKS_PER_HOUR)
    local minute = (tick_in_day % TICKS_PER_HOUR) * 6
    
    return {
        day = day,
        hour = hour,
        minute = minute,
        period = get_period(hour),
        is_night = hour < 6 or hour >= 20
    }
end
```

---

## Time System (4 tests)

| Test Name | What It Validates |
|-----------|------------------|
| Time Info Function | get_time_info() exists |
| Hour Advancement | Hours tick correctly |
| Day Advancement | Days advance at TICKS_PER_DAY |
| Year Advancement | Years at TICKS_PER_YEAR |

---

## Event System (4 tests)

| Test Name | What It Validates |
|-----------|------------------|
| World Event Checking | check_world_events() |
| Event Broadcasting | broadcast_event() |
| Weather Events | Weather changes |
| Random City Events | Dynamic events fire |

### World Events

| Event Type | Trigger | Effect |
|------------|---------|--------|
| Market Peak | Economy threshold | Prices spike |
| Power Fluctuation | Random | District blackout |
| Protest | Faction tension | Street activity |
| Weather Change | Time-based | Behavior changes |
| Megacorp Announcement | Economy event | Market effects |

---

## District System (3 tests)

| Test Name | What It Validates |
|-----------|------------------|
| District Registration | Districts register |
| AO Handlers | District handlers |
| NPC Location Tracking | NPCs placed in districts |

### Districts

```lua
DISTRICTS = {
    "downtown",      -- Commercial hub
    "industrial",    -- Factories, production
    "residential_upper",  -- Wealthy housing
    "residential_lower",  -- Working class
    "undercity",     -- Underground
    "temple_district",  -- Religious zone
    "port",          -- Shipping, trade
    "tech_zone"      -- R&D, hackers
}
```

---

## Living World (11 tests)

| Test Name | What It Validates |
|-----------|------------------|
| Simulation Loop | Main loop runs |
| NPC Updates | NPCs tick each cycle |
| Economy Updates | Economy updates |
| Social Updates | Relationships update |
| Event Generation | Events fire |
| Day/Night Cycle | Time advances |
| Population Movement | NPCs move around |
| District Activity | Activity per zone |
| Traffic Patterns | Commute behavior |
| Weather Influence | Weather affects NPCs |
| News Spread | Information propagates |

---

## Procedural Generation (7 tests)

| Test Name | What It Validates |
|-----------|------------------|
| Name Generation | NPC names generated |
| Personality Generation | Traits generated |
| Backstory Generation | Histories created |
| Schedule Generation | Routines created |
| Relationship Generation | Links generated |
| Location Assignment | Placements created |
| Occupation Assignment | Jobs assigned |

---

## AI Intelligence (8 tests)

| Test Name | What It Validates |
|-----------|------------------|
| Decision Making | NPCs decide actions |
| Goal Setting | NPCs have goals |
| Plan Execution | NPCs follow plans |
| Adaptation | NPCs adapt to change |
| Memory | NPCs remember events |
| Learning | Behavior improves |
| Communication | NPCs talk |
| Cooperation | NPCs work together |

---

## Predictions (7 tests)

| Test Name | What It Validates |
|-----------|------------------|
| Schedule Prediction | Where NPC will be |
| Encounter Prediction | Who will meet |
| Faction Prediction | Faction changes |
| Economy Prediction | Market trends |
| Relationship Prediction | Trust changes |
| Event Prediction | Event likelihood |
| Outcome Prediction | Action results |

---

## News System (10 tests)

| Test Name | What It Validates |
|-----------|------------------|
| News Creation | News items created |
| News Types | 6 news categories |
| Propagation Logic | News spreads |
| Decay Logic | News expires |
| Bias Calculation | Source bias |
| Importance Weighting | Significance |
| Location Relevance | Local news |
| Faction Relevance | Faction news |
| Public vs Private | Info classification |
| Memory Duration | Retention time |

---

## Encounter System (10 tests)

| Test Name | What It Validates |
|-----------|------------------|
| Encounter Markers | Markers defined |
| Mission Generation | Missions created |
| Trigger Conditions | Triggers work |
| Location Influence | Zone matters |
| Time Influence | Time matters |
| Faction Influence | Faction matters |
| NPC Pairing | NPCs pair up |
| Outcome Calculation | Results computed |
| Reward System | Rewards given |
| Consequence Tracking | Effects tracked |

---

## Faction System (13 tests)

| Test Name | What It Validates |
|-----------|------------------|
| Resistance Faction | Protagonist faction |
| Temple Faction | Religious authority |
| Megacorp Faction | Corporate power |
| Undercity Faction | Underground |
| StreetGangs Faction | Criminal element |
| SpecialForces Faction | Military |
| Neutral Faction | No alignment |
| Territory Claims | Zone control |
| Rivalry System | Faction conflicts |
| Reputation Modifiers | Player standing |
| Membership Rules | Join conditions |
| Hierarchy Structure | Ranks/roles |
| Faction NPCs | Members listed |

---

*Part of the AO World Engine Test Suite*
