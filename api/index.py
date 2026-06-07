from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pathlib import Path
import json
import math

app = FastAPI()

# CORS - allow ANY origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

# Load data
DATA_FILE = Path(__file__).parent.parent / "telemetry.json"

with open(DATA_FILE, "r", encoding="utf-8") as f:
    DATA = json.load(f)

class RequestBody(BaseModel):
    regions: list[str]
    threshold_ms: float

def p95(values):
    values = sorted(values)

    if len(values) == 1:
        return values[0]

    index = math.ceil(0.95 * len(values)) - 1
    return values[index]

@app.get("/")
def health():
    return {"status": "ok"}

@app.post("/")
def analyze(req: RequestBody):
    result = {}

    for region in req.regions:
        rows = [r for r in DATA if r["region"] == region]

        if not rows:
            result[region] = {
                "avg_latency": 0,
                "p95_latency": 0,
                "avg_uptime": 0,
                "breaches": 0
            }
            continue

        latencies = [r["latency_ms"] for r in rows]
        uptimes = [r["uptime_pct"] for r in rows]

        result[region] = {
            "avg_latency": sum(latencies) / len(latencies),
            "p95_latency": p95(latencies),
            "avg_uptime": sum(uptimes) / len(uptimes),
            "breaches": sum(
                1
                for r in rows
                if r["latency_ms"] > req.threshold_ms
            )
        }

    return result