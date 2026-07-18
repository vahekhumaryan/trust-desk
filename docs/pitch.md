# Trust Desk — pitch narrative (living doc)

**Track:** Facility Trust Desk · **Live app:** https://trust-desk-7474650580216748.aws.databricksapps.com
**One-liner:** An evidence desk for NGO planners: every facility claim in India's messiest healthcare dataset is ranked, cited, audited, and overridable — and uncertainty is honest, not hidden.

## The problem (0:00–0:30)

An NGO planner deciding where to send an ICU program has 10,088 scraped facility records. "Has ICU" might be marketing. Coordinates might be in the ocean — **Sanjivani Multi Speciality Hospital, Kerala, is geocoded to the middle of the North Atlantic** (59.9, −38.2). And the numbers we found are worse than anyone assumes:

- **~half of all high-acuity claims have zero independent corroboration** — NICU 51%, oncology 49%, emergency 48%, ICU 46%, maternity 45% (claim appears in the capability field, with nothing in equipment, procedures, or description).
- Real coverage is hidden by literal `'null'` strings: bed capacity exists for **25%** of rows, doctor counts for **36%**.
- Absurdities pass silently: Harsh Hospital claims **200,000 beds**; Nithya Hospital claims **15,000 doctors**; 21 "multi-speciality hospitals" have fewer than 10 beds.

You can't fix this data by tomorrow. You CAN reason about how much to trust each row — that's what we built.

## The solution (0:30–2:30 = live demo)

**Demo script:**

1. **Rank** — pick *ICU* + *Kerala*. Facilities ranked by a transparent 0–100 trust score (4 evidence signals + suspicion penalties, all SQL over the medallion tables — no black box). Chest Hospital tops the list; badge says *2/3 fields corroborate*.
2. **Inspect citations** — click a facility: every trust point traces to **row-level quotes** — capability claims, corroborating equipment ("Ventilators in Intensive Care Unit"), procedures, description sentences, keywords highlighted. A claim-only facility shows an explicit warning: *no independent corroboration — this is a bare claim*.
3. **AI second opinion** — "Verify with AI": an LLM audit (Databricks FM API, gpt-oss-120b) returns verdict + confidence + **exact quotes only** + medical-consistency checks (ICU⇒ventilators+monitoring, surgery⇒anesthesia). Cached in Lakebase, every reasoning step **traced in MLflow**. It's skeptical by design: for our top-ranked ICU facility it says *plausible, 0.6* — and shows which checks failed.
4. **Override** — the planner knows things the data doesn't: *Dispute — called them, ICU closed since 2024*. Persists in **Lakebase Postgres** across sessions. Human beats model; the model must show its work.
5. **Crisis Map** — the money shot: 3,166 maternity claims as dots (green corroborated → red claim-only), plus the district view separating **medical desert from data desert**: 189 districts with *zero facilities known* (purple — "we don't know") vs 82 districts where *every claim is unverified* (amber — "we know, but can't trust"), cross-referenced with NFHS institutional-birth rates to find the highest-risk gaps. Bad-geo callout names the 6 facilities mapped outside India.

## Why it's advanced (2:30–2:50)

- **Confidence without ground truth** (open research question): corroboration across independent fields as the discriminating signal — measured claim-only rates per capability (10–51%), scored 40/100, with completeness 20, web presence 25, geo validity 15, minus suspicion penalties. Fully SQL-expressible, fully explainable, derived from a 10-question data profile (`docs/data-profile.md`).
- **Claims vs evidence** (open question #2): a bare keyword scores 0; corroboration counts only *independent* fields, with word-boundary matching (naive matching counts "Cali**cu**t" as ICU — we found and fixed that).
- **Data desert ≠ medical desert** (open question #3): explicit 4-state district taxonomy on the map, joined facilities→pincode→district→NFHS (95.5% join rate).
- **Self-correction**: LLM verifier runs consistency rules and can *disagree* with the SQL score; humans can override both. Three layers of skepticism, all persisted, all traced.

## Stack (fully Free Edition)

Databricks Apps (FastAPI + vanilla JS) · serverless SQL warehouse (medallion: raw→silver→gold trust tables) · **Lakebase Postgres** (overrides, shortlists, verification cache) · **FM API** (gpt-oss-120b — Claude/GPT-5.6/Gemini endpoints are rate-limited to 0 on Free Edition; noted as a tradeoff) · **MLflow 3 tracing** (every AI audit) · **Vector Search** (gte-large-en index over facility text) · Unity Catalog.

## Key tradeoffs (say in video)

- LLM verification is **on-demand + cached**, not bulk over 10k rows — cost-honest, and the SQL score means every row still has a trust ranking without an LLM call.
- Trust score is deliberately **rules-over-model**: a planner can defend "why is this ranked #1" to a donor by pointing at quotes, not embeddings.
- `address_stateOrRegion` is unreliable (sometimes a district); geo trust comes from the pincode join instead.

## Submission checklist

- [x] Live Databricks App (Free Edition)
- [x] Row-level citations everywhere
- [x] Persistence beyond session (Lakebase: overrides + verification cache)
- [ ] Pitch video ≤3 min (user, workflow, technical approach, tradeoffs)
- [ ] README with run instructions
