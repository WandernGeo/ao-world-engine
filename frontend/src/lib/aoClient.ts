/**
 * AO Client - Connect frontend to Arweave AO Process
 * 
 * This module provides functions to query and interact with
 * the AO World Engine process running on Arweave mainnet.
 */

// AO Process ID (deployed on Arweave mainnet)
const AO_PROCESS_ID = "nJe-5S9dpBxeA9BO7Q7FNP2jHpl6ETTN5hmyBdf-XxA";

// Gateway URLs for querying AO
const AO_GATEWAY = "https://cu.ao-testnet.xyz";
const ARWEAVE_GATEWAY = "https://arweave.net";

// Types
export interface WorldState {
    worldTick: number;
    worldDay: number;
    worldYear: number;
    budget: number;
    population: number;
    layerId: string;
}

export interface NPCData {
    id: string;
    name: string;
    archetype: string;
    faction: string;
    home: string;
    workplace: string;
    personality: {
        aggression: number;
        sociability: number;
        greed: number;
        loyalty: number;
        curiosity: number;
    };
    skills: {
        combat: number;
        stealth: number;
        tech: number;
        social: number;
        survival: number;
    };
    age: number;
    family: {
        spouse_id: string | null;
        parent_ids: string[];
        sibling_ids: string[];
        children_ids: string[];
        household_id: string;
        marital_status: string;
    };
    appearance: {
        skin: string;
        hair: string;
        eyes: string;
        height: number;
        build: string;
        notable: string | null;
    };
    mood: {
        current: string;
        intensity: number;
        stability: number;
        triggers: string[];
    };
    desires?: {
        short_term: string[];
        long_term: string[];
        life_goal: string;
    };
}

export interface DistrictData {
    id: string;
    name: string;
    population: number;
    danger_level: number;
}

// =============================================================================
// CORE AO COMMUNICATION
// =============================================================================

/**
 * Send a dry-run query to the AO process (read-only, no state change)
 */
export async function queryAO(action: string, data: Record<string, unknown> = {}): Promise<unknown> {
    try {
        const response = await fetch(`${AO_GATEWAY}/dry-run?process-id=${AO_PROCESS_ID}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                Id: '0000000000000000000000000000000000000000001',
                Target: AO_PROCESS_ID,
                Owner: '0000000000000000000000000000000000000000001',
                Tags: [
                    { name: 'Action', value: action },
                    { name: 'Data-Protocol', value: 'ao' },
                    { name: 'Type', value: 'Message' },
                    { name: 'Variant', value: 'ao.TN.1' }
                ],
                Data: JSON.stringify(data)
            })
        });

        if (!response.ok) {
            console.error('AO query failed:', response.status);
            return null;
        }

        const result = await response.json();

        // Extract data from AO response
        if (result.Messages && result.Messages.length > 0) {
            const msg = result.Messages[0];
            if (msg.Data) {
                try {
                    return JSON.parse(msg.Data);
                } catch {
                    return msg.Data;
                }
            }
        }

        return result;
    } catch (error) {
        console.error('AO query error:', error);
        return null;
    }
}

/**
 * Send a message to the AO process (requires wallet for state changes)
 * For now, this is a placeholder - state changes require ArConnect
 */
export async function sendMessage(action: string, data: Record<string, unknown> = {}): Promise<unknown> {
    // TODO: Integrate ArConnect for signed transactions
    console.warn('State-changing messages require ArConnect wallet');
    return queryAO(action, data);
}

// =============================================================================
// WORLD STATE QUERIES
// =============================================================================

/**
 * Get the current world state from AO
 */
export async function getWorldState(): Promise<WorldState | null> {
    const result = await queryAO('get-state');

    if (result && typeof result === 'object') {
        const r = result as Record<string, unknown>;
        return {
            worldTick: (r.world_tick as number) || 0,
            worldDay: (r.world_day as number) || 0,
            worldYear: (r.world_year as number) || 0,
            budget: (r.budget as number) || 0,
            population: (r.population as number) || 0,
            layerId: (r.layer_id as string) || 'layer_00_testnet'
        };
    }

    return null;
}

/**
 * Get time information for current tick
 */
export async function getTimeInfo(): Promise<{
    tick: number;
    day: number;
    hour: number;
    period: string;
} | null> {
    const result = await queryAO('get-time');

    if (result && typeof result === 'object') {
        return result as { tick: number; day: number; hour: number; period: string };
    }

    return null;
}

// =============================================================================
// NPC QUERIES
// =============================================================================

/**
 * Get all NPCs from the AO process
 */
export async function getAllNPCs(): Promise<NPCData[]> {
    const result = await queryAO('get-all-npcs');

    if (result && Array.isArray(result)) {
        return result as NPCData[];
    }

    // Return empty array if AO query fails
    return [];
}

/**
 * Get a specific NPC by ID
 */
export async function getNPC(npcId: string): Promise<NPCData | null> {
    const result = await queryAO('get-npc', { npc_id: npcId });

    if (result && typeof result === 'object') {
        return result as NPCData;
    }

    return null;
}

/**
 * Get NPCs in a specific district
 */
export async function getDistrictNPCs(districtId: string): Promise<NPCData[]> {
    const result = await queryAO('get-district-npcs', { district_id: districtId });

    if (result && Array.isArray(result)) {
        return result as NPCData[];
    }

    return [];
}

/**
 * Get founding NPCs (the 12 canonical characters)
 */
export async function getFoundingNPCs(): Promise<NPCData[]> {
    const result = await queryAO('get-founding-npcs');

    if (result && Array.isArray(result)) {
        return result as NPCData[];
    }

    return [];
}

// =============================================================================
// DISTRICT QUERIES
// =============================================================================

/**
 * Get all districts
 */
export async function getDistricts(): Promise<DistrictData[]> {
    const result = await queryAO('get-districts');

    if (result && Array.isArray(result)) {
        return result as DistrictData[];
    }

    return [];
}

// =============================================================================
// UTILITY FUNCTIONS
// =============================================================================

/**
 * Check if AO process is reachable
 */
export async function checkAOConnection(): Promise<boolean> {
    try {
        const state = await getWorldState();
        return state !== null;
    } catch {
        return false;
    }
}

/**
 * Get the AO process ID
 */
export function getProcessId(): string {
    return AO_PROCESS_ID;
}

/**
 * Format tick to human-readable time
 */
export function formatTickTime(tick: number): { day: number; hour: number; minute: number } {
    const TICKS_PER_HOUR = 10;
    const HOURS_PER_DAY = 24;

    const totalHours = Math.floor(tick / TICKS_PER_HOUR);
    const day = Math.floor(totalHours / HOURS_PER_DAY) + 1;
    const hour = totalHours % HOURS_PER_DAY;
    const minute = (tick % TICKS_PER_HOUR) * 6;

    return { day, hour, minute };
}
