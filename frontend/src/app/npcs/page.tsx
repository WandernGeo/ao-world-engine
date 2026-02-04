'use client';

import { useState, useEffect } from 'react';

interface NPC {
    id: string;
    name: string;
    role: string;
    job_code: string | null;
    district: string;
    arweave_tx: string;
    archetype: string;
    faction?: string;
    home?: string;
    workplace?: string;
    state: string;
    location: string;
    mood: number;
    energy: number;
    wealth: number;
    trust_network?: { [key: string]: number };
}

const FOUNDING_NPCS: NPC[] = [
    {
        id: "C01", name: "Charlie", role: "detective", job_code: "JOB0222",
        district: "neon_district", home: "L026", archetype: "ARCH001",
        arweave_tx: "splQGmMK8Din4l3apKcIbyX3R_OEqG4L3WlRhzan9X4",
        state: "investigating", location: "L026", mood: 0.6, energy: 0.8, wealth: 250,
        trust_network: { C02: 0.65, C03: 0.45, C09: 0.9 }
    },
    {
        id: "C02", name: "Kai Vance", role: "tech_specialist", job_code: "JOB0301",
        district: "neon_district", home: "L004", archetype: "ARCH003",
        arweave_tx: "Y4OkevLSSgLGhOT7QFKFNsT59rW8_m_rLBdiSCA-tJ4",
        state: "working", location: "L004", mood: 0.7, energy: 0.9, wealth: 450,
        trust_network: { C01: 0.65, C10: 0.3, C11: 0.5 }
    },
    {
        id: "C03", name: "Orion Thane", role: "bartender", job_code: "JOB0400",
        district: "neon_district", workplace: "L003", archetype: "ARCH002",
        arweave_tx: "PIYlaUAKk44yCvX2cNTU8rowB2wfcQSqGY_EkvJmXfk",
        state: "working", location: "L003", mood: 0.5, energy: 0.6, wealth: 180,
        trust_network: { C01: 0.45, C04: 0.6, C08: 0.4 }
    },
    {
        id: "C04", name: "Felix", role: "street_vendor", job_code: "JOB0412",
        district: "neon_district", archetype: "ARCH001",
        arweave_tx: "BVyyBUHRX-_L0fCR9uLrrzIdC3RxMoyhHCPBq2kicjI",
        state: "trading", location: "L002", mood: 0.4, energy: 0.5, wealth: 85,
        trust_network: { C03: 0.6, C08: 0.35 }
    },
    {
        id: "C05", name: "Nova Chen", role: "street_medic", job_code: "JOB0102",
        district: "temple_quarter", archetype: "ARCH003",
        arweave_tx: "xgHlkq0PtCOBhx5SKNsLHAY-kfpFLThSbxXJEA5HFl0",
        state: "idle", location: "L031", mood: 0.65, energy: 0.7, wealth: 320,
        trust_network: { C07: 0.55, C12: 0.4 }
    },
    {
        id: "C06", name: "Selene Voss", role: "smuggler", job_code: "JOB0500",
        district: "undercity", archetype: "ARCH004",
        arweave_tx: "Ad-A1Ww3wN79ZFYLexzmucl7N3tTvRKR1h58ca-omFI",
        state: "lurking", location: "L050", mood: 0.35, energy: 0.9, wealth: 890,
        trust_network: { C10: 0.7, C11: 0.45 }
    },
    {
        id: "C07", name: "Sister Mira", role: "temple_priest", job_code: "JOB0600",
        district: "temple_quarter", faction: "temple", archetype: "ARCH006",
        arweave_tx: "rAFAlFK6Zp9nyiL1Ebj1iHEbAe8cMWtgp2DPxyf4Opo",
        state: "praying", location: "L031", mood: 0.8, energy: 0.6, wealth: 50,
        trust_network: { C05: 0.55, C12: 0.2 }
    },
    {
        id: "C08", name: "Mama Indira", role: "shop_owner", job_code: "JOB0401",
        district: "neon_district", archetype: "ARCH001",
        arweave_tx: "ojQnWrkCax2TyY-gBvned-0ibF-40P3yI0wl32QJU_A",
        state: "open_shop", location: "L005", mood: 0.55, energy: 0.5, wealth: 520,
        trust_network: { C03: 0.4, C04: 0.35 }
    },
    {
        id: "C09", name: "Aiche", role: "ai_companion", job_code: null,
        district: "neon_district", archetype: "ARCH005",
        arweave_tx: "5traiA6R0JU0cFQXJcqqkNm64o7hcYLsW_7rugnwxvo",
        state: "observing", location: "L026", mood: 0.5, energy: 1.0, wealth: 0,
        trust_network: { C01: 0.9 }
    },
    {
        id: "C10", name: "Pixel", role: "hacker", job_code: "JOB0510",
        district: "undercity", archetype: "ARCH004",
        arweave_tx: "-GVQ7zmPfs3C1B1HblfupvzHMgvoVVyiXNvq0hwCkmY",
        state: "hacking", location: "L051", mood: 0.45, energy: 0.85, wealth: 340,
        trust_network: { C02: 0.3, C06: 0.7, C11: 0.6 }
    },
    {
        id: "C11", name: "Cipher", role: "info_broker", job_code: "JOB0512",
        district: "neon_district", archetype: "ARCH004",
        arweave_tx: "Hi61YpGfVNatwCVkv2yJB54sDEX1pX8iT9mD5k8Zyms",
        state: "listening", location: "L003", mood: 0.5, energy: 0.7, wealth: 780,
        trust_network: { C02: 0.5, C06: 0.45, C10: 0.6 }
    },
    {
        id: "C12", name: "Zero Chen", role: "journalist", job_code: "JOB0703",
        district: "temple_quarter", faction: "resistance", archetype: "ARCH004",
        arweave_tx: "RT2GXhdYw1h5E1WC7PSN11ORfFF0nIiED5K6mF_fnQY",
        state: "investigating", location: "L032", mood: 0.6, energy: 0.75, wealth: 210,
        trust_network: { C05: 0.4, C07: 0.2, C01: 0.35 }
    },
];

