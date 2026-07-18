"""Trust Desk — healthcare facility trust explorer (Databricks App backend)."""

import json
import os
import re
import threading
import time

import psycopg
from databricks import sql as dbsql
from databricks.sdk import WorkspaceClient
from databricks.sdk.core import Config
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

WAREHOUSE_ID = os.getenv("DATABRICKS_WAREHOUSE_ID", "4c8cec5ddedd872b")

STATS_SQL = """
SELECT count(*) n,
       sum(case when latitude between 6 and 37 and longitude between 68 and 98
                then 1 else 0 end) geo_ok
FROM databricks_virtue_foundation_dataset_dais_2026.virtue_foundation_dataset.facilities
"""

FACILITIES = "workspace.hackathon.facilities_raw"
TRUST = "workspace.hackathon.facility_trust"

# Regex patterns per capability — MUST stay in sync with sql/gold_trust.sql.
# Word boundaries on short tokens (icu/hdu/nicu) prevent substring hits like
# "Calicut". Corroboration = the same signal appearing independently in
# equipment / procedure / description, not just in the capability claim.
CAPABILITY_KEYWORDS = {
    "icu": [r"\bicu\b", "intensive care", "critical care", "ventilator", r"\bhdu\b"],
    "maternity": ["matern", "obstet", "deliver", "labour", "labor room", "gynec", "midwif"],
    "emergency": ["emergency", "casualty", "ambulance", "24x7", "24 x 7", "24/7"],
    "oncology": ["oncolog", "cancer", "chemother", "radiother", "radiation therap", "tumor", "tumour"],
    "trauma": ["trauma", "accident", "fracture", "orthopa"],
    "nicu": [r"\bnicu\b", "neonatal", "incubator", "premature", "newborn"],
    "dialysis": ["dialysis", "nephrolog", "kidney", "renal"],
    "surgery": ["surger", "surgical", "operation theat", "operating theat", "anesthes", "anaesthes"],
}


def _matches(patterns: list[str], text: str) -> bool:
    low = text.lower()
    return any(re.search(p, low) for p in patterns)


def ranked_facilities_sql(capability: str, state: str | None) -> tuple[str, list]:
    # capability comes from the CAPABILITY_KEYWORDS whitelist, never user input
    params: list = []
    state_filter = ""
    if state:
        state_filter = "AND lower(state) = lower(?)"
        params.append(state)
    sql = f"""
SELECT unique_id, name, city, state, latitude, longitude,
       capacity_n, doctors_n, year_est,
       claim_{capability} AS claimed, corr_{capability} AS corroborations,
       corr_score, completeness_score, web_score, geo_score, penalty,
       geo_in_india AS geo_valid, trust_score, tier
FROM {TRUST}
WHERE claim_{capability} {state_filter}
ORDER BY trust_score DESC, corroborations DESC
LIMIT 100
"""
    return sql, params

app = FastAPI(title="Trust Desk")

# ---- simple in-process cache -------------------------------------------------
_cache: dict = {}
_cache_lock = threading.Lock()
CACHE_TTL_SECONDS = 600


def _cached(key: str, ttl: int = CACHE_TTL_SECONDS):
    entry = _cache.get(key)
    if entry and (time.time() - entry["t"] < ttl):
        return entry["v"]
    return None


def _store(key: str, value):
    with _cache_lock:
        _cache[key] = {"v": value, "t": time.time()}


# ---- SQL helper --------------------------------------------------------------
def run_query(query: str, params: list | None = None):
    cfg = Config()  # picks up app service-principal creds injected by the runtime
    with dbsql.connect(
        server_hostname=cfg.host,
        http_path=f"/sql/1.0/warehouses/{WAREHOUSE_ID}",
        credentials_provider=lambda: cfg.authenticate,
    ) as conn:
        with conn.cursor() as cur:
            cur.execute(query, params or [])
            cols = [c[0] for c in cur.description]
            return [dict(zip(cols, row)) for row in cur.fetchall()]


# ---- Lakebase (Postgres) persistence ----------------------------------------
# Env vars PGHOST/PGDATABASE/PGUSER/LAKEBASE_ENDPOINT are injected by the Apps
# runtime because the app has a `postgres` resource attached. OAuth tokens live
# 1 hour, so cache one and refresh with headroom.
_pg_token: dict = {"token": None, "t": 0.0}
PG_TOKEN_TTL = 45 * 60


