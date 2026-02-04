'use client';

import { useState, useEffect, useRef } from 'react';
import { Button } from '@/components/ui/button';

interface NPCNode {
    id: string;
    name: string;
    x: number;
    y: number;
    archetype: string;
    connections: string[];
}

interface Relationship {
    source: string;
    target: string;
    type: string;
    trust: number;
}

const CLOUD_API = 'https://ao-world-engine-1071951656531.us-central1.run.app';
const LOCAL_API = 'http://localhost:8080';

// Generate random position in a circle layout
function generatePosition(index: number, total: number, centerX = 400, centerY = 350, radius = 250) {
    const angle = (index / total) * 2 * Math.PI - Math.PI / 2;
    return {
        x: centerX + radius * Math.cos(angle) + (Math.random() - 0.5) * 50,
        y: centerY + radius * Math.sin(angle) + (Math.random() - 0.5) * 50
    };
}

// Archetypes for random assignment
const ARCHETYPES = ['resistance_fighter', 'info_broker', 'street_oracle', 'tech_specialist', 'ai_consciousness', 'tactician', 'hacker', 'resident', 'vendor', 'worker', 'criminal'];

// Generate demo nodes (shown while API loads or if API fails)
function generateDemoNodes(count: number): NPCNode[] {
    const nodes: NPCNode[] = [];
    for (let i = 0; i < count; i++) {
        const pos = generatePosition(i, count);
        const id = `npc_${i.toString().padStart(3, '0')}`;
        const archetype = ARCHETYPES[i % ARCHETYPES.length];
        nodes.push({
            id,
            name: `NPC ${i + 1}`,
            x: pos.x,
            y: pos.y,
            archetype,
            connections: []
        });
    }
    // Add random connections (2-4 per node)
    nodes.forEach((node, i) => {
        const numConnections = 2 + Math.floor(Math.random() * 3);
        for (let c = 0; c < numConnections; c++) {
            const targetIdx = Math.floor(Math.random() * nodes.length);
            if (targetIdx !== i && !node.connections.includes(nodes[targetIdx].id)) {
                node.connections.push(nodes[targetIdx].id);
            }
        }
    });
    return nodes;
}

// Initial displayed nodes - show subset for performance
const INITIAL_NODES = generateDemoNodes(50);

