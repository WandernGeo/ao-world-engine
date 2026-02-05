# City Simulation Research: Interface & Implementation Patterns

> Deep analysis of 4 city simulation repositories for applicable patterns in AO World Engine.

## Overview

| Repository | Tech Stack | Focus Area | Relevance |
|------------|-----------|------------|-----------|
| [IsoCity](https://github.com/amilich/isometric-city) | Next.js, TypeScript, Canvas | Isometric rendering, Traffic/Pedestrian | **HIGH** - Same stack |
| [Egregoria](https://github.com/Uriopass/Egregoria) | Rust, ECS | Agent-based simulation | **HIGH** - Agent patterns |
| [Micropolis](https://github.com/SimHacker/micropolis) | C, TCL/Tk | Classic city sim logic | **MEDIUM** - Simulation formulas |
| [CSM](https://github.com/CitiesSkylinesMultiplayer/CSM) | C#, Unity | Multiplayer sync | **MEDIUM** - Network patterns |

---

## 1. IsoCity (amilich/isometric-city)

### Key Features
- **Isometric Rendering Engine**: Custom `CanvasIsometricGrid` with depth sorting, layer management
- **Traffic System**: Autonomous vehicles (cars, trains, planes, seaplanes)
- **Pedestrian System**: Pathfinding and crowd simulation
- **Economy & Resources**: Zoning (Residential, Commercial, Industrial), city growth logic
- **State Management**: Save/Load for multiple cities

### Architecture Patterns

#### Isometric Grid System
```typescript
// Isometric coordinate conversion
interface IsometricGrid {
  tileWidth: number;
  tileHeight: number;
  
  // Convert screen coords to tile coords
  screenToTile(x: number, y: number): { tileX: number, tileY: number };
  
  // Convert tile coords to screen coords
  tileToScreen(tileX: number, tileY: number): { x: number, y: number };
  
  // Depth sorting for proper occlusion
  sortByDepth(entities: Entity[]): Entity[];
}
```

#### Traffic Vehicle Interface
```typescript
interface Vehicle {
  id: string;
  type: 'car' | 'train' | 'plane' | 'seaplane';
  position: { x: number, y: number };
  velocity: { vx: number, vy: number };
  destination?: { x: number, y: number };
  path?: PathNode[];
  
  // Autonomous behavior
  update(deltaTime: number): void;
  findPath(to: Position): PathNode[];
  avoidCollision(others: Vehicle[]): void;
}
```

#### Pedestrian Crowd Simulation
```typescript
interface Pedestrian {
  id: string;
  position: { x: number, y: number };
  destination?: { x: number, y: number };
  speed: number;
  
  // Crowd behavior
  separationForce(neighbors: Pedestrian[]): Vector2;
  alignmentForce(neighbors: Pedestrian[]): Vector2;
  cohesionForce(neighbors: Pedestrian[]): Vector2;
  
  // Steering
  seek(target: Position): Vector2;
  arrive(target: Position): Vector2;
}
```

### Implementation for AO World Engine

```typescript
// Applicable pattern: Canvas-based NPC movement visualization
interface NPCMovementRenderer {
  canvas: CanvasRenderingContext2D;
  npcs: Map<string, NPCRenderState>;
  buildings: Map<string, BuildingRenderState>;
  
  // Render loop
  render(): void {
    // Clear canvas
    this.canvas.clearRect(0, 0, width, height);
    
    // Sort by depth (y-position for isometric effect)
    const sorted = [...this.npcs.values()].sort((a, b) => a.y - b.y);
    
    // Render each NPC
    for (const npc of sorted) {
      this.renderNPC(npc);
      this.renderPath(npc.currentPath);
    }
  }
}
```

---

## 2. Egregoria (Uriopass/Egregoria)

### Key Features
- **Individual Thought Models**: Each agent has unique decision-making
- **Grid-free Building**: No tile constraints
- **Logistics Simulation**: Supply chains, transportation
- **ECS Architecture**: Entity-Component-System for performance

### Architecture Patterns

#### Agent Thought Model (Rust -> TypeScript adaptation)
```typescript
// Agent decision-making system
interface AgentBrain {
  needs: {
    hunger: number;      // 0-100
    rest: number;        // 0-100
    social: number;      // 0-100
    money: number;       // 0-100
    entertainment: number;
  };
  
  // Personality affects decisions
  personality: {
    extroversion: number;   // -1 to 1
    conscientiousness: number;
    agreeableness: number;
  };
  
  // Decide next action based on needs and personality
  decideAction(world: WorldState): AgentAction;
  
  // Update needs over time
  tickNeeds(deltaTime: number): void;
}

type AgentAction = 
  | { type: 'work', destination: BuildingId }
  | { type: 'eat', venue: BuildingId }
  | { type: 'sleep', home: BuildingId }
  | { type: 'socialize', target: AgentId }
  | { type: 'idle' };
```

#### ECS Pattern for Scalability
```typescript
// Entity-Component-System for 10K+ NPCs
interface ECSWorld {
  entities: Map<EntityId, Set<ComponentType>>;
  components: {
    position: Map<EntityId, Position>;
    velocity: Map<EntityId, Velocity>;
    needs: Map<EntityId, AgentNeeds>;
    schedule: Map<EntityId, Schedule>;
    family: Map<EntityId, FamilyRelations>;
  };
  
  // Systems run on components
  systems: {
    movement: (entities: EntityId[], dt: number) => void;
    needsDecay: (entities: EntityId[], dt: number) => void;
    decisionMaking: (entities: EntityId[]) => void;
    socialInteraction: (entities: EntityId[]) => void;
  };
}
```

#### Pathfinding for Grid-free World
```typescript
// Navigation mesh for non-grid pathfinding
interface NavMesh {
  polygons: NavPolygon[];
  graph: NavigationGraph;
  
  // Find path between any two points
  findPath(from: Vector2, to: Vector2): Vector2[];
  
  // Query walkable areas
  isWalkable(point: Vector2): boolean;
  nearestWalkable(point: Vector2): Vector2;
}
```

### Implementation for AO World Engine

```typescript
// Applicable pattern: Need-based NPC behavior
class NPCBehaviorSystem {
  private world: SimulationWorld;
  
  // Run behavior decisions every simulation tick
  tick(deltaTime: number): void {
    for (const npc of this.world.npcs) {
      // Decay needs over time
      npc.needs.hunger -= deltaTime * 0.01;
      npc.needs.energy -= deltaTime * 0.02;
      npc.needs.social -= deltaTime * 0.005;
      
      // If any need is critical, prioritize it
      if (npc.needs.hunger < 20 && !npc.currentAction) {
        npc.setAction({ type: 'eat', venue: this.findNearestRestaurant(npc) });
      } else if (npc.needs.energy < 15 && !npc.currentAction) {
        npc.setAction({ type: 'sleep', home: npc.homeBuilding });
      }
    }
  }
}
```

---

## 3. Micropolis (SimHacker/micropolis)

### Key Features
- **Classic SimCity Logic**: Proven simulation formulas from 1989
- **Zone Types**: Residential, Commercial, Industrial (RCI)
- **Infrastructure**: Power, roads, rails, water
- **Disaster System**: Random events affecting city

### Architecture Patterns

#### Zone Growth Model
```typescript
// Classic RCI demand model
interface RCIModel {
  residential: {
    demand: number;        // -100 to 100
    population: number;
    growthRate: number;
  };
  commercial: {
    demand: number;
    jobs: number;
    growthRate: number;
  };
  industrial: {
    demand: number;
    production: number;
    pollution: number;
  };
  
  // Calculate demand based on factors
  calculateDemand(): void {
    // Residential demand increases with jobs
    this.residential.demand += (this.commercial.jobs + this.industrial.jobs) * 0.1;
    // Commercial demand increases with population
    this.commercial.demand += this.residential.population * 0.05;
    // Industrial demand as base for economy
    this.industrial.demand += 5 - (this.industrial.pollution * 0.1);
  }
}
```

#### Power Grid Simulation
```typescript
// Power distribution using flood-fill
interface PowerGrid {
  tiles: PowerTile[][];
  powerPlants: PowerPlant[];
  
  // Flood-fill power from plants
  distributePower(): void {
    // Reset all tiles to unpowered
    for (const row of this.tiles) {
      for (const tile of row) {
        tile.powered = false;
      }
    }
    
    // BFS from each power plant
    for (const plant of this.powerPlants) {
      this.floodFillPower(plant.x, plant.y, plant.capacity);
    }
  }
  
  floodFillPower(x: number, y: number, remaining: number): void {
    // Spread power through connected tiles
  }
}
```

### Implementation for AO World Engine

```typescript
// Applicable: Building zone influence on NPCs
interface BuildingInfluence {
  building: Building;
  type: 'residential' | 'commercial' | 'industrial' | 'entertainment';
  
  // Range of influence on nearby NPCs
  influenceRadius: number;
  
  // Effect on NPC needs when nearby
  needsModifier: {
    hunger?: number;      // Restaurants reduce hunger
    entertainment?: number; // Entertainment venues
    social?: number;      // Social spaces
    money?: number;       // Workplaces increase money
  };
  
  // Capacity and current occupancy
  capacity: number;
  currentOccupants: NPCId[];
}
```

---

## 4. CSM - Cities: Skylines Multiplayer

### Key Features
- **Real-time Sync**: Multiple players in same city
- **Client-Server Architecture**: Authoritative server
- **State Synchronization**: Efficient delta updates
- **Conflict Resolution**: Handling simultaneous edits

### Architecture Patterns

#### Network Synchronization
```typescript
// State synchronization pattern
interface SyncManager {
  // Server sends authoritative state
  serverState: GameState;
  
  // Client predicts locally for responsiveness
  clientPrediction: GameState;
  
  // Reconciliation when server confirms
  reconcile(serverUpdate: StateUpdate): void {
    // Apply server's authoritative changes
    this.serverState = applyUpdate(this.serverState, serverUpdate);
    
    // Re-predict client state from server base
    this.clientPrediction = clone(this.serverState);
    for (const pendingAction of this.pendingActions) {
      this.clientPrediction = applyAction(this.clientPrediction, pendingAction);
    }
  }
}
```

#### Event-based City Updates
```typescript
// City modification events for multiplayer
type CityEvent = 
  | { type: 'building_placed', building: Building, player: PlayerId }
  | { type: 'road_built', from: Position, to: Position, player: PlayerId }
  | { type: 'zone_changed', area: BoundingBox, newZone: ZoneType }
  | { type: 'npc_action', npcId: NPCId, action: NPCAction };

interface EventLog {
  events: CityEvent[];
  
  // Apply events to city state
  apply(state: CityState, event: CityEvent): CityState;
  
  // Compact old events into snapshots
  createSnapshot(upToEvent: number): CitySnapshot;
}
```

### Implementation for AO World Engine

```typescript
// Applicable: Event sourcing for simulation state
interface SimulationEventStore {
  // All events that have occurred
  events: SimulationEvent[];
  
  // Current materialized state
  currentState: SimulationState;
  
  // Apply event and store
  apply(event: SimulationEvent): void {
    this.events.push(event);
    this.currentState = this.reducer(this.currentState, event);
  }
  
  // Time-travel: reconstruct state at any point
  getStateAt(eventIndex: number): SimulationState {
    let state = this.initialState;
    for (let i = 0; i <= eventIndex; i++) {
      state = this.reducer(state, this.events[i]);
    }
    return state;
  }
  
  // Persist to Arweave
  persistToArweave(): Promise<string> {
    return uploadToArweave({
      events: this.events,
      snapshot: this.currentState
    });
  }
}
```

---

## Recommended Implementations for AO World Engine

### Priority 1: Canvas Isometric Grid (from IsoCity)
```typescript
// components/IsometricCanvas.tsx
export function IsometricCanvas({ npcs, buildings, zoom, pan }) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [canvasSize, setCanvasSize] = useState({ width: 0, height: 0 });
  
  // Dynamic canvas sizing (already implemented in graph)
  useEffect(() => {
    const observer = new ResizeObserver(entries => {
      const { width, height } = entries[0].contentRect;
      setCanvasSize({ width, height });
    });
    observer.observe(canvasRef.current!.parentElement!);
    return () => observer.disconnect();
  }, []);
  
  // Isometric render loop
  useEffect(() => {
    const ctx = canvasRef.current?.getContext('2d');
    if (!ctx) return;
    
    // Sort by depth (isometric: y + x/2)
    const sorted = [...npcs].sort((a, b) => 
      (a.y + a.x * 0.5) - (b.y + b.x * 0.5)
    );
    
    // Render with isometric projection
    ctx.clearRect(0, 0, canvasSize.width, canvasSize.height);
    for (const npc of sorted) {
      const screenX = (npc.x - npc.y) * TILE_WIDTH * 0.5 * zoom + pan.x;
      const screenY = (npc.x + npc.y) * TILE_HEIGHT * 0.5 * zoom + pan.y;
      renderNPC(ctx, npc, screenX, screenY);
    }
  }, [npcs, zoom, pan, canvasSize]);
  
  return <canvas ref={canvasRef} width={canvasSize.width} height={canvasSize.height} />;
}
```

### Priority 2: Agent Needs System (from Egregoria)
```typescript
// api/behavior_system.py
class AgentNeedsSystem:
    """Egregoria-inspired needs-based decision making."""
    
    def __init__(self, npc: NPC):
        self.npc = npc
        self.needs = {
            'hunger': 80,
            'energy': 80,
            'social': 60,
            'money': 50,
            'entertainment': 50
        }
    
    def tick(self, delta_hours: float):
        # Decay needs over time
        self.needs['hunger'] -= delta_hours * 4
        self.needs['energy'] -= delta_hours * 3
        self.needs['social'] -= delta_hours * 1
        self.needs['entertainment'] -= delta_hours * 2
        
        # Clamp values
        for need in self.needs:
            self.needs[need] = max(0, min(100, self.needs[need]))
    
    def decide_action(self, world_state: WorldState) -> Action:
        # Find most urgent need
        urgent = min(self.needs.items(), key=lambda x: x[1])
        
        if urgent[0] == 'hunger' and urgent[1] < 30:
            return EatAction(venue=world_state.nearest_restaurant(self.npc))
        elif urgent[0] == 'energy' and urgent[1] < 20:
            return SleepAction(home=self.npc.home)
        elif urgent[0] == 'social' and urgent[1] < 25:
            return SocializeAction(target=self.find_friend())
        # ... more actions
        
        return IdleAction()
```

### Priority 3: Event Sourcing for Arweave (from CSM)
```typescript
// lib/eventStore.ts
interface SimulationEvent {
  timestamp: number;
  type: string;
  payload: unknown;
  npcId?: string;
}

export class SimulationEventStore {
  private events: SimulationEvent[] = [];
  private state: SimulationState;
  
  constructor(initial: SimulationState) {
    this.state = initial;
  }
  
  dispatch(event: SimulationEvent): void {
    this.events.push(event);
    this.state = this.reduce(this.state, event);
  }
  
  // Create Arweave-ready bundle
  toArweaveBundle(sinceTimestamp?: number): object {
    const events = sinceTimestamp 
      ? this.events.filter(e => e.timestamp > sinceTimestamp)
      : this.events;
    
    return {
      schemaVersion: '2.0.0',
      bundleType: 'simulation_events',
      timestamp: Date.now(),
      eventCount: events.length,
      events,
      stateSnapshot: this.state
    };
  }
  
  // Upload to Arweave
  async persist(): Promise<string> {
    const bundle = this.toArweaveBundle();
    return await uploadToArweave(bundle);
  }
}
```

---

## Summary: What to Implement

| Pattern | Source | Priority | Effort |
|---------|--------|----------|--------|
| Isometric Canvas Rendering | IsoCity | HIGH | 2 days |
| Agent Needs System | Egregoria | HIGH | 3 days |
| Crowd/Pedestrian Simulation | IsoCity | MEDIUM | 2 days |
| Event Sourcing | CSM | MEDIUM | 1 day |
| Zone Influence System | Micropolis | LOW | 2 days |
| Power Grid Simulation | Micropolis | LOW | 1 day |

## References

- IsoCity: https://github.com/amilich/isometric-city
- Egregoria: https://github.com/Uriopass/Egregoria
- Micropolis: https://github.com/SimHacker/micropolis
- CSM: https://github.com/CitiesSkylinesMultiplayer/CSM
- Egregoria Devblog: http://douady.paris/blog/index.html
- Micropolis Documentation: https://github.com/SimHacker/micropolis/blob/wiki/InsideTheSimulator.md
