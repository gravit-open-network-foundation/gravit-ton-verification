#!/usr/bin/env python3
"""
TN-01 part 2: the current TON (GRAM) validator set, stake shares and grouping of nodes by operator.

python -m ton_verify.validators fetch    read the validator set, each validator account and its pool roles (tonapi.io)
python -m ton_verify.validators verify   offline: stake shares, grouping by operator, Nakamoto coefficient

Public data only. Evidence goes to evidence/validators/, results to results/validators/.
"""

import gzip
import json
import sys
import time
from collections import defaultdict
from pathlib import Path

from ton_verify.frozen import API, ROOT, get

# get methods that name who controls a staking contract, by the interface tonapi reports
ROLE_METHODS = {
    "single_nominator_pool": ["get_roles"],
    "tf_nominator": ["get_pool_data"],
    "tv_pool": ["get_pool_data", "list_nominators"],
    "nominator_pool": ["get_pool_data"],
    "validator_controller": ["get_validator_controller_data"],
    "whales_nominators": ["get_owner", "get_proxy"],
}
NANO = 10**9


def call(addr: str, method: str):
    try:
        r = get(f"/blockchain/accounts/{addr}/methods/{method}")
        return r.get("decoded") if r.get("success") else None
    except RuntimeError:
        return None


def fetch() -> None:
    vs = get("/blockchain/validators")
    out = ROOT / "evidence" / "validators"
    out.mkdir(parents=True, exist_ok=True)
    rows = []
    for i, v in enumerate(vs["validators"]):
        acc = get(f"/accounts/{v['address']}")
        time.sleep(1.1)
        roles = {}
        for itf in acc.get("interfaces") or []:
            for m in ROLE_METHODS.get(itf, []):
                roles[m] = call(v["address"], m)
                time.sleep(1.1)
        rows.append({"address": v["address"], "stake": int(v["stake"]), "max_factor": v.get("max_factor"),
                     "interfaces": acc.get("interfaces") or [], "name": acc.get("name"), "balance": int(acc.get("balance", 0)), "roles": roles})
        if i % 25 == 0:
            print(f"  {i}/{len(vs['validators'])} validators", flush=True)
    pools = get("/staking/pools")["pools"]
    labels = {}
    for key in {f(v) for v in rows for f in (operator, funder)}:
        try:
            labels[key] = get(f"/accounts/{key}").get("name")
        except RuntimeError:
            labels[key] = None
        time.sleep(1.1)
    meta = {"source": API, "elect_at": vs["elect_at"], "elect_close": vs["elect_close"], "total_stake": int(vs["total_stake"]),
            "min_stake": int(vs["min_stake"]), "count": len(rows), "fetched_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    with gzip.open(out / "evidence.json.gz", "wt") as fh:
        json.dump({"meta": meta, "validators": rows, "pools": pools, "labels": labels}, fh, sort_keys=True)
    print(f"{len(rows)} validators, {len(pools)} staking pools")


def operator(v: dict) -> str:
    """The address that controls a validator node, as far as public get methods tell."""
    r = v["roles"]
    if (r.get("get_roles") or {}).get("owner"):
        return r["get_roles"]["owner"]
    va = (r.get("get_pool_data") or {}).get("validator_address")
    if va and va.strip("0"):
        return va if ":" in va else "-1:" + va
    for k in ("approver", "validator", "owner"):
        if (r.get("get_validator_controller_data") or {}).get(k):
            return r["get_validator_controller_data"][k]
    if (r.get("get_owner") or {}).get("owner"):
        return r["get_owner"]["owner"]
    return v["address"]


def funder(v: dict) -> str:
    """The address whose coins make up most of the stake: pool owner or largest nominator."""
    r = v["roles"]
    if (r.get("get_roles") or {}).get("owner"):
        return r["get_roles"]["owner"]
    noms = (r.get("list_nominators") or {}).get("nominators") or []
    if noms:
        top = max(noms, key=lambda n: int(n["amount"]))["address"]
        return top if ":" in top else "0:" + top
    return operator(v)


def nakamoto(stakes: list, share: float) -> int:
    total, acc = sum(stakes), 0
    for n, s in enumerate(sorted(stakes, reverse=True), 1):
        acc += s
        if acc * 1.0 / total > share:
            return n
    return len(stakes)


def verify() -> int:
    with gzip.open(ROOT / "evidence" / "validators" / "evidence.json.gz", "rt") as fh:
        ev = json.load(fh)
    vals = ev["validators"]
    total = sum(v["stake"] for v in vals)
    labels = ev.get("labels", {})

    def grouped(key):
        groups = defaultdict(lambda: {"nodes": 0, "stake": 0, "interfaces": set()})
        for v in vals:
            g = groups[key(v)]
            g["nodes"] += 1
            g["stake"] += v["stake"]
            g["interfaces"].update(v["interfaces"])
        return sorted(({"address": k, "label": labels.get(k), "nodes": g["nodes"], "stake_ton": g["stake"] // NANO,
                        "share_pct": round(100 * g["stake"] / total, 3), "interfaces": sorted(g["interfaces"])} for k, g in groups.items()),
                      key=lambda o: -o["stake_ton"])

    ops, funds = grouped(operator), grouped(funder)
    node_stakes = [v["stake"] for v in vals]
    op_stakes = [o["stake_ton"] for o in ops]
    summary = {
        "fetched_at": ev["meta"]["fetched_at"], "elect_at": ev["meta"]["elect_at"],
        "validators": len(vals), "total_stake_ton": total // NANO, "operators": len(ops),
        "largest_node_pct": round(100 * max(node_stakes) / total, 3),
        "largest_operator_pct": ops[0]["share_pct"],
        "top10_operators_pct": round(sum(o["share_pct"] for o in ops[:10]), 3),
        "nodes_to_one_third": nakamoto(node_stakes, 1 / 3), "operators_to_one_third": nakamoto(op_stakes, 1 / 3),
        "nodes_to_half": nakamoto(node_stakes, 1 / 2), "operators_to_half": nakamoto(op_stakes, 1 / 2),
        "stake_owners": len(funds), "largest_stake_owner": {k: funds[0][k] for k in ("address", "label", "nodes", "share_pct")},
        "top10_stake_owners_pct": round(sum(o["share_pct"] for o in funds[:10]), 3),
        "stake_owners_to_one_third": nakamoto([o["stake_ton"] for o in funds], 1 / 3),
        "stake_owners_to_half": nakamoto([o["stake_ton"] for o in funds], 1 / 2),
        "interfaces": dict(sorted(((i, sum(1 for v in vals if i in v["interfaces"])) for i in {i for v in vals for i in v["interfaces"]}), key=lambda x: -x[1])),
        "nodes_without_known_role": sum(1 for v in vals if operator(v) == v["address"]),
    }
    res = ROOT / "results" / "validators"
    res.mkdir(parents=True, exist_ok=True)
    (res / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    (res / "operators.json").write_text(json.dumps(ops, indent=1, ensure_ascii=False) + "\n")
    (res / "stake_owners.json").write_text(json.dumps(funds, indent=1, ensure_ascii=False) + "\n")
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "verify"
    sys.exit(fetch() or 0 if cmd == "fetch" else verify())
