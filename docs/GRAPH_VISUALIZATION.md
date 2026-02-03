# 🔗 Graph Network Visualization

> Interactive force-directed graph showing NPC-Building relationships

## What It Does

The **Graph Network** view shows your world as a neural-network-style visualization:

- **Yellow squares** = Buildings
- **Colored circles** = NPCs (color = faction)
- **Green lines** = Home connections
- **Blue lines** = Work connections

## Controls

| Action | What It Does |
|--------|-------------|
| **Scroll** | Zoom in/out |
| **Click + Drag** | Pan around |
| **Click node** | Shows NPC profile or building info |

## Physics Simulation

The graph uses **force-directed physics** to create an organic, readable layout:

### How It Works

```
1. REPULSION: Nodes push away from each other
   - Prevents overlapping
   - Creates even spacing
   
2. ATTRACTION: Connected nodes pull toward each other
   - NPCs cluster near their home/work buildings
   - Related entities stay close
   
3. CENTERING: All nodes gently pulled toward center
   - Keeps the graph from drifting off-screen
   
4. DAMPING: Velocity decreases over time
   - Graph settles into stable layout
   - Prevents perpetual motion
```

### The Algorithm (Simplified)

```javascript
// For each node
node.velocity += repulsion_from_other_nodes
node.velocity += attraction_to_connected_nodes  
node.velocity += attraction_to_center

// Apply movement
node.position += node.velocity * 0.1

// Slow down (damping)
node.velocity *= 0.9
```

### Benefits

| Benefit | How |
|---------|-----|
| **Readable** | No manual layout needed - physics spreads nodes evenly |
| **Clustered** | NPCs group near their home/work buildings naturally |
| **Organic** | Looks like a living neural network |
| **Interactive** | Nodes settle as you watch |

## Use Cases

1. **Understand relationships** - See which NPCs share buildings
2. **Find clusters** - Identify tight-knit communities  
3. **Explore factions** - Colors show faction distribution
4. **Debug data** - Spot NPCs with missing home/work assignments

## Performance

- Limited to 50 NPCs for smooth animation
- Buildings always shown (they're anchor points)
- Physics runs every frame (~60fps)

## Future Improvements

- [ ] Show NPC-to-NPC relationships
- [ ] Add hobby nodes (diamonds)
- [ ] Drag individual nodes
- [ ] Filter by faction/building type
