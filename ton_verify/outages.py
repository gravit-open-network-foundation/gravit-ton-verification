#!/usr/bin/env python3
"""
TN-01 part 5 (ledger checks for public claims): exact length of reported TON (GRAM) outages.

python -m ton_verify.outages fetch    for each reported outage: the last masterchain block before and the first after
python -m ton_verify.outages verify   offline: the length of each pause

A pause in the masterchain is visible in the ledger itself: consecutive block numbers with a long time between them.
Evidence goes to evidence/outages/, results to results/outages/.
"""

import calendar
import json
import sys
import time

from ton_verify.frozen import ROOT, get

MC = "8000000000000000"
# (name, a moment inside the reported pause, UTC)
REPORTED = [("27-28 Aug 2024 (DOGS launch)", "2024-08-28 02:00"), ("1 Jun 2025", "2025-06-01 13:00")]


def utime(seqno: int) -> int:
    time.sleep(0.6)
    return get(f"/blockchain/blocks/(-1,{MC},{seqno})")["gen_utime"]


def seqno_near(ts: int, step: int) -> int:
    """A masterchain block number near ts, looking backwards (step < 0) or forwards (step > 0) in half hours."""
    for k in range(48):
        t = ts + step * k * 1800
        bs = [b for b in get(f"/blockchain/reduced/blocks?from={t}&to={t + 60}")["blocks"] if b["workchain_id"] == -1]
        time.sleep(0.6)
        if bs:
            return min(b["seqno"] for b in bs)
    raise RuntimeError("no block found")


def fetch() -> None:
    rows = []
    for name, inside in REPORTED:
        t = calendar.timegm(time.strptime(inside, "%Y-%m-%d %H:%M"))
        lo, hi = seqno_near(t, -1), seqno_near(t, 1)
        while hi - lo > 1:  # the last block before t and the first at or after it are consecutive numbers
            mid = (lo + hi) // 2
            lo, hi = (mid, hi) if utime(mid) < t else (lo, mid)
        rows.append({"name": name, "probe_utc": inside, "last_before": {"seqno": lo, "gen_utime": utime(lo)},
                     "first_after": {"seqno": hi, "gen_utime": utime(hi)}})
        print(f"  {name}: blocks {lo} and {hi}")
    out = ROOT / "evidence" / "outages"
    out.mkdir(parents=True, exist_ok=True)
    (out / "evidence.json").write_text(json.dumps({"source": "https://tonapi.io/v2", "fetched_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                                                   "outages": rows}, indent=1) + "\n")


def verify() -> int:
    ev = json.loads((ROOT / "evidence" / "outages" / "evidence.json").read_text())
    res = []
    for r in ev["outages"]:
        a, b = r["last_before"]["gen_utime"], r["first_after"]["gen_utime"]
        assert r["first_after"]["seqno"] == r["last_before"]["seqno"] + 1, "blocks are not consecutive"
        res.append({"name": r["name"], "last_block_before_utc": time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(a)),
                    "first_block_after_utc": time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(b)),
                    "pause_minutes": round((b - a) / 60, 1), "masterchain_blocks": [r["last_before"]["seqno"], r["first_after"]["seqno"]]})
    out = ROOT / "results" / "outages"
    out.mkdir(parents=True, exist_ok=True)
    (out / "summary.json").write_text(json.dumps(res, indent=2) + "\n")
    print(json.dumps(res, indent=2))
    return 0


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "verify"
    sys.exit(fetch() or 0 if cmd == "fetch" else verify())
