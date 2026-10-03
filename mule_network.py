"""
mule_network.py — money-mule and suspicious-network discovery (graph analytics).

Idea: a single scam transfer can look almost normal, but mule wallets give themselves away as a GROUP.
They receive high-risk money from many unrelated victims and then forward it to the same collector wallet.

Steps:
  1. Wallet level: a recipient is a suspected mule if it received at least MIN_FLAGGED high-risk transfers
     from different senders, and most of its incoming transfers are high risk.
  2. Graph level: build a directed graph of onward transfers (wallet -> wallet). A wallet that receives money
     from 2+ suspected mules is a suspected collector.
  3. Rings: connected groups of suspected mules + their collector = one mule ring, ranked by money involved.
"""
import networkx as nx
import pandas as pd

FLAG_SCORE = 0.70     # transfer counts as high risk at the HOLD threshold
MIN_FLAGGED = 3       # high-risk transfers from different senders before a wallet is suspected
MIN_SHARE = 0.5       # share of the wallet's incoming transfers that are high risk


def find_mules(scored: pd.DataFrame) -> pd.DataFrame:
    s = scored.assign(flag=scored.risk_score >= FLAG_SCORE)
    g = s.groupby("recipient_id")
    w = pd.DataFrame({
        "incoming": g.size(),
        "senders": g.user_id.nunique(),
        "flagged_senders": s[s.flag].groupby("recipient_id").user_id.nunique(),
        "flagged_amount": s[s.flag].groupby("recipient_id").amount.sum(),
        "avg_risk": g.risk_score.mean(),
    }).fillna(0)
    w["flagged_share"] = w.flagged_senders / w.senders
    w["suspected_mule"] = (w.flagged_senders >= MIN_FLAGGED) & (w.flagged_share >= MIN_SHARE)
    return w.sort_values("flagged_amount", ascending=False)


def find_rings(wallets: pd.DataFrame, forwarding: pd.DataFrame):
    mules = set(wallets.index[wallets.suspected_mule])
    G = nx.DiGraph()
    for r in forwarding.itertuples():
        G.add_edge(r.from_wallet, r.to_wallet)
    collectors = {n for n in G.nodes if sum(1 for p in G.predecessors(n) if p in mules) >= 2}
    H = G.subgraph(mules | collectors).to_undirected()
    rings = []
    for comp in nx.connected_components(H):
        comp_mules = sorted(c for c in comp if c in mules)
        comp_coll = sorted(c for c in comp if c in collectors)
        if not comp_coll or len(comp_mules) < 2:
            continue
        sub = wallets.loc[comp_mules]
        rings.append({
            "collector": ", ".join(comp_coll),
            "mules": comp_mules,
            "n_mules": len(comp_mules),
            "victims": int(sub.flagged_senders.sum()),
            "flagged_amount": float(sub.flagged_amount.sum()),
        })
    rings.sort(key=lambda r: -r["flagged_amount"])
    for i, r in enumerate(rings, 1):
        r["ring_id"] = f"RING-{i:02d}"
    return rings


def ring_dot(ring, wallets):
    """Graphviz DOT for one ring: victims -> mule wallets -> collector (upay colours)."""
    lines = ['digraph G { rankdir=LR; bgcolor="transparent"; node [style=filled, fontname="Helvetica", fontsize=11];']
    for c in ring["collector"].split(", "):
        lines.append(f'"{c}" [shape=doublecircle, fillcolor="#FF4D5E", color="#FF4D5E", fontcolor="white", label="{c}\\ncollector"];')
    for m in ring["mules"]:
        v = int(wallets.loc[m, "flagged_senders"])
        lines.append(f'"{m}" [shape=box, fillcolor="#FFD200", color="#FFD200", fontcolor="#06306B", label="{m}\\nmule wallet"];')
        lines.append(f'"v_{m}" [shape=ellipse, fillcolor="#0E2142", color="#2F8CFF", fontcolor="#E6EEF8", label="{v} victims"];')
        lines.append(f'"v_{m}" -> "{m}" [color="#2F8CFF"];')
        for c in ring["collector"].split(", "):
            lines.append(f'"{m}" -> "{c}" [color="#FFD200", penwidth=1.6];')
    lines.append("}")
    return "\n".join(lines)
