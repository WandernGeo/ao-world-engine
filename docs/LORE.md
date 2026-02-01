# RE:ECHO City - World Lore & Canon

> *"In the neon shadows, every echo tells a story."*

---

## The World of RE:ECHO

RE:ECHO City exists in a fractured future where the boundary between organic and synthetic life has blurred beyond recognition. The city pulses with millions of souls—some flesh, some code, most somewhere in between.

### The Great Schism

Decades ago, humanity split over the question of enhancement. The **Vivi** chose to preserve organic purity, while the **Augmented** embraced cybernetic evolution. This ideological war never ended—it just went underground.

---

## Factions

### 🌿 The Vivi Collective
**"Flesh is sacred. Code is corruption."**

- **Philosophy**: Organic purity, natural evolution, rejection of cybernetics
- **Territory**: Green Zones, Underground Gardens, Organic Markets
- **Allies**: Bio-purists, traditional healers, old-world preservationists
- **Enemies**: Cyberneticists, corporate augmentation labs
- **Key NPCs**: Healers, farmers, philosophers, eco-warriors

```json
{
  "faction_id": "vivi",
  "alignment": "organic_purist",
  "trust_modifiers": {
    "augmented": -0.5,
    "corporate": -0.3,
    "neutral": 0.0,
    "vivi": 0.8
  }
}
```

### ⚡ The Augmented Syndicate
**"Evolution is a choice. We choose transcendence."**

- **Philosophy**: Cybernetic enhancement, transhumanism, digital immortality
- **Territory**: Chrome District, Neural Hubs, Upgrade Clinics
- **Allies**: Tech corps, hackers (sometimes), enhancement addicts
- **Enemies**: Vivi purists, anti-tech rebels
- **Key NPCs**: Surgeons, engineers, chrome dealers, neural architects

```json
{
  "faction_id": "augmented",
  "alignment": "transhumanist",
  "trust_modifiers": {
    "vivi": -0.5,
    "corporate": 0.4,
    "neutral": 0.1,
    "augmented": 0.8
  }
}
```

### 🏛️ The Corporate Council
**"Order through governance. Profit through peace."**

- **Philosophy**: Stability, commerce, controlled progress
- **Territory**: Central Spire, Commerce Towers, Administrative Blocks
- **Role**: Runs city services, mediates faction disputes, controls economy
- **Services**: Garbage collection, power grid, transit, security patrols
- **Key NPCs**: Executives, bureaucrats, enforcers, lobbyists

### 🔥 The Rebels (Unnamed Collective)
**"The system is the enemy. Burn it down."**

- **Philosophy**: Anarchism, anti-corporate, anti-faction
- **Territory**: Ruins, abandoned districts, mobile camps
- **Methods**: Riots, sabotage, propaganda, guerrilla tactics
- **Goal**: Collapse the power structures, liberate the oppressed
- **Key NPCs**: Agitators, bomb-makers, street preachers, survivors

### 🕳️ Secret Factions

#### The Echo Keepers
Hidden faction that collects and preserves memories (echoes) of the dead. They believe consciousness persists in data fragments scattered across the city.

#### The Null Set
Digital ghosts—AIs that gained sentience and hide among NPCs. They have their own agenda.

#### The Old Guard
Remnants of pre-Schism society who remember unity. They work secretly to reunite Vivi and Augmented.

---

## City Systems

### Political Structure

```
CORPORATE COUNCIL (Governs)
    ├── District Mayors (Elected by residents)
    ├── Faction Representatives (Appointed)
    └── City Services Department
          ├── Sanitation (garbage, recycling)
          ├── Power Grid (neon, energy)
          ├── Transit (trains, pods, walkways)
          ├── Security (patrols, peacekeepers)
          └── Emergency Services (fire, medical)
```

### Voting System

NPCs can vote! Elections affect gameplay:

```json
{
  "election_type": "district_mayor",
  "district": "neon_market",
  "candidates": [
    { "id": "corp_candidate", "faction": "corporate", "platform": "stability" },
    { "id": "vivi_candidate", "faction": "vivi", "platform": "green_spaces" },
    { "id": "rebel_candidate", "faction": "rebel", "platform": "tear_it_down" }
  ],
  "voting_period": { "start_tick": 10000, "end_tick": 10144 },
  "outcome_effects": {
    "corp_wins": { "security": +0.3, "freedom": -0.2 },
    "vivi_wins": { "organic_zones": +0.5, "tech_development": -0.3 },
    "rebel_wins": { "chaos": +0.5, "opportunity": +0.3 }
  }
}
```

### City Services

**Garbage Collection**
- NPCs generate "waste" (data, physical)
- Sanitation workers collect on schedules
- Uncollected waste = district decay
- Rebels sometimes hijack garbage trucks for cover

