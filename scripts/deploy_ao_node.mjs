/**
 * AO World Engine - Node.js Deployment Script
 * 
 * Spawns the world process on AO testnet using aoconnect.
 * Uses proper ArweaveSigner for wallet authentication.
 */

import { connect, createDataItemSigner } from "@permaweb/aoconnect";
import Arweave from "arweave";
import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));

// Config
const WALLET_PATH = process.env.WALLET_PATH ||
    path.join(__dirname, "../wallet.json");  // Use local wallet.json
const AO_PROCESSES_DIR = path.join(__dirname, "../ao-processes");

// Initialize Arweave
const arweave = Arweave.init({
    host: "arweave.net",
    port: 443,
    protocol: "https"
});

async function deployWorldProcess() {
    console.log("========================================");
    console.log("  AO World Engine - Deployment");
    console.log("========================================\n");

    // Load wallet
    console.log(`Loading wallet from: ${WALLET_PATH}`);
    const wallet = JSON.parse(fs.readFileSync(WALLET_PATH, "utf-8"));

    // Get wallet address for verification
    const address = await arweave.wallets.jwkToAddress(wallet);
    console.log(`✓ Wallet loaded: ${address.slice(0, 12)}...`);

    // Check balance
    const balance = await arweave.wallets.getBalance(address);
    const ar = arweave.ar.winstonToAr(balance);
    console.log(`  Balance: ${ar} AR\n`);

    // Create signer
    const signer = createDataItemSigner(wallet);

    // Load Lua source
    console.log("Loading Lua modules...");
    const worldLua = fs.readFileSync(path.join(AO_PROCESSES_DIR, "world.lua"), "utf-8");
    const foundingNpcsLua = fs.readFileSync(path.join(AO_PROCESSES_DIR, "founding_npcs.lua"), "utf-8");
    const initBootstrapLua = fs.readFileSync(path.join(AO_PROCESSES_DIR, "init_bootstrap.lua"), "utf-8");
    console.log(`  - world.lua: ${worldLua.length} bytes`);
    console.log(`  - founding_npcs.lua: ${foundingNpcsLua.length} bytes`);
    console.log(`  - init_bootstrap.lua: ${initBootstrapLua.length} bytes`);
    console.log("✓ Lua modules loaded\n");

    // Connect to AO with explicit gateway URLs (bypass CDN issues)
    const ao = connect({
        MU_URL: "https://mu.ao-testnet.xyz",
        CU_URL: "https://cu.ao-testnet.xyz",
        GATEWAY_URL: "https://arweave.net",
    });

    // Spawn world process with CRON
    console.log("Spawning world process on AO...");
    try {
        const processId = await ao.spawn({
            module: "cNlipBptaF9JeFAf4wUmpi43EojNanIBos3EfNrEOWo", // AO Lua module
            scheduler: "_GQ33BkPtZrqxA84vM8Zk-N2aO0toNNu_C-l-rawrBA",
            signer,
            tags: [
                { name: "App-Name", value: "AO-World-Engine" },
                { name: "App-Version", value: "1.0.0" },
                { name: "Cron-Interval", value: "1-minute" },
                { name: "Cron-Tag-Action", value: "Cron" }
            ]
        });

        console.log(`✓ Process spawned: ${processId}\n`);

        // Load Lua code into the process
        console.log("Loading Lua code into process...\n");

        // Load init_bootstrap.lua
        console.log("  Loading init_bootstrap.lua...");
        await ao.message({
            process: processId,
            signer,
            tags: [{ name: "Action", value: "Eval" }],
            data: initBootstrapLua
        });
        console.log("  ✓ init_bootstrap loaded");

        // Load founding_npcs.lua
        console.log("  Loading founding_npcs.lua...");
        await ao.message({
            process: processId,
            signer,
            tags: [{ name: "Action", value: "Eval" }],
            data: foundingNpcsLua
        });
        console.log("  ✓ founding_npcs loaded");

        // Load world.lua
        console.log("  Loading world.lua...");
        await ao.message({
            process: processId,
            signer,
            tags: [{ name: "Action", value: "Eval" }],
            data: worldLua
        });
        console.log("  ✓ world.lua loaded");

        // Initialize
        console.log("\nInitializing world simulation...");
        const initMsgId = await ao.message({
            process: processId,
            signer,
            tags: [{ name: "Action", value: "Eval" }],
            data: "return Initialize()"
        });

        // Get result
        const initResult = await ao.result({
            process: processId,
            message: initMsgId
        });

        console.log("✓ World initialized");
        if (initResult.Messages?.[0]?.Data) {
            console.log("  Response:", initResult.Messages[0].Data.slice(0, 300));
        }

        console.log("\n========================================");
        console.log("  Deployment Complete!");
        console.log("========================================");
        console.log(`Process ID: ${processId}`);
        console.log(`\nView on: https://ao.link/#/entity/${processId}`);

        // Save process ID
        const configPath = path.join(__dirname, "../ao-process-ids.json");
        const config = fs.existsSync(configPath) ? JSON.parse(fs.readFileSync(configPath)) : {};
        config.world = processId;
        config.deployedAt = new Date().toISOString();
        config.walletAddress = address;
        fs.writeFileSync(configPath, JSON.stringify(config, null, 2));
        console.log(`\nProcess ID saved to: ao-process-ids.json`);

        return processId;
    } catch (error) {
        console.error("\n❌ Deployment failed:", error.message);
        console.error("\nStack:", error.stack);
        throw error;
    }
}

deployWorldProcess().catch(console.error);
