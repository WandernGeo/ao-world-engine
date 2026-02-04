'use client';

import { useState, useEffect, useRef, useCallback } from 'react';
import { Button } from '@/components/ui/button';

interface NPCNode {
    id: string;
    name: string;
    x: number;
    y: number;
    z: number;
    vx: number;
    vy: number;
    vz: number;
    archetype: string;
    connections: string[];
}

const CLOUD_API = 'https://ao-world-engine-1071951656531.us-central1.run.app';
const LOCAL_API = 'http://localhost:8080';

const ARCHETYPES = ['resistance_fighter', 'info_broker', 'street_oracle', 'tech_specialist', 'ai_consciousness', 'tactician', 'hacker', 'resident', 'vendor', 'worker', 'criminal'];

// Metallic/regal color palette
const ARCHETYPE_COLORS: Record<string, string> = {
    resistance_fighter: '#c41e3a',    // Ruby
    info_broker: '#50c878',           // Emerald
    street_oracle: '#9966cc',         // Amethyst
    tech_specialist: '#4169e1',       // Sapphire
    ai_consciousness: '#00ced1',      // Diamond
    tactician: '#cd7f32',             // Bronze
    hacker: '#c0c0c0',                // Silver
    resident: '#71797e',              // Steel
    vendor: '#ffd700',                // Gold
    worker: '#b87333',                // Copper
    criminal: '#722f37',              // Burgundy
};

// Cyberpunk name generator
const FIRST_NAMES = ['Zero', 'Nova', 'Kai', 'Raven', 'Phoenix', 'Ghost', 'Blade', 'Cipher', 'Echo', 'Frost', 'Hex', 'Jinx', 'Neon', 'Pixel', 'Rogue', 'Shadow', 'Spike', 'Storm', 'Volt', 'Wire', 'Ash', 'Drake', 'Ember', 'Flux', 'Glitch', 'Haze', 'Ion', 'Jazz', 'Kira', 'Luna', 'Max', 'Nico', 'Ori', 'Pulse', 'Quinn', 'Rex', 'Sage', 'Trix', 'Vex', 'Wolf', 'Xen', 'Yuki', 'Zen', 'Arc', 'Blaze', 'Colt', 'Dex', 'Edge', 'Fang', 'Grim'];
const LAST_NAMES = ['Black', 'Chen', 'Vance', 'Reyes', 'Park', 'Kim', 'Silva', 'Tanaka', 'Okafor', 'Petrov', 'Sato', 'Garcia', 'Wei', 'Nakamura', 'Hassan', 'Volkov', 'Martinez', 'Zhang', 'Singh', 'Yamamoto', 'Frost', 'Stone', 'Steel', 'Blade', 'Cross', 'Drake', 'Grey', 'Hart', 'Kane', 'Lynch', 'Moon', 'Night', 'Price', 'Quinn', 'Raven', 'Stark', 'Thorn', 'Vale', 'Ward', 'Wren'];
const NICKNAMES = ['Runner', 'Doc', 'Ace', 'Fixer', 'Shark', 'Prophet', 'Saint', 'Devil', 'Angel', 'Whisper', 'Razor', 'Torch', 'Lucky', 'Jester', 'Bishop', 'Knight', 'Hawk', 'Viper', 'Spider', 'Crow'];

function generateName(index: number): string {
    // Use index as seed for deterministic names
    const firstIdx = index % FIRST_NAMES.length;
    const lastIdx = Math.floor(index / FIRST_NAMES.length) % LAST_NAMES.length;
    const hasNickname = index % 7 === 0; // Every 7th NPC has a nickname

    if (hasNickname) {
        const nickIdx = Math.floor(index / 7) % NICKNAMES.length;
        return `"${NICKNAMES[nickIdx]}" ${LAST_NAMES[lastIdx]}`;
    }
    return `${FIRST_NAMES[firstIdx]} ${LAST_NAMES[lastIdx]}`;
}

