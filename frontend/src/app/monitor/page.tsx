'use client';

import { useState, useEffect, useCallback } from 'react';

interface LogEntry {
    tick: number;
    type: string;
    timestamp: number;
    data: Record<string, unknown>;
}

interface LogStats {
    total_logs: number;
    logs_by_type: Record<string, number>;
    first_tick: number;
    last_tick: number;
    buffer_sizes: Record<string, number>;
}

interface WorldStatus {
    world_name: string;
    version: string;
    tick: number;
    day: number;
    year: number;
    population: number;
    active_npcs: number;
    budget: number;
    districts: number;
    uptime_ticks: number;
}

interface EconomyStatus {
    budget: number;
    crisis_level: string;
    indicators: {
        gdp: number;
        inflation: number;
        unemployment_rate: number;
        gini_coefficient: number;
        black_market_share: number;
    };
    service_levels: Record<string, number>;
}

const LOG_TYPES = [
    { id: 'npc_action', label: 'NPC Actions', color: 'bg-blue-500' },
    { id: 'npc_meeting', label: 'Meetings', color: 'bg-green-500' },
    { id: 'economy_tx', label: 'Economy', color: 'bg-yellow-500' },
    { id: 'building_event', label: 'Buildings', color: 'bg-purple-500' },
    { id: 'world_event', label: 'World Events', color: 'bg-red-500' },
    { id: 'system_tick', label: 'System Ticks', color: 'bg-gray-500' },
];

