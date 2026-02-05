'use client';

import { useRef, useEffect, useCallback, useMemo } from 'react';
import dynamic from 'next/dynamic';

// Dynamic import to avoid SSR issues
const ForceGraph3D = dynamic(() => import('react-force-graph-3d'), {
    ssr: false,
    loading: () => (
        <div style={{
            width: '100%',
            height: '100%',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            background: '#0a0a1a',
            color: '#00d4ff',
            fontFamily: 'monospace'
        }}>
            Loading 3D Graph...
        </div>
    ),
});

// Types
export type EntityType = 'npc' | 'building' | 'faction' | 'lore' | 'item' | 'location' | 'event';

export interface Entity {
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

export interface Relationship {
    source: string;
    target: string;
    type: string;
}

// Grakn-style color scheme
const TYPE_COLORS: Record<EntityType, string> = {
    npc: '#00e676',       // Bright green
    building: '#aa00ff',  // Purple
    faction: '#ff9100',   // Orange
    lore: '#00b0ff',      // Light blue
    item: '#f50057',      // Pink
    location: '#651fff',  // Deep purple
    event: '#ff1744',     // Red
};

const RELATIONSHIP_COLORS: Record<string, string> = {
    spouse: '#ff4081',
    parent_of: '#40c4ff',
    sibling: '#ffab00',
    member_of: '#69f0ae',
    works_at: '#ea80fc',
    lives_at: '#7c4dff',
    default: '#448aff',
};

interface Graph3DProps {
    entities: Entity[];
    relationships: Relationship[];
    selectedEntity: Entity | null;
    onSelectEntity: (entity: Entity | null) => void;
    onDoubleClickEntity: (entity: Entity) => void;
    filter: EntityType | 'all';
    showFamilyOnly: boolean;
    isSimulating: boolean;
}

// Convert our data format to force-graph format
interface GraphNode {
    id: string;
    name: string;
    type: EntityType;
    color: string;
    val: number;
    properties?: Record<string, string>;
}

interface GraphLink {
    source: string;
    target: string;
    type: string;
    color: string;
}

interface Graph3DProps {
    entities: Entity[];
    relationships: Relationship[];
    selectedEntity: Entity | null;
    onSelectEntity: (entity: Entity | null) => void;
    onDoubleClickEntity: (entity: Entity) => void;
    filter: EntityType | 'all';
    showFamilyOnly: boolean;
    isSimulating: boolean;
    controlMode?: 'orbit' | 'fly' | 'trackball';
}

export default function Graph3D({
    entities,
    relationships,
    selectedEntity,
    onSelectEntity,
    onDoubleClickEntity,
    filter,
    showFamilyOnly,
    isSimulating,
    controlMode = 'fly',  // Default to fly for WASD control
}: Graph3DProps) {
    const fgRef = useRef<any>(null);

    // Filter entities
    const filteredEntities = useMemo(() => {
        return filter === 'all' ? entities : entities.filter(e => e.type === filter);
    }, [entities, filter]);

    // Filter relationships
    const familyTypes = ['spouse', 'parent_of', 'sibling'];
    const filteredRelationships = useMemo(() => {
        const entityIds = new Set(filteredEntities.map(e => e.id));
        return relationships.filter(r => {
            if (showFamilyOnly && !familyTypes.includes(r.type)) return false;
            return entityIds.has(r.source) && entityIds.has(r.target);
        });
    }, [relationships, filteredEntities, showFamilyOnly]);

    // Convert to force-graph data format
    const graphData = useMemo(() => {
        const nodes: GraphNode[] = filteredEntities.map(e => ({
            id: e.id,
            name: e.name,
            type: e.type,
            color: TYPE_COLORS[e.type],
            val: e.type === 'faction' ? 20 : e.type === 'building' ? 8 : 3,
            properties: e.properties,
        }));

        const links: GraphLink[] = filteredRelationships.map(r => ({
            source: r.source,
            target: r.target,
            type: r.type,
            color: RELATIONSHIP_COLORS[r.type] || RELATIONSHIP_COLORS.default,
        }));

        return { nodes, links };
    }, [filteredEntities, filteredRelationships]);

    // Get connected node IDs for highlighting
    const connectedIds = useMemo(() => {
        if (!selectedEntity) return new Set<string>();
        const ids = new Set<string>();
        relationships.forEach(r => {
            if (r.source === selectedEntity.id) ids.add(r.target);
            if (r.target === selectedEntity.id) ids.add(r.source);
        });
        return ids;
    }, [selectedEntity, relationships]);

    // Track double-click timing
    const lastClickRef = useRef<{ id: string; time: number } | null>(null);

    // Handle node click - single click selects, double click flies/navigates
    const handleNodeClick = useCallback((node: any) => {
        const now = Date.now();
        const entity = entities.find(e => e.id === node.id);

        // Check for double-click (within 300ms)
        if (lastClickRef.current &&
            lastClickRef.current.id === node.id &&
            now - lastClickRef.current.time < 300) {
            // DOUBLE CLICK - fly close and navigate if NPC
            if (fgRef.current) {
                const distance = 40;  // Closer for double-click
                const distRatio = 1 + distance / Math.hypot(node.x, node.y, node.z);
                fgRef.current.cameraPosition(
                    { x: node.x * distRatio, y: node.y * distRatio, z: node.z * distRatio },
                    node,
                    800  // Faster animation
                );
            }
            // Navigate to entity page for NPCs/buildings
            if (entity) {
                setTimeout(() => {
                    onDoubleClickEntity(entity);
                }, 800);  // Wait for fly animation
            }
            lastClickRef.current = null;
        } else {
            // SINGLE CLICK - select and show connections
            onSelectEntity(entity || null);

            // Gentle camera drift toward node
            if (fgRef.current) {
                const distance = 120;
                const distRatio = 1 + distance / Math.hypot(node.x, node.y, node.z);
                fgRef.current.cameraPosition(
                    { x: node.x * distRatio, y: node.y * distRatio, z: node.z * distRatio },
                    node,
                    1500
                );
            }
            lastClickRef.current = { id: node.id, time: now };
        }
    }, [entities, onSelectEntity, onDoubleClickEntity]);

    // Pause/resume simulation
    useEffect(() => {
        if (fgRef.current) {
            if (isSimulating) {
                fgRef.current.d3ReheatSimulation();
            } else {
                fgRef.current.pauseAnimation();
            }
        }
    }, [isSimulating]);

    // Custom node rendering for Grakn-style
    const nodeThreeObject = useCallback((node: any) => {
        const THREE = require('three');

        // Create group for node
        const group = new THREE.Group();

        // Determine size based on type
        const size = node.type === 'faction' ? 6 : node.type === 'building' ? 3 : 1.5;

        // Main sphere with glow effect
        const geometry = new THREE.SphereGeometry(size, 32, 32);
        const material = new THREE.MeshLambertMaterial({
            color: node.color,
            transparent: true,
            opacity: 0.9,
        });
        const sphere = new THREE.Mesh(geometry, material);
        group.add(sphere);

        // Outer glow ring for selected
        if (selectedEntity?.id === node.id) {
            const ringGeometry = new THREE.RingGeometry(size * 1.5, size * 2, 32);
            const ringMaterial = new THREE.MeshBasicMaterial({
                color: '#00d4ff',
                transparent: true,
                opacity: 0.6,
                side: THREE.DoubleSide,
            });
            const ring = new THREE.Mesh(ringGeometry, ringMaterial);
            ring.lookAt(0, 0, 1);
            group.add(ring);
        }

        // Connected node highlight
        if (connectedIds.has(node.id)) {
            const glowGeometry = new THREE.SphereGeometry(size * 1.3, 16, 16);
            const glowMaterial = new THREE.MeshBasicMaterial({
                color: '#00d4ff',
                transparent: true,
                opacity: 0.2,
            });
            const glow = new THREE.Mesh(glowGeometry, glowMaterial);
            group.add(glow);
        }

        return group;
    }, [selectedEntity, connectedIds]);

    // Custom link rendering - MORE VISIBLE
    const linkColor = useCallback((link: any) => {
        const isHighlighted = selectedEntity &&
            (link.source.id === selectedEntity.id || link.target.id === selectedEntity.id);
        // Brighter default links, very bright when selected
        return isHighlighted ? link.color : 'rgba(80, 180, 255, 0.6)';
    }, [selectedEntity]);

    const linkWidth = useCallback((link: any) => {
        const isHighlighted = selectedEntity &&
            (link.source.id === selectedEntity.id || link.target.id === selectedEntity.id);
        // Thicker lines for visibility
        return isHighlighted ? 4 : 1;
    }, [selectedEntity]);

    return (
        <div style={{ width: '100%', height: '100%', background: '#0a0a1a' }}>
            <ForceGraph3D
                ref={fgRef}
                graphData={graphData}
                nodeThreeObject={nodeThreeObject}
                nodeLabel={(node: any) => `
                    <div style="
                        background: rgba(10, 10, 26, 0.95);
                        padding: 8px 12px;
                        border-radius: 4px;
                        border: 1px solid ${node.color};
                        font-family: 'SF Mono', monospace;
                        font-size: 12px;
                        color: #fff;
                        box-shadow: 0 0 10px ${node.color}40;
                    ">
                        <div style="color: ${node.color}; font-weight: 600;">${node.name}</div>
                        <div style="color: #888; font-size: 10px;">${node.type.toUpperCase()}</div>
                        ${node.properties?.archetype ? `<div style="color: #aaa; font-size: 10px; margin-top: 4px;">${node.properties.archetype}</div>` : ''}
                    </div>
                `}
                nodeVal={(node: any) => node.val}
                onNodeClick={handleNodeClick}
                onNodeDragEnd={(node: any) => {
                    // Pin node after drag
                    node.fx = node.x;
                    node.fy = node.y;
                    node.fz = node.z;
                }}
                linkColor={linkColor}
                linkWidth={linkWidth}
                linkOpacity={0.6}
                linkDirectionalParticles={2}
                linkDirectionalParticleWidth={1.5}
                linkDirectionalParticleSpeed={0.005}
                backgroundColor="#0a0a1a"
                showNavInfo={false}
                enableNodeDrag={true}
                enableNavigationControls={true}
                controlType={controlMode}
                d3AlphaDecay={0.02}
                d3VelocityDecay={0.3}
                warmupTicks={100}
                cooldownTicks={200}
            />
        </div>
    );
}
