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

// Sample data - replaces with API data
const SAMPLE_NODES: NPCNode[] = [
    { id: 'charlie', name: 'Charlie', x: 400, y: 300, archetype: 'resistance_fighter', connections: ['felix', 'kira', 'zero_chen'] },
    { id: 'felix', name: 'Felix', x: 300, y: 200, archetype: 'info_broker', connections: ['charlie', 'orion'] },
    { id: 'kira', name: 'Kira', x: 500, y: 200, archetype: 'street_oracle', connections: ['charlie', 'aiche'] },
    { id: 'zero_chen', name: 'Zero Chen', x: 250, y: 400, archetype: 'resistance_fighter', connections: ['charlie', 'kai_vance'] },
    { id: 'orion', name: 'Orion', x: 200, y: 300, archetype: 'tech_specialist', connections: ['felix', 'pixel'] },
    { id: 'aiche', name: 'Aiche', x: 600, y: 300, archetype: 'ai_consciousness', connections: ['kira'] },
    { id: 'kai_vance', name: 'Kai Vance', x: 350, y: 450, archetype: 'tactician', connections: ['zero_chen', 'charlie'] },
    { id: 'pixel', name: 'Pixel', x: 150, y: 380, archetype: 'hacker', connections: ['orion', 'charlie'] },
];

export default function GraphPage() {
    const canvasRef = useRef<HTMLCanvasElement>(null);
    const [nodes, setNodes] = useState<NPCNode[]>(SAMPLE_NODES);
    const [selectedNode, setSelectedNode] = useState<NPCNode | null>(null);
    const [hoveredNode, setHoveredNode] = useState<NPCNode | null>(null);
    const [isDragging, setIsDragging] = useState(false);
    const [dragNode, setDragNode] = useState<string | null>(null);

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
                <div className="w-72 p-4 border-l border-zinc-800">
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
