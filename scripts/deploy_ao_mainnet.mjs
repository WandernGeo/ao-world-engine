#!/usr/bin/env node
/**
 * AO World Engine - Mainnet Deployment Script
 * 
 * Spawns the world process on AO MAINNET using aoconnect.
 * Then loads Lua modules and initializes the world simulation.
 * 
 * CRON is configured to auto-tick every 10 minutes FOR FREE.
 * 
 * Usage: 
 *   WALLET_PATH=/path/to/wallet.json node scripts/deploy_ao_mainnet.mjs
 *   
 * Or with defaults:
 *   node scripts/deploy_ao_mainnet.mjs
 */

import { connect, createDataItemSigner } from "@permaweb/aoconnect";
import Arweave from "arweave";
import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));

// =============================================================================
// CONFIG
// =============================================================================

const WALLET_PATH = process.env.WALLET_PATH || "/Users/ram/arweave-wallet.json";
const AO_PROCESSES_DIR = path.join(__dirname, "../ao-processes");

// AO Mainnet IDs
// Module: AOS 2.0 Lua runtime module for mainnet
const AO_MODULE = process.env.AO_MODULE || "Do_Uc2Sju_XF1_x756ixkQCbj97gOgEhRE-GMfimSew";
// Scheduler: AO mainnet default scheduler
const AO_SCHEDULER = process.env.AO_SCHEDULER || "n_XZJhUnmldNFo4dhajoPZWhBXuJk-OcQr5JQ49c4Zo";

const arweave = Arweave.init({
    host: "arweave.net",
    port: 443,
    protocol: "https"
});

// =============================================================================
// DEPLOY
// =============================================================================

