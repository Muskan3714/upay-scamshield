"""
risk_engine.py — scoring, explanation and decision policy.

Design (per hackathon architecture guidance):
  1. ML model     -> probability that a transfer is a scam (XGBoost)
  2. Explanation  -> per-feature SHAP contributions (XGBoost pred_contribs) turned into plain-language reasons
  3. Policy       -> business rules + thresholds kept SEPARATE from the model, so upay can tune them
The model never blocks money on its own: HIGH risk = hold for user re-confirmation / human review.
"""
import json
import os

import joblib

import numpy as np
import pandas as pd
import xgboost as xgb

from features import FEATURES

HERE = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(HERE, "model", "model.json")
IFOREST_PATH = os.path.join(HERE, "model", "iforest.joblib")

# Decision thresholds (business policy, not ML)
WARN_THRESHOLD = 0.30
HOLD_THRESHOLD = 0.70
ANOMALY_THRESHOLD = 0.99   # top 1% most unusual transfers get a WARN even if the classifier is unsure


def load_model(path=MODEL_PATH):
    model = xgb.XGBClassifier()
    model.load_model(path)
    return model


def fit_iforest(train_df: pd.DataFrame, seed=7):
    """Unsupervised behavioural anomaly model: learns what normal transfers look like (no labels used)."""
    from sklearn.ensemble import IsolationForest
    X = train_df[FEATURES].astype(float)
    model = IsolationForest(n_estimators=300, contamination="auto", random_state=seed).fit(X)
    raw = -model.score_samples(X)                      # higher = more unusual
    q = np.quantile(raw, np.linspace(0, 1, 1001))      # used to turn raw scores into a 0-1 percentile
    return {"model": model, "q": q}


def load_iforest(path=IFOREST_PATH):
    try:
        return joblib.load(path)
    except Exception:  # e.g. scikit-learn version mismatch on a new server: refit next to the saved file
        folder = os.path.dirname(path)
        feats = os.path.join(folder, "..", "data", "features_all.parquet") if folder.endswith("model") else None
        if feats and os.path.exists(feats):
            return fit_iforest(pd.read_parquet(feats))
        import pipeline as pl                       # workspace: rebuild features from its own raw log
        return fit_iforest(pl.build_features(pd.read_csv(os.path.join(folder, "raw.csv"))))


def anomaly(bundle, df: pd.DataFrame):
    """Percentile (0-1) of how unusual each transfer is compared with normal behaviour."""
    raw = -bundle["model"].score_samples(df[FEATURES].astype(float))
    return np.interp(raw, bundle["q"], np.linspace(0, 1, len(bundle["q"])))


def score(model, df: pd.DataFrame):
    """Returns (probabilities, shap_contributions DataFrame)."""
    X = df[FEATURES].astype(float)
    proba = model.predict_proba(X)[:, 1]
    contribs = model.get_booster().predict(xgb.DMatrix(X), pred_contribs=True)
    contribs = pd.DataFrame(contribs[:, :-1], columns=FEATURES, index=df.index)  # drop bias column
    return proba, contribs


def _reason(feature, row):
    """Plain-language reason (English, Bangla) for a feature that raised risk."""
    v = row[feature]
    if feature == "is_new_recipient" and v == 1:
        return ("You have never sent money to this number before.",
                "এই নম্বরে আপনি আগে কখনো টাকা পাঠাননি।")
    if feature == "recipient_account_age_days" and v < 180:
        return (f"The receiving account is very new ({int(v)} days old).",
                f"প্রাপকের অ্যাকাউন্টটি খুবই নতুন ({int(v)} দিন আগে খোলা)।")
    if feature == "recipient_unique_senders_24h" and v >= 5:
        return (f"{int(v)} different people sent money to this account in the last 24 hours.",
                f"গত ২৪ ঘণ্টায় {int(v)} জন আলাদা মানুষ এই অ্যাকাউন্টে টাকা পাঠিয়েছে।")
    if feature == "amount_ratio" and v >= 1.5:
        return (f"This amount is {v:.1f}x your usual transfer.",
                f"এই পরিমাণ আপনার স্বাভাবিক লেনদেনের {v:.1f} গুণ।")
    if feature == "amount" and v >= 5000:
        return (f"Large amount: ৳{v:,.0f}.", f"বড় অঙ্কের লেনদেন: ৳{v:,.0f}।")
    if feature == "outside_usual_hours" and v == 1:
        return (f"This is outside the time you normally use upay ({int(row['hour']):02d}:00).",
                f"আপনি সাধারণত এই সময়ে লেনদেন করেন না ({int(row['hour']):02d}:00)।")
    if feature == "hour" and (v <= 5 or v >= 23):
        return (f"Unusual time of day ({int(v):02d}:00).",
                f"অস্বাভাবিক সময়ে লেনদেন ({int(v):02d}:00)।")
    if feature == "device_changed" and v == 1:
        return ("Your account was just logged in from a new device.",
                "আপনার অ্যাকাউন্টে নতুন একটি ডিভাইস থেকে লগইন হয়েছে।")
    if feature == "new_location" and v == 1:
        return ("This transfer is being made from a location you have never used before.",
                "এমন একটি জায়গা থেকে লেনদেন হচ্ছে যেখান থেকে আপনি আগে কখনো লেনদেন করেননি।")
    if feature == "on_active_call" and v == 1:
        return ("You are on a phone call while sending money.",
                "টাকা পাঠানোর সময় আপনি ফোন কলে আছেন।")
    if feature == "user_txns_last_1h" and v >= 2:
        return (f"{int(v)} transfers from your account in the last hour.",
                f"গত এক ঘণ্টায় আপনার অ্যাকাউন্ট থেকে {int(v)}টি লেনদেন হয়েছে।")
    if feature == "user_tenure_days" and v < 180:
        return ("Your account is relatively new.", "আপনার অ্যাকাউন্টটি তুলনামূলক নতুন।")
    return None


