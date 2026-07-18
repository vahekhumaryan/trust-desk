# Portal submission content — ready to paste

Portal: https://projects.hack-nation.ai · event `hack-nation-event-6` · **deadline Jul 19, 9:00 AM ET (17:00 Yerevan)**
Project Team ID (assigned by portal): **HN-5694** · Account ID: 7eb47421-4b5d-457b-9cd4-98a97f767d80

## Project Title
Trust Desk — The Trust Layer for Indian Healthcare

## Challenge
Challenge 4 _ Data Legend: Building the Trust Layer for Indian Healthcare

## Short Description
Trust Desk evidence-scores 10,088 scraped Indian health-facility records: every capability claim is ranked by corroboration, cited to quoted text, uncertainty is shown honestly as a score range, an AI auditor gives a traced second opinion, and the planner's own judgment persists forever — live on Databricks Free Edition.

## 1. Problem & Challenge
In India, a postal code often determines a lifespan. Families drive hours to an ICU that was a claim, not a capability. NGO planners have data but no evidence they can act on: in the sponsor's 10,088-record dataset we measured that **roughly half of all high-acuity claims (ICU 51%, NICU 50%, oncology 49%) have zero independent corroboration** anywhere in their own record. One Kerala hospital is geocoded to the middle of the North Atlantic; another claims 200,000 beds. There is no ground truth — so the challenge is to reason about trust honestly and still let a non-technical planner make defensible decisions.

## 2. Target Audience
Non-technical NGO program planners and public-health officials (the Virtue Foundation persona) deciding where to send equipment, staff, or referral programs — people who must defend every choice to donors and ministries. Secondary users: referral coordinators ("dialysis near Jaipur"), and data stewards triaging which records to fix first.

## 3. Solution & Core Features
A live Databricks App with one core loop and receipts at every step:
- **Rank** facilities per capability & region by a transparent 0–100 evidence score (corroboration 40 / completeness 20 / web presence 25 / geo validity 15 − suspicion penalties)
- **Inspect** row-level citations: claim quotes plus corroborating equipment/procedure/description quotes, keyword-highlighted
- **Honest uncertainty**: every score is a range — the width is the data deficit from unobservable fields; facilities are labeled solid / moderate / speculative
- **AI evidence audit** on demand: verdict + confidence + exact quotes + medical-consistency checks (ICU⇒ventilators, surgery⇒anesthesia), cached in Lakebase, MLflow-traced
- **Human override & shortlists** persisted in Lakebase Postgres, badged on every future ranking
- **Crisis Map**: 708 districts classified covered / unverified / no-capability / **data desert** — visually separating "no hospitals here" from "we don't know what's here", risk-ranked by NFHS-5 indicators
- **Review queue** of 112 suspicious records with human-readable reasons; **side-by-side evidence compare**; **hybrid semantic search** incl. distance-aware referral ("dialysis near Jaipur")
- **Genie space** + published **AI/BI dashboard** for every question we didn't build a screen for

## 4. Unique Selling Proposition (USP)
Trust Desk answers all three of the sponsor's open research questions instead of hiding from them: (1) **confidence without ground truth** — corroboration across independently-extracted fields, statistically self-validated (cross-field odds ratios 1.8–5.1, n=1.4–2.7k per capability); (2) **claims vs evidence** — a bare keyword scores zero, corroborated claims score high, and every point traces to a quote; (3) **data desert ≠ medical desert** — an explicit four-state district taxonomy on the map. The architecture is three layers of skepticism that can disagree with each other — deterministic SQL score, skeptical AI auditor, human override — so the planner sees the machine's evidence, the model's doubts, and their team's field knowledge side by side. No black box anywhere: the method page publishes weights, validation, and known limits.

## 5. Implementation & Technology
Medallion pipeline in pure SQL on Unity Catalog serverless (raw → silver normalization/dedup → gold per-capability corroboration + scores + uncertainty), joined against India Post (165,627 PINs) for geo validation and NFHS-5 for district need. App: FastAPI on Databricks Apps (OAuth service principal, zero secrets in code). Persistence: Lakebase Postgres (overrides, shortlists, AI-audit cache). Retrieval: Mosaic AI Vector Search, hybrid queries over all 10,088 records (gte-large-en). AI audit: Foundation Model API (gpt-oss-120b — frontier endpoints are rate-limited to 0 on Free Edition; documented tradeoff) with MLflow 3 tracing on every call. Plus a Genie space with claim-vs-evidence semantic instructions and a published AI/BI Lakeview dashboard. A 14-check smoke test covers every surface. Built solo in one overnight session.

## 6. Results & Impact
- Exposed the dataset's core truth: ~half of high-acuity capability claims have zero supporting evidence — now every one of 10,088 records carries a defensible, cited trust score
- 189 data-desert districts separated from 82 all-claims-unverified districts (maternity) — two different crises that were previously indistinguishable
- 1,284 facilities honestly flagged as moderate/speculative evidence; 112 suspicious records queued for review with reasons
- Trust signal validated without any ground truth (odds ratios 1.8–5.1) — a reusable method for any claims-vs-evidence dataset
- Fully live on Free Edition, 14/14 checks green; the entire framework transfers to any country with a postal directory and a health survey

## Most fun moment
At ~1 a.m. we discovered our ICU detector had quietly diagnosed every hospital in Calicut with an ICU — because "Cali**cu**t" contains "icu". One word-boundary regex later, an entire city was cured. Minutes after, the opposite lesson: a hospital claiming "established 1756" looked like obvious parse junk — it turned out to be INHS Asvini, genuinely India's oldest naval hospital, and it deserves its 90/100. The dataset punishes you for trusting it AND for distrusting it.

## Live Project URL
https://trust-desk-7474650580216748.aws.databricksapps.com

## GitHub Repository URL
https://github.com/vahekhumaryan/trust-desk

## Technologies/Tags
Databricks, Unity Catalog, Lakebase, Vector Search, MLflow, Genie, Databricks Apps, FastAPI, Python, SQL, Serverless, Healthcare AI

## Media plan (portal requires)
- Team picture* — NEEDED FROM VAHE (landscape photo)
- Demo video ≤60s* — `assets/submission/demo-video.mp4` (51s, UI/UX flow) ✓
- Tech video ≤60s* — `assets/submission/tech-video.mp4` (57s, architecture slides) ✓
- Team video ≤60s* — build from Vahe's photo + roles narration once photo arrives
- Optional media (up to 8): full 124s film `assets/trust-desk-demo.mp4`, screenshots ui-detail/ui-map-dist/ui-compare/ui-method, README PDF?
- Consent checkbox: requires Vahe's explicit OK (grants Hack-Nation usage/licensing review rights)
