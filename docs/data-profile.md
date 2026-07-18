# Data profile — workspace.hackathon.facilities_raw

10,088 rows, 51 cols, all strings except `latitude`/`longitude` (double). **Null placeholder is the literal string `'null'`** (and `''`, `'[]'` for arrays) — every coverage/cast must strip these first. Helper predicate used throughout:
`trim(coalesce(col,'')) NOT IN ('','null','None','[]')` — abbreviated below as `nb(col)` ("non-blank").

## 1. Coverage (non-blank count / 10,088)

| column | n | % | | column | n | % |
|---|---|---|---|---|---|---|
| unique_id | 10088 | 100 | | description | 10006 | 99.2 |
| name | 10023 | 99.4 | | specialties | 9972 | 98.9 |
| websites (array) | 10027 | 99.4 | | capability | 9947 | 98.6 |
| officialWebsite | 8421 | 83.5 | | procedure | 9218 | 91.4 (+724 `[]`) |
| email | 8569 | 84.9 | | equipment | 7683 | 76.2 (+2180 `[]`) |
| officialPhone | 9523 | 94.4 | | capacity | 2520 | 25.0 |
| phone_numbers (array) | 9747 | 96.6 | | numberDoctors | 3633 | 36.0 |
| facebookLink | 9896 | 98.1 | | yearEstablished | 4803 | 47.6 |
| address_city | 10024 | 99.4 | | area | 129 | 1.3 |
| address_stateOrRegion | 10025 | 99.4 | | acceptsVolunteers | 42 | 0.4 |
| address_zipOrPostcode | 10022 | 99.3 | | countries | 28 | 0.3 |
| address_country(+code) | 10029 | 99.4 | | affiliationTypeIds | 1239 | 12.3 |
| facilityTypeId | 9962 | 98.8 | | recency_of_page_update | 3547 | 35.2 |
| operatorTypeId | 9327 | 92.5 | | number_of_facts | 2757 | 27.3 |
| latitude/longitude | 9970 | 98.8 | | n_followers | 8885 | 88.1 |
| coordinates / source / source_urls / cluster_id | 9970–9971 | 98.8 | | n_likes / n_engagements | 7801 / 4888 | 77.3 / 48.5 |
| source_types / source_ids | 10010 / 9298 | 99.2 / 92.2 | | last_post_date / post_count | 4932 / 3785 | 48.9 / 37.5 |

~65 rows are junk/misaligned (name = 'null' or contains array/coordinate spillover from CSV column shift — see Q3 facilityTypeId).

## 2. Geo quality (India bbox: lat 6–37, lon 68–98)

- **null lat/lon: 118** (1.2%) · **in bbox: 9,964** · **out of bbox: 6** (0.06%)
- Of the 6: 1 negative lon, 1 negative lat, **0 fixable by lat/lon swap**, rest are just wrong (Mongolia, Morocco coast, Mediterranean, South China Sea).
- All 6 offenders:
  | name | state | lat | lon |
  |---|---|---|---|
  | Sanjivani Multi Speciality Hospital | Alappuzha (Kerala — note: district in state col) | 59.95 | −38.26 |
  | Krishna Hospital Multispeciality | Uttar Pradesh | −81.71 | 26.95 |
  | Hzb Arogyam Multispeciality Hospital | Jharkhand | 46.07 | 106.17 |
  | Cura Imaging & Gastro Clinic | Maharashtra | 2.95 | 41.39 |
  | The Family Tree Hospital | Andhra Pradesh | 32.96 | 7.48 |
  | Cardia Health Care | Uttar Pradesh | 7.71 | 109.69 |
- `address_stateOrRegion` sometimes holds a **district**, not a state (e.g. "Alappuzha") — don't trust it as a state enum; validate via pincode join instead.

## 3. Capability taxonomy

