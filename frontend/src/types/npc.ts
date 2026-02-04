// NPC data types matching the backend npcs_generated_with_personality.json

export interface NPCPersonality {
    aggression: number;
    sociability: number;
    greed: number;
    loyalty: number;
    curiosity: number;
    birth_tick?: number;
    echo_alignment?: {
        signal: string;
        method: string;
        name: string;
    };
    archetype?: string;
    mbti?: string;
    zodiac?: string;
    zodiac_element?: string;
    chinese_animal?: string;
    chinese_element?: string;
    traits?: string[];
    weaknesses?: string[];
}

export interface NPCSkills {
    combat: number;
    stealth: number;
    tech: number;
    social: number;
    survival: number;
}

export interface NPC {
    id: string;
    name: string;
    archetype: string;
    schedule: string;
    faction: string;
    home: string;
    workplace: string;
    block: number;
    personality: NPCPersonality;
    skills: NPCSkills;
    // Runtime state (added by simulation)
    location?: string;
    activity?: string;
    mood?: string;
    // Visual (to be generated)
    portrait_url?: string;
    description?: string;
}

export interface Building {
    id: string;
    name: string;
    type: 'residential' | 'commercial' | 'temple' | 'industrial' | 'entertainment' | 'financial';
    block?: number;
    floors?: number;
    units?: number;
    capacity?: number;
    shops?: number;
    polygon?: [number, number][];
    occupants?: string[];
}

export interface District {
    id: string;
    name: string;
    description?: string;
    color: string;
    blocks?: number;
    grid?: string;
    area_sqm?: number;
    buildings: Building[];
}

export interface WorldData {
    district: {
        name: string;
        description: string;
        blocks: number;
        grid: string;
        area_sqm: number;
    };
    buildings: Building[];
    npcs: NPC[];
    total_npcs: number;
    generated_at: string;
}

// Mood calculation based on personality
export function calculateMood(npc: NPC): string {
    const { aggression, sociability, greed, loyalty } = npc.personality;

    if (aggression > 0.7) return 'hostile';
    if (aggression > 0.5 && loyalty < 0.3) return 'suspicious';
    if (sociability > 0.7) return 'friendly';
    if (sociability > 0.5) return 'neutral';
    if (greed > 0.7) return 'calculating';
    if (loyalty > 0.7) return 'devoted';
    return 'cautious';
}

// Activity based on archetype and time
export function calculateActivity(npc: NPC, tick: number): string {
    const hour = Math.floor((tick % 100) / 4.16); // 100 ticks = 24 hours
    const isNight = hour < 6 || hour > 22;
    const isWorkHours = hour >= 9 && hour <= 17;

    if (isNight) {
        if (npc.archetype === 'criminal') return 'prowling';
        return 'sleeping';
    }

    if (isWorkHours) {
        switch (npc.archetype) {
            case 'criminal': return 'planning';
            case 'merchant': return 'selling';
            case 'worker': return 'working';
            case 'temple': return 'praying';
            case 'entertainer': return 'performing';
            default: return 'working';
        }
    }

    // Evening/morning activities
    const activities = ['eating', 'walking', 'socializing', 'shopping', 'relaxing'];
    return activities[Math.floor(Math.random() * activities.length)];
}

// Get NPC location based on time and schedule
export function calculateLocation(npc: NPC, tick: number): string {
    const hour = Math.floor((tick % 100) / 4.16);
    const isWorkHours = hour >= 9 && hour <= 17;
    const isNight = hour < 6 || hour > 22;

    if (isNight) return npc.home;
    if (isWorkHours) return npc.workplace;
    return Math.random() > 0.5 ? npc.home : npc.workplace;
}
