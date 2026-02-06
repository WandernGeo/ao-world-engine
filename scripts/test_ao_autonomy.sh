#!/bin/bash
# AO Autonomy Verification Test
# Run this to verify the simulation is advancing automatically

PROCESS_ID="3KJMDJ81ob8qHUB8Fc-fn9n4pmSBqIh2S1DOM1zkqt0"
OUTPUT_FILE="test_results_$(date '+%Y%m%d_%H%M%S').log"

echo "AO Autonomy Verification Test" | tee $OUTPUT_FILE
echo "==============================" | tee -a $OUTPUT_FILE
echo "Process ID: $PROCESS_ID" | tee -a $OUTPUT_FILE
echo "Started: $(date '+%Y-%m-%d %H:%M:%S')" | tee -a $OUTPUT_FILE
echo "" | tee -a $OUTPUT_FILE

# Baseline
echo "=== Test 1 (Baseline): $(date '+%H:%M:%S') ===" | tee -a $OUTPUT_FILE
TICK1=$(node scripts/send_ao_message.mjs get-state '{}' 2>&1 | grep "World Tick" | awk '{print $3}')
echo "WorldTick: $TICK1" | tee -a $OUTPUT_FILE
echo "" | tee -a $OUTPUT_FILE

echo "Waiting 10 minutes for CRON..."
sleep 600

# After 10 min
echo "=== Test 2 (+10 min): $(date '+%H:%M:%S') ===" | tee -a $OUTPUT_FILE
TICK2=$(node scripts/send_ao_message.mjs get-state '{}' 2>&1 | grep "World Tick" | awk '{print $3}')
echo "WorldTick: $TICK2" | tee -a $OUTPUT_FILE

if [ "$TICK2" -gt "$TICK1" ]; then
    echo "✅ PASSED: Tick advanced from $TICK1 to $TICK2" | tee -a $OUTPUT_FILE
else
    echo "❌ FAILED: Tick did not advance (was $TICK1, still $TICK2)" | tee -a $OUTPUT_FILE
fi
echo "" | tee -a $OUTPUT_FILE

echo "Waiting another 10 minutes..."
sleep 600

# After 20 min
echo "=== Test 3 (+20 min): $(date '+%H:%M:%S') ===" | tee -a $OUTPUT_FILE
TICK3=$(node scripts/send_ao_message.mjs get-state '{}' 2>&1 | grep "World Tick" | awk '{print $3}')
echo "WorldTick: $TICK3" | tee -a $OUTPUT_FILE

if [ "$TICK3" -gt "$TICK2" ]; then
    echo "✅ PASSED: Tick advanced from $TICK2 to $TICK3" | tee -a $OUTPUT_FILE
else
    echo "❌ FAILED: Tick did not advance" | tee -a $OUTPUT_FILE
fi

echo "" | tee -a $OUTPUT_FILE
echo "Test completed: $(date '+%Y-%m-%d %H:%M:%S')" | tee -a $OUTPUT_FILE
echo "Results saved to: $OUTPUT_FILE"
