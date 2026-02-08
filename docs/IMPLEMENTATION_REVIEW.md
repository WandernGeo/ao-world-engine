# AO World Engine — Game Mechanics Implementation Review

> Cross-referencing CS2, Workers & Resources, Dwarf Fortress, ONI, and CS1 mechanics
> against existing AO engine architecture to identify concrete enhancements.

---

## Existing AO Engine Architecture Summary

| Layer | File(s) | Current Capability |
|-------|---------|--------------------|
| **Needs System** | `agent_needs.lua`, `world_codec_26_utility_ai.json` | 7 needs (hunger, energy, social, safety, entertainment, hygiene, purpose), decay per tick, mood calculation |
| **Scheduling** | `district.lua` | Hash-based deterministic location, archetype routines (merchant/guard/informant), time-slot schedules |
| **Decision Engine** | `district.lua`, `agent_needs.lua` | Utility AI with 14 actions, archetype curves, schedule overrides when need delta > 50 |
| **Behaviors** | `world_codec_14_behaviors.json` | 6 archetypes (shopkeeper/bartender/guard/street_vendor/medic/civilian), personality bases, dialogue templates |
| **City Services** | `city_services.lua`, `world_codec_28_city_services.json` | 12 service types, budget efficiency, service fees, incident generation |
| **Economy** | `economy.lua`, `world_codec_15_economy.json`, `world_codec_20_economy.json` | Resource tracking, trade mechanics |
| **Districts** | `world_codec_25_district_demographics.json` | 8 districts with demographic profiles |

---

## 1. COMMUTING & TRAVEL COSTS

### What the games teach us

| Game | Mechanic | Key Numbers |
|------|----------|-------------|
| **Workers & Resources** | Walking radius 250–411m, 4h max commute, happiness penalty >5h | 3x workers for 24/7 coverage |
| **CS2** | Time/Comfort/Money/Behavior route factors, age-specific priorities | Teens=Money, Adults=Time, Seniors=Comfort |
| **CS1** | Multi-modal pathfinding (walk→bus→metro), agent cap, teleport fallback | 4 updates/sec, no lane changing |
| **Dwarf Fortress** | A* with traffic designations, Manhattan metric for materials | Restricted/High/Low traffic costs |

### AO Implementation

#### New codec: `world_codec_29_commuting.json`

```json
{
  "commuting": {
    "travel_cost_formula": "{district_distance} * {traffic_weight} + {mode_cost}",
    "modes": {
      "walk":    { "code": "CM001", "speed": 1.0, "cost": 0, "max_distance": 3 },
      "bike":    { "code": "CM002", "speed": 2.5, "cost": 5, "max_distance": 8 },
      "bus":     { "code": "CM003", "speed": 4.0, "cost": 15, "max_distance": 20 },
      "metro":   { "code": "CM004", "speed": 8.0, "cost": 25, "max_distance": 50 },
      "car":     { "code": "CM005", "speed": 6.0, "cost": 40, "max_distance": 30 },
      "taxi":    { "code": "CM006", "speed": 6.0, "cost": 80, "max_distance": 30 }
    },
    "commute_happiness_curve": {
      "0-2_ticks":  { "modifier": 0.0, "description": "Short commute, no penalty" },
      "3-4_ticks":  { "modifier": -0.05, "description": "Moderate commute" },
      "5-6_ticks":  { "modifier": -0.15, "description": "Long commute, noticeable stress" },
      "7+_ticks":   { "modifier": -0.30, "description": "Brutal commute, major unhappiness" }
    },
    "district_traffic_weights": {
      "_desc": "Dwarf Fortress-inspired traffic designations per district",
      "harbor":     { "weight": 1.2, "reason": "heavy cargo traffic" },
      "downtown":   { "weight": 1.5, "reason": "congestion, pedestrian priority" },
      "industrial": { "weight": 1.3, "reason": "freight corridors" },
      "residential":{ "weight": 0.8, "reason": "quiet streets" },
      "park":       { "weight": 0.6, "reason": "pedestrian zone" }
    },
    "age_route_preference": {
      "_desc": "CS2-style age-based route selection",
      "child":  { "primary": "comfort", "weight": { "time": 0.2, "cost": 0.1, "comfort": 0.7 }},
      "teen":   { "primary": "cost",    "weight": { "time": 0.3, "cost": 0.6, "comfort": 0.1 }},
      "adult":  { "primary": "time",    "weight": { "time": 0.6, "cost": 0.3, "comfort": 0.1 }},
      "senior": { "primary": "comfort", "weight": { "time": 0.1, "cost": 0.2, "comfort": 0.7 }}
    }
  }
}
```