def _pg_password() -> str:
    if _pg_token["token"] and time.time() - _pg_token["t"] < PG_TOKEN_TTL:
        return _pg_token["token"]
    w = WorkspaceClient()
    token = w.postgres.generate_database_credential(
        endpoint=os.environ["LAKEBASE_ENDPOINT"]
    ).token
    _pg_token.update(token=token, t=time.time())
    return token


def pg_conn():
    return psycopg.connect(
        host=os.environ["PGHOST"],
        port=int(os.environ.get("PGPORT", "5432")),
        dbname=os.environ.get("PGDATABASE", "databricks_postgres"),
        user=os.environ["PGUSER"],
        password=_pg_password(),
        sslmode="require",
        connect_timeout=10,
    )


DDL = """
CREATE SCHEMA IF NOT EXISTS trust_desk;
CREATE TABLE IF NOT EXISTS trust_desk.overrides (
    id          bigserial PRIMARY KEY,
    facility_id text NOT NULL,
    verdict     text NOT NULL,          -- 'confirm' | 'dispute' | 'flag'
    capability  text,                   -- which claim the verdict is about
    note        text,
    author      text,
    created_at  timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS overrides_facility_idx
    ON trust_desk.overrides (facility_id);
CREATE TABLE IF NOT EXISTS trust_desk.shortlists (
    id           bigserial PRIMARY KEY,
    name         text NOT NULL,
    facility_ids jsonb NOT NULL DEFAULT '[]',
    created_at   timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS trust_desk.verifications (
    facility_id text NOT NULL,
    capability  text NOT NULL,
    result      jsonb NOT NULL,
    created_at  timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (facility_id, capability)
);
"""


@app.on_event("startup")
def init_db():
    # Best-effort: the app must still serve read-only pages if Lakebase is cold.
    try:
        with pg_conn() as conn:
            conn.execute(DDL)
        app.state.pg_ready = True
    except Exception as e:
        app.state.pg_ready = False
        app.state.pg_error = str(e)


# ---- Semantic search (Vector Search) -----------------------------------------
VS_INDEX = "workspace.hackathon.facility_text_index"


@app.get("/api/search")
def semantic_search(q: str, state: str | None = None):
    try:
        w = WorkspaceClient()
        kwargs = {}
        if state:
            kwargs["filters_json"] = json.dumps({"state": state})
        res = w.vector_search_indexes.query_index(
            index_name=VS_INDEX,
            columns=["unique_id", "name", "city", "state", "content"],
            query_text=q,
            num_results=15,
            **kwargs,
        )
        cols = [c.name for c in res.manifest.columns]
        hits = [dict(zip(cols, row)) for row in (res.result.data_array or [])]
        if not hits:
            return {"results": []}
        # join trust scores for the hit set
        ids = [h["unique_id"] for h in hits]
        ph = ",".join("?" * len(ids))
        trows = run_query(
            f"SELECT unique_id, trust_score, tier FROM {TRUST} WHERE unique_id IN ({ph})",
            ids,
        )
        tmap = {t["unique_id"]: t for t in trows}
        for h in hits:
            h["score"] = h.pop("score", None)
            # keep only the first matching line of content as a snippet
            h["snippet"] = (h.pop("content", "") or "")[:220]
            h.update(tmap.get(h["unique_id"], {}))
        return {"results": hits}
    except Exception as e:
        msg = str(e)
        if "not ready" in msg.lower() or "PENDING" in msg or "provisioning" in msg.lower():
            msg = "Semantic index is still syncing — try again in a few minutes."
        return JSONResponse(status_code=503, content={"error": msg})


