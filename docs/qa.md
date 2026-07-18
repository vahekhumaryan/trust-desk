# Expected judge Q&A — Trust Desk

Prepared answers for the live pitch / follow-ups. Numbers are real and verifiable in the app.

**Q: How can you score trust with no ground truth?**
We don't claim truth — we score *evidential support*. The discriminating signal is corroboration across independently-extracted fields (claim in `capability` backed by `equipment`/`procedure`/`description`). We validated the signal statistically: if it were keyword noise, equipment- and procedure-corroboration would be independent; observed joint rates are 1.3–1.6× the independence expectation (odds ratios 1.8 ICU, 3.6 maternity, 5.1 dialysis, n=1.4–2.7k). And where evidence is unobservable, the score honestly widens into a range instead of pretending.

**Q: Why a rules-based score instead of an ML model?**
Because the user is an NGO planner who must *defend* decisions to donors and governments. Every point traces to a quote; a learned score would trade that defensibility for accuracy we can't even measure (no labels). The LLM auditor is deliberately the second opinion, not the referee — three layers: deterministic SQL score → skeptical AI audit → human override, each able to disagree with the previous.

**Q: Keyword matching is brittle — paraphrases, synonyms?**
True, and we say so on the method page. Mitigations: word-boundary regexes (we caught "Cali**cu**t" matching ICU and fixed it), per-capability synonym sets, hybrid vector search for semantic recall, and the AI auditor precisely to catch paraphrased evidence the regexes miss. Uncaught paraphrase = false "claim-only" = conservative direction — we under-trust, never over-trust.

**Q: Your "independent fields" all come from the same website scrape. Isn't the corroboration circular?**
Sharpest question — it's limitation #2 on our method page. They're independent *extractions*, not independent *sources*. That's why corroboration caps at 40/100, why web presence (out-of-band verifiability) is 25, and why the override layer exists: true independence requires phone calls and site visits, and the product's job is to *record* those into Lakebase so verification compounds over time.

**Q: Why gpt-oss-120b and not Claude/GPT?**
Free Edition rate-limits the frontier endpoints (Claude, GPT-5.6, Gemini) to zero — we verified this empirically. gpt-oss-120b is the strongest available FM API endpoint; the verifier is model-agnostic (endpoint name is one env var). The tradeoff is documented, not hidden.

**Q: Does the AI audit run on all 10,088 rows? What does it cost?**
No — on-demand per facility+capability, cached permanently in Lakebase. Every row already has a deterministic score for free; the LLM spends tokens only where a human is actually looking. Every call is MLflow-traced, so cost per audit is observable.

**Q: What exactly distinguishes a data desert from a medical desert?**
District-level four-state taxonomy via facilities→PIN→district (95.5% join to the 165k-row India Post directory): *covered* (≥1 corroborated facility), *unverified* (claims exist, zero corroborated), *no capability* (facilities known, no claims), *data desert* (zero facilities known — absence of data, not of care). 189 data-desert vs 82 unverified districts for maternity, cross-referenced with NFHS-5 institutional-birth rates to rank real risk.

**Q: How do human overrides interact with the algorithmic score?**
They don't silently change it — that would launder opinion into "data". The score stays reproducible; the human verdict is displayed *beside* it on every ranking (✓ confirmed / ✗ disputed / ⚑ flagged) with the note and author. Decision-makers see both signals and their provenance.

**Q: The uncertainty range — what does 68–95 actually mean?**
Floor = score supported by observed evidence. Ceiling = score if every unobservable check (blank equipment list, missing coordinates) had turned out favorable. It's interval arithmetic over missing fields, not a confidence interval pretending to a probability model — and that honesty is the point: 1,284 facilities are flagged moderate/speculative.

**Q: Scale beyond 10k rows / other countries?**
The pipeline is three SQL statements over Unity Catalog (silver→gold) — 10k rows build in ~40 seconds serverless; 10M would still be minutes. Country transfer = new keyword sets + a postal directory + a health survey (every country has equivalents of India Post + NFHS). Nothing is India-hardcoded except those reference tables.

**Q: Why Lakebase for persistence instead of Delta tables?**
Millisecond transactional writes for user actions (override, shortlist toggle) with row-level upserts — OLTP shape. Analytics stay in Delta/serverless SQL. Right tool per workload, and it demonstrates the platform breadth the challenge asked for.

**Q: What's Genie adding beyond the app?**
The long tail. We built screens for the planner's core loop; Genie (with instructions encoding claimed-vs-corroborated semantics) answers everything else — "which states have the worst NICU corroboration rate?" — correctly distinguishing claims from evidence, no SQL knowledge needed.

**Q: What breaks in a live demo? / reliability?**
`tools/smoke` checks all 14 surfaces (app, Lakebase round-trip, search, referral, map, Genie, dashboard, MLflow) — 14/14 green at submission. Caches pre-warm on app start; the AI audit for demo facilities is pre-cached. The app link needs a Databricks login (platform constraint) — the video shows the full flow, and we add reviewers to the workspace on request.

**Q: Most surprising thing you found?**
INHS Asvini claims "established 1756" — looks like parse junk, is actually India's oldest naval hospital, and scores 90 with full corroboration. Meanwhile "Harsh Hospital" claims 200,000 beds. The dataset punishes naive rules in both directions — that's why suspicion penalties are calibrated per finding (we flag <1800 except documented-old, cap plausible at 5,000 beds).

**Q: What would you build next with a week?**
(1) Override-informed re-scoring with provenance (Bayesian update where field-verified facts adjust priors, visibly). (2) Bulk audit queue: run the LLM verifier over the 82 unverified-district facilities overnight and feed the review queue. (3) True source independence: cross-reference government facility registries (HMIS/NIN) as a second evidence source. (4) Mobile-first field-worker mode for on-site verification capture.

**Q: Is any of this real patient data / PII risk?**
No patient data — facility-level public web information only, from the sponsor-provided dataset. Planner notes are the only user-generated content, stored in Lakebase within the same governed workspace.
