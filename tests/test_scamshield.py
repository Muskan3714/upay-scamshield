"""Run from the project root:  pytest -q"""
import json
import os
import sys

import pandas as pd
import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
os.chdir(ROOT)

import engines as en  # noqa: E402
import mule_network as mn  # noqa: E402
import pipeline as pl  # noqa: E402
import risk_engine as re_  # noqa: E402
from features import FEATURES  # noqa: E402

RAW = pd.read_csv("data/transactions_raw.csv")


def _row(**kw):
    base = dict(amount=1200, amount_ratio=1.1, hour=14, outside_usual_hours=0, is_new_recipient=0,
                recipient_account_age_days=900, recipient_unique_senders_24h=1, user_txns_last_1h=0,
                device_changed=0, new_location=0, on_active_call=0, user_tenure_days=700)
    base.update(kw)
    return pd.Series(base)


def _network():
    w = mn.find_mules(pd.read_parquet("data/scored_all.parquet"))
    rings = mn.find_rings(w, RAW.rename(columns={"sender_id": "from_wallet", "receiver_id": "to_wallet"}))
    return w, rings, {m: r["ring_id"] for r in rings for m in r["mules"]}


# ---------- data and pipeline ----------
def test_raw_log_has_no_labels_and_validates():
    assert pl.validate(RAW) == []
    assert "is_fraud" not in RAW.columns and "scam_type" not in RAW.columns


def test_validate_catches_bad_input():
    bad = RAW.head(10).drop(columns=["amount"])
    assert any("amount" in p for p in pl.validate(bad))


def test_point_in_time_no_future_leakage():
    """Features of early transfers must not change when later transfers are added."""
    head = RAW.head(3000)
    a = pl.build_features(head)
    b = pl.build_features(RAW.head(6000)).head(3000)
    assert (a[FEATURES].values == b[FEATURES].values).all()


def test_live_scoring_matches_batch_features():
    """The API's live path (FeatureState.peek) gives exactly the batch features."""
    prep = pl.prepare(RAW)
    _, state = pl.run(prep.iloc[:-1])
    last = prep.iloc[-1]
    live = state.peek(last.timestamp, last.sender_id, last.receiver_id, last.amount, last.device_id, last.district,
                      last.on_active_call, last.sender_created_at, last.receiver_created_at)
    batch = pl.build_features(RAW).iloc[-1]
    for k in FEATURES:
        assert abs(float(live[k]) - float(batch[k])) < 0.01, k


def test_day_first_dates_and_data_quality_notes():
    small = RAW.head(200)[pl.REQUIRED].copy()
    small["timestamp"] = pd.to_datetime(small.timestamp).dt.strftime("%d/%m/%Y %H:%M")
    assert pl.validate(small) == []
    assert len(pl.data_quality(small)) >= 2


# ---------- models ----------
def test_model_beats_rule_baseline_on_future_data():
    m = json.load(open("model/metrics.json"))
    assert m["roc_auc"] > 0.9
    assert m["ai_system"]["scam_recall"] > m["rule_baseline"]["scam_recall"]


def test_normal_transfer_allowed():
    model, r = re_.load_model(), _row()
    p, _ = re_.score(model, pd.DataFrame([r]))
    assert re_.decide(float(p[0]), r)[0] == "ALLOW"


def test_phone_scam_flagged_with_reasons():
    model = re_.load_model()
    r = _row(amount=6000, amount_ratio=5.0, is_new_recipient=1, recipient_account_age_days=12,
             recipient_unique_senders_24h=23, on_active_call=1)
    p, c = re_.score(model, pd.DataFrame([r]))
    assert re_.decide(float(p[0]), r)[0] in ("WARN", "HOLD")
    assert len(re_.explain(r, c.iloc[0])) >= 1


def test_business_rule_independent_of_model():
    r = _row(device_changed=1, user_txns_last_1h=4)
    assert re_.decide(0.0, r)[0] == "HOLD"


def test_anomaly_model_flags_never_seen_pattern():
    f = re_.load_iforest()
    weird = _row(amount=20000, amount_ratio=15.0, hour=4, outside_usual_hours=1, user_txns_last_1h=8, new_location=1)
    a = re_.anomaly(f, pd.DataFrame([_row(), weird]))
    assert a[1] > a[0] and a[1] >= re_.ANOMALY_THRESHOLD


def test_anomaly_helps_on_unseen_scam_type():
    m = json.load(open("model/metrics.json"))["novel_scam_test_account_takeover_recall"]
    assert m["classifier_plus_anomaly"] > m["classifier_only"]


def test_mule_network_finds_rings_without_flagging_shops():
    w, rings, _ = _network()
    roles = pd.read_csv("data/wallet_roles_ground_truth.csv").set_index("wallet_id").role
    assert len(rings) >= 10
    assert not any(roles.get(x) == "shop" for x in w.index[w.suspected_mule])
    assert all(roles.get(r["collector"]) == "collector" for r in rings)