- Format: **JSON array of free-text scraped claim sentences**, avg **23.3 items/row**, 3 rows fail `from_json(...,'array<string>')`, 26 rows empty variants, 833 empty-string items inside arrays. **Not a controlled vocabulary** — same concept spelled many ways ("24/7 emergency care" 575, "provides 24/7 emergency care" 537, "24x7 emergency care" 137; "multispeciality/multi-speciality/multi-specialty/multispecialty hospital" 443+305+199+168).
- Top items: nabh accredited 663, outpatient dental clinic 662, 24/7 emergency care 575, operates 24/7 533, private hospital 501, inpatient+outpatient 481, multispeciality hospital 443, ivf program 359, "has 1 doctor on staff" 356, nabh accreditation 322, iso 9001:2015 certified 138, wheelchair accessible 144, "has 11-50 employees" 127.
- **Accreditation lives inside capability as text**: NABH ≈ 985+ mentions, ISO 9001 ≈ 138 — extract with `capability ILIKE '%nabh%'` / `'%iso 9001%'`. No structured care-level column.
- `specialties` IS a controlled camelCase vocabulary (internalmedicine 68k occurrences, familymedicine 23.7k, dentistry 13.1k, gynecologyandobstetrics 11k, …) — use it, not capability, for specialty logic.
- `facilityTypeId` near-controlled: hospital 5637, clinic 3782, dentist 490, doctor 21, farmacy 10 (typo), pharmacy 2, nursing_home 1, 'null'/∅ 126, plus ~5 misaligned rows containing floats/GeoJSON/URL arrays.

## 4. Corroboration matrix (claim in `capability`; corroborating fields = equipment, procedure, description via keyword RLIKE)

| claim | claims | claim-only (0 fields) | 1 field | 2+ fields | % claim-only |
|---|---|---|---|---|---|
| surgery | 4716 | 460 | 1930 | 2326 | 10% |
| emergency | 3263 | 1581 | 1253 | 429 | **48%** |
| maternity | 2546 | 1135 | 1039 | 372 | **45%** |
| icu | 1959 | 899 | 777 | 283 | **46%** |
| oncology | 1508 | 737 | 517 | 254 | **49%** |
| trauma | 1134 | 328 | 537 | 269 | 29% |
| nicu | 813 | 412 | 279 | 122 | **51%** |

Roughly **half of high-acuity claims (ICU/NICU/oncology/emergency/maternity) have zero independent corroboration** in equipment/procedure/description. Surgery corroborates best (equipment lists OTs, C-arms, cautery).

## 5. Contradictions / suspicious patterns

- **Surgery claim (capability∪specialties, 7,026 rows) with no anesthesia/anaesth signal in ANY field: 5,142 (73%)** — anesthesia is rarely scraped even for real hospitals (Fortis Anandapur Kolkata, Jupiter Hospital Thane, HCG Manavata Cancer Centre Nashik, Rajarajeswari Medical College Bengaluru, RAM Hospital Kanpur all trip it). Use as a *soft* signal only, or restrict to small facilities.
- **"Multi speciality" (name/capability) with capacity < 10: 21** — e.g. S.S. Dental Hospital Hyderabad (0), ICON KRISHI HOSPITAL Visakhapatnam (0), Prasad Hospital Bangalore (2), Ankur Hospital Karad (4), Ketkar Nursing Home Pune (4).
- **numberDoctors null/0 but ≥10 procedures: 2,888** — but procedure arrays are capped at 50 items and doctors coverage is only 36%, so this mostly flags missing data, not lies (Bangalore Baptist Hospital, Amrita Kochi, Kasturba Tumkur, MOSC Kolenchery, Govt Medical College Chandrapur — all real large hospitals with 50 procedures, null doctors).
- yearEstablished parse artifacts: values 0,1,4,7,15 (likely "N years ago" mis-parses); INHS Asvini = 1756 is **genuinely correct** (oldest naval hospital) — don't flag pre-1900 blindly, flag <1800 except known-old.

## 6. Web presence

