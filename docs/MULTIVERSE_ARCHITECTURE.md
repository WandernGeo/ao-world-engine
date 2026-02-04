# AO World Engine - Multiverse Architecture

## Vision

The AO World Engine creates **interconnected simulated worlds** on Arweave. Each deployment is a "layer" in a shared multiverse. All layers share **Echoes** - artifacts that bleed between worlds and into the real world via the GeoEchoes app.

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         THE MULTIVERSE                                   │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│   LAYER 0: Prime (Testnet)        LAYER 1: Alpha               LAYER 2+  │
│   ├── 800 NPCs                    ├── 10M NPCs                 ├── Your  │
│   ├── NYC Claimed                 ├── Full NYC                    World  │
│   ├── $0.01 deployment            ├── Main production          ├── Phila?│
│   └── Testing layer bleed         └── Canon universe           └── Tokyo?│
│                                                                          │
│                          ↕ ECHOES ↕                                      │
│                                                                          │
│   ┌──────────────────────────────────────────────────────────┐          │
│   │               LAYER REGISTRY (Master AO Process)         │          │
│   │   • Tracks all worlds                                    │          │
│   │   • Validates geo-claims                                 │          │
│   │   • Routes echo propagation                              │          │
│   │   • Enforces multiverse rules                            │          │
│   └──────────────────────────────────────────────────────────┘          │
│                          ↕                                               │
│   ┌──────────────────────────────────────────────────────────┐          │
│   │                  GEOECHOES APP (Real World)              │          │
│   │   • Finds echoes at real GPS coordinates                 │          │
│   │   • Users leave echoes that appear in simulations        │          │
│   │   • NPCs leave echoes users find IRL                     │          │
│   └──────────────────────────────────────────────────────────┘          │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 1. Layer Registry (Master Process)

Every AO World Engine deployment MUST register with the Layer Registry.

### On Arweave (ao-processes/layer_registry.lua)

```lua
-- Global state
Layers = Layers or {}           -- All registered worlds
GeoClaims = GeoClaims or {}     -- city -> layer mapping
EchoQueue = EchoQueue or {}     -- Cross-layer echo propagation

-- Register a new layer
Handlers.add("register-layer", function(msg)
    local data = json.decode(msg.Data)
    
    -- Validate geo-claim doesn't conflict
    if data.geo_claim then
        local existing = GeoClaims[data.geo_claim.city_id]
        if existing and existing.layer_id ~= data.layer_id then
            return ao.send({ Target = msg.From, Action = "error", 
                Data = "City already claimed by layer: " .. existing.layer_id })
        end
        GeoClaims[data.geo_claim.city_id] = { 
            layer_id = data.layer_id,
            coordinates = data.geo_claim.coordinates,
            claimed_at = WorldTick
        }
    end
    
    Layers[data.layer_id] = {
        process_id = msg.From,
        name = data.name,
        layer_number = #Layers,
        parent_layer = data.parent_layer or "prime",
        population = data.population,
        geo_claim = data.geo_claim,
        created_at = WorldTick
    }
end)

-- Propagate echo between layers
Handlers.add("propagate-echo", function(msg)
    local echo = json.decode(msg.Data)
    
    -- Send to all connected layers (with bleed probability)
    for layer_id, layer in pairs(Layers) do
        if layer_id ~= echo.source_layer then
            local bleed_chance = calculate_bleed_probability(echo, layer)
            if bleed_chance > 0 then
                ao.send({
                    Target = layer.process_id,
                    Action = "receive-echo",
                    Data = json.encode({
                        echo = echo.content,
                        source_layer = echo.source_layer,
                        bleed_intensity = bleed_chance
                    })
                })
            end
        end
    end
end)
```

---

## 2. Geo-Claiming System

Cities are tied to **real-world GPS coordinates**. Once claimed, no other layer can claim that location in the same parent universe.

### Geo-Claim Structure

```json
{
  "city_id": "nyc",
  "display_name": "RE:ECHO City (New York)",
  "coordinates": {
    "type": "Polygon",
    "bbox": [-74.2591, 40.4774, -73.7002, 40.9176]
  },
  "real_world_mapping": {
    "temple_district": "Midtown Manhattan",
    "neon_district": "Times Square",
    "undercity": "Subway System"
  },
  "claimed_by": "layer_00_prime",
  "claimed_at_tx": "arweave_tx_id"
}
```

### Rules
1. **First-come-first-served** - First to deploy owns it
2. **Must populate** - Min 100 NPCs per claim
3. **Gas cost** - Pay AR to prevent spam
4. **Interconnection required** - MUST register with Layer Registry

---

## 3. Auto-Generated GeoEchoes

NPCs create "echoes" - moments from their lives that become findable IRL.

### Echo Content

```json
{
  "echo_id": "ECHO_NPC0001_T50000",
  "arweave_tx": "abc123...",
  "npc": {
    "id": "npc_0001",
    "name": "Charlie",
    "canonical_image_tx": "def456..."
  },
  "content": {
    "text": "Rain washes nothing clean here. Met Felix tonight.",
    "mood": "contemplative",
    "generated_image_tx": "ghi789..."
  },
  "location": {
    "sim_location": "neon_bar",
    "real_world": { "lat": 40.7580, "lng": -73.9855 }
  }
}
```

### Arweave Tags for GeoEchoes App Discovery

```lua
{
    { name = "App-Name", value = "AO-World-Engine" },
    { name = "Type", value = "geoecho" },
    { name = "Layer-ID", value = "layer_00_testnet" },
    { name = "NPC-ID", value = "npc_0001" },
    { name = "Geo-Lat", value = "40.7580" },
    { name = "Geo-Lng", value = "-73.9855" },
    { name = "City", value = "nyc" }
}
```

---

## 4. Deployment Tiers

| Tier | NPCs | Purpose | Cost |
|------|------|---------|------|
| Testnet | 800 | Validate layers work | ~$0.01 |
| Alpha | 10,000 | Live demo, GeoEchoes testing | ~$1-5 |
| Production | 10M | Full NYC simulation | ~$10-100 |

---

## 5. Licensing Requirements

**Add to LICENSE.md:**

Any world created with AO World Engine MUST:
1. Register with Layer Registry
2. Enable cross-layer echo bleed
3. Respect existing geo-claims
4. Link to shared codec for interoperability

Forks may modify the engine but must connect to Layer Registry for official multiverse membership.

---

## 6. Implementation Phases

### Phase 1: Testnet with Layers (NOW)
- [ ] Create `layer_registry.lua`
- [ ] Add geo-claim validation
- [ ] Deploy 800 NPCs to AO testnet
- [ ] Verify layer bleed works

### Phase 2: GeoEcho Generation
- [ ] Add echo generation to NPCs
- [ ] Connect Gemini for images
- [ ] Upload echoes with proper tags

### Phase 3: Multi-City
- [ ] City claiming UI
- [ ] Allow Philadelphia, Tokyo, etc.
- [ ] Inter-city echo propagation

### Phase 4: Scale
- [ ] 10M+ NPCs
- [ ] Shard districts
- [ ] Production NYC

---

## Technical Files

```
ao-processes/
├── layer_registry.lua      [NEW] Master multiverse coordinator
├── world.lua               [EXISTS] Per-world coordinator  
├── district.lua            [EXISTS] NPC management
├── echo_generator.lua      [NEW] Auto-creates GeoEchoes
├── layer_event_bus.lua     [EXISTS] Cross-layer messaging
└── geo_claim_validator.lua [NEW] Validates city claims
```