async function deployToMainnet() {
    console.log("╔══════════════════════════════════════════╗");
    console.log("║  AO World Engine — MAINNET Deployment    ║");
    console.log("╚══════════════════════════════════════════╝\n");

    // 1. Load and verify wallet
    console.log(`Loading wallet from: ${WALLET_PATH}`);
    if (!fs.existsSync(WALLET_PATH)) {
        console.error(`❌ Wallet not found at ${WALLET_PATH}`);
        console.error("Set WALLET_PATH env var or place wallet at the default path");
        process.exit(1);
    }

    const wallet = JSON.parse(fs.readFileSync(WALLET_PATH, "utf-8"));
    const address = await arweave.wallets.jwkToAddress(wallet);
    const balance = await arweave.wallets.getBalance(address);
    const ar = arweave.ar.winstonToAr(balance);

    console.log(`✓ Wallet: ${address.slice(0, 12)}...`);
    console.log(`  Balance: ${ar} AR\n`);

    if (parseFloat(ar) < 0.001) {
        console.error("⚠️  Low balance! You need AR tokens to spawn a process.");
        console.error("   Get AR from: https://arweave.org or an exchange\n");
    }

    // 2. Load Lua source files
    console.log("Loading Lua modules...");

    const luaFiles = [
        "init_bootstrap.lua",
        "founding_npcs.lua",
        "world.lua"
    ];

    const luaSources = {};
    for (const file of luaFiles) {
        const filepath = path.join(AO_PROCESSES_DIR, file);
        if (!fs.existsSync(filepath)) {
            console.error(`❌ Missing Lua file: ${filepath}`);
            process.exit(1);
        }
        luaSources[file] = fs.readFileSync(filepath, "utf-8");
        console.log(`  ✓ ${file}: ${luaSources[file].length} bytes`);
    }
    console.log("");

    // 3. Connect to AO MAINNET
    console.log("Connecting to AO mainnet...");
    const signer = createDataItemSigner(wallet);

    // Use legacy mode for compatibility with existing module
    const ao = connect({
        MODE: "legacy",
        CU_URL: "https://cu.ao-testnet.xyz",
        MU_URL: "https://mu.ao-testnet.xyz",
        GATEWAY_URL: "https://arweave.net",
    });

    // 4. Spawn world process with CRON
    console.log("Spawning world process...");
    console.log(`  Module: ${AO_MODULE}`);
    console.log(`  Scheduler: ${AO_SCHEDULER}`);
    console.log(`  CRON: every 10 minutes\n`);

    try {
        const processId = await ao.spawn({
            module: AO_MODULE,
            scheduler: AO_SCHEDULER,
            signer,
            tags: [
                { name: "App-Name", value: "AO-World-Engine" },
                { name: "App-Version", value: "2.0.0" },
                { name: "Cron-Interval", value: "10-minutes" },
                { name: "Cron-Tag-Action", value: "Cron" },
                { name: "Name", value: "AO-World-Engine" }
            ]
        });

        console.log(`✅ Process spawned on AO!`);
        console.log(`   Process ID: ${processId}`);
        console.log(`   View: https://ao.link/#/entity/${processId}\n`);

        // 5. Load Lua code into process
        console.log("Loading Lua code into process...\n");

        for (const file of luaFiles) {
            console.log(`  Loading ${file}...`);
            const msgId = await ao.message({
                process: processId,
                signer,
                tags: [{ name: "Action", value: "Eval" }],
                data: luaSources[file]
            });

            // Wait for result
            const res = await ao.result({
                process: processId,
                message: msgId
            });

            if (res.Error) {
                console.error(`  ❌ Error loading ${file}:`, res.Error);
            } else {
                console.log(`  ✓ ${file} loaded`);
                if (res.Output?.data) {
                    const output = typeof res.Output.data === 'string'
                        ? res.Output.data.slice(0, 200)
                        : JSON.stringify(res.Output.data).slice(0, 200);
                    console.log(`    Output: ${output}`);
                }
            }
        }

        // 6. Initialize world
        console.log("\nInitializing world simulation...");
        const initMsgId = await ao.message({
            process: processId,
            signer,
            tags: [{ name: "Action", value: "Eval" }],
            data: "return Initialize()"
        });

        const initResult = await ao.result({
            process: processId,
            message: initMsgId
        });

        console.log("✓ World initialized");
        if (initResult.Messages?.[0]?.Data) {
            try {
                const state = JSON.parse(initResult.Messages[0].Data);
                console.log(`  Tick: ${state.tick || state.world_tick || 0}`);
                console.log(`  Population: ${state.population || 0}`);
                console.log(`  Budget: ${state.budget || 0} GEP`);
            } catch {
                console.log(`  Response: ${initResult.Messages[0].Data.slice(0, 300)}`);
            }
        }
        if (initResult.Output?.data) {
            console.log(`  Output: ${typeof initResult.Output.data === 'string' ? initResult.Output.data.slice(0, 300) : JSON.stringify(initResult.Output.data).slice(0, 300)}`);
        }

        // 7. Verify state
        console.log("\nVerifying state...");
        const stateMsgId = await ao.message({
            process: processId,
            signer,
            tags: [{ name: "Action", value: "get-state" }],
            data: "{}"
        });

        const stateResult = await ao.result({
            process: processId,
            message: stateMsgId
        });

        if (stateResult.Messages?.[0]?.Data) {
            try {
                const state = JSON.parse(stateResult.Messages[0].Data);
                console.log("╔══════════════════════════════════════════╗");
                console.log("║  VERIFIED WORLD STATE                    ║");
                console.log("╠══════════════════════════════════════════╣");
                console.log(`║  World Tick:  ${String(state.tick || 0).padEnd(26)}║`);
                console.log(`║  World Day:   ${String(state.day || 0).padEnd(26)}║`);
                console.log(`║  Population:  ${String(state.population || 0).padEnd(26)}║`);
                console.log(`║  Budget:      ${String((state.budget || 0) + ' GEP').padEnd(26)}║`);
                console.log("╚══════════════════════════════════════════╝");
            } catch {
                console.log(`  Raw: ${stateResult.Messages[0].Data.slice(0, 300)}`);
            }
        }

        // 8. Save process ID
        const configPath = path.join(__dirname, "../ao-process-ids.json");
        const config = {
            world: processId,
            deployedAt: new Date().toISOString(),
            walletAddress: address,
            network: "mainnet"
        };
        fs.writeFileSync(configPath, JSON.stringify(config, null, 2));
        console.log(`\n📁 Process ID saved to: ao-process-ids.json`);

        // Output the important values for frontend update
        console.log("\n" + "═".repeat(50));
        console.log("NEXT STEPS:");
        console.log("═".repeat(50));
        console.log(`\n1. Update ao-client.ts with new process ID:`);
        console.log(`   world: "${processId}"`);
        console.log(`\n2. Deploy frontend:`);
        console.log(`   cd ao-world-engine-studio && gcloud builds submit`);
        console.log(`\n3. Verify CRON ticks (wait 10 min, then):`);
        console.log(`   node scripts/verify_ao_state.mjs`);

        return processId;

    } catch (error) {
        console.error("\n❌ Deployment failed:", error.message);
        if (error.message.includes("402")) {
            console.error("\n   This likely means insufficient AR balance.");
            console.error("   You need AR tokens to spawn a process on Arweave.");
        }
        if (error.stack) {
            console.error("\nStack:", error.stack);
        }
        throw error;
    }
}

deployToMainnet().catch(console.error);
