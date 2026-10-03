"""
api.py — real-time scoring API: how upay's backend would call ScamShield before confirming a Send Money transfer.

Run:   uvicorn api:app --port 8000        then open http://localhost:8000/docs to try it
       (Dataset A, the demo). To run on your own data: build Dataset B first (python workspace.py your_log.csv),
       then set SCAMSHIELD_WORKSPACE=B before starting uvicorn.
Call:  POST /score  with the transfer details (see ScoreRequest)

At startup it reads the active dataset's transaction history so it knows
every customer's habits. Each new transfer is turned into features with the SAME code used for training
(pipeline.FeatureState), scored by the models, and optionally added to history (commit=true).
"""
import os
from datetime import datetime
from typing import Optional

import pandas as pd
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

import engines as en
import mule_network as mn
import pipeline as pl
import risk_engine as re_
import workspace as wsp

WORKSPACE = os.environ.get("SCAMSHIELD_WORKSPACE", "A")
if not wsp.exists(WORKSPACE):
    raise RuntimeError(f"Dataset {WORKSPACE} is not built. Run: python workspace.py your_log.csv")
P = wsp.paths(WORKSPACE)
LOG = P["raw"]
app = FastAPI(title="upay ScamShield API", version="1.0",
              description="Scores a Send Money transfer before it is confirmed. Decision support only: "
                          "HOLD means pause and re-verify, never an automatic permanent block.")

_raw = wsp.read_log(LOG)
_feats, STATE = pl.run(_raw)
MODEL, IFOREST = re_.load_model(P["model"]), re_.load_iforest(P["iforest"])
_scored = re_.score_frame(MODEL, IFOREST, _feats)
WALLETS = mn.find_mules(_scored)
_edges = _raw.rename(columns={"sender_id": "from_wallet", "receiver_id": "to_wallet"})
RINGS = mn.find_rings(WALLETS, _edges)
RING_OF = {m: r["ring_id"] for r in RINGS for m in r["mules"]}


class ScoreRequest(BaseModel):
    sender_id: str = Field(..., examples=["U00042"])
    receiver_id: str = Field(..., examples=["W12345"])
    amount: float = Field(..., gt=0, examples=[6000])
    device_id: str = Field(..., examples=["DEV-1A2B"])
    district: str = Field(..., examples=["Dhaka"])
    on_active_call: int = Field(0, ge=0, le=1)
    timestamp: Optional[datetime] = Field(None, description="Defaults to now")
    commit: bool = Field(False, description="Add this transfer to history after scoring")


@app.get("/health")
def health():
    return {"status": "ok", "dataset": WORKSPACE, "transfers_in_history": len(_raw), "suspected_mule_wallets": int(WALLETS.suspected_mule.sum()),
            "mule_rings": len(RINGS)}


@app.post("/score")
def score(req: ScoreRequest):
    ts = pd.Timestamp(req.timestamp or datetime.now())
    f = STATE.peek(ts, req.sender_id, req.receiver_id, req.amount, req.device_id, req.district, req.on_active_call)
    row = pd.Series(f)
    one = pd.DataFrame([row])
    prob, contribs = re_.score(MODEL, one)
    prob = float(prob[0])
    anom = float(re_.anomaly(IFOREST, one)[0])
    level, rules = re_.decide(prob, row, anom)
    engs, n_flag = en.engine_panel(prob, anom, row, req.receiver_id, WALLETS, RING_OF)
    if engs[3]["flagged"] and level == "ALLOW":
        level, rules = "WARN", rules + ["KNOWN_MULE_WALLET"]
    reasons = [{"en": e, "bn": b} for _, _, e, b in re_.explain(row, contribs.iloc[0])]
    if "UNUSUAL_BEHAVIOUR" in rules:
        reasons.append({"en": re_.UNUSUAL_REASON[0], "bn": re_.UNUSUAL_REASON[1]})
    if req.commit:
        STATE.update(int(ts.value // 10**9), req.sender_id, req.receiver_id, req.amount, req.device_id, req.district)
    return {"decision": level, "action": re_.ACTIONS[level][0], "scam_probability": round(prob, 4),
            "anomaly_percentile": round(anom, 4), "engines_flagging": int(n_flag),
            "engines": [dict(name=e["name"], method=e["method"], score=round(float(e["score"]), 4),
                             flagged=bool(e["flagged"]), finding=str(e["note"])) for e in engs],
            "rules": rules, "reasons": reasons, "safety_tip": {"en": re_.SAFETY_TIP[0], "bn": re_.SAFETY_TIP[1]},
            "features": {k: round(float(row[k]), 3) for k in re_.FEATURES}}


@app.get("/customers/{customer_id}/profile")
def profile(customer_id: str):
    prep = pl.prepare(_raw)
    if customer_id not in set(prep.sender_id):
        raise HTTPException(404, "Unknown customer")
    return en.json_safe(pl.customer_profile(prep, customer_id, prep.timestamp.max() + pd.Timedelta(seconds=1)))