- officialWebsite 8,421 (83.5%): **8,395 contain a dot, only 26 junk**; just 518 have `http` prefix (rest are bare domains — normalize before display); 43 point at directories/social (justdial/practo/facebook/google) masquerading as official sites.
- email 8,569, of which **8,151 contain '@'** (418 junk). officialPhone 9,523 (E.164 `+91…` format). facebookLink 9,896 and 9,878 actually contain "facebook".
- `websites` (plural) is a JSON array of **source URLs, not facility sites** — contains pubmed, makemytrip, gov portals. Use `officialWebsite` only.
- Social columns: n_followers 88%, last_post_date 49%, custom_logo_presence 95%, affiliated_staff_presence 99% populated (values need casting; many are '0'/'false').

## 7. cluster_id

- 9,970 rows have one; **9,959 distinct**: 9,948 singletons, **11 clusters of size 2, max size 2**.
- The 11 pairs are **exact duplicates** (same name/city/source, e.g. "HCG Multi Specialty Hospital" Ahmedabad ×2, "PPK Hospital" Marthandam ×2, "Sabine Hospital" Muvattupuzha ×2). Semantics: entity-resolution key from source `kie`; safe to dedupe with `row_number() over (partition by cluster_id order by unique_id)` — removes 11 rows. Not branch/chain groupings.

## 8. Sibling tables & join keys

- `workspace.hackathon.pincodes` (both clones landed): circlename, regionname, divisionname, officename, **pincode bigint**, officetype, delivery, **district**, **statename** (UPPERCASE), latitude/longitude (strings). One row per post office → **pincode is not unique; dedupe to pincode→(district,statename) first**.
- `workspace.hackathon.nfhs`: 109 cols. **district_name / state_ut are Title Case WITH TRAILING SPACES** — must `trim()`. ~half the indicator cols are `string` (contain '*'/na markers) — `try_cast` needed. Key indicators for the demo: institutional_birth_5y_pct, births_delivered_by_csection_5y_pct, hh_member_covered_health_insurance_pct, child_12_23m vaccination cols, anaemia cols.
- Join chain that works: `facilities.address_zipOrPostcode` → 9,766/10,022 are clean 6-digit; **9,568 (95.5%) match `pincodes.pincode`** → `lower(trim(pincodes.district))` = `lower(trim(nfhs.district_name))` covers **597/698 NFHS districts**; state join `lower(trim(statename))=lower(trim(state_ut))` matches 31 states. (Raw un-trimmed district join matches only 2 — the trailing spaces are a trap.)

## 9. Numeric distributions (try_cast from string)

| field | n | min | p50 | p90 | max | absurd |
|---|---|---|---|---|---|---|
| capacity | 2520 | 0 | 100 | 500 | **200,000** (Harsh Hospital) | 13 zeros, 1 >10k, 3 non-castable |
| numberDoctors | 3633 | 0 | 2 | 40 | **15,000** (Nithya Hospital); 6,000 (Kims) | 13 zeros |
| yearEstablished | 4803 | 0 | 2005 | — | 2025 | 13 < 1800 (mostly 0/1/4/7/15 parse junk; 1756 INHS Asvini is real) |

## 10. Free-text quality

- description: 10,006 rows; length p10=35, **p50=115**, p90=388, max=6,557. Mostly 1–2 sentence directory blurbs ("PMNRF empanelled private hospital in Surat, Gujarat."), some marketing ("Leading Siddha and Homeopathy hospital… 29+ years"), some affiliations only.
- equipment/procedure: JSON arrays of free-text sentences. Model numbers do appear ("1.5 Tesla MRI", "C-ARM", "Modular Operation Theater") but **quantities are rare**: 29% of equipment rows contain any digit, only ~1% match `<number> <unit>` patterns — the schema doc oversells this.
- **LLM-extraction noise**: 237 equipment rows / 129 procedure rows contain filler like "There are no specific medical equipment … listed in the provided content", plus empty-string array items. Filter items matching `'no specific'` or `''` before counting/corroborating.

---

# Trust rubric v1 (0–100, floor 0)

All predicates SQL-expressible against `facilities_raw` (+ pincode join). `nb(col)` = non-blank predicate above; `LOW(x)` = `lower(coalesce(x,''))`.

