'use client';

import { useState, useEffect, useCallback, Suspense } from 'react';
import Link from 'next/link';
import { useSearchParams } from 'next/navigation';
import { TimeControls } from '@/components/TimeControls';
import { SceneGenerator } from '@/components/SceneGenerator';
import { TimelineBar } from '@/components/TimelineBar';
import { BuildingBlueprint } from '@/components/BuildingBlueprint';
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
    // Extended bio fields
    archetype?: string;
    mbti?: string;
    zodiac?: string;
    faction?: string;
    role?: string;
    traits?: string[];
    catchphrase?: string;
    // Home/workplace for role calculation
    home?: string;
    workplace?: string;
}

interface District {
    id: string;
    name: string;
    color: string;
    buildings: Building[];
}

const API_BASE = 'https://ao-world-engine-api-1071951656531.us-central1.run.app';

// Initial districts data - expanded city
const INITIAL_DISTRICTS: District[] = [
    {
        id: 'undercity',
        name: 'Undercity',
        color: '#1a1a2e',
        buildings: [
            { id: 'B001', name: "Felix's Bar", type: 'commercial', polygon: [[50, 150], [150, 150], [150, 220], [50, 220]], levels: 2, occupants: ['felix', 'charlie', 'mason'] },
            { id: 'B002', name: 'Abandoned Warehouse', type: 'industrial', polygon: [[170, 130], [280, 130], [280, 250], [170, 250]], levels: 3, occupants: ['ghost'] },
            { id: 'B003', name: 'Neon Motel', type: 'residential', polygon: [[50, 250], [130, 250], [130, 320], [50, 320]], levels: 4, occupants: ['drifter_1', 'drifter_2'] },
            { id: 'B004', name: 'Chop Shop', type: 'industrial', polygon: [[150, 270], [250, 270], [250, 340], [150, 340]], levels: 1, occupants: ['mechanic'] },
        ],
    },
    {
        id: 'market',
        name: 'Market District',
        color: '#2d2d44',
        buildings: [
            { id: 'B010', name: 'Central Market', type: 'commercial', polygon: [[350, 80], [520, 80], [520, 180], [350, 180]], levels: 1, occupants: ['vendor_1', 'vendor_2', 'vendor_3'] },
            { id: 'B011', name: 'Tech Shop', type: 'commercial', polygon: [[350, 200], [450, 200], [450, 280], [350, 280]], levels: 2, occupants: ['orion', 'assistant'] },
            { id: 'B012', name: 'Noodle Stand', type: 'commercial', polygon: [[470, 200], [550, 200], [550, 260], [470, 260]], levels: 1, occupants: ['chef_lin'] },
            { id: 'B013', name: 'Pawn Shop', type: 'commercial', polygon: [[350, 300], [430, 300], [430, 370], [350, 370]], levels: 2, occupants: ['dealer'] },
            { id: 'B014', name: 'Info Broker', type: 'commercial', polygon: [[450, 280], [540, 280], [540, 350], [450, 350]], levels: 1, occupants: ['whisper'] },
        ],
    },
    {
        id: 'temple',
        name: 'Temple District',
        color: '#3d2d2d',
        buildings: [
            { id: 'B016', name: 'Citizen Processing', type: 'temple', polygon: [[620, 100], [780, 100], [780, 220], [700, 250], [620, 220]], levels: 5, occupants: ['inquisitor_1', 'clerk_1', 'clerk_2'] },
            { id: 'B017', name: 'Archive Tower', type: 'temple', polygon: [[620, 270], [720, 270], [720, 380], [620, 380]], levels: 8, occupants: ['archivist'] },
            { id: 'B018', name: 'Confession Hall', type: 'temple', polygon: [[740, 250], [820, 250], [820, 340], [740, 340]], levels: 3, occupants: ['confessor'] },
        ],
    },
    {
        id: 'residential',
        name: 'Hab Blocks',
        color: '#252538',
        buildings: [
            { id: 'B020', name: 'Block A-7', type: 'residential', polygon: [[50, 380], [150, 380], [150, 480], [50, 480]], levels: 12, occupants: ['resident_1', 'resident_2', 'resident_3'] },
            { id: 'B021', name: 'Block A-8', type: 'residential', polygon: [[170, 380], [270, 380], [270, 480], [170, 480]], levels: 12, occupants: ['resident_4', 'resident_5'] },
            { id: 'B022', name: 'Clinic', type: 'commercial', polygon: [[290, 400], [380, 400], [380, 470], [290, 470]], levels: 2, occupants: ['doc_mercy', 'nurse'] },
        ],
    },
];