#### Lua enhancement: `district.lua` — add commute cost to `calculate_npc_location()`

```lua
function calculate_commute_cost(npc_id, from_district, to_district, tick)
  local npc = NPCs[npc_id]
  local distance = DISTRICT_DISTANCES[from_district][to_district] or 5
  local traffic = DISTRICT_TRAFFIC[to_district] or 1.0
  
  -- Age-based preference (CS2 style)
  local age_pref = AGE_PREFERENCES[npc.age_group] or AGE_PREFERENCES.adult
  
  -- Select mode deterministically based on NPC hash + wealth
  local mode_seed = hash_to_number(npc_id .. "_mode_" .. tick, 100)
  local mode = select_transport_mode(npc, distance, mode_seed)
  
  local time_cost = distance / MODES[mode].speed * traffic
  local money_cost = MODES[mode].cost
  
  -- Weighted cost (CS2: Time/Money/Comfort factors)
  local total = (time_cost * age_pref.time) + 
                (money_cost * age_pref.cost) + 
                ((1.0 - MODES[mode].comfort) * age_pref.comfort)
  
  -- Happiness impact (Workers & Resources: penalty for >5h commute)
  local happiness_penalty = 0
  if time_cost > 6 then happiness_penalty = -0.30
  elseif time_cost > 4 then happiness_penalty = -0.15
  elseif time_cost > 2 then happiness_penalty = -0.05
  end
  
  return {
    mode = mode,
    time_cost = time_cost,
    money_cost = money_cost,
    total_cost = total,
    happiness_penalty = happiness_penalty
  }
end
```

---

## 2. PRIORITY-BASED TASK SELECTION

### What the games teach us

| Game | Mechanic | Key Numbers |
|------|----------|-------------|
| **ONI** | 5 category levels (Very High → Disabled), sub-priority 1–9, hidden priority vs proximity | Personal needs always override |
| **Dwarf Fortress** | Nearest valid material, Manhattan metric, workshop stockpile linking | Jobs picked by proximity to task |
| **CS2** | Company job complexity matches education level, efficiency loss on mismatch | 5 education tiers |

### AO Implementation

#### Enhance: `world_codec_26_utility_ai.json` — add priority tiers

```json
{
  "priority_system": {
    "_desc": "ONI-inspired priority tiers for NPC task selection",
    "category_priorities": {
      "emergency":  { "level": 5, "label": "!!",  "overrides_schedule": true },
      "critical":   { "level": 4, "label": "↑↑",  "overrides_schedule": true },
      "high":       { "level": 3, "label": "↑",   "overrides_schedule": false },
      "normal":     { "level": 2, "label": "—",   "overrides_schedule": false },
      "low":        { "level": 1, "label": "↓",   "overrides_schedule": false },
      "disabled":   { "level": 0, "label": "✕",   "never_performed": true }
    },
    "personal_needs_always_override": true,
    "tie_breaking": {
      "small_population": "hidden_priority",
      "large_population": "proximity",
      "threshold": 500
    },
    "archetype_task_priorities": {
      "_desc": "Per-archetype default priorities (like ONI duplicant settings)",
      "guard":    { "patrol": 5, "fight": 5, "trade": 1, "socialize": 2, "eat": 3, "sleep": 3 },
      "merchant": { "trade": 5, "socialize": 4, "patrol": 0, "fight": 1, "eat": 3, "sleep": 3 },
      "medic":    { "seek_medical": 5, "socialize": 3, "patrol": 0, "fight": 0, "eat": 3, "sleep": 3 },
      "civilian": { "eat": 4, "sleep": 4, "socialize": 4, "trade": 2, "flee": 5, "fight": 1 }
    }
  }
}
```

