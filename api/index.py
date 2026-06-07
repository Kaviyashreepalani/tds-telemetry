from fastapi import FastAPI, Response
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from pathlib import Path
import json

app = FastAPI()

# Load telemetry data
DATA_FILE = Path(__file__).parent.parent / "telemetry.json"

with open(DATA_FILE, "r", encoding="utf-8") as f:
    DATA = json.load(f)

class RequestBody(BaseModel):
    regions: list[str]
    threshold_ms: float

def percentile(values, p):
    values = sorted(values)
    n = len(values)

    if n == 1:
        return values[0]

    pos = (p / 100) * (n - 1)

    lower = int(pos)
    upper = min(lower + 1, n - 1)

    weight = pos - lower

    return values[lower] * (1 - weight) + values[upper] * weight

def add_cors(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "POST, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "*"
    return response

@app.options("/")
def options_handler():
    return add_cors(Response(status_code=200))

@app.get("/")
def health():
    return add_cors(JSONResponse({"status": "ok"}))

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
            "p95_latency": percentile(latencies, 95),
            "avg_uptime": sum(uptimes) / len(uptimes),
            "breaches": sum(
                1
                for r in rows
                if r["latency_ms"] > req.threshold_ms
            )
        }

    return add_cors(JSONResponse(result))