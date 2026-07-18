# Trust Desk — Building the Trust Layer for Indian Healthcare

**Hack-Nation Global AI Hackathon 2026 · Challenge #04 (Databricks × Virtue Foundation) · Track: Facility Trust Desk**

**Live app:** https://trust-desk-7474650580216748.aws.databricksapps.com

> **Reviewer access:** Databricks Apps require workspace authentication, so the link above prompts for a
> Databricks login. The demo video shows the complete workflow end-to-end; verified UI screenshots are in
> `assets/`. To try it live, send any email address to vahevahevahe@gmail.com and I'll add you to the
> workspace within minutes — or run `tools/smoke` against your own deployment using the run instructions below.

An NGO planner deciding where to send an ICU program has 10,088 scraped facility records. "Has ICU" might be marketing. Coordinates might be in the ocean. Trust Desk answers the track question — *can this facility do what it claims?* — with cited evidence, honest uncertainty, and persistent human judgment.

## The finding that drives the product

**~half of all high-acuity capability claims have zero independent corroboration** anywhere in their own record (ICU 51%, NICU 50%, oncology 49%, emergency 48%, maternity 45%). A claim is not a capability — so every facility gets a transparent 0–100 evidence score, and every point traces to quoted text.

## What the app does

| Step | Feature | Where it lives |
|---|---|---|
| Rank | Trust-scored facilities per capability + state; score = corroboration 40 + completeness 20 + web presence 25 + geo validity 15 − suspicion penalties | gold table `facility_trust`, `/api/facilities` |
| Inspect | Row-level citations: claim quotes + corroborating equipment/procedure/description quotes, keyword-highlighted | `/api/facility/{id}` |
| Uncertainty | Every score is a **range** — width = what the record can't show (blank fields, missing coordinates). `solid / moderate / speculative` labels. Absence of data ≠ absence of care | gold table, method page |
| AI audit | On-demand LLM cross-examination (Databricks FM API): verdict + confidence + exact quotes + medical-consistency checks. Cached in Lakebase, traced in MLflow 3 | `/api/verify` |
| Override | Planner confirms/disputes/flags with a note — persists across sessions, badges shown in rankings | Lakebase `trust_desk.overrides` |
| Shortlist | Named shortlists persisted across sessions | Lakebase `trust_desk.shortlists` |
| Search | Hybrid (semantic + keyword) over all 10,088 records; `"dialysis near Jaipur"` triggers distance-aware referral ranking | Vector Search `facility_text_index` |
| Crisis Map | Facility corroboration dots + 708-district view separating **medical desert** from **data desert**, risk-ranked by NFHS institutional-birth rates | `/map.html` |
| Review queue | 112 suspicious records (200,000-bed claims, North-Atlantic coordinates…) with human-readable reasons | `/api/review_queue` |
| Compare | Side-by-side evidence for two facilities | `/compare.html` |
| Methodology | Full scoring transparency + statistical self-validation + known limits | `/method.html` |

## Native Databricks surfaces

- **Genie space** — "Trust Desk — Ask the data": NL questions with claim-vs-corroboration semantics baked into space instructions
- **AI/BI dashboard** — "Trust Landscape": claim-only rates, tiers, evidence observability, suspicious records (published, Genie-linked)

## Architecture (all Free Edition)

```
Marketplace dataset (10,088 facilities, 51 cols)
  └─ Unity Catalog: workspace.hackathon
       ├─ facilities_raw → facilities_silver (nb-normalized, deduped)
       ├─ facility_trust (gold: per-capability claims/corroboration, scores, uncertainty)
       ├─ pincodes (165,627 · India Post) + nfhs (706 districts · NFHS-5)  → geo validation + need
       └─ facility_text → Vector Search index (gte-large-en, hybrid queries)
Databricks App (FastAPI + vanilla JS)
  ├─ SQL warehouse (serverless) for all analytics
  ├─ Lakebase Postgres: overrides, shortlists, AI-verification cache
  ├─ FM API (gpt-oss-120b) for evidence audits — MLflow 3 tracing on every call
  └─ Genie + AI/BI dashboard links
```

## Key tradeoffs

- **Rules-over-model trust score**: a planner can defend "why is this #1" to a donor by pointing at quotes, not embeddings. The LLM is a second opinion, not the referee.
- **LLM verification on-demand + cached**, not bulk over 10k rows — cost-honest; every row still has a score without an LLM call.
- **Claude/GPT-5.6/Gemini endpoints are rate-limited to 0 on Free Edition** — verifier runs on `gpt-oss-120b` (noted, not hidden).
- `address_stateOrRegion` sometimes holds a district, not a state — geo trust uses the pincode join instead.

## Self-validation without ground truth

If corroboration were keyword noise, equipment-corroboration and procedure-corroboration would be independent. They aren't: odds ratios 1.8 (ICU), 3.6 (maternity), 5.1 (dialysis), n = 1.4–2.7k per capability. The signal clusters on real capability. Full table on `/method.html`.

## Repo map

- `app/` — the Databricks App (FastAPI backend, static frontend, `app.yaml`)
- `sql/` — silver/gold table definitions + dashboard JSON
- `docs/` — challenge brief, data profile (10-question analysis + rubric), pitch
- `tools/dbsql` — SQL helper · `tools/smoke` — 14-check pre-demo smoke test
- `assets/` — verified UI screenshots

## Run / redeploy

```bash
export DATABRICKS_CONFIG_PROFILE=hackathon
./tools/smoke                                   # 14 checks, all surfaces
cd app && databricks sync --full . /Workspace/Users/<you>/trust-desk-src \
  && databricks apps deploy trust-desk --source-code-path /Workspace/Users/<you>/trust-desk-src
```

Rebuild tables: `./tools/dbsql "$(cat sql/silver_facilities.sql)"` then `gold_trust.sql`.