#### Lua enhancement: `agent_needs.lua` — priority-weighted action selection

```lua
function decide_action_with_priority(npc_id, tick, context)
  local npc = NPCs[npc_id]
  local needs = get_npc_needs(npc_id)
  local priorities = ARCHETYPE_PRIORITIES[npc.archetype] or DEFAULT_PRIORITIES
  
  -- 1. Personal needs always override (ONI rule)
  if needs.hunger < 15 then return { action = "eat", priority = 5, reason = "starving" } end
  if needs.energy < 10 then return { action = "sleep", priority = 5, reason = "exhausted" } end
  
  -- 2. Score all actions with priority weighting
  local candidates = {}
  for action_name, action_config in pairs(UTILITY_ACTIONS) do
    local archetype_priority = priorities[action_name] or 2
    if archetype_priority > 0 then  -- 0 = disabled (ONI style)
      local base_score = evaluate_utility(action_config, needs, npc)
      local weighted_score = base_score * (archetype_priority / 3.0)
      table.insert(candidates, { 
        action = action_name, 
        score = weighted_score, 
        priority = archetype_priority 
      })
    end
  end
  
  -- 3. Sort by priority tier first, then score (ONI: category > sub-priority)
  table.sort(candidates, function(a, b)
    if a.priority ~= b.priority then return a.priority > b.priority end
    return a.score > b.score
  end)
  
  -- 4. Select from top-N using deterministic seed
  return select_weighted_random(candidates, npc_id, tick, 3)
end
```

---

## 3. DYNAMIC METRICS THAT CHANGE OVER TIME

### What the games teach us

| Game | Mechanic | Key Dynamic |
|------|----------|-------------|
| **CS2** | Building levels up with services, taxes affect demand, budget 50-150% | Efficiency = f(budget, workers, service) |
| **Workers & Resources** | Productivity = f(happiness), 30% floor, loyalty from propaganda | Happiness decays without needs met |
| **CS2** | Crime probability per building, pollution spreads, land value shifts | All metrics respond to service coverage |
| **ONI** | Attribute gain through use, stress from unmet needs | Skills improve with practice |

### AO Implementation

#### New codec: `world_codec_30_dynamic_metrics.json`

