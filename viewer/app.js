/**
 * AO World Engine Viewer - Open Source
 * Minimal viewer for AO world state
 */

// AO Process Configuration
const AO_PROCESS_ID = "nJe-5S9dpBxeA9BO7Q7FNP2jHpl6ETTN5hmyBdf-XxA";
const AO_GATEWAY = "https://cu.ao-testnet.xyz";

// Constants for time conversion
const TICKS_PER_HOUR = 10;
const HOURS_PER_DAY = 24;

// =============================================================================
// AO QUERIES
// =============================================================================

async function queryAO(action, data = {}) {
    try {
        const response = await fetch(`${AO_GATEWAY}/dry-run?process-id=${AO_PROCESS_ID}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                Id: '0000000000000000000000000000000000000000001',
                Target: AO_PROCESS_ID,
                Owner: '0000000000000000000000000000000000000000001',
                Tags: [
                    { name: 'Action', value: action },
                    { name: 'Data-Protocol', value: 'ao' },
                    { name: 'Type', value: 'Message' },
                    { name: 'Variant', value: 'ao.TN.1' }
                ],
                Data: JSON.stringify(data)
            })
        });

        if (!response.ok) return null;

        const result = await response.json();
        if (result.Messages && result.Messages.length > 0) {
            const msg = result.Messages[0];
            if (msg.Data) {
                try { return JSON.parse(msg.Data); }
                catch { return msg.Data; }
            }
        }
        return result;
    } catch (error) {
        console.error('AO query error:', error);
        return null;
    }
}

// =============================================================================
// TIME FORMATTING
// =============================================================================

function formatTickTime(tick) {
    const totalHours = Math.floor(tick / TICKS_PER_HOUR);
    const day = Math.floor(totalHours / HOURS_PER_DAY) + 1;
    const hour = totalHours % HOURS_PER_DAY;
    const minute = (tick % TICKS_PER_HOUR) * 6;
    return { day, hour, minute };
}

// =============================================================================
// UI UPDATES
// =============================================================================

function updateConnectionStatus(connected) {
    const el = document.getElementById('connection-status');
    if (connected) {
        el.textContent = '● Connected';
        el.className = 'online';
    } else {
        el.textContent = '● Offline';
        el.className = 'offline';
    }
}

function updateWorldState(state) {
    if (!state) return;

    const time = formatTickTime(state.world_tick || 0);

    document.getElementById('tick-display').textContent = `Tick: ${state.world_tick || 0}`;
    document.getElementById('population').textContent = (state.population || 0).toLocaleString();
    document.getElementById('budget').textContent = `◊${((state.budget || 0) / 1000).toFixed(0)}k`;
    document.getElementById('day').textContent = time.day;
    document.getElementById('time').textContent =
        `${time.hour.toString().padStart(2, '0')}:${time.minute.toString().padStart(2, '0')}`;
}

function renderNPCs(npcs) {
    const container = document.getElementById('npc-list');
    document.getElementById('npc-count').textContent = npcs.length;

    if (!npcs || npcs.length === 0) {
        container.innerHTML = '<p class="loading">No NPCs found</p>';
        return;
    }

    container.innerHTML = npcs.map(npc => `
        <div class="npc-card">
            <div class="name">${npc.name || npc.id}</div>
            <div class="info">
                ${npc.archetype || 'Unknown'} • ${npc.faction || 'None'}
            </div>
        </div>
    `).join('');
}

function renderDistricts(districts) {
    const container = document.getElementById('district-list');

    if (!districts || districts.length === 0) {
        container.innerHTML = '<p class="loading">No districts found</p>';
        return;
    }

    container.innerHTML = districts.map(d => `
        <div class="district-card">
            <div class="name">${d.name || d.id}</div>
            <div class="info">
                Pop: ${d.population || 0} • Danger: ${d.danger_level || 0}/10
            </div>
        </div>
    `).join('');
}

// =============================================================================
// INITIALIZATION
// =============================================================================

async function init() {
    console.log('AO World Engine Viewer starting...');
    document.getElementById('process-id').textContent = AO_PROCESS_ID.slice(0, 8) + '...';

    // Fetch world state
    const state = await queryAO('get-state');
    if (state) {
        updateConnectionStatus(true);
        updateWorldState(state);
    } else {
        updateConnectionStatus(false);
    }

    // Fetch NPCs
    const npcs = await queryAO('get-all-npcs');
    renderNPCs(Array.isArray(npcs) ? npcs : []);

    // Fetch districts
    const districts = await queryAO('get-districts');
    renderDistricts(Array.isArray(districts) ? districts : []);

    // Auto-refresh every 30 seconds
    setInterval(async () => {
        const state = await queryAO('get-state');
        if (state) {
            updateConnectionStatus(true);
            updateWorldState(state);
        }
    }, 30000);
}

// Start when DOM is ready
document.addEventListener('DOMContentLoaded', init);
