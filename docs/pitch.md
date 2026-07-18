# Trust Desk — pitch narrative + video script (FINAL)

**Track:** Facility Trust Desk · **Live app:** https://trust-desk-7474650580216748.aws.databricksapps.com
**One-liner:** An evidence desk for NGO planners: every claim in India's messiest healthcare dataset is ranked, cited, audited, and overridable — and uncertainty is honest, not hidden.

## Video script — 150 seconds, narrated screen capture

Judging criteria coverage: user + workflow (Product 30%), citations/uncertainty/desert-distinction (Evidence & Trust 35%), stack usage (Technical 25%), multi-track + self-correction (Ambition 10%). Tradeoffs stated explicitly (submission requirement).

| # | t | Screen | Narration |
|---|---|---|---|
| 1 | 0–15s | Crisis map, maternity dots; zoom to a red cluster | "An NGO planner has ten thousand scraped records of Indian health facilities. One Kerala hospital is geocoded to the middle of the North Atlantic. And when a facility says it has an ICU — is that capability, or marketing?" |
| 2 | 15–30s | Trust Desk list, ICU + Kerala, ranked scores | "Trust Desk scores every claim by evidence, not keywords. We found that half of all ICU, NICU and oncology claims have zero independent corroboration anywhere in their own record. So ranking by trust changes everything." |
| 3 | 30–50s | Click top facility: breakdown + cited quotes | "Every point of the score traces to quoted text: the claim, the corroborating equipment, the procedures. Nothing is a black box — a planner can defend this ranking to a donor line by line." |
| 4 | 50–65s | Open speculative facility (68–95 range bar) | "When the record can't show us something, we don't guess — the score becomes a range. The width is the data deficit. Absence of data is not absence of care." |
| 5 | 65–85s | Click Verify with AI → verdict card | "For a second opinion, an AI auditor cross-examines the record on Databricks Foundation Model API — exact quotes only, medical-consistency checks, every reasoning step traced in MLflow, cached in Lakebase." |
| 6 | 85–100s | Dispute override + note; badge appears in list; shortlist | "The planner's judgment wins: overrides and shortlists persist across sessions in Lakebase Postgres, and show up in every future ranking." |
| 7 | 100–120s | Map, Districts mode: purple vs amber | "The crisis map separates two things everyone conflates: 189 purple districts where we simply have no data — and 82 amber districts where every maternity claim exists but none can be verified. Different problems, different missions." |
| 8 | 120–140s | Compare view; then "dialysis near Jaipur" referral | "Compare evidence side by side. Ask for dialysis near Jaipur — hybrid vector search plus distance, trust-weighted. Genie answers the questions we didn't build screens for." |
| 9 | 140–150s | Dashboard glance → app home | "Built solo in one night on Databricks Free Edition: Apps, serverless SQL, Vector Search, Lakebase, MLflow, Genie. Trust Desk — because before you can fix healthcare data, you have to know how much to trust it." |

**Tradeoffs to keep in narration (already embedded above):** rules-over-model scoring (defensible), LLM on-demand + cached (cost-honest), FM availability constraint (gpt-oss-120b since Claude/GPT/Gemini endpoints are disabled on Free Edition — stated on the method page).

## The three open research questions — our answers

1. **Confidence without ground truth** → corroboration across independent fields (odds-ratio validated 1.8–5.1) + uncertainty ranges whose width = unobservable evidence.
2. **Claims vs evidence** → bare keyword scores 0; independent-field corroboration with word-boundary matching; AI audit demands operational detail.
3. **Data desert ≠ medical desert** → explicit 4-state district taxonomy on the map, facilities→pincode→district→NFHS join (95.5% match).

## Demo numbers (memorize)

10,088 facilities · ICU claims 51% claim-only · 189 data-desert vs 82 unverified districts · Sanjivani at (59.9, −38.2) · Harsh Hospital 200,000 beds · INHS Asvini est. 1756 is REAL (scores 90) · odds ratios 1.8/3.6/5.1 · 14/14 smoke checks green

## Submission checklist

- [x] Live Databricks App (Free Edition) — all 14 surfaces smoke-tested
- [x] Row-level citations everywhere; honest uncertainty; desert distinction
- [x] Persistence: overrides + shortlists + AI-audit cache (Lakebase)
- [x] README with architecture + run instructions
- [ ] Video ≤3 min (script above, 150s target) — narrated screen capture
- [ ] Submit repo + app link + video