```json
{
  "dynamic_metrics": {
    "_desc": "Metrics that evolve each tick based on city state and NPC behavior",
    
    "npc_metrics": {
      "productivity": {
        "formula": "max(0.30, happiness * skill_match * health_factor)",
        "floor": 0.30,
        "ceiling": 1.20,
        "factors": {
          "happiness":    { "weight": 0.40, "source": "needs_satisfaction_avg" },
          "skill_match":  { "weight": 0.30, "source": "education_vs_job_complexity" },
          "health_factor":{ "weight": 0.20, "source": "health_need_value / 100" },
          "commute_stress":{"weight": 0.10, "source": "commute_happiness_penalty" }
        }
      },
      "crime_tendency": {
        "formula": "base_rate * (1.0 - wellbeing) * (1.0 - police_coverage) * unemployment_factor",
        "base_rate": 0.05,
        "modifiers": {
          "unemployment": "+0.15 if no job",
          "low_education": "+0.10 if uneducated",
          "police_nearby": "-0.20 per police building in district",
          "welfare_office": "-0.10 if district has welfare"
        }
      },
      "loyalty": {
        "formula": "base + service_satisfaction - grievances",
        "decay_rate": 0.01,
        "boosted_by": ["propaganda", "welfare", "entertainment", "employment"],
        "reduced_by": ["taxation_high", "pollution", "crime_victim", "service_shortage"]
      },
      "skill_growth": {
        "_desc": "ONI-style: attributes improve through use",
        "rate": 0.001,
        "formula": "current_skill + (rate * ticks_performing_action)",
        "cap": 1.0,
        "relevant_skills": {
          "trading":    { "improved_by": ["trade", "negotiate"], "affects": "trade_profit_margin" },
          "combat":     { "improved_by": ["fight", "patrol"],   "affects": "fight_success_rate" },
          "social":     { "improved_by": ["socialize", "gossip"],"affects": "information_quality" },
          "crafting":   { "improved_by": ["work_workshop"],     "affects": "product_quality" },
          "medical":    { "improved_by": ["heal", "diagnose"],  "affects": "treatment_efficacy" }
        }
      }
    },
    
    "district_metrics": {
      "land_value": {
        "formula": "base_value * service_coverage * (1.0 - pollution) * safety_factor",
        "update_frequency": "every_100_ticks",
        "factors": {
          "service_coverage": { "parks": 1.15, "healthcare": 1.10, "education": 1.10, "police": 1.05 },
          "pollution_penalty": { "air": -0.15, "water": -0.20, "ground": -0.10 },
          "crime_penalty": -0.20,
          "transit_bonus": { "metro_station": 1.20, "bus_stop": 1.05 }
        }
      },
      "pollution_spread": {
        "_desc": "CS2: pollution spreads based on source and wind",
        "types": {
          "air":    { "spread_radius": 5, "decay_rate": 0.1, "affected_by": "wind_direction" },
          "ground": { "spread_radius": 2, "decay_rate": 0.02, "contaminates": "groundwater" },
          "noise":  { "spread_radius": 3, "decay_rate": 0.3, "blocked_by": "sound_barriers" }
        }
      },
      "service_efficiency": {
        "_desc": "CS2 budget scaling: 50% budget = 25% efficiency, 150% = 125%",
        "formula": "if budget < 100: efficiency = budget * 0.5; else: efficiency = 75 + (budget * 0.333)",
        "affects": ["response_time", "coverage_radius", "vehicle_count", "capacity"]
      }
    }
  }
}
```

#### Lua enhancement: `agent_needs.lua` — tick-based metric evolution

```lua
function evolve_npc_metrics(npc_id, tick)
  local npc = NPCs[npc_id]
  local needs = NPC_NEEDS[npc_id]
  if not npc or not needs then return end
  
  -- Productivity (Workers & Resources formula, 30% floor)
  local happiness_avg = (needs.hunger + needs.energy + needs.social + 
                         needs.entertainment + needs.safety) / 500.0
  local skill_match = get_skill_match(npc)
  local health_factor = (needs.hygiene or 50) / 100.0
  npc.productivity = math.max(0.30, happiness_avg * skill_match * health_factor)
  
  -- Crime tendency (CS2 formula)
  local police_coverage = get_district_service(npc.district, "police") or 0
  local unemployment = npc.employed and 0 or 0.15
  npc.crime_tendency = 0.05 * (1.0 - happiness_avg) * (1.0 - police_coverage) + unemployment
  
  -- Skill growth (ONI: improve through use)
  if npc.current_action and SKILL_MAP[npc.current_action] then
    local skill = SKILL_MAP[npc.current_action]
    npc.skills[skill] = math.min(1.0, (npc.skills[skill] or 0) + 0.001)
  end
  
  -- Loyalty (Workers & Resources)
  local service_sat = get_district_satisfaction(npc.district)
  local tax_burden = get_tax_burden(npc.education_level)
  npc.loyalty = math.max(0, math.min(100, 
    npc.loyalty + (service_sat * 0.1) - (tax_burden * 0.05) - 0.01
  ))
end
```

---

## 4. ENHANCED DAILY ROUTINES & LIFE STAGES

### What the games teach us

| Game | Mechanic |
|------|----------|
| **CS1** | 5 life stages (Child→Senior), each generates different movement patterns |
| **CS2** | Education progression, employment matching, family formation |
| **Workers & Resources** | 8h work + commute, 16h free, 3-shift 24/7 coverage |
| **ONI** | Schedule blocks (Work/Downtime/Bathtime/Sleep), configurable per dupe |

### AO Implementation — Enhanced Schedule System

