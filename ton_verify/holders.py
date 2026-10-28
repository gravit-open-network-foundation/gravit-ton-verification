#!/usr/bin/env python3
"""
TN-01 part 4: the largest TON (GRAM) accounts, what they are, and how concentrated the supply is.

python -m ton_verify.holders fetch    top accounts by balance (toncenter.com), each cross-checked and labelled through tonapi.io
python -m ton_verify.holders verify   offline: classify every account, shares of the total supply from part 3

Public data only. Evidence goes to evidence/holders/, results to results/holders/.
"""

import gzip
import json
import sys
import time
import urllib.request

from ton_verify.frozen import ROOT, UA, get

NANO = 10**9
TOP = 200
ELECTOR = "-1:3333333333333333333333333333333333333333333333333333333333333333"


def toncenter(path: str):
    with urllib.request.urlopen(urllib.request.Request("https://toncenter.com/api/v3" + path, headers=UA), timeout=60) as r:
        return json.load(r)


def norm(a: str) -> str:
    wc, h = a.split(":")
    return f"{wc}:{h.lower()}"


def fetch() -> None:
    out = ROOT / "evidence" / "holders"
    out.mkdir(parents=True, exist_ok=True)
    top = []
    for off in range(0, TOP, 100):
        top += toncenter(f"/topAccountsByBalance?limit=100&offset={off}")
        time.sleep(1.1)
    rows = []
    for i, t in enumerate(top):
        a = norm(t["account"])
        try:
            acc = get(f"/accounts/{a}")
        except RuntimeError:
            acc = {}
        rows.append({"address": a, "balance_toncenter": int(t["balance"]), "balance_tonapi": int(acc["balance"]) if "balance" in acc else None,
                     "name": acc.get("name"), "interfaces": acc.get("interfaces") or [], "status": acc.get("status"),
                     "is_scam": acc.get("is_scam"), "last_activity": acc.get("last_activity")})
        time.sleep(1.1)
        if i % 50 == 0:
            print(f"  {i}/{len(top)} accounts", flush=True)
    (out / "evidence.json").write_text(json.dumps({"source": ["https://toncenter.com/api/v3/topAccountsByBalance", "https://tonapi.io/v2/accounts"],
                                                   "fetched_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "accounts": rows}, indent=1) + "\n")
    print(f"{len(rows)} accounts")


def kind(r: dict, frozen: set, pools: set, owners: set) -> str:
    itf = set(r["interfaces"])
    if r["address"] == ELECTOR:
        return "elector (validator stakes held by the protocol)"
    if r["address"] in frozen:
        return "suspended early-miner wallet (part 1)"
    if r["address"] in pools or itf & {"single_nominator_pool", "tv_pool", "nominator_pool", "validator_controller", "whales_nominators", "tf_nominator"}:
        return "staking pool or validator"
    if r["address"] in owners:
        return "owner of validator stake (part 2)"
    if itf & {"lockup_vesting", "vesting", "lockup_universal", "restricted_wallet"}:
        return "lockup or vesting contract"
    if any(i.startswith(("wallet", "highload")) for i in itf):
        return "wallet"
    if itf:
        return "contract: " + ", ".join(sorted(itf))
    return "unknown or not deployed"


def verify() -> int:
    ev = json.loads((ROOT / "evidence" / "holders" / "evidence.json").read_text())
    supply = json.loads((ROOT / "results" / "supply" / "summary.json").read_text())["points"][0]["total_supply_ton"]
    frozen = {a["address"] for a in json.loads((ROOT / "results" / "frozen" / "accounts.json").read_text())}
    vals = json.loads((ROOT / "results" / "validators" / "stake_owners.json").read_text())
    owners = {o["address"] for o in vals}
    with gzip.open(ROOT / "evidence" / "validators" / "evidence.json.gz", "rt") as fh:
        pools = {v["address"] for v in json.load(fh)["validators"]}
    accs = []
    for r in ev["accounts"]:
        bal = r["balance_toncenter"] / NANO
        drift = None if r["balance_tonapi"] is None else round((r["balance_tonapi"] - r["balance_toncenter"]) / NANO, 3)
        accs.append({"rank": len(accs) + 1, "address": r["address"], "label": r["name"], "kind": kind(r, frozen, pools, owners),
                     "balance_ton": round(bal, 3), "share_of_supply_pct": round(100 * bal / supply, 3),
                     "providers_differ_by_ton": drift, "last_activity": r["last_activity"]})
    by_kind = {}
    for a in accs:
        k = by_kind.setdefault(a["kind"], {"accounts": 0, "ton": 0.0})
        k["accounts"] += 1
        k["ton"] += a["balance_ton"]
    for k in by_kind.values():
        k["ton"] = round(k["ton"])
        k["share_of_supply_pct"] = round(100 * k["ton"] / supply, 2)
    share = lambda n: round(100 * sum(a["balance_ton"] for a in accs[:n]) / supply, 2)
    summary = {"fetched_at": ev["fetched_at"], "total_supply_ton": supply, "accounts_read": len(accs),
               "top1_pct": share(1), "top10_pct": share(10), "top50_pct": share(50), "top100_pct": share(100), f"top{len(accs)}_pct": share(len(accs)),
               "by_kind": dict(sorted(by_kind.items(), key=lambda kv: -kv[1]["ton"])),
               "largest_provider_difference_ton": max((abs(a["providers_differ_by_ton"] or 0) for a in accs), default=0),
               "labelled": sum(1 for a in accs if a["label"])}
    res = ROOT / "results" / "holders"
    res.mkdir(parents=True, exist_ok=True)
    (res / "summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n")
    (res / "accounts.json").write_text(json.dumps(accs, indent=1, ensure_ascii=False) + "\n")
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "verify"
    sys.exit(fetch() or 0 if cmd == "fetch" else verify())
