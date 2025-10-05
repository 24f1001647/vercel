from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
import pandas as pd

app = FastAPI()

# Enable CORS for POST from any origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["POST"],
    allow_headers=["*"],
)

# Pydantic model for request body
class LatencyRequest(BaseModel):
    regions: List[str]
    threshold_ms: float

# Load telemetry JSON
df = pd.read_json("q-vercel-latency.json")

@app.post("/")
def compute_metrics(req: LatencyRequest):
    result = {}
    for region in req.regions:
        region_df = df[df["region"] == region]
        if region_df.empty:
            continue
        avg_latency = region_df["latency_ms"].mean()
        p95_latency = region_df["latency_ms"].quantile(0.95)
        avg_uptime = region_df["uptime_pct"].mean() / 100  # convert to 0-1 scale
        breaches = (region_df["latency_ms"] > req.threshold_ms).sum()

        result[region] = {
            "avg_latency": round(avg_latency, 2),
            "p95_latency": round(p95_latency, 2),
            "avg_uptime": round(avg_uptime, 3),
            "breaches": int(breaches)
        }
    return result
