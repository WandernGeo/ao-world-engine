'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';

interface NPC {
    id: string;
    name: string;
    archetype: string;
    location?: string;
}

interface Message {
    role: 'user' | 'npc';
    content: string;
    timestamp: number;
}

const CLOUD_API = 'https://ao-world-engine-1071951656531.us-central1.run.app';
const LOCAL_API = 'http://localhost:8080';

// Try localhost first, fall back to Cloud
async function getApiBase(): Promise<string> {
    try {
        const res = await fetch(`${LOCAL_API}/health`, { method: 'GET', signal: AbortSignal.timeout(1000) });
        if (res.ok) return LOCAL_API;
    } catch { /* ignore */ }
    return CLOUD_API;
}

// Founding NPC IDs from codec - these are the 12 special characters
const FOUNDING_NPC_IDS = [
    'charlie', 'kai_vance', 'orion_thane', 'felix', 'nova_chen',
    'selene_voss', 'sister_mira', 'mama_indira', 'aiche', 'pixel',
    'cipher', 'zero_chen'
];

// Fallback founding NPCs (used if API fails)
const FALLBACK_NPCS: NPC[] = [
    { id: 'charlie', name: 'Charlie', archetype: 'Resistance Fighter' },
    { id: 'felix', name: 'Felix', archetype: 'Bartender / Info Broker' },
    { id: 'zero_chen', name: 'Zero Chen', archetype: 'Resistance Leader' },
    { id: 'pixel', name: 'Pixel', archetype: 'Tech Genius' },
    { id: 'kai_vance', name: 'Kai Vance', archetype: 'Tactician' },
    { id: 'nova_chen', name: 'Nova Chen', archetype: 'Operative' },
    { id: 'orion_thane', name: 'Orion Thane', archetype: 'Mystic' },
    { id: 'aiche', name: 'Aiche', archetype: 'AI Interface' },
    { id: 'sister_mira', name: 'Sister Mira', archetype: 'Temple Priestess' },
    { id: 'mama_indira', name: 'Mama Indira', archetype: 'Underground Matriarch' },
    { id: 'cipher', name: 'Cipher', archetype: 'Unknown Entity' },
    { id: 'selene_voss', name: 'Selene Voss', archetype: 'Ghost-Child' },
];

