/**
 * Data Loader Utility
 * Fetches data from the AO World Engine API
 */

const CLOUD_API = 'https://ao-world-engine-1071951656531.us-central1.run.app';
const LOCAL_API = 'http://localhost:8080';

// Types matching the codec/API data
export interface NPCData {
    id: string;
    name: string;
    archetype: string;
    faction: string;
    home: string;
    workplace?: string;
    schedule: string;
    personality: {
        aggression: number;
        curiosity: number;
        greed: number;
        loyalty: number;
        sociability: number;
    };
    skills: {
        combat: number;
        social: number;
        stealth: number;
        survival: number;
        tech: number;
    };
    // Extended personality (from full codec)
    mbti?: string;
    zodiac?: string;
    traits?: string[];
    catchphrase?: string;
    role?: string;
    // Runtime state
    activity?: string;
    mood?: string;
    location?: string;
}

export interface BuildingData {
    id: string;
    name: string;
    type: string;
    district: string;
    levels: number;
    template?: string;
}

export interface DistrictData {
    id: string;
    name: string;
    code: string;
    color: string;
    buildings: BuildingData[];
    center?: { lat: number; lon: number };
}

// Get best API endpoint
export async function getApiBase(): Promise<string> {
    try {
        const res = await fetch(`${LOCAL_API}/health`, {
            method: 'GET',
            signal: AbortSignal.timeout(1000)
        });
        if (res.ok) return LOCAL_API;
    } catch { /* ignore */ }
    return CLOUD_API;
}

// Fetch all NPCs from API
export async function fetchNPCs(apiBase?: string, limit: number = 800): Promise<NPCData[]> {
    const base = apiBase || await getApiBase();
    try {
        const res = await fetch(`${base}/api/npcs?limit=${limit}`);
        if (!res.ok) throw new Error('Failed to fetch NPCs');
        const data = await res.json();
        return data.npcs || [];
    } catch (error) {
        console.error('fetchNPCs error:', error);
        return [];
    }
}

// Fetch NPC state at a specific tick
export async function fetchNPCState(npcId: string, tick: number, apiBase?: string): Promise<NPCData | null> {
    const base = apiBase || await getApiBase();
    try {
        const res = await fetch(`${base}/api/npcs/${npcId}/state?tick=${tick}`);
        if (!res.ok) throw new Error('Failed to fetch NPC state');
        return await res.json();
    } catch (error) {
        console.error('fetchNPCState error:', error);
        return null;
    }
}

// Fetch buildings from API
export async function fetchBuildings(apiBase?: string): Promise<BuildingData[]> {
    const base = apiBase || await getApiBase();
    try {
        const res = await fetch(`${base}/api/buildings`);
        if (!res.ok) throw new Error('Failed to fetch buildings');
        const data = await res.json();
        return data.buildings || [];
    } catch (error) {
        console.error('fetchBuildings error:', error);
        return [];
    }
}

// Mood/activity derivation from personality
export function deriveMood(personality: NPCData['personality']): string {
    const { aggression, sociability, curiosity, loyalty } = personality;
    if (aggression > 0.7) return 'hostile';
    if (sociability > 0.7) return 'friendly';
    if (curiosity > 0.6 && aggression < 0.3) return 'curious';
    if (loyalty > 0.7) return 'cautious';
    if (sociability < 0.3) return 'secretive';
    return 'neutral';
}

// Activity derivation from archetype/schedule
const ARCHETYPE_ACTIVITIES: Record<string, string[]> = {
    criminal: ['scheming', 'hiding', 'dealing'],
    worker: ['working', 'resting', 'commuting'],
    resistance_fighter: ['training', 'patrolling', 'meeting'],
    temple: ['praying', 'preaching', 'processing'],
    merchant: ['trading', 'selling', 'negotiating'],
    hacker: ['hacking', 'researching', 'coding'],
    visitor: ['exploring', 'shopping', 'wandering'],
    default: ['walking', 'waiting', 'watching'],
};

export function deriveActivity(archetype: string): string {
    const activities = ARCHETYPE_ACTIVITIES[archetype] || ARCHETYPE_ACTIVITIES.default;
    return activities[Math.floor(Math.random() * activities.length)];
}
