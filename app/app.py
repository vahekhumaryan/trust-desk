"""Trust Desk — healthcare facility trust explorer (Databricks App backend)."""

import os
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
def run_query(query: str):
    cfg = Config()  # picks up app service-principal creds injected by the runtime
    with dbsql.connect(
        server_hostname=cfg.host,
        http_path=f"/sql/1.0/warehouses/{WAREHOUSE_ID}",
        credentials_provider=lambda: cfg.authenticate,
    ) as conn:
        with conn.cursor() as cur:
            cur.execute(query)
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
