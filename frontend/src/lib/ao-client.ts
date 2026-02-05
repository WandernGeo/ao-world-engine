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

// No connection needed - dryrun works without wallet

/**
 * Query world state from AO
 */
export async function getWorldState(): Promise<{
    worldTick: number;
    population: number;
    districts: number;
    budget: number;
    currentTime: string;
}> {
    try {
        const result = await dryrun({
            process: AO_PROCESS_IDS.world,
            tags: [{ name: "Action", value: "Eval" }],
            data: `
        local state = get_state()
        if state then
          return require("json").encode({
            world_tick = state.world_tick or 0,
            population = state.population or 0,
            districts = state.districts or 0,
            budget = state.budget or 0,
            current_time = state.current_time or "unknown"
          })
        else
          return require("json").encode({error = "No state"})
        end
      `,
        });

        if (result.Messages?.[0]?.Data) {
            const data = JSON.parse(result.Messages[0].Data);
            return {
                worldTick: data.world_tick || 0,
                population: data.population || 0,
                districts: data.districts || 0,
                budget: data.budget || 0,
                currentTime: data.current_time || "unknown",
            };
        }
        throw new Error("No response from AO");
    } catch (error) {
        console.error("Failed to query AO world state:", error);
        // Return fallback for demo mode
        return {
            worldTick: 0,
            population: 800,
            districts: 12,
            budget: 1000000,
            currentTime: new Date().toISOString(),
        };
    }
}

/**
 * Query NPC location from AO (deterministic based on tick)
 */
export async function getNPCLocation(
    npcId: string
): Promise<{ location: string; activity: string } | null> {
    try {
        const result = await dryrun({
            process: AO_PROCESS_IDS.world,
            tags: [{ name: "Action", value: "Eval" }],
            data: `
        local npc = get_npc("${npcId}")
        if npc then
          return require("json").encode({
            location = npc.current_location or npc.home_location,
            activity = npc.current_activity or "idle"
          })
        end
        return require("json").encode({error = "NPC not found"})
      `,
        });

        if (result.Messages?.[0]?.Data) {
            const data = JSON.parse(result.Messages[0].Data);
            if (data.error) return null;
            return data;
        }
        return null;
    } catch (error) {
        console.error("Failed to query NPC location:", error);
        return null;
    }
}

/**
 * Get all founding NPCs from AO
 */
export async function getFoundingNPCs(): Promise<
    Array<{
        id: string;
        name: string;
        faction: string;
        role: string;
        location: string;
    }>
> {
    try {
        const result = await dryrun({
            process: AO_PROCESS_IDS.world,
            tags: [{ name: "Action", value: "Eval" }],
            data: `
        local npcs = get_all_founding_npcs()
        local list = {}
        for key, npc in pairs(npcs) do
          table.insert(list, {
            id = npc.id,
            name = npc.name,
            faction = npc.faction,
            role = npc.role,
            location = npc.home_location
          })
        end
        return require("json").encode(list)
      `,
        });

        if (result.Messages?.[0]?.Data) {
            return JSON.parse(result.Messages[0].Data);
        }
        return [];
    } catch (error) {
        console.error("Failed to query founding NPCs:", error);
        return [];
    }
}

/**
 * Check if AO connection is live
 */
export async function isAOLive(): Promise<boolean> {
    try {
        const result = await dryrun({
            process: AO_PROCESS_IDS.world,
            tags: [{ name: "Action", value: "Eval" }],
            data: "return 'live'",
        });
        return result.Messages?.[0]?.Data === "live";
    } catch {
        return false;
    }
}
