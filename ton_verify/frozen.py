#!/usr/bin/env python3
"""
TN-01 part 1: the early-miner accounts suspended by TON (GRAM) config parameter 44.

python -m ton_verify.frozen fetch    read param 44, balances and every transaction since the freeze (tonapi.io)
python -m ton_verify.frozen verify   offline: did any suspended account send value out after the freeze?

Public data only. Evidence goes to evidence/frozen/, results to results/frozen/.
"""

import gzip
import json
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
API = "https://tonapi.io/v2"
FREEZE_FROM = 1676937600  # 21 Feb 2023 00:00 UTC, day the validator vote ended
MAX_TX = 20000  # safety cap per account; an account that hits it is reported as incomplete
UA = {"User-Agent": "gravit-ton-verification (+https://github.com/gravit-open-network-foundation)"}


def get(path: str):
    err = None
    for attempt in range(6):
        try:
            with urllib.request.urlopen(urllib.request.Request(API + path, headers=UA), timeout=60) as r:
                return json.load(r)
        except Exception as e:  # rate limit or transient error: back off
            err = e
            time.sleep(2 * (attempt + 1))
    raise RuntimeError(f"{path}: {err}")


def slim(t: dict) -> dict:
    """Keep only what the checks need."""
    im = t.get("in_msg") or {}
    return {"lt": int(t["lt"]), "utime": t["utime"], "hash": t["hash"], "success": t.get("success"), "aborted": t.get("aborted"),
            "in_value": int(im.get("value") or 0), "in_from": (im.get("source") or {}).get("address"),
            "out": [{"value": int(m.get("value") or 0), "to": (m.get("destination") or {}).get("address"), "bounced": m.get("bounced")}
                    for m in t.get("out_msgs", [])]}


def fetch() -> None:
    conf = get("/blockchain/config")
    p44 = conf["44"]
    out = ROOT / "evidence" / "frozen"
    out.mkdir(parents=True, exist_ok=True)
    accounts = []
    for i, a in enumerate(p44["accounts"]):
        acc = get(f"/accounts/{a}")
        time.sleep(1.1)
        txs, before = [], None
        while True:
            q = f"/blockchain/accounts/{a}/transactions?limit=100" + (f"&before_lt={before}" if before else "")
            page = get(q)["transactions"]
            time.sleep(1.1)
            txs += [slim(t) for t in page]
            if len(page) < 100 or page[-1]["utime"] < FREEZE_FROM or len(txs) >= MAX_TX:
                break
            before = page[-1]["lt"]
        accounts.append({"address": a, "balance": int(acc.get("balance", 0)), "status": acc.get("status"), "complete": len(txs) < MAX_TX,
                         "last_activity": acc.get("last_activity"), "transactions": txs})
        if i % 20 == 0:
            print(f"  {i}/{len(p44['accounts'])} accounts", flush=True)
    meta = {"source": API, "config_param": 44, "suspended_until": p44["suspended_until"], "count": len(p44["accounts"]),
            "fetched_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    with gzip.open(out / "evidence.json.gz", "wt") as fh:
        json.dump({"meta": meta, "accounts": accounts}, fh, sort_keys=True)
    print(f"{len(accounts)} accounts, {sum(len(a['transactions']) for a in accounts)} transactions")


def verify() -> int:
    with gzip.open(ROOT / "evidence" / "frozen" / "evidence.json.gz", "rt") as fh:
        ev = json.load(fh)
    rows, sent = [], []
    for a in ev["accounts"]:
        after = [t for t in a["transactions"] if t["utime"] >= FREEZE_FROM]
        value_out = [(t["hash"], t["utime"], m) for t in after for m in t["out"] if m["value"] > 0 and not m["bounced"]]
        rows.append({"address": a["address"], "balance_nanoton": a["balance"], "tx_since_freeze": len(after),
                     "successful_tx_since_freeze": sum(1 for t in after if t["success"]), "value_sent_since_freeze": len(value_out)})
        sent += [{"address": a["address"], "tx": h, "utime": u, "to": m["to"], "value": m["value"]} for h, u, m in value_out]
    total = sum(r["balance_nanoton"] for r in rows)
    summary = {"meta": ev["meta"], "accounts": len(rows), "total_balance_ton": total / 1e9,
               "accounts_that_sent_value_since_freeze": len({s["address"] for s in sent}),
               "value_sent_since_freeze_ton": sum(s["value"] for s in sent) / 1e9,
               "transactions_since_freeze": sum(r["tx_since_freeze"] for r in rows),
               "successful_transactions_since_freeze": sum(r["successful_tx_since_freeze"] for r in rows)}
    d = ROOT / "results" / "frozen"
    d.mkdir(parents=True, exist_ok=True)
    (d / "accounts.json").write_text(json.dumps(sorted(rows, key=lambda r: -r["balance_nanoton"]), indent=1) + "\n")
    (d / "outgoing.json").write_text(json.dumps(sent, indent=1) + "\n")
    (d / "summary.json").write_text(json.dumps(summary, indent=1, sort_keys=True) + "\n")
    print(json.dumps(summary, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(fetch() if sys.argv[1] == "fetch" else verify())
