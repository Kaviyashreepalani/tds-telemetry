from fastapi import FastAPI
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from pathlib import Path
import json
import math

app = FastAPI()

DATA_FILE = Path(__file__).parent.parent / "telemetry.json"

with open(DATA_FILE, "r", encoding="utf-8") as f:
    DATA = json.load(f)

class RequestBody(BaseModel):
    regions: list[str]
    threshold_ms: float

def p95(values):
    values = sorted(values)
    idx = math.ceil(0.95 * len(values)) - 1
    return values[idx]

CORS_HEADERS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "POST, OPTIONS",
    "Access-Control-Allow-Headers": "*"
}

@app.options("/")
def options_root():
    return JSONResponse({}, headers=CORS_HEADERS)

@app.get("/")
def health():
    return JSONResponse(
        {"status": "ok"},
        headers=CORS_HEADERS
    )

@app.post("/")
def analyze(req: RequestBody):
    result = {}

    for region in req.regions:
        rows = [r for r in DATA if r["region"] == region]

        latencies = [r["latency_ms"] for r in rows]
        uptimes = [r["uptime_pct"] for r in rows]

        result[region] = {
            "avg_latency": sum(latencies) / len(latencies),
            "p95_latency": p95(latencies),
            "avg_uptime": sum(uptimes) / len(uptimes),
            "breaches": sum(
                1 for r in rows
                if r["latency_ms"] > req.threshold_ms
            )
        }

    return JSONResponse(result, headers=CORS_HEADERS)