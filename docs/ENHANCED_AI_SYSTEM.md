# Enhanced Autonomous AI System

> Borrowing from the best game AI + AO Network's "always running" capabilities

---

## 🎮 Inspirations from Great Game AI

### 1. emergent AI - Deep Needs System
```
Each NPC has 500+ interlocking needs, skills, and memories.
A preference for a certain drink can escalate into a tavern brawl.
```

**What we can copy:**
- ✅ Already have: Basic needs (hunger, energy, hygiene)
- 🆕 ADD: Personality quirks that affect behavior
- 🆕 ADD: Preference chains (likes → seeks → conflicts)
- 🆕 ADD: Emotional states that compound over time

### 2. utility AI - AI Storyteller
```
A centralized "storyteller" picks from event types to create drama.
Cassandra = steady difficulty, Randy = chaotic, Phoebe = relaxed.
```

**What we can copy:**
- 🆕 ADD: Storyteller modes (dramatic, peaceful, chaotic)
- 🆕 ADD: Pacing control (not just random - CURATED random)
- 🆕 ADD: Event weighting based on recent history
- 🆕 ADD: "Beat structure" - buildup → climax → resolution

### 3. Crusader Kings - Secret Systems
```
Characters have hidden traits, claims, and plots.
AI dynasties make autonomous decisions: marry, assassinate, ally.
```

**What we can copy:**
- 🆕 ADD: Hidden relationships (secret lovers, conspiracies)
- 🆕 ADD: Long-term NPC goals (ambition system)
- 🆕 ADD: Dynasty/lineage tracking
- 🆕 ADD: Political schemes that unfold over time

### 4. needs-based AI - Social Networks
```
Relationships have multiple dimensions: friendship, romance, rivalry.
Social actions have visible effects on mood and behavior.
```

**What we can copy:**
- ✅ Already have: Trust-based relationships
- 🆕 ADD: Multiple relationship dimensions (respect, fear, attraction)
- 🆕 ADD: Group dynamics (cliques, factions within factions)

---

## ⚡ AO Network: Always Running (Free!)

### Key Discovery: AO Processes Run Autonomously

From the research:
> "AO processes can operate autonomously, executing predefined tasks 
> without requiring external triggers or centralized infrastructure."

> "Processes can continue running indefinitely."

> "Up to 16 GB memory per compute unit."

> "No protocol-enforced limitations on computation size."

### How It Works: Cron Messages

```lua
-- AO Process with built-in cron job
Handlers.add("Cron-Tick", 
  function(msg) return msg.Action == "Cron" end,
  function(msg)
    -- This runs AUTOMATICALLY every interval!
    local tick = GetCurrentTick()
    local world_state = GetWorldState()
    
    -- Run simulation
    for _, npc in ipairs(world_state.npcs) do
      ProcessNPCTick(npc, tick)
    end
    
    -- Save state back to process memory
    SaveWorldState(world_state)
  end
)
```

### Who Pays? Nobody (Mostly)!

```
TRIGGER              │ WHO PAYS
─────────────────────┼─────────────────────────────
User sends message   │ User (very small AR fee)
Cron auto-tick       │ Process creator (pre-funded)
Read-only query      │ FREE (just reading Arweave)
```

**The key:** Pre-fund the process with a small amount of AR, and it can run for months/years on cron ticks.

---

## 🔄 The "Always Living" Architecture

### Current Problem
```
Your server runs → Simulation happens
Server stops     → World freezes
Nobody online    → NPCs don't exist
```

### Solution: AO Autonomous Process
```
ARWEAVE + AO NETWORK
┌──────────────────────────────────────────────────────────────┐
│                                                               │
│  AO Process: "reecho_city_v1"                                │
│  ├── State: Full world (NPCs, buildings, relationships)     │
│  ├── Code: Embedded Python behaviors (base64)               │
│  └── Cron: Every 60 seconds, run simulate_tick()            │
│                                                               │
│  Cron triggers automatically:                                │
│  ┌─────────────────────────────────────────────────────────┐│
│  │ Tick 1000: Charlie meets Felix at bar                   ││
│  │ Tick 1001: Resistance faction recruits Jax              ││
│  │ Tick 1002: Temple builds new checkpoint                 ││
│  │ Tick 1003: Nova trades tech parts to smuggler           ││
│  │ ... (continues forever, even with no users)             ││
│  └─────────────────────────────────────────────────────────┘│
│                                                               │
│  Users just READ the state:                                  │
│  └── ao.send({Action="GetState"}) → Returns current world   │
│                                                               │
└──────────────────────────────────────────────────────────────┘

When user connects:
1. Fetch current state from AO process
2. World is already at tick 50,000
3. Charlie has met Felix 200 times
4. Jax joined Resistance at tick 1001
5. The city has evolved without you!
```

