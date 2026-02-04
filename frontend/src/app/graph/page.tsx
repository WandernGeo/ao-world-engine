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
    z: number; // 3D depth coordinate
    vx: number;
    vy: number;
    vz: number; // velocity in z
    properties?: Record<string, string>;
}

interface Relationship {
    source: string;
    target: string;
    type: string; // e.g. "works_at", "member_of", "knows", "owns"
}

interface APIBuilding {
    id: string;
    name: string;
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
        household_id?: string;
        marital_status?: string;
    };
    age?: number;
}

const CLOUD_API = 'https://ao-world-engine-1071951656531.us-central1.run.app';
const LOCAL_API = 'http://localhost:8081';

// Try localhost first, fall back to Cloud
async function getApiBase(): Promise<string> {
    try {
        const res = await fetch(`${LOCAL_API}/health`, { method: 'GET', signal: AbortSignal.timeout(1000) });
        if (res.ok) return LOCAL_API;
    } catch { /* ignore */ }
    return CLOUD_API;
}

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

// Fetch knowledge graph data from API
async function fetchKnowledgeGraphFromAPI(): Promise<{ entities: Entity[], relationships: Relationship[] } | null> {
    try {
        const API_BASE = await getApiBase();
        // Fetch NPCs and buildings from API
        const [npcRes, buildingRes] = await Promise.all([
            fetch(`${API_BASE}/api/npcs?limit=800`),  // Increased to 800 to show all NPCs
            fetch(`${API_BASE}/api/buildings`),
        ]);

        if (!npcRes.ok || !buildingRes.ok) return null;

        const npcData = await npcRes.json();
        const buildingData = await buildingRes.json();

        const apiNPCs: APINPC[] = npcData.npcs || [];
        const apiBuildings: APIBuilding[] = buildingData.buildings || [];

        const entities: Entity[] = [];
        const relationships: Relationship[] = [];

        // Extract unique factions from NPCs
        const factionSet = new Set<string>();
        apiNPCs.forEach((n: APINPC) => {
            if (n.faction) factionSet.add(n.faction);
        });
        const factions = Array.from(factionSet);

        // Create faction entities - on outer sphere shell
        factions.forEach((name, i) => {
            const theta = (i * Math.PI * 2) / factions.length;
            const phi = Math.PI / 3; // Upper hemisphere
            entities.push({
                id: `faction_${name}`,
                name: name.charAt(0).toUpperCase() + name.slice(1),
                type: 'faction',
                x: 600 + Math.sin(phi) * Math.cos(theta) * 400,
                y: 500 + Math.sin(phi) * Math.sin(theta) * 400,
                z: Math.cos(phi) * 300,
                vx: 0, vy: 0, vz: 0,
            });
        });

        // Create building entities (first 15) - spread in sphere
        apiBuildings.slice(0, 15).forEach((b: APIBuilding, i) => {
            const theta = (i * Math.PI * 2) / 15;
            const phi = Math.PI / 2 + (Math.random() - 0.5) * 0.5;
            entities.push({
                id: b.id,
                name: b.name,
                type: 'building',
                x: 600 + Math.sin(phi) * Math.cos(theta) * 350,
                y: 500 + Math.sin(phi) * Math.sin(theta) * 350,
                z: Math.cos(phi) * 250 + (Math.random() - 0.5) * 100,
                vx: 0, vy: 0, vz: 0,
                properties: { buildingType: b.type },
            });
        });

        // Create NPC entities and relationships - spread throughout sphere
        apiNPCs.forEach((n: APINPC, i) => {
            const theta = (i * 0.618 * Math.PI * 2) % (Math.PI * 2); // Golden angle
            const phi = Math.acos(1 - 2 * ((i % 100) / 100)); // Uniform sphere distribution
            const radius = 200 + Math.random() * 150;
            entities.push({
                id: n.id,
                name: n.name,
                type: 'npc',
                x: 600 + Math.sin(phi) * Math.cos(theta) * radius,
                y: 500 + Math.sin(phi) * Math.sin(theta) * radius,
                z: Math.cos(phi) * radius * 0.8,
                vx: 0, vy: 0, vz: 0,
                properties: { archetype: n.archetype, faction: n.faction },
            });

            // Relationship to faction
            if (n.faction) {
                relationships.push({ source: n.id, target: `faction_${n.faction}`, type: 'member_of' });
            }

            // Relationship to workplace/home building
            if (n.workplace && apiBuildings.find(b => b.id === n.workplace)) {
                relationships.push({ source: n.id, target: n.workplace, type: 'works_at' });
            }
            if (n.home && apiBuildings.find(b => b.id === n.home)) {
                relationships.push({ source: n.id, target: n.home, type: 'lives_at' });
            }

            // Family relationships
            if (n.family) {
                // Spouse relationship
                if (n.family.spouse_id && n.id < n.family.spouse_id) {  // Avoid duplicates
                    relationships.push({ source: n.id, target: n.family.spouse_id, type: 'spouse' });
                }
                // Parent-child relationships
                if (n.family.children_ids) {
                    n.family.children_ids.forEach(childId => {
                        relationships.push({ source: n.id, target: childId, type: 'parent_of' });
                    });
                }
                // Sibling relationships (only add if this NPC's ID is less to avoid duplicates)
                if (n.family.sibling_ids) {
                    n.family.sibling_ids.forEach(sibId => {
                        if (n.id < sibId) {
                            relationships.push({ source: n.id, target: sibId, type: 'sibling' });
                        }
                    });
                }
            }
        });

        console.log(`Knowledge graph loaded from API: ${entities.length} entities, ${relationships.length} relationships`);
        return { entities, relationships };
    } catch (error) {
        console.log('Failed to fetch knowledge graph from API:', error);
        return null;
    }
}

