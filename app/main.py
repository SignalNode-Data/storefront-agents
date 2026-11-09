"""Half Tempo Café demo: run the agent pipeline live on preset products.

Safety (see SCOPE.md section 7):
- Preset products only: visitors pick from the catalog; there is no free-text input.
- Research is served from the cache, so visitors never trigger Search grounding.
- Per-visitor limit and a daily global limit, kept in memory (Cloud Run max instances = 1).
- Gemini runs through Vertex AI with the service account: no API key exists.
"""
import json
import os
import pathlib
import threading
import time
from collections import defaultdict

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse

from storefront_agents import agents
from storefront_agents.catalog import load_catalog
from storefront_agents.pipeline import run_product

PER_VISITOR_PER_DAY = int(os.environ.get("PER_VISITOR_PER_DAY", "5"))
GLOBAL_PER_DAY = int(os.environ.get("GLOBAL_PER_DAY", "60"))
RECORDED_RUN = os.environ.get("RECORDED_RUN", "runs/pipeline-v1/outputs.jsonl")
BASELINE_RUN = os.environ.get("BASELINE_RUN", "runs/baseline-v1/outputs.jsonl")

app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)  # no public API docs
CATALOG = {p["id"]: p for p in load_catalog()}
RAW = {json.loads(l)["item_id"]: json.loads(l) for l in open("data/abo/selected_listings.jsonl", encoding="utf-8")}


def _load(path):
    f = pathlib.Path(path)
    return {json.loads(l)["id"]: json.loads(l) for l in f.open(encoding="utf-8")} if f.exists() else {}


RECORDED, BASELINE = _load(RECORDED_RUN), _load(BASELINE_RUN)

_lock = threading.Lock()
_day = [time.strftime("%Y-%m-%d")]
_per_visitor = defaultdict(int)
_global = [0]


def _visitor(request: Request):
    fwd = request.headers.get("x-forwarded-for", "")
    return fwd.split(",")[0].strip() or (request.client.host if request.client else "?")


def _take_quota(visitor):
    with _lock:
        today = time.strftime("%Y-%m-%d")
        if today != _day[0]:
            _day[0] = today
            _per_visitor.clear()
            _global[0] = 0
        if _global[0] >= GLOBAL_PER_DAY:
            return "The demo has reached today's limit. Recorded runs are still available."
        if _per_visitor[visitor] >= PER_VISITOR_PER_DAY:
            return f"You've used your {PER_VISITOR_PER_DAY} live runs for today. Recorded runs are still available."
        _per_visitor[visitor] += 1
        _global[0] += 1
        return None


@app.middleware("http")
async def noindex(request, call_next):
    resp = await call_next(request)
    resp.headers["X-Robots-Tag"] = "noindex, nofollow"
    return resp


@app.get("/")
def index():
    return FileResponse("app/static/index.html")


@app.get("/robots.txt")
def robots():
    return FileResponse("app/static/robots.txt", media_type="text/plain")


@app.get("/api/products")
def products():
    return [{"id": p["id"], "name": p["name"], "group": p["group"]} for p in CATALOG.values()]


@app.get("/api/image/{pid}")
def image(pid: str):
    if pid not in CATALOG:
        raise HTTPException(404)
    return FileResponse(CATALOG[pid]["image"], media_type="image/jpeg")


@app.get("/api/recorded/{pid}")
def recorded(pid: str):
    if pid not in CATALOG:
        raise HTTPException(404)
    research = json.loads((pathlib.Path("data/research") / f"{pid}.json").read_text()) if (pathlib.Path("data/research") / f"{pid}.json").exists() else {}
    return {"after": RECORDED.get(pid), "before": BASELINE.get(pid), "product": CATALOG[pid],
            "search_entry_point": research.get("search_entry_point")}


@app.post("/api/run/{pid}")
def run(pid: str, request: Request):
    if pid not in CATALOG:
        raise HTTPException(404)
    cache = pathlib.Path("data/research") / f"{pid}.json"
    if not cache.exists():  # never trigger live Search grounding from the demo
        raise HTTPException(409, "No cached research for this product.")
    msg = _take_quota(_visitor(request))
    if msg:
        raise HTTPException(429, msg)
    t0 = time.time()
    result = run_product(CATALOG[pid], RAW[pid])
    result["seconds"] = round(time.time() - t0, 1)
    result["search_entry_point"] = json.loads(cache.read_text()).get("search_entry_point")
    return result