```json
{
  "enhanced_schedules": {
    "life_stages": {
      "child":  { "age": [0, 14], "activities": ["school", "play", "home"], "commute_range": 2 },
      "teen":   { "age": [15, 19], "activities": ["high_school", "part_time_work", "socialize", "home"], "commute_range": 4 },
      "adult":  { "age": [20, 59], "activities": ["work", "trade", "socialize", "errands", "home"], "commute_range": 10 },
      "senior": { "age": [60, 99], "activities": ["leisure", "medical", "socialize", "home"], "commute_range": 3 }
    },
    "schedule_blocks": {
      "_desc": "ONI-inspired configurable schedule blocks",
      "templates": {
        "day_worker":   ["sleep","sleep","commute","work","work","work","work","lunch","work","work","commute","socialize","leisure","home","sleep","sleep"],
        "night_worker": ["work","work","commute","sleep","sleep","sleep","sleep","sleep","sleep","sleep","sleep","commute","work","work","work","work"],
        "student":      ["sleep","sleep","commute","school","school","school","lunch","school","school","commute","study","socialize","leisure","home","sleep","sleep"],
        "vendor":       ["sleep","sleep","setup","trade","trade","trade","trade","lunch","trade","trade","trade","cleanup","socialize","home","sleep","sleep"],
        "retired":      ["sleep","sleep","sleep","leisure","medical","leisure","lunch","socialize","leisure","socialize","home","home","sleep","sleep","sleep","sleep"]
      }
    },
    "shift_coverage": {
      "_desc": "Workers & Resources: 3x workers for 24/7 service",
      "shifts": {
        "morning":   { "hours": [6, 14],  "workers_needed": 1.0 },
        "afternoon": { "hours": [14, 22], "workers_needed": 1.0 },
        "night":     { "hours": [22, 6],  "workers_needed": 1.0 }
      },
      "total_workers_for_24h": 3.0,
      "understaffed_penalty": {
        "efficiency": -0.30,
        "service_coverage": -0.25
      }
    }
  }
}
```

---

## 5. MODDING & PLUGIN OPPORTUNITIES

### Current Plugin System
The AO engine already has a plugin architecture: `plugins/economy_modifier.lua`, `plugins/event_logger.lua`, `plugins/nature.lua`, `plugins/weather.lua`.

### Proposed New Plugins

| Plugin | Source Inspiration | Function |
|--------|-------------------|----------|
| `plugins/commuting.lua` | W&R, CS2, DF | Calculate travel costs, mode selection, commute penalties |
| `plugins/crime_system.lua` | CS2 | Crime probability per NPC, police response, prison mechanics |
| `plugins/education_pipeline.lua` | CS2 | Education levels, school capacity, skill progression |
| `plugins/pollution_engine.lua` | CS2 | Air/ground/noise pollution spread and decay |
| `plugins/land_value.lua` | CS2 | Dynamic land value based on services, pollution, transit |
| `plugins/public_transport.lua` | CS1, CS2 | Transit lines, stops, ticket pricing, ridership |
| `plugins/governance.lua` | CS2 | Policies, taxation, budget management, service fees |
| `plugins/trade_logistics.lua` | CS2, DF | Supply chains, cargo routing, resource processing |

### Plugin Interface Pattern

```lua
-- plugins/commuting.lua
local Plugin = {}

Plugin.name = "commuting"
Plugin.version = "1.0.0"
Plugin.hooks = {
  "on_tick",           -- Calculate commute costs each tick
  "on_npc_relocate",   -- Recalculate when NPC moves
  "on_district_change" -- Update traffic weights
}

function Plugin.on_tick(tick, district_state)
  for npc_id, npc in pairs(district_state.npcs) do
    if npc.current_action == "commute" then
      local cost = calculate_commute_cost(npc_id, npc.home_district, npc.work_district, tick)
      apply_commute_effects(npc_id, cost)
    end
  end
end

function Plugin.on_npc_relocate(npc_id, old_district, new_district)
  -- Recalculate commute when NPC moves housing
  recalculate_routes(npc_id)
end

return Plugin
```

