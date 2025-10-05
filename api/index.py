from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
import pandas as pd
import json

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class MetricsRequest(BaseModel):
    regions: List[str]
    threshold_ms: float

with open("telemetry.json", "r") as f:
    telemetry_data = json.load(f)
df = pd.DataFrame(telemetry_data)

@app.post("/metrics")
def get_metrics(request: MetricsRequest, response: Response):
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

    # Manually set CORS header in the response
    response.headers["Access-Control-Allow-Origin"] = "*"
    return result


