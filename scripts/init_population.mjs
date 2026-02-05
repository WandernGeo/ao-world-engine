#!/usr/bin/env node
/**
 * AO World Engine - Initialize NPCs
 * 
 * Sends Init message to set population count.
 * 
 * Usage: node scripts/init_population.mjs [count]
 */

import { writeFileSync, readFileSync } from 'fs';

const PROCESS_ID = '3KJMDJ81ob8qHUB8Fc-fn9n4pmSBqIh2S1DOM1zkqt0';
const GATEWAY = 'https://cu.ao-testnet.xyz';
const POPULATION = process.argv[2] || 800;

async function initPopulation() {
    console.log('🌍 AO World Engine - Initialize Population\n');
    console.log(`Process ID: ${PROCESS_ID}`);
    console.log(`Population: ${POPULATION}`);
    console.log(`Gateway: ${GATEWAY}\n`);

    try {
        // Send Init message via dry-run (for testing)
        console.log('Sending Init message...\n');

        const response = await fetch(`${GATEWAY}/dry-run?process-id=${PROCESS_ID}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                Id: '0000000000000000000000000000000000000000001',
                Target: PROCESS_ID,
                Owner: '0000000000000000000000000000000000000000001',
                Tags: [
                    { name: 'Action', value: 'Init' },
                    { name: 'Data-Protocol', value: 'ao' },
                    { name: 'Type', value: 'Message' },
                    { name: 'Variant', value: 'ao.TN.1' }
                ],
                Data: JSON.stringify({ population: parseInt(POPULATION) })
            })
        });

        if (!response.ok) {
            console.error(`❌ Gateway error: ${response.status}`);
            return;
        }

        const result = await response.json();

        if (result.Messages && result.Messages.length > 0) {
            console.log('✅ Init message processed!');
            const data = result.Messages[0].Data;
            if (data) {
                try {
                    const parsed = JSON.parse(data);
                    console.log('\nResponse:', JSON.stringify(parsed, null, 2));
                } catch (e) {
                    console.log('\nResponse:', data);
                }
            }
        } else {
            console.log('⚠️ No response messages');
            if (result.Output) {
                console.log('Output:', result.Output.data || result.Output);
            }
        }

        // Now verify state
        console.log('\n--- Verifying State ---\n');

        const stateResponse = await fetch(`${GATEWAY}/dry-run?process-id=${PROCESS_ID}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                Id: '0000000000000000000000000000000000000000002',
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

        const stateResult = await stateResponse.json();

        if (stateResult.Messages && stateResult.Messages.length > 0) {
            const stateData = JSON.parse(stateResult.Messages[0].Data);
            console.log('═══════════════════════════════════════');
            console.log('📊 UPDATED WORLD STATE');
            console.log('═══════════════════════════════════════');
            console.log(`  World Tick:     ${stateData.tick}`);
            console.log(`  World Day:      ${stateData.day}`);
            console.log(`  Population:     ${stateData.population}`);
            console.log(`  City Budget:    ${stateData.budget} GEP`);
            console.log('═══════════════════════════════════════\n');
        }

    } catch (error) {
        console.error('❌ Error:', error.message);
    }
}

initPopulation();
