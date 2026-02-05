#!/usr/bin/env node
/**
 * AO World Engine - State Verification Script
 * 
 * Queries the AO process to check if it's running autonomously.
 * 
 * Usage: node scripts/verify_ao_state.mjs
 */

import { connect, createDataItemSigner } from '@permaweb/aoconnect';
import fs from 'fs';
import path from 'path';

const PROCESS_ID = '3KJMDJ81ob8qHUB8Fc-fn9n4pmSBqIh2S1DOM1zkqt0';
const GATEWAY = 'https://cu.ao-testnet.xyz';

async function queryState() {
    console.log('🌍 AO World Engine - State Verification\n');
    console.log(`Process ID: ${PROCESS_ID}`);
    console.log(`Gateway: ${GATEWAY}\n`);

    try {
        // Use dry-run to query state (no wallet needed)
        const response = await fetch(`${GATEWAY}/dry-run?process-id=${PROCESS_ID}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                Id: '0000000000000000000000000000000000000000001',
                Target: PROCESS_ID,
                Owner: '0000000000000000000000000000000000000000001',
                Tags: [
                    { name: 'Action', value: 'get-state' },
                    { name: 'Data-Protocol', value: 'ao' },
                    { name: 'Type', value: 'Message' },
                    { name: 'Variant', value: 'ao.TN.1' }
                ],
                Data: '{}'
            })
        });

        if (!response.ok) {
            console.error(`❌ Gateway error: ${response.status} ${response.statusText}`);
            return null;
        }

        const result = await response.json();

        // Parse response
        if (result.Messages && result.Messages.length > 0) {
            const msg = result.Messages[0];
            const data = msg.Data ? JSON.parse(msg.Data) : {};

            console.log('✅ Process Response Received\n');
            console.log('═══════════════════════════════════════');
            console.log('📊 WORLD STATE');
            console.log('═══════════════════════════════════════');
            console.log(`  World Tick:     ${data.tick || data.WorldTick || 'N/A'}`);
            console.log(`  World Day:      ${data.day || data.WorldDay || 'N/A'}`);
            console.log(`  World Year:     ${data.year || data.WorldYear || 'N/A'}`);
            console.log(`  Status:         ${data.status || data.SimulationStatus || 'N/A'}`);
            console.log(`  Population:     ${data.population || data.PopulationCount || 'N/A'}`);
            console.log(`  Active NPCs:    ${data.active_npcs || data.ActiveNpcCount || 'N/A'}`);
            console.log(`  City Budget:    ${data.budget || data.CityBudget || 'N/A'} GEP`);
            console.log('═══════════════════════════════════════\n');

            // Check if CRON is working (tick should be > 0 if running)
            const tick = data.tick || data.WorldTick || 0;
            if (tick > 0) {
                console.log('🟢 CRON appears to be ACTIVE - WorldTick is advancing\n');
            } else {
                console.log('🟡 WorldTick is 0 - CRON may not be configured\n');
                console.log('To enable CRON, respawn with:');
                console.log('  Cron-Interval: "10-minutes"');
                console.log('  Cron-Tag-Action: "Cron"\n');
            }

            return data;
        } else {
            console.log('⚠️ No Messages in response. Process may not have handlers loaded.\n');
            console.log('Raw output:', JSON.stringify(result.Output || {}, null, 2));
            return null;
        }
    } catch (error) {
        console.error('❌ Error querying AO:', error.message);
        return null;
    }
}

// Run verification
queryState().then((state) => {
    if (state) {
        console.log('✅ Verification complete');
    } else {
        console.log('❌ Could not verify state - check process deployment');
    }
});
