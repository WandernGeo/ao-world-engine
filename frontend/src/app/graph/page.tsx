'use client';

import { useState, useEffect, useCallback, Suspense } from 'react';
import Link from 'next/link';
import { Button } from '@/components/ui/button';
import dynamic from 'next/dynamic';

// Dynamically import Graph3D to avoid SSR issues with Three.js
const Graph3D = dynamic(() => import('@/components/Graph3D'), {
    ssr: false,
    loading: () => (
        <div className="flex-1 flex items-center justify-center bg-zinc-950">
            <div className="text-cyan-400 font-mono animate-pulse">Loading 3D Graph...</div>
        </div>
    ),
});

// Entity types
type EntityType = 'npc' | 'building' | 'faction' | 'lore' | 'item' | 'location' | 'event';

interface Entity {
    id: string;
    name: string;
    type: EntityType;
    x: number;
    y: number;
    z: number;
    vx: number;
    vy: number;
    vz: number;
    properties?: Record<string, string>;
}

interface Relationship {
    source: string;
    target: string;
    type: string;
}

interface APINPC {
    id: string;
    name: string;
    archetype: string;
    faction: string;
    home?: string;
    workplace?: string;
    family?: {
        spouse_id?: string | null;
        parent_ids?: string[];
        sibling_ids?: string[];
        children_ids?: string[];
    };
}

interface APIBuilding {
    id: string;
    name: string;
    type: string;
}

const CLOUD_API = 'https://ao-world-engine-api-1071951656531.us-central1.run.app';
const LOCAL_API = 'http://localhost:8081';

async function getApiBase(): Promise<string> {
    try {
        const res = await fetch(`${LOCAL_API}/health`, { method: 'GET', signal: AbortSignal.timeout(1000) });
        if (res.ok) return LOCAL_API;
    } catch { /* ignore */ }
    return CLOUD_API;
}

