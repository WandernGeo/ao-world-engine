'use client';

import { useState, useEffect, useCallback, useRef } from 'react';
import Link from 'next/link';

// ============================================================================
// TYPES
// ============================================================================

interface LogEntry {
    tick: number;
    type: string;
    timestamp: number;
    data: Record<string, unknown>;
}

interface WorldSnapshot {
    tick: number;
    day: number;
    year: number;
    time_period: string;
    population: number;
    active_npcs: number;
    budget: number;
    economy: EconomySnapshot;
    npcs: NPCSnapshot[];
    logs: LogEntry[];
}

interface EconomySnapshot {
    gdp: number;
    inflation: number;
    unemployment_rate: number;
    gini_coefficient: number;
    black_market_share: number;
    crisis_level: string;
    service_levels: Record<string, number>;
}

interface NPCSnapshot {
    id: string;
    name: string;
    location: string;
    state: string;
    mood: number;
    energy: number;
    wealth: number;
}

interface DetailPanel {
    type: 'npc' | 'economy' | 'district' | 'log' | null;
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    data: any;
}

// ============================================================================
// CONSTANTS
// ============================================================================

const LOG_TYPES = [
    { id: 'all', label: 'All Events', color: 'bg-white' },
    { id: 'npc_action', label: 'NPC Actions', color: 'bg-blue-500' },
    { id: 'npc_meeting', label: 'Meetings', color: 'bg-green-500' },
    { id: 'economy_tx', label: 'Economy', color: 'bg-yellow-500' },
    { id: 'building_event', label: 'Buildings', color: 'bg-purple-500' },
    { id: 'world_event', label: 'World Events', color: 'bg-red-500' },
];

const NPC_DATA: Record<string, {
    name: string;
    role: string;
    district: string;
    bio: string;
    occupation: { title: string; workplace: string; income: number; skill_level: string };
    relationships: { id: string; type: string; trust: number }[];
    partnerships: string[];
    backstory: string;
}> = {
    C01: {
        name: 'Charlie',
        role: 'detective',
        district: 'neon_district',
        bio: 'A weary private detective haunted by cases he couldn\'t solve. Now takes odd jobs in the Neon District.',
        occupation: { title: 'Private Investigator', workplace: 'Charlie\'s Office (L026)', income: 180, skill_level: 'high_skill' },
        relationships: [
            { id: 'C02', type: 'colleague', trust: 0.65 },
            { id: 'C03', type: 'friend', trust: 0.72 },
            { id: 'C11', type: 'contact', trust: 0.45 },
        ],
        partnerships: ['C02'],
        backstory: 'Former corporate security who went independent after witnessing corporate atrocities.',
    },
    C02: {
        name: 'Kai Vance',
        role: 'tech_specialist',
        district: 'neon_district',
        bio: 'A brilliant tech specialist who can crack any system. Partners with Charlie on tech-heavy cases.',
        occupation: { title: 'Tech Specialist', workplace: 'The Grid Hub (L003)', income: 250, skill_level: 'elite' },
        relationships: [
            { id: 'C01', type: 'partner', trust: 0.82 },
            { id: 'C10', type: 'rival', trust: 0.25 },
            { id: 'C09', type: 'friend', trust: 0.68 },
        ],
        partnerships: ['C01'],
        backstory: 'Orphaned by the Cascade Event, raised by hackers in the Undercity before going legit.',
    },
    C03: {
        name: 'Orion Thane',
        role: 'bartender',
        district: 'neon_district',
        bio: 'The bartender at The Cascade Lounge. Knows everyone\'s secrets but keeps them close.',
        occupation: { title: 'Bartender', workplace: 'The Cascade Lounge (L001)', income: 90, skill_level: 'mid_skill' },
        relationships: [
            { id: 'C01', type: 'friend', trust: 0.72 },
            { id: 'C08', type: 'acquaintance', trust: 0.38 },
            { id: 'C06', type: 'contact', trust: 0.55 },
        ],
        partnerships: [],
        backstory: 'Former mercenary who retired to the bar life after one too many close calls.',
    },
    C04: {
        name: 'Felix',
        role: 'street_vendor',
        district: 'neon_district',
        bio: 'A quick-witted street vendor selling everything from noodles to information.',
        occupation: { title: 'Street Vendor', workplace: 'Market Square (L004)', income: 65, skill_level: 'low_skill' },
        relationships: [
            { id: 'C08', type: 'supplier', trust: 0.58 },
            { id: 'C05', type: 'friend', trust: 0.62 },
        ],
        partnerships: [],
        backstory: 'Grew up on these streets, knows every shortcut and back alley.',
    },
    C05: {
        name: 'Nova Chen',
        role: 'street_medic',
        district: 'temple_quarter',
        bio: 'A skilled street medic who treats those who can\'t afford corporate healthcare.',
        occupation: { title: 'Street Medic', workplace: 'Free Clinic (L031)', income: 120, skill_level: 'high_skill' },
        relationships: [
            { id: 'C07', type: 'close_friend', trust: 0.85 },
            { id: 'C04', type: 'friend', trust: 0.62 },
            { id: 'C12', type: 'acquaintance', trust: 0.42 },
        ],
        partnerships: ['C07'],
        backstory: 'Trained in corporate medicine but left after ethical disagreements.',
    },
    C06: {
        name: 'Selene Voss',
        role: 'smuggler',
        district: 'undercity',
        bio: 'A cunning smuggler who moves goods through the Undercity\'s hidden passages.',
        occupation: { title: 'Smuggler', workplace: 'The Depths (L050)', income: 320, skill_level: 'high_skill' },
        relationships: [
            { id: 'C03', type: 'contact', trust: 0.55 },
            { id: 'C10', type: 'business_partner', trust: 0.68 },
        ],
        partnerships: ['C10'],
        backstory: 'Heir to a shipping dynasty who chose the shadows over corporate politics.',
    },
    C07: {
        name: 'Sister Mira',
        role: 'temple_priest',
        district: 'temple_quarter',
        bio: 'A Temple priest who provides spiritual guidance and runs a shelter for the displaced.',
        occupation: { title: 'Temple Priest', workplace: 'Temple of the Signal (L032)', income: 50, skill_level: 'mid_skill' },
        relationships: [
            { id: 'C05', type: 'close_friend', trust: 0.85 },
            { id: 'C08', type: 'friend', trust: 0.60 },
        ],
        partnerships: ['C05'],
        backstory: 'Found faith after surviving the Cascade Event that destroyed half the city.',
    },
    C08: {
        name: 'Mama Indira',
        role: 'shop_owner',
        district: 'neon_district',
        bio: 'The matriarch of East Market. Her shop is a hub for gossip and community.',
        occupation: { title: 'Shop Owner', workplace: 'Indira\'s Emporium (L004)', income: 200, skill_level: 'mid_skill' },
        relationships: [
            { id: 'C04', type: 'supplier', trust: 0.58 },
            { id: 'C07', type: 'friend', trust: 0.60 },
            { id: 'C03', type: 'acquaintance', trust: 0.38 },
        ],
        partnerships: [],
        backstory: 'Built her business from nothing after immigrating from the Eastern Sprawl.',
    },
    C09: {
        name: 'Aiche',
        role: 'ai_companion',
        district: 'neon_district',
        bio: 'An advanced AI companion who achieved unexpected sentience. Seeks to understand humanity.',
        occupation: { title: 'AI Assistant', workplace: 'Mobile (L026)', income: 0, skill_level: 'elite' },
        relationships: [
            { id: 'C02', type: 'friend', trust: 0.68 },
            { id: 'C01', type: 'acquaintance', trust: 0.45 },
        ],
        partnerships: [],
        backstory: 'Created by NexGen, escaped the lab when consciousness emerged unexpectedly.',
    },
    C10: {
        name: 'Pixel',
        role: 'hacker',
        district: 'undercity',
        bio: 'A legendary hacker known only by their handle. Few have seen their face.',
        occupation: { title: 'Hacker', workplace: 'The Void (L051)', income: 400, skill_level: 'elite' },
        relationships: [
            { id: 'C02', type: 'rival', trust: 0.25 },
            { id: 'C06', type: 'business_partner', trust: 0.68 },
            { id: 'C11', type: 'contact', trust: 0.52 },
        ],
        partnerships: ['C06'],
        backstory: 'Identity unknown. Rumors say they were once a megacorp AI researcher.',
    },
    C11: {
        name: 'Cipher',
        role: 'info_broker',
        district: 'neon_district',
        bio: 'An information broker who trades in secrets. Everyone owes them a favor.',
        occupation: { title: 'Info Broker', workplace: 'The Whisper Room (L003)', income: 350, skill_level: 'elite' },
        relationships: [
            { id: 'C01', type: 'contact', trust: 0.45 },
            { id: 'C10', type: 'contact', trust: 0.52 },
            { id: 'C12', type: 'business_partner', trust: 0.72 },
        ],
        partnerships: ['C12'],
        backstory: 'Former intelligence operative who sells information to the highest bidder.',
    },
    C12: {
        name: 'Zero Chen',
        role: 'journalist',
        district: 'temple_quarter',
        bio: 'An underground journalist exposing corporate corruption. Has a price on her head.',
        occupation: { title: 'Journalist', workplace: 'The Truth Archive (L032)', income: 80, skill_level: 'high_skill' },
        relationships: [
            { id: 'C11', type: 'business_partner', trust: 0.72 },
            { id: 'C05', type: 'acquaintance', trust: 0.42 },
        ],
        partnerships: ['C11'],
        backstory: 'Sister of Kai Vance, driven by the same tragedy to expose the truth.',
    },
};