# ---- Map: medical desert vs data desert --------------------------------------
@app.get("/api/map")
def map_points(capability: str):
    if capability not in CAPABILITY_KEYWORDS:
        return JSONResponse(status_code=400, content={"error": "unknown capability"})
    cache_key = f"map:{capability}"
    cached = _cached(cache_key)
    if cached is not None:
        return cached
    try:
        rows = run_query(
            f"""SELECT unique_id, name, city, state, latitude, longitude,
                       corr_{capability} AS corr, trust_score, tier, geo_in_india
                FROM {TRUST}
                WHERE claim_{capability} AND latitude IS NOT NULL"""
        )
        result = {
            "points": [r for r in rows if r["geo_in_india"]],
            "bad_geo": [r for r in rows if not r["geo_in_india"]],
        }
        _store(cache_key, result)
        return result
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


@app.get("/api/districts")
def district_gaps(capability: str):
    """Per-district coverage: separates 'no facilities known here' (data desert)
    from 'facilities exist but claims are uncorroborated' (trust desert)."""
    if capability not in CAPABILITY_KEYWORDS:
        return JSONResponse(status_code=400, content={"error": "unknown capability"})
    cache_key = f"districts:{capability}"
    cached = _cached(cache_key)
    if cached is not None:
        return cached
    try:
        rows = run_query(
            f"""
WITH districts AS (
  SELECT lower(trim(district)) d, first(trim(district)) district,
         first(trim(statename)) state,
         avg(try_cast(latitude AS double)) lat, avg(try_cast(longitude AS double)) lon
  FROM workspace.hackathon.pincodes GROUP BY 1
),
fac AS (
  SELECT lower(trim(pin_district)) d,
         count(*) n_fac,
         sum(CASE WHEN claim_{capability} THEN 1 ELSE 0 END) n_claim,
         sum(CASE WHEN claim_{capability} AND corr_{capability} >= 1 THEN 1 ELSE 0 END) n_corr
  FROM {TRUST} WHERE pin_district IS NOT NULL GROUP BY 1
),
need AS (
  SELECT lower(trim(district_name)) d,
         first(try_cast(institutional_birth_5y_pct AS double)) inst_birth_pct
  FROM workspace.hackathon.nfhs GROUP BY 1
)
SELECT di.district, di.state, di.lat, di.lon,
       coalesce(f.n_fac, 0) n_fac, coalesce(f.n_claim, 0) n_claim,
       coalesce(f.n_corr, 0) n_corr, n.inst_birth_pct,
       CASE
         WHEN coalesce(f.n_fac, 0) = 0 THEN 'data_desert'
         WHEN coalesce(f.n_claim, 0) = 0 THEN 'no_capability'
         WHEN coalesce(f.n_corr, 0) = 0 THEN 'unverified'
         ELSE 'covered'
       END AS status
FROM districts di
LEFT JOIN fac f ON di.d = f.d
LEFT JOIN need n ON di.d = n.d
WHERE di.lat BETWEEN 6 AND 37 AND di.lon BETWEEN 68 AND 98
"""
        )
        _store(cache_key, rows)
        return rows
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


# ---- LLM evidence verifier (on-demand, cached, MLflow-traced) ----------------
SERVING_ENDPOINT = os.getenv("VERIFIER_ENDPOINT", "databricks-gpt-oss-120b")
MLFLOW_EXPERIMENT_ID = os.getenv("MLFLOW_EXPERIMENT_ID", "4503398429584691")

try:
    import mlflow

    mlflow.set_tracking_uri("databricks")
    mlflow.set_experiment(experiment_id=MLFLOW_EXPERIMENT_ID)
    _trace = mlflow.trace
except Exception:  # tracing must never take the app down
    def _trace(fn=None, **kw):
        return fn if fn else (lambda f: f)


VERIFY_PROMPT = """You are an evidence auditor for NGO healthcare planning in India.
Facility claims are scraped free text and may be marketing, not capability.

Assess whether this facility can actually deliver: {capability}

FACILITY RECORD (the only evidence you may use):
name: {name}
capability claims: {cap}
procedures: {proc}
equipment: {equip}
description: {desc}
specialties: {specs}
beds: {beds} | doctors: {doctors} | year established: {year}

Rules:
- Cite EXACT quotes from the record for every piece of evidence. Never invent.
- Advanced claims need corroborating operational detail (equipment models, unit
  sizes, named staff/departments), not keyword repetition.
- Apply medical-consistency checks, e.g. surgery needs an anesthesia signal,
  ICU needs ventilators/monitoring, NICU needs incubators/warmers, dialysis
  needs machines/nephrology.
- Data absence is uncertainty, NOT evidence of absence — say so explicitly.

Respond with ONLY this JSON (no markdown fence):
{{"verdict": "corroborated|plausible|unsupported|contradicted",
 "confidence": 0.0-1.0,
 "summary": "<=2 sentences for a non-technical planner",
 "evidence": [{{"field": "...", "quote": "...", "supports": true/false}}],
 "consistency_checks": [{{"rule": "...", "passed": true/false, "note": "..."}}],
 "reasoning_steps": ["...", "..."]}}"""


