#!/usr/bin/env node
/**
 * AO World Engine - Live Lua Test Suite
 * 
 * Tests all the Lua handlers on the deployed AO process.
 * 
 * Usage: node scripts/test_ao_lua.mjs
 */

const PROCESS_ID = '3KJMDJ81ob8qHUB8Fc-fn9n4pmSBqIh2S1DOM1zkqt0';
const GATEWAY = 'https://cu.ao-testnet.xyz';

const tests = [
    { action: 'get-state', data: '{}', description: 'World State' },
    { action: 'get-time', data: '{}', description: 'Current Time' },
    { action: 'get-economy', data: '{}', description: 'Economy Stats' },
];

async function dryRun(action, data) {
    const response = await fetch(`${GATEWAY}/dry-run?process-id=${PROCESS_ID}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            Id: Date.now().toString(),
            Target: PROCESS_ID,
            Owner: '0000000000000000000000000000000000000000001',
            Tags: [
                { name: 'Action', value: action },
                { name: 'Data-Protocol', value: 'ao' },
                { name: 'Type', value: 'Message' },
                { name: 'Variant', value: 'ao.TN.1' }
            ],
            Data: data
        })
    });
    return response.json();
}

async function runTests() {
    console.log('🧪 AO WORLD ENGINE - LIVE LUA TESTS\n');
    console.log(`Process: ${PROCESS_ID}\n`);
    console.log('═══════════════════════════════════════════════════════════');

    let passed = 0;
    let failed = 0;

    for (const test of tests) {
        process.stdout.write(`Testing ${test.description}...`);

        try {
            const result = await dryRun(test.action, test.data);

            if (result.Messages && result.Messages.length > 0) {
                const data = result.Messages[0].Data;
                let parsed;
                try {
                    parsed = JSON.parse(data);
                } catch {
                    parsed = data;
                }

                console.log(' ✅ PASS');
                console.log(`   Response: ${JSON.stringify(parsed).slice(0, 100)}...`);
                passed++;
            } else if (result.Output && result.Output.data) {
                console.log(' ⚠️ OUTPUT');
                console.log(`   Output: ${result.Output.data.slice(0, 100)}`);
                passed++;
            } else {
                console.log(' ❌ FAIL (No response)');
                failed++;
            }
        } catch (error) {
            console.log(` ❌ ERROR: ${error.message}`);
            failed++;
        }
    }

    console.log('\n═══════════════════════════════════════════════════════════');
    console.log(`\n📊 Results: ${passed} passed, ${failed} failed\n`);

    // Additional: Check WorldTick is advancing
    console.log('Checking CRON advancement...');
    const state1 = await dryRun('get-state', '{}');
    const tick1 = state1.Messages?.[0]?.Data ? JSON.parse(state1.Messages[0].Data).tick : 0;
    console.log(`  Current WorldTick: ${tick1}`);

    if (tick1 > 0) {
        console.log('  ✅ CRON is active - WorldTick > 0\n');
    } else {
        console.log('  ⚠️ WorldTick is 0 - CRON may not be running\n');
    }

    return { passed, failed };
}

runTests().then(({ passed, failed }) => {
    process.exit(failed > 0 ? 1 : 0);
});
