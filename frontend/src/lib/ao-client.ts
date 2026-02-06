/**
 * AO World Engine Client
 *
 * Connects frontend to the deployed AO world process.
 * Provides read-only access to world state without requiring a wallet.
 */

import { dryrun } from "@permaweb/aoconnect";

// Process IDs from deployment
export const AO_PROCESS_IDS = {
    world: "3KJMDJ81ob8qHUB8Fc-fn9n4pmSBqIh2S1DOM1zkqt0",
};

/**
 * Query world state from AO using get-state handler
 */
export async function getWorldState(): Promise<{
    tick: number;
    day: number;
    year: number;
    population: number;
    budget: number;
    time: { hour: number; period: string };
}> {
    try {
        const result = await dryrun({
            process: AO_PROCESS_IDS.world,
            tags: [{ name: "Action", value: "get-state" }],
            data: "{}",
        });

        if (result.Messages?.[0]?.Data) {
            const data = JSON.parse(result.Messages[0].Data);
            return {
                tick: data.tick || 0,
                day: data.day || 0,
                year: data.year || 0,
                population: data.population || 0,
                budget: data.budget || 0,
                time: data.time || { hour: 0, period: "T01" },
            };
        }
        throw new Error("No response from AO");
    } catch (error) {
        console.error("Failed to query AO world state:", error);
        // Return fallback for demo mode
        return {
            tick: 0,
            day: 0,
            year: 0,
            population: 800,
            budget: 1000000,
            time: { hour: 0, period: "T01" },
        };
    }
}

/**
 * Query economy stats from AO using get-economy handler
 */
export async function getEconomyState(): Promise<{
    budget: number;
    taxRate: number;
    population: number;
    estimatedDailyRevenue: number;
}> {
    try {
        const result = await dryrun({
            process: AO_PROCESS_IDS.world,
            tags: [{ name: "Action", value: "get-economy" }],
            data: "{}",
        });

        if (result.Messages?.[0]?.Data) {
            const data = JSON.parse(result.Messages[0].Data);
            return {
                budget: data.budget || 0,
                taxRate: data.tax_rate || 0.1,
                population: data.population || 0,
                estimatedDailyRevenue: data.estimated_daily_revenue || 0,
            };
        }
        throw new Error("No response from AO");
    } catch (error) {
        console.error("Failed to query AO economy:", error);
        return {
            budget: 1000000,
            taxRate: 0.1,
            population: 800,
            estimatedDailyRevenue: 6000,
        };
    }
}

/**
 * Query time info from AO using get-time handler
 */
export async function getTimeState(): Promise<{
    tick: number;
    day: number;
    hour: number;
    period: string;
    year: number;
}> {
    try {
        const result = await dryrun({
            process: AO_PROCESS_IDS.world,
            tags: [{ name: "Action", value: "get-time" }],
            data: "{}",
        });

        if (result.Messages?.[0]?.Data) {
            const data = JSON.parse(result.Messages[0].Data);
            return {
                tick: data.tick || 0,
                day: data.day || 0,
                hour: data.hour || 0,
                period: data.period || "T01",
                year: data.year || 0,
            };
        }
        throw new Error("No response from AO");
    } catch (error) {
        console.error("Failed to query AO time:", error);
        return { tick: 0, day: 0, hour: 0, period: "T01", year: 0 };
    }
}

/**
 * Check if AO connection is live by querying state
 */
export async function isAOLive(): Promise<boolean> {
    try {
        const result = await dryrun({
            process: AO_PROCESS_IDS.world,
            tags: [{ name: "Action", value: "get-state" }],
            data: "{}",
        });
        return !!(result.Messages?.[0]?.Data);
    } catch {
        return false;
    }
}

/**
 * Query NPC locations from AO
 */
export interface NPCLocation {
    location: string;
    state: string;
    since_tick: number;
}

export async function getNPCLocations(): Promise<{
    count: number;
    tick: number;
    locations: Record<string, NPCLocation>;
}> {
    try {
        const result = await dryrun({
            process: AO_PROCESS_IDS.world,
            tags: [{ name: "Action", value: "get-npc-locations" }],
            data: "{}",
        });

        if (result.Messages?.[0]?.Data) {
            const data = JSON.parse(result.Messages[0].Data);
            return {
                count: data.count || 0,
                tick: data.tick || 0,
                locations: data.locations || {},
            };
        }
        throw new Error("No response from AO");
    } catch (error) {
        console.error("Failed to query NPC locations:", error);
        return { count: 0, tick: 0, locations: {} };
    }
}

/**
 * Query NPC movement log from AO
 */
export interface MovementLogEntry {
    tick: number;
    npc_id: string;
    from: string;
    to: string;
    state: string;
    hour: number;
    shift?: string;
}

export async function getMovementLog(limit: number = 20): Promise<{
    count: number;
    entries: MovementLogEntry[];
}> {
    try {
        const result = await dryrun({
            process: AO_PROCESS_IDS.world,
            tags: [{ name: "Action", value: "get-movement-log" }],
            data: JSON.stringify({ limit }),
        });

        if (result.Messages?.[0]?.Data) {
            const data = JSON.parse(result.Messages[0].Data);
            return {
                count: data.count || 0,
                entries: data.log || [],
            };
        }
        throw new Error("No response from AO");
    } catch (error) {
        console.error("Failed to query movement log:", error);
        return { count: 0, entries: [] };
    }
}

/**
 * Query NPC wallets (wealth/balance) from AO
 */
export interface NPCWallet {
    npc_id: string;
    balance: number;
    income_tick: number;
    spending_tick: number;
}

export async function getNPCWallets(limit: number = 800): Promise<{
    wallets: NPCWallet[];
    total_economy: number;
}> {
    try {
        const result = await dryrun({
            process: AO_PROCESS_IDS.world,
            tags: [{ name: "Action", value: "get-npc-wallets" }],
            data: JSON.stringify({ limit }),
        });

        if (result.Messages?.[0]?.Data) {
            const data = JSON.parse(result.Messages[0].Data);
            return {
                wallets: data.wallets || [],
                total_economy: data.total_economy || 0,
            };
        }
        throw new Error("No response from AO");
    } catch (error) {
        console.error("Failed to query NPC wallets:", error);
        return { wallets: [], total_economy: 0 };
    }
}

/**
 * Query all NPCs basic info from AO
 */
export async function getAllNPCs(): Promise<Record<string, unknown>[]> {
    try {
        const result = await dryrun({
            process: AO_PROCESS_IDS.world,
            tags: [{ name: "Action", value: "get-all-npcs" }],
            data: "{}",
        });

        if (result.Messages?.[0]?.Data) {
            const data = JSON.parse(result.Messages[0].Data);
            // Convert object to array if needed
            if (Array.isArray(data.npcs)) {
                return data.npcs;
            }
            if (data.npcs && typeof data.npcs === 'object') {
                return Object.values(data.npcs);
            }
            return [];
        }
        throw new Error("No response from AO");
    } catch (error) {
        console.error("Failed to query all NPCs:", error);
        return [];
    }
}

// Re-export for convenience
export type WorldState = Awaited<ReturnType<typeof getWorldState>>;
export type EconomyState = Awaited<ReturnType<typeof getEconomyState>>;
export type TimeState = Awaited<ReturnType<typeof getTimeState>>;
export type NPCLocationsState = Awaited<ReturnType<typeof getNPCLocations>>;
export type MovementLogState = Awaited<ReturnType<typeof getMovementLog>>;