---

## 🆕 Enhanced Features to Add

### 1. utility AI-Style Storyteller

```python
class StorytellerAI:
    """Controls pacing and drama of the simulation."""
    
    def __init__(self, mode="dramatic"):
        self.mode = mode
        self.recent_events = []
        self.tension_level = 0.3
    
    def pick_next_event(self, world_state, tick):
        # Dramatic mode: build tension, then release
        if self.tension_level < 0.7:
            # Build tension
            return self.pick_escalating_event()
        else:
            # Climax or resolution
            return self.pick_dramatic_event()
    
    def pick_escalating_event(self):
        events = [
            "suspicious_stranger_arrives",
            "secret_discovered",
            "resource_shortage",
            "faction_tension_rises",
        ]
        return deterministic_choice(events, self.seed)
```

### 2. emergent AI-Style Personality Quirks

```python
PERSONALITY_QUIRKS = {
    "perfectionist": {
        "triggers": ["low_quality_item", "messy_room"],
        "effects": {"mood": -10, "social": -5},
        "behaviors": ["complain", "fix_it", "leave"]
    },
    "alcoholic": {
        "triggers": ["bar_nearby", "stress_high"],
        "effects": {"seek_drink": 0.9},
        "behaviors": ["go_to_bar", "drink_alone"]
    },
    "paranoid": {
        "triggers": ["stranger_nearby", "night_time"],
        "effects": {"trust_strangers": -0.3, "safety": -20},
        "behaviors": ["hide", "watch", "flee"]
    },
    "romantic": {
        "triggers": ["attractive_npc_nearby"],
        "effects": {"social_need": +20},
        "behaviors": ["flirt", "give_gift", "write_poetry"]
    }
}
```

### 3. Crusader Kings-Style Schemes

```python
class Scheme:
    """Long-term NPC plan that unfolds over multiple ticks."""
    
    def __init__(self, npc_id, scheme_type, target_id):
        self.npc_id = npc_id
        self.type = scheme_type  # "assassinate", "seduce", "usurp"
        self.target_id = target_id
        self.progress = 0.0
        self.steps_completed = []
        self.discovered = False
    
    SCHEME_TYPES = {
        "overthrow_leader": {
            "steps": [
                "gather_allies",
                "spread_rumors",
                "weaken_target",
                "strike"
            ],
            "success_chance": 0.3,
            "consequences_failure": ["exile", "prison", "death"]
        },
        "secret_romance": {
            "steps": [
                "exchange_glances",
                "secret_meeting",
                "love_letter",
                "declaration"
            ],
            "success_chance": 0.6,
            "consequences_failure": ["rejected", "scandal", "shame"]
        }
    }
```

### 4. Emergent Group Dynamics

```python
class SocialGroup:
    """Bowling clubs, drinking buddies, crime syndicates."""
    
    def __init__(self, group_id, group_type):
        self.id = group_id
        self.type = group_type  # "club", "gang", "family", "religion"
        self.members = []
        self.leader_id = None
        self.reputation = 0.5
        self.territory = []
        self.rivals = []
        self.allies = []
    
    def weekly_meeting(self, tick):
        """Group meets and dynamics evolve."""
        # Members bond
        for m1 in self.members:
            for m2 in self.members:
                if m1 != m2:
                    increase_trust(m1, m2, 0.02)
        
        # Leader challenges
        if self.should_challenge_leader(tick):
            challenger = self.pick_challenger()
            self.resolve_challenge(challenger)
        
        # Group decisions
        if self.type == "gang":
            self.plan_heist()
        elif self.type == "resistance":
            self.plan_rebellion()
```

---

## ✅ IMPLEMENTED: Comprehensive Personality System

### RE:ECHO Alignment (Primary System)

