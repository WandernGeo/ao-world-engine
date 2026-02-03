# Arweave Transaction Log

> Permanent record of all RE:ECHO City data uploaded to Arweave

## Summary

| Metric | Value |
|--------|-------|
| Total NPCs | 12 |
| Total Bytes | 18,815 |
| Uploader | arweave-uploader-zdku5kri5a-uc.a.run.app |
| All Success | ✅ |

---

## NPC Profiles (Uploaded 2026-02-02)

| NPC | ID | TX ID | Size | Arweave URL |
|-----|----|----|------|-------------|
| Charlie | npc_0001 | `splQGmMK8Din4l3apKcIbyX3R_OEqG4L3WlRhzan9X4` | 2,250 | [View](https://arweave.net/splQGmMK8Din4l3apKcIbyX3R_OEqG4L3WlRhzan9X4) |
| Kai Vance | npc_0002 | `Y4OkevLSSgLGhOT7QFKFNsT59rW8_m_rLBdiSCA-tJ4` | 1,488 | [View](https://arweave.net/Y4OkevLSSgLGhOT7QFKFNsT59rW8_m_rLBdiSCA-tJ4) |
| Orion Thane | npc_0003 | `PIYlaUAKk44yCvX2cNTU8rowB2wfcQSqGY_EkvJmXfk` | 1,514 | [View](https://arweave.net/PIYlaUAKk44yCvX2cNTU8rowB2wfcQSqGY_EkvJmXfk) |
| Felix | npc_0004 | `BVyyBUHRX-_L0fCR9uLrrzIdC3RxMoyhHCPBq2kicjI` | 1,529 | [View](https://arweave.net/BVyyBUHRX-_L0fCR9uLrrzIdC3RxMoyhHCPBq2kicjI) |
| Nova Chen | npc_0005 | `xgHlkq0PtCOBhx5SKNsLHAY-kfpFLThSbxXJEA5HFl0` | 1,478 | [View](https://arweave.net/xgHlkq0PtCOBhx5SKNsLHAY-kfpFLThSbxXJEA5HFl0) |
| Selene Voss | npc_0006 | `Ad-A1Ww3wN79ZFYLexzmucl7N3tTvRKR1h58ca-omFI` | 1,510 | [View](https://arweave.net/Ad-A1Ww3wN79ZFYLexzmucl7N3tTvRKR1h58ca-omFI) |
| Sister Mira | npc_0007 | `rAFAlFK6Zp9nyiL1Ebj1iHEbAe8cMWtgp2DPxyf4Opo` | 1,473 | [View](https://arweave.net/rAFAlFK6Zp9nyiL1Ebj1iHEbAe8cMWtgp2DPxyf4Opo) |
| Mama Indira | npc_0008 | `ojQnWrkCax2TyY-gBvned-0ibF-40P3yI0wl32QJU_A` | 1,464 | [View](https://arweave.net/ojQnWrkCax2TyY-gBvned-0ibF-40P3yI0wl32QJU_A) |
| Aiche | npc_0009 | `5traiA6R0JU0cFQXJcqqkNm64o7hcYLsW_7rugnwxvo` | 1,512 | [View](https://arweave.net/5traiA6R0JU0cFQXJcqqkNm64o7hcYLsW_7rugnwxvo) |
| Pixel | npc_0010 | `-GVQ7zmPfs3C1B1HblfupvzHMgvoVVyiXNvq0hwCkmY` | 1,433 | [View](https://arweave.net/-GVQ7zmPfs3C1B1HblfupvzHMgvoVVyiXNvq0hwCkmY) |
| Cipher | npc_0011 | `Hi61YpGfVNatwCVkv2yJB54sDEX1pX8iT9mD5k8Zyms` | 1,563 | [View](https://arweave.net/Hi61YpGfVNatwCVkv2yJB54sDEX1pX8iT9mD5k8Zyms) |
| Zero Chen | npc_0012 | `RT2GXhdYw1h5E1WC7PSN11ORfFF0nIiED5K6mF_fnQY` | 1,601 | [View](https://arweave.net/RT2GXhdYw1h5E1WC7PSN11ORfFF0nIiED5K6mF_fnQY) |

---

## GraphQL Queries

Query all RE:ECHO NPCs:
```graphql
{
  transactions(
    tags: [
      { name: "App-Name", values: ["AO-World-Engine"] }
      { name: "Type", values: ["npc_profile"] }
    ]
  ) {
    edges {
      node {
        id
        tags { name value }
      }
    }
  }
}
```

Query at: https://arweave.net/graphql

---

## Pending Uploads

- [ ] World Codec manifest
- [ ] Location data
- [ ] Event chunks
- [ ] Updated NPC profiles with visual_description field

---

## Wallet Info

- **Address**: `1sq5dtoU38758TrCw-67-_LHbdBI3thFaZX97I0Rvb8`
- **Keyfile**: `wandern-back/arweave-wallet.json`
