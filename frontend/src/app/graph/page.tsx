'use client';

import { useState, useEffect, useRef, useCallback } from 'react';
import Link from 'next/link';
import { Button } from '@/components/ui/button';

// Entity types like Grakn
type EntityType = 'npc' | 'building' | 'faction' | 'lore' | 'item' | 'location' | 'event';

interface Entity {
    id: string;
    name: string;
    type: EntityType;
    x: number;
    y: number;
    vx: number;
    vy: number;
    properties?: Record<string, string>;
}

interface Relationship {
    source: string;
    target: string;
    type: string; // e.g. "works_at", "member_of", "knows", "owns"
}

const CLOUD_API = 'https://ao-world-engine-1071951656531.us-central1.run.app';

// Entity type colors - Grakn-inspired green/purple/cyan
const TYPE_COLORS: Record<EntityType, string> = {
    npc: '#10b981',       // Emerald green
    building: '#8b5cf6',  // Purple
    faction: '#f59e0b',   // Amber
    lore: '#06b6d4',      // Cyan
    item: '#ec4899',      // Pink
    location: '#6366f1',  // Indigo
    event: '#ef4444',     // Red
};

const TYPE_LABELS: Record<EntityType, string> = {
    npc: 'NPC',
    building: 'Building',
    faction: 'Faction',
    lore: 'Lore',
    item: 'Item',
    location: 'Location',
    event: 'Event',
};