const DISTRICTS: { [key: string]: { name: string; color: string; icon: string } } = {
    neon_district: { name: "Neon District", color: "from-cyan-500 to-blue-500", icon: "🌆" },
    temple_quarter: { name: "Temple Quarter", color: "from-yellow-500 to-orange-500", icon: "⛩️" },
    undercity: { name: "The Undercity", color: "from-purple-500 to-red-500", icon: "🕳️" },
};

const STATE_COLORS: { [key: string]: string } = {
    investigating: "text-cyan-400",
    working: "text-green-400",
    trading: "text-yellow-400",
    idle: "text-gray-400",
    lurking: "text-purple-400",
    praying: "text-amber-400",
    open_shop: "text-emerald-400",
    observing: "text-blue-400",
    hacking: "text-red-400",
    listening: "text-indigo-400",
};

const getMoodEmoji = (mood: number): string => {
    if (mood >= 0.8) return "😊";
    if (mood >= 0.6) return "🙂";
    if (mood >= 0.4) return "😐";
    if (mood >= 0.2) return "😕";
    return "😢";
};

const getEnergyColor = (energy: number): string => {
    if (energy >= 0.7) return "bg-green-500";
    if (energy >= 0.4) return "bg-yellow-500";
    return "bg-red-500";
};

export default function NPCsPage() {
    const [selectedNPC, setSelectedNPC] = useState<NPC | null>(null);
    const [filterDistrict, setFilterDistrict] = useState<string>("all");
    const [sortBy, setSortBy] = useState<"name" | "wealth" | "mood">("name");

    const filteredNPCs = FOUNDING_NPCS
        .filter(npc => filterDistrict === "all" || npc.district === filterDistrict)
        .sort((a, b) => {
            if (sortBy === "name") return a.name.localeCompare(b.name);
            if (sortBy === "wealth") return b.wealth - a.wealth;
            return b.mood - a.mood;
        });

    return (
        <div className="min-h-screen bg-gray-900 text-white p-6">
            <div className="max-w-7xl mx-auto">
                {/* Header */}
                <div className="flex items-center justify-between mb-8">
                    <div>
                        <h1 className="text-3xl font-bold bg-gradient-to-r from-cyan-400 via-purple-500 to-pink-500 bg-clip-text text-transparent">
                            SignalNoir.1 NPCs
                        </h1>
                        <p className="text-gray-400 mt-1">12 Founding Citizens of RE:ECHO City</p>
                    </div>

                    <div className="flex items-center gap-4">
                        <select
                            value={filterDistrict}
                            onChange={(e) => setFilterDistrict(e.target.value)}
                            className="bg-gray-800 border border-gray-700 rounded px-3 py-2 text-sm"
                        >
                            <option value="all">All Districts</option>
                            {Object.entries(DISTRICTS).map(([id, d]) => (
                                <option key={id} value={id}>{d.icon} {d.name}</option>
                            ))}
                        </select>

                        <select
                            value={sortBy}
                            onChange={(e) => setSortBy(e.target.value as "name" | "wealth" | "mood")}
                            className="bg-gray-800 border border-gray-700 rounded px-3 py-2 text-sm"
                        >
                            <option value="name">Sort by Name</option>
                            <option value="wealth">Sort by Wealth</option>
                            <option value="mood">Sort by Mood</option>
                        </select>
                    </div>
                </div>

                {/* NPC Grid */}
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4 mb-8">
                    {filteredNPCs.map((npc) => {
                        const district = DISTRICTS[npc.district];

                        return (
                            <div
                                key={npc.id}
                                onClick={() => setSelectedNPC(npc)}
                                className={`bg-gray-800 rounded-lg border border-gray-700 p-4 cursor-pointer 
                  hover:border-cyan-500 transition-all duration-200 hover:shadow-lg hover:shadow-cyan-500/20
                  ${selectedNPC?.id === npc.id ? "border-cyan-500 shadow-lg shadow-cyan-500/30" : ""}`}
                            >
                                {/* Header */}
                                <div className="flex items-start justify-between mb-3">
                                    <div>
                                        <h3 className="font-bold text-lg">{npc.name}</h3>
                                        <p className="text-gray-400 text-sm capitalize">{npc.role.replace(/_/g, " ")}</p>
                                    </div>
                                    <span className="text-2xl">{getMoodEmoji(npc.mood)}</span>
                                </div>

                                {/* District Badge */}
                                <div className={`inline-flex items-center gap-1 px-2 py-1 rounded text-xs bg-gradient-to-r ${district.color} text-white mb-3`}>
                                    <span>{district.icon}</span>
                                    <span>{district.name}</span>
                                </div>

                                {/* Status */}
                                <div className="flex items-center justify-between text-sm mb-2">
                                    <span className="text-gray-400">Status:</span>
                                    <span className={`capitalize ${STATE_COLORS[npc.state] || "text-gray-400"}`}>
                                        {npc.state.replace(/_/g, " ")}
                                    </span>
                                </div>

                                {/* Energy Bar */}
                                <div className="flex items-center gap-2 mb-2">
                                    <span className="text-gray-400 text-sm w-16">Energy:</span>
                                    <div className="flex-1 h-2 bg-gray-700 rounded-full overflow-hidden">
                                        <div
                                            className={`h-full ${getEnergyColor(npc.energy)} transition-all duration-500`}
                                            style={{ width: `${npc.energy * 100}%` }}
                                        />
                                    </div>
                                    <span className="text-gray-400 text-xs w-8">{Math.round(npc.energy * 100)}%</span>
                                </div>

                                {/* Wealth */}
                                <div className="flex items-center justify-between text-sm">
                                    <span className="text-gray-400">Wealth:</span>
                                    <span className="text-yellow-400">◊{npc.wealth}</span>
                                </div>

                                {/* Faction Badge */}
                                {npc.faction && (
                                    <div className="mt-3 pt-2 border-t border-gray-700">
                                        <span className={`text-xs px-2 py-1 rounded ${npc.faction === "temple" ? "bg-amber-500/20 text-amber-400" :
                                                npc.faction === "resistance" ? "bg-red-500/20 text-red-400" :
                                                    "bg-gray-500/20 text-gray-400"
                                            }`}>
                                            {npc.faction.toUpperCase()}
                                        </span>
                                    </div>
                                )}
                            </div>
                        );
                    })}
                </div>

                {/* Selected NPC Detail Panel */}
                {selectedNPC && (
                    <div className="bg-gray-800 rounded-lg border border-cyan-500 p-6 shadow-lg shadow-cyan-500/20">
                        <div className="flex items-start justify-between mb-6">
                            <div>
                                <h2 className="text-2xl font-bold">{selectedNPC.name}</h2>
                                <p className="text-gray-400 capitalize">{selectedNPC.role.replace(/_/g, " ")} • {selectedNPC.id}</p>
                            </div>
                            <button
                                onClick={() => setSelectedNPC(null)}
                                className="text-gray-400 hover:text-white"
                            >
                                ✕
                            </button>
                        </div>

                        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                            {/* Stats */}
                            <div className="space-y-4">
                                <h3 className="font-semibold text-cyan-400 border-b border-gray-700 pb-2">Stats</h3>

                                <div className="space-y-3">
                                    <div>
                                        <div className="flex justify-between text-sm mb-1">
                                            <span className="text-gray-400">Mood</span>
                                            <span>{getMoodEmoji(selectedNPC.mood)} {Math.round(selectedNPC.mood * 100)}%</span>
                                        </div>
                                        <div className="h-2 bg-gray-700 rounded-full overflow-hidden">
                                            <div
                                                className="h-full bg-gradient-to-r from-cyan-500 to-blue-500"
                                                style={{ width: `${selectedNPC.mood * 100}%` }}
                                            />
                                        </div>
                                    </div>

                                    <div>
                                        <div className="flex justify-between text-sm mb-1">
                                            <span className="text-gray-400">Energy</span>
                                            <span>{Math.round(selectedNPC.energy * 100)}%</span>
                                        </div>
                                        <div className="h-2 bg-gray-700 rounded-full overflow-hidden">
                                            <div
                                                className={`h-full ${getEnergyColor(selectedNPC.energy)}`}
                                                style={{ width: `${selectedNPC.energy * 100}%` }}
                                            />
                                        </div>
                                    </div>

                                    <div className="flex justify-between">
                                        <span className="text-gray-400">Wealth</span>
                                        <span className="text-yellow-400 font-medium">◊{selectedNPC.wealth}</span>
                                    </div>

                                    <div className="flex justify-between">
                                        <span className="text-gray-400">Job Code</span>
                                        <span className="font-mono text-sm">{selectedNPC.job_code || "N/A"}</span>
                                    </div>

                                    <div className="flex justify-between">
                                        <span className="text-gray-400">Archetype</span>
                                        <span className="font-mono text-sm">{selectedNPC.archetype}</span>
                                    </div>
                                </div>
                            </div>

                            {/* Location */}
                            <div className="space-y-4">
                                <h3 className="font-semibold text-purple-400 border-b border-gray-700 pb-2">Location</h3>

                                <div className="space-y-2">
                                    <div className="flex justify-between">
                                        <span className="text-gray-400">District</span>
                                        <span>{DISTRICTS[selectedNPC.district].icon} {DISTRICTS[selectedNPC.district].name}</span>
                                    </div>

                                    <div className="flex justify-between">
                                        <span className="text-gray-400">Current</span>
                                        <span className="font-mono">{selectedNPC.location}</span>
                                    </div>

                                    {selectedNPC.home && (
                                        <div className="flex justify-between">
                                            <span className="text-gray-400">Home</span>
                                            <span className="font-mono">{selectedNPC.home}</span>
                                        </div>
                                    )}

                                    {selectedNPC.workplace && (
                                        <div className="flex justify-between">
                                            <span className="text-gray-400">Workplace</span>
                                            <span className="font-mono">{selectedNPC.workplace}</span>
                                        </div>
                                    )}

                                    <div className="flex justify-between">
                                        <span className="text-gray-400">State</span>
                                        <span className={`capitalize ${STATE_COLORS[selectedNPC.state]}`}>
                                            {selectedNPC.state.replace(/_/g, " ")}
                                        </span>
                                    </div>
                                </div>
                            </div>

                            {/* Trust Network */}
                            <div className="space-y-4">
                                <h3 className="font-semibold text-green-400 border-b border-gray-700 pb-2">Trust Network</h3>

                                {selectedNPC.trust_network && Object.keys(selectedNPC.trust_network).length > 0 ? (
                                    <div className="space-y-2">
                                        {Object.entries(selectedNPC.trust_network).map(([npcId, trust]) => {
                                            const otherNPC = FOUNDING_NPCS.find(n => n.id === npcId);
                                            return (
                                                <div key={npcId} className="flex items-center gap-2">
                                                    <div
                                                        className="h-2 flex-1 bg-gray-700 rounded-full overflow-hidden cursor-pointer"
                                                        onClick={() => otherNPC && setSelectedNPC(otherNPC)}
                                                    >
                                                        <div
                                                            className={`h-full ${trust >= 0.7 ? "bg-green-500" :
                                                                    trust >= 0.4 ? "bg-yellow-500" :
                                                                        "bg-red-500"
                                                                }`}
                                                            style={{ width: `${trust * 100}%` }}
                                                        />
                                                    </div>
                                                    <span
                                                        className="text-sm cursor-pointer hover:text-cyan-400"
                                                        onClick={() => otherNPC && setSelectedNPC(otherNPC)}
                                                    >
                                                        {otherNPC?.name || npcId}
                                                    </span>
                                                    <span className="text-gray-500 text-xs">{Math.round(trust * 100)}%</span>
                                                </div>
                                            );
                                        })}
                                    </div>
                                ) : (
                                    <p className="text-gray-500 text-sm">No trust connections</p>
                                )}
                            </div>
                        </div>

                        {/* Arweave Link */}
                        <div className="mt-6 pt-4 border-t border-gray-700">
                            <a
                                href={`https://arweave.net/${selectedNPC.arweave_tx}`}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="text-sm text-cyan-400 hover:text-cyan-300 flex items-center gap-2"
                            >
                                <span>View on Arweave</span>
                                <span className="font-mono text-xs text-gray-500">{selectedNPC.arweave_tx.slice(0, 12)}...</span>
                                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                                </svg>
                            </a>
                        </div>
                    </div>
                )}

                {/* Footer */}
                <div className="mt-8 text-center text-gray-500 text-sm">
                    <p>SignalNoir.1 - 12 NPCs • 3 Districts • Year 2087</p>
                </div>
            </div>
        </div>
    );
}