@_trace(name="verify_capability")
def run_verification(facility_id: str, capability: str) -> dict:
    rows = run_query(
        f"""SELECT r.name, r.capability, r.procedure, r.equipment, r.description,
                   r.specialties, t.capacity_n, t.doctors_n, t.year_est
            FROM {FACILITIES} r JOIN {TRUST} t ON r.unique_id = t.unique_id
            WHERE r.unique_id = ?""",
        [facility_id],
    )
    if not rows:
        raise ValueError("facility not found")
    r = rows[0]
    prompt = VERIFY_PROMPT.format(
        capability=capability, name=r["name"], cap=r["capability"],
        proc=r["procedure"], equip=r["equipment"],
        desc=(r["description"] or "")[:4000], specs=r["specialties"],
        beds=r["capacity_n"], doctors=r["doctors_n"], year=r["year_est"],
    )
    w = WorkspaceClient()
    resp = w.api_client.do(
        "POST",
        f"/serving-endpoints/{SERVING_ENDPOINT}/invocations",
        body={"messages": [{"role": "user", "content": prompt}],
              "max_tokens": 1500, "temperature": 0.0},
    )
    content = resp["choices"][0]["message"]["content"]
    if isinstance(content, list):  # reasoning models return a list of blocks
        content = " ".join(
            b.get("text", "") for b in content
            if isinstance(b, dict) and b.get("type") in ("text", "output_text")
        )
    start, end = content.find("{"), content.rfind("}")
    return json.loads(content[start:end + 1])


class VerifyIn(BaseModel):
    facility_id: str
    capability: str


@app.post("/api/verify")
def verify(body: VerifyIn):
    if body.capability not in CAPABILITY_KEYWORDS:
        return JSONResponse(status_code=400, content={"error": "unknown capability"})
    try:
        with pg_conn() as conn:
            row = conn.execute(
                """SELECT result, created_at FROM trust_desk.verifications
                   WHERE facility_id = %s AND capability = %s""",
                (body.facility_id, body.capability),
            ).fetchone()
        if row:
            return {"cached": True, "created_at": row[1].isoformat(), **row[0]}
        result = run_verification(body.facility_id, body.capability)
        with pg_conn() as conn:
            conn.execute(
                """INSERT INTO trust_desk.verifications (facility_id, capability, result)
                   VALUES (%s, %s, %s)
                   ON CONFLICT (facility_id, capability) DO UPDATE SET result = EXCLUDED.result""",
                (body.facility_id, body.capability, json.dumps(result)),
            )
        return {"cached": False, **result}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


class OverrideIn(BaseModel):
    facility_id: str
    verdict: str
    capability: str | None = None
    note: str | None = None
    author: str | None = None


# ---- API ---------------------------------------------------------------------
@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "pg_ready": getattr(app.state, "pg_ready", None),
        "pg_error": getattr(app.state, "pg_error", None),
    }


@app.get("/api/capabilities")
def capabilities():
    return sorted(CAPABILITY_KEYWORDS.keys())


@app.get("/api/states")
def states():
    cached = _cached("states")
    if cached is not None:
        return cached
    try:
        rows = run_query(
            f"""SELECT state, count(*) n FROM {TRUST}
                WHERE state IS NOT NULL
                GROUP BY 1 HAVING count(*) >= 5 ORDER BY 1"""
        )
        result = [{"state": r["state"], "n": r["n"]} for r in rows]
        _store("states", result)
        return result
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