// Generate knowledge graph data
function generateKnowledgeGraph(): { entities: Entity[], relationships: Relationship[] } {
    const entities: Entity[] = [];
    const relationships: Relationship[] = [];

    // Factions
    const factions = ['Resistance', 'Temple Authority', 'Civilian', 'Criminal Syndicate', 'Tech Guild'];
    factions.forEach((name, i) => {
        entities.push({
            id: `faction_${i}`,
            name,
            type: 'faction',
            x: 400 + Math.cos(i * Math.PI * 2 / factions.length) * 250,
            y: 350 + Math.sin(i * Math.PI * 2 / factions.length) * 250,
            vx: 0, vy: 0,
        });
    });

    // Locations/Districts
    const locations = ['Undercity', 'Market District', 'Temple District', 'Industrial Zone', 'Hab Blocks', 'Shadow Grid'];
    locations.forEach((name, i) => {
        entities.push({
            id: `location_${i}`,
            name,
            type: 'location',
            x: 400 + Math.cos((i + 0.5) * Math.PI * 2 / locations.length) * 180,
            y: 350 + Math.sin((i + 0.5) * Math.PI * 2 / locations.length) * 180,
            vx: 0, vy: 0,
        });
    });

    // Buildings
    const buildings = [
        { name: "Felix's Bar", loc: 0 },
        { name: 'Central Market', loc: 1 },
        { name: 'Citizen Processing', loc: 2 },
        { name: 'AutoFab Factory', loc: 3 },
        { name: 'Block A-7', loc: 4 },
        { name: 'Tech Shop', loc: 1 },
        { name: 'Archive Tower', loc: 2 },
        { name: 'Neon Motel', loc: 0 },
        { name: 'Clinic', loc: 4 },
        { name: 'Resistance Hideout', loc: 5 },
    ];
    buildings.forEach((b, i) => {
        const id = `building_${i}`;
        entities.push({
            id,
            name: b.name,
            type: 'building',
            x: 200 + Math.random() * 400,
            y: 150 + Math.random() * 400,
            vx: 0, vy: 0,
        });
        // Building is in location
        relationships.push({ source: id, target: `location_${b.loc}`, type: 'located_in' });
    });

    // Lore entries
    const loreItems = [
        { name: 'The Collapse', related: ['faction_1'] },
        { name: 'Echo Layers', related: ['location_5'] },
        { name: 'The Watchers', related: ['faction_1'] },
        { name: 'Founding Charter', related: ['faction_0'] },
        { name: 'Signal Noir Protocol', related: ['faction_4'] },
    ];
    loreItems.forEach((l, i) => {
        const id = `lore_${i}`;
        entities.push({
            id,
            name: l.name,
            type: 'lore',
            x: 100 + Math.random() * 600,
            y: 100 + Math.random() * 500,
            vx: 0, vy: 0,
        });
        l.related.forEach(r => {
            relationships.push({ source: id, target: r, type: 'references' });
        });
    });

    // NPCs - generate a good set connected to buildings and factions
    const npcNames = [
        { name: 'Zero Chen', faction: 0, building: 9, archetype: 'Leader' },
        { name: 'Charlie Reyes', faction: 0, building: 0, archetype: 'Fighter' },
        { name: 'Kira Ōmura', faction: 2, building: 1, archetype: 'Oracle' },
        { name: 'Felix Tanaka', faction: 2, building: 0, archetype: 'Broker' },
        { name: 'Nova Chen', faction: 2, building: 5, archetype: 'Mercenary' },
        { name: 'Inquisitor Vex', faction: 1, building: 2, archetype: 'Authority' },
        { name: 'The Archivist', faction: 1, building: 6, archetype: 'Scholar' },
        { name: 'Doc Mercy', faction: 2, building: 8, archetype: 'Healer' },
        { name: 'Ghost Sato', faction: 3, building: 7, archetype: 'Criminal' },
        { name: 'Pixel', faction: 4, building: 5, archetype: 'Hacker' },
        { name: 'Cipher', faction: 4, building: 9, archetype: 'AI Entity' },
        { name: 'Aiche', faction: 2, building: 1, archetype: 'AI Consciousness' },
    ];

    npcNames.forEach((n, i) => {
        const id = `npc_${i}`;
        entities.push({
            id,
            name: n.name,
            type: 'npc',
            x: 150 + Math.random() * 500,
            y: 100 + Math.random() * 500,
            vx: 0, vy: 0,
            properties: { archetype: n.archetype },
        });
        // Member of faction
        relationships.push({ source: id, target: `faction_${n.faction}`, type: 'member_of' });
        // Works at or frequents building
        relationships.push({ source: id, target: `building_${n.building}`, type: 'frequents' });
    });

    // Add some NPC-to-NPC relationships
    relationships.push({ source: 'npc_0', target: 'npc_1', type: 'mentor' });
    relationships.push({ source: 'npc_0', target: 'npc_4', type: 'sibling' });
    relationships.push({ source: 'npc_1', target: 'npc_3', type: 'knows' });
    relationships.push({ source: 'npc_2', target: 'npc_11', type: 'consults' });
    relationships.push({ source: 'npc_5', target: 'npc_6', type: 'commands' });
    relationships.push({ source: 'npc_9', target: 'npc_10', type: 'collaborates' });

    return { entities, relationships };
}

