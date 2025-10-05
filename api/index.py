# api/index.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
import pandas as pd
import json

app = FastAPI()

# Enable CORS for POST requests from any origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["POST"],
    allow_headers=["*"],
)

# Pydantic model for the request body
class MetricsRequest(BaseModel):
    regions: List[str]
    threshold_ms: float

# Load telemetry data once at startup
with open("telemetry.json", "r") as f:
    telemetry_data = json.load(f)
df = pd.DataFrame(telemetry_data)

@app.post("/metrics")
def get_metrics(request: MetricsRequest):
    result = {}
    for region in request.regions:
        region_df = df[df["region"] == region]
        if region_df.empty:
            continue
        avg_latency = region_df["latency_ms"].mean()
        p95_latency = region_df["latency_ms"].quantile(0.95)
        avg_uptime = region_df["uptime_pct"].mean() / 100  # convert to 0-1
        breaches = (region_df["latency_ms"] > request.threshold_ms).sum()

        result[region] = {
            "avg_latency": round(avg_latency, 2),
            "p95_latency": round(p95_latency, 2),
            "avg_uptime": round(avg_uptime, 3),
            "breaches": int(breaches)
        }
    return result


