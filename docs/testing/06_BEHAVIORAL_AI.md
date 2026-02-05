# Behavioral AI Tests (27 tests)

> **Updated:** 2026-02-05T07:20:00-05:00

Tests for AI decision-making logic that drives NPC behavior.

---

## Need-Driven Decision Tests (8 tests)

| Test Name | What It Validates | Logic Tested |
|-----------|------------------|--------------|
| Decision Function Exists | Core AI present | `decide_action` in code |
| Hunger → Eat Decision | Hungry NPC eats | urgent_need == "hunger" → eat |
| Energy → Sleep Decision | Tired NPC sleeps | urgent_need == "energy" → sleep |
| Social → Socialize Decision | Lonely NPC talks | urgent_need == "social" → socialize |
| Money → Work Decision | Poor NPC works | urgent_need == "money" → work |
| Critical Need Threshold | Urgent priority | Threshold at 0.2 |
| Need Decay Logic | Needs decrease | All needs decay each tick |
| Activity Satisfaction | Actions help needs | Activities restore values |

### Decision Logic

```lua
function decide_action(npc)
    local urgent_need, is_urgent = find_urgent_need(npc)
    
    if is_urgent then
        -- Immediate action required
        if urgent_need == "hunger" then
            return "eat", find_nearest_food(npc.location)
        elseif urgent_need == "energy" then
            return "sleep", npc.home_location
        elseif urgent_need == "social" then
            return "socialize", find_social_venue(npc.location)
        elseif urgent_need == "money" then
            return "work", npc.work_location
        elseif urgent_need == "safety" then
            return "flee", find_safe_zone(npc.location)
        end
    end
    
    -- No urgent need, follow schedule
    return get_scheduled_activity(npc, WorldTick)
end
```

---

## Encounter Trigger Tests (7 tests)

| Test Name | What It Validates | Logic Tested |
|-----------|------------------|--------------|
| Encounter Calculation | Probability math | calculate_encounter_chance |
| Marker-Based Triggers | Location matters | Markers affect chance |
| Location Occupancy | Who's around | NPCs in same location |
| Time-Based Chances | When matters | Time modifiers |
| Faction Hangouts | Territory behavior | Faction bonuses |
| Probability Randomness | Non-deterministic | Math.random() usage |
| Location Modifiers | Zone effects | Zone type modifiers |

### Encounter Probability Formula

```lua
function calculate_encounter_chance(npc, location)
    local base_chance = 0.1  -- 10% base
    
    -- Location modifiers
    local zone_modifier = ZONE_MODIFIERS[location.zone_type] or 1.0
    --  bar = 2.0, workplace = 0.5, street = 1.0, etc.
    
    -- Time modifiers  
    local time_modifier = get_time_modifier(WorldTick)
    --  night = 1.5, rush_hour = 2.0, work_hours = 0.5
    
    -- Faction territory bonus
    local faction_bonus = 0
    if is_faction_territory(location, npc.faction) then
        faction_bonus = 0.2
    end
    
    -- Crowding bonus
    local npcs_here = count_npcs_at(location)
    local crowd_bonus = math.min(npcs_here * 0.02, 0.3)
    
    return base_chance * zone_modifier * time_modifier + faction_bonus + crowd_bonus
end
```

---

## Schedule Prediction Tests (3 tests)

| Test Name | What It Validates |
|-----------|------------------|
| World Time Tracking | WorldTick, WorldDay, WorldYear |
| NPC Schedule Data | Routines defined |
| Work Hour Logic | work_start_hour, work_end_hour |

### Time Period Mapping

```
Period  Hours       Description
─────────────────────────────────────
T01     00:00-03:00 Late Night (most asleep)
T02     03:00-06:00 Pre-Dawn (early risers)
T03     06:00-09:00 Morning Commute
T04     09:00-12:00 Morning Work
T05     12:00-15:00 Lunch/Afternoon
T06     15:00-18:00 Afternoon Work
T07     18:00-20:00 Evening Commute
T08     20:00-23:00 Evening/Night Life
T09     23:00-00:00 Late Evening
```

---

## Faction Interaction Tests (4 tests)

| Test Name | What It Validates |
|-----------|------------------|
| Faction Territories | Territory claims exist |
| Faction Encounters | Cross-faction meetings |
| Faction Mood Effects | Faction status affects NPCs |
| Faction Loyalty | Loyalty tracking |

### Faction Influence on Behavior

```lua
function get_faction_mood_modifier(npc, location)
    local faction = npc.faction
    local territory_owner = get_territory_owner(location)
    
    if territory_owner == faction then
        return 1.2  -- Confident on home turf
    elseif is_rival_faction(faction, territory_owner) then
        return 0.7  -- Nervous in rival territory
    else
        return 1.0  -- Neutral territory
    end
end
```

---

## Mood and Social Tests (3 tests)

| Test Name | What It Validates |
|-----------|------------------|
| Mood Calculation | Mood from needs |
| Social Influence | Others affect mood |
| Mood Effects | Mood changes behavior |

### Mood Calculation

```lua
function calculate_mood(npc)
    local base_mood = 0.5
    
    -- Average of all needs
    local need_sum = 0
    for _, value in pairs(npc.needs) do
        need_sum = need_sum + value
    end
    local avg_needs = need_sum / 7  -- 7 needs
    
    -- Recent events
    local event_modifier = get_recent_event_modifier(npc)
    
    -- Social influence
    local social_modifier = get_social_mood_influence(npc)
    
    return math.clamp(base_mood + avg_needs * 0.3 + event_modifier + social_modifier, 0, 1)
end
```

---

## Mission Outcome Tests (2 tests)

| Test Name | What It Validates |
|-----------|------------------|
| Mission Generation | Missions created |
| Outcome Calculation | Success probability |

---

*Part of the AO World Engine Test Suite*