export default function MonitorPage() {
    const [processId, setProcessId] = useState<string>('');
    const [connected, setConnected] = useState(false);
    const [status, setStatus] = useState<WorldStatus | null>(null);
    const [economy, setEconomy] = useState<EconomyStatus | null>(null);
    const [logs, setLogs] = useState<LogEntry[]>([]);
    const [logStats, setLogStats] = useState<LogStats | null>(null);
    const [selectedLogType, setSelectedLogType] = useState('npc_action');
    const [autoRefresh, setAutoRefresh] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [isLoading, setIsLoading] = useState(false);

    // Mock data for demo mode
    const [demoMode, setDemoMode] = useState(true);

    const generateMockData = useCallback(() => {
        const mockStatus: WorldStatus = {
            world_name: 'SignalNoir.1',
            version: '0.1.0-alpha',
            tick: Math.floor(Date.now() / 1000) % 100000,
            day: Math.floor((Date.now() / 1000) % 100000 / 240) + 1,
            year: 2087,
            population: 12,
            active_npcs: Math.floor(Math.random() * 4) + 8,
            budget: 100000 - Math.floor(Math.random() * 5000),
            districts: 3,
            uptime_ticks: Math.floor((Date.now() / 1000) % 100000),
        };

        const mockEconomy: EconomyStatus = {
            budget: mockStatus.budget,
            crisis_level: mockStatus.budget > 80000 ? 'healthy' : mockStatus.budget > 50000 ? 'strained' : 'crisis',
            indicators: {
                gdp: 900000 + Math.floor(Math.random() * 100000),
                inflation: 0.02 + Math.random() * 0.01,
                unemployment_rate: 0.12 + Math.random() * 0.05,
                gini_coefficient: 0.72 + Math.random() * 0.05,
                black_market_share: 0.20 + Math.random() * 0.1,
            },
            service_levels: {
                law_enforcement: 0.85 + Math.random() * 0.15,
                infrastructure: 0.90 + Math.random() * 0.10,
                healthcare: 0.80 + Math.random() * 0.20,
                sanitation: 0.75 + Math.random() * 0.25,
                education: 0.70 + Math.random() * 0.30,
            },
        };

        const npcs = ['C01', 'C02', 'C03', 'C04', 'C05', 'C06', 'C07', 'C08', 'C09', 'C10', 'C11', 'C12'];
        const npcNames: Record<string, string> = {
            C01: 'Charlie', C02: 'Kai Vance', C03: 'Orion Thane', C04: 'Felix',
            C05: 'Nova Chen', C06: 'Selene Voss', C07: 'Sister Mira', C08: 'Mama Indira',
            C09: 'Aiche', C10: 'Pixel', C11: 'Cipher', C12: 'Zero Chen',
        };
        const locations = ['L001', 'L003', 'L004', 'L026', 'L031', 'L050'];
        const actions = ['move', 'talk', 'work', 'rest', 'observe', 'trade'];

        const mockLogs: LogEntry[] = [];
        for (let i = 0; i < 20; i++) {
            const npc = npcs[Math.floor(Math.random() * npcs.length)];
            const logTypes = ['npc_action', 'npc_meeting', 'economy_tx', 'building_event', 'world_event', 'system_tick'];
            const logType = selectedLogType || logTypes[Math.floor(Math.random() * logTypes.length)];

            let data: Record<string, unknown> = {};

            switch (logType) {
                case 'npc_action':
                    data = {
                        npc_id: npc,
                        npc_name: npcNames[npc],
                        action: actions[Math.floor(Math.random() * actions.length)],
                        location: locations[Math.floor(Math.random() * locations.length)],
                    };
                    break;
                case 'npc_meeting':
                    const npc2 = npcs.filter(n => n !== npc)[Math.floor(Math.random() * (npcs.length - 1))];
                    data = {
                        participants: [npc, npc2],
                        participant_names: [npcNames[npc], npcNames[npc2]],
                        location: locations[Math.floor(Math.random() * locations.length)],
                        trust_delta: (Math.random() * 0.1 - 0.02).toFixed(3),
                    };
                    break;
                case 'economy_tx':
                    data = {
                        tx_type: ['tax', 'trade', 'salary', 'ubi'][Math.floor(Math.random() * 4)],
                        amount: Math.floor(Math.random() * 500) + 10,
                        from: npc,
                        to: 'city_treasury',
                    };
                    break;
                case 'building_event':
                    data = {
                        building_id: locations[Math.floor(Math.random() * locations.length)],
                        npc_id: npc,
                        event: Math.random() > 0.5 ? 'entry' : 'exit',
                    };
                    break;
                case 'world_event':
                    data = {
                        event_type: ['weather_change', 'market_peak', 'power_fluctuation'][Math.floor(Math.random() * 3)],
                        scope: 'city',
                    };
                    break;
                case 'system_tick':
                    data = {
                        day: mockStatus.day,
                        year: mockStatus.year,
                        time_period: ['T01', 'T02', 'T03', 'T04', 'T05'][Math.floor(Math.random() * 5)],
                        population: mockStatus.population,
                        budget: mockStatus.budget,
                    };
                    break;
            }

            mockLogs.push({
                tick: mockStatus.tick - i * 10,
                type: logType,
                timestamp: mockStatus.tick - i * 10,
                data,
            });
        }

        const mockStats: LogStats = {
            total_logs: 1234 + Math.floor(Math.random() * 100),
            logs_by_type: {
                npc_action: 456,
                npc_meeting: 123,
                economy_tx: 234,
                building_event: 187,
                world_event: 45,
                system_tick: 189,
            },
            first_tick: 0,
            last_tick: mockStatus.tick,
            buffer_sizes: {
                npc_action: 500,
                npc_meeting: 200,
                economy_tx: 300,
                building_event: 200,
                world_event: 100,
                system_tick: 1000,
            },
        };

        setStatus(mockStatus);
        setEconomy(mockEconomy);
        setLogs(mockLogs);
        setLogStats(mockStats);
        setConnected(true);
    }, [selectedLogType]);

    // Auto-refresh effect
    useEffect(() => {
        if (autoRefresh && demoMode) {
            const interval = setInterval(generateMockData, 5000);
            return () => clearInterval(interval);
        }
    }, [autoRefresh, demoMode, generateMockData]);

    // Initial load for demo mode
    useEffect(() => {
        if (demoMode) {
            generateMockData();
        }
    }, [demoMode, generateMockData]);

    const handleConnect = async () => {
        if (demoMode) {
            generateMockData();
            return;
        }

        if (!processId) {
            setError('Please enter a Process ID');
            return;
        }

        setIsLoading(true);
        setError(null);

        try {
            // TODO: Implement actual AO connection via aoconnect
            // For now, this is a placeholder
            setError('Live connection not yet implemented. Use Demo Mode.');
        } catch (err) {
            setError(`Connection failed: ${err}`);
        } finally {
            setIsLoading(false);
        }
    };

    const formatLogData = (log: LogEntry): string => {
        const d = log.data;
        switch (log.type) {
            case 'npc_action':
                return `${d.npc_name || d.npc_id} → ${d.action} at ${d.location}`;
            case 'npc_meeting':
                const names = d.participant_names as string[] || d.participants as string[];
                return `${names?.[0]} met ${names?.[1]} (trust: ${d.trust_delta})`;
            case 'economy_tx':
                return `${d.tx_type}: ${d.amount} GEP (${d.from} → ${d.to})`;
            case 'building_event':
                return `${d.npc_id} ${d.event} ${d.building_id}`;
            case 'world_event':
                return `${d.event_type} (${d.scope})`;
            case 'system_tick':
                return `Day ${d.day} | Budget: ${d.budget} GEP`;
            default:
                return JSON.stringify(d).slice(0, 60);
        }
    };

    const getLogColor = (type: string): string => {
        return LOG_TYPES.find(lt => lt.id === type)?.color || 'bg-gray-500';
    };

    return (
        <div className="min-h-screen bg-gray-900 text-white p-6">
            {/* Header */}
            <div className="max-w-7xl mx-auto">
                <div className="flex items-center justify-between mb-8">
                    <div>
                        <h1 className="text-3xl font-bold bg-gradient-to-r from-cyan-400 to-purple-500 bg-clip-text text-transparent">
                            SignalNoir.1 Monitor
                        </h1>
                        <p className="text-gray-400 mt-1">Real-time simulation monitoring</p>
                    </div>

                    <div className="flex items-center gap-4">
                        <label className="flex items-center gap-2 cursor-pointer">
                            <input
                                type="checkbox"
                                checked={demoMode}
                                onChange={(e) => setDemoMode(e.target.checked)}
                                className="w-4 h-4 rounded"
                            />
                            <span className="text-sm text-gray-400">Demo Mode</span>
                        </label>

                        <label className="flex items-center gap-2 cursor-pointer">
                            <input
                                type="checkbox"
                                checked={autoRefresh}
                                onChange={(e) => setAutoRefresh(e.target.checked)}
                                className="w-4 h-4 rounded"
                            />
                            <span className="text-sm text-gray-400">Auto-refresh</span>
                        </label>
                    </div>
                </div>

                {/* Connection Panel */}
                {!demoMode && (
                    <div className="bg-gray-800 rounded-lg p-4 mb-6">
                        <div className="flex items-center gap-4">
                            <input
                                type="text"
                                value={processId}
                                onChange={(e) => setProcessId(e.target.value)}
                                placeholder="AO Process ID"
                                className="flex-1 bg-gray-700 border border-gray-600 rounded px-4 py-2 text-white focus:border-cyan-500 focus:outline-none"
                            />
                            <button
                                onClick={handleConnect}
                                disabled={isLoading}
                                className="px-6 py-2 bg-cyan-600 hover:bg-cyan-700 rounded font-medium disabled:opacity-50"
                            >
                                {isLoading ? 'Connecting...' : 'Connect'}
                            </button>
                        </div>
                        {error && (
                            <p className="text-red-400 text-sm mt-2">{error}</p>
                        )}
                    </div>
                )}

                {/* Status Cards */}
                {connected && status && (
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
                        <div className="bg-gray-800 rounded-lg p-4 border border-gray-700">
                            <h3 className="text-gray-400 text-sm mb-1">World Tick</h3>
                            <p className="text-2xl font-bold text-cyan-400">{status.tick.toLocaleString()}</p>
                            <p className="text-xs text-gray-500">Day {status.day}, Year {status.year}</p>
                        </div>

                        <div className="bg-gray-800 rounded-lg p-4 border border-gray-700">
                            <h3 className="text-gray-400 text-sm mb-1">Population</h3>
                            <p className="text-2xl font-bold text-green-400">{status.population}</p>
                            <p className="text-xs text-gray-500">{status.active_npcs} active NPCs</p>
                        </div>

                        <div className="bg-gray-800 rounded-lg p-4 border border-gray-700">
                            <h3 className="text-gray-400 text-sm mb-1">City Budget</h3>
                            <p className="text-2xl font-bold text-yellow-400">◊{status.budget.toLocaleString()}</p>
                            <p className="text-xs text-gray-500">
                                {economy?.crisis_level === 'healthy' && '✅ Healthy'}
                                {economy?.crisis_level === 'strained' && '⚠️ Strained'}
                                {economy?.crisis_level === 'crisis' && '🔴 Crisis'}
                            </p>
                        </div>

                        <div className="bg-gray-800 rounded-lg p-4 border border-gray-700">
                            <h3 className="text-gray-400 text-sm mb-1">Districts</h3>
                            <p className="text-2xl font-bold text-purple-400">{status.districts}</p>
                            <p className="text-xs text-gray-500">{status.world_name}</p>
                        </div>
                    </div>
                )}

                {/* Economy Indicators */}
                {connected && economy && (
                    <div className="bg-gray-800 rounded-lg p-4 mb-6 border border-gray-700">
                        <h3 className="text-lg font-semibold mb-4">Economic Indicators</h3>
                        <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
                            <div>
                                <p className="text-gray-400 text-xs">GDP</p>
                                <p className="text-lg font-medium">◊{economy.indicators.gdp.toLocaleString()}</p>
                            </div>
                            <div>
                                <p className="text-gray-400 text-xs">Inflation</p>
                                <p className="text-lg font-medium">{(economy.indicators.inflation * 100).toFixed(1)}%</p>
                            </div>
                            <div>
                                <p className="text-gray-400 text-xs">Unemployment</p>
                                <p className="text-lg font-medium text-orange-400">
                                    {(economy.indicators.unemployment_rate * 100).toFixed(1)}%
                                </p>
                            </div>
                            <div>
                                <p className="text-gray-400 text-xs">Gini Coefficient</p>
                                <p className="text-lg font-medium">{economy.indicators.gini_coefficient.toFixed(2)}</p>
                            </div>
                            <div>
                                <p className="text-gray-400 text-xs">Black Market</p>
                                <p className="text-lg font-medium text-red-400">
                                    {(economy.indicators.black_market_share * 100).toFixed(0)}%
                                </p>
                            </div>
                        </div>
                    </div>
                )}

                {/* Main Content */}
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                    {/* Log Type Selector */}
                    <div className="lg:col-span-1">
                        <div className="bg-gray-800 rounded-lg p-4 border border-gray-700">
                            <h3 className="text-lg font-semibold mb-4">Log Categories</h3>
                            <div className="space-y-2">
                                {LOG_TYPES.map((lt) => (
                                    <button
                                        key={lt.id}
                                        onClick={() => {
                                            setSelectedLogType(lt.id);
                                            if (demoMode) generateMockData();
                                        }}
                                        className={`w-full flex items-center justify-between px-4 py-2 rounded ${selectedLogType === lt.id
                                                ? 'bg-gray-700 border border-cyan-500'
                                                : 'bg-gray-700/50 hover:bg-gray-700'
                                            }`}
                                    >
                                        <span className="flex items-center gap-2">
                                            <span className={`w-3 h-3 rounded-full ${lt.color}`}></span>
                                            {lt.label}
                                        </span>
                                        <span className="text-gray-500 text-sm">
                                            {logStats?.logs_by_type[lt.id] || 0}
                                        </span>
                                    </button>
                                ))}
                            </div>

                            {logStats && (
                                <div className="mt-6 pt-4 border-t border-gray-700">
                                    <p className="text-sm text-gray-400">
                                        Total Logs: <span className="text-white font-medium">{logStats.total_logs.toLocaleString()}</span>
                                    </p>
                                    <p className="text-sm text-gray-400 mt-1">
                                        Tick Range: {logStats.first_tick} - {logStats.last_tick}
                                    </p>
                                </div>
                            )}
                        </div>
                    </div>

                    {/* Log Stream */}
                    <div className="lg:col-span-2">
                        <div className="bg-gray-800 rounded-lg p-4 border border-gray-700">
                            <div className="flex items-center justify-between mb-4">
                                <h3 className="text-lg font-semibold">
                                    {LOG_TYPES.find(lt => lt.id === selectedLogType)?.label || 'Logs'}
                                </h3>
                                <button
                                    onClick={() => demoMode ? generateMockData() : handleConnect()}
                                    className="text-sm text-cyan-400 hover:text-cyan-300"
                                >
                                    Refresh
                                </button>
                            </div>

                            <div className="space-y-2 max-h-[600px] overflow-y-auto">
                                {logs.length === 0 ? (
                                    <p className="text-gray-500 text-center py-8">No logs yet</p>
                                ) : (
                                    logs.map((log, idx) => (
                                        <div
                                            key={idx}
                                            className="flex items-start gap-3 px-3 py-2 bg-gray-700/50 rounded hover:bg-gray-700"
                                        >
                                            <span className={`w-2 h-2 rounded-full mt-2 ${getLogColor(log.type)}`}></span>
                                            <div className="flex-1 min-w-0">
                                                <div className="flex items-center justify-between">
                                                    <p className="text-sm text-white truncate">
                                                        {formatLogData(log)}
                                                    </p>
                                                    <span className="text-xs text-gray-500 ml-2 shrink-0">
                                                        T{log.tick}
                                                    </span>
                                                </div>
                                            </div>
                                        </div>
                                    ))
                                )}
                            </div>
                        </div>
                    </div>
                </div>

                {/* Footer */}
                <div className="mt-8 text-center text-gray-500 text-sm">
                    <p>SignalNoir.1 - AO World Engine Monitor</p>
                    <p className="mt-1">
                        {demoMode ? '🔶 Demo Mode - Simulated Data' : connected ? '🟢 Connected' : '⚪ Disconnected'}
                    </p>
                </div>
            </div>
        </div>
    );
}