// Entity type colors
const TYPE_COLORS: Record<EntityType, string> = {
    npc: '#10b981',
    building: '#8b5cf6',
    faction: '#f59e0b',
    lore: '#06b6d4',
    item: '#ec4899',
    location: '#6366f1',
    event: '#ef4444',
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

// Fetch knowledge graph from API
async function fetchKnowledgeGraphFromAPI(): Promise<{ entities: Entity[], relationships: Relationship[] } | null> {
    try {
        const API_BASE = await getApiBase();
        const [npcRes, buildingRes] = await Promise.all([
            fetch(`${API_BASE}/api/npcs/all?limit=800`),
            fetch(`${API_BASE}/api/buildings`),
        ]);

        if (!npcRes.ok || !buildingRes.ok) return null;

        const npcData = await npcRes.json();
        const buildingData = await buildingRes.json();

        const apiNPCs: APINPC[] = npcData.npcs || [];
        const apiBuildings: APIBuilding[] = buildingData.buildings || [];

        const entities: Entity[] = [];
        const relationships: Relationship[] = [];

        // Get unique factions
        const factionSet = new Set<string>();
        apiNPCs.forEach(n => { if (n.faction) factionSet.add(n.faction); });
        const factions = Array.from(factionSet);

        // Create FACTION HUBS - spread far apart in a ring
        const factionPositions = new Map<string, { x: number, y: number, z: number }>();
        factions.forEach((name, i) => {
            const theta = (i * Math.PI * 2) / factions.length;
            const hubRadius = 600;  // Large separation between hubs
            const pos = {
                x: Math.cos(theta) * hubRadius,
                y: Math.sin(theta) * hubRadius,
                z: ((i % 3) - 1) * 150,  // Varied Z levels
            };
            factionPositions.set(name, pos);
            entities.push({
                id: `faction_${name}`,
                name: name.charAt(0).toUpperCase() + name.slice(1),
                type: 'faction',
                x: pos.x,
                y: pos.y,
                z: pos.z,
                vx: 0, vy: 0, vz: 0,
            });
        });

        // Create building entities - in center
        apiBuildings.slice(0, 20).forEach((b, i) => {
            const theta = (i * Math.PI * 2) / 20;
            const radius = 200;
            entities.push({
                id: b.id,
                name: b.name,
                type: 'building',
                x: Math.cos(theta) * radius,
                y: Math.sin(theta) * radius,
                z: (Math.random() - 0.5) * 100,
                vx: 0, vy: 0, vz: 0,
                properties: { buildingType: b.type },
            });
        });

        // Group NPCs by faction for counting
        const npcsByFaction = new Map<string, number>();
        apiNPCs.forEach(n => {
            const f = n.faction || 'unknown';
            npcsByFaction.set(f, (npcsByFaction.get(f) || 0) + 1);
        });
        const factionNpcIndex = new Map<string, number>();

        // Create NPC entities - ORBITING their faction hub
        apiNPCs.forEach((n, i) => {
            const faction = n.faction || 'unknown';
            const factionPos = factionPositions.get(faction) || { x: 0, y: 0, z: 0 };

            // Get this NPC's index within faction
            const idx = factionNpcIndex.get(faction) || 0;
            factionNpcIndex.set(faction, idx + 1);

            // Spiral around faction hub
            const count = npcsByFaction.get(faction) || 100;
            const angle = (idx / count) * Math.PI * 6;  // Multiple rotations
            const orbitRadius = 50 + (idx / count) * 150;  // Spiral outward

            entities.push({
                id: n.id,
                name: n.name,
                type: 'npc',
                x: factionPos.x + Math.cos(angle) * orbitRadius,
                y: factionPos.y + Math.sin(angle) * orbitRadius,
                z: factionPos.z + (Math.random() - 0.5) * 100,
                vx: 0, vy: 0, vz: 0,
                properties: { archetype: n.archetype, faction: n.faction },
            });

            // Faction relationship
            if (n.faction) {
                relationships.push({ source: n.id, target: `faction_${n.faction}`, type: 'member_of' });
            }

            // Family relationships
            if (n.family) {
                if (n.family.spouse_id && n.id < n.family.spouse_id) {
                    relationships.push({ source: n.id, target: n.family.spouse_id, type: 'spouse' });
                }
                if (n.family.children_ids) {
                    n.family.children_ids.forEach(childId => {
                        relationships.push({ source: n.id, target: childId, type: 'parent_of' });
                    });
                }
                if (n.family.sibling_ids) {
                    n.family.sibling_ids.forEach(sibId => {
                        if (n.id < sibId) {
                            relationships.push({ source: n.id, target: sibId, type: 'sibling' });
                        }
                    });
                }
            }
        });

        console.log(`Loaded: ${entities.length} entities, ${relationships.length} relationships`);
        return { entities, relationships };
    } catch (error) {
        console.error('Failed to fetch knowledge graph:', error);
        return null;
    }
}

// Fallback data generator
function generateFallbackGraph(): { entities: Entity[], relationships: Relationship[] } {
    const entities: Entity[] = [];
    const relationships: Relationship[] = [];

    const factions = ['Resistance', 'Temple Authority', 'Civilian', 'Criminal Syndicate', 'Tech Guild'];
    factions.forEach((name, i) => {
        const theta = (i * Math.PI * 2) / factions.length;
        entities.push({
            id: `faction_${i}`,
            name,
            type: 'faction',
            x: Math.cos(theta) * 300,
            y: Math.sin(theta) * 300,
            z: (Math.random() - 0.5) * 200,
            vx: 0, vy: 0, vz: 0,
        });
    });

    // Sample NPCs
    const npcs = [
        { name: 'Zero Chen', faction: 0, archetype: 'Leader' },
        { name: 'Charlie Reyes', faction: 0, archetype: 'Fighter' },
        { name: 'Kira Ōmura', faction: 2, archetype: 'Oracle' },
        { name: 'Felix Tanaka', faction: 2, archetype: 'Broker' },
        { name: 'Pixel', faction: 4, archetype: 'Hacker' },
    ];

    npcs.forEach((n, i) => {
        const theta = (i * 0.618 * Math.PI * 2) % (Math.PI * 2);
        entities.push({
            id: `npc_${i}`,
            name: n.name,
            type: 'npc',
            x: Math.cos(theta) * 150,
            y: Math.sin(theta) * 150,
            z: (Math.random() - 0.5) * 200,
            vx: 0, vy: 0, vz: 0,
            properties: { archetype: n.archetype },
        });
        relationships.push({ source: `npc_${i}`, target: `faction_${n.faction}`, type: 'member_of' });
    });

    return { entities, relationships };
}

export default function KnowledgeGraphPage() {
    const [data, setData] = useState<{ entities: Entity[], relationships: Relationship[] }>({ entities: [], relationships: [] });
    const [selectedEntity, setSelectedEntity] = useState<Entity | null>(null);
    const [filter, setFilter] = useState<EntityType | 'all'>('all');
    const [showFamilyOnly, setShowFamilyOnly] = useState(false);
    const [isSimulating, setIsSimulating] = useState(false);
    const [controlMode, setControlMode] = useState<'orbit' | 'fly'>('fly');
    const [stats, setStats] = useState({ entities: 0, relationships: 0, npcs: 0 });
    const [sidebarOpen, setSidebarOpen] = useState(false); // Mobile sidebar toggle

    // Load data
    useEffect(() => {
        const loadData = async () => {
            const apiData = await fetchKnowledgeGraphFromAPI();
            const d = apiData || generateFallbackGraph();
            setData(d);
            setStats({
                entities: d.entities.length,
                relationships: d.relationships.length,
                npcs: d.entities.filter(e => e.type === 'npc').length,
            });
        };
        loadData();
    }, []);

    const handleSelectEntity = useCallback((entity: Entity | null) => {
        setSelectedEntity(entity);
    }, []);

    const handleDoubleClickEntity = useCallback((entity: Entity) => {
        if (entity.type === 'npc') {
            window.location.href = `/npcs?npc=${encodeURIComponent(entity.name)}`;
        } else if (entity.type === 'building') {
            window.location.href = `/explore?building=${encodeURIComponent(entity.id)}`;
        }
    }, []);

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
            <header className="fixed top-0 left-0 right-0 h-14 bg-black/80 backdrop-blur border-b border-zinc-800 z-50 flex items-center px-4">
                {/* Mobile menu button */}
                <button
                    onClick={() => setSidebarOpen(!sidebarOpen)}
                    className="lg:hidden mr-3 p-2 text-cyan-400 hover:bg-zinc-800 rounded"
                >
                    <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
                    </svg>
                </button>
                <Link href="/" className="text-xl font-bold font-mono text-cyan-400 hover:text-white transition-colors truncate">
                    AO WORLD ENGINE
                </Link>
                <nav className="ml-8 hidden lg:flex gap-4">
                    <Link href="/explore" className="text-sm font-medium text-zinc-300 hover:text-white px-3 py-1.5 rounded transition-colors">
                        Explore
                    </Link>
                    <Link href="/npcs" className="text-sm font-medium text-zinc-300 hover:text-white px-3 py-1.5 rounded transition-colors">
                        NPCs
                    </Link>
                    <Link href="/chat" className="text-sm font-medium text-zinc-300 hover:text-white px-3 py-1.5 rounded transition-colors">
                        Chat
                    </Link>
                    <Link href="/graph" className="text-sm font-medium text-white px-3 py-1.5 rounded transition-colors bg-cyan-600/30">
                        Graph
                    </Link>
                </nav>
                <div className="ml-auto text-xs text-cyan-400 font-mono hidden md:block">
                    WebGL 3D • Click nodes to select • Drag to rotate
                </div>
            </header>

            <div className="pt-14 flex h-screen">
                {/* 3D Canvas */}
                <div className="flex-1 relative">
                    <Graph3D
                        entities={data.entities}
                        relationships={data.relationships}
                        selectedEntity={selectedEntity}
                        onSelectEntity={handleSelectEntity}
                        onDoubleClickEntity={handleDoubleClickEntity}
                        filter={filter}
                        showFamilyOnly={showFamilyOnly}
                        isSimulating={isSimulating}
                        controlMode={controlMode}
                    />

                    {/* Filter buttons */}
                    <div className="absolute top-4 left-4 flex gap-1 flex-wrap z-20 bg-zinc-900/90 backdrop-blur-sm p-2 rounded-lg border border-zinc-700">
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
                    <div className="absolute bottom-4 left-4 flex gap-2 items-center bg-zinc-900/80 p-2 rounded-lg border border-zinc-700 backdrop-blur-sm">
                        <Button
                            size="lg"
                            variant={isSimulating ? 'default' : 'outline'}
                            onClick={() => setIsSimulating(!isSimulating)}
                            className={`px-6 font-bold ${isSimulating
                                ? 'bg-gradient-to-r from-cyan-500 to-purple-500 shadow-lg shadow-cyan-500/50'
                                : 'border-cyan-500 text-cyan-400 hover:bg-cyan-500/20'}`}
                        >
                            {isSimulating ? '⏸ PAUSE' : '▶ PHYSICS'}
                        </Button>
                        <Button
                            size="sm"
                            variant={showFamilyOnly ? 'default' : 'outline'}
                            onClick={() => setShowFamilyOnly(!showFamilyOnly)}
                            className={showFamilyOnly ? 'bg-pink-600' : ''}
                        >
                            👨‍👩‍👧 Family
                        </Button>
                        <Button
                            size="sm"
                            variant={controlMode === 'fly' ? 'default' : 'outline'}
                            onClick={() => setControlMode(m => m === 'fly' ? 'orbit' : 'fly')}
                            className={controlMode === 'fly' ? 'bg-violet-600' : ''}
                            title="Fly: WASD/Arrows to move, mouse to look | Orbit: drag to rotate"
                        >
                            {controlMode === 'fly' ? '🚀 FLY' : '🔄 ORBIT'}
                        </Button>
                    </div>

                    <div className="absolute bottom-4 right-80 text-xs text-zinc-500">
                        {controlMode === 'fly'
                            ? 'WASD/Arrows: move • Mouse: look • Scroll: zoom • Click: select'
                            : 'Drag: rotate • Scroll: zoom • Click: select • Double-click: fly to'}
                    </div>
                </div>

                {/* Info Panel - Collapsible on mobile */}
                <div className={`fixed lg:relative top-14 right-0 bottom-0 w-80 p-4 border-l border-zinc-800 overflow-y-auto bg-zinc-950/95 backdrop-blur z-40 transform transition-transform duration-300 ${sidebarOpen ? 'translate-x-0' : 'translate-x-full lg:translate-x-0'}`}>
                    {/* Stats */}
                    <div className="mb-4 p-4 bg-gradient-to-r from-cyan-900/40 to-purple-900/40 rounded-lg border border-cyan-500/30">
                        <div className="text-sm text-cyan-400 font-mono mb-3 font-bold">KNOWLEDGE GRAPH</div>
                        <div className="grid grid-cols-3 gap-3 text-center">
                            <div>
                                <div className="text-3xl font-bold text-white">{stats.entities}</div>
                                <div className="text-xs text-zinc-400">Entities</div>
                            </div>
                            <div>
                                <div className="text-3xl font-bold text-white">{stats.relationships}</div>
                                <div className="text-xs text-zinc-400">Relations</div>
                            </div>
                            <div>
                                <div className="text-3xl font-bold text-white">{stats.npcs}</div>
                                <div className="text-xs text-zinc-400">NPCs</div>
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
                                <Button
                                    size="sm"
                                    className="w-full mt-3 bg-cyan-600 hover:bg-cyan-500 text-white"
                                    onClick={() => handleDoubleClickEntity(selectedEntity)}
                                >
                                    {selectedEntity.type === 'npc' ? '👤 View NPC Profile' :
                                        selectedEntity.type === 'building' ? '🏢 View Building' : '🔍 Explore'}
                                </Button>
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
