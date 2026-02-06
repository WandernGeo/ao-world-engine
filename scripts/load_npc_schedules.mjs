#!/usr/bin/env node
/**
 * AO World Engine - Load NPC Schedules
 * 
 * Extracts NPC location data from codec files and loads into the AO process.
 * This populates NPCSchedules global so NPC movement behaviors work.
 * 
 * Usage: node scripts/load_npc_schedules.mjs [--dry-run]
 * 
 * Data sources:
 *   - data/codec_chunks/world_codec_01_npcs_expanded.json (founding NPCs)
 *   - data/founding_npcs/*.json (individual NPC files)
 */

import { message, result, createDataItemSigner } from '@permaweb/aoconnect';
import { readFileSync, readdirSync, existsSync } from 'fs';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const PROJECT_ROOT = join(__dirname, '..');

const PROCESS_ID = '3KJMDJ81ob8qHUB8Fc-fn9n4pmSBqIh2S1DOM1zkqt0';
const WALLET_PATH = '/Users/ram/Documents/wandern/wandern-back/arweave-wallet.json';

// Paths to codec data
const CODEC_PATH = join(PROJECT_ROOT, 'data/codec_chunks/world_codec_01_npcs_expanded.json');
const FOUNDING_DIR = join(PROJECT_ROOT, 'data/founding_npcs');

/**
 * Extract NPC schedule data from codec format
 */
function extractScheduleFromNPC(npc, npcId) {
    return {
        id: npcId || npc.code || npc.id,
        location_home: npc.location_home || npc.home || 'L001',
        location_work: npc.location_work || npc.work || npc.workplace || npc.location_home || 'L001',
        location_frequent: npc.location_frequent || [],
        archetype: npc.archetype || npc.role || '',
        role: npc.role || npc.archetype || '',
        shift: npc.shift || null  // Let AO auto-derive from archetype
    };
}

/**
 * Load founding NPCs from codec file
 */
function loadFromCodec() {
    const schedules = [];

    if (existsSync(CODEC_PATH)) {
        console.log(`📖 Reading codec: ${CODEC_PATH}`);
        const codec = JSON.parse(readFileSync(CODEC_PATH, 'utf8'));

        if (codec.founding_npcs) {
            for (const [npcId, npc] of Object.entries(codec.founding_npcs)) {
                const schedule = extractScheduleFromNPC(npc, npc.code || npcId);
                schedules.push(schedule);
                console.log(`   ✓ ${npc.name || npcId}: ${schedule.location_home} → ${schedule.location_work} (${schedule.archetype})`);
            }
        }
    }

    return schedules;
}

/**
 * Load founding NPCs from individual JSON files
 */
function loadFromFoundingDir() {
    const schedules = [];

    if (existsSync(FOUNDING_DIR)) {
        console.log(`\n📂 Reading founding NPCs: ${FOUNDING_DIR}`);
        const files = readdirSync(FOUNDING_DIR).filter(f => f.endsWith('.json'));

        for (const file of files) {
            try {
                const npc = JSON.parse(readFileSync(join(FOUNDING_DIR, file), 'utf8'));
                const schedule = extractScheduleFromNPC(npc, npc.code);

                // Only add if not already in list
                if (!schedules.find(s => s.id === schedule.id)) {
                    schedules.push(schedule);
                    console.log(`   ✓ ${npc.name || file}: ${schedule.location_home} → ${schedule.location_work} (${schedule.archetype || 'unknown'})`);
                }
            } catch (e) {
                console.log(`   ⚠ Failed to parse ${file}: ${e.message}`);
            }
        }
    }

    return schedules;
}

/**
 * Send schedules to AO process
 */
async function loadSchedulesToAO(schedules) {
    console.log(`\n📤 Loading ${schedules.length} schedules to AO...`);

    try {
        const wallet = JSON.parse(readFileSync(WALLET_PATH, 'utf8'));
        const signer = createDataItemSigner(wallet);

        const msgId = await message({
            process: PROCESS_ID,
            signer,
            tags: [{ name: 'Action', value: 'load-npc-schedules' }],
            data: JSON.stringify({ schedules })
        });

        console.log(`   Message ID: ${msgId}`);

        // Wait for result
        const res = await result({
            message: msgId,
            process: PROCESS_ID
        });

        if (res.Messages && res.Messages.length > 0) {
            const response = JSON.parse(res.Messages[0].Data);
            console.log(`\n✅ Success!`);
            console.log(`   Loaded:    ${response.loaded} schedules`);
            console.log(`   Total:     ${response.total_scheduled} NPCs with schedules`);
            return response;
        }

        return null;
    } catch (error) {
        console.error(`\n❌ Error: ${error.message}`);
        return null;
    }
}

/**
 * Verify schedules were loaded
 */
async function verifySchedules() {
    console.log(`\n🔍 Verifying loaded schedules...`);

    try {
        const wallet = JSON.parse(readFileSync(WALLET_PATH, 'utf8'));
        const signer = createDataItemSigner(wallet);

        const msgId = await message({
            process: PROCESS_ID,
            signer,
            tags: [{ name: 'Action', value: 'get-npc-locations' }],
            data: '{}'
        });

        const res = await result({
            message: msgId,
            process: PROCESS_ID
        });

        if (res.Messages && res.Messages.length > 0) {
            const response = JSON.parse(res.Messages[0].Data);
            console.log(`   NPCs with locations: ${response.count}`);
            console.log(`   Current tick: ${response.tick}`);

            // Show first few
            const locations = Object.entries(response.locations || {}).slice(0, 5);
            for (const [npcId, loc] of locations) {
                console.log(`   - ${npcId}: ${loc.location} (${loc.state})`);
            }

            if (response.count > 5) {
                console.log(`   ... and ${response.count - 5} more`);
            }
        }
    } catch (error) {
        console.error(`   ⚠ Verification failed: ${error.message}`);
    }
}

// Main execution
async function main() {
    const isDryRun = process.argv.includes('--dry-run');

    console.log('═══════════════════════════════════════════════════════');
    console.log('  AO World Engine - NPC Schedule Loader');
    console.log('═══════════════════════════════════════════════════════\n');

    if (isDryRun) {
        console.log('🔸 DRY RUN MODE - No changes will be made\n');
    }

    // Collect schedules from all sources
    const codecSchedules = loadFromCodec();
    const foundingSchedules = loadFromFoundingDir();

    // Merge (dedup by id)
    const allSchedules = [...codecSchedules];
    for (const schedule of foundingSchedules) {
        if (!allSchedules.find(s => s.id === schedule.id)) {
            allSchedules.push(schedule);
        }
    }

    console.log(`\n📊 Total unique schedules: ${allSchedules.length}`);

    if (isDryRun) {
        console.log('\n🔸 Dry run complete. Add --live to load to AO.');
        return;
    }

    // Load to AO
    const response = await loadSchedulesToAO(allSchedules);

    if (response) {
        await verifySchedules();
    }

    console.log('\n═══════════════════════════════════════════════════════');
    console.log('  Complete!');
    console.log('═══════════════════════════════════════════════════════\n');
}

main().catch(console.error);