## A. Corroboration — 40 pts

Per claimed capability c ∈ {icu, surgery, maternity, emergency, oncology, trauma, nicu}:
- claim: `LOW(capability) RLIKE claim_pattern(c)` (patterns from Q4 query)
- n_corr(c) = `IF(equip match,1,0)+IF(proc match,1,0)+IF(desc match,1,0)` — **after filtering 'no specific' filler items**
- credit(c) = 1.0 if n_corr≥2, 0.5 if n_corr=1, 0.0 if 0
- `corr_score = 40 * avg(credit over claimed c)`; if no claims at all: 40 × 0.5 (neutral — absence of claims isn't dishonesty).

Rationale: claim-only rate is 10–51% per claim (Q4) — this is the discriminating signal.

## B. Completeness — 20 pts (8 checks × 2.5)

1. `nb(name) AND name NOT RLIKE '^\\['` (not a misaligned array row)
2. `try_cast(capacity AS int) BETWEEN 1 AND 5000`
3. `try_cast(numberDoctors AS int) BETWEEN 1 AND 1000`
4. `try_cast(yearEstablished AS int) BETWEEN 1800 AND 2026`
5. `length(description) >= 60`
6. `nb(specialties)`
7. `nb(equipment) AND LOW(equipment) NOT LIKE '%no specific%'`
8. `nb(procedure) AND LOW(procedure) NOT LIKE '%no specific%'`

Rationale: capacity 25% / doctors 36% / year 48% coverage — these separate curated records from scrapes.

## C. Web presence — 25 pts

- `officialWebsite`: `nb` AND `LIKE '%.%'` AND NOT directory/social (`justdial|practo|lybrate|facebook|google\.`) → **10**
- `email` `nb` AND `LIKE '%@%'` → **5**
- `officialPhone` `nb` → **4**
- `facebookLink` `nb` AND `ILIKE '%facebook%'` → **2**
- engagement: `try_cast(engagement_metrics_n_followers AS int) > 0 OR try_cast(post_metrics_post_count AS int) > 0 OR LOW(custom_logo_presence) IN ('true','1')` → **4**

Rationale: junk rate is tiny (26/8,421 websites), so presence ≈ verifiability; 43 directory-as-official cases get zeroed.

## D. Geo validity — 15 pts

- `latitude BETWEEN 6 AND 37 AND longitude BETWEEN 68 AND 98` → **8** (nulls score 0; 118 nulls + 6 out-of-bbox affected)
- `trim(address_zipOrPostcode) RLIKE '^[1-9][0-9]{5}$'` AND exists in `pincodes.pincode` → **5** (95.5% pass — failures are meaningful)
- pincode's `statename` consistent with `upper(address_stateOrRegion)` (exact or address_state is a district in that state's pincode rows) → **2**

## Penalties (subtract after summing; floor at 0)

- Misaligned/junk row (`facilityTypeId` not in {hospital,clinic,dentist,doctor,pharmacy,farmacy,nursing_home} while non-blank, or `name`='null') → **−15**
- "multi-special*" in name/capability AND `try_cast(capacity)<10` → **−5** (21 rows)
- `try_cast(capacity)=0 OR >5000` or `try_cast(numberDoctors)>1000` or `yearEstablished` in (0,1,…,15) → **−3 each**
- Surgery claim AND no `anesth|anaesth` anywhere AND `try_cast(capacity)<50` → **−3** (soft: 73% base rate makes the raw flag useless — Q5)
- Non-first member of a duplicate `cluster_id` pair → exclude from scoring (dedupe, 11 rows)

## Tier mapping (for the app)

`>=75` Trusted · `50–74` Plausible · `25–49` Thin evidence · `<25` Red flag. Expect roughly: corroborated hospitals with sites land 70–90; scrape-only clinics 35–55; the 6 geo offenders + 21 tiny "multi-speciality" land <30 (good demo rows: Sanjivani Multi Speciality, Harsh Hospital capacity 200k, Nithya Hospital 15k doctors).