// Cyberpunk name generator
const FIRST_NAMES = ['Zero', 'Nova', 'Kai', 'Raven', 'Phoenix', 'Ghost', 'Blade', 'Cipher', 'Echo', 'Frost', 'Hex', 'Jinx', 'Neon', 'Pixel', 'Rogue', 'Shadow', 'Spike', 'Storm', 'Volt', 'Wire', 'Ash', 'Drake', 'Ember', 'Flux', 'Glitch', 'Haze', 'Ion', 'Jazz', 'Kira', 'Luna', 'Max', 'Nico', 'Ori', 'Pulse', 'Quinn', 'Rex', 'Sage', 'Trix', 'Vex', 'Wolf'];
const LAST_NAMES = ['Black', 'Chen', 'Vance', 'Reyes', 'Park', 'Kim', 'Silva', 'Tanaka', 'Okafor', 'Petrov', 'Sato', 'Garcia', 'Wei', 'Nakamura', 'Hassan', 'Volkov', 'Martinez', 'Zhang', 'Singh', 'Yamamoto', 'Frost', 'Stone', 'Steel', 'Cross', 'Drake', 'Grey', 'Hart', 'Kane', 'Lynch', 'Moon'];
const ACTIVITIES = ['working', 'trading', 'walking', 'talking', 'resting', 'eating', 'drinking', 'watching', 'waiting', 'hiding', 'reading', 'sleeping', 'praying', 'shopping', 'gambling', 'hacking', 'crafting', 'patrolling'];
const MOODS = ['friendly', 'cautious', 'nervous', 'calm', 'busy', 'tired', 'focused', 'cheerful', 'cold', 'secretive'];

// Determine NPC role in a building based on their home/workplace vs current location
function getNPCRole(npc: NPC, buildingId: string, buildingType: string): string {
    // If they LIVE here - they're a resident
    if (npc.home === buildingId) {
        if (npc.archetype?.includes('Bartender') || npc.archetype?.includes('Broker')) return 'Owner';
        return 'Resident';
    }

    // If they WORK here - employee/owner type
    if (npc.workplace === buildingId) {
        if (npc.archetype?.includes('vendor') || npc.archetype?.includes('Merchant')) return 'Vendor';
        if (npc.archetype?.includes('service')) return 'Staff';
        if (npc.archetype?.includes('guard')) return 'Security';
        if (npc.archetype?.includes('worker')) return 'Worker';
        if (buildingType === 'commercial' || buildingType === 'shop') return 'Clerk';
        if (buildingType === 'entertainment' || buildingType === 'bar') return 'Staff';
        if (buildingType === 'restaurant') return 'Server';
        return 'Employee';
    }

    // They're visiting - determine visitor type based on activity and building type
    const activity = npc.activity?.toLowerCase() || '';
    if (activity === 'shopping') return 'Customer';
    if (activity === 'drinking' || activity === 'socializing') return 'Patron';
    if (activity === 'eating') return 'Diner';
    if (activity === 'gambling') return 'Gambler';
    if (activity === 'patrol') return 'Guard';
    if (activity === 'mission' || activity === 'intel') return 'Agent';
    if (buildingType === 'commercial') return 'Customer';
    if (buildingType === 'entertainment' || buildingType === 'bar') return 'Patron';
    if (buildingType === 'restaurant') return 'Diner';
    return 'Visitor';
}

function generateNPCs(districts: District[], count: number): NPC[] {
    const npcs: NPC[] = [];
    const allBuildings = districts.flatMap(d => d.buildings);

    for (let i = 0; i < count; i++) {
        const firstIdx = i % FIRST_NAMES.length;
        const lastIdx = Math.floor(i / FIRST_NAMES.length) % LAST_NAMES.length;
        const building = allBuildings[i % allBuildings.length];

        npcs.push({
            id: `npc_${i.toString().padStart(4, '0')}`,
            name: `${FIRST_NAMES[firstIdx]} ${LAST_NAMES[lastIdx]}`,
            location: building?.id || 'B001',
            activity: ACTIVITIES[i % ACTIVITIES.length],
            mood: MOODS[i % MOODS.length],
        });
    }
    return npcs;
}