// Generate knowledge graph data (fallback)
function generateKnowledgeGraph(): { entities: Entity[], relationships: Relationship[] } {
    const entities: Entity[] = [];
    const relationships: Relationship[] = [];

    // Factions
    const factions = ['Resistance', 'Temple Authority', 'Civilian', 'Criminal Syndicate', 'Tech Guild'];
    factions.forEach((name, i) => {
        const theta = (i * Math.PI * 2) / factions.length;
        entities.push({
            id: `faction_${i}`,
            name,
            type: 'faction',
            x: 600 + Math.cos(theta) * 400,
            y: 500 + Math.sin(theta) * 400,
            z: (Math.random() - 0.5) * 300,
            vx: 0, vy: 0, vz: 0,
        });
    });

    // Locations/Districts
    const locations = ['Undercity', 'Market District', 'Temple District', 'Industrial Zone', 'Hab Blocks', 'Shadow Grid'];
    locations.forEach((name, i) => {
        const theta = ((i + 0.5) * Math.PI * 2) / locations.length;
        entities.push({
            id: `location_${i}`,
            name,
            type: 'location',
            x: 600 + Math.cos(theta) * 280,
            y: 500 + Math.sin(theta) * 280,
            z: (Math.random() - 0.5) * 200,
            vx: 0, vy: 0, vz: 0,
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
        const theta = (i * Math.PI * 2) / buildings.length;
        entities.push({
            id,
            name: b.name,
            type: 'building',
            x: 600 + Math.cos(theta) * (200 + Math.random() * 150),
            y: 500 + Math.sin(theta) * (200 + Math.random() * 150),
            z: (Math.random() - 0.5) * 250,
            vx: 0, vy: 0, vz: 0,
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
            x: 600 + (Math.random() - 0.5) * 500,
            y: 500 + (Math.random() - 0.5) * 400,
            z: (Math.random() - 0.5) * 300,
            vx: 0, vy: 0, vz: 0,
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
        const theta = (i * 0.618 * Math.PI * 2) % (Math.PI * 2); // Golden angle
        entities.push({
            id,
            name: n.name,
            type: 'npc',
            x: 600 + Math.cos(theta) * (150 + Math.random() * 200),
            y: 500 + Math.sin(theta) * (150 + Math.random() * 200),
            z: (Math.random() - 0.5) * 350,
            vx: 0, vy: 0, vz: 0,
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
    const [zoom, setZoom] = useState(1.0); // Start well zoomed in
    const [pan, setPan] = useState({ x: -800, y: -600 }); // Center on the graph cluster
    const [isDragging, setIsDragging] = useState(false);
    const [dragStart, setDragStart] = useState({ x: 0, y: 0 });
    const [isSimulating, setIsSimulating] = useState(true);
    const [stats, setStats] = useState({ entities: 0, relationships: 0, npcs: 0 });
    const [draggedNode, setDraggedNode] = useState<string | null>(null); // NEW: track dragged node
    const [autoRotate, setAutoRotate] = useState(false); // Auto-rotation toggle
    const [showFamilyOnly, setShowFamilyOnly] = useState(false); // Show only family relationships

    // 3D rotation state
    const [rotationX, setRotationX] = useState(0); // Rotation around X axis (tilt up/down)
    const [rotationY, setRotationY] = useState(0); // Rotation around Y axis (spin left/right)
    const [isRotating, setIsRotating] = useState(false); // Right-click drag to rotate
    const [rotateStart, setRotateStart] = useState({ x: 0, y: 0 });
    // Bouncy drag state - track mouse velocity for throw effect
    const lastDragPos = useRef<{ x: number; y: number; time: number }>({ x: 0, y: 0, time: 0 });

    const width = 2400; // Huge canvas for spread
    const height = 2000; // More vertical space

    // 3D projection helper - project 3D point to 2D
    const project3D = (x: number, y: number, z: number = 0) => {
        const centerX = width / 2;
        const centerY = height / 2;

        // Translate to center
        let px = x - centerX;
        let py = y - centerY;
        let pz = z;

        // Rotate around Y axis
        const cosY = Math.cos(rotationY);
        const sinY = Math.sin(rotationY);
        const rx = px * cosY - pz * sinY;
        const rz = px * sinY + pz * cosY;
        px = rx;
        pz = rz;

        // Rotate around X axis
        const cosX = Math.cos(rotationX);
        const sinX = Math.sin(rotationX);
        const ry = py * cosX - pz * sinX;
        pz = py * sinX + pz * cosX;
        py = ry;

        // Perspective projection with depth fade
        const perspective = 1200; // Deeper perspective
        const scale = Math.max(0.2, perspective / (perspective + pz));

        return {
            x: centerX + px * scale,
            y: centerY + py * scale,
            scale: scale,
            depth: pz // Keep track of depth for rendering order
        };
    };

    // Initialize data - try API first, fallback to generated
    useEffect(() => {
        const loadData = async () => {
            // Try to fetch from API first
            const apiData = await fetchKnowledgeGraphFromAPI();
            const d = apiData || generateKnowledgeGraph();
            setData(d);
            setStats({
                entities: d.entities.length,
                relationships: d.relationships.length,
                npcs: d.entities.filter(e => e.type === 'npc').length,
            });
        };
        loadData();
    }, []);

    // Force-directed simulation
    useEffect(() => {
        if (!isSimulating || data.entities.length === 0) return;

        const interval = setInterval(() => {
            setData(prev => {
                const entities = [...prev.entities];
                const relationships = prev.relationships;

                // Apply forces - bouncy spring physics in 3D!
                entities.forEach((e, i) => {
                    // Initialize z if undefined
                    if (e.z === undefined) e.z = (Math.random() - 0.5) * 600;
                    if (e.vz === undefined) e.vz = 0;

                    // Strong repulsion from other entities (3D)
                    entities.forEach((other, j) => {
                        if (i === j) return;
                        const dx = e.x - other.x;
                        const dy = e.y - other.y;
                        const dz = (e.z || 0) - (other.z || 0);
                        const dist = Math.sqrt(dx * dx + dy * dy + dz * dz) || 1;
                        const force = 2000 / (dist * dist); // Stronger repulsion
                        e.vx += (dx / dist) * force * 0.15;
                        e.vy += (dy / dist) * force * 0.15;
                        e.vz += (dz / dist) * force * 0.15;
                    });

                    // Bouncy spring attraction along relationships
                    relationships.forEach(r => {
                        if (r.source === e.id || r.target === e.id) {
                            const other = entities.find(x => x.id === (r.source === e.id ? r.target : r.source));
                            if (other) {
                                const dx = other.x - e.x;
                                const dy = other.y - e.y;
                                const dz = (other.z || 0) - (e.z || 0);
                                const dist = Math.sqrt(dx * dx + dy * dy + dz * dz) || 1;
                                const idealDist = 180; // Ideal spring length
                                const springForce = (dist - idealDist) * 0.008; // Bouncy spring
                                e.vx += (dx / dist) * springForce;
                                e.vy += (dy / dist) * springForce;
                                e.vz += (dz / dist) * springForce;
                            }
                        }
                    });

                    // Gentle center gravity (keeps sphere centered)
                    e.vx += (width / 2 - e.x) * 0.0003;
                    e.vy += (height / 2 - e.y) * 0.0003;
                    e.vz += (0 - (e.z || 0)) * 0.0001; // Gentle z centering

                    // Bouncy damping (less friction = more bounce)
                    e.vx *= 0.92;
                    e.vy *= 0.92;
                    e.vz *= 0.92;

                    // Update position
                    e.x += e.vx;
                    e.y += e.vy;
                    e.z = (e.z || 0) + e.vz;

                    // Soft bounds (bounce at edges)
                    if (e.x < 100) { e.x = 100; e.vx *= -0.5; }
                    if (e.x > width - 100) { e.x = width - 100; e.vx *= -0.5; }
                    if (e.y < 100) { e.y = 100; e.vy *= -0.5; }
                    if (e.y > height - 100) { e.y = height - 100; e.vy *= -0.5; }
                    if (e.z < -400) { e.z = -400; e.vz *= -0.5; }
                    if (e.z > 400) { e.z = 400; e.vz *= -0.5; }
                });

                return { entities, relationships };
            });
        }, 30);

        return () => clearInterval(interval);
    }, [isSimulating, data.entities.length]);

    // Auto-rotation effect
    useEffect(() => {
        if (!autoRotate) return;

        const interval = setInterval(() => {
            setRotationY(prev => prev + 0.01); // Slow continuous rotation
        }, 30);

        return () => clearInterval(interval);
    }, [autoRotate]);

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
        const familyTypes = ['spouse', 'parent_of', 'sibling'];
        data.relationships.forEach(r => {
            // Filter by showFamilyOnly
            if (showFamilyOnly && !familyTypes.includes(r.type)) return;

            if (!entityIds.has(r.source) && filter !== 'all') return;
            if (!entityIds.has(r.target) && filter !== 'all') return;

            const source = data.entities.find(e => e.id === r.source);
            const target = data.entities.find(e => e.id === r.target);
            if (!source || !target) return;

            const isHighlighted = selectedEntity && (r.source === selectedEntity.id || r.target === selectedEntity.id);
            const isFamily = familyTypes.includes(r.type);

            // Color by relationship type
            let edgeColor = 'rgba(34, 211, 238, 0.15)'; // Default cyan
            if (r.type === 'spouse') edgeColor = isHighlighted ? '#ec4899' : 'rgba(236, 72, 153, 0.4)'; // Pink
            else if (r.type === 'parent_of') edgeColor = isHighlighted ? '#22d3ee' : 'rgba(34, 211, 238, 0.4)'; // Cyan
            else if (r.type === 'sibling') edgeColor = isHighlighted ? '#f59e0b' : 'rgba(245, 158, 11, 0.4)'; // Amber
            else if (isHighlighted) edgeColor = '#22d3ee';

            // Apply 3D projection
            const srcProj = project3D(source.x, source.y);
            const tgtProj = project3D(target.x, target.y);

            ctx.beginPath();
            ctx.moveTo(srcProj.x, srcProj.y);
            ctx.lineTo(tgtProj.x, tgtProj.y);
            ctx.strokeStyle = edgeColor;
            ctx.lineWidth = isHighlighted ? 2 : (isFamily ? 1 : 0.5);
            ctx.stroke();

            // Draw relationship label at midpoint if highlighted
            if (isHighlighted) {
                const mx = (srcProj.x + tgtProj.x) / 2;
                const my = (srcProj.y + tgtProj.y) / 2;
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
            const baseSize = isSelected ? 6 : isHovered ? 5 : 4;

            // Apply 3D projection
            const proj = project3D(entity.x, entity.y);
            const size = Math.max(1, Math.abs(baseSize * proj.scale)); // Ensure positive radius

            // Glow for selected/connected
            if (isSelected || isConnected) {
                ctx.beginPath();
                ctx.arc(proj.x, proj.y, size + 4, 0, Math.PI * 2);
                ctx.fillStyle = isSelected ? 'rgba(34, 211, 238, 0.3)' : 'rgba(34, 211, 238, 0.15)';
                ctx.fill();
            }

            // Node
            ctx.beginPath();
            ctx.arc(proj.x, proj.y, size, 0, Math.PI * 2);
            ctx.fillStyle = color;
            ctx.fill();

            // Label (only if large enough to see)
            if (proj.scale > 0.5) {
                ctx.font = `${Math.round(10 * proj.scale)}px monospace`;
                ctx.fillStyle = isSelected ? '#fff' : isConnected ? '#a5f3fc' : '#94a3b8';
                ctx.textAlign = 'center';
                ctx.fillText(entity.name, proj.x, proj.y + size + 12);
            }
        });

        ctx.restore();
    }, [data, selectedEntity, hoveredEntity, filter, zoom, pan, showFamilyOnly, rotationX, rotationY]);

    // Mouse handlers - support node dragging and rotation
    const handleMouseDown = (e: React.MouseEvent) => {
        const rect = canvasRef.current?.getBoundingClientRect();
        if (!rect) return;

        // Right-click = start 3D rotation
        if (e.button === 2) {
            e.preventDefault();
            setIsRotating(true);
            setRotateStart({ x: e.clientX, y: e.clientY });
            setAutoRotate(false); // Stop auto-rotate when manually rotating
            return;
        }

        // Screen mouse position relative to canvas element
        const screenX = e.clientX - rect.left;
        const screenY = e.clientY - rect.top;

        // IMPORTANT: Account for CSS scaling of canvas (canvas is 2400x2000 but CSS scales it to fit)
        const scaleX = width / rect.width;
        const scaleY = height / rect.height;
        const canvasX = screenX * scaleX;
        const canvasY = screenY * scaleY;

        // Convert canvas coords to world coords (reverse the canvas transform)
        const worldMouseX = (canvasX - pan.x) / zoom;
        const worldMouseY = (canvasY - pan.y) / zoom;

        // Check if clicking on a node using PROJECTED coordinates (3D aware)
        // Sort by depth - front-most nodes (smallest depth/largest scale) first!
        const sortedEntities = [...data.entities]
            .map(entity => ({ entity, proj: project3D(entity.x, entity.y, entity.z || 0) }))
            .sort((a, b) => a.proj.depth - b.proj.depth); // Smaller depth = closer to viewer

        for (const { entity, proj } of sortedEntities) {
            const dist = Math.sqrt((proj.x - worldMouseX) ** 2 + (proj.y - worldMouseY) ** 2);
            const hitRadius = Math.max(25, 40 * proj.scale); // BIGGER hit radius for easier clicking
            if (dist < hitRadius) {
                setDraggedNode(entity.id);
                setSelectedEntity(entity);
                setIsSimulating(false); // Pause simulation while dragging
                return;
            }
        }

        // Not on a node - start panning
        setIsDragging(true);
        setDragStart({ x: e.clientX - pan.x, y: e.clientY - pan.y });
        setSelectedEntity(null);
    };

    const handleMouseMove = (e: React.MouseEvent) => {
        const rect = canvasRef.current?.getBoundingClientRect();
        if (!rect) return;

        // Handle 3D rotation with right-drag
        if (isRotating) {
            const dx = e.clientX - rotateStart.x;
            const dy = e.clientY - rotateStart.y;
            setRotationY(prev => prev + dx * 0.005);
            setRotationX(prev => Math.max(-Math.PI / 3, Math.min(Math.PI / 3, prev + dy * 0.005)));
            setRotateStart({ x: e.clientX, y: e.clientY });
            return;
        }

        const mx = (e.clientX - rect.left - pan.x) / zoom;
        const my = (e.clientY - rect.top - pan.y) / zoom;

        // If dragging a node, update its position
        if (draggedNode) {
            const now = Date.now();
            // Track velocity for bouncy throw
            const dt = Math.max(1, now - lastDragPos.current.time) / 1000;
            const throwVx = (mx - lastDragPos.current.x) / dt * 0.02; // Scale down for nice throw
            const throwVy = (my - lastDragPos.current.y) / dt * 0.02;
            lastDragPos.current = { x: mx, y: my, time: now };

            setData(prev => ({
                ...prev,
                entities: prev.entities.map(e =>
                    e.id === draggedNode
                        ? { ...e, x: mx, y: my, vx: throwVx, vy: throwVy } // Keep velocity for bounce!
                        : e
                )
            }));
            return;
        }

        // If panning the view
        if (isDragging) {
            setPan({ x: e.clientX - dragStart.x, y: e.clientY - dragStart.y });
            return;
        }

        // Hover detection using PROJECTED coordinates (3D aware)
        // Convert screen coords to canvas coords (accounting for CSS scaling)
        const hoverScreenX = e.clientX - rect.left;
        const hoverScreenY = e.clientY - rect.top;
        const scaleX = width / rect.width;
        const scaleY = height / rect.height;
        const hoverCanvasX = hoverScreenX * scaleX;
        const hoverCanvasY = hoverScreenY * scaleY;
        // Convert canvas coords to world coords
        const hoverWorldX = (hoverCanvasX - pan.x) / zoom;
        const hoverWorldY = (hoverCanvasY - pan.y) / zoom;

        // Sort by depth - front-most nodes first (same as click detection)
        const sortedForHover = [...data.entities]
            .map(entity => ({ entity, proj: project3D(entity.x, entity.y, entity.z || 0) }))
            .sort((a, b) => a.proj.depth - b.proj.depth);

        for (const { entity, proj } of sortedForHover) {
            const dist = Math.sqrt((proj.x - hoverWorldX) ** 2 + (proj.y - hoverWorldY) ** 2);
            const hitRadius = Math.max(25, 40 * proj.scale); // Match click detection radius
            if (dist < hitRadius) {
                setHoveredEntity(entity);
                // Change cursor to pointer when over a node
                if (canvasRef.current) canvasRef.current.style.cursor = 'pointer';
                return;
            }
        }
        setHoveredEntity(null);
        // Reset cursor when not over a node
        if (canvasRef.current) canvasRef.current.style.cursor = 'default';
    };

    const handleMouseUp = () => {
        // Apply throw velocity when releasing a dragged node
        if (draggedNode) {
            setIsSimulating(true); // Resume simulation to let it bounce!
        }
        setIsDragging(false);
        setDraggedNode(null);
        setIsRotating(false);
    };

    const handleContextMenu = (e: React.MouseEvent) => {
        e.preventDefault(); // Prevent context menu on right-click
    };

    // Double-click to navigate to NPC/building page
    const handleDoubleClick = (e: React.MouseEvent) => {
        const rect = canvasRef.current?.getBoundingClientRect();
        if (!rect) return;

        const screenX = e.clientX - rect.left;
        const screenY = e.clientY - rect.top;
        const worldMouseX = (screenX - pan.x) / zoom;
        const worldMouseY = (screenY - pan.y) / zoom;

        // Find clicked entity using depth-sorted projection
        const sortedEntities = [...data.entities]
            .map(entity => ({ entity, proj: project3D(entity.x, entity.y, entity.z || 0) }))
            .sort((a, b) => a.proj.depth - b.proj.depth);

        for (const { entity, proj } of sortedEntities) {
            const dist = Math.sqrt((proj.x - worldMouseX) ** 2 + (proj.y - worldMouseY) ** 2);
            const hitRadius = Math.max(25, 40 * proj.scale);
            if (dist < hitRadius) {
                // Navigate based on entity type
                if (entity.type === 'npc') {
                    window.location.href = `/npcs?npc=${encodeURIComponent(entity.name)}`;
                } else if (entity.type === 'building') {
                    window.location.href = `/explore?building=${encodeURIComponent(entity.id)}`;
                }
                return;
            }
        }
    };

    const handleWheel = (e: React.WheelEvent) => {
        e.preventDefault();
        const rect = canvasRef.current?.getBoundingClientRect();
        if (!rect) return;

        // Mouse position relative to canvas
        const mouseX = e.clientX - rect.left;
        const mouseY = e.clientY - rect.top;

        // Calculate new zoom
        const delta = e.deltaY * -0.001;
        const newZoom = Math.max(0.2, Math.min(3, zoom + delta));
        const zoomRatio = newZoom / zoom;

        // Adjust pan so zoom centers on mouse position
        const newPanX = mouseX - (mouseX - pan.x) * zoomRatio;
        const newPanY = mouseY - (mouseY - pan.y) * zoomRatio;

        setZoom(newZoom);
        setPan({ x: newPanX, y: newPanY });
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
            <header className="fixed top-0 left-0 right-0 h-14 bg-zinc-900 z-50 flex items-center px-4 border-b border-zinc-800">
                <Link href="/" className="font-mono text-lg font-bold text-cyan-400 tracking-wider">
                    AO WORLD ENGINE
                </Link>
                <nav className="ml-8 flex gap-4">
                    <Link href="/explore" className="text-sm font-medium text-zinc-300 hover:text-white px-3 py-1.5 rounded transition-colors">
                        Explore
                    </Link>
                    <Link href="/npcs" className="text-sm font-medium text-zinc-300 hover:text-white px-3 py-1.5 rounded transition-colors">
                        NPCs
                    </Link>
                    <Link href="/chat" className="text-sm font-medium text-zinc-300 hover:text-white px-3 py-1.5 rounded transition-colors">
                        Chat
                    </Link>
                    <Link href="/graph" className="text-sm font-medium text-white px-3 py-1.5 rounded transition-colors">
                        Graph
                    </Link>
                </nav>
            </header>

            <div className="pt-14 flex h-screen">
                {/* Canvas */}
                <div className={`flex-1 relative ${hoveredEntity ? 'cursor-pointer' : 'cursor-grab'} active:cursor-grabbing`}>
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
                        onContextMenu={handleContextMenu}
                        onDoubleClick={handleDoubleClick}
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

                    {/* Controls - prominent play button */}
                    <div className="absolute bottom-4 left-4 flex gap-2 flex-wrap items-center bg-zinc-900/80 p-2 rounded-lg border border-zinc-700 backdrop-blur-sm">
                        <Button
                            size="lg"
                            variant={isSimulating ? 'default' : 'outline'}
                            onClick={() => setIsSimulating(!isSimulating)}
                            className={`px-6 font-bold transition-all ${isSimulating
                                ? 'bg-gradient-to-r from-cyan-500 to-purple-500 shadow-lg shadow-cyan-500/50 animate-pulse'
                                : 'border-cyan-500 text-cyan-400 hover:bg-cyan-500/20'}`}
                        >
                            {isSimulating ? '⏸ PAUSE' : '▶ PLAY'}
                        </Button>
                        <Button
                            size="sm"
                            variant={showFamilyOnly ? 'default' : 'outline'}
                            onClick={() => setShowFamilyOnly(!showFamilyOnly)}
                            className={showFamilyOnly ? 'bg-pink-600' : ''}
                        >
                            {showFamilyOnly ? '👨‍👩‍👧 Family Only' : '👨‍👩‍👧 Show Family'}
                        </Button>
                        <div className="flex gap-1">
                            <Button size="sm" variant="outline" onClick={() => setZoom(z => Math.min(5, z + 0.1))}>+</Button>
                            <Button size="sm" variant="outline" onClick={() => setZoom(z => Math.max(0.1, z - 0.1))}>−</Button>
                        </div>
                        <Button size="sm" variant="outline" onClick={() => { setPan({ x: -800, y: -600 }); setZoom(1.0); setRotationX(0); setRotationY(0); }}>Reset</Button>
                        <Button
                            size="sm"
                            variant={autoRotate ? 'default' : 'outline'}
                            onClick={() => setAutoRotate(!autoRotate)}
                            className={autoRotate ? 'bg-purple-600 shadow-lg shadow-purple-500/30' : ''}
                        >
                            {autoRotate ? '🔄 Spinning' : '🔄 Auto Spin'}
                        </Button>
                    </div>

                    <div className="absolute bottom-4 right-80 text-xs text-zinc-500">
                        Drag nodes · Scroll=zoom · Right-drag=3D rotate · Click to inspect
                    </div>
                </div>

                {/* Info Panel */}
                <div className="w-80 p-4 border-l border-zinc-800 overflow-y-auto bg-zinc-950/80 backdrop-blur">
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
                                {/* View Full Profile Button */}
                                <Button
                                    size="sm"
                                    className="w-full mt-3 bg-cyan-600 hover:bg-cyan-500 text-white"
                                    onClick={() => {
                                        if (selectedEntity.type === 'npc') {
                                            window.location.href = `/npcs?npc=${encodeURIComponent(selectedEntity.name)}`;
                                        } else if (selectedEntity.type === 'building') {
                                            window.location.href = `/explore?building=${encodeURIComponent(selectedEntity.id)}`;
                                        } else {
                                            window.location.href = `/explore`;
                                        }
                                    }}
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
