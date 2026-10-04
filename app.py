"""
app.py — upay ScamShield prototype (Streamlit).
Run:  streamlit run app.py
"""
import os
import subprocess
import sys

import html as _html

import numpy as np
import pandas as pd
import streamlit as st

import cases as cs
import engines as en
import mule_network as mn
import business as bz
import risk_engine as re_
from icons import ic

st.set_page_config(page_title="upay ScamShield", page_icon=":material/shield:", layout="wide")


def dl(*args, **kw):
    """Download button with a vector icon."""
    return st.download_button(*args, icon=":material/download:", **kw)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600;700&family=Space+Grotesk:wght@400;600;700&display=swap');
:root { --bg:#040A16; --panel:#0A1730; --panel2:#0E2142; --line:#1B3A66; --blue:#2F8CFF; --blue2:#0B5CAD;
        --yel:#FFD200; --txt:#E6EEF8; --mut:#8EA3BF; --ok:#22D38A; --warn:#FFB020; --bad:#FF4D5E;
        --mono:'JetBrains Mono', ui-monospace, monospace; --head:'Space Grotesk', 'Segoe UI', sans-serif; }
/* animated cyber grid background */
.stApp { background:
   radial-gradient(1200px 600px at 85% -10%, rgba(47,140,255,.18), transparent 60%),
   radial-gradient(900px 500px at -10% 110%, rgba(255,210,0,.08), transparent 60%),
   linear-gradient(rgba(47,140,255,.06) 1px, transparent 1px) 0 0/36px 36px,
   linear-gradient(90deg, rgba(47,140,255,.06) 1px, transparent 1px) 0 0/36px 36px, var(--bg);
   animation: gridmove 18s linear infinite; }
@keyframes gridmove { to { background-position: 0 0, 0 0, 0 36px, 36px 0, 0 0; } }
header[data-testid="stHeader"] { background: transparent; }
.block-container { padding-top: 2.6rem; max-width: 1350px; }
html, body, .stApp, p, li, label, .stMarkdown { font-family: var(--head); }
h1, h2, h3, h4 { font-family: var(--head) !important; color: var(--txt) !important; letter-spacing:.2px; }
code, .mono { font-family: var(--mono) !important; }
/* boot line */
.boot { font-family: var(--mono); font-size:.72rem; color: var(--blue); letter-spacing:2px; margin-bottom:6px;
        white-space:nowrap; overflow:hidden; width:0; animation: type 2.4s steps(60) .2s forwards; }
.boot:after { content:"█"; animation: blink 1s step-end infinite; color: var(--yel); }
@keyframes type { to { width: 60ch; } } @keyframes blink { 50% { opacity:0; } }
/* hero */
.hero { position:relative; overflow:hidden; border-radius:22px; padding:24px 28px; margin-bottom:10px;
        background: linear-gradient(120deg, rgba(10,23,48,.95), rgba(11,92,173,.55));
        border:1px solid var(--line); box-shadow: 0 0 0 1px rgba(47,140,255,.15), 0 20px 60px rgba(0,0,0,.45);
        display:flex; align-items:center; gap:22px; }
.hero:before { content:""; position:absolute; inset:0; background: linear-gradient(transparent 0, rgba(47,140,255,.10) 50%, transparent 100%);
        height:40%; animation: scan 5s linear infinite; pointer-events:none; }