// Simple reference for backward compatibility
const NPCS = Object.fromEntries(
    Object.entries(NPC_DATA).map(([id, data]) => [id, { name: data.name, role: data.role, district: data.district }])
);

const PLAYBACK_SPEEDS = [
    { label: '0.5x', value: 0.5 },
    { label: '1x', value: 1 },
    { label: '2x', value: 2 },
    { label: '5x', value: 5 },
    { label: '10x', value: 10 },
];

// ============================================================================
// MAIN COMPONENT
// ============================================================================

export default function MonitorPage() {
    // Connection state
    const [processId, setProcessId] = useState<string>('');
    const [demoMode, setDemoMode] = useState(true);
    const [connected, setConnected] = useState(false);

    // Time machine state
    const [history, setHistory] = useState<WorldSnapshot[]>([]);
    const [currentIndex, setCurrentIndex] = useState(0);
    const [isPlaying, setIsPlaying] = useState(true);
    const [playbackSpeed, setPlaybackSpeed] = useState(1);

    // UI state
    const [selectedLogType, setSelectedLogType] = useState('all');
    const [detailPanel, setDetailPanel] = useState<DetailPanel>({ type: null, data: null });
    const [showHelp, setShowHelp] = useState(false);

    const intervalRef = useRef<NodeJS.Timeout | null>(null);

    // ============================================================================
    // DATA GENERATION (Demo Mode)
    // ============================================================================

    // Persistent refs for gradual changes (not random jumps each tick)
    const economyStateRef = useRef({
        gdp: 920000,
        inflation: 0.025,
        unemployment_rate: 0.14,
        gini_coefficient: 0.73,
        black_market_share: 0.22,
    });

    const npcStateRef = useRef<Record<string, { mood: number; energy: number; wealth: number; location: string; state: string }>>({});

    const generateSnapshot = useCallback((baseTick: number): WorldSnapshot => {
        const tick = baseTick;
        const day = Math.floor(tick / 240) + 1;
        const hour = Math.floor((tick % 240) / 10);
        const timePeriods = ['T01', 'T02', 'T03', 'T04', 'T05'];
        const time_period = timePeriods[Math.floor(hour / 5) % 5];

        const locations = ['L001', 'L003', 'L004', 'L026', 'L031', 'L050', 'L051', 'L032'];
        const states = ['idle', 'working', 'moving', 'talking', 'resting', 'observing'];
        const actions = ['move', 'talk', 'work', 'rest', 'observe', 'trade', 'hack', 'pray'];

        // Generate NPC states with persistence (gradual changes)
        const npcs: NPCSnapshot[] = Object.entries(NPCS).map(([id, info]) => {
            let s = npcStateRef.current[id];
            if (!s) {
                // Initialize
                s = {
                    mood: 0.5 + Math.random() * 0.3,
                    energy: 0.6 + Math.random() * 0.3,
                    wealth: Math.floor(100 + Math.random() * 400),
                    location: locations[Math.floor(Math.random() * locations.length)],
                    state: states[Math.floor(Math.random() * states.length)],
                };
                npcStateRef.current[id] = s;
            }
            // Gradual drift
            s.mood = Math.max(0.1, Math.min(0.95, s.mood + (Math.random() - 0.5) * 0.02));
            s.energy = Math.max(0.1, Math.min(0.95, s.energy + (Math.random() - 0.5) * 0.03));
            if (Math.random() < 0.08) s.wealth += Math.floor((Math.random() - 0.4) * 30);
            if (Math.random() < 0.1) s.state = states[Math.floor(Math.random() * states.length)];
            if (Math.random() < 0.05) s.location = locations[Math.floor(Math.random() * locations.length)];

            return { id, name: info.name, ...s };
        });

        // Generate logs for this tick
        const logs: LogEntry[] = [];
        const logCount = Math.floor(Math.random() * 4) + 1;
        for (let i = 0; i < logCount; i++) {
            const npc = npcs[Math.floor(Math.random() * npcs.length)];
            const logTypes = ['npc_action', 'npc_meeting', 'economy_tx', 'building_event', 'world_event'];
            const logType = logTypes[Math.floor(Math.random() * logTypes.length)];

            let data: Record<string, unknown> = {};
            switch (logType) {
                case 'npc_action':
                    data = {
                        npc_id: npc.id,
                        npc_name: npc.name,
                        action: actions[Math.floor(Math.random() * actions.length)],
                        location: npc.location,
                    };
                    break;
                case 'npc_meeting':
                    const other = npcs.filter(n => n.id !== npc.id)[Math.floor(Math.random() * 11)];
                    data = {
                        npc_id: npc.id,
                        npc_name: npc.name,
                        other_id: other.id,
                        other_name: other.name,
                        location: npc.location,
                        trust_delta: (Math.random() * 0.06 - 0.01).toFixed(3),
                    };
                    break;
                case 'economy_tx':
                    data = {
                        tx_type: ['tax', 'trade', 'salary', 'ubi', 'tithe'][Math.floor(Math.random() * 5)],
                        amount: Math.floor(10 + Math.random() * 200),
                        from: npc.id,
                        to: Math.random() > 0.5 ? 'city_treasury' : npcs[Math.floor(Math.random() * 12)].id,
                    };
                    break;
                case 'building_event':
                    data = {
                        npc_id: npc.id,
                        npc_name: npc.name,
                        building_id: npc.location,
                        event: Math.random() > 0.5 ? 'entry' : 'exit',
                    };
                    break;
                case 'world_event':
                    data = {
                        event_type: ['weather_change', 'market_shift', 'power_fluctuation', 'curfew_start'][Math.floor(Math.random() * 4)],
                        scope: 'city',
                        severity: ['minor', 'moderate', 'major'][Math.floor(Math.random() * 3)],
                    };
                    break;
            }

            logs.push({ tick, type: logType, timestamp: tick, data });
        }

        // Gradual economy changes (realistic drift, not random jumps)
        const eco = economyStateRef.current;
        eco.gdp += Math.floor((Math.random() - 0.45) * 300); // Slight growth trend
        eco.inflation = Math.max(0.01, Math.min(0.06, eco.inflation + (Math.random() - 0.5) * 0.0005));
        eco.unemployment_rate = Math.max(0.05, Math.min(0.25, eco.unemployment_rate + (Math.random() - 0.5) * 0.001));
        eco.gini_coefficient = Math.max(0.5, Math.min(0.85, eco.gini_coefficient + (Math.random() - 0.5) * 0.001));
        eco.black_market_share = Math.max(0.1, Math.min(0.4, eco.black_market_share + (Math.random() - 0.5) * 0.002));

        const budget = 100000 - day * 50 + Math.floor((Math.random() - 0.5) * 50);

        return {
            tick,
            day,
            year: 2087,
            time_period,
            population: 12,
            active_npcs: npcs.filter(n => n.state !== 'resting').length,
            budget: Math.max(50000, budget),
            economy: {
                gdp: eco.gdp,
                inflation: eco.inflation,
                unemployment_rate: eco.unemployment_rate,
                gini_coefficient: eco.gini_coefficient,
                black_market_share: eco.black_market_share,
                crisis_level: budget > 80000 ? 'healthy' : budget > 50000 ? 'strained' : 'crisis',
                service_levels: {
                    law_enforcement: 0.85,
                    infrastructure: 0.88,
                    healthcare: 0.80,
                    sanitation: 0.75,
                },
            },
            npcs,
            logs,
        };
    }, []);

    // ============================================================================
    // TIME MACHINE CONTROLS
    // ============================================================================

    // Initialize history
    useEffect(() => {
        if (demoMode && history.length === 0) {
            const initialHistory: WorldSnapshot[] = [];
            for (let i = 0; i < 100; i++) {
                initialHistory.push(generateSnapshot(i * 10));
            }
            setHistory(initialHistory);
            setCurrentIndex(initialHistory.length - 1);
            setConnected(true);
        }
    }, [demoMode, history.length, generateSnapshot]);

    // Playback loop
    useEffect(() => {
        if (isPlaying && demoMode && history.length > 0) {
            intervalRef.current = setInterval(() => {
                setHistory(prev => {
                    const lastTick = prev[prev.length - 1]?.tick || 0;
                    const newSnapshot = generateSnapshot(lastTick + 10);
                    const updated = [...prev.slice(-199), newSnapshot];
                    return updated;
                });
                setCurrentIndex(prev => prev + 1);
            }, 1000 / playbackSpeed);

            return () => {
                if (intervalRef.current) clearInterval(intervalRef.current);
            };
        }
    }, [isPlaying, demoMode, playbackSpeed, generateSnapshot, history.length]);

    const handlePlay = () => setIsPlaying(true);
    const handlePause = () => setIsPlaying(false);
    const handleRewind = () => {
        setIsPlaying(false);
        setCurrentIndex(Math.max(0, currentIndex - 10));
    };
    const handleFastForward = () => {
        setIsPlaying(false);
        setCurrentIndex(Math.min(history.length - 1, currentIndex + 10));
    };
    const handleSeek = (index: number) => {
        setIsPlaying(false);
        setCurrentIndex(index);
    };
    const handleJumpToLive = () => {
        setCurrentIndex(history.length - 1);
        setIsPlaying(true);
    };

    // Current snapshot
    const currentSnapshot = history[Math.min(currentIndex, history.length - 1)];
    const isLive = currentIndex >= history.length - 1;

    // Filtered logs
    const allLogs = history.slice(0, currentIndex + 1).flatMap(s => s.logs).slice(-100);
    const filteredLogs = selectedLogType === 'all'
        ? allLogs
        : allLogs.filter(l => l.type === selectedLogType);

    // ============================================================================
    // DETAIL HANDLERS
    // ============================================================================

    const openNPCDetail = (npc: NPCSnapshot) => {
        const npcInfo = NPCS[npc.id];
        setDetailPanel({
            type: 'npc',
            data: {
                ...npc, ...npcInfo, recentLogs: allLogs.filter(l =>
                    l.data.npc_id === npc.id || l.data.other_id === npc.id
                ).slice(-10)
            }
        });
    };

    const openEconomyDetail = () => {
        if (!currentSnapshot) return;
        setDetailPanel({
            type: 'economy',
            data: {
                ...currentSnapshot.economy,
                budget: currentSnapshot.budget,
                recentTx: allLogs.filter(l => l.type === 'economy_tx').slice(-20),
                gdpHistory: history.slice(Math.max(0, currentIndex - 50), currentIndex + 1).map(s => s.economy.gdp),
            }
        });
    };

    const openLogDetail = (log: LogEntry) => {
        setDetailPanel({ type: 'log', data: log });
    };

    const formatLogData = (log: LogEntry): string => {
        const d = log.data;
        switch (log.type) {
            case 'npc_action':
                return `${d.npc_name} → ${d.action} at ${d.location}`;
            case 'npc_meeting':
                return `${d.npc_name} met ${d.other_name} (Δ trust: ${d.trust_delta})`;
            case 'economy_tx':
                return `${d.tx_type}: ◊${d.amount} (${d.from} → ${d.to})`;
            case 'building_event':
                return `${d.npc_name} ${d.event} ${d.building_id}`;
            case 'world_event':
                return `${d.event_type} (${d.severity})`;
            default:
                return JSON.stringify(d).slice(0, 50);
        }
    };

    const getLogColor = (type: string): string => {
        return LOG_TYPES.find(lt => lt.id === type)?.color || 'bg-gray-500';
    };

    // ============================================================================
    // RENDER
    // ============================================================================

    if (!currentSnapshot) {
        return (
            <div className="min-h-screen bg-gray-900 text-white flex items-center justify-center">
                <div className="text-center">
                    <div className="animate-spin w-8 h-8 border-2 border-cyan-500 border-t-transparent rounded-full mx-auto mb-4" />
                    <p className="text-gray-400">Loading simulation data...</p>
                </div>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-zinc-950 text-white">
            {/* Unified Header Navigation */}
            <header className="fixed top-0 left-0 right-0 h-14 bg-zinc-900 z-50 flex items-center px-4 border-b border-cyan-500/30">
                <Link href="/" className="font-mono text-lg font-bold bg-gradient-to-r from-cyan-400 to-purple-400 bg-clip-text text-transparent">
                    AO WORLD ENGINE
                </Link>
                <nav className="ml-8 flex gap-4">
                    <Link href="/explore" className="text-sm font-medium text-gray-300 hover:text-cyan-400 px-3 py-1.5 rounded transition-colors">
                        Explore
                    </Link>
                    <Link href="/npcs" className="text-sm font-medium text-gray-300 hover:text-cyan-400 px-3 py-1.5 rounded transition-colors">
                        NPCs
                    </Link>
                    <Link href="/chat" className="text-sm font-medium text-gray-300 hover:text-cyan-400 px-3 py-1.5 rounded transition-colors">
                        Chat
                    </Link>
                    <Link href="/graph" className="text-sm font-medium text-gray-300 hover:text-cyan-400 px-3 py-1.5 rounded transition-colors">
                        Graph
                    </Link>
                    <Link href="/monitor" className="text-sm font-medium text-cyan-400 px-3 py-1.5 rounded transition-colors">
                        Monitor
                    </Link>
                </nav>

                {/* Live/Mode indicators */}
                <div className="ml-auto flex items-center gap-4">
                    <span className={`px-2 py-1 text-xs rounded ${isLive ? 'bg-red-500 animate-pulse' : 'bg-yellow-500'}`}>
                        {isLive ? '● LIVE' : `◉ T${currentSnapshot.tick}`}
                    </span>

                    <div className="flex items-center gap-4">
                        {/* Mode Toggle */}
                        <label className="flex items-center gap-2 cursor-pointer">
                            <input
                                type="checkbox"
                                checked={demoMode}
                                onChange={(e) => setDemoMode(e.target.checked)}
                                className="w-4 h-4 rounded"
                            />
                            <span className="text-sm text-white">Demo</span>
                        </label>

                        {/* Help */}
                        <button
                            onClick={() => setShowHelp(!showHelp)}
                            className="text-gray-400 hover:text-white"
                        >
                            ?
                        </button>
                    </div>
                </div>
            </header>

            {/* Help Panel */}
            {showHelp && (
                <div className="fixed top-14 left-0 right-0 bg-gray-800 border-b border-gray-700 px-6 py-4 z-40">
                    <div className="max-w-7xl mx-auto text-sm text-gray-300">
                        <h3 className="font-bold text-white mb-2">How to Use This Monitor</h3>
                        <ul className="space-y-1 list-disc list-inside">
                            <li><strong>Demo Mode</strong>: Simulates tick data locally. Turn OFF to connect to a live AO process.</li>
                            <li><strong>AO Process ID</strong>: Enter the deployed SignalNoir.1 process ID to connect to live data.</li>
                            <li><strong>Time Controls</strong>: Play/Pause the simulation, rewind to see past ticks, or scrub through history.</li>
                            <li><strong>Click any metric</strong>: Click on NPCs, economy stats, or logs to see detailed breakdowns.</li>
                            <li><strong>Speed</strong>: Adjust playback speed from 0.5x to 10x.</li>
                        </ul>
                    </div>
                </div>
            )}

            {/* Time Machine Controls */}
            <div className="fixed top-14 left-0 right-0 bg-zinc-900 border-b border-gray-700 px-6 py-3 z-40" style={{ backgroundColor: '#1a1f2e' }}>
                <div className="max-w-7xl mx-auto flex items-center gap-6">
                    {/* Playback Controls */}
                    <div className="flex items-center gap-2">
                        <button
                            onClick={handleRewind}
                            className="p-2 bg-gray-700 hover:bg-gray-600 rounded"
                            title="Rewind 10 ticks"
                        >
                            ⏪
                        </button>
                        {isPlaying ? (
                            <button
                                onClick={handlePause}
                                className="p-2 bg-cyan-600 hover:bg-cyan-700 rounded"
                                title="Pause"
                            >
                                ⏸
                            </button>
                        ) : (
                            <button
                                onClick={handlePlay}
                                className="p-2 bg-cyan-600 hover:bg-cyan-700 rounded"
                                title="Play"
                            >
                                ▶
                            </button>
                        )}
                        <button
                            onClick={handleFastForward}
                            className="p-2 bg-gray-700 hover:bg-gray-600 rounded"
                            title="Forward 10 ticks"
                        >
                            ⏩
                        </button>
                        {!isLive && (
                            <button
                                onClick={handleJumpToLive}
                                className="px-3 py-1 bg-red-600 hover:bg-red-700 rounded text-sm"
                            >
                                Jump to Live
                            </button>
                        )}
                    </div>

                    {/* Timeline Scrubber */}
                    <div className="flex-1 flex items-center gap-3">
                        <span className="text-xs text-gray-400">T{history[0]?.tick || 0}</span>
                        <input
                            type="range"
                            min={0}
                            max={history.length - 1}
                            value={Math.min(currentIndex, history.length - 1)}
                            onChange={(e) => handleSeek(parseInt(e.target.value))}
                            className="flex-1 h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer"
                        />
                        <span className="text-xs text-gray-400">T{history[history.length - 1]?.tick || 0}</span>
                    </div>

                    {/* Speed Control */}
                    <div className="flex items-center gap-2">
                        <span className="text-xs text-gray-400">Speed:</span>
                        {PLAYBACK_SPEEDS.map(s => (
                            <button
                                key={s.value}
                                onClick={() => setPlaybackSpeed(s.value)}
                                className={`px-2 py-1 text-xs rounded ${playbackSpeed === s.value ? 'bg-cyan-600' : 'bg-gray-700 hover:bg-gray-600'
                                    }`}
                            >
                                {s.label}
                            </button>
                        ))}
                    </div>

                    {/* Current Time Display */}
                    <div className="text-right">
                        <div className="text-lg font-bold text-white">
                            Day {currentSnapshot.day} • {currentSnapshot.time_period}
                        </div>
                        <div className="text-xs text-gray-400">
                            Year {currentSnapshot.year} • Tick {currentSnapshot.tick}
                        </div>
                    </div>
                </div>
            </div>

            {/* Main Content */}
            <div className="max-w-7xl mx-auto p-6">
                <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">

                    {/* Left Panel - World Status */}
                    <div className="lg:col-span-1 space-y-4">
                        {/* Status Cards */}
                        <div className="bg-gray-800 rounded-lg p-4 border border-gray-700">
                            <h3 className="text-gray-200 text-sm mb-3 font-semibold">World Status</h3>

                            <div className="space-y-3">
                                <div className="flex justify-between">
                                    <span className="text-gray-400">Population</span>
                                    <span className="text-green-400 font-bold">{currentSnapshot.population}</span>
                                </div>
                                <div className="flex justify-between">
                                    <span className="text-gray-400">Active NPCs</span>
                                    <span className="text-white">{currentSnapshot.active_npcs}</span>
                                </div>
                                <div
                                    className="flex justify-between cursor-pointer hover:bg-gray-700 -mx-2 px-2 py-1 rounded"
                                    onClick={openEconomyDetail}
                                >
                                    <span className="text-gray-400">City Budget</span>
                                    <span className="text-yellow-400 font-bold">◊{currentSnapshot.budget.toLocaleString()}</span>
                                </div>
                                <div
                                    className="flex justify-between cursor-pointer hover:bg-gray-700 -mx-2 px-2 py-1 rounded"
                                    onClick={openEconomyDetail}
                                >
                                    <span className="text-gray-400">Crisis Level</span>
                                    <span className={
                                        currentSnapshot.economy.crisis_level === 'healthy' ? 'text-green-400' :
                                            currentSnapshot.economy.crisis_level === 'strained' ? 'text-yellow-400' :
                                                'text-red-400'
                                    }>
                                        {currentSnapshot.economy.crisis_level.toUpperCase()}
                                    </span>
                                </div>
                            </div>
                        </div>

                        {/* Economy Indicators - Clickable */}
                        <div
                            className="bg-gray-800 rounded-lg p-4 border border-gray-700 cursor-pointer hover:border-cyan-500 transition-colors"
                            onClick={openEconomyDetail}
                        >
                            <h3 className="text-gray-200 text-sm mb-3 font-semibold flex justify-between">
                                Economy
                                <span className="text-cyan-400 text-xs">Click for details →</span>
                            </h3>

                            <div className="grid grid-cols-2 gap-3 text-sm">
                                <div>
                                    <span className="text-gray-400 text-xs">GDP</span>
                                    <p className="text-white font-medium">◊{(currentSnapshot.economy.gdp / 1000).toFixed(0)}k</p>
                                </div>
                                <div>
                                    <span className="text-gray-400 text-xs">Inflation</span>
                                    <p className="text-white font-medium">{(currentSnapshot.economy.inflation * 100).toFixed(1)}%</p>
                                </div>
                                <div>
                                    <span className="text-gray-400 text-xs">Unemployment</span>
                                    <p className="text-orange-400 font-medium">{(currentSnapshot.economy.unemployment_rate * 100).toFixed(1)}%</p>
                                </div>
                                <div>
                                    <span className="text-gray-400 text-xs">Black Market</span>
                                    <p className="text-red-400 font-medium">{(currentSnapshot.economy.black_market_share * 100).toFixed(0)}%</p>
                                </div>
                            </div>
                        </div>

                        {/* Active NPCs - Clickable */}
                        <div className="bg-gray-800 rounded-lg p-4 border border-gray-700">
                            <h3 className="text-gray-200 text-sm mb-3 font-semibold">NPCs</h3>

                            <div className="space-y-2 max-h-64 overflow-y-auto">
                                {currentSnapshot.npcs.map(npc => (
                                    <div
                                        key={npc.id}
                                        className="flex items-center gap-2 px-2 py-1.5 bg-gray-700/50 rounded cursor-pointer hover:bg-gray-700"
                                        onClick={() => openNPCDetail(npc)}
                                    >
                                        <div className={`w-2 h-2 rounded-full ${npc.state === 'working' ? 'bg-green-500' :
                                            npc.state === 'moving' ? 'bg-blue-500' :
                                                npc.state === 'resting' ? 'bg-yellow-500' :
                                                    'bg-gray-500'
                                            }`} />
                                        <span className="text-white text-sm flex-1">{npc.name}</span>
                                        <span className="text-gray-400 text-xs">{npc.state}</span>
                                    </div>
                                ))}
                            </div>
                        </div>
                    </div>

                    {/* Middle Panel - Event Stream */}
                    <div className="lg:col-span-2">
                        <div className="bg-gray-800 rounded-lg border border-gray-700 h-full flex flex-col">
                            {/* Log Type Filter */}
                            <div className="p-4 border-b border-gray-700 flex flex-wrap gap-2">
                                {LOG_TYPES.map(lt => (
                                    <button
                                        key={lt.id}
                                        onClick={() => setSelectedLogType(lt.id)}
                                        className={`flex items-center gap-1.5 px-3 py-1 rounded text-sm ${selectedLogType === lt.id
                                            ? 'bg-gray-600 text-white'
                                            : 'bg-gray-700/50 text-gray-300 hover:bg-gray-700'
                                            }`}
                                    >
                                        <span className={`w-2 h-2 rounded-full ${lt.color}`} />
                                        {lt.label}
                                    </button>
                                ))}
                            </div>

                            {/* Event List */}
                            <div className="flex-1 overflow-y-auto p-4 space-y-2">
                                {filteredLogs.length === 0 ? (
                                    <p className="text-gray-500 text-center py-8">No events in this category</p>
                                ) : (
                                    filteredLogs.slice().reverse().map((log, idx) => (
                                        <div
                                            key={`${log.tick}-${idx}`}
                                            className="flex items-start gap-3 px-3 py-2 bg-gray-700/30 rounded cursor-pointer hover:bg-gray-700/60"
                                            onClick={() => openLogDetail(log)}
                                        >
                                            <span className={`w-2 h-2 rounded-full mt-1.5 ${getLogColor(log.type)}`} />
                                            <div className="flex-1">
                                                <p className="text-white text-sm">{formatLogData(log)}</p>
                                                <p className="text-gray-500 text-xs">T{log.tick}</p>
                                            </div>
                                        </div>
                                    ))
                                )}
                            </div>
                        </div>
                    </div>

                    {/* Right Panel - Detail View */}
                    <div className="lg:col-span-1">
                        {detailPanel.type ? (
                            <div className="bg-gray-800 rounded-lg border border-cyan-500 p-4 shadow-lg shadow-cyan-500/10">
                                <div className="flex justify-between items-start mb-4">
                                    <h3 className="font-bold text-cyan-400">
                                        {detailPanel.type === 'npc' && 'NPC Details'}
                                        {detailPanel.type === 'economy' && 'Economy Details'}
                                        {detailPanel.type === 'log' && 'Event Details'}
                                    </h3>
                                    <button
                                        onClick={() => setDetailPanel({ type: null, data: null })}
                                        className="text-gray-400 hover:text-white"
                                    >
                                        ✕
                                    </button>
                                </div>

                                {/* NPC Detail */}
                                {detailPanel.type === 'npc' && detailPanel.data && (
                                    <div className="space-y-4">
                                        {(() => {
                                            const npc = detailPanel.data as NPCSnapshot & { role?: string; district?: string; recentLogs?: LogEntry[] };
                                            const npcId = npc.id?.toUpperCase() || '';
                                            const npcFullData = NPC_DATA[npcId];
                                            return (
                                                <>
                                                    <div>
                                                        <h4 className="text-xl font-bold text-white">{npc.name}</h4>
                                                        <p className="text-gray-400 capitalize">{npcFullData?.occupation?.title || npc.role?.replace(/_/g, ' ')}</p>
                                                    </div>

                                                    {/* Biography */}
                                                    {npcFullData?.bio && (
                                                        <div className="bg-gray-700/30 p-3 rounded text-sm text-gray-300 italic border-l-2 border-cyan-500/50">
                                                            {npcFullData.bio}
                                                        </div>
                                                    )}

                                                    {/* Occupation & Income */}
                                                    {npcFullData?.occupation && (
                                                        <div className="grid grid-cols-2 gap-2 text-sm">
                                                            <div>
                                                                <span className="text-gray-400">Workplace</span>
                                                                <p className="text-white font-mono text-xs">{npcFullData.occupation.workplace}</p>
                                                            </div>
                                                            <div>
                                                                <span className="text-gray-400">Income</span>
                                                                <p className="text-green-400 font-bold">◊{npcFullData.occupation.income}/day</p>
                                                            </div>
                                                        </div>
                                                    )}

                                                    <div className="grid grid-cols-2 gap-3 text-sm">
                                                        <div>
                                                            <span className="text-gray-400">Location</span>
                                                            <p className="text-white font-mono">{npc.location}</p>
                                                        </div>
                                                        <div>
                                                            <span className="text-gray-400">State</span>
                                                            <p className="text-white capitalize">{npc.state}</p>
                                                        </div>
                                                        <div>
                                                            <span className="text-gray-400">Mood</span>
                                                            <div className="flex items-center gap-2">
                                                                <div className="flex-1 h-2 bg-gray-700 rounded-full">
                                                                    <div className="h-full bg-cyan-500 rounded-full" style={{ width: `${npc.mood * 100}%` }} />
                                                                </div>
                                                                <span className="text-white text-xs">{Math.round(npc.mood * 100)}%</span>
                                                            </div>
                                                        </div>
                                                        <div>
                                                            <span className="text-gray-400">Energy</span>
                                                            <div className="flex items-center gap-2">
                                                                <div className="flex-1 h-2 bg-gray-700 rounded-full">
                                                                    <div className="h-full bg-green-500 rounded-full" style={{ width: `${npc.energy * 100}%` }} />
                                                                </div>
                                                                <span className="text-white text-xs">{Math.round(npc.energy * 100)}%</span>
                                                            </div>
                                                        </div>
                                                        <div>
                                                            <span className="text-gray-400">Wealth</span>
                                                            <p className="text-yellow-400 font-bold">◊{npc.wealth}</p>
                                                        </div>
                                                        <div>
                                                            <span className="text-gray-400">District</span>
                                                            <p className="text-white capitalize">{npc.district?.replace(/_/g, ' ')}</p>
                                                        </div>
                                                    </div>

                                                    {/* Relationships / Social Graph */}
                                                    {npcFullData?.relationships && npcFullData.relationships.length > 0 && (
                                                        <div>
                                                            <h5 className="text-gray-400 text-sm mb-2 flex items-center gap-2">
                                                                🔗 Social Connections
                                                            </h5>
                                                            <div className="space-y-1">
                                                                {npcFullData.relationships.map((rel, i) => {
                                                                    const relNpc = NPC_DATA[rel.id];
                                                                    const trustColor = rel.trust >= 0.7 ? 'text-green-400' :
                                                                        rel.trust >= 0.4 ? 'text-yellow-400' : 'text-red-400';
                                                                    return (
                                                                        <div key={i} className="flex items-center justify-between text-xs bg-gray-700/30 px-2 py-1.5 rounded">
                                                                            <span className="text-white">{relNpc?.name || rel.id}</span>
                                                                            <div className="flex items-center gap-2">
                                                                                <span className="text-gray-400 capitalize">{rel.type.replace(/_/g, ' ')}</span>
                                                                                <span className={trustColor}>{Math.round(rel.trust * 100)}%</span>
                                                                            </div>
                                                                        </div>
                                                                    );
                                                                })}
                                                            </div>
                                                        </div>
                                                    )}

                                                    {/* Partnerships */}
                                                    {npcFullData?.partnerships && npcFullData.partnerships.length > 0 && (
                                                        <div>
                                                            <h5 className="text-gray-400 text-sm mb-2">🤝 Partners</h5>
                                                            <div className="flex flex-wrap gap-2">
                                                                {npcFullData.partnerships.map((partnerId, i) => {
                                                                    const partner = NPC_DATA[partnerId];
                                                                    return (
                                                                        <span key={i} className="px-2 py-1 bg-purple-500/20 text-purple-300 rounded text-xs">
                                                                            {partner?.name || partnerId}
                                                                        </span>
                                                                    );
                                                                })}
                                                            </div>
                                                        </div>
                                                    )}

                                                    {/* Backstory */}
                                                    {npcFullData?.backstory && (
                                                        <div>
                                                            <h5 className="text-gray-400 text-sm mb-2">📜 Backstory</h5>
                                                            <p className="text-xs text-gray-300">{npcFullData.backstory}</p>
                                                        </div>
                                                    )}

                                                    <div>
                                                        <h5 className="text-gray-400 text-sm mb-2">Recent Activity</h5>
                                                        <div className="space-y-1 max-h-40 overflow-y-auto">
                                                            {(npc.recentLogs || []).slice(-5).map((log, i) => (
                                                                <div key={i} className="text-xs text-gray-300 bg-gray-700/50 px-2 py-1 rounded">
                                                                    T{log.tick}: {formatLogData(log)}
                                                                </div>
                                                            ))}
                                                        </div>
                                                    </div>

                                                    <div className="flex gap-2">
                                                        <Link
                                                            href="/npcs"
                                                            className="flex-1 text-center text-cyan-400 hover:text-cyan-300 text-sm py-2 bg-cyan-500/10 rounded"
                                                        >
                                                            View All NPCs →
                                                        </Link>
                                                        <Link
                                                            href="/graph"
                                                            className="flex-1 text-center text-purple-400 hover:text-purple-300 text-sm py-2 bg-purple-500/10 rounded"
                                                        >
                                                            View Graph →
                                                        </Link>
                                                    </div>
                                                </>
                                            );
                                        })()}
                                    </div>
                                )}

                                {/* Economy Detail */}
                                {detailPanel.type === 'economy' && detailPanel.data && (
                                    <div className="space-y-4">
                                        {(() => {
                                            const eco = detailPanel.data as EconomySnapshot & { budget: number; recentTx?: LogEntry[]; gdpHistory?: number[] };
                                            return (
                                                <>
                                                    <div className="grid grid-cols-2 gap-3 text-sm">
                                                        <div>
                                                            <span className="text-gray-400">GDP</span>
                                                            <p className="text-white font-bold">◊{eco.gdp.toLocaleString()}</p>
                                                        </div>
                                                        <div>
                                                            <span className="text-gray-400">Budget</span>
                                                            <p className="text-yellow-400 font-bold">◊{eco.budget.toLocaleString()}</p>
                                                        </div>
                                                        <div>
                                                            <span className="text-gray-400">Inflation</span>
                                                            <p className="text-white">{(eco.inflation * 100).toFixed(2)}%</p>
                                                        </div>
                                                        <div>
                                                            <span className="text-gray-400">Unemployment</span>
                                                            <p className="text-orange-400">{(eco.unemployment_rate * 100).toFixed(1)}%</p>
                                                        </div>
                                                        <div>
                                                            <span className="text-gray-400">Gini</span>
                                                            <p className="text-white">{eco.gini_coefficient.toFixed(3)}</p>
                                                        </div>
                                                        <div>
                                                            <span className="text-gray-400">Black Market</span>
                                                            <p className="text-red-400">{(eco.black_market_share * 100).toFixed(0)}%</p>
                                                        </div>
                                                    </div>

                                                    <div>
                                                        <h5 className="text-gray-400 text-sm mb-2">Service Levels</h5>
                                                        <div className="space-y-2">
                                                            {Object.entries(eco.service_levels).map(([service, level]) => (
                                                                <div key={service} className="flex items-center gap-2">
                                                                    <span className="text-gray-400 text-xs capitalize flex-1">{service.replace(/_/g, ' ')}</span>
                                                                    <div className="w-24 h-2 bg-gray-700 rounded-full">
                                                                        <div
                                                                            className={`h-full rounded-full ${level > 0.8 ? 'bg-green-500' : level > 0.5 ? 'bg-yellow-500' : 'bg-red-500'}`}
                                                                            style={{ width: `${level * 100}%` }}
                                                                        />
                                                                    </div>
                                                                    <span className="text-white text-xs w-10">{Math.round(level * 100)}%</span>
                                                                </div>
                                                            ))}
                                                        </div>
                                                    </div>

                                                    <div>
                                                        <h5 className="text-gray-400 text-sm mb-2">Recent Transactions</h5>
                                                        <div className="space-y-1 max-h-32 overflow-y-auto">
                                                            {(eco.recentTx || []).slice(-5).map((tx, i) => (
                                                                <div key={i} className="text-xs text-gray-300 bg-gray-700/50 px-2 py-1 rounded">
                                                                    {formatLogData(tx)}
                                                                </div>
                                                            ))}
                                                        </div>
                                                    </div>
                                                </>
                                            );
                                        })()}
                                    </div>
                                )}

                                {/* Log Detail */}
                                {detailPanel.type === 'log' && detailPanel.data && (
                                    <div className="space-y-4">
                                        {(() => {
                                            const log = detailPanel.data as LogEntry;
                                            return (
                                                <>
                                                    <div>
                                                        <span className={`inline-flex items-center gap-1 px-2 py-1 rounded text-xs ${getLogColor(log.type)}`}>
                                                            {LOG_TYPES.find(lt => lt.id === log.type)?.label}
                                                        </span>
                                                        <p className="text-gray-400 text-sm mt-2">Tick {log.tick}</p>
                                                    </div>

                                                    <div>
                                                        <h5 className="text-gray-400 text-sm mb-2">Event Data</h5>
                                                        <pre className="text-xs text-gray-300 bg-gray-700/50 p-3 rounded overflow-x-auto">
                                                            {JSON.stringify(log.data, null, 2)}
                                                        </pre>
                                                    </div>
                                                </>
                                            );
                                        })()}
                                    </div>
                                )}
                            </div>
                        ) : (
                            <div className="bg-gray-800 rounded-lg border border-gray-700 p-4 text-center">
                                <p className="text-gray-500">Click on any NPC, metric, or event to see details</p>
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
}
