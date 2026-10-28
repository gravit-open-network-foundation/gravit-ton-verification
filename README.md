# Gravit × TON (GRAM): independent re-check from the public ledger

**Experiment TN-01 · status: research, read-only, public data only · work in progress**

TON (GRAM) has been the subject of many claims, good and bad. This repository separates what the public ledger shows from what it does not, with an open method anyone can rerun. It makes no accusations and is not an audit.

## Part 1: early-miner accounts suspended by config parameter 44 (done, 28 Oct 2026)

In February 2023 validators voted to suspend inactive early-miner wallets for 48 months. The list lives on chain, in configuration parameter 44.

| | From the ledger |
|---|---|
| Accounts in parameter 44 | **180** (179 miner wallets plus the all-zero address `0:000…0`) |
| Balance of the 179 miner wallets | **1,081,391,803 TON (GRAM)** |
| Amount reported frozen at the vote (Feb 2023) | 1,081,389,416 TON |
| Suspended until (on chain) | **21 Feb 2027, 06:00 UTC** (`suspended_until` = 1803189600) |
| Owner-signed transactions after 21 Feb 2023 | **none** |
| Value sent out after 21 Feb 2023 | **none** |

- The difference of about 2,400 TON is incoming transfers that other people sent to these wallets since the freeze (2,454 TON credited), minus storage fees. The wallets can still receive; they cannot send.
- On 21 Feb 2023, the day the vote closed, 9 of these wallets sent a total of 24,802.86 TON in 12 transfers between 05:18 and 21:32 UTC. After that day no transaction signed by an owner appears on any of the 179 wallets.
- The all-zero address is also listed in parameter 44. It holds 10,714 TON and receives many small transfers; we read its latest 20,000 transactions (since 19 Jul 2026), none of which sends value. Its full history was not read.
- What the ledger cannot show: attempts that were refused before reaching the chain. A suspended account's external messages are rejected by validators and leave no trace.

Files: `results/frozen/summary.json`, `accounts.json` (every wallet with balance and counts), `outgoing.json` (the 12 transfers of 21 Feb 2023).

## Coming next
2. Validators: count, stake shares, grouping of nodes by operator (including Telegram), Nakamoto coefficient.
3. Supply: total, issuance to validators, fees burned.
4. Largest holders, matched against public disclosures (for example TON Strategy filings with the SEC).
5. Rumours and facts: public claims about TON, each marked confirmed, not confirmed or opinion, with sources.

## Reproduce
```
python3 -m ton_verify.frozen fetch    # public API tonapi.io, about 1 hour
python3 -m ton_verify.frozen verify   # offline
```

Apache 2.0. Gravit Open Network Foundation.
