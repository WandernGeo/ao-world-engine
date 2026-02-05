#!/usr/bin/env node
/**
 * AO World Engine - Send Signed Message
 * 
 * Sends a SIGNED message to the AO process to persist state changes.
 * 
 * Usage: node scripts/send_ao_message.mjs
 */

import { message, result, createDataItemSigner } from '@permaweb/aoconnect';
import { readFileSync } from 'fs';

const PROCESS_ID = '3KJMDJ81ob8qHUB8Fc-fn9n4pmSBqIh2S1DOM1zkqt0';
const WALLET_PATH = '/Users/ram/Documents/wandern/wandern-back/arweave-wallet.json';

async function sendMessage(action, data) {
    console.log(`🌍 AO World Engine - Send Message\n`);
    console.log(`Process: ${PROCESS_ID}`);
    console.log(`Action:  ${action}`);
    console.log(`Data:    ${JSON.stringify(data)}\n`);

    try {
        // Load wallet
        const wallet = JSON.parse(readFileSync(WALLET_PATH, 'utf8'));
        const signer = createDataItemSigner(wallet);

        console.log('📤 Sending signed message...\n');

        // Send the message
        const msgId = await message({
            process: PROCESS_ID,
            signer,
            tags: [
                { name: 'Action', value: action }
            ],
            data: JSON.stringify(data)
        });

        console.log(`✅ Message sent!`);
        console.log(`   Message ID: ${msgId}\n`);

        // Wait for result
        console.log('⏳ Waiting for result...\n');

        const res = await result({
            message: msgId,
            process: PROCESS_ID
        });

        if (res.Messages && res.Messages.length > 0) {
            console.log('📨 Response received:');
            for (const msg of res.Messages) {
                if (msg.Data) {
                    try {
                        const parsed = JSON.parse(msg.Data);
                        console.log(JSON.stringify(parsed, null, 2));
                    } catch {
                        console.log(msg.Data);
                    }
                }
            }
        }

        if (res.Output && res.Output.data) {
            console.log('\n📋 Output:', res.Output.data);
        }

        return msgId;

    } catch (error) {
        console.error('❌ Error:', error.message);
        if (error.stack) {
            console.error(error.stack);
        }
        return null;
    }
}

// Main execution
const action = process.argv[2] || 'Init';
const dataArg = process.argv[3] || '{"population": 800}';

let data;
try {
    data = JSON.parse(dataArg);
} catch {
    data = { population: 800 };
}

sendMessage(action, data).then(async (msgId) => {
    if (msgId) {
        console.log('\n--- Verifying State ---\n');

        // Get state to verify
        const wallet = JSON.parse(readFileSync(WALLET_PATH, 'utf8'));
        const signer = createDataItemSigner(wallet);

        const stateId = await message({
            process: PROCESS_ID,
            signer,
            tags: [{ name: 'Action', value: 'get-state' }],
            data: '{}'
        });

        const stateRes = await result({
            message: stateId,
            process: PROCESS_ID
        });

        if (stateRes.Messages && stateRes.Messages.length > 0) {
            const stateData = JSON.parse(stateRes.Messages[0].Data);
            console.log('═══════════════════════════════════════');
            console.log('📊 VERIFIED WORLD STATE');
            console.log('═══════════════════════════════════════');
            console.log(`  World Tick:     ${stateData.tick}`);
            console.log(`  World Day:      ${stateData.day}`);
            console.log(`  Population:     ${stateData.population}`);
            console.log(`  City Budget:    ${stateData.budget} GEP`);
            console.log('═══════════════════════════════════════\n');
        }
    }
});
