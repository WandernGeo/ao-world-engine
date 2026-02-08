# Deployment Next Steps — Full Pipeline

> Generated: 2026-02-08. Codecs 00-26 on Arweave. Open-source repo pushed. Studio + Arweave upload pending.

---

## Phase 1: Upload Codecs 27-35 to Arweave

9 new codec JSON files from CS2/DF/ONI research need uploading:

```
world_codec_27_city_finance.json
world_codec_28_city_services.json
world_codec_29_commuting.json
world_codec_30_dynamic_metrics.json
world_codec_31_crime_justice.json
world_codec_32_education.json
world_codec_33_pollution.json
world_codec_34_schedules_enhanced.json
world_codec_35_trade_diplomacy.json
```

**Command:**
```bash
cd ao-world-engine
python scripts/upload_codec_to_arweave.py        # live upload
python scripts/upload_codec_to_arweave.py --dry-run  # preview first
```

Updates `data/arweave_codec_manifest.json` with new TX IDs.

---

## Phase 2: Load Codecs into AO Process

Send `LoadCodec` messages to AO process `3KJMDJ81ob8qHUB8Fc-fn9n4pmSBqIh2S1DOM1zkqt0`:

- `codec_loader.lua` handles `Action = "LoadCodec"` with `Tags.CodecName` + `Data = JSON`
- All 9 refactored Lua modules auto-apply via `register_codec_callback`
- Ticks use new config immediately after loading

---

## Phase 3: Studio Repo — Consolidate + Push

### 3a. Consolidate `reecho-city-private` → `ao-world-engine-studio/docs/internal/`

| From (`reecho-city-private/`) | To (`studio/docs/internal/`) |
|------|-----|
| `LORE.md` | `lore.md` |
| `MONETIZATION_STRATEGY.md` | `monetization.md` |
| `GRANT_PITCH.md` | `grants.md` |
| `API_BUSINESS_MODEL.md` | `api_business_model.md` |
| `IP_ARCHITECTURE.md` | `ip_architecture.md` |
| `ADMIN_WORKSHOP.md` | `admin_workshop.md` |
| `KILLSWITCH.md` | `killswitch.md` |
| `kill_switch.py` | `kill_switch.py` |
| `starter_archetypes.json` | `starter_archetypes.json` |
| `engine-content/` | `engine_content/` |

### 3b. Commit + push studio pending changes

Modified: `chat/page.tsx`, `graph/page.tsx`, `monitor/page.tsx`, `GlobalTimeBar.tsx`, `ao-client.ts`
New: `KnowledgeGraph.tsx`

### 3c. Push to `WandernGeo/ao-world-engine-studio` (private)

---

## Phase 4: Deploy Both Services to Cloud Run

```bash
# Studio (frontend)
cd ao-world-engine-studio
gcloud builds submit --tag gcr.io/wandern-prod/ao-world-engine-studio

# API (backend)
cd ao-world-engine
gcloud builds submit --config cloudbuild-api.yaml
```

---

## Verification Checklist

- [ ] `https://ao-world-engine-1071951656531.us-central1.run.app/monitor` — new data loads
- [ ] GlobalTimeBar shows advancing ticks (AO live)
- [ ] Economy data reflects codecs 27-35 (city finance, services, etc.)
- [ ] `lua scripts/test_integration_systems.lua` — 72/72 pass
- [ ] No secrets in public repo, no engine code in private repo