export default function GraphPage() {
    const canvasRef = useRef<HTMLCanvasElement>(null);
    const [nodes, setNodes] = useState<NPCNode[]>(INITIAL_NODES);
    const [allNodes, setAllNodes] = useState<NPCNode[]>([]); // Full list from API
    const [selectedNode, setSelectedNode] = useState<NPCNode | null>(null);
    const [hoveredNode, setHoveredNode] = useState<NPCNode | null>(null);
    const [isDragging, setIsDragging] = useState(false);
    const [dragNode, setDragNode] = useState<string | null>(null);
    const [displayCount, setDisplayCount] = useState(50);
    const [totalNPCs, setTotalNPCs] = useState(800);
    const [apiStatus, setApiStatus] = useState<'loading' | 'local' | 'cloud' | 'offline'>('loading');

    // Load NPCs from API
    useEffect(() => {
        const loadNPCs = async () => {
            try {
                // Try local first
                let res = await fetch(`${LOCAL_API}/api/npcs`, { signal: AbortSignal.timeout(2000) });
                if (!res.ok) {
                    res = await fetch(`${CLOUD_API}/api/npcs`, { signal: AbortSignal.timeout(5000) });
                    setApiStatus('cloud');
                } else {
                    setApiStatus('local');
                }

                if (res.ok) {
                    const data = await res.json();
                    if (data.npcs && data.npcs.length > 0) {
                        setTotalNPCs(data.npcs.length);
                        // Convert API data to nodes
                        const apiNodes: NPCNode[] = data.npcs.map((npc: any, i: number) => {
                            const pos = generatePosition(i, data.npcs.length);
                            return {
                                id: npc.id || npc.key || `npc_${i}`,
                                name: npc.name || `NPC ${i}`,
                                x: pos.x,
                                y: pos.y,
                                archetype: npc.archetype || ARCHETYPES[i % ARCHETYPES.length],
                                connections: npc.relationships?.map((r: any) => r.target) || []
                            };
                        });
                        setAllNodes(apiNodes);
                        setNodes(apiNodes.slice(0, displayCount));
                    }
                }
            } catch {
                setApiStatus('offline');
                // Keep demo nodes
            }
        };
        loadNPCs();
    }, []);

    // Update display when count changes
    useEffect(() => {
        if (allNodes.length > 0) {
            setNodes(allNodes.slice(0, displayCount));
        } else {
            setNodes(generateDemoNodes(displayCount));
        }
    }, [displayCount, allNodes]);

    // Draw graph
    useEffect(() => {
        const canvas = canvasRef.current;
        if (!canvas) return;

        const ctx = canvas.getContext('2d');
        if (!ctx) return;

        // Clear
        ctx.fillStyle = '#09090b';
        ctx.fillRect(0, 0, canvas.width, canvas.height);

        // Draw connections
        nodes.forEach(node => {
            node.connections.forEach(connId => {
                const target = nodes.find(n => n.id === connId);
                if (target) {
                    ctx.beginPath();
                    ctx.moveTo(node.x, node.y);
                    ctx.lineTo(target.x, target.y);

                    // Color based on relationship type
                    const isSelected = selectedNode?.id === node.id || selectedNode?.id === target.id;
                    ctx.strokeStyle = isSelected ? '#06b6d4' : '#3f3f46';
                    ctx.lineWidth = isSelected ? 2 : 1;
                    ctx.stroke();
                }
            });
        });

        // Draw nodes
        nodes.forEach(node => {
            const isSelected = selectedNode?.id === node.id;
            const isHovered = hoveredNode?.id === node.id;
            const isConnected = selectedNode?.connections.includes(node.id);

            // Node circle
            ctx.beginPath();
            ctx.arc(node.x, node.y, isSelected ? 25 : 20, 0, Math.PI * 2);

            // Color by archetype
            const colors: Record<string, string> = {
                resistance_fighter: '#ef4444',
                info_broker: '#22c55e',
                street_oracle: '#a855f7',
                tech_specialist: '#3b82f6',
                ai_consciousness: '#06b6d4',
                tactician: '#f97316',
                hacker: '#84cc16',
            };

            ctx.fillStyle = isSelected ? '#06b6d4' : (colors[node.archetype] || '#6b7280');
            if (isHovered) ctx.fillStyle = '#f0f0f0';
            if (isConnected && selectedNode) ctx.fillStyle = '#fcd34d';

            ctx.fill();
            ctx.strokeStyle = isSelected ? '#fff' : '#27272a';
            ctx.lineWidth = 2;
            ctx.stroke();

            // Label
            ctx.fillStyle = '#fff';
            ctx.font = '12px monospace';
            ctx.textAlign = 'center';
            ctx.fillText(node.name, node.x, node.y + 35);
        });

    }, [nodes, selectedNode, hoveredNode]);

    // Handle mouse events
    const handleMouseDown = (e: React.MouseEvent) => {
        const rect = canvasRef.current?.getBoundingClientRect();
        if (!rect) return;

        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;

        const clicked = nodes.find(n =>
            Math.sqrt((n.x - x) ** 2 + (n.y - y) ** 2) < 25
        );

        if (clicked) {
            setSelectedNode(clicked);
            setDragNode(clicked.id);
            setIsDragging(true);
        } else {
            setSelectedNode(null);
        }
    };

    const handleMouseMove = (e: React.MouseEvent) => {
        const rect = canvasRef.current?.getBoundingClientRect();
        if (!rect) return;

        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;

        // Drag node
        if (isDragging && dragNode) {
            setNodes(prev => prev.map(n =>
                n.id === dragNode ? { ...n, x, y } : n
            ));
            return;
        }

        // Hover detection
        const hovered = nodes.find(n =>
            Math.sqrt((n.x - x) ** 2 + (n.y - y) ** 2) < 25
        );
        setHoveredNode(hovered || null);
    };

    const handleMouseUp = () => {
        setIsDragging(false);
        setDragNode(null);
    };

    const getArchetypeColor = (archetype: string) => {
        const colors: Record<string, string> = {
            resistance_fighter: 'bg-red-500',
            info_broker: 'bg-green-500',
            street_oracle: 'bg-purple-500',
            tech_specialist: 'bg-blue-500',
            ai_consciousness: 'bg-cyan-500',
            tactician: 'bg-orange-500',
            hacker: 'bg-lime-500',
        };
        return colors[archetype] || 'bg-gray-500';
    };

    return (
        <div className="min-h-screen bg-zinc-950 text-white">
            {/* Header */}
            <header className="fixed top-0 left-0 right-0 h-14 bg-gradient-to-b from-zinc-900 to-transparent z-50 flex items-center px-4 border-b border-cyan-500/20">
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
                <div className="flex-1 relative">
                    <canvas
                        ref={canvasRef}
                        width={800}
                        height={600}
                        className="w-full h-full"
                        onMouseDown={handleMouseDown}
                        onMouseMove={handleMouseMove}
                        onMouseUp={handleMouseUp}
                        onMouseLeave={handleMouseUp}
                    />

                    {/* Instructions */}
                    <div className="absolute bottom-4 left-4 text-xs text-zinc-500">
                        Click nodes to select • Drag to move • Yellow = connected
                    </div>
                </div>

                {/* Info Panel */}
                <div className="w-72 p-4 border-l border-zinc-800 overflow-y-auto">
                    {/* NPC Count Badge */}
                    <div className="mb-4 p-3 bg-gradient-to-r from-cyan-900/50 to-purple-900/50 rounded-lg border border-cyan-500/30">
                        <div className="flex items-center justify-between">
                            <span className="text-xs text-cyan-400 font-mono">TOTAL NPCs</span>
                            <span className={`text-xs px-2 py-0.5 rounded ${apiStatus === 'loading' ? 'bg-yellow-500/20 text-yellow-400' : apiStatus === 'offline' ? 'bg-red-500/20 text-red-400' : 'bg-green-500/20 text-green-400'}`}>
                                {apiStatus === 'loading' ? 'Loading...' : apiStatus === 'offline' ? 'Demo Mode' : apiStatus === 'local' ? 'Local' : 'Cloud'}
                            </span>
                        </div>
                        <div className="text-3xl font-bold text-white mt-1">{totalNPCs.toLocaleString()}</div>
                        <div className="text-xs text-zinc-500">Showing {nodes.length} / {totalNPCs}</div>
                    </div>

                    {/* Display Slider */}
                    <div className="mb-4">
                        <label className="text-xs text-zinc-500 block mb-2">Display Count: {displayCount}</label>
                        <input
                            type="range"
                            min="10"
                            max="200"
                            value={displayCount}
                            onChange={(e) => setDisplayCount(Number(e.target.value))}
                            className="w-full accent-cyan-500"
                        />
                        <div className="flex justify-between text-xs text-zinc-600">
                            <span>10</span>
                            <span>200</span>
                        </div>
                    </div>

                    <h2 className="text-xs text-cyan-400 font-mono mb-4">RELATIONSHIP GRAPH</h2>

                    {selectedNode ? (
                        <div className="space-y-4">
                            <div className="p-4 bg-zinc-900 rounded-lg">
                                <h3 className="text-lg font-bold text-cyan-400">{selectedNode.name}</h3>
                                <p className="text-sm text-zinc-500">{selectedNode.archetype.replace('_', ' ')}</p>
                            </div>

                            <div>
                                <h4 className="text-xs text-zinc-500 mb-2">CONNECTIONS ({selectedNode.connections.length})</h4>
                                <div className="space-y-1">
                                    {selectedNode.connections.map(connId => {
                                        const conn = nodes.find(n => n.id === connId);
                                        return conn ? (
                                            <button
                                                key={connId}
                                                onClick={() => setSelectedNode(conn)}
                                                className="w-full text-left p-2 bg-zinc-800 rounded hover:bg-zinc-700 flex items-center gap-2"
                                            >
                                                <span className={`w-2 h-2 rounded-full ${getArchetypeColor(conn.archetype)}`} />
                                                <span>{conn.name}</span>
                                            </button>
                                        ) : null;
                                    })}
                                </div>
                            </div>
                        </div>
                    ) : (
                        <div className="text-center text-zinc-600 mt-8">
                            <div className="text-4xl mb-4">🕸️</div>
                            <div>Click an NPC to see relationships</div>
                        </div>
                    )}

                    {/* Legend */}
                    <div className="mt-8">
                        <h4 className="text-xs text-zinc-500 mb-2">ARCHETYPES</h4>
                        <div className="space-y-1 text-xs">
                            <div className="flex items-center gap-2"><span className="w-2 h-2 rounded-full bg-red-500" /> Resistance Fighter</div>
                            <div className="flex items-center gap-2"><span className="w-2 h-2 rounded-full bg-green-500" /> Info Broker</div>
                            <div className="flex items-center gap-2"><span className="w-2 h-2 rounded-full bg-purple-500" /> Street Oracle</div>
                            <div className="flex items-center gap-2"><span className="w-2 h-2 rounded-full bg-blue-500" /> Tech Specialist</div>
                            <div className="flex items-center gap-2"><span className="w-2 h-2 rounded-full bg-cyan-500" /> AI Consciousness</div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}
