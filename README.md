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

## Part 2: validators and who stands behind them (done, 28 Oct 2026)

Current validator round (elected at unix time 1793150728), read from the public ledger through tonapi.io.

| | From the ledger |
|---|---|
| Validators (nodes) | **374** |
| Total stake | **667,435,547 TON (GRAM)** |
| Largest single node | 0.49 % |
| Nodes needed for one third of the stake | 81 |
| Distinct operators, after grouping nodes by the address that controls them | **204** |
| Largest operator | **16.29 %**: 52 nodes, 108,706,006 TON |
| Top 10 operators | 38.72 % |
| Operators needed for one third / one half of the stake | **7** / 26 |
| Stake owners (pool owner or largest nominator) needed for one third / one half | 7 / 20 |

- Counting nodes makes the network look more spread than it is. Grouped by who controls them, 7 operators together hold more than one third of the stake, the share that can halt consensus.
- The largest operator owns 52 single nominator pools. Its wallet `0:8c397c43…7ab3` is labelled **"Telegram"** by tonapi.io. The label comes from the data provider, not from the ledger; Telegram has said publicly in 2026 that it became a validator, but we have not found a statement by Telegram that names this address. Public reports of Telegram's stake differ widely (2.2 million TON, 28.2 million TON, "USD 191 million"); the ledger shows 108.7 million TON staked through this owner in the current round.
- Grouping uses public get methods: `get_roles` (single nominator pools), `get_pool_data` and `list_nominators` (nominator pools), `get_validator_controller_data` (liquid staking controllers). 53 nodes expose no such role (plain wallets, lockup contracts); each is counted as its own operator, so the concentration figures are a lower bound.

Files: `results/validators/summary.json`, `operators.json`, `stake_owners.json`.

## Coming next
3. Supply: total, issuance to validators, fees burned.
4. Largest holders, matched against public disclosures (for example TON Strategy filings with the SEC).
5. Rumours and facts: public claims about TON, each marked confirmed, not confirmed or opinion, with sources.

## Reproduce
```
python3 -m ton_verify.frozen fetch    # public API tonapi.io, about 1 hour
python3 -m ton_verify.frozen verify   # offline
python3 -m ton_verify.validators fetch    # about 20 minutes
python3 -m ton_verify.validators verify   # offline
```

Apache 2.0. Gravit Open Network Foundation.