export default function ChatPage() {
    const [selectedNPC, setSelectedNPC] = useState<NPC | null>(null);
    const [message, setMessage] = useState('');
    const [messages, setMessages] = useState<Message[]>([]);
    const [isLoading, setIsLoading] = useState(false);
    const [currentTick, setCurrentTick] = useState(100);
    const [npcs, setNpcs] = useState<NPC[]>(FALLBACK_NPCS);
    const [apiBase, setApiBase] = useState(CLOUD_API);
    const [apiStatus, setApiStatus] = useState<'checking' | 'local' | 'cloud' | 'offline'>('checking');

    // Find best API endpoint and load NPCs on mount
    useEffect(() => {
        const initChat = async () => {
            const base = await getApiBase();
            setApiBase(base);
            setApiStatus(base === LOCAL_API ? 'local' : 'cloud');

            // Try to fetch founding NPCs from API
            try {
                const response = await fetch(`${base}/api/npcs?limit=50`);
                if (response.ok) {
                    const data = await response.json();
                    const apiNPCs = data.npcs || data;
                    if (Array.isArray(apiNPCs)) {
                        // Filter to founding NPCs or first 12
                        const founding = apiNPCs
                            .filter((n: { id: string }) => FOUNDING_NPC_IDS.includes(n.id) || n.id.startsWith('npc_000'))
                            .slice(0, 12)
                            .map((n: Record<string, unknown>) => ({
                                id: n.id as string,
                                name: n.name as string,
                                archetype: n.archetype as string || 'Citizen',
                            }));
                        if (founding.length > 0) {
                            setNpcs(founding);
                            console.log(`Loaded ${founding.length} NPCs for chat from API`);
                        }
                    }
                }
            } catch (error) {
                console.log('Failed to fetch NPCs for chat:', error);
                // Keep using fallback NPCs
            }
        };
        initChat();
    }, []);

    const sendMessage = async () => {
        if (!message.trim() || !selectedNPC) return;

        const userMsg: Message = { role: 'user', content: message, timestamp: Date.now() };
        setMessages(prev => [...prev, userMsg]);
        setMessage('');
        setIsLoading(true);

        try {
            const res = await fetch(`${apiBase}/api/npc/chat`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    npc_id: selectedNPC.id,
                    message: message,
                    tick: currentTick,
                    user_id: 'web_user'
                })
            });

            if (res.ok) {
                const data = await res.json();
                const npcMsg: Message = { role: 'npc', content: data.response, timestamp: Date.now() };
                setMessages(prev => [...prev, npcMsg]);
            } else {
                setMessages(prev => [...prev, { role: 'npc', content: '[Error: Could not reach NPC]', timestamp: Date.now() }]);
            }
        } catch {
            setMessages(prev => [...prev, { role: 'npc', content: '[Offline - API unavailable]', timestamp: Date.now() }]);
        }

        setIsLoading(false);
    };

    const handleKeyPress = (e: React.KeyboardEvent) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    };

    return (
        <div className="min-h-screen bg-zinc-950 text-white">
            {/* Header */}
            <header className="fixed top-0 left-0 right-0 h-14 bg-gradient-to-b from-zinc-900 to-transparent z-50 flex items-center px-4 border-b border-cyan-500/20">
                <Link href="/" className="font-mono text-lg font-bold bg-gradient-to-r from-cyan-400 to-purple-400 bg-clip-text text-transparent">
                    AO WORLD ENGINE
                </Link>
                <nav className="ml-8 flex gap-4">
                    <Link href="/explore" className="text-sm font-medium text-zinc-500 hover:text-cyan-400 px-3 py-1.5 rounded transition-colors">
                        Explore
                    </Link>
                    <Link href="/chat" className="text-sm font-medium text-cyan-400 px-3 py-1.5 rounded transition-colors">
                        Chat
                    </Link>
                    <Link href="/graph" className="text-sm font-medium text-zinc-500 hover:text-cyan-400 px-3 py-1.5 rounded transition-colors">
                        Graph
                    </Link>
                </nav>
            </header>

            <div className="pt-14 flex h-screen">
                {/* NPC List */}
                <div className="w-64 p-4 border-r border-zinc-800 overflow-y-auto">
                    <h2 className="text-xs text-cyan-400 font-mono mb-4">SELECT NPC</h2>
                    <div className="space-y-2">
                        {npcs.map(npc => (
                            <button
                                key={npc.id}
                                onClick={() => { setSelectedNPC(npc); setMessages([]); }}
                                className={`w-full text-left p-3 rounded-lg transition-all ${selectedNPC?.id === npc.id
                                    ? 'bg-cyan-600/30 border border-cyan-500'
                                    : 'bg-zinc-900 hover:bg-zinc-800 border border-transparent'
                                    }`}
                            >
                                <div className="font-medium">{npc.name}</div>
                                <div className="text-xs text-zinc-500">{npc.archetype}</div>
                            </button>
                        ))}
                    </div>
                </div>

                {/* Chat Area */}
                <div className="flex-1 flex flex-col">
                    {selectedNPC ? (
                        <>
                            {/* NPC Header */}
                            <div className="p-4 border-b border-zinc-800 bg-zinc-900/50">
                                <h2 className="text-xl font-bold text-cyan-400">{selectedNPC.name}</h2>
                                <p className="text-sm text-zinc-500">{selectedNPC.archetype} • Tick {currentTick}</p>
                            </div>

                            {/* Messages */}
                            <div className="flex-1 p-4 overflow-y-auto space-y-4">
                                {messages.length === 0 && (
                                    <div className="text-center text-zinc-600 mt-8">
                                        Start a conversation with {selectedNPC.name}
                                    </div>
                                )}
                                {messages.map((msg, i) => (
                                    <div
                                        key={i}
                                        className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
                                    >
                                        <div className={`max-w-[70%] p-3 rounded-lg ${msg.role === 'user'
                                            ? 'bg-cyan-600/30 text-cyan-100'
                                            : 'bg-zinc-800 text-zinc-100'
                                            }`}>
                                            {msg.content}
                                        </div>
                                    </div>
                                ))}
                                {isLoading && (
                                    <div className="flex justify-start">
                                        <div className="bg-zinc-800 p-3 rounded-lg text-zinc-400">
                                            <span className="animate-pulse">...</span>
                                        </div>
                                    </div>
                                )}
                            </div>

                            {/* Input */}
                            <div className="p-4 border-t border-zinc-800">
                                <div className="flex gap-2">
                                    <input
                                        type="text"
                                        value={message}
                                        onChange={(e) => setMessage(e.target.value)}
                                        onKeyPress={handleKeyPress}
                                        placeholder={`Say something to ${selectedNPC.name}...`}
                                        className="flex-1 bg-zinc-900 border border-zinc-700 rounded-lg px-4 py-2 
                             focus:outline-none focus:border-cyan-500"
                                    />
                                    <Button
                                        onClick={sendMessage}
                                        disabled={isLoading || !message.trim()}
                                        className="bg-cyan-600 hover:bg-cyan-500"
                                    >
                                        Send
                                    </Button>
                                </div>
                            </div>
                        </>
                    ) : (
                        <div className="flex-1 flex items-center justify-center text-zinc-600">
                            <div className="text-center">
                                <div className="text-4xl mb-4">💬</div>
                                <div>Select an NPC to start chatting</div>
                            </div>
                        </div>
                    )}
                </div>

                {/* Tick Control */}
                <div className="w-48 p-4 border-l border-zinc-800">
                    <h3 className="text-xs text-cyan-400 font-mono mb-2">WORLD TIME</h3>
                    <Card className="bg-zinc-900 border-zinc-700">
                        <CardContent className="p-3">
                            <div className="text-2xl font-mono text-cyan-400">{currentTick}</div>
                            <div className="text-xs text-zinc-500">Current Tick</div>
                            <div className="mt-2 flex gap-1">
                                <Button
                                    size="sm"
                                    variant="outline"
                                    onClick={() => setCurrentTick(t => Math.max(0, t - 10))}
                                    className="text-xs"
                                >
                                    -10
                                </Button>
                                <Button
                                    size="sm"
                                    variant="outline"
                                    onClick={() => setCurrentTick(t => t + 10)}
                                    className="text-xs"
                                >
                                    +10
                                </Button>
                            </div>
                        </CardContent>
                    </Card>
                </div>
            </div>
        </div>
    );
}
