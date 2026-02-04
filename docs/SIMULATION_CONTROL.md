# 🛑 Simulation Control (Kill Switch)

The AO World Engine includes simulation control handlers that let you pause, freeze, or terminate your simulation.

## What Does "Terminate" Mean?

**Termination does NOT delete anything.** When you terminate a simulation:

| ✅ What Happens | ❌ What Doesn't Happen |
|-----------------|------------------------|
| Time stops advancing | Data is NOT deleted |
| CRON ticks are skipped | History is NOT lost |
| World becomes "frozen" | You can still query any tick |

Think of it as **pressing pause forever** - the movie stops, but you can still rewind to any frame.

### You Can Still:
- Query any NPC's state at any historical tick
- Recreate scenes (e.g., "show me the bar at 6pm on day 45")
- Extract data for analysis
- Fork the world to a new process

### You Cannot:
- Advance time further
- Run autonomous NPC behaviors
- Generate new events

## Setting Up Your Kill Switch

### 1. Generate a Password Hash

```bash
python3 scripts/kill_switch.py --hash
# Or manually:
python3 -c "
password = 'your_secret_password'
h = 0
for c in password:
    h = (h * 31 + ord(c)) % 2147483647
print(f'Hash: {h}')
"
```

### 2. Update world.lua

Find the `terminate-simulation` handler and set your hash:

```lua
local secret_hash = YOUR_HASH_HERE  -- Your computed hash
```

### 3. Configure the Script

Edit `scripts/kill_switch.py`:

```python
PROCESS_ID = "your-ao-process-id"
PASSWORD = "your_secret_password"
```

### 4. Run When Needed

```bash
python3 scripts/kill_switch.py
# Type 'TERMINATE' to confirm
```

## Other Controls

```lua
-- Pause (can resume later)
Send({ Target = ao.id, Action = "pause-simulation" })

-- Resume from pause
Send({ Target = ao.id, Action = "resume-simulation" })

-- Freeze (permanent pause, but not terminated)
Send({ Target = ao.id, Action = "freeze-simulation" })

-- Check status
Send({ Target = ao.id, Action = "get-simulation-status" })
```

## Security

- Only the **password hash** is stored in code (safe to commit)
- Nobody can reverse the hash to get your password
- You control when and if to terminate