---

## 6. NPC CODEC ENHANCEMENTS

### Current: 6 archetypes → Proposed: 20+ archetypes

| New Archetype | Source | Key Behaviors |
|---------------|--------|---------------|
| teacher | CS2 Education | School schedule, student interaction, education boost |
| doctor | CS2 Healthcare | Medical facility schedule, ambulance response |
| firefighter | CS2 Fire & Rescue | Emergency response, fire hazard patrol |
| police_officer | CS2 Police | Crime response, patrol routes, arrest mechanics |
| factory_worker | CS2 Industry, W&R | Shift work, 24/7 coverage, commute sensitivity |
| office_worker | CS2 Office | Weekday 9-5, education-gated, lunch routines |
| bus_driver | CS2 Transport | Route-based schedule, fixed stops, service level |
| sanitation_worker | CS2 Garbage | Collection routes, garbage generation response |
| postal_worker | CS2 Communications | Mail collection, delivery routes |
| farmer | CS2 Agriculture | Seasonal schedule, renewable resource management |
| student | CS2 Education, ONI | School schedule, study vs work decisions |
| retired | CS2 Citizens | Leisure-heavy, medical visits, slow movement |
| tourist | CS2 Parks | Visit attractions, hotel-based, spending behavior |
| criminal | CS2 Crime | Target selection, crime probability, arrest risk |

### Enhanced NPC Properties

```json
{
  "npc_enhanced_properties": {
    "education_level": { "range": [0, 4], "labels": ["uneducated","poorly","educated","well","highly"] },
    "wealth_tier": { "range": [1, 5], "affects": ["car_ownership", "housing_quality", "leisure_options"] },
    "commute_mode": { "determined_by": "wealth + distance + age" },
    "productivity": { "range": [0.30, 1.20], "decays_from": "happiness" },
    "crime_tendency": { "range": [0, 1.0], "driven_by": "wellbeing + employment + police" },
    "loyalty": { "range": [0, 100], "affected_by": "services + taxation + propaganda" },
    "skills": { "type": "dict", "grows_through_use": true, "cap": 1.0 },
    "relationships_expanded": {
      "coworkers": "same workplace NPCs",
      "neighbors": "same building/block NPCs",
      "classmates": "same school NPCs",
      "family": "household members"
    }
  }
}
```

---

## 7. IMPLEMENTATION PRIORITY ORDER

| Priority | Enhancement | Effort | Impact |
|----------|------------|--------|--------|
| **P0** | Enhanced schedules (life stages + ONI blocks) | Low | High — immediate behavior diversity |
| **P0** | Dynamic metrics (productivity, crime, loyalty) | Medium | High — city feels alive |
| **P1** | Commuting system (travel costs, mode selection) | Medium | High — realistic movement |
| **P1** | Priority task selection (ONI-style) | Low | Medium — smarter NPC decisions |
| **P2** | New archetypes (teacher, doctor, police, etc.) | Medium | High — role diversity |
| **P2** | Skill growth through use | Low | Medium — NPC evolution |
| **P3** | Pollution spread engine | Medium | Medium — environmental realism |
| **P3** | Land value dynamics | Low | Medium — economic depth |
| **P3** | Public transport simulation | High | Medium — infrastructure layer |
| **P4** | Plugin architecture expansion | Medium | Long-term — modding support |

---

## Source Documents

| Folder | Files | Topic |
|--------|-------|-------|
| `docs/cs2_wiki/` | 56 files (580+ KB) | Complete CS2 mechanics reference |
| `docs/workers_resources_wiki/` | `citizens.md` | Commuting, walking radii, happiness, shifts |
| `docs/dwarf_fortress_wiki/` | `pathfinding.md` | A* algorithm, traffic designations, job selection |
| `docs/oni_wiki/` | `priority.md` | Priority queues, schedules, errand system |
| `docs/cs1_wiki/` | `traffic_ai_deep_dive.md` | Multi-modal pathfinding, agent caps, teleport fallback |