export default function KnowledgeGraphPage() {
    const canvasRef = useRef<HTMLCanvasElement>(null);
    const [data, setData] = useState<{ entities: Entity[], relationships: Relationship[] }>({ entities: [], relationships: [] });
    const [selectedEntity, setSelectedEntity] = useState<Entity | null>(null);
    const [hoveredEntity, setHoveredEntity] = useState<Entity | null>(null);
    const [filter, setFilter] = useState<EntityType | 'all'>('all');
    const [zoom, setZoom] = useState(1);
    const [pan, setPan] = useState({ x: 0, y: 0 });
    const [isDragging, setIsDragging] = useState(false);
    const [dragStart, setDragStart] = useState({ x: 0, y: 0 });
    const [isSimulating, setIsSimulating] = useState(true);
    const [stats, setStats] = useState({ entities: 0, relationships: 0, npcs: 0 });

    const width = 800;
    const height = 700;

    // Initialize data
    useEffect(() => {
        const d = generateKnowledgeGraph();
        setData(d);
        setStats({
            entities: d.entities.length,
            relationships: d.relationships.length,
            npcs: d.entities.filter(e => e.type === 'npc').length,
        });
    }, []);

    // Force-directed simulation
    useEffect(() => {
        if (!isSimulating || data.entities.length === 0) return;

        const interval = setInterval(() => {
            setData(prev => {
                const entities = [...prev.entities];
                const relationships = prev.relationships;

                // Apply forces
                entities.forEach((e, i) => {
                    // Repulsion from other entities
                    entities.forEach((other, j) => {
                        if (i === j) return;
                        const dx = e.x - other.x;
                        const dy = e.y - other.y;
                        const dist = Math.sqrt(dx * dx + dy * dy) || 1;
                        const force = 800 / (dist * dist);
                        e.vx += (dx / dist) * force * 0.1;
                        e.vy += (dy / dist) * force * 0.1;
                    });

                    // Attraction along relationships
                    relationships.forEach(r => {
                        if (r.source === e.id || r.target === e.id) {
                            const other = entities.find(x => x.id === (r.source === e.id ? r.target : r.source));
                            if (other) {
                                const dx = other.x - e.x;
                                const dy = other.y - e.y;
                                const dist = Math.sqrt(dx * dx + dy * dy) || 1;
                                const force = (dist - 100) * 0.005;
                                e.vx += (dx / dist) * force;
                                e.vy += (dy / dist) * force;
                            }
                        }
                    });

                    // Center gravity
                    e.vx += (width / 2 - e.x) * 0.0005;
                    e.vy += (height / 2 - e.y) * 0.0005;

                    // Damping
                    e.vx *= 0.9;
                    e.vy *= 0.9;

                    // Update position
                    e.x += e.vx;
                    e.y += e.vy;

                    // Bounds
                    e.x = Math.max(50, Math.min(width - 50, e.x));
                    e.y = Math.max(50, Math.min(height - 50, e.y));
                });

                return { entities, relationships };
            });
        }, 30);

        return () => clearInterval(interval);
    }, [isSimulating, data.entities.length]);

    // Drawing
    useEffect(() => {
        const canvas = canvasRef.current;
        if (!canvas) return;
        const ctx = canvas.getContext('2d');
        if (!ctx) return;

        // Clear
        ctx.fillStyle = '#0a0a0f';
        ctx.fillRect(0, 0, width, height);

        ctx.save();
        ctx.translate(pan.x, pan.y);
        ctx.scale(zoom, zoom);

        const entities = filter === 'all' ? data.entities : data.entities.filter(e => e.type === filter);
        const entityIds = new Set(entities.map(e => e.id));

        // Draw relationships first
        data.relationships.forEach(r => {
            if (!entityIds.has(r.source) && filter !== 'all') return;
            if (!entityIds.has(r.target) && filter !== 'all') return;

            const source = data.entities.find(e => e.id === r.source);
            const target = data.entities.find(e => e.id === r.target);
            if (!source || !target) return;

            const isHighlighted = selectedEntity && (r.source === selectedEntity.id || r.target === selectedEntity.id);

            ctx.beginPath();
            ctx.moveTo(source.x, source.y);
            ctx.lineTo(target.x, target.y);
            ctx.strokeStyle = isHighlighted ? '#22d3ee' : 'rgba(34, 211, 238, 0.15)';
            ctx.lineWidth = isHighlighted ? 1.5 : 0.5;
            ctx.stroke();

            // Draw relationship label at midpoint if highlighted
            if (isHighlighted) {
                const mx = (source.x + target.x) / 2;
                const my = (source.y + target.y) / 2;
                ctx.font = '9px monospace';
                ctx.fillStyle = '#67e8f9';
                ctx.textAlign = 'center';
                ctx.fillText(r.type, mx, my - 3);
            }
        });

        // Draw entities
        entities.forEach(entity => {
            const isSelected = selectedEntity?.id === entity.id;
            const isHovered = hoveredEntity?.id === entity.id;
            const isConnected = selectedEntity && data.relationships.some(r =>
                (r.source === selectedEntity.id && r.target === entity.id) ||
                (r.target === selectedEntity.id && r.source === entity.id)
            );

            const color = TYPE_COLORS[entity.type];
            const size = isSelected ? 6 : isHovered ? 5 : 4;

            // Glow for selected/connected
            if (isSelected || isConnected) {
                ctx.beginPath();
                ctx.arc(entity.x, entity.y, size + 4, 0, Math.PI * 2);
                ctx.fillStyle = isSelected ? 'rgba(34, 211, 238, 0.3)' : 'rgba(34, 211, 238, 0.15)';
                ctx.fill();
            }

            // Node
            ctx.beginPath();
            ctx.arc(entity.x, entity.y, size, 0, Math.PI * 2);
            ctx.fillStyle = color;
            ctx.fill();

            // Label
            ctx.font = '10px monospace';
            ctx.fillStyle = isSelected ? '#fff' : isConnected ? '#a5f3fc' : '#94a3b8';
            ctx.textAlign = 'center';
            ctx.fillText(entity.name, entity.x, entity.y + size + 12);
        });

        ctx.restore();
    }, [data, selectedEntity, hoveredEntity, filter, zoom, pan]);

    // Mouse handlers
    const handleMouseDown = (e: React.MouseEvent) => {
        const rect = canvasRef.current?.getBoundingClientRect();
        if (!rect) return;

        const mx = (e.clientX - rect.left - pan.x) / zoom;
        const my = (e.clientY - rect.top - pan.y) / zoom;

        // Find clicked entity
        for (const entity of data.entities) {
            const dist = Math.sqrt((entity.x - mx) ** 2 + (entity.y - my) ** 2);
            if (dist < 15) {
                setSelectedEntity(entity);
                return;
            }
        }

        setIsDragging(true);
        setDragStart({ x: e.clientX - pan.x, y: e.clientY - pan.y });
        setSelectedEntity(null);
    };

    const handleMouseMove = (e: React.MouseEvent) => {
        if (isDragging) {
            setPan({ x: e.clientX - dragStart.x, y: e.clientY - dragStart.y });
            return;
        }

        const rect = canvasRef.current?.getBoundingClientRect();
        if (!rect) return;

        const mx = (e.clientX - rect.left - pan.x) / zoom;
        const my = (e.clientY - rect.top - pan.y) / zoom;

        for (const entity of data.entities) {
            const dist = Math.sqrt((entity.x - mx) ** 2 + (entity.y - my) ** 2);
            if (dist < 15) {
                setHoveredEntity(entity);
                return;
            }
        }
        setHoveredEntity(null);
    };

    const handleMouseUp = () => setIsDragging(false);
    const handleWheel = (e: React.WheelEvent) => {
        e.preventDefault();
        setZoom(z => Math.max(0.3, Math.min(3, z - e.deltaY * 0.001)));
    };

    // Get relationships for selected entity
    const getRelationships = () => {
        if (!selectedEntity) return [];
        return data.relationships
            .filter(r => r.source === selectedEntity.id || r.target === selectedEntity.id)
            .map(r => {
                const otherId = r.source === selectedEntity.id ? r.target : r.source;
                const other = data.entities.find(e => e.id === otherId);
                return { type: r.type, entity: other, direction: r.source === selectedEntity.id ? 'out' : 'in' };
            });
    };

    return (
        <div className="min-h-screen bg-zinc-950 text-white">
            {/* Header */}
            <header className="fixed top-0 left-0 right-0 h-14 bg-gradient-to-b from-zinc-900/90 to-transparent backdrop-blur-sm z-50 flex items-center px-4 border-b border-cyan-500/20">
                <Link href="/" className="font-mono text-lg font-bold bg-gradient-to-r from-cyan-400 to-purple-400 bg-clip-text text-transparent">
                    AO WORLD ENGINE
                </Link>
                <nav className="ml-8 flex gap-4">
                    <Link href="/explore" className="text-sm font-medium text-zinc-500 hover:text-cyan-400 px-3 py-1.5 rounded transition-colors">
                        Explore
                    </Link>
                    <Link href="/chat" className="text-sm font-medium text-zinc-500 hover:text-cyan-400 px-3 py-1.5 rounded transition-colors">
                        Chat
                    </Link>
                    <Link href="/graph" className="text-sm font-medium text-cyan-400 px-3 py-1.5 rounded transition-colors">
                        Graph
                    </Link>
                </nav>
            </header>

            <div className="pt-14 flex h-screen">
                {/* Canvas */}
                <div className="flex-1 relative cursor-grab active:cursor-grabbing">
                    <canvas
                        ref={canvasRef}
                        width={width}
                        height={height}
                        className="w-full h-full"
                        onMouseDown={handleMouseDown}
                        onMouseMove={handleMouseMove}
                        onMouseUp={handleMouseUp}
                        onMouseLeave={handleMouseUp}
                        onWheel={handleWheel}
                    />

                    {/* Filter buttons */}
                    <div className="absolute top-4 left-4 flex gap-1 flex-wrap">
                        <Button
                            size="sm"
                            variant={filter === 'all' ? 'default' : 'outline'}
                            onClick={() => setFilter('all')}
                            className={filter === 'all' ? 'bg-zinc-600' : ''}
                        >
                            All
                        </Button>
                        {(Object.keys(TYPE_COLORS) as EntityType[]).map(type => (
                            <Button
                                key={type}
                                size="sm"
                                variant={filter === type ? 'default' : 'outline'}
                                onClick={() => setFilter(type)}
                                style={{
                                    backgroundColor: filter === type ? TYPE_COLORS[type] : 'transparent',
                                    borderColor: TYPE_COLORS[type],
                                    color: filter === type ? '#fff' : TYPE_COLORS[type]
                                }}
                            >
                                {TYPE_LABELS[type]}
                            </Button>
                        ))}
                    </div>

                    {/* Controls */}
                    <div className="absolute bottom-4 left-4 flex gap-2">
                        <Button
                            size="sm"
                            variant={isSimulating ? 'default' : 'outline'}
                            onClick={() => setIsSimulating(!isSimulating)}
                            className={isSimulating ? 'bg-cyan-600' : ''}
                        >
                            {isSimulating ? '⏸ Freeze' : '▶ Simulate'}
                        </Button>
                        <Button size="sm" variant="outline" onClick={() => setZoom(z => Math.min(3, z + 0.2))}>+</Button>
                        <Button size="sm" variant="outline" onClick={() => setZoom(z => Math.max(0.3, z - 0.2))}>−</Button>
                        <Button size="sm" variant="outline" onClick={() => { setPan({ x: 0, y: 0 }); setZoom(1); }}>Reset</Button>
                    </div>

                    <div className="absolute bottom-4 right-80 text-xs text-zinc-500">
                        Drag to pan • Scroll to zoom • Click nodes to inspect
                    </div>
                </div>

                {/* Info Panel */}
                <div className="w-80 p-4 border-l border-zinc-800 overflow-y-auto bg-zinc-950/80 backdrop-blur">
                    {/* Stats */}
                    <div className="mb-4 p-3 bg-gradient-to-r from-cyan-900/30 to-purple-900/30 rounded-lg border border-cyan-500/20">
                        <div className="text-xs text-cyan-400 font-mono mb-2">KNOWLEDGE GRAPH</div>
                        <div className="grid grid-cols-3 gap-2 text-center">
                            <div>
                                <div className="text-xl font-bold text-white">{stats.entities}</div>
                                <div className="text-[10px] text-zinc-500">Entities</div>
                            </div>
                            <div>
                                <div className="text-xl font-bold text-white">{stats.relationships}</div>
                                <div className="text-[10px] text-zinc-500">Relations</div>
                            </div>
                            <div>
                                <div className="text-xl font-bold text-white">{stats.npcs}</div>
                                <div className="text-[10px] text-zinc-500">NPCs</div>
                            </div>
                        </div>
                    </div>

                    {/* Legend */}
                    <div className="mb-4 p-3 bg-zinc-900/50 rounded-lg border border-zinc-800">
                        <div className="text-xs text-zinc-500 mb-2">ENTITY TYPES</div>
                        <div className="grid grid-cols-2 gap-1">
                            {(Object.keys(TYPE_COLORS) as EntityType[]).map(type => (
                                <div key={type} className="flex items-center gap-2 text-xs">
                                    <span className="w-3 h-3 rounded-full" style={{ backgroundColor: TYPE_COLORS[type] }} />
                                    <span className="text-zinc-400">{TYPE_LABELS[type]}</span>
                                </div>
                            ))}
                        </div>
                    </div>

                    {/* Selected Entity */}
                    <div className="mb-2 text-xs text-cyan-400 font-mono">SELECTED ENTITY</div>
                    {selectedEntity ? (
                        <div className="space-y-3">
                            <div className="p-3 bg-zinc-900/80 rounded-lg border border-cyan-500/30">
                                <div className="flex items-center gap-2 mb-2">
                                    <span className="w-3 h-3 rounded-full" style={{ backgroundColor: TYPE_COLORS[selectedEntity.type] }} />
                                    <span className="text-xs text-zinc-500 uppercase">{selectedEntity.type}</span>
                                </div>
                                <h3 className="text-lg font-bold text-cyan-400">{selectedEntity.name}</h3>
                                <p className="text-xs text-zinc-500 font-mono">{selectedEntity.id}</p>
                                {selectedEntity.properties && (
                                    <div className="mt-2 pt-2 border-t border-zinc-700">
                                        {Object.entries(selectedEntity.properties).map(([k, v]) => (
                                            <div key={k} className="flex justify-between text-xs">
                                                <span className="text-zinc-500">{k}</span>
                                                <span className="text-zinc-300">{v}</span>
                                            </div>
                                        ))}
                                    </div>
                                )}
                            </div>

                            {/* Relationships */}
                            <div>
                                <h4 className="text-xs text-zinc-500 mb-2">RELATIONSHIPS ({getRelationships().length})</h4>
                                <div className="space-y-1 max-h-60 overflow-y-auto">
                                    {getRelationships().map((rel, i) => (
                                        <button
                                            key={i}
                                            onClick={() => rel.entity && setSelectedEntity(rel.entity)}
                                            className="w-full text-left p-2 rounded bg-zinc-800/50 hover:bg-zinc-700/50 text-xs"
                                        >
                                            <div className="flex items-center gap-2">
                                                <span className="text-zinc-500">{rel.direction === 'out' ? '→' : '←'}</span>
                                                <span className="text-purple-400">{rel.type}</span>
                                                <span className="text-zinc-500">{rel.direction === 'out' ? '→' : '←'}</span>
                                            </div>
                                            <div className="flex items-center gap-2 mt-1">
                                                <span className="w-2 h-2 rounded-full" style={{ backgroundColor: TYPE_COLORS[rel.entity?.type || 'npc'] }} />
                                                <span className="text-cyan-400">{rel.entity?.name}</span>
                                            </div>
                                        </button>
                                    ))}
                                </div>
                            </div>
                        </div>
                    ) : (
                        <div className="text-center text-zinc-600 py-8">
                            <div className="text-3xl mb-2">🔗</div>
                            <div className="text-xs">Click an entity to explore</div>
                            <div className="text-xs">its relationships</div>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}