@keyframes scan { from { transform: translateY(-120%); } to { transform: translateY(320%); } }
.hero .badge { position:relative; width:78px; height:78px; border-radius:50%; flex-shrink:0; display:flex; align-items:center;
        justify-content:center; font-size:38px; background: radial-gradient(circle, #FFE45C, var(--yel)); box-shadow:0 0 30px rgba(255,210,0,.45); }
.hero .badge:after { content:""; position:absolute; inset:-8px; border-radius:50%; border:2px solid rgba(255,210,0,.6);
        animation: ring 2.4s ease-out infinite; }
@keyframes ring { from { transform:scale(.9); opacity:1; } to { transform:scale(1.35); opacity:0; } }
.hero h1, .hero h1 * {
    color: white !important;
}

.hero h1 span, .hero h1 span * {
    color: var(--yel) !important;
}

.hero h1 .upay-name {
    color: #ffffff !important;
}
.hero p { margin:2px 0 8px 0; color:#C9D8EC; }
.chip { display:inline-block; font-family:var(--mono); font-size:.7rem; font-weight:700; letter-spacing:1px; border-radius:999px;
        padding:4px 11px; margin:2px 6px 2px 0; border:1px solid var(--line); background:rgba(4,10,22,.55); color:var(--txt); }
.chip.y { background: var(--yel); color:#06306B; border-color: var(--yel); }
.dot { display:inline-block; width:8px; height:8px; border-radius:50%; background: var(--ok); margin-right:6px;
       box-shadow:0 0 0 0 rgba(34,211,138,.7); animation: pulse 1.6s infinite; vertical-align:middle; }
@keyframes pulse { 70% { box-shadow:0 0 0 9px rgba(34,211,138,0); } 100% { box-shadow:0 0 0 0 rgba(34,211,138,0); } }
/* live ticker */
.ticker { overflow:hidden; white-space:nowrap; border:1px solid var(--line); border-radius:12px; background: rgba(10,23,48,.85);
          margin: 0 0 14px 0; position:relative; }
.ticker .lbl { position:absolute; left:0; top:0; bottom:0; z-index:2; display:flex; align-items:center; padding:0 12px;
          font-family:var(--mono); font-size:.7rem; font-weight:700; letter-spacing:1.5px; background: var(--bad); color:white; }
.ticker .track { display:inline-block; padding:8px 0 8px 150px; animation: tick 180s linear infinite; font-family:var(--mono); font-size:.76rem; color:var(--mut); }
.ticker .track b { color: var(--txt); } .ticker .track .h { color: var(--bad); font-weight:700; } .ticker .track .w { color: var(--warn); font-weight:700; }
@keyframes tick { from { transform: translateX(0); } to { transform: translateX(-50%); } }
/* KPI strip with count-up */
@property --n { syntax:'<integer>'; initial-value:0; inherits:false; }
.kpis { display:grid; grid-template-columns: repeat(5, 1fr); gap:10px; margin-bottom:14px; }
.kpi { background: linear-gradient(160deg, var(--panel2), var(--panel)); border:1px solid var(--line); border-radius:14px; padding:12px 14px; }
.kpi .k { font-family:var(--mono); font-size:.66rem; color:var(--mut); letter-spacing:1.5px; }
.kpi .v { font-family:var(--head); font-size:1.65rem; font-weight:700; color:white; }
.kpi .v.c { animation: count 2s ease-out forwards; counter-reset: n var(--n); }
.kpi .v.c:after { content: counter(n); }
@keyframes count { from { --n: 0; } }
.kpi .s { font-size:.72rem; color: var(--ok); font-family:var(--mono); }
/* tabs */
.stTabs [data-baseweb="tab-list"] { gap:6px; border-bottom:1px solid var(--line); }
.stTabs [data-baseweb="tab"] { background: rgba(10,23,48,.8); border:1px solid var(--line); border-bottom:none;
        border-radius:10px 10px 0 0; padding:8px 16px; font-family:var(--mono); font-size:.78rem; letter-spacing:.5px; color:var(--mut); }
.stTabs [aria-selected="true"] { background: linear-gradient(180deg, var(--blue2), #0A3F7A) !important; color:white !important;
        box-shadow: 0 -2px 0 var(--yel) inset; }
.section-title { font-family:var(--mono); color: var(--yel); font-weight:700; font-size:.9rem; letter-spacing:2px;
        text-transform:uppercase; margin: 6px 0 10px 0; }
.section-title:before { content:"// "; color: var(--blue); }
/* metrics + inputs */
[data-testid="stMetric"] { background: linear-gradient(160deg, var(--panel2), var(--panel)); border:1px solid var(--line); border-radius:14px; padding:12px 16px; }
[data-testid="stMetricLabel"] p { font-family:var(--mono); font-size:.7rem !important; letter-spacing:1.2px; color:var(--mut) !important; text-transform:uppercase; }
[data-testid="stMetricValue"] { color:white; font-weight:700; }
[data-testid="stExpander"] { border:1px solid var(--line) !important; border-radius:12px !important; background: rgba(10,23,48,.6); }
.stButton button, .stDownloadButton button, [data-testid="stFormSubmitButton"] button { border-radius:10px; font-family:var(--mono); font-weight:700; letter-spacing:.5px; }
/* phone frame for the customer view */
.phone { border-radius:34px; padding:12px; background: linear-gradient(160deg,#1a2233,#05080f); border:1px solid #2a3550;
         box-shadow: 0 25px 60px rgba(0,0,0,.55), 0 0 0 1px rgba(255,255,255,.04) inset; }
.phone .notch { width:110px; height:14px; border-radius:0 0 12px 12px; background:#05080f; margin:-12px auto 2px auto; }
.phone .bar { display:flex !important; justify-content:space-between; align-items:center; box-sizing:border-box;
         height:30px !important; min-height:30px; line-height:1.4 !important; font-family:var(--mono); font-size:.68rem;
         color:var(--mut); padding:0 14px; margin-bottom:6px; overflow:visible; }
.phone .bar span { display:inline-block !important; line-height:1.4 !important; height:auto !important; white-space:nowrap; }
.phone .bar b { color: var(--yel); }
/* decision card */
.card { border-radius:22px; padding:18px 20px; margin-bottom:6px; position:relative; color: var(--txt); background: var(--panel); }
.card.ALLOW { border:1.5px solid var(--ok); box-shadow: 0 0 24px rgba(34,211,138,.25); }
.card.WARN  { border:1.5px solid var(--warn); box-shadow: 0 0 26px rgba(255,176,32,.30); }
.card.HOLD  { border:1.5px solid var(--bad); animation: alarm 1.6s ease-in-out infinite; }
@keyframes alarm { 0%,100% { box-shadow: 0 0 18px rgba(255,77,94,.25); } 50% { box-shadow: 0 0 38px rgba(255,77,94,.65); } }
.card .lvl { font-size:1.55rem; font-weight:700; font-family: var(--head); }
.card.ALLOW .lvl { color: var(--ok); } .card.WARN .lvl { color: var(--warn); } .card.HOLD .lvl { color: var(--bad); }
.card .score { float:right; font-size:1.6rem; font-weight:700; text-align:right; line-height:1.1; font-family:var(--mono); }
.card .score small { color: var(--mut); }
.reason { background: rgba(255,255,255,.04); border:1px solid var(--line); border-left:3px solid var(--yel); color:var(--txt);
          border-radius:10px; padding:8px 12px; margin:7px 0; animation: slidein .5s ease both; }
.reason:nth-child(2) { animation-delay:.1s } .reason:nth-child(3) { animation-delay:.2s } .reason:nth-child(4) { animation-delay:.3s }
@keyframes slidein { from { opacity:0; transform: translateX(14px); } to { opacity:1; transform:none; } }
.reason small { color: var(--mut); }
.tip { background: var(--yel); color:#06306B; border-radius:10px; padding:9px 13px; margin-top:10px; font-weight:700; }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<style>
.eng-head { display:flex; justify-content:space-between; align-items:center; margin:16px 0 8px 0; }
.eng-head .t { font-family:var(--mono); color: var(--yel); font-weight:700; letter-spacing:2px; font-size:.85rem; }
.agree { border-radius:999px; padding:4px 14px; font-family:var(--mono); font-weight:700; font-size:.78rem; letter-spacing:1px; }
.agree.hi { background: var(--bad); color:white; box-shadow:0 0 18px rgba(255,77,94,.5); }
.agree.mid { background: var(--warn); color:#1a1200; } .agree.lo { background: rgba(34,211,138,.15); color: var(--ok); border:1px solid var(--ok); }
.eng-grid { display:grid; grid-template-columns: repeat(2, 1fr); gap:10px; }
.eng { background: linear-gradient(160deg, var(--panel2), var(--panel)); border:1px solid var(--line); border-radius:14px; padding:12px 14px; }
.eng.on { border-color: var(--bad); box-shadow: 0 0 18px rgba(255,77,94,.18) inset; }
.eng .nm { font-weight:700; color:white; } .eng .mt { font-family:var(--mono); font-size:.68rem; color: var(--mut); letter-spacing:.5px; }
.eng .chip2 { float:right; font-family:var(--mono); font-size:.66rem; font-weight:700; border-radius:999px; padding:2px 9px; letter-spacing:1px; }
.eng.on .chip2 { background: var(--bad); color:white; } .eng .chip2.off { background: rgba(34,211,138,.12); color: var(--ok); border:1px solid rgba(34,211,138,.5); }
.bar { height:7px; background: rgba(255,255,255,.07); border-radius:6px; margin:9px 0 6px 0; overflow:hidden; }
.bar > div { height:100%; border-radius:6px; background: linear-gradient(90deg, var(--blue), #7FC1FF); animation: grow 1.1s ease-out both; }
.eng.on .bar > div { background: linear-gradient(90deg, var(--warn), var(--bad)); }
@keyframes grow { from { width:0 !important; } }
.eng .nt { font-size:.82rem; color: #C9D8EC; }
table.prof { width:100%; border-collapse:separate; border-spacing:0; font-size:.86rem; border:1px solid var(--line); border-radius:14px; overflow:hidden; }
table.prof th { background: #0B2A55; color: var(--yel); text-align:left; padding:8px 10px; font-family:var(--mono); font-size:.7rem; letter-spacing:1.5px; text-transform:uppercase; }
table.prof td { padding:8px 10px; border-top:1px solid var(--line); color: var(--txt); background: rgba(10,23,48,.7); }
table.prof tr.u td { background: rgba(255,77,94,.09); }
.st { font-family:var(--mono); border-radius:999px; padding:2px 9px; font-size:.66rem; font-weight:700; white-space:nowrap; letter-spacing:1px; }
.st.u { background: var(--bad); color:white; } .st.n { background: rgba(34,211,138,.12); color: var(--ok); border:1px solid rgba(34,211,138,.45); }
.casebox { background: linear-gradient(160deg, var(--panel2), var(--panel)); border:1px solid var(--line); border-radius:14px; padding:14px 16px; margin-bottom:10px; color:var(--txt); }
.pri { font-family:var(--mono); border-radius:999px; padding:2px 10px; font-size:.7rem; font-weight:700; letter-spacing:1px; }
.pri.HOLD, .pri.Critical { background: var(--bad); color:white; } .pri.WARN, .pri.High { background: var(--warn); color:#1a1200; }
.pri.ALLOW, .pri.Low { background: rgba(34,211,138,.15); color: var(--ok); }
section[data-testid="stSidebar"] { background: linear-gradient(180deg, #071226 0%, #040A16 100%); border-right:1px solid var(--line); }
section[data-testid="stSidebar"] .block-container, section[data-testid="stSidebar"] > div { padding-top: 1rem; }
.sb-logo { display:flex; gap:10px; align-items:center; margin-bottom:14px; }
.sb-badge { width:42px; height:42px; border-radius:50%; background: var(--yel); display:flex; align-items:center; justify-content:center;
            font-size:22px; box-shadow:0 0 18px rgba(255,210,0,.45); }
.sb-t { font-weight:700; font-size:1.15rem; color:white; } .sb-t span { color: var(--yel); }
.sb-s { font-family:var(--mono); font-size:.6rem; letter-spacing:2px; color: var(--mut); }
section[data-testid="stSidebar"] [role="radiogroup"] { gap:4px; }
section[data-testid="stSidebar"] [role="radiogroup"] label { width:100%; padding:9px 12px; border-radius:10px; border:1px solid transparent;
            transition: all .15s ease; font-family:var(--mono); font-size:.8rem; }
section[data-testid="stSidebar"] [role="radiogroup"] label:hover { background: rgba(47,140,255,.10); border-color: var(--line); }
section[data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) { background: linear-gradient(90deg, rgba(47,140,255,.28), rgba(47,140,255,.05));
            border-color: var(--blue); box-shadow: inset 3px 0 0 var(--yel); }
.sb-box { border:1px solid var(--line); border-radius:12px; padding:10px 12px; margin:12px 0; background: rgba(10,23,48,.7); }
.sb-h { font-family:var(--mono); font-size:.62rem; letter-spacing:2px; color: var(--yel); margin-bottom:6px; }
.sb-row { font-size:.78rem; color: var(--txt); margin:4px 0; } .sb-row b { float:right; color: var(--mut); font-weight:600; font-family:var(--mono); font-size:.68rem; }
.sb-kv { display:flex; justify-content:space-between; font-size:.78rem; color: var(--mut); margin:3px 0; } .sb-kv b { color: white; font-family:var(--mono); font-size:.74rem; }
.sb-foot { font-family:var(--mono); font-size:.6rem; color: var(--mut); letter-spacing:.5px; margin-top:10px; }
.ic { vertical-align:-3px; flex-shrink:0; }
.section-title .ic { color: var(--blue); margin-right:4px; }
.card .lvl .ic { vertical-align:-5px; margin-right:6px; }
.tip .ic { vertical-align:-3px; margin-right:4px; }
.card .trig { font-family:var(--mono); font-size:.66rem; letter-spacing:1px; color: var(--yel); margin-top:6px; }
.hero .badge .ic, .sb-badge .ic { vertical-align:middle; }
.ds { border:1px solid var(--line); border-radius:16px; padding:16px 18px; background: linear-gradient(160deg, var(--panel2), var(--panel)); height:100%; }
.ds h4 { margin:0 0 4px 0; } .ds .tag { font-family:var(--mono); font-size:.62rem; letter-spacing:1.5px; color: var(--yel); }
.ds p { color:#C9D8EC; font-size:.86rem; }
</style>
""", unsafe_allow_html=True)


import pipeline as pl

NEEDED = [re_.MODEL_PATH, "data/transactions_raw.csv", "data/test_scored.parquet", "data/scored_all.parquet"]
if not all(os.path.exists(p) for p in NEEDED):
    with st.spinner("Building features and training models on the synthetic log (first run only, about a minute)..."):
        subprocess.run([sys.executable, "train.py"], check=True)


import workspace as wsp

# Dataset B is private to each browser session on a public server (one visitor's upload is never shown to another).
# An organisation running its own server can share one Dataset B built with `python workspace.py log.csv`
# by setting SCAMSHIELD_SHARED_B=1.
if "b_name" not in st.session_state:
    import uuid
    st.session_state.b_name = "B" if os.environ.get("SCAMSHIELD_SHARED_B") == "1" else f"B_{uuid.uuid4().hex[:10]}"
    wsp.cleanup(max_age_hours=12)          # remove other sessions' old uploads so the server disk never fills up
BN = st.session_state.b_name
if "ws" not in st.session_state:
    st.session_state.ws = "A"
if st.session_state.ws == "B" and not wsp.exists(BN):
    st.session_state.ws = "A"
WS = st.session_state.ws
WSN = "A" if WS == "A" else BN                 # folder name of the active dataset
WP = wsp.paths(WSN)
STAMP = os.path.getmtime(WP["metrics"])          # cache key: rebuilding Dataset B refreshes everything


@st.cache_resource
def get_model(ws, stamp):
    return re_.load_model(wsp.paths(ws)["model"])


@st.cache_resource
def get_iforest(ws, stamp):
    return re_.load_iforest(wsp.paths(ws)["iforest"])


@st.cache_resource(show_spinner="> SYNCHRONIZING_RISK_GRID: learning every customer's habits from the transaction log...")
def get_history(ws, stamp):
    raw = wsp.read_log(wsp.paths(ws)["raw"])
    _, state = pl.run(raw)
    return pl.prepare(raw), state


@st.cache_data
def get_test(ws=None, stamp=None):
    ws = ws or st.session_state.ws
    return pd.read_parquet(wsp.paths(ws)["test"])


@st.cache_data(show_spinner="> MAPPING_MULE_NETWORK...")
def get_network(ws, stamp):
    wallets = mn.find_mules(pd.read_parquet(wsp.paths(ws)["scored"]))
    raw = wsp.read_log(wsp.paths(ws)["raw"])
    rings = mn.find_rings(wallets, raw.rename(columns={"sender_id": "from_wallet", "receiver_id": "to_wallet"}))
    ring_of = {m: r["ring_id"] for r in rings for m in r["mules"]}
    return wallets, rings, ring_of


model, iforest = get_model(WSN, STAMP), get_iforest(WSN, STAMP)
hist, STATE = get_history(WSN, STAMP)
wallets, rings, ring_of = get_network(WSN, STAMP)
metrics = wsp.load_metrics(WSN)
_get_test = get_test
get_test = lambda: _get_test(WSN, STAMP)      # every page reads the active dataset's queue


def customer_ids(h):
    """Dataset A marks customers with U...; for your own data every sender counts as a customer."""
    s = h.sender_id
    return s[s.str.startswith("U")] if WS == "A" else s


DS_LABEL = "DATASET A · DEMO (SYNTHETIC)" if WS == "A" else (
    "DATASET B · YOUR DATA · " + ("MODEL TRAINED ON YOUR LABELS" if metrics.get("mode") == "trained" else "DEMO CLASSIFIER + YOUR ANOMALY MODEL"))
if "cases" not in st.session_state:
    st.session_state.cases = []
CASES = st.session_state.cases
ANALYST = "Fraud analyst (demo)"


# ---------------- helpers ----------------
def E(x):
    """Escape any text that came from data before it goes into HTML (blocks injected markup in uploaded CSVs)."""
    return _html.escape(str(x))


def engines_html(engs, n_flag):
    cls = "hi" if n_flag >= 3 else "mid" if n_flag >= 1 else "lo"
    h = (f'<div class="eng-head"><span class="t">// ENGINE_CONSENSUS</span>'
         f'<span class="agree {cls}">{n_flag}/4 ENGINES FLAG THIS</span></div><div class="eng-grid">')
    for e in engs:
        on = "on" if e["flagged"] else ""
        chip = '<span class="chip2">FLAGGED</span>' if e["flagged"] else '<span class="chip2 off">CLEAR</span>'
        h += (f'<div class="eng {on}">{chip}<div class="nm">{e["name"]}</div><div class="mt">{e["method"]}</div>'
              f'<div class="bar"><div style="width:{max(e["score"], 0.02) * 100:.0f}%"></div></div>'
              f'<div class="nt">{E(e["note"])}</div></div>')
    return h + "</div>"


def profile_html(rows, name=""):
    h = ('<table class="prof"><tr><th>Behaviour</th><th>Customer\'s usual</th><th>This transfer</th>'
         '<th>Finding</th></tr>')
    for r in rows:
        stt = '<span class="st u">UNUSUAL</span>' if r["unusual"] else '<span class="st n">NORMAL</span>'
        h += (f'<tr class="{"u" if r["unusual"] else ""}"><td><b>{E(r["dimension"])}</b></td><td>{E(r["baseline"])}</td>'
              f'<td>{E(r["this_transfer"])}</td><td>{stt} {E(r["deviation"])}</td></tr>')
    return h + "</table>"


def txn_evidence(r, prep, wl, r_of):
    """Everything an analyst needs for one transaction, also stored in the case when escalated."""
    df1 = pd.DataFrame([r])
    _, c = re_.score(model, df1)
    lvl, rl = re_.decide(float(r.risk_score), r, float(r.anomaly_pct))
    ring = r_of.get(r.recipient_id)
    engs, n_flag = en.engine_panel(float(r.risk_score), float(r.anomaly_pct), r, r.recipient_id, wl, r_of)
    if engs[3]["flagged"] and lvl == "ALLOW":
        lvl = "WARN"
    prof = en.profile_comparison(r, pl.customer_profile(prep, r.user_id, r.timestamp))
    why = [f"{en_} (model contribution +{k:.2f})" for _, k, en_, _ in re_.explain(r, c.iloc[0], top_k=4)]
    why += [f"Profile: {p['dimension'].lower()}: {p['deviation'].lower()}" for p in prof if p["unusual"]]
    if rl:
        why.append("Business rules triggered: " + ", ".join(rl))
    if ring:
        why.append(f"Receiving wallet {r.recipient_id} is a suspected mule wallet in {ring}")
    nxt = re_.ACTIONS[lvl][0] + (f" Also review all wallets in {ring} and hold their outgoing transfers." if ring else "")
    what = (f"Customer {r.user_id} sent ৳{r.amount:,.0f} to wallet {r.recipient_id} on "
            f"{pd.Timestamp(r.timestamp):%d %b %Y %H:%M} from {r.district} on device {r.device_id}. "
            f"Scam probability {r.risk_score:.0%}; more unusual than {r.anomaly_pct:.1%} of normal transfers.")
    return dict(level=lvl, what=what, why=why, next=nxt, engines=engs, n_flag=n_flag, profile=prof, ring=ring)


def escalate_button(kind, ref, title, priority, evidence, key):
    existing = cs.find_case(CASES, ref)
    if existing:
        st.success(f"Already escalated as **{existing['id']}** ({existing['status']}). Open the Cases tab to work on it.")
    elif st.button("Escalate to case", key=key, type="primary", icon=":material/create_new_folder:"):
        cs.create_case(CASES, kind, ref, title, priority, evidence, ANALYST)
        st.rerun()


def case_view(r, prep, wl, r_of, key_prefix):
    ev = txn_evidence(r, prep, wl, r_of)
    st.markdown(f'#### Case summary: {r.txn_id} &nbsp; <span class="pri {ev["level"]}">{ev["level"]}</span>',
                unsafe_allow_html=True)
    a1, a2 = st.columns([1, 1])
    with a1:
        st.markdown(f"**What happened:** {ev['what']}")
        st.markdown("**Why it is risky:**")
        for w in ev["why"] or ["No strong risk signals."]:
            st.markdown(f"- {w}")
        st.markdown(f"**What upay should do next:** {ev['next']}")
        escalate_button("Transaction", f"{WS}:{r.txn_id}", f"[Dataset {WS}] {ev['level']} transfer {r.txn_id} from {r.user_id}",
                        {"HOLD": "Critical", "WARN": "High", "ALLOW": "Low"}[ev["level"]],
                        {k: ev[k] for k in ("what", "why", "next", "engines", "profile")}, key=f"{key_prefix}_{r.txn_id}")
    with a2:
        st.markdown(engines_html(ev["engines"], ev["n_flag"]), unsafe_allow_html=True)
    st.markdown(f"**Customer {r.user_id}: this transfer vs. their own history before it**")
    st.markdown(profile_html(ev["profile"]), unsafe_allow_html=True)


def customer_result(row, rec_id, prof_for_table):
    """Score one transfer and render what the customer sees, the engines and the profile comparison."""
    df_one = pd.DataFrame([row])
    prob, contribs = re_.score(model, df_one)
    prob = float(prob[0])
    anom = float(re_.anomaly(iforest, df_one)[0])
    level, rules = re_.decide(prob, row, anom)
    engs, n_flag = en.engine_panel(prob, anom, row, rec_id, wallets, ring_of)
    if engs[3]["flagged"] and level == "ALLOW":       # known mule wallet: always warn the customer
        level, rules = "WARN", rules + ["KNOWN_MULE_WALLET"]
    reasons = re_.explain(row, contribs.iloc[0])
    if "UNUSUAL_BEHAVIOUR" in rules:
        reasons.append(("anomaly", anom, re_.UNUSUAL_REASON[0], re_.UNUSUAL_REASON[1]))
    if engs[3]["flagged"]:
        reasons.insert(0, ("network", 1.0, "This wallet has received money from many people in patterns linked to scams.",
                           "এই অ্যাকাউন্টে অনেক সন্দেহজনক লেনদেন এসেছে।"))
    reasons = reasons[:4]
    drivers = [e["name"] for e in engs if e["flagged"]] + [r_ for r_ in rules if r_ not in ("UNUSUAL_BEHAVIOUR", "KNOWN_MULE_WALLET")]
    icon = {"ALLOW": ic("check-circle", 26), "WARN": ic("alert", 26), "HOLD": ic("stop", 26)}[level]
    head = {"ALLOW": "Looks safe", "WARN": "সাবধান! Possible scam", "HOLD": "Transfer paused for your safety"}[level]
    html = (f'<div class="card {level}"><span class="score">{prob:.0%}<br><small style="font-size:.75rem;font-weight:600">'
            f'scam risk · unusual {anom:.1%}</small></span><div class="lvl">{icon} {level}</div><div>{head}</div>'
            + (f'<div class="trig">TRIGGERED BY: {" · ".join(d.upper() for d in drivers)}</div>' if level != "ALLOW" and drivers else ""))
    if level == "ALLOW":
        html += f'<div style="margin-top:8px">{re_.ACTIONS["ALLOW"][1]}<br><small>{re_.ACTIONS["ALLOW"][0]}</small></div>'
    else:
        html += '<div style="margin-top:10px;font-weight:700">কেন / Why:</div>'
        for _, _, en_txt, bn in reasons:
            html += f'<div class="reason">{E(bn)}<br><small>{E(en_txt)}</small></div>'
        html += f'<div class="tip">{ic("lock", 16)} {re_.SAFETY_TIP[1]}</div>'
        html += f'<div style="margin-top:10px"><b>Action:</b> {re_.ACTIONS[level][0]}</div>'
    phone = ('<div class="phone"><div class="notch"></div><div class="bar"><span><b>upay</b> · Send Money</span>'
             f'<span>{int(row["hour"]):02d}:00 · ৳{float(row["amount"]):,.0f}</span></div>')
    st.markdown(phone + html + "</div></div>", unsafe_allow_html=True)
    if level != "ALLOW":
        b1, b2 = st.columns(2)
        b1.button("বাতিল করুন / Cancel", type="primary", icon=":material/block:", width="stretch", key=f"cancel_{id(row)}")
        b2.button("চালিয়ে যান / Continue", width="stretch", icon=":material/arrow_forward:", key=f"cont_{id(row)}")
    st.markdown(engines_html(engs, n_flag), unsafe_allow_html=True)
    with st.expander("This transfer vs. the customer's own habits", expanded=True, icon=":material/person_search:"):
        st.markdown(profile_html(en.profile_comparison(row, prof_for_table)), unsafe_allow_html=True)
    with st.expander("Transparency: features, model, rules", icon=":material/data_object:"):
        st.write(f"**Classifier (XGBoost):** P(scam) = {prob:.3f}  (warn ≥ {re_.WARN_THRESHOLD}, hold ≥ {re_.HOLD_THRESHOLD})")
        st.write(f"**Anomaly model (Isolation Forest):** more unusual than {anom:.1%} of normal transfers "
                 f"(warn ≥ {re_.ANOMALY_THRESHOLD:.0%})")
        st.write(f"**Business rules triggered:** {', '.join(rules) if rules else 'none'}")
        st.write("**Features the models received:**")
        st.dataframe(pd.DataFrame([{k: row[k] for k in re_.FEATURES}]), hide_index=True)
        st.write("**Feature contributions (SHAP, log-odds):**")
        st.bar_chart(contribs.iloc[0].sort_values(), horizontal=True, color="#0B5CAD")


# ---------------- header ----------------
_test_for_ticker = get_test()
_alerts = _test_for_ticker[_test_for_ticker.risk_score >= re_.WARN_THRESHOLD].head(28)
_items = []
for _r in _alerts.itertuples():
    _lvl = "HOLD" if _r.risk_score >= re_.HOLD_THRESHOLD else "WARN"
    _items.append(f'<span class="{"h" if _lvl == "HOLD" else "w"}">▲ {_lvl}</span> <b>{E(_r.txn_id)}</b> '
                  f'৳{_r.amount:,.0f} → {E(_r.recipient_id)} · risk {_r.risk_score:.0%} · {E(_r.district)}')
for _rg in rings[:6]:
    _items.append(f'<span class="h">◆ RING</span> <b>{_rg["ring_id"]}</b> {_rg["n_mules"]} mule wallets → collector {E(_rg["collector"])}')
_feed = " &nbsp;&nbsp;│&nbsp;&nbsp; ".join(_items)
_n_cust = int(customer_ids(hist).nunique())
_n_alerts = int((_test_for_ticker.risk_score >= re_.WARN_THRESHOLD).sum())
KPI_HTML = f"""<div class="kpis">
<div class="kpi"><div class="k">TRANSFERS MONITORED</div><div class="v c" style="--n:{len(hist)}"></div><div class="s">● raw transaction log</div></div>
<div class="kpi"><div class="k">CUSTOMER PROFILES</div><div class="v c" style="--n:{_n_cust}"></div><div class="s">● learned from history</div></div>
<div class="kpi"><div class="k">ALERTS · TEST WINDOW</div><div class="v c" style="--n:{_n_alerts}"></div><div class="s">● HOLD + WARN</div></div>
<div class="kpi"><div class="k">MULE WALLETS FLAGGED</div><div class="v c" style="--n:{int(wallets.suspected_mule.sum())}"></div><div class="s">● graph analysis</div></div>
<div class="kpi"><div class="k">MULE RINGS TRACKED</div><div class="v c" style="--n:{len(rings)}"></div><div class="s">● collectors identified</div></div>
</div>"""
st.markdown(f"""
<div class="boot">&gt; SYNCHRONIZING_RISK_GRID ... 4/4 ENGINES ONLINE ... OK</div>
<div class="hero"><div class="badge">{ic("shield-check", 40, "#06306B", 2.2)}</div><div style="flex:1">
<h1><span class="upay-name">upay</span> <span>ScamShield</span></h1>
<p>Real-time scam interception and mule-network intelligence for mobile financial services.</p>
<span class="chip"><span class="dot"></span>ENGINES ONLINE 4/4</span>
<span class="chip">XGBOOST · ISOLATION_FOREST · NETWORKX · SHAP</span>
<span class="chip">POINT-IN-TIME FEATURES</span>
<span class="chip y">{DS_LABEL}</span>
</div></div>
<div class="ticker"><div class="lbl">● LIVE THREAT FEED</div>
<div class="track">{_feed} &nbsp;&nbsp;│&nbsp;&nbsp; {_feed}</div></div>
""", unsafe_allow_html=True)

n_open = sum(c["status"] in ("Open", "In progress") for c in CASES)
PAGES = [":material/radar: Command Center", ":material/send_money: Send Money", ":material/manage_search: Analyst Queue",
         ":material/hub: Mule Network", ":material/upload_file: Dataset B · Your Data", ":material/database: Datasets",
         ":material/folder_open: Cases", ":material/insights: Model & Impact"]
with st.sidebar:
    st.markdown("""<div class="sb-logo"><div class="sb-badge">""" + ic("shield-check", 22, "#06306B", 2.4) + """</div><div><div class="sb-t">upay <span>ScamShield</span></div>
    <div class="sb-s">TRUST &amp; RISK OPS CONSOLE</div></div></div>""", unsafe_allow_html=True)
    st.markdown('<div class="sb-h" style="margin-top:4px">ACTIVE DATASET</div>', unsafe_allow_html=True)
    ds_opts = ["A · Demo (synthetic)"] + (["B · Your data"] if wsp.exists(BN) else [])
    st.radio("Dataset", ds_opts, index=1 if WS == "B" and len(ds_opts) > 1 else 0, label_visibility="collapsed",
             key="ds_pick", on_change=lambda: st.session_state.update(ws=st.session_state.ds_pick[0]))
    if not wsp.exists(BN):
        st.caption("Dataset B not built yet: load your own log in the Dataset B page.")
    st.markdown('<div class="sb-h" style="margin-top:10px">NAVIGATION</div>', unsafe_allow_html=True)
    page = st.radio("Navigation", PAGES, label_visibility="collapsed", key="nav")
    st.markdown(f"""
<div class="sb-box"><div class="sb-h">SYSTEM STATUS</div>
<div class="sb-row"><span class="dot"></span>Scam classifier <b>XGBoost</b></div>
<div class="sb-row"><span class="dot"></span>Anomaly model <b>Isolation Forest</b></div>
<div class="sb-row"><span class="dot"></span>Takeover check <b>Profile rules</b></div>
<div class="sb-row"><span class="dot"></span>Network check <b>NetworkX</b></div>
</div>
<div class="sb-box"><div class="sb-h">DATA</div>
<div class="sb-kv"><span>Transfers</span><b>{len(hist):,}</b></div>
<div class="sb-kv"><span>Customers</span><b>{customer_ids(hist).nunique():,}</b></div>
<div class="sb-kv"><span>Model</span><b>{"trained" if WS == "A" or metrics.get("mode") == "trained" else "demo classifier"}</b></div>
<div class="sb-kv"><span>ROC-AUC (future)</span><b>{f"{metrics['roc_auc']:.3f}" if "roc_auc" in metrics else "n/a (no labels)"}</b></div>
</div>
<div class="sb-box"><div class="sb-h">OPERATIONS</div>
<div class="sb-kv"><span>Open cases</span><b>{n_open}</b></div>
<div class="sb-kv"><span>Mule rings tracked</span><b>{len(rings)}</b></div>
<div class="sb-kv"><span>Thresholds</span><b>warn {re_.WARN_THRESHOLD:.0%} · hold {re_.HOLD_THRESHOLD:.0%}</b></div>
</div>
<div class="sb-foot">Synthetic data · decision support only<br>HOLD = pause &amp; re-verify, never auto-block</div>
""", unsafe_allow_html=True)

# ---------------- Business impact (shared by Command Center and Model & Impact) ----------------
@st.cache_data(show_spinner=False)
def impact_rates(wsn, stamp):
    """Measured rates on the active dataset's labelled future test set; falls back to Dataset A when there are no labels."""
    t = pd.read_parquet(wsp.paths(wsn)["test"])
    if "is_fraud" in t and t.is_fraud.notna().sum() > 0 and t.is_fraud.sum() >= 5:
        lab = t[t.is_fraud.notna()]
        return bz.measured_rates(re_.score_frame(model, iforest, lab)), wsn
    tA = pd.read_parquet(wsp.paths("A")["test"])
    mA, fA = re_.load_model(wsp.paths("A")["model"]), re_.load_iforest(wsp.paths("A")["iforest"])
    return bz.measured_rates(re_.score_frame(mA, fA, tA)), "A"


PRESETS_BIZ = {"Base": dict(loss_share=1.0, detection_factor=1.0, false_alarm_factor=1.0),
               "Cautious": dict(loss_share=0.5, detection_factor=1.0, false_alarm_factor=1.0),
               "Stress test": dict(loss_share=0.5, detection_factor=0.5, false_alarm_factor=2.0)}


def tk(x):
    return f"-Tk {abs(x):,.0f}" if x < 0 else f"Tk {x:,.0f}"


def business_impact_ui():
    rates, src = impact_rates(WSN, STAMP)
    st.markdown(f'<div class="section-title">{ic("wallet", 16)} Business impact per 100,000 send money transfers</div>',
                unsafe_allow_html=True)
    st.caption("Our test data has far more scams (1.9%) than real life, so its alert counts are not used directly. We take the "
               "rates the system achieved on future transfers and apply them to a realistic number of scams, from the reported "
               "loss of Tk 92.60 crore a year and Bangladesh Bank's 134.26 million send money transfers a month. "
               + ("Rates measured on your Dataset B." if src != "A" else "Rates measured on Dataset A (demo)."))
    preset = st.radio("Scenario", list(PRESETS_BIZ) + ["Custom"], horizontal=True, key="biz_preset")
    p = dict(PRESETS_BIZ.get(preset, PRESETS_BIZ["Base"]))
    with st.expander("Assumptions (change them to test the estimate)", expanded=preset == "Custom", icon=":material/tune:"):
        a1, a2, a3 = st.columns(3)
        loss_share = a1.slider("Share of reported losses from send money scams", 0.1, 1.0, p["loss_share"], 0.05,
                               disabled=preset != "Custom", help="100% is an upper bound: the figure also covers cards and banks")
        det = a2.slider("Real detection vs. our test", 0.25, 1.0, p["detection_factor"], 0.05, disabled=preset != "Custom",
                        help="1.0 = as good as on our future test data")
        fa = a3.slider("Real false alarms vs. our test", 1.0, 4.0, p["false_alarm_factor"], 0.25, disabled=preset != "Custom")
        b1, b2, b3, b4 = st.columns(4)
        avg_scam = b1.number_input("Average scam transfer (Tk)", 500, 50000, int(round(rates["avg_scam"])), 100)
        warn_cost = b2.number_input("Cost of a false WARN (Tk)", 0, 50, 2)
        hold_cost = b3.number_input("Customer cost of a HOLD (Tk)", 0, 500, 20)
        minutes = b4.number_input("Analyst minutes per HOLD", 1, 60, 10)
        rate = st.number_input("Analyst cost per hour (Tk)", 50, 2000, 300, 50)
    e = bz.estimate(rates, loss_share=loss_share, avg_scam=avg_scam, warn_cost=warn_cost, hold_customer_cost=hold_cost,
                    analyst_minutes=minutes, analyst_rate=rate, detection_factor=det, false_alarm_factor=fa)
    s, r = e["ScamShield"], e["Simple rule"]
    net_cls = "" if s["net"] >= 0 else ' style="color:var(--bad)"'
    st.markdown(f"""<div class="kpis">
<div class="kpi"><div class="k">MONEY PROTECTED</div><div class="v">{tk(s["protected"])}</div><div class="s">● scams stopped before payout</div></div>
<div class="kpi"><div class="k">FRICTION COST</div><div class="v">{tk(s["friction"])}</div><div class="s">● false alarms + HOLD reviews</div></div>
<div class="kpi"><div class="k">NET BENEFIT</div><div class="v"{net_cls}>{tk(s["net"])}</div><div class="s">● {s["ratio"]:.1f}x protected per Tk 1 of friction</div></div>
<div class="kpi"><div class="k">ALERTS</div><div class="v">{s["alerts"]:,.0f}</div><div class="s">● {s["warn"]:,.0f} WARN · {s["hold"]:,.0f} HOLD</div></div>
<div class="kpi"><div class="k">ANALYST HOURS</div><div class="v">{s["analyst_hours"]:,.1f}</div><div class="s">● {s["analyst_hours"] * 10 / 160:.1f} analysts per 1M transfers</div></div>
</div>""", unsafe_allow_html=True)
    st.dataframe(pd.DataFrame({
        "ScamShield": [f"{s['scams']:.1f}", f"{s['alerts']:,.0f}", f"{s['warn']:,.0f}", f"{s['hold']:,.0f}", f"{s['analyst_hours']:,.1f}",
                       tk(s["protected"]), tk(s["friction"]), tk(s["net"]), f"{s['ratio']:.1f}"],
        "Simple rule (no WARN step, every alert reviewed)": [f"{r['scams']:.1f}", f"{r['alerts']:,.0f}", "n/a", f"{r['hold']:,.0f}",
                       f"{r['analyst_hours']:,.1f}", tk(r["protected"]), tk(r["friction"]), tk(r["net"]), f"{r['ratio']:.1f}"]},
        index=["Scam transfers", "Alerts in total", "WARN (customer decides)", "HOLD (analyst review)", "Analyst hours",
               "Money protected", "Friction cost", "Net benefit", "Protected per Tk 1 of friction"]), width="stretch")
    st.caption(f"Per 1 million transfers, multiply by 10: {tk(s['protected'] * 10)} protected for {tk(s['friction'] * 10)} of friction. "
               "Friction = false WARNs × WARN cost + every HOLD × (customer cost + analyst time). Not counted: customer trust, "
               "fewer complaints and disputes, rings stopped before more victims, regulatory value. These are estimates from "
               "stated assumptions, not measured savings.")
    if s["net"] < 0:
        st.warning("In this scenario friction costs more than it saves. The lever is the HOLD threshold: tune it on real data in "
                   "shadow mode so only the strongest cases reach an analyst.")

# ---------------- Command Center ----------------
if page.endswith("Command Center"):
    st.markdown(KPI_HTML, unsafe_allow_html=True)
    c1, c2 = st.columns([1.15, 1])
    with c1:
        st.markdown('<div class="section-title">Engine health (future test window)</div>', unsafe_allow_html=True)
        if WS == "A":
            nv = metrics["novel_scam_test_account_takeover_recall"]
            e = [("Scam classifier", "XGBoost + SHAP", f"ROC-AUC {metrics['roc_auc']:.3f}", metrics["roc_auc"]),
                 ("Anomaly model", "Isolation Forest, no labels", f"Unseen scam type: {nv['classifier_only']:.0%} → {nv['classifier_plus_anomaly']:.0%}", nv["classifier_plus_anomaly"]),
                 ("Takeover check", "Customer's own profile", f"Takeovers caught {metrics['recall_by_scam_type'].get('account_takeover', 0):.0%}", metrics['recall_by_scam_type'].get('account_takeover', 0)),
                 ("Network check", "NetworkX graph", f"Rings found {metrics['network']['rings_correct']}/{metrics['network']['true_rings']}", metrics['network']['rings_correct'] / max(metrics['network']['true_rings'], 1))]
        else:
            trained = metrics.get("mode") == "trained"
            e = [("Scam classifier", "XGBoost + SHAP · " + ("trained on your labels" if trained else "demo model"),
                  f"ROC-AUC {metrics['roc_auc']:.3f} on your future data" if trained else "No labels to measure accuracy", metrics.get("roc_auc", 0.5)),
                 ("Anomaly model", "Isolation Forest · fitted on your data", f"Learned from {metrics['rows']:,} of your transfers", 1.0),
                 ("Takeover check", "Each customer's own history", f"{metrics['senders']:,} sender profiles", 1.0),
                 ("Network check", "NetworkX graph on your log", f"{int(wallets.suspected_mule.sum())} suspected mules · {len(rings)} rings", 1.0)]
        h = '<div class="eng-grid">'
        for name, meth, note, sc in e:
            h += (f'<div class="eng"><span class="chip2 off">ONLINE</span><div class="nm">{name}</div><div class="mt">{meth}</div>'
                  f'<div class="bar"><div style="width:{sc * 100:.0f}%"></div></div><div class="nt">{note}</div></div>')
        st.markdown(h + "</div>", unsafe_allow_html=True)
        st.markdown('<div class="section-title" style="margin-top:16px">Decisions in the future test window</div>', unsafe_allow_html=True)
        tdec = re_.score_frame(model, iforest, get_test())
        vc = tdec.decision.value_counts()
        m1, m2, m3 = st.columns(3)
        m1.metric("ALLOW", f"{vc.get('ALLOW', 0):,}", f"{vc.get('ALLOW', 0) / len(tdec):.1%}", delta_color="off")
        m2.metric("WARN", f"{vc.get('WARN', 0):,}", f"{vc.get('WARN', 0) / len(tdec):.1%}", delta_color="off")
        m3.metric("HOLD", f"{vc.get('HOLD', 0):,}", f"{vc.get('HOLD', 0) / len(tdec):.1%}", delta_color="off")
        if "ai_system" in metrics:
            st.caption(f"{metrics['ai_system']['scam_recall']:.0%} of scams caught with {metrics['ai_system']['false_alarm_rate']:.1%} "
                       "of genuine transfers warned, on transfers the models never saw.")
        else:
            st.caption("No fraud labels in this dataset, so accuracy cannot be measured; decisions are shown for all transfers.")
        _r, _ = impact_rates(WSN, STAMP)
        _e = bz.estimate(_r, avg_scam=_r["avg_scam"])["ScamShield"]
        st.markdown(f'<div class="casebox">{ic("wallet", 16)} <b>Business impact (base case, per 100,000 transfers):</b> '
                    f'Tk {_e["protected"]:,.0f} protected for Tk {_e["friction"]:,.0f} of friction, '
                    f'<b>{_e["ratio"]:.1f}x</b>, with {_e["analyst_hours"]:.0f} analyst hours. Details in Model &amp; Impact.</div>',
                    unsafe_allow_html=True)
    with c2:
        st.markdown('<div class="section-title">Latest high-risk transfers</div>', unsafe_allow_html=True)
        lt = tdec[tdec.decision == "HOLD"].sort_values("timestamp", ascending=False).head(10)
        st.dataframe(lt[["timestamp", "txn_id", "user_id", "amount", "risk_score", "recipient_id"]], hide_index=True, width="stretch", height=300)
        st.markdown('<div class="section-title">Largest mule rings</div>', unsafe_allow_html=True)
        st.dataframe(pd.DataFrame([{"Ring": r["ring_id"], "Mules": r["n_mules"], "Victims": r["victims"],
                                    "Money (৳)": f"{r['flagged_amount']:,.0f}"} for r in rings[:5]]), hide_index=True, width="stretch")
    st.info("Use the sidebar: **Send Money** to score a live transfer for a real customer, **Analyst Queue** to investigate, "
            "**Mule Network** for rings, **Dataset B** to load your own log and train real models on it, **Datasets** to compare A and B. "
            "Switch the active dataset at the top of the sidebar.")

# ---------------- Send Money ----------------
if page.endswith("Send Money"):
    mode = st.radio("Mode", [":material/person: Real customer: live scoring from their history", ":material/science: What-if simulator"],
                    horizontal=True, label_visibility="collapsed")
    left, right = st.columns([1, 1.25])
    if "Real customer" in mode:
        with left:
            st.markdown(f'<div class="section-title">{ic("send", 16)} New transfer from a real customer</div>', unsafe_allow_html=True)
            st.caption("Pick a customer from the transaction log. Every signal is computed live from their real history, "
                       "exactly like the API would do inside upay.")
            active = customer_ids(hist).value_counts().index[:400]
            cust = st.selectbox("Customer", active)
            now = hist.timestamp.max() + pd.Timedelta(hours=1)
            prof = pl.customer_profile(hist, cust, now)
            mine = hist[hist.sender_id == cust]
            st.markdown(f'<div class="casebox"><b>{E(cust)}</b> · {prof["history"]} past transfers · usual ৳{prof["usual_amount"]:,.0f} · '
                        f'active {prof["active_start"]:02d}:00 to {prof["active_end"]:02d}:00 · {E(prof["home_district"])} · '
                        f'{prof["known_recipients"]} contacts</div>', unsafe_allow_html=True)
            amount = st.number_input("Amount (৳)", 10, 25000, int(round(prof["usual_amount"], -1)), step=100)
            contacts = list(mine.receiver_id.value_counts().index[:5])
            mule_w = [r["mules"][0] for r in rings[:3]]
            rec_opt = st.selectbox("Send to", [f"{w} (a usual contact)" for w in contacts] +
                                   [f"{w} (a wallet in the mule network)" for w in mule_w] + ["Type a new wallet number"])
            rec_id = st.text_input("New wallet number", "W77777") if rec_opt.startswith("Type") else rec_opt.split(" ")[0]
            devs = list(mine.device_id.value_counts().index[:2])
            dev = st.selectbox("Device", [f"{d} (their phone)" for d in devs] + ["A new phone (DEV-NEW1)"]).split(" ")[0]
            dev = "DEV-NEW1" if dev == "A" else dev
            dists = [prof["home_district"]] + [d for d in sorted(set(hist.district)) if d != prof["home_district"]]
            dist = st.selectbox("District", dists)
            c1, c2 = st.columns(2)
            day = c1.date_input("Date", now.date(), min_value=now.date())
            hour = c2.slider("Hour", 0, 23, 14)
            call = st.checkbox("Customer is on a phone call while sending")
            ts = pd.Timestamp(day) + pd.Timedelta(hours=hour)
            if ts <= hist.timestamp.max():       # a new transfer must come after the history (no peeking at the future)
                ts = hist.timestamp.max() + pd.Timedelta(minutes=1)
                st.caption(f"Time moved to {ts:%d %b %Y %H:%M}, just after the last transfer in the history.")
        f = STATE.peek(ts, cust, rec_id, amount, dev, dist, int(call))
        row = pd.Series({**f, "device_id": dev, "district": dist})
        with right:
            st.markdown(f'<div class="section-title">{ic("phone", 16)} What the customer sees</div>', unsafe_allow_html=True)
            customer_result(row, rec_id, prof)
    else:
        PRESETS = {
            "Normal: paying a regular contact": dict(usual=1100, win=(9, 21), amount=1200, hour=14, new_rec=0, rec_age=900,
                senders=1, txns=0, dev=0, loc=0, call=0, tenure=700),
            "Scam: 'You won a prize, send a fee' call": dict(usual=1200, win=(8, 20), amount=6000, hour=16, new_rec=1,
                rec_age=12, senders=23, txns=0, dev=0, loc=0, call=1, tenure=120),
            "Takeover: new device draining wallet at 2 AM": dict(usual=1500, win=(9, 22), amount=15000, hour=2, new_rec=1,
                rec_age=30, senders=5, txns=3, dev=1, loc=1, call=0, tenure=1500),
            "Legit but unusual: paying a new tutor": dict(usual=1200, win=(9, 21), amount=1200, hour=19, new_rec=1,
                rec_age=1100, senders=3, txns=0, dev=0, loc=0, call=0, tenure=900),
            "New pattern: 15x usual, 8 transfers in an hour, 4 AM": dict(usual=1333, win=(8, 22), amount=20000, hour=4,
                new_rec=0, rec_age=1500, senders=2, txns=8, dev=0, loc=1, call=0, tenure=2000),
        }
        with left:
            st.markdown(f'<div class="section-title">{ic("flask", 16)} What-if simulator</div>', unsafe_allow_html=True)
            st.caption("Set every signal by hand to see how the engines react.")
            preset = st.selectbox("Scenario", list(PRESETS.keys()))
            v = PRESETS[preset]
            usual = st.number_input("Customer's usual amount (৳)", 10, 25000, v["usual"], step=100, key=f"u{preset}")
            win = st.slider("Customer's usual hours", 0, 23, v["win"], key=f"w{preset}")
            amount = st.number_input("Amount (৳)", 10, 25000, v["amount"], step=100, key=f"a{preset}")
            hour = st.slider("Hour of day", 0, 23, v["hour"], key=f"h{preset}")
            c1, c2 = st.columns(2)
            is_new = c1.checkbox("New recipient", bool(v["new_rec"]), key=f"n{preset}")
            on_call = c2.checkbox("On a phone call", bool(v["call"]), key=f"c{preset}")
            device = c1.checkbox("New device", bool(v["dev"]), key=f"d{preset}")
            new_loc = c2.checkbox("New location", bool(v["loc"]), key=f"l{preset}")
            rec_age = st.number_input("Recipient account age (days)", 0, 5000, v["rec_age"], key=f"ra{preset}")
            senders = st.number_input("Other senders to recipient (24h)", 0, 200, v["senders"], key=f"s{preset}")
            txns1h = st.number_input("Customer's transfers in last hour", 0, 20, v["txns"], key=f"x{preset}")
            tenure = st.number_input("Customer account age (days)", 0, 5000, v["tenure"], key=f"t{preset}")
        row = pd.Series(dict(amount=amount, amount_ratio=round(amount / max(usual, 1), 2), hour=hour,
                             outside_usual_hours=int(hour < win[0] or hour > win[1]), is_new_recipient=int(is_new),
                             recipient_account_age_days=rec_age, recipient_unique_senders_24h=senders,
                             user_txns_last_1h=txns1h, device_changed=int(device), new_location=int(new_loc),
                             on_active_call=int(on_call), user_tenure_days=tenure,
                             device_id="New phone" if device else "Usual phone",
                             district="New district" if new_loc else "Home district"))
        with right:
            st.markdown(f'<div class="section-title">{ic("phone", 16)} What the customer sees</div>', unsafe_allow_html=True)
            customer_result(row, None, dict(usual_amount=usual, active_start=win[0], active_end=win[1],
                                            devices="Usual phone", home_district="Home district", known_recipients=8))

# ---------------- Analyst view ----------------
if page.endswith("Analyst Queue"):
    st.markdown(f'<div class="section-title">{ic("search", 16)} Fraud analyst queue</div>', unsafe_allow_html=True)
    test = get_test()
    _split = metrics.get("split", "")
    st.caption((f"Future transfers the models never saw ({_split.split('test (future): ')[1]}), highest risk first"
                if "test (future): " in _split else "All transfers in your log, highest risk first"))
    thr = st.slider("Show transactions with risk ≥", 0.0, 1.0, re_.HOLD_THRESHOLD, 0.05)
    q = test[test.risk_score >= thr].head(200).reset_index(drop=True)
    st.write(f"{len(test[test.risk_score >= thr]):,} transactions in queue (showing up to 200)")
    st.dataframe(q[["txn_id", "timestamp", "user_id", "recipient_id", "amount", "risk_score", "anomaly_pct", "district",
                    "device_changed", "new_location", "on_active_call", "recipient_unique_senders_24h"]],
                 width="stretch", height=230, hide_index=True)
    if len(q):
        pick = st.selectbox("Investigate transaction", q.txn_id)
        r = q[q.txn_id == pick].iloc[0]
        case_view(r, hist, wallets, ring_of, "an")
        if "scam_type" in r:
            st.caption(f"Ground truth (synthetic label, hidden in production): {r.scam_type}")
        elif "is_fraud" in r and pd.notna(r.is_fraud):
            st.caption(f"Your label for this transfer: {'fraud' if r.is_fraud == 1 else 'genuine'}")

# ---------------- Mule network ----------------
if page.endswith("Mule Network"):
    st.markdown(f'<div class="section-title">{ic("network", 16)} Money-mule network discovery</div>', unsafe_allow_html=True)
    st.caption("One scam transfer can look normal, but mule wallets give themselves away as a group: they receive "
               "high-risk money from many unrelated victims and forward it to the same collector wallet.")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Wallets analysed", f"{len(wallets):,}")
    c2.metric("Suspected mule wallets", int(wallets.suspected_mule.sum()))
    c3.metric("Mule rings found", len(rings))
    if WS == "A":
        c4.metric("Shops wrongly flagged", metrics["network"]["shops_wrongly_flagged"])
    else:
        c4.metric("High-risk money in rings (৳)", f"{sum(r['flagged_amount'] for r in rings):,.0f}")
    if rings:
        st.dataframe(pd.DataFrame([{"Ring": r["ring_id"], "Collector": r["collector"], "Mule wallets": r["n_mules"],
                                    "Victims": r["victims"], "High-risk money (৳)": f"{r['flagged_amount']:,.0f}"}
                                   for r in rings]), width="stretch", hide_index=True, height=240)
        pick_r = st.selectbox("Investigate ring", [r["ring_id"] for r in rings])
        ring = next(r for r in rings if r["ring_id"] == pick_r)
        g1, g2 = st.columns([1.4, 1])
        with g1:
            st.graphviz_chart(mn.ring_dot(ring, wallets), width="stretch")
        with g2:
            what = (f"{ring['n_mules']} wallets received high-risk transfers from {ring['victims']} different senders "
                    f"(৳{ring['flagged_amount']:,.0f}) and forwarded money to the same collector wallet {ring['collector']}.")
            why = "Many unrelated victims, then a few new wallets, then one collector: the typical cash-out pattern of a mule ring."
            nxt = ("Hold outgoing transfers from these wallets, re-check their KYC, warn anyone sending money to them, "
                   "and escalate to the fraud team for review.")
            st.markdown(f"#### Case summary: {pick_r}")
            st.markdown(f"**What happened:** {what}")
            st.markdown(f"**Why it is risky:** {why}")
            st.markdown(f"**What upay should do next:** {nxt}")
            escalate_button("Mule ring", f"{WS}:{pick_r}", f"[Dataset {WS}] Mule ring {pick_r} ({ring['n_mules']} wallets, collector {ring['collector']})",
                            "Critical", dict(what=what, why=[why], next=nxt, ring_wallets=ring["mules"] + [ring["collector"]]),
                            key=f"esc_{pick_r}")
    st.info("Graph analysis runs on out-of-fold model scores over the whole log, so no wallet is judged by a model that saw its own labels. "
            "Wallets used by scammers only once or twice are hard to spot this way; that is a known limitation.")

# ---------------- Dataset B: your data ----------------
def eval_block(y, flagged, amounts):
    y, flagged = np.asarray(y).astype(int), np.asarray(flagged)
    tp = (flagged & (y == 1)).sum()
    return {"Scams caught": f"{tp / max((y == 1).sum(), 1):.0%}",
            "Precision": f"{tp / max(flagged.sum(), 1):.0%}",
            "False alarm rate": f"{(flagged & (y == 0)).sum() / max((y == 0).sum(), 1):.1%}",
            "Scam money protected": f"{amounts[flagged & (y == 1)].sum() / max(amounts[y == 1].sum(), 1):.0%}"}


def fmt_stats(d):
    return {"Scams caught": f"{d['scam_recall']:.0%}", "Precision": f"{d['precision']:.0%}",
            "False alarm rate": f"{d['false_alarm_rate']:.1%}", "Scam money protected": f"{d['scam_money_protected_pct']:.0%}"}


if page.endswith("Your Data"):
    st.markdown('<div class="section-title">Dataset B · run ScamShield as a real model on your own data</div>', unsafe_allow_html=True)
    st.markdown("Load a transaction log exported from your own system. ScamShield learns every customer's habits from it, "
                "fits a **new anomaly model on your data**, and, if the log has confirmed fraud labels (`is_fraud`), "
                "**trains a new scam classifier** on the earlier 70% and tests it on the later 30%. The result is saved as "
                "**Dataset B**; switch to it in the sidebar and every page, plus the API, runs on your data.")
    if wsp.exists(BN):
        mb = wsp.load_metrics(BN)
        st.success(f"Dataset B is ready: {mb['rows']:,} transfers, {mb['senders']:,} senders, {mb['days']} days · "
                   + ("classifier trained on your labels" if mb["mode"] == "trained" else "demo classifier (no usable labels)")
                   + (" · **active now**" if WS == "B" else " · switch to it in the sidebar"))
    with st.expander("Required format", expanded=not wsp.exists(BN), icon=":material/table_view:"):
        st.dataframe(pd.DataFrame([
            ("txn_id", "required", "Unique transfer ID", "T000123"),
            ("timestamp", "required", "Date and time", "2026-07-01 14:30:00 or 01/07/2026 14:30"),
            ("sender_id", "required", "Customer wallet sending", "U00042"),
            ("receiver_id", "required", "Wallet receiving", "W12345"),
            ("amount", "required", "Amount in BDT", "1500"),
            ("device_id", "required", "Device used", "DEV-1A2B"),
            ("district", "required", "Where the transfer was made", "Dhaka"),
            ("on_active_call", "optional", "1 if on a phone call (0 if unknown)", "0"),
            ("sender_created_at / receiver_created_at", "optional", "Wallet opening dates (strongly recommended)", "2024-05-22"),
            ("is_fraud", "optional", "1 = confirmed fraud, 0 = genuine. Needed to train a new classifier", "0"),
        ], columns=["Column", "Need", "Meaning", "Example"]), hide_index=True, width="stretch")
        tmpl = pd.read_csv("data/transactions_raw.csv", nrows=5)
        dl("Download a template CSV", tmpl.to_csv(index=False), "scamshield_template.csv", "text/csv")
        st.caption("Command line, without the app:  python workspace.py your_log.csv   ·   API on your data:  "
                   "set SCAMSHIELD_WORKSPACE=B, then uvicorn api:app")
    src = st.radio("Source", ["Upload a CSV file", "Practice: a labelled sample built from the demo log"], horizontal=True)
    raw_u = None
    if src.startswith("Upload"):
        up = st.file_uploader("Your transaction log (CSV)", type="csv")
        if up is not None:
            raw_u = wsp.read_log(up)
    else:
        st.caption("Uses the last 70 days of the demo log with its fraud labels added and wallet-opening dates for senders "
                   "removed, so you can see the whole Dataset B flow end to end.")
        if st.toggle("Prepare the practice sample", value=False):
            _r = wsp.read_log("data/transactions_raw.csv").merge(
                pd.read_csv("data/ground_truth.csv", dtype={"txn_id": str})[["txn_id", "is_fraud"]], on="txn_id", how="left")
            raw_u = _r[pd.to_datetime(_r.timestamp) >= pd.to_datetime(_r.timestamp).max() - pd.Timedelta(days=70)] \
                .drop(columns=["sender_created_at"])
    if raw_u is not None:
        problems = pl.validate(raw_u)
        if problems:
            for p_ in problems:
                st.error(p_)
        else:
            k = st.columns(4)
            k[0].metric("Rows", f"{len(raw_u):,}")
            k[1].metric("Senders", f"{raw_u.sender_id.nunique():,}")
            _t = pl.parse_time(raw_u.timestamp)
            k[2].metric("Days covered", (_t.max() - _t.min()).days)
            k[3].metric("Fraud labels", f"{int(pd.to_numeric(raw_u.is_fraud, errors='coerce').sum()):,}" if "is_fraud" in raw_u else "none")
            for note in pl.data_quality(raw_u):
                st.warning("Data quality: " + note)
            st.dataframe(raw_u.head(6), hide_index=True, width="stretch")
            if st.button("Build Dataset B from this log", type="primary", icon=":material/model_training:"):
                box = st.status("> BUILDING_DATASET_B ...", expanded=True)
                try:
                    mb = wsp.build_b(raw_u, BN, progress=lambda m_: box.write(m_))
                    box.update(label="> DATASET_B_READY", state="complete")
                    st.session_state.ws = "B"
                    st.session_state.pop("ds_pick", None)
                    st.cache_data.clear()
                    st.rerun()
                except Exception as ex:          # show the problem instead of crashing
                    box.update(label="> BUILD_FAILED", state="error")
                    st.error(f"Could not build Dataset B: {ex}")
    if wsp.exists(BN):
        mb = wsp.load_metrics(BN)
        st.markdown('<div class="section-title" style="margin-top:16px">Dataset B results</div>', unsafe_allow_html=True)
        st.write(mb["note"])
        st.caption(mb["split"])
        if mb["mode"] == "trained":
            st.dataframe(pd.DataFrame({"New model trained on your data": fmt_stats(mb["ai_system"]),
                                       "Demo model (trained on Dataset A)": fmt_stats(mb["demo_model_on_same_test"]),
                                       "Simple rule": fmt_stats(mb["rule_baseline"])}), width="stretch")
            st.caption(f"Measured on the later 30% of your log ({mb['test_size']:,} transfers) that the new model never saw. "
                       f"ROC-AUC {mb['roc_auc']:.3f}.")
        c1, c2 = st.columns(2)
        if WS != "B" and c1.button("Switch to Dataset B now", icon=":material/swap_horiz:"):
            st.session_state.ws = "B"
            st.session_state.pop("ds_pick", None)
            st.rerun()
        if c2.button("Delete Dataset B", icon=":material/delete:"):
            wsp.delete(BN)
            st.session_state.ws = "A"
            st.session_state.pop("ds_pick", None)
            st.cache_data.clear()
            st.rerun()

# ---------------- Datasets ----------------
@st.cache_data(show_spinner="> CROSS_DATASET_TEST: scoring the previous dataset with the current models...")
def previous_dataset_eval():
    d = pd.read_csv("data/previous/transactions.csv")
    y = d.is_scam.values
    mA, fA = re_.load_model(wsp.paths("A")["model"]), re_.load_iforest(wsp.paths("A")["iforest"])
    sc = re_.score_frame(mA, fA, d)
    rule = ((d.is_new_recipient == 1) & (d.amount >= 5000)).values
    out = {"Demo models (trained on the main log)": eval_block(y, (sc.decision != "ALLOW").values, d.amount.values),
           "Simple rule": eval_block(y, rule, d.amount.values)}
    # retrain on the previous dataset itself: earlier 70% -> later 30%
    import xgboost as xgb
    cut = int(len(d) * 0.7)
    tr, te = d.iloc[:cut], d.iloc[cut:]
    m2 = xgb.XGBClassifier(n_estimators=300, max_depth=4, learning_rate=0.08, subsample=0.9, colsample_bytree=0.9,
                           eval_metric="aucpr", random_state=7, scale_pos_weight=(tr.is_scam == 0).sum() / tr.is_scam.sum())
    m2.fit(tr[re_.FEATURES], tr.is_scam)
    s_old = re_.score_frame(mA, fA, te)
    s_new = re_.score_frame(m2, re_.fit_iforest(tr), te)
    retrain = {"Current models": eval_block(te.is_scam, (s_old.decision != "ALLOW").values, te.amount.values),
               "Retrained on this set": eval_block(te.is_scam, (s_new.decision != "ALLOW").values, te.amount.values)}
    by_type = sc.groupby(d.scam_type).decision.apply(lambda s: f"{(s != 'ALLOW').mean():.0%}").to_dict()
    wl = mn.find_mules(sc)
    rg = mn.find_rings(wl, pd.read_csv("data/previous/forwarding.csv"))
    roles = pd.read_csv("data/previous/wallet_roles_ground_truth.csv").set_index("wallet_id").role
    sus = wl.index[wl.suspected_mule]
    net = {"Suspected mules": len(sus), "Of which real mules": f"{(roles.reindex(sus) == 'mule').mean():.0%}",
           "Rings found": len(rg)}
    return out, retrain, by_type, net, d


if page.endswith("Datasets"):
    st.markdown('<div class="section-title">Datasets</div>', unsafe_allow_html=True)
    st.caption("Dataset A is our synthetic demo data (the main raw log plus our earlier synthetic set, both kept). "
               "Dataset B is your own data: load it in the Dataset B page and ScamShield builds real models from it.")
    if wsp.exists(BN):
        mb = wsp.load_metrics(BN)
        st.markdown(f"""<div class="ds" style="margin-bottom:12px"><div class="tag">DATASET B · YOUR DATA · {"ACTIVE" if WS == "B" else "READY"}</div>
<h4>Your transaction log</h4><p><b>{mb['rows']:,}</b> transfers · <b>{mb['senders']:,}</b> senders · <b>{mb['days']}</b> days ·
{"classifier trained on your labels" if mb['mode'] == "trained" else "demo classifier, anomaly model fitted on your data"}</p>
<p>{mb['note']}</p></div>""", unsafe_allow_html=True)
    else:
        st.markdown("""<div class="ds" style="margin-bottom:12px"><div class="tag">DATASET B · YOUR DATA · NOT BUILT YET</div>
<h4>Your transaction log</h4><p>Upload a CSV in the Dataset B page. ScamShield will learn every customer's habits from it,
fit an anomaly model on it and, if it has fraud labels, train a new classifier, then run every page and the API on it.</p></div>""",
                    unsafe_allow_html=True)
    raw_main = pd.read_csv("data/transactions_raw.csv")
    gt_main = pd.read_csv("data/ground_truth.csv")
    prev = pd.read_csv("data/previous/transactions.csv")
    c1, c2 = st.columns(2)
    with c1:
        cust_gt = gt_main[gt_main.kind == "customer"]
        st.markdown(f"""<div class="ds"><div class="tag">DATASET A · DEMO · MAIN SYNTHETIC LOG</div><h4>Synthetic raw transaction log</h4>
<p>What upay actually stores: time, sender, receiver, amount, device, district. No labels inside; every signal is computed
from history by the pipeline. Labels are kept in a separate file like a fraud team's confirmed cases.</p>
<p><b>{len(raw_main):,}</b> transfers · <b>{raw_main.sender_id.str.startswith('U').groupby(raw_main.sender_id).any().sum():,}</b> customers ·
<b>90</b> days · scam rate <b>{cust_gt.is_fraud.mean():.1%}</b> · 80 mule wallets in 12 rings</p>
<p>Generator: <code>generate_data.py</code> · used for training (days 30–72) and the future test (days 72–90)</p></div>""",
                    unsafe_allow_html=True)
        st.dataframe(raw_main.head(8), hide_index=True, width="stretch")
        dl("Download the main synthetic log (CSV)", raw_main.to_csv(index=False), "dataset_A_main_log.csv", "text/csv")
    with c2:
        st.markdown(f"""<div class="ds"><div class="tag">DATASET A · DEMO · EARLIER SYNTHETIC SET (KEPT)</div><h4>Synthetic customer-profile set</h4>
<p>Our earlier dataset: 8,000 synthetic customers with fixed profiles (usual amount, usual hours, devices, home district),
with the same 12 signals already computed for each transfer. Generated independently from the main log.</p>
<p><b>{len(prev):,}</b> transfers · <b>8,000</b> customers · scam rate <b>{prev.is_scam.mean():.1%}</b> ·
80 mule wallets in 12 rings</p>
<p>Generator: <code>generate_data_profiles.py</code> · used here as an independent test set</p></div>""",
                    unsafe_allow_html=True)
        st.dataframe(prev.head(8), hide_index=True, width="stretch")
        dl("Download the earlier synthetic set (CSV)", prev.to_csv(index=False), "dataset_A_earlier_set.csv", "text/csv")
        dl("Download its customer profiles (CSV)",
                           pd.read_csv("data/previous/user_profiles.csv").to_csv(index=False), "dataset_A_earlier_profiles.csv", "text/csv")

    st.markdown('<div class="section-title" style="margin-top:18px">Cross-dataset test: demo models on the earlier synthetic set</div>',
                unsafe_allow_html=True)
    st.caption("The demo models were trained only on the main synthetic log. The earlier set was generated separately with different assumptions, "
               "so this shows what happens when a model meets data that is not like its training data, as with real upay data.")
    if st.toggle("Run the cross-dataset test", value=False):
        out, retrain, by_type, net, _ = previous_dataset_eval()
        d1, d2 = st.columns(2)
        with d1:
            st.markdown("**All 60,000 transfers of the earlier set**")
            st.dataframe(pd.DataFrame(out), width="stretch")
            st.markdown("**Caught by scam type:** " + ", ".join(f"{k.replace('_', ' ')} {v}" for k, v in by_type.items() if k != "none")
                        + f" · genuine transfers warned {by_type.get('none', '')}")
            st.markdown("**Mule network on the earlier set:** " + " · ".join(f"{k}: {v}" for k, v in net.items()))
        with d2:
            st.markdown("**After retraining on the earlier set** (first 70% → last 30%)")
            st.dataframe(pd.DataFrame(retrain), width="stretch")
        st.info("What this shows: the method carries over to a different dataset and still catches most scams, but false alarms "
                "rise because the data looks different. Retraining on the target data brings them back down. That is exactly "
                "why Dataset B exists: load your own data and ScamShield retrains on it.")

# ---------------- Cases ----------------
if page.endswith("Cases"):
    st.markdown(f'<div class="section-title">{ic("folder", 16)} Case management</div>', unsafe_allow_html=True)
    st.caption("Human-in-the-loop: AI raises and explains alerts, analysts decide. Every action is recorded in the audit trail.")
    if not CASES:
        st.info("No cases yet. Escalate an alert from the **Analyst queue** or a ring from the **Mule network** tab.")
    else:
        k1, k2, k3, k4 = st.columns(4)
        k1.metric("Open", sum(c["status"] == "Open" for c in CASES))
        k2.metric("In progress", sum(c["status"] == "In progress" for c in CASES))
        k3.metric("Confirmed fraud", sum(c["status"] == "Resolved: confirmed fraud" for c in CASES))
        k4.metric("False alarms", sum(c["status"] == "Resolved: false alarm" for c in CASES))
        flt = st.radio("Filter", ["All"] + cs.STATUSES, horizontal=True)
        shown = [c for c in CASES if flt == "All" or c["status"] == flt]
        st.dataframe(pd.DataFrame([{"Case": c["id"], "Title": c["title"], "Type": c["kind"], "Priority": c["priority"],
                                    "Status": c["status"], "Analyst": c["analyst"], "Created": c["created"]}
                                   for c in shown]), width="stretch", hide_index=True)
        if shown:
            cid = st.selectbox("Open case", [c["id"] for c in shown])
            case = next(c for c in CASES if c["id"] == cid)
            d1, d2 = st.columns([1.2, 1])
            with d1:
                st.markdown(f'<div class="casebox"><b>{case["id"]}</b> &nbsp; <span class="pri {case["priority"]}">'
                            f'{case["priority"]}</span><br>{E(case["title"])}<br><small>Status: <b>{case["status"]}</b> · '
                            f'Analyst: {E(case["analyst"])} · Created {case["created"]}</small></div>', unsafe_allow_html=True)
                ev = case["evidence"]
                st.markdown(f"**What happened:** {ev['what']}")
                st.markdown("**Why it is risky:**\n" + "\n".join(f"- {w}" for w in ev["why"]))
                st.markdown(f"**What upay should do next:** {ev['next']}")
                if ev.get("engines"):
                    st.markdown(engines_html(ev["engines"], sum(e["flagged"] for e in ev["engines"])),
                                unsafe_allow_html=True)
            with d2:
                with st.form(f"upd_{cid}"):
                    new_status = st.selectbox("Status", cs.STATUSES, index=cs.STATUSES.index(case["status"]))
                    new_analyst = st.text_input("Assigned analyst", case["analyst"])
                    note = st.text_area("Add a note", placeholder="e.g. Called the customer, they confirmed a prize-call scam.")
                    if st.form_submit_button("Save changes", type="primary", icon=":material/save:"):
                        cs.assign(case, new_analyst, new_analyst or ANALYST)
                        cs.update_status(case, new_status, new_analyst or ANALYST)
                        cs.add_note(case, note, new_analyst or ANALYST)
                        st.rerun()
                st.download_button("Download case report (PDF)", cs.pdf_report(case), icon=":material/picture_as_pdf:", file_name=f"{cid}_report.pdf",
                                   mime="application/pdf", width="stretch")
                if case["notes"]:
                    st.markdown("**Notes**")
                    for n in case["notes"]:
                        st.markdown(f"- _{n['time']}_ · **{n['actor']}**: {n['text']}")
            st.markdown("**Audit trail**")
            st.dataframe(pd.DataFrame(case["audit"]).rename(columns=str.title), width="stretch", hide_index=True)
        dl("Export all cases (CSV)",
                           pd.DataFrame([{k: c[k] for k in ("id", "kind", "ref", "title", "priority", "status", "analyst",
                                                            "created")} for c in CASES]).to_csv(index=False),
                           file_name="scamshield_cases.csv", mime="text/csv")

# ---------------- Model & impact ----------------
if page.endswith("Model & Impact"):
    business_impact_ui()
    st.divider()

if page.endswith("Model & Impact") and WS == "B":
    st.markdown(f'<div class="section-title">{ic("chart", 16)} Dataset B · your data</div>', unsafe_allow_html=True)
    st.write(metrics["note"])
    st.caption(metrics["split"])
    if metrics.get("mode") == "trained":
        c1, c2, c3, c4 = st.columns(4)
        a = metrics["ai_system"]
        c1.metric("ROC-AUC", f"{metrics['roc_auc']:.3f}")
        c2.metric("Scams caught", f"{a['scam_recall']:.0%}")
        c3.metric("Scam money protected", f"{a['scam_money_protected_pct']:.0%}")
        c4.metric("Genuine transfers warned", f"{a['false_alarm_rate']:.1%}")
        st.dataframe(pd.DataFrame({"New model trained on your data": fmt_stats(a),
                                   "Demo model (trained on Dataset A)": fmt_stats(metrics["demo_model_on_same_test"]),
                                   "Simple rule": fmt_stats(metrics["rule_baseline"])}), width="stretch")
    else:
        st.info("This log has no usable fraud labels, so accuracy cannot be measured yet. Add an is_fraud column "
                "(confirmed cases from your fraud team) and rebuild Dataset B to train and evaluate a classifier on your data.")
    for note in metrics.get("data_quality", []):
        st.warning("Data quality: " + note)
    st.markdown("**Feature importance of the active classifier**")
    st.bar_chart(pd.Series(metrics["feature_importance"]), color="#FFD200")

if page.endswith("Model & Impact") and WS == "A":
    st.markdown(f'<div class="section-title">{ic("chart", 16)} Offline evaluation on a clean held-out test set</div>', unsafe_allow_html=True)
    m = metrics
    a, b = m["ai_system"], m["rule_baseline"]
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("ROC-AUC", f"{m['roc_auc']:.3f}")
    c2.metric("Scams caught", f"{a['scam_recall']:.0%}", f"{(a['scam_recall'] - b['scam_recall']) * 100:+.0f} pts vs rule")
    c3.metric("Scam money protected", f"{a['scam_money_protected_pct']:.0%}",
              f"{(a['scam_money_protected_pct'] - b['scam_money_protected_pct']) * 100:+.0f} pts vs rule")
    c4.metric("Legit transfers warned", f"{a['false_alarm_rate']:.1%}")
    st.markdown("**AI system vs. a simple rule** (rule = new recipient AND amount ≥ ৳5,000)")
    st.dataframe(pd.DataFrame({"AI + rules (ScamShield)": a, "Simple rule baseline": b}), width="stretch")
    st.markdown("**Catching scam types the classifier has never seen** (both models trained without any account-takeover examples)")
    nv = m["novel_scam_test_account_takeover_recall"]
    st.bar_chart(pd.Series({"Classifier only": nv["classifier_only"], "Classifier + anomaly model": nv["classifier_plus_anomaly"]}),
                 color="#0B5CAD")
    st.markdown("**Detection rate by scam type**")
    st.bar_chart(pd.Series(m["recall_by_scam_type"]), color="#0B5CAD")
    st.markdown("**Fairness check: new vs. established users**")
    st.dataframe(pd.DataFrame(m["fairness_by_tenure"]), width="stretch")
    st.markdown("**Global feature importance**")
    st.bar_chart(pd.Series(m["feature_importance"]), color="#FFD200")
    st.info("All data is synthetic. Results on injected patterns are optimistic; real performance must be validated on governed upay data.")
    st.info("Thresholds are business-policy settings that upay would tune on real data. The models never block money on "
            "their own: high-risk transfers are paused for re-verification and human review.")
