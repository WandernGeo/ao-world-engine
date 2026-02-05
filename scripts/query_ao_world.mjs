/**
 * Query AO World Process State
 * 
 * Verifies the deployed world process is working.
 */

import { connect, createDataItemSigner } from "@permaweb/aoconnect";
import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));

async function queryWorld() {
    // Load config
    const config = JSON.parse(fs.readFileSync(path.join(__dirname, "../ao-process-ids.json"), "utf-8"));
    const processId = config.world;

    console.log("========================================");
    console.log("  AO World Engine - Query State");
    console.log("========================================\n");
    console.log(`Process ID: ${processId}\n`);

    const ao = connect();

    // Load wallet for signing
    const wallet = JSON.parse(fs.readFileSync(path.join(__dirname, "../wallet.json"), "utf-8"));
    const signer = createDataItemSigner(wallet);

    // Query state
    console.log("Querying world state...\n");

    const msgId = await ao.message({
        process: processId,
        signer,
        tags: [{ name: "Action", value: "Eval" }],
        data: `
      local state = get_state()
      return require("json").encode({
        world_tick = state.world_tick,
        population = state.population,
        districts = state.districts,
        budget = state.budget,
        time = state.current_time
      })
    `
    });

    const result = await ao.result({
        process: processId,
        message: msgId
    });

    console.log("Result:", JSON.stringify(result, null, 2));

    if (result.Messages?.[0]?.Data) {
        try {
            const state = JSON.parse(result.Messages[0].Data);
            console.log("\n✅ WORLD STATE:");
            console.log(`  - Tick: ${state.world_tick}`);
            console.log(`  - Population: ${state.population}`);
            console.log(`  - Districts: ${state.districts}`);
            console.log(`  - Budget: ${state.budget}`);
            console.log(`  - Time: ${state.time}`);
        } catch (e) {
            console.log("\nRaw response:", result.Messages[0].Data);
        }
    }

    console.log("\n✓ Query complete");
}

queryWorld().catch(console.error);
