import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import json
import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Optional

from code import utils
from code.predictor import predict_row, predict_csv

app = FastAPI(
    title="ClaimLens AI",
    description="Multi-Modal Evidence Intelligence Platform",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ClaimInput(BaseModel):
    user_id: str
    image_paths: str
    user_claim: str
    claim_object: str

class BatchInput(BaseModel):
    claims: List[ClaimInput]

@app.get("/api/health")
def health():
    return {"status": "ok", "service": "ClaimLens AI"}

@app.get("/api/dashboard")
def dashboard():
    try:
        df = pd.read_csv(str(utils.DATASET_DIR / "claims.csv"))
        user_df = pd.read_csv(str(utils.DATASET_DIR / "user_history.csv"))
        stats = {
            "total_claims": len(df),
            "unique_users": df["user_id"].nunique(),
            "objects": df["claim_object"].value_counts().to_dict(),
            "users_with_risk": int((user_df["history_flags"].str.lower() != "none").sum()),
            "high_risk_users": int((user_df["rejected_claim"].astype(int) >= 3).sum()),
        }
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/claims")
def get_claims():
    try:
        df = pd.read_csv(str(utils.DATASET_DIR / "claims.csv"))
        records = df.to_dict(orient="records")
        for r in records:
            r["image_list"] = utils.parse_image_paths(r["image_paths"])
        return records
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/claims/{user_id}")
def get_user_claims(user_id: str):
    try:
        df = pd.read_csv(str(utils.DATASET_DIR / "claims.csv"))
        user_claims = df[df["user_id"] == user_id]
        if user_claims.empty:
            raise HTTPException(status_code=404, detail=f"No claims for {user_id}")
        records = user_claims.to_dict(orient="records")
        for r in records:
            r["image_list"] = utils.parse_image_paths(r["image_paths"])
        return records
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/users")
def get_users():
    try:
        df = pd.read_csv(str(utils.DATASET_DIR / "user_history.csv"))
        records = df.to_dict(orient="records")
        return records
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/users/{user_id}")
def get_user(user_id: str):
    try:
        df = pd.read_csv(str(utils.DATASET_DIR / "user_history.csv"))
        row = df[df["user_id"] == user_id]
        if row.empty:
            raise HTTPException(status_code=404, detail=f"User {user_id} not found")
        return row.iloc[0].to_dict()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/predict")
def predict(claim: ClaimInput):
    try:
        result = predict_row(claim.model_dump())
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/predict/batch")
def predict_batch(batch: BatchInput):
    try:
        results = []
        for claim in batch.claims:
            result = predict_row(claim.model_dump())
            results.append(result)
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/output")
def get_output():
    output_path = Path.cwd() / "output.csv"
    if not output_path.exists():
        raise HTTPException(status_code=404, detail="output.csv not found. Run predictions first.")
    df = pd.read_csv(str(output_path))
    return df.to_dict(orient="records")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
