'use client';

import { useState, useEffect, useCallback } from 'react';
import { TimeControls } from '@/components/TimeControls';
import { SceneGenerator } from '@/components/SceneGenerator';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';

// Types
interface Building {
    id: string;
    name: string;
    type: 'residential' | 'commercial' | 'temple' | 'industrial';
    polygon: [number, number][];
    levels: number;
    occupants: string[];
}

interface NPC {
    id: string;
    name: string;
    location: string;
    activity: string;
    mood: string;
}

interface District {
    id: string;
    name: string;
    color: string;
    buildings: Building[];
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'https://ao-world-engine-1071951656531.us-central1.run.app';

// Initial districts data
const INITIAL_DISTRICTS: District[] = [
    {
        id: 'undercity',
        name: 'Undercity',
        color: '#1a1a2e',
        buildings: [
            { id: 'B001', name: "Felix's Bar", type: 'commercial', polygon: [[50, 100], [120, 100], [120, 160], [50, 160]], levels: 2, occupants: ['felix', 'charlie'] },
            { id: 'B002', name: 'Abandoned Warehouse', type: 'industrial', polygon: [[140, 80], [220, 80], [220, 180], [140, 180]], levels: 3, occupants: [] },
        ],
    },
    {
        id: 'market',
        name: 'Market District',
        color: '#2d2d44',
        buildings: [
            { id: 'B010', name: 'Central Market', type: 'commercial', polygon: [[300, 50], [450, 50], [450, 150], [300, 150]], levels: 1, occupants: ['vendor_1', 'vendor_2'] },
            { id: 'B011', name: 'Tech Shop', type: 'commercial', polygon: [[300, 170], [380, 170], [380, 230], [300, 230]], levels: 2, occupants: ['orion'] },
        ],
    },
    {
        id: 'temple',
        name: 'Temple District',
        color: '#3d2d2d',
        buildings: [
            { id: 'B016', name: 'Citizen Processing', type: 'temple', polygon: [[500, 100], [650, 100], [650, 200], [580, 220], [500, 200]], levels: 5, occupants: ['inquisitor_1'] },
        ],
    },
];

const INITIAL_NPCS: NPC[] = [
    { id: 'charlie', name: 'Charlie', location: 'B001', activity: 'drinking', mood: 'cautious' },
    { id: 'felix', name: 'Felix', location: 'B001', activity: 'bartending', mood: 'friendly' },
    { id: 'orion', name: 'Orion Thanewilk', location: 'B011', activity: 'working', mood: 'focused' },
];

export default function ExplorePage() {
    // State - initialized as empty/defaults to avoid hydration mismatch
    const [mounted, setMounted] = useState(false);
    const [currentTick, setCurrentTick] = useState(100);
    const [isPlaying, setIsPlaying] = useState(false);
    const [tickSpeed, setTickSpeed] = useState(1);
    const [selectedBuilding, setSelectedBuilding] = useState<Building | null>(null);
    const [selectedNPC, setSelectedNPC] = useState<NPC | null>(null);
    const [npcs, setNpcs] = useState<NPC[]>([]);
    const [districts, setDistricts] = useState<District[]>([]);

    // Initialize on mount to avoid hydration mismatch
    useEffect(() => {
        setMounted(true);
        setDistricts(INITIAL_DISTRICTS);
        setNpcs(INITIAL_NPCS);
    }, []);

    // Auto-advance tick when playing
    useEffect(() => {
        if (!isPlaying || !mounted) return;

        const interval = setInterval(() => {
            setCurrentTick(prev => prev + 1);
        }, 1000 / tickSpeed);

        return () => clearInterval(interval);
    }, [isPlaying, tickSpeed, mounted]);

    // Fetch NPCs - only fetch if API available, otherwise use mock data
    const fetchNPCs = useCallback(async () => {
        if (!mounted) return; // Don't fetch until mounted
        try {
            const response = await fetch(`${API_BASE}/api/npcs?tick=${currentTick}`);
            if (response.ok) {
                const data = await response.json();
                // Only set if we got a valid array
                if (Array.isArray(data)) {
                    setNpcs(data);
                }
            }
        } catch {
            // API failed - keep using INITIAL_NPCS (already set on mount)
        }
    }, [currentTick, mounted]);

    // Don't auto-fetch on every tick change - just use initial data for demo
    // useEffect(() => {
    //     fetchNPCs();
    // }, [fetchNPCs]);

    // Render building polygon
    const renderBuilding = (building: Building, districtColor: string) => {
        const points = building.polygon.map(p => p.join(',')).join(' ');
        const isSelected = selectedBuilding?.id === building.id;
        const buildingNPCs = (npcs || []).filter(n => n.location === building.id);

        return (
            <g key={building.id} className="cursor-pointer" onClick={() => setSelectedBuilding(building)}>
                {/* Building shape */}
                <polygon
                    points={points}
                    fill={isSelected ? 'rgba(0, 255, 255, 0.3)' : districtColor}
                    stroke={isSelected ? '#00ffff' : '#444'}
                    strokeWidth={isSelected ? 2 : 1}
                    className="transition-all hover:fill-cyan-900/50"
                />

                {/* Building label */}
                <text
                    x={building.polygon.reduce((sum, p) => sum + p[0], 0) / building.polygon.length}
                    y={building.polygon.reduce((sum, p) => sum + p[1], 0) / building.polygon.length}
                    textAnchor="middle"
                    className="fill-white text-xs font-mono pointer-events-none"
                    style={{ fontSize: '10px' }}
                >
                    {building.name}
                </text>

                {/* NPC dots */}
                {buildingNPCs.map((npc, i) => {
                    const centerX = building.polygon.reduce((sum, p) => sum + p[0], 0) / building.polygon.length;
                    const centerY = building.polygon.reduce((sum, p) => sum + p[1], 0) / building.polygon.length + 15;
                    return (
                        <circle
                            key={npc.id}
                            cx={centerX + (i * 12) - ((buildingNPCs.length - 1) * 6)}
                            cy={centerY}
                            r={5}
                            fill={npc.mood === 'friendly' ? '#00ff88' : npc.mood === 'cautious' ? '#ffaa00' : '#ff4444'}
                            stroke="#000"
                            strokeWidth={1}
                            className="cursor-pointer hover:r-7"
                            onClick={(e) => {
                                e.stopPropagation();
                                setSelectedNPC(npc);
                            }}
                        >
                            <title>{npc.name}: {npc.activity}</title>
                        </circle>
                    );
                })}

                {/* Levels indicator */}
                {building.levels > 1 && (
                    <text
                        x={building.polygon[0][0] + 5}
                        y={building.polygon[0][1] + 12}
                        className="fill-zinc-500 font-mono pointer-events-none"
                        style={{ fontSize: '8px' }}
                    >
                        L{building.levels}
                    </text>
                )}
            </g>
        );
    };

    // Show loading state until mounted to prevent hydration mismatch
    if (!mounted) {
        return (
            <div className="min-h-screen bg-zinc-950 text-white flex items-center justify-center">
                <div className="text-center">
                    <div className="text-4xl animate-pulse mb-4">🌃</div>
                    <div className="text-cyan-400 font-mono">Loading City...</div>
                </div>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-zinc-950 text-white">
            {/* Header */}
            <header className="fixed top-0 left-0 right-0 h-14 bg-gradient-to-b from-zinc-900 to-transparent z-50 flex items-center px-4 border-b border-cyan-500/20">
                <h1 className="font-mono text-lg font-bold bg-gradient-to-r from-cyan-400 to-purple-400 bg-clip-text text-transparent">
                    AO WORLD ENGINE
                </h1>
                <nav className="ml-8 flex gap-4">
                    <Button variant="ghost" size="sm" className="text-cyan-400">Explore</Button>
                    <Button variant="ghost" size="sm" className="text-zinc-500 hover:text-cyan-400">Chat</Button>
                    <Button variant="ghost" size="sm" className="text-zinc-500 hover:text-cyan-400">Graph</Button>
                </nav>
            </header>

            <div className="pt-14 flex h-screen">
                {/* Main Canvas */}
                <div className="flex-1 relative overflow-hidden">
                    <svg
                        viewBox="0 0 800 500"
                        className="w-full h-full"
                        style={{ background: 'linear-gradient(180deg, #0a0a0f 0%, #12121a 100%)' }}
                    >
                        {/* Grid lines */}
                        {[...Array(20)].map((_, i) => (
                            <line
                                key={`h${i}`}
                                x1={0}
                                y1={i * 25}
                                x2={800}
                                y2={i * 25}
                                stroke="rgba(0, 255, 255, 0.05)"
                                strokeWidth={0.5}
                            />
                        ))}
                        {[...Array(32)].map((_, i) => (
                            <line
                                key={`v${i}`}
                                x1={i * 25}
                                y1={0}
                                x2={i * 25}
                                y2={500}
                                stroke="rgba(0, 255, 255, 0.05)"
                                strokeWidth={0.5}
                            />
                        ))}

                        {/* District labels */}
                        {districts.map(district => (
                            <text
                                key={district.id}
                                x={district.buildings[0]?.polygon[0][0] || 0}
                                y={30}
                                className="fill-zinc-600 font-mono"
                                style={{ fontSize: '12px' }}
                            >
                                {district.name.toUpperCase()}
                            </text>
                        ))}

                        {/* Buildings */}
                        {districts.map(district =>
                            district.buildings.map(building => renderBuilding(building, district.color))
                        )}

                        {/* Streets */}
                        <path
                            d="M 0 300 L 800 300"
                            stroke="rgba(100, 100, 100, 0.5)"
                            strokeWidth={20}
                            strokeLinecap="round"
                        />
                        <path
                            d="M 250 0 L 250 500"
                            stroke="rgba(100, 100, 100, 0.5)"
                            strokeWidth={15}
                            strokeLinecap="round"
                        />
                    </svg>

                    {/* View Mode Buttons */}
                    <div className="absolute top-4 left-4 flex gap-2">
                        <Button variant="outline" size="sm" className="bg-black/50">District View</Button>
                        <Button variant="ghost" size="sm" className="text-zinc-500">Blueprint</Button>
                        <Button variant="ghost" size="sm" className="text-zinc-500">3D</Button>
                    </div>
                </div>

                {/* Right Panel */}
                <div className="w-80 p-4 space-y-4 overflow-y-auto border-l border-zinc-800">
                    {/* Time Controls */}
                    <TimeControls
                        currentTick={currentTick}
                        onTickChange={setCurrentTick}
                        isPlaying={isPlaying}
                        onPlayPause={() => setIsPlaying(!isPlaying)}
                        tickSpeed={tickSpeed}
                        onSpeedChange={setTickSpeed}
                    />

                    {/* Selected Building Info */}
                    {selectedBuilding && (
                        <Card className="bg-zinc-900/90 border-amber-500/30 backdrop-blur-sm">
                            <CardHeader className="pb-2">
                                <CardTitle className="text-amber-400 font-mono text-sm">
                                    🏢 {selectedBuilding.name}
                                </CardTitle>
                            </CardHeader>
                            <CardContent className="text-sm space-y-2">
                                <div className="flex justify-between">
                                    <span className="text-zinc-500">Type</span>
                                    <span className="text-zinc-300 capitalize">{selectedBuilding.type}</span>
                                </div>
                                <div className="flex justify-between">
                                    <span className="text-zinc-500">Levels</span>
                                    <span className="text-zinc-300">{selectedBuilding.levels}</span>
                                </div>
                                <div className="flex justify-between">
                                    <span className="text-zinc-500">Occupants</span>
                                    <span className="text-zinc-300">{npcs.filter(n => n.location === selectedBuilding.id).length}</span>
                                </div>
                                <Button
                                    variant="outline"
                                    size="sm"
                                    className="w-full mt-2"
                                    onClick={() => setSelectedNPC(npcs.find(n => n.location === selectedBuilding.id) || null)}
                                >
                                    View Occupants
                                </Button>
                            </CardContent>
                        </Card>
                    )}

                    {/* Selected NPC Info */}
                    {selectedNPC && (
                        <Card className="bg-zinc-900/90 border-green-500/30 backdrop-blur-sm">
                            <CardHeader className="pb-2">
                                <CardTitle className="text-green-400 font-mono text-sm flex items-center gap-2">
                                    👤 {selectedNPC.name}
                                </CardTitle>
                            </CardHeader>
                            <CardContent className="text-sm space-y-2">
                                <div className="flex justify-between">
                                    <span className="text-zinc-500">Activity</span>
                                    <span className="text-zinc-300 capitalize">{selectedNPC.activity}</span>
                                </div>
                                <div className="flex justify-between">
                                    <span className="text-zinc-500">Mood</span>
                                    <span className={`capitalize ${selectedNPC.mood === 'friendly' ? 'text-green-400' :
                                        selectedNPC.mood === 'cautious' ? 'text-amber-400' : 'text-red-400'
                                        }`}>{selectedNPC.mood}</span>
                                </div>
                                <Button variant="default" size="sm" className="w-full mt-2 bg-cyan-600 hover:bg-cyan-500">
                                    💬 Chat with {selectedNPC.name}
                                </Button>
                            </CardContent>
                        </Card>
                    )}

                    {/* Scene Generator */}
                    <SceneGenerator
                        locationId={selectedBuilding?.id || 'undercity'}
                        locationName={selectedBuilding?.name || 'Undercity District'}
                        currentTick={currentTick}
                        apiBaseUrl={API_BASE}
                    />
                </div>
            </div>
        </div>
    );
}