@app.get("/api/facilities")
def facilities(capability: str, state: str | None = None):
    if capability not in CAPABILITY_KEYWORDS:
        return JSONResponse(status_code=400, content={"error": f"unknown capability '{capability}'"})
    cache_key = f"fac:{capability}:{state or '*'}"
    cached = _cached(cache_key)
    if cached is not None:
        return cached
    try:
        sql_text, params = ranked_facilities_sql(capability, state)
        rows = run_query(sql_text, params)
        _store(cache_key, rows)
        return rows
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


@app.get("/api/facility/{unique_id}")
def facility_detail(unique_id: str, capability: str | None = None):
    try:
        rows = run_query(
            f"""SELECT r.unique_id, r.name, r.description,
                       r.capability, r.procedure, r.equipment, r.specialties,
                       t.address_line1, t.city AS address_city,
                       t.state AS address_stateOrRegion, t.pincode AS address_zipOrPostcode,
                       t.latitude, t.longitude, t.geo_in_india,
                       t.doctors_n AS numberDoctors, t.capacity_n AS capacity,
                       t.year_est AS yearEstablished,
                       t.email, t.phone AS officialPhone, t.website AS officialWebsite,
                       t.trust_score, t.tier, t.corr_score, t.completeness_score,
                       t.web_score, t.geo_score, t.penalty, t.anesthesia_signal
                FROM {FACILITIES} r JOIN {TRUST} t ON r.unique_id = t.unique_id
                WHERE r.unique_id = ?""",
            [unique_id],
        )
        if not rows:
            return JSONResponse(status_code=404, content={"error": "not found"})
        row = rows[0]
        # Claim fields are JSON arrays of free-text strings — parse them so the
        # frontend can render row-level citations.
        for field in ("capability", "procedure", "equipment", "specialties"):
            try:
                row[field] = json.loads(row[field]) if row[field] else []
            except (ValueError, TypeError):
                row[field] = [row[field]] if row[field] else []
        if capability in CAPABILITY_KEYWORDS:
            kws = CAPABILITY_KEYWORDS[capability]
            row["matched_keywords"] = kws
            row["citations"] = {
                field: [c for c in row[field] if _matches(kws, c)]
                for field in ("capability", "procedure", "equipment")
            }
            desc = row.get("description") or ""
            row["citations"]["description"] = [
                s.strip() for s in desc.replace("\n", " ").split(".")
                if _matches(kws, s)
            ][:5]
        return row
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


@app.post("/api/overrides")
def create_override(body: OverrideIn):
    try:
        with pg_conn() as conn:
            row = conn.execute(
                """INSERT INTO trust_desk.overrides
                   (facility_id, verdict, capability, note, author)
                   VALUES (%s, %s, %s, %s, %s)
                   RETURNING id, created_at""",
                (body.facility_id, body.verdict, body.capability, body.note, body.author),
            ).fetchone()
        return {"id": row[0], "created_at": row[1].isoformat()}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


@app.get("/api/overrides")
def list_overrides(facility_id: str | None = None):
    try:
        q = """SELECT id, facility_id, verdict, capability, note, author, created_at
               FROM trust_desk.overrides"""
        params: tuple = ()
        if facility_id:
            q += " WHERE facility_id = %s"
            params = (facility_id,)
        q += " ORDER BY created_at DESC LIMIT 200"
        with pg_conn() as conn:
            rows = conn.execute(q, params).fetchall()
        return [
            {
                "id": r[0], "facility_id": r[1], "verdict": r[2],
                "capability": r[3], "note": r[4], "author": r[5],
                "created_at": r[6].isoformat(),
            }
            for r in rows
        ]
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


@app.get("/api/stats")
def stats():
    cached = _cached("stats")
    if cached is not None:
        return {**cached, "cached": True}
    try:
        rows = run_query(STATS_SQL)
        result = {
            "facilities": int(rows[0]["n"]),
            "geo_valid": int(rows[0]["geo_ok"] or 0),
        }
        _store("stats", result)
        return {**result, "cached": False}
    except Exception as e:  # surface SQL/permission errors to the client clearly
        return JSONResponse(status_code=500, content={"error": str(e)})


# ---- static frontend (mounted last so /api/* wins) ---------------------------
app.mount("/", StaticFiles(directory="static", html=True), name="static")
