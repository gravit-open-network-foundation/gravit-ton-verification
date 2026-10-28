#!/usr/bin/env python3
"""
TN-01 part 3: total supply of TON (GRAM), read from Merkle proofs of the masterchain state.

python -m ton_verify.supply fetch    for today and earlier dates: masterchain block, state and config proofs (tonapi.io),
                                     block hash cross-checked with toncenter.com
python -m ton_verify.supply verify   offline: check each proof chain, read global_balance, compute the change over time

Needs pytoniq-core (pip install -r requirements.txt). Evidence goes to evidence/supply/, results to results/supply/.
"""

import json
import sys
import time
import urllib.request

from pytoniq_core import Cell

from ton_verify.frozen import ROOT, UA, get

NANO = 10**9
DAYS_BACK = [0, 30, 90, 365, 730]
MC = "8000000000000000"


def mc_block_at(ts: int) -> dict:
    """The first masterchain block at or after unix time ts."""
    for width in (10, 60, 600):
        blocks = [b for b in get(f"/blockchain/reduced/blocks?from={ts}&to={ts + width}")["blocks"] if b["workchain_id"] == -1]
        if blocks:
            seqno = min(b["seqno"] for b in blocks)
            return get(f"/blockchain/blocks/(-1,{MC},{seqno})")
    raise RuntimeError(f"no masterchain block near {ts}")


def toncenter_hash(seqno: int):
    url = f"https://toncenter.com/api/v3/blocks?workchain=-1&shard=-9223372036854775808&seqno={seqno}"
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60) as r:
            b = json.load(r)["blocks"][0]
        import base64
        return base64.b64decode(b["root_hash"]).hex()
    except Exception:
        return None


def fetch() -> None:
    out = ROOT / "evidence" / "supply"
    out.mkdir(parents=True, exist_ok=True)
    now = int(time.time())
    rows = []
    for d in DAYS_BACK:
        b = get("/blockchain/masterchain-head") if d == 0 else mc_block_at(now - d * 86400)
        bid = f"(-1,{MC},{b['seqno']},{b['root_hash']},{b['file_hash']})"
        try:
            proof = get(f"/liteserver/get_config_all/{bid}?mode=0")
        except RuntimeError as e:
            print(f"  {d} days back: no proof ({e})")
            continue
        rows.append({"days_back": d, "seqno": b["seqno"], "gen_utime": b["gen_utime"], "root_hash": b["root_hash"],
                     "file_hash": b["file_hash"], "toncenter_root_hash": toncenter_hash(b["seqno"]),
                     "state_proof": proof["state_proof"], "config_proof": proof["config_proof"],
                     "value_flow": b.get("value_flow")})
        print(f"  {d} days back: block {b['seqno']}", flush=True)
        time.sleep(1.1)
    cfg = get("/blockchain/config")
    (out / "evidence.json").write_text(json.dumps({"source": "https://tonapi.io/v2", "fetched_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                                                   "blocks": rows, "param5": cfg.get("5"), "param14": cfg.get("14")}, indent=1) + "\n")


def global_balance(row: dict) -> int:
    """Check block hash -> state proof -> config proof, then read McStateExtra.global_balance."""
    block = Cell.one_from_boc(row["state_proof"]).refs[0]
    assert block.get_hash(0).hex() == row["root_hash"], "state proof does not match the block hash"
    upd = block.refs[2].begin_parse()
    upd.skip_bits(8 + 256)
    new_state = upd.load_bytes(32)
    state = Cell.one_from_boc(row["config_proof"]).refs[0]
    assert state.get_hash(0) == new_state, "config proof does not match the block's state"
    s = state.begin_parse()
    assert s.load_uint(32) == 0x9023AFE2, "not a ShardStateUnsplit"
    m = state.refs[-1].begin_parse()  # custom: McStateExtra
    assert m.load_uint(16) == 0xCC26, "not a McStateExtra"
    m.load_bit()  # shard_hashes (HashmapE): a reference, not inline
    m.skip_bits(256)  # config_addr
    return m.load_coins()  # global_balance: grams


def verify() -> int:
    ev = json.loads((ROOT / "evidence" / "supply" / "evidence.json").read_text())
    pts = []
    for r in ev["blocks"]:
        bal = global_balance(r)
        pts.append({"days_back": r["days_back"], "date_utc": time.strftime("%Y-%m-%d %H:%M", time.gmtime(r["gen_utime"])), "seqno": r["seqno"],
                    "block_hash_matches_toncenter": r["toncenter_root_hash"] == r["root_hash"] if r["toncenter_root_hash"] else None,
                    "total_supply_ton": round(bal / NANO, 3)})
    now = pts[0]
    for p in pts[1:]:
        days = (now["days_back"] - p["days_back"]) or 1
        p["change_to_today_ton"] = round(now["total_supply_ton"] - p["total_supply_ton"], 3)
        p["per_year_pct"] = round(100 * p["change_to_today_ton"] / p["total_supply_ton"] * 365 / abs(days), 3)
    # block rate explains the change: every block creates a fixed reward (config param 14)
    for a, b in zip(pts, pts[1:]):
        secs = (a["days_back"] - b["days_back"]) * -86400 or 1
        b["masterchain_blocks_to_next_point"] = a["seqno"] - b["seqno"]
        b["masterchain_blocks_per_second"] = round((a["seqno"] - b["seqno"]) / secs, 3)
    summary = {"fetched_at": ev["fetched_at"], "rules": {"block_reward_masterchain_ton": ev["param14"]["masterchain_block_fee"] / NANO,
                                                          "block_reward_basechain_ton": ev["param14"]["basechain_block_fee"] / NANO,
                                                          "share_of_fees_burned": f"{ev['param5']['fee_burn_nom']}/{ev['param5']['fee_burn_denom']}",
                                                          "burn_address": ev["param5"]["blackhole_addr"]},
               "points": pts}
    res = ROOT / "results" / "supply"
    res.mkdir(parents=True, exist_ok=True)
    (res / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "verify"
    sys.exit(fetch() or 0 if cmd == "fetch" else verify())