function ExplorePageContent() {
    const searchParams = useSearchParams();
    const npcIdFromUrl = searchParams.get('npc');
    const buildingIdFromUrl = searchParams.get('building');

    // State - initialized as empty/defaults to avoid hydration mismatch
    const [mounted, setMounted] = useState(false);
    const [currentTick, setCurrentTick] = useState(100);
    const [isPlaying, setIsPlaying] = useState(false);
    const [tickSpeed, setTickSpeed] = useState(1);
    const [selectedBuilding, setSelectedBuilding] = useState<Building | null>(null);
    const [selectedNPC, setSelectedNPC] = useState<NPC | null>(null);
    const [npcs, setNpcs] = useState<NPC[]>([]);
    const [districts, setDistricts] = useState<District[]>([]);
    const [showBlueprint, setShowBlueprint] = useState(false);
    const [expandedNPCList, setExpandedNPCList] = useState(false); // NEW: show all NPCs

    // Timeline events
    const [timelineEvents, setTimelineEvents] = useState([
        { tick: 10, timestamp: 'Day 1, 10:00', type: 'gossip', description: 'Rumors spreading in the Market', participants: ['Old Chen', 'Mika'] },
        { tick: 35, timestamp: 'Day 2, 11:00', type: 'trade', description: 'Tech parts sold at Tech Shop', participants: ['Orion', 'Pixel'] },
        { tick: 58, timestamp: 'Day 3, 10:00', type: 'conflict', description: 'Altercation at Neon Motel', participants: ['Kira', 'Ghost'] },
        { tick: 72, timestamp: 'Day 4, 00:00', type: 'news', description: 'New regulation from Temple', participants: ['Inquisitor Vex'] },
        { tick: 95, timestamp: 'Day 4, 23:00', type: 'friendly_chat', description: 'Patrons chatting at Felix\'s Bar', participants: ['Felix', 'Charlie', 'Mason'] },
    ]);

    // Pan and zoom state
    const [zoom, setZoom] = useState(1);
    const [pan, setPan] = useState({ x: 0, y: 0 });
    const [isDragging, setIsDragging] = useState(false);
    const [dragStart, setDragStart] = useState({ x: 0, y: 0 });

    // Initialize on mount - fetch from API, fallback to generated data
    useEffect(() => {
        setMounted(true);

        // Load buildings from API and merge with layout from INITIAL_DISTRICTS
        const loadBuildings = async () => {
            try {
                const response = await fetch(`${API_BASE}/api/buildings`);
                if (response.ok) {
                    const data = await response.json();
                    const apiBuildings = data.buildings || data;
                    if (Array.isArray(apiBuildings) && apiBuildings.length > 0) {
                        // Create a map of API buildings by ID
                        const apiBuildingMap = new Map<string, { name: string; type: string }>();
                        apiBuildings.forEach((b: { id: string; name: string; type: string }) => {
                            apiBuildingMap.set(b.id, { name: b.name, type: b.type });
                        });

                        // Merge API data with layout from INITIAL_DISTRICTS
                        const updatedDistricts = INITIAL_DISTRICTS.map(district => ({
                            ...district,
                            buildings: district.buildings.map(building => {
                                const apiData = apiBuildingMap.get(building.id);
                                if (apiData) {
                                    return {
                                        ...building,
                                        name: apiData.name,
                                        type: apiData.type as 'residential' | 'commercial' | 'temple' | 'industrial',
                                    };
                                }
                                return building;
                            })
                        }));
                        setDistricts(updatedDistricts);
                        console.log(`Synced ${apiBuildingMap.size} buildings from API`);
                    }
                }
            } catch (error) {
                console.log('Building API fetch failed, using defaults:', error);
                setDistricts(INITIAL_DISTRICTS);
            }
        };
        loadBuildings();

        // Try to fetch NPCs from API
        const loadNPCs = async () => {
            try {
                const response = await fetch(`${API_BASE}/api/npcs/all?limit=800`);
                if (response.ok) {
                    const data = await response.json();
                    const apiNPCs = data.npcs || data;
                    if (Array.isArray(apiNPCs) && apiNPCs.length > 0) {
                        // Map API NPCs to our format
                        const mappedNPCs: NPC[] = apiNPCs.map((n: Record<string, unknown>) => ({
                            id: n.id as string,
                            name: n.name as string,
                            location: (n.home as string) || 'B001', // Start at home
                            activity: 'sleeping', // Default to sleeping (will update on tick)
                            mood: MOODS[Math.floor(Math.random() * MOODS.length)],
                            archetype: n.archetype as string,
                            faction: n.faction as string,
                            role: n.role as string,
                            mbti: (n.personality as { mbti?: string })?.mbti,
                            traits: Array.isArray((n.personality as { all_traits?: string[] })?.all_traits)
                                ? (n.personality as { all_traits: string[] }).all_traits.slice(0, 5)
                                : undefined,
                            // Home/workplace for role calculation
                            home: n.home as string,
                            workplace: n.workplace as string,
                        }));
                        setNpcs(mappedNPCs);
                        console.log(`Loaded ${mappedNPCs.length} NPCs from API`);
                        return;
                    }
                }
            } catch (error) {
                console.log('API fetch failed, using generated data:', error);
            }
            // Fallback to generated data
            setNpcs(generateNPCs(INITIAL_DISTRICTS, 800));
        };
        loadNPCs();
    }, []);

    // Deep linking: auto-select NPC or building from URL parameters
    useEffect(() => {
        if (!mounted) return;

        // Auto-select NPC from URL
        if (npcIdFromUrl && npcs.length > 0 && !selectedNPC) {
            const npcFromUrl = npcs.find(n => n.id === npcIdFromUrl || n.name.toLowerCase().replace(/\s+/g, '_') === npcIdFromUrl.toLowerCase());
            if (npcFromUrl) {
                setSelectedNPC(npcFromUrl);
                // Also select the building they're in
                const allBuildings = districts.flatMap(d => d.buildings);
                const building = allBuildings.find(b => b.id === npcFromUrl.location);
                if (building) setSelectedBuilding(building);
                console.log(`Deep link: auto-selected NPC ${npcFromUrl.name}`);
            }
        }

        // Auto-select building from URL
        if (buildingIdFromUrl && districts.length > 0 && !selectedBuilding) {
            const allBuildings = districts.flatMap(d => d.buildings);
            const building = allBuildings.find(b => b.id === buildingIdFromUrl || b.name.toLowerCase().replace(/\s+/g, '_') === buildingIdFromUrl.toLowerCase());
            if (building) {
                setSelectedBuilding(building);
                console.log(`Deep link: auto-selected building ${building.name}`);
            }
        }
    }, [npcIdFromUrl, buildingIdFromUrl, npcs, districts, mounted, selectedNPC, selectedBuilding]);

    // Auto-advance tick when playing
    useEffect(() => {
        if (!isPlaying || !mounted) return;

        const interval = setInterval(() => {
            setCurrentTick(prev => prev + 1);
        }, 1000 / tickSpeed);

        return () => clearInterval(interval);
    }, [isPlaying, tickSpeed, mounted]);

    // Fetch NPC states when tick changes (every 2 ticks = ~12 min game time)
    useEffect(() => {
        if (!mounted) return;

        // Update every 2 ticks for smoother movement (~12 min game time between updates)
        if (currentTick % 2 !== 0) return;

        const fetchNPCStates = async () => {
            try {
                // Request full=true to get ALL 800 NPC states
                const response = await fetch(`${API_BASE}/api/simulation/tick?tick=${currentTick}&full=true`);
                if (response.ok) {
                    const data = await response.json();
                    const npcStates = data.npc_states || [];

                    if (Array.isArray(npcStates) && npcStates.length > 0) {
                        // Update NPC locations and activities from API
                        setNpcs(prevNpcs => {
                            // Create a map of API states by ID
                            const stateMap = new Map<string, { location: string; activity: string; mood: string }>();
                            npcStates.forEach((s: { npc_id: string; location: string; activity: string; mood: string }) => {
                                stateMap.set(s.npc_id, {
                                    location: s.location,
                                    activity: s.activity,
                                    mood: s.mood
                                });
                            });

                            // Update existing NPCs with new states
                            let updatedCount = 0;
                            const updated = prevNpcs.map(npc => {
                                const apiState = stateMap.get(npc.id);
                                if (apiState) {
                                    updatedCount++;
                                    return {
                                        ...npc,
                                        location: apiState.location,
                                        activity: apiState.activity,
                                        mood: apiState.mood
                                    };
                                }
                                return npc;
                            });
                            console.log(`Tick ${currentTick}: Updated ${updatedCount}/${npcStates.length} NPC states`);
                            return updated;
                        });
                    }
                }
            } catch (error) {
                console.log('Failed to fetch NPC states:', error);
            }
        };

        fetchNPCStates();
    }, [currentTick, mounted]);

    // Fetch NPCs - only fetch if API available, otherwise use mock data
    const fetchNPCs = useCallback(async () => {
        if (!mounted) return; // Don't fetch until mounted
        try {
            const response = await fetch(`${API_BASE}/api/npcs/all?limit=800`);
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
        // Match NPCs to building by location (workplace or home)
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

                {/* NPC dots - limit to 5 visible per building */}
                {buildingNPCs.slice(0, 5).map((npc, i) => {
                    const centerX = building.polygon.reduce((sum, p) => sum + p[0], 0) / building.polygon.length;
                    const centerY = building.polygon.reduce((sum, p) => sum + p[1], 0) / building.polygon.length + 15;
                    const isSelected = selectedNPC?.id === npc.id;
                    return (
                        <circle
                            key={npc.id}
                            cx={centerX + (i * 12) - (Math.min(buildingNPCs.length, 5) - 1) * 6}
                            cy={centerY}
                            r={isSelected ? 6 : 4}
                            fill={npc.mood === 'friendly' ? '#00ff88' : npc.mood === 'cautious' ? '#ffaa00' : '#ff4444'}
                            stroke={isSelected ? '#fff' : '#000'}
                            strokeWidth={1}
                            className="cursor-pointer transition-all hover:opacity-80"
                            style={{ filter: isSelected ? 'drop-shadow(0 0 4px #0ff)' : undefined }}
                            onClick={(e) => {
                                e.stopPropagation();
                                setSelectedNPC(npc);
                            }}
                        >
                            <title>{npc.name}: {npc.activity}</title>
                        </circle>
                    );
                })}
                {/* Show count if more than 5 NPCs */}
                {buildingNPCs.length > 5 && (
                    <text
                        x={building.polygon.reduce((sum, p) => sum + p[0], 0) / building.polygon.length + 35}
                        y={building.polygon.reduce((sum, p) => sum + p[1], 0) / building.polygon.length + 18}
                        className="fill-cyan-400 font-mono pointer-events-none"
                        style={{ fontSize: '9px' }}
                    >
                        +{buildingNPCs.length - 5}
                    </text>
                )}

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
            <header className="fixed top-0 left-0 right-0 h-14 bg-zinc-900 z-50 flex items-center px-4 border-b border-zinc-800">
                <Link href="/" className="font-mono text-lg font-bold text-cyan-400 tracking-wider">
                    AO WORLD ENGINE
                </Link>
                <nav className="ml-8 flex gap-4">
                    <Link href="/explore" className="text-sm font-medium text-white px-3 py-1.5 rounded transition-colors">
                        Explore
                    </Link>
                    <Link href="/npcs" className="text-sm font-medium text-zinc-300 hover:text-white px-3 py-1.5 rounded transition-colors">
                        NPCs
                    </Link>
                    <Link href="/chat" className="text-sm font-medium text-zinc-300 hover:text-white px-3 py-1.5 rounded transition-colors">
                        Chat
                    </Link>
                    <Link href="/graph" className="text-sm font-medium text-zinc-300 hover:text-white px-3 py-1.5 rounded transition-colors">
                        Graph
                    </Link>
                </nav>
            </header>

            <div className="pt-14 flex h-screen">
                {/* Main Canvas */}
                <div
                    className="flex-1 relative overflow-hidden cursor-grab active:cursor-grabbing"
                    onMouseDown={(e) => {
                        setIsDragging(true);
                        setDragStart({ x: e.clientX - pan.x, y: e.clientY - pan.y });
                    }}
                    onMouseMove={(e) => {
                        if (isDragging) {
                            setPan({ x: e.clientX - dragStart.x, y: e.clientY - dragStart.y });
                        }
                    }}
                    onMouseUp={() => setIsDragging(false)}
                    onMouseLeave={() => setIsDragging(false)}
                    onWheel={(e) => {
                        e.preventDefault();
                        const delta = e.deltaY > 0 ? 0.9 : 1.1;
                        setZoom(prev => Math.min(Math.max(prev * delta, 0.5), 3));
                    }}
                >
                    <svg
                        viewBox="0 0 900 550"
                        className="w-full h-full"
                        style={{
                            background: 'linear-gradient(180deg, #0a0a0f 0%, #12121a 100%)',
                            transform: `scale(${zoom}) translate(${pan.x / zoom}px, ${pan.y / zoom}px)`,
                            transformOrigin: 'center center',
                        }}
                    >
                        {/* Grid lines */}
                        {[...Array(24)].map((_, i) => (
                            <line
                                key={`h${i}`}
                                x1={0}
                                y1={i * 25}
                                x2={900}
                                y2={i * 25}
                                stroke="rgba(0, 255, 255, 0.03)"
                                strokeWidth={0.5}
                            />
                        ))}
                        {[...Array(36)].map((_, i) => (
                            <line
                                key={`v${i}`}
                                x1={i * 25}
                                y1={0}
                                x2={i * 25}
                                y2={550}
                                stroke="rgba(0, 255, 255, 0.03)"
                                strokeWidth={0.5}
                            />
                        ))}

                        {/* District labels */}
                        {districts.map(district => (
                            <text
                                key={district.id}
                                x={district.buildings[0]?.polygon[0][0] || 0}
                                y={district.buildings[0]?.polygon[0][1] - 10 || 30}
                                className="fill-zinc-500 font-mono"
                                style={{ fontSize: '11px', fontWeight: 'bold' }}
                            >
                                {district.name.toUpperCase()}
                            </text>
                        ))}

                        {/* Streets */}
                        <path d="M 0 360 L 900 360" stroke="rgba(60, 60, 80, 0.6)" strokeWidth={25} />
                        <path d="M 300 0 L 300 550" stroke="rgba(60, 60, 80, 0.6)" strokeWidth={20} />
                        <path d="M 600 0 L 600 550" stroke="rgba(60, 60, 80, 0.6)" strokeWidth={20} />
                        {/* Street markings */}
                        <path d="M 0 360 L 900 360" stroke="rgba(255, 200, 0, 0.3)" strokeWidth={2} strokeDasharray="20 30" />

                        {/* Buildings */}
                        {districts.map(district =>
                            district.buildings.map(building => renderBuilding(building, district.color))
                        )}
                    </svg>

                    {/* Zoom Controls */}
                    <div className="absolute bottom-4 left-4 flex flex-col gap-2">
                        <Button
                            variant="outline"
                            size="sm"
                            className="bg-black/70 w-10 h-10 text-lg"
                            onClick={() => setZoom(prev => Math.min(prev * 1.2, 3))}
                        >
                            +
                        </Button>
                        <Button
                            variant="outline"
                            size="sm"
                            className="bg-black/70 w-10 h-10 text-lg"
                            onClick={() => setZoom(prev => Math.max(prev * 0.8, 0.5))}
                        >
                            −
                        </Button>
                        <Button
                            variant="outline"
                            size="sm"
                            className="bg-black/70 w-10 h-10 text-xs"
                            onClick={() => { setZoom(1); setPan({ x: 0, y: 0 }); }}
                        >
                            ⟲
                        </Button>
                    </div>

                    {/* Stats Overlay */}
                    <div className="absolute top-4 right-4 bg-black/70 px-3 py-2 rounded border border-cyan-500/30 font-mono text-xs">
                        <div className="text-cyan-400">NPCs: {npcs.length}</div>
                        <div className="text-purple-400">Buildings: {districts.reduce((sum, d) => sum + d.buildings.length, 0)}</div>
                        <div className="text-zinc-500">Zoom: {Math.round(zoom * 100)}%</div>
                    </div>

                    {/* View Mode Buttons */}
                    <div className="absolute top-4 left-4 flex gap-2">
                        <Button variant="outline" size="sm" className="bg-zinc-800 text-white border-zinc-600 hover:bg-zinc-700">District View</Button>
                        <Button
                            variant={showBlueprint ? "default" : "outline"}
                            size="sm"
                            className={showBlueprint ? "bg-cyan-600 text-white" : "bg-zinc-800 text-zinc-300 border-zinc-600 hover:bg-zinc-700 hover:text-white"}
                            onClick={() => setShowBlueprint(!showBlueprint)}
                        >
                            Blueprint
                        </Button>
                        <Button variant="outline" size="sm" className="bg-zinc-800 text-zinc-300 border-zinc-600 hover:bg-zinc-700 hover:text-white">3D</Button>
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

                    {/* Timeline Visualizer */}
                    <TimelineBar
                        currentTick={currentTick}
                        maxTick={200}
                        events={timelineEvents}
                        onTickChange={setCurrentTick}
                        onEventClick={(event) => console.log('Event clicked:', event)}
                    />

                    {/* Building Blueprint (shown when building selected + blueprint mode) */}
                    {showBlueprint && !selectedBuilding && (
                        <Card className="bg-zinc-900/90 border-cyan-500/30">
                            <CardContent className="p-4 text-center text-zinc-400">
                                <div className="text-3xl mb-2">🏗️</div>
                                <div className="text-sm">Click a building to view its blueprint</div>
                            </CardContent>
                        </Card>
                    )}
                    {selectedBuilding && showBlueprint && (
                        <BuildingBlueprint
                            building={{
                                ...selectedBuilding,
                                occupants: npcs.filter(n => n.location === selectedBuilding.id).map(n => n.name)
                            }}
                            onClose={() => setShowBlueprint(false)}
                            onNpcClick={(npcId) => {
                                const npc = npcs.find(n => n.name === npcId);
                                if (npc) setSelectedNPC(npc);
                            }}
                        />
                    )}

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
                                    <span className="text-cyan-400 font-bold">{npcs.filter(n => n.location === selectedBuilding.id).length}</span>
                                </div>

                                {/* Scrollable NPC list with role legend */}
                                <div className="mt-3 pt-2 border-t border-zinc-700">
                                    <div className="text-xs text-zinc-500 mb-1">NPCs in building:</div>
                                    {/* Role Legend */}
                                    <div className="flex flex-wrap gap-1 mb-2 text-[9px]">
                                        <span className="px-1 py-0.5 bg-emerald-500/20 text-emerald-400 rounded">Resident</span>
                                        <span className="px-1 py-0.5 bg-blue-500/20 text-blue-400 rounded">Employee</span>
                                        <span className="px-1 py-0.5 bg-purple-500/20 text-purple-400 rounded">Vendor</span>
                                        <span className="px-1 py-0.5 bg-yellow-500/20 text-yellow-400 rounded">Customer</span>
                                        <span className="px-1 py-0.5 bg-red-500/20 text-red-400 rounded">Security</span>
                                        <span className="px-1 py-0.5 bg-zinc-600/30 text-zinc-400 rounded">Visitor</span>
                                    </div>
                                    <div className="max-h-60 overflow-y-auto space-y-1">
                                        {npcs.filter(n => n.location === selectedBuilding.id).slice(0, expandedNPCList ? 500 : 50).map(npc => {
                                            const role = getNPCRole(npc, selectedBuilding.id, selectedBuilding.type);
                                            return (
                                                <button
                                                    key={npc.id}
                                                    onClick={() => setSelectedNPC(npc)}
                                                    onDoubleClick={() => window.location.href = `/npcs?npc=${encodeURIComponent(npc.name)}`}
                                                    className={`w-full text-left px-2 py-1 rounded text-xs flex items-center gap-2 ${selectedNPC?.id === npc.id
                                                        ? 'bg-cyan-600/30 border border-cyan-500/50'
                                                        : 'bg-zinc-800/50 hover:bg-zinc-700/50'
                                                        }`}
                                                    title="Double-click to view full profile"
                                                >
                                                    <span className={`w-2 h-2 rounded-full flex-shrink-0 ${npc.mood === 'friendly' ? 'bg-green-400' :
                                                        npc.mood === 'cautious' ? 'bg-amber-400' : 'bg-red-400'
                                                        }`} />
                                                    <span className="truncate flex-1">{npc.name}</span>
                                                    <span className={`text-[10px] px-1.5 py-0.5 rounded font-medium ${role === 'Resident' ? 'bg-emerald-500/20 text-emerald-400' :
                                                        role === 'Owner' ? 'bg-amber-500/20 text-amber-300' :
                                                            role === 'Employee' || role === 'Worker' ? 'bg-blue-500/20 text-blue-400' :
                                                                role === 'Staff' || role === 'Server' || role === 'Clerk' ? 'bg-sky-500/20 text-sky-400' :
                                                                    role === 'Vendor' ? 'bg-purple-500/20 text-purple-400' :
                                                                        role === 'Security' || role === 'Guard' ? 'bg-red-500/20 text-red-400' :
                                                                            role === 'Customer' || role === 'Patron' || role === 'Diner' || role === 'Gambler' ? 'bg-yellow-500/20 text-yellow-400' :
                                                                                'bg-zinc-600/30 text-zinc-400'
                                                        }`}>{role}</span>
                                                </button>
                                            );
                                        })}
                                        {npcs.filter(n => n.location === selectedBuilding.id).length > 50 && !expandedNPCList && (
                                            <button onClick={() => setExpandedNPCList(true)} className="w-full text-center text-cyan-400 hover:text-cyan-300 text-xs py-2 hover:bg-cyan-500/10 rounded cursor-pointer">
                                                + Show all {npcs.filter(n => n.location === selectedBuilding.id).length - 50} more...
                                            </button>
                                        )}
                                        {expandedNPCList && npcs.filter(n => n.location === selectedBuilding.id).length > 50 && (
                                            <button onClick={() => setExpandedNPCList(false)} className="w-full text-center text-zinc-400 hover:text-zinc-300 text-xs py-2 hover:bg-zinc-700/30 rounded cursor-pointer">
                                                ▲ Show less
                                            </button>
                                        )}
                                    </div>
                                </div>
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
                                {selectedNPC.role && (
                                    <p className="text-xs text-zinc-500 italic">{selectedNPC.role}</p>
                                )}
                            </CardHeader>
                            <CardContent className="text-xs space-y-2">
                                {/* Basic Info */}
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

                                {/* Personality Section */}
                                {(selectedNPC.archetype || selectedNPC.mbti || selectedNPC.zodiac) && (
                                    <div className="pt-2 mt-2 border-t border-zinc-700">
                                        <div className="text-zinc-400 font-mono mb-1">PERSONALITY</div>
                                        {selectedNPC.archetype && (
                                            <div className="flex justify-between">
                                                <span className="text-zinc-500">Archetype</span>
                                                <span className="text-purple-400">{selectedNPC.archetype}</span>
                                            </div>
                                        )}
                                        {selectedNPC.mbti && (
                                            <div className="flex justify-between">
                                                <span className="text-zinc-500">MBTI</span>
                                                <span className="text-cyan-400">{selectedNPC.mbti}</span>
                                            </div>
                                        )}
                                        {selectedNPC.zodiac && (
                                            <div className="flex justify-between">
                                                <span className="text-zinc-500">Zodiac</span>
                                                <span className="text-amber-400 capitalize">{selectedNPC.zodiac}</span>
                                            </div>
                                        )}
                                        {selectedNPC.faction && (
                                            <div className="flex justify-between">
                                                <span className="text-zinc-500">Faction</span>
                                                <span className="text-emerald-400">{selectedNPC.faction}</span>
                                            </div>
                                        )}
                                    </div>
                                )}

                                {/* Traits */}
                                {selectedNPC.traits && selectedNPC.traits.length > 0 && (
                                    <div className="pt-2 mt-2 border-t border-zinc-700">
                                        <div className="text-zinc-400 font-mono mb-1">TRAITS</div>
                                        <div className="flex flex-wrap gap-1">
                                            {selectedNPC.traits.slice(0, 5).map((trait, i) => (
                                                <span key={i} className="px-1.5 py-0.5 bg-zinc-800 rounded text-[10px] text-zinc-300 capitalize">
                                                    {trait.replace(/_/g, ' ')}
                                                </span>
                                            ))}
                                        </div>
                                    </div>
                                )}

                                {/* Catchphrase */}
                                {selectedNPC.catchphrase && (
                                    <div className="pt-2 mt-2 border-t border-zinc-700">
                                        <div className="text-zinc-400 font-mono mb-1">CATCHPHRASE</div>
                                        <p className="text-zinc-300 italic text-[11px]">"{selectedNPC.catchphrase}"</p>
                                    </div>
                                )}

                                <div className="flex gap-2 mt-3">
                                    <Button
                                        variant="default"
                                        size="sm"
                                        className="flex-1 bg-cyan-600 hover:bg-cyan-500"
                                        onClick={() => window.location.href = `/npcs?npc=${encodeURIComponent(selectedNPC.name)}`}
                                    >
                                        👤 Full Profile
                                    </Button>
                                    <Button
                                        variant="outline"
                                        size="sm"
                                        className="flex-1 border-cyan-500/50 text-cyan-400 hover:bg-cyan-600/20"
                                        onClick={() => window.location.href = `/chat?npc=${encodeURIComponent(selectedNPC.id)}`}
                                    >
                                        💬 Chat
                                    </Button>
                                </div>
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

// Wrap with Suspense for useSearchParams (required by Next.js)
export default function ExplorePage() {
    return (
        <Suspense fallback={<div className="min-h-screen bg-zinc-950 flex items-center justify-center"><span className="text-cyan-400">Loading city...</span></div>}>
            <ExplorePageContent />
        </Suspense>
    );
}