// Generate 3D nodes in a sphere
function generateNodes(count: number): NPCNode[] {
    const nodes: NPCNode[] = [];
    const phi = Math.PI * (3 - Math.sqrt(5)); // Golden angle

    for (let i = 0; i < count; i++) {
        const y = 1 - (i / (count - 1)) * 2;
        const radius = Math.sqrt(1 - y * y);
        const theta = phi * i;

        nodes.push({
            id: `npc_${i.toString().padStart(3, '0')}`,
            name: generateName(i),
            x: Math.cos(theta) * radius * 200,
            y: y * 200,
            z: Math.sin(theta) * radius * 200,
            vx: 0, vy: 0, vz: 0,
            archetype: ARCHETYPES[i % ARCHETYPES.length],
            connections: []
        });
    }

    // Add random connections
    nodes.forEach((node, i) => {
        const numConn = 1 + Math.floor(Math.random() * 3);
        for (let c = 0; c < numConn; c++) {
            const target = Math.floor(Math.random() * nodes.length);
            if (target !== i && !node.connections.includes(nodes[target].id)) {
                node.connections.push(nodes[target].id);
            }
        }
    });


    return nodes;
}

export default function GraphPage() {
    const canvasRef = useRef<HTMLCanvasElement>(null);
    const [nodes, setNodes] = useState<NPCNode[]>(() => generateNodes(100));
    const [selectedNode, setSelectedNode] = useState<NPCNode | null>(null);
    const [hoveredNode, setHoveredNode] = useState<NPCNode | null>(null);
    const [rotation, setRotation] = useState({ x: 0, y: 0 });
    const [autoRotate, setAutoRotate] = useState(false); // Default: manual control
    const [isDragging, setIsDragging] = useState(false);
    const [lastMouse, setLastMouse] = useState({ x: 0, y: 0 });
    const [zoom, setZoom] = useState(1);
    const [displayCount, setDisplayCount] = useState(100);
    const [totalNPCs, setTotalNPCs] = useState(800);
    const [apiStatus, setApiStatus] = useState<'loading' | 'local' | 'cloud' | 'offline'>('loading');

    const centerX = 400;
    const centerY = 350;

    // Project 3D to 2D
    const project = useCallback((node: NPCNode) => {
        const cosX = Math.cos(rotation.x);
        const sinX = Math.sin(rotation.x);
        const cosY = Math.cos(rotation.y);
        const sinY = Math.sin(rotation.y);

        // Rotate around Y axis, then X axis
        let x = node.x * cosY - node.z * sinY;
        let z = node.x * sinY + node.z * cosY;
        let y = node.y * cosX - z * sinX;
        z = node.y * sinX + z * cosX;

        // Perspective projection
        const scale = 800 / (800 - z * zoom);
        return {
            x: centerX + x * scale * zoom,
            y: centerY + y * scale * zoom,
            z: z,
            scale: scale * zoom
        };
    }, [rotation, zoom]);

    // Load NPCs from API
    useEffect(() => {
        const loadNPCs = async () => {
            try {
                let res = await fetch(`${LOCAL_API}/api/npcs`, { signal: AbortSignal.timeout(2000) });
                if (!res.ok) {
                    res = await fetch(`${CLOUD_API}/api/npcs`, { signal: AbortSignal.timeout(5000) });
                    setApiStatus('cloud');
                } else {
                    setApiStatus('local');
                }

                if (res.ok) {
                    const data = await res.json();
                    if (data.npcs?.length > 0) {
                        setTotalNPCs(data.npcs.length);
                    }
                }
            } catch {
                setApiStatus('offline');
            }
        };
        loadNPCs();
    }, []);

    // Update nodes when count changes
    useEffect(() => {
        setNodes(generateNodes(displayCount));
    }, [displayCount]);

    // Animation loop
    useEffect(() => {
        let animationId: number;

        const animate = () => {
            if (autoRotate && !isDragging) {
                setRotation(r => ({
                    x: r.x,
                    y: r.y + 0.003
                }));
            }
            animationId = requestAnimationFrame(animate);
        };

        animationId = requestAnimationFrame(animate);
        return () => cancelAnimationFrame(animationId);
    }, [autoRotate, isDragging]);

    // Draw
    useEffect(() => {
        const canvas = canvasRef.current;
        if (!canvas) return;

        const ctx = canvas.getContext('2d');
        if (!ctx) return;

        // Clear with gradient background
        const gradient = ctx.createRadialGradient(centerX, centerY, 0, centerX, centerY, 500);
        gradient.addColorStop(0, '#0a0a0f');
        gradient.addColorStop(1, '#000005');
        ctx.fillStyle = gradient;
        ctx.fillRect(0, 0, canvas.width, canvas.height);

        // Sort nodes by z-depth for proper rendering
        const projected = nodes.map(n => ({ node: n, ...project(n) }));
        projected.sort((a, b) => a.z - b.z);

        // Draw connections first (behind nodes)
        ctx.globalAlpha = 0.15;
        projected.forEach(({ node, x, y }) => {
            node.connections.forEach(connId => {
                const conn = projected.find(p => p.node.id === connId);
                if (conn) {
                    const isHighlighted = selectedNode?.id === node.id || selectedNode?.id === connId;
                    ctx.beginPath();
                    ctx.moveTo(x, y);
                    ctx.lineTo(conn.x, conn.y);
                    ctx.strokeStyle = isHighlighted ? '#06b6d4' : '#334155';
                    ctx.lineWidth = isHighlighted ? 1.5 : 0.5;
                    ctx.stroke();
                }
            });
        });
        ctx.globalAlpha = 1;

        // Draw nodes
        projected.forEach(({ node, x, y, scale }) => {
            const isSelected = selectedNode?.id === node.id;
            const isHovered = hoveredNode?.id === node.id;
            const isConnected = selectedNode?.connections.includes(node.id);

            // Node size based on depth (smaller when far)
            const baseSize = 4;
            const size = Math.max(2, baseSize * scale);

            // Glow effect for selected/hovered
            if (isSelected || isHovered || isConnected) {
                ctx.beginPath();
                ctx.arc(x, y, size + 4, 0, Math.PI * 2);
                ctx.fillStyle = isSelected ? 'rgba(6, 182, 212, 0.3)' : 'rgba(255, 255, 255, 0.2)';
                ctx.fill();
            }

            // Node
            ctx.beginPath();
            ctx.arc(x, y, size, 0, Math.PI * 2);

            const color = ARCHETYPE_COLORS[node.archetype] || '#6b7280';
            ctx.fillStyle = isSelected ? '#06b6d4' : isConnected ? '#fcd34d' : color;
            ctx.fill();

            // Label for selected/hovered only
            if (isSelected || isHovered) {
                ctx.font = '10px monospace';
                ctx.fillStyle = '#fff';
                ctx.textAlign = 'center';
                ctx.fillText(node.name, x, y - size - 6);
            }
        });

        // Draw center indicator
        ctx.beginPath();
        ctx.arc(centerX, centerY, 2, 0, Math.PI * 2);
        ctx.fillStyle = '#334155';
        ctx.fill();

    }, [nodes, rotation, selectedNode, hoveredNode, zoom, project]);

    // Mouse handlers
    const handleMouseDown = (e: React.MouseEvent) => {
        const rect = canvasRef.current?.getBoundingClientRect();
        if (!rect) return;

        const mx = e.clientX - rect.left;
        const my = e.clientY - rect.top;

        // Find clicked node
        const projected = nodes.map(n => ({ node: n, ...project(n) }));
        projected.sort((a, b) => b.z - a.z); // Click check in reverse order

        for (const p of projected) {
            const size = Math.max(2, 4 * p.scale);
            if (Math.sqrt((p.x - mx) ** 2 + (p.y - my) ** 2) < size + 5) {
                setSelectedNode(p.node);
                return;
            }
        }

        setIsDragging(true);
        setLastMouse({ x: e.clientX, y: e.clientY });
        setSelectedNode(null);
    };

    const handleMouseMove = (e: React.MouseEvent) => {
        const rect = canvasRef.current?.getBoundingClientRect();
        if (!rect) return;

        if (isDragging) {
            const dx = e.clientX - lastMouse.x;
            const dy = e.clientY - lastMouse.y;
            setRotation(r => ({
                x: r.x + dy * 0.005,
                y: r.y + dx * 0.005
            }));
            setLastMouse({ x: e.clientX, y: e.clientY });
            return;
        }

        // Hover detection
        const mx = e.clientX - rect.left;
        const my = e.clientY - rect.top;
        const projected = nodes.map(n => ({ node: n, ...project(n) }));
        projected.sort((a, b) => b.z - a.z);

        for (const p of projected) {
            const size = Math.max(2, 4 * p.scale);
            if (Math.sqrt((p.x - mx) ** 2 + (p.y - my) ** 2) < size + 5) {
                setHoveredNode(p.node);
                return;
            }
        }
        setHoveredNode(null);
    };

    const handleMouseUp = () => setIsDragging(false);
    const handleWheel = (e: React.WheelEvent) => {
        e.preventDefault();
        setZoom(z => Math.max(0.5, Math.min(3, z - e.deltaY * 0.001)));
    };

    return (
        <div className="min-h-screen bg-zinc-950 text-white">
            {/* Header */}
            <header className="fixed top-0 left-0 right-0 h-14 bg-gradient-to-b from-zinc-900/90 to-transparent backdrop-blur-sm z-50 flex items-center px-4 border-b border-cyan-500/20">
                <h1 className="font-mono text-lg font-bold bg-gradient-to-r from-cyan-400 to-purple-400 bg-clip-text text-transparent">
                    AO WORLD ENGINE
                </h1>
                <nav className="ml-8 flex gap-4">
                    <a href="/explore"><Button variant="ghost" size="sm" className="text-zinc-500 hover:text-cyan-400">Explore</Button></a>
                    <a href="/chat"><Button variant="ghost" size="sm" className="text-zinc-500 hover:text-cyan-400">Chat</Button></a>
                    <Button variant="ghost" size="sm" className="text-cyan-400">Graph</Button>
                </nav>
            </header>

            <div className="pt-14 flex h-screen">
                {/* Canvas */}
                <div className="flex-1 relative cursor-grab active:cursor-grabbing">
                    <canvas
                        ref={canvasRef}
                        width={800}
                        height={700}
                        className="w-full h-full"
                        onMouseDown={handleMouseDown}
                        onMouseMove={handleMouseMove}
                        onMouseUp={handleMouseUp}
                        onMouseLeave={handleMouseUp}
                        onWheel={handleWheel}
                    />

                    {/* Controls overlay */}
                    <div className="absolute bottom-4 left-4 flex gap-2">
                        <Button
                            size="sm"
                            variant={autoRotate ? "default" : "outline"}
                            onClick={() => setAutoRotate(!autoRotate)}
                            className={autoRotate ? "bg-cyan-600" : ""}
                        >
                            {autoRotate ? '⏸ Pause' : '▶ Spin'}
                        </Button>
                        <Button size="sm" variant="outline" onClick={() => setZoom(z => Math.min(3, z + 0.2))}>+</Button>
                        <Button size="sm" variant="outline" onClick={() => setZoom(z => Math.max(0.5, z - 0.2))}>−</Button>
                        <Button size="sm" variant="outline" onClick={() => { setRotation({ x: 0, y: 0 }); setZoom(1); }}>Reset</Button>
                    </div>

                    <div className="absolute bottom-4 right-80 text-xs text-zinc-500">
                        Drag to rotate • Scroll to zoom • Click nodes to select
                    </div>
                </div>

                {/* Info Panel */}
                <div className="w-72 p-4 border-l border-zinc-800 overflow-y-auto bg-zinc-950/50 backdrop-blur">
                    {/* NPC Count */}
                    <div className="mb-4 p-3 bg-gradient-to-r from-cyan-900/30 to-purple-900/30 rounded-lg border border-cyan-500/20">
                        <div className="flex items-center justify-between">
                            <span className="text-xs text-cyan-400 font-mono">TOTAL NPCs</span>
                            <span className={`text-xs px-2 py-0.5 rounded ${apiStatus === 'offline' ? 'bg-yellow-500/20 text-yellow-400' : 'bg-green-500/20 text-green-400'}`}>
                                {apiStatus === 'cloud' ? '☁️ Cloud' : apiStatus === 'local' ? '💻 Local' : '🎮 Demo'}
                            </span>
                        </div>
                        <div className="text-2xl font-bold text-white mt-1">{totalNPCs.toLocaleString()}</div>
                    </div>

                    {/* Slider */}
                    <div className="mb-4">
                        <label className="text-xs text-zinc-500 block mb-1">Visible: {displayCount}</label>
                        <input
                            type="range" min="20" max="300" value={displayCount}
                            onChange={(e) => setDisplayCount(Number(e.target.value))}
                            className="w-full accent-cyan-500 h-1"
                        />
                    </div>

                    <h2 className="text-xs text-cyan-400 font-mono mb-3 border-b border-zinc-800 pb-2">SELECTED NPC</h2>

                    {selectedNode ? (
                        <div className="space-y-3">
                            <div className="p-3 bg-zinc-900/80 rounded-lg border border-cyan-500/30">
                                <h3 className="text-lg font-bold text-cyan-400">{selectedNode.name}</h3>
                                <p className="text-xs text-zinc-500 capitalize">{selectedNode.archetype.replace('_', ' ')}</p>
                            </div>

                            <div>
                                <h4 className="text-xs text-zinc-500 mb-2">CONNECTIONS ({selectedNode.connections.length})</h4>
                                <div className="space-y-1 max-h-40 overflow-y-auto">
                                    {selectedNode.connections.slice(0, 10).map(connId => {
                                        const conn = nodes.find(n => n.id === connId);
                                        return conn ? (
                                            <button
                                                key={connId}
                                                onClick={() => setSelectedNode(conn)}
                                                className="w-full text-left p-2 bg-zinc-800/50 rounded hover:bg-zinc-700 flex items-center gap-2 text-sm"
                                            >
                                                <span className="w-2 h-2 rounded-full" style={{ backgroundColor: ARCHETYPE_COLORS[conn.archetype] }} />
                                                <span className="truncate">{conn.name}</span>
                                            </button>
                                        ) : null;
                                    })}
                                </div>
                            </div>
                        </div>
                    ) : (
                        <div className="text-center text-zinc-600 py-4">
                            <div className="text-2xl mb-2">🌐</div>
                            <div className="text-xs">Click a node to see details</div>
                        </div>
                    )}

                    {/* Legend */}
                    <div className="mt-4 pt-4 border-t border-zinc-800">
                        <h4 className="text-xs text-zinc-500 mb-2">ARCHETYPES</h4>
                        <div className="grid grid-cols-2 gap-1 text-xs">
                            {Object.entries(ARCHETYPE_COLORS).slice(0, 6).map(([type, color]) => (
                                <div key={type} className="flex items-center gap-1">
                                    <span className="w-2 h-2 rounded-full" style={{ backgroundColor: color }} />
                                    <span className="text-zinc-400 capitalize truncate">{type.replace('_', ' ')}</span>
                                </div>
                            ))}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}