From the series lore, NPCs have a two-axis alignment:

| Axis | Values | Description |
|------|--------|-------------|
| **Signal** | Resonant / Neutral / Dissonant | How NPC relates to Echoes (Good/Neutral/Evil) |
| **Method** | Harmonic / Adaptive / Chaotic | How NPC achieves goals (Law/Neutral/Chaos) |

**9 Possible Alignments:**
- Harmonic Resonant = Protects Echoes through tradition
- Chaotic Dissonant = Seeks to destroy Echoes entirely
- etc.

### RE:ECHO Archetypes (8 Types)

| Archetype | Description | MBTI-Like | Example |
|-----------|-------------|-----------|---------|
| Architect | Builds systems for order | INTJ | Zero Chen |
| Advocate | Champions others' causes | ENFJ | Sister Mira |
| Commander | Leads with authority | ESTJ | Morack |
| Seeker | Explores truth and mystery | INTP | Charlie |
| Catalyst | Sparks change and action | ENFP | Kai Vance |
| Sentinel | Guards and protects | ISTJ | Prophet Elijah |
| Mediator | Bridges divides | INFP | Orion Thane |
| Operative | Gets things done | ESTP | Aiche |

### Additional Personality Layers

- **MBTI** (16 types with compatibility)
- **Western Zodiac** (12 signs with elements)
- **Chinese Zodiac** (12 animals × 5 elements)
- **Combined traits** (aggregated from all systems)

### Family & Faction Influence

NPCs don't have random personalities - social groups share traits:

```python
# Family members (same last name) share tendencies
"Nova Chen" and "Zero Chen" → Similar archetype family

# Faction members share alignment tendencies  
FACTION_TENDENCIES = {
    "resistance": {"signal": "resonant", "method": "chaotic"},
    "temple": {"signal": "neutral", "method": "harmonic"},
    "civilian": {"signal": "neutral", "method": "adaptive"},
}
```

### Usage

```bash
# Preview all NPC personalities
python scripts/npc_personality_generator.py --preview

# Update bulk NPCs with personality
python scripts/npc_personality_generator.py --update-bulk

# Single NPC personality
python scripts/npc_personality_generator.py --npc charlie
```

---

## ✅ IMPLEMENTED: Advanced AI Systems

All systems are in `scripts/advanced_ai_systems.py`:

### 1. Utility System (utility AI)
```python
utility_system = UtilitySystem()
action, score = utility_system.evaluate_actions(npc_state, available_actions)
```

### 2. GOAP (General Game AI)
```python
goap = GOAPPlanner()
plan = goap.plan(npc, current_state, goal_state)
```

### 3. A-Life Migration (STALKER)
```python
alife = ALifeSystem(world)
migrations = alife.simulate_migrations(tick)
```

### 4. Personality Quirks (emergent AI)
```python
quirks = QuirkSystem()
effects = quirks.process_quirks(npc, situation)
```

### 5. Storyteller AI (utility AI)
```python
storyteller = StorytellerAI(mode="dramatic")
event = storyteller.pick_next_event(world_state, tick)
```

---

## Next Steps

### ✅ Completed
1. ✅ **Utility System** - utility-based action scoring
2. ✅ **GOAP Planning** - Goal-Oriented Action Planning
3. ✅ **A-Life Migration** - STALKER-style zone roaming
4. ✅ **AI Storyteller** - utility-based event curation
5. ✅ **Personality Quirks** - emergent AI emergent behavior
6. ✅ **Apophenia Support** - Pattern generation for player speculation
7. ✅ **Social Groups** - needs-based AI: cliques, clubs, gangs, families
8. ✅ **Long-term Schemes** - Crusader Kings: assassination, seduction, usurpation
9. ✅ **Dynasty System** - Crusader Kings: inheritance, family traits, succession
10. ✅ **Personality System** - Full RE:ECHO + MBTI + Zodiacs with family/faction influence

### 🚧 Upcoming
1. **Dialogue System (Rasa-style)** - Intents, entities, stories, canned responses
   - Eliminates LLM dependency for NPC conversations
   - Deterministic dialogue trees compatible with AO
   - Personality-influenced response selection
2. **Create AO Process** - Deploy autonomous cron-based simulation
3. **Test on AO Testnet** - Verify always-running behavior
