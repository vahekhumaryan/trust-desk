# Challenge: Data Legend — Databricks × Virtue Foundation
## "Building the Trust Layer for Indian Healthcare"

Source: `task.docx.pdf` (challenge #04, sponsor: Databricks). Read this file first in any fresh session.

## The task in one paragraph

We get **10,000 messy records of Indian healthcare facilities** (51 columns: structured location/specialty fields + noisy free-text claims about equipment, procedures, services). Facility claims are **unverified** — "has ICU" may be marketing, not capability. Build a **live Databricks App on Free Edition** that a non-technical NGO planner can use to make decisions they can trust and defend: every output cites the row-level text that supports it, communicates uncertainty honestly, and **persists user actions** (notes, overrides, shortlists, scenarios) across sessions.

## Core requirements (all three, for ONE chosen track)

1. **Evidence Engine** — extract structure from the free-text fields; every important output traces back to supporting facility text (row-level citations).
2. **Trust Scorer** — no ground truth exists; reason about confidence. A facility claiming "Advanced Surgery" with no anesthesiologist listed must rank below one with corroborating evidence across fields. Flag suspicious/incomplete data.
3. **Planner's Workflow** — clear non-technical user journey in a Databricks App; user actions persist beyond the session; demo live on Free Edition.

## Tracks (choose ONE, nail it end-to-end)

| Track | Question | Minimum workflow |
|---|---|---|
| **Facility Trust Desk** | Can this facility do what it claims? | Select capability (ICU, maternity, emergency, oncology, trauma, NICU) + region → ranked facilities w/ trust signals → expand facility to inspect citations → override assessment with a note |
| **Medical Desert Planner** | Where are the highest-risk gaps, and how confident are we? | Select capability + geography (state/city/district/PIN) → trust-weighted coverage → drill into records behind an aggregate → save planning scenario |
| **Referral Copilot** | Where should a patient actually go? | Enter location + care need ("dialysis near Jaipur") → evidence-attached shortlist w/ distance, matching evidence, gaps → save shortlist |
| **Data Readiness Desk** | What must be fixed before trusting this dataset? | Surface completeness gaps, contradictions, suspicious claims, high-leverage records → flagged review queue → persist reviewer decisions |

**Our choice: Facility Trust Desk** (core) + Medical-Desert-style map as a stretch (see decision log in pitch.md).

## Stretch goals

1. **Agentic Traceability** — sentence-level citations + reasoning steps; MLflow 3 Tracing to visualize the evidence pipeline.
2. **Self-Correction Loops** — Validator step cross-checking extracted claims against medical-consistency rules (e.g., surgery claim requires anesthesia signal).
3. **Dynamic Crisis Mapping** — map of India, trust-weighted, by PIN code; visually separate "no hospitals here" from "we don't know what's here". Inspiration: https://vfmatch.org/explore
4. **Real-Impact Bonus** — solving any "could have"/"won't have" open question; call it out in the demo.

## Open research questions (they don't have answers — bonus if we do)

- **Confidence scoring without ground truth** — statistics-based prediction intervals around conclusions (solid vs. speculative).
- **Claims vs. evidence** — what separates a corroborated ICU claim from a bare keyword?
- **Data desert vs. medical desert** — only 25% of records have capacity, 36% doctor counts; sparse region ≠ no care.

## Dataset

**India 10k**: 10,000 facilities, 51 columns. Field coverage: description 100%, capability 99.7%, procedure 92.5%, equipment 77.0%, numberDoctors 36.4%, capacity 25.2%, yearEstablished 47.8%. Treat extracted evidence fields as **noisy claims, not ground truth**.

- Dataset: Databricks Marketplace listing `19326b3d-db63-4627-abc0-cf4e8131a305` — https://login.databricks.com/signin?intent=SIGN_IN&auto_login=true&destination_url=%2Fmarketplace%2Fconsumer%2Flistings%2F19326b3d-db63-4627-abc0-cf4e8131a305 (requires Databricks account)
- Virtue Foundation schema doc: https://docs.google.com/document/d/1UDkH0WLmm3ppE3OpzSuZQC9_7w3HO1PupDLFVqzS_2g — orgs are NGO / facility / other; contact layer (E164 phones, domain-only website), multi-line address + ISO alpha-2 country, facility attrs (type: hospital/pharmacy/doctor/clinic/dentist; operator public/private; affiliations faith-based/philanthropic/community/academic/government; floor area, doctor count, bed capacity), specialties in exact camelCase (e.g. `cardiology`), procedures w/ quantities, equipment w/ model numbers, capabilities w/ care levels + accreditations.
- Starter materials (prompts + pydantic models used to CREATE the data): `docs/starter/*.py` — key: `free_form.py` (FacilityFacts: procedure/equipment/capability extraction prompt), `medical_specialties.py` (camelCase specialty taxonomy + mapping rules), `facility_and_ngo_fields.py` (full Facility/NGO schema), `organization_extraction.py` (facility vs NGO classification). These tell us exactly how the noisy fields were generated → design the trust scorer around their failure modes.

## Required stack (Free Edition ONLY — no paid workspace)

- **Databricks Apps** — the submission surface (live deployable app)
- **Agent Bricks** — foundation model training/serving
- **Genie** — autonomous multi-step data tasks
- **MLflow 3** — agent observability, trace cost tracking
- **Mosaic AI Vector Search** — retrieval across 10k rows
- **Lakebase** — persistence for notes/overrides/shortlists/scenarios

## Evaluation

- **Evidence & Trust 35%** — row-level citations, honest uncertainty, data desert ≠ medical desert, self-checking
- **Product Judgment 30%** — clear user, intuitive for non-technical NGO planner, real decision problem (not tech behind a chat box)
- **Technical Execution 25%** — works live on Free Edition; good use of Apps, serverless, Vector Search, Lakebase
- **Ambition 10%** — beyond minimum: multi-track integration, self-correction, crisis mapping

## Submission

Git repo + live Databricks App. One-minute demo: user, workflow, technical approach, key tradeoffs.
