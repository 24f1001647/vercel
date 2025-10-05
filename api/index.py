# api/index.py
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List
import pandas as pd
import json

app = FastAPI()

# Request body model
class MetricsRequest(BaseModel):
    regions: List[str]
    threshold_ms: float

# Load telemetry once at startup
with open("q-vercel-latency.json", "r") as f:
    telemetry_data = json.load(f)
df = pd.DataFrame(telemetry_data)

# Helper to add CORS headers to every response
def add_cors_headers(response: JSONResponse):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "POST, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "*"
    return response

# Handle preflight OPTIONS requests
@app.options("/metrics")
async def preflight():
    response = JSONResponse(content={})
    return add_cors_headers(response)

# Main POST endpoint
@app.post("/metrics")
async def metrics(request: MetricsRequest):
    result = {}
    for region in request.regions:
        region_df = df[df["region"] == region]
        if region_df.empty:
            continue
        avg_latency = region_df["latency_ms"].mean()
        p95_latency = region_df["latency_ms"].quantile(0.95)
        avg_uptime = region_df["uptime_pct"].mean() / 100
        breaches = (region_df["latency_ms"] > request.threshold_ms).sum()
        result[region] = {
            "avg_latency": round(avg_latency, 2),
            "p95_latency": round(p95_latency, 2),
            "avg_uptime": round(avg_uptime, 3),
            "breaches": int(breaches)
        }

    response = JSONResponse(content=result)
    return add_cors_headers(response)