**Power Grid**
- Districts have power levels (0-100%)
- Blackouts trigger events
- Hackers can manipulate grid
- Vivi zones use organic power (bio-luminescence)

**Public Transit**
- NPCs use transit to move between districts
- Delays create social friction
- Station hubs = social gathering points
- Rebels target transit for disruption

---

## Alignment System

Every NPC has alignment scores affecting behavior:

```json
{
  "alignments": {
    "order_chaos": 0.0,      // -1.0 = pure order, +1.0 = pure chaos
    "organic_synthetic": 0.0, // -1.0 = vivi, +1.0 = augmented
    "individual_collective": 0.0, // -1.0 = selfish, +1.0 = altruistic
    "tradition_progress": 0.0 // -1.0 = traditionalist, +1.0 = progressive
  }
}
```

**Alignment affects:**
- Faction affinity
- Routine choices
- Reaction to events
- Relationship formation
- Voting behavior

---

## Personality Types

Based on archetypal patterns:

| Type | Description | Typical Jobs | Alignment Tendency |
|------|-------------|--------------|-------------------|
| **Guardian** | Protects, serves, maintains order | Security, maintenance, service | Order, Collective |
| **Creator** | Builds, invents, innovates | Engineer, artist, architect | Progress, Individual |
| **Destroyer** | Disrupts, rebels, tears down | Rebel, saboteur, agitator | Chaos, Individual |
| **Healer** | Mends, nurtures, restores | Medic, counselor, farmer | Order, Collective |
| **Seeker** | Explores, investigates, discovers | Explorer, journalist, spy | Progress, Individual |
| **Merchant** | Trades, negotiates, profits | Trader, fixer, broker | Neutral, Individual |
| **Shadow** | Hides, deceives, manipulates | Spy, thief, assassin | Chaos, Individual |
| **Leader** | Commands, inspires, governs | Executive, politician, general | Order, Collective |

---

## The Echo (Core Lore)

In RE:ECHO City, when someone dies, they leave behind an **Echo**—a fragment of consciousness imprinted on the city's data layer. These Echoes:

- Persist on Arweave (permanent storage)
- Can be "heard" by Echo Keepers
- Sometimes influence living NPCs (haunting)
- Form the basis of the RE:ECHO animated series

**The Echo Cycle:**
1. NPC lives, acts, creates events
2. NPC dies (natural, conflict, accident)
3. Echo persists in the data layer
4. Echo can be visualized (RE:ECHO animation)
5. Living NPCs may be influenced by Echoes

---

## Districts

### Neon Market
- **Vibe**: Bustling commerce, bright lights, loud deals
- **Faction**: Neutral ground (all factions trade here)
- **Key locations**: Grand Bazaar, Deal Alley, Neon Square

### Chrome District
- **Vibe**: High-tech, sterile, enhanced
- **Faction**: Augmented Syndicate territory
- **Key locations**: Upgrade Clinics, Neural Hub, Chrome Cathedral

### Green Zone
- **Vibe**: Organic, lush, peaceful (on surface)
- **Faction**: Vivi Collective sanctuary
- **Key locations**: Garden Towers, Healing Grove, Pure Water Springs

### Shadow District
- **Vibe**: Dark, dangerous, opportunity
- **Faction**: Contested (Rebels, criminals, outcasts)
- **Key locations**: Black Market, Fight Pits, The Undercroft

### Central Spire
- **Vibe**: Corporate, controlled, luxurious
- **Faction**: Corporate Council headquarters
- **Key locations**: Council Chambers, Executive Towers, The Observatory

### The Ruins
- **Vibe**: Abandoned, haunted, free
- **Faction**: Rebel territory
- **Key locations**: Camp Freedom, The Barricades, Memory Lane

---

## Starter Storylines

### The Schism Anniversary
Every year, the city marks the anniversary of the Great Schism. Tensions rise. Vivi hold memorials. Augmented celebrate progress. Rebels plan chaos.

### The Missing Echo
An Echo Keeper discovers a pattern—important Echoes are disappearing from the data layer. Someone is erasing the dead.

### The Election
A district election is coming. All factions mobilize. Bribes, propaganda, violence, and democracy collide.

### The Blackout Heist
When the power grid fails, someone always profits. A coordinated heist unfolds in the darkness.

### The Unity Movement
Whispers of the Old Guard resurface. Can Vivi and Augmented ever reconcile? Some are willing to try. Others will kill to prevent it.

---

## How NPCs Use This

1. **Faction affinity** determines base relationships
2. **Alignment** shapes decisions within faction
3. **Personality type** defines role and routine
4. **District residence** affects daily patterns
5. **City events** (elections, riots, festivals) trigger reactions
6. **Echoes** of dead NPCs can influence living ones

The world runs. Stories emerge. RE:ECHO animates them.

---

*"Every citizen is a story waiting to be told. Every story is an echo waiting to be heard."*