def explain(row: pd.Series, contrib_row: pd.Series, top_k=3):
    """Top features that pushed risk UP, as (feature, contribution, en, bn)."""
    out = []
    for feat, c in contrib_row.sort_values(ascending=False).items():
        if c <= 0.05 or len(out) >= top_k:
            break
        r = _reason(feat, row)
        if r:
            out.append((feat, float(c), r[0], r[1]))
    return out


def business_rules(row: pd.Series):
    """Deterministic safety rules, independent of the ML model. Returns list of triggered rule names."""
    rules = []
    if row["on_active_call"] == 1 and row["is_new_recipient"] == 1 and row["amount"] >= 5000:
        rules.append("CALL_COACHING_GUARD")   # classic phone-coached scam pattern
    if row["device_changed"] == 1 and row.get("new_location", 0) == 1 and row["amount_ratio"] >= 3:
        rules.append("NEW_DEVICE_NEW_LOCATION")  # takeover pattern: new phone, new place, big amount
    if row["device_changed"] == 1 and row["user_txns_last_1h"] >= 3:
        rules.append("NEW_DEVICE_VELOCITY")   # possible account takeover drain
    return rules


def decide(prob: float, row: pd.Series, anomaly_pct: float = 0.0):
    """Combine classifier score, anomaly score and business rules into an action."""
    rules = business_rules(row)
    if anomaly_pct >= ANOMALY_THRESHOLD:
        rules.append("UNUSUAL_BEHAVIOUR")     # very different from normal behaviour, even if it matches no known scam
    if prob >= HOLD_THRESHOLD or "NEW_DEVICE_VELOCITY" in rules or "NEW_DEVICE_NEW_LOCATION" in rules:
        level = "HOLD"
    elif prob >= WARN_THRESHOLD or rules:
        level = "WARN"
    else:
        level = "ALLOW"
    return level, rules


ACTIONS = {
    "ALLOW": ("Transfer proceeds normally.", "লেনদেন স্বাভাবিকভাবে সম্পন্ন হবে।"),
    "WARN": ("Show a warning with reasons; user must confirm to continue.",
             "কারণসহ সতর্কবার্তা দেখানো হবে; চালিয়ে যেতে ব্যবহারকারীকে নিশ্চিত করতে হবে।"),
    "HOLD": ("Pause transfer; user re-verifies (PIN + cooling period) and case goes to the fraud analyst queue.",
             "লেনদেন সাময়িক স্থগিত; পুনরায় যাচাই করতে হবে এবং কেসটি ফ্রড অ্যানালিস্টের কাছে যাবে।"),
}

SAFETY_TIP = ("upay never asks for your PIN or OTP. If someone on the phone is telling you to send money, "
              "hang up and verify first.",
              "উপায় কখনো আপনার পিন বা ওটিপি চায় না। ফোনে কেউ টাকা পাঠাতে বললে কল কেটে আগে যাচাই করুন।")


UNUSUAL_REASON = ("This transfer is very different from normal behaviour (top 1% most unusual).",
                  "এই লেনদেনটি স্বাভাবিক আচরণ থেকে অনেক আলাদা।")


def load_metrics():
    p = os.path.join(HERE, "model", "metrics.json")
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def score_frame(model, iforest, feats: pd.DataFrame) -> pd.DataFrame:
    """Score a whole table of transfers at once (same logic as decide(), vectorised)."""
    X = feats[FEATURES].astype(float)
    out = feats.copy()
    out["risk_score"] = model.predict_proba(X)[:, 1].round(4)
    out["anomaly_pct"] = anomaly(iforest, feats).round(4)
    coach = (X.on_active_call == 1) & (X.is_new_recipient == 1) & (X.amount >= 5000)
    dnl = (X.device_changed == 1) & (X.new_location == 1) & (X.amount_ratio >= 3)
    dvel = (X.device_changed == 1) & (X.user_txns_last_1h >= 3)
    unusual = out.anomaly_pct >= ANOMALY_THRESHOLD
    out["rules"] = [", ".join(n for n, v in zip(["CALL_COACHING_GUARD", "NEW_DEVICE_NEW_LOCATION",
                                                  "NEW_DEVICE_VELOCITY", "UNUSUAL_BEHAVIOUR"], flags) if v)
                    for flags in zip(coach, dnl, dvel, unusual)]
    hold = (out.risk_score >= HOLD_THRESHOLD) | dnl | dvel
    warn = (out.risk_score >= WARN_THRESHOLD) | coach | unusual
    out["decision"] = np.where(hold, "HOLD", np.where(warn, "WARN", "ALLOW"))
    return out