# ---------- engines and cases ----------
def test_profile_comparison_flags_deviations_from_own_baseline():
    prof = dict(usual_amount=1000, active_start=9, active_end=21, devices="DEV-AAAA", home_district="Dhaka",
                known_recipients=5)
    normal = en.profile_comparison(_row(amount=1100, device_id="DEV-AAAA", district="Dhaka"), prof)
    odd = en.profile_comparison(_row(amount=9000, hour=3, outside_usual_hours=1, device_changed=1, new_location=1,
                                     device_id="DEV-BBBB", district="Sylhet"), prof)
    assert not any(r["unusual"] for r in normal)
    assert sum(r["unusual"] for r in odd) >= 4


def test_engine_panel_counts_agreement():
    w, rings, ring_of = _network()
    takeover = _row(amount=15000, amount_ratio=10, hour=2, outside_usual_hours=1, device_changed=1, new_location=1,
                    user_txns_last_1h=3, is_new_recipient=1)
    assert en.engine_panel(0.95, 0.999, takeover, rings[0]["mules"][0], w, ring_of)[1] == 4
    assert en.engine_panel(0.01, 0.2, _row(), None, w, ring_of)[1] == 0


def test_case_workflow_no_duplicates_and_audit_and_pdf():
    import cases as cs
    store = []
    ev = dict(what="Test ৳1,000 transfer", why=["reason"], next="hold")
    c1, new1 = cs.create_case(store, "Transaction", "T1", "test", "Critical", ev)
    _, new2 = cs.create_case(store, "Transaction", "T1", "test", "Critical", ev)
    assert new1 and not new2 and len(store) == 1
    cs.update_status(c1, "In progress", "analyst")
    cs.add_note(c1, "called customer", "analyst")
    assert [a["action"] for a in c1["audit"]] == ["Case created", "Status changed", "Note added"]
    assert cs.pdf_report(c1)[:4] == b"%PDF"


# ---------- API ----------
def test_api_scores_live_transfers():
    pytest.importorskip("fastapi")
    pytest.importorskip("httpx")
    from fastapi.testclient import TestClient
    import api
    c = TestClient(api.app)
    assert c.get("/health").json()["status"] == "ok"
    cust = api._raw.sender_id.value_counts().index[0]
    prof = c.get(f"/customers/{cust}/profile").json()
    ok = c.post("/score", json=dict(sender_id=cust, receiver_id=api._raw[api._raw.sender_id == cust].receiver_id.iloc[-1],
                                     amount=prof["usual_amount"], device_id=prof["devices"].split(",")[0],
                                     district=prof["home_district"], timestamp="2026-09-29 14:00:00")).json()
    bad = c.post("/score", json=dict(sender_id=cust, receiver_id="W00001", amount=prof["usual_amount"] * 10,
                                      device_id="DEV-NEW1", district="Bandarban", timestamp="2026-09-29 03:00:00")).json()
    assert ok["decision"] == "ALLOW" and bad["decision"] == "HOLD"


def test_previous_dataset_kept_and_scorable():
    """Dataset B (the previous synthetic dataset) is kept and can be scored by the current models."""
    prev = pd.read_csv("data/previous/transactions.csv")
    assert set(FEATURES) <= set(prev.columns) and len(prev) == 60000
    sc = re_.score_frame(re_.load_model(), re_.load_iforest(), prev.head(5000))
    assert set(sc.decision.unique()) <= {"ALLOW", "WARN", "HOLD"}


def test_dataset_b_unlabelled_log_with_phone_ids():
    """Someone's own log (phone-style IDs, day-first dates, no labels) builds a working Dataset B."""
    import workspace as wsp
    raw = RAW.tail(20000).reset_index(drop=True)
    ids = pd.Series(pd.concat([raw.sender_id, raw.receiver_id]).unique())
    mp = dict(zip(ids, ["01" + str(7000000000 + i)[1:] for i in range(len(ids))]))
    log = pd.DataFrame({"txn_id": "TX" + raw.index.astype(str),
                        "timestamp": pd.to_datetime(raw.timestamp).dt.strftime("%d/%m/%Y %H:%M"),
                        "sender_id": raw.sender_id.map(mp), "receiver_id": raw.receiver_id.map(mp),
                        "amount": raw.amount.astype(str), "device_id": raw.device_id, "district": raw.district})
    log.to_csv("/tmp/_b_test.csv", index=False)
    try:
        m = wsp.build_b(wsp.read_log("/tmp/_b_test.csv"), "TEST")
        assert m["mode"] == "demo_classifier" and wsp.exists("TEST")
        scored = pd.read_parquet(wsp.paths("TEST")["test"])
        assert scored.user_id.str.startswith("01").all()          # leading zeros kept
        assert set(scored.decision.unique()) <= {"ALLOW", "WARN", "HOLD"}
    finally:
        wsp.delete("TEST")


def test_dataset_b_trains_new_model_when_labels_exist():
    import workspace as wsp
    gt = pd.read_csv("data/ground_truth.csv")
    log = RAW.merge(gt[["txn_id", "is_fraud"]], on="txn_id").tail(40000)
    try:
        m = wsp.build_b(log, "TEST")
        assert m["mode"] == "trained" and m["roc_auc"] > 0.8
        assert m["ai_system"]["scam_recall"] > m["rule_baseline"]["scam_recall"]
    finally:
        wsp.delete("TEST")
