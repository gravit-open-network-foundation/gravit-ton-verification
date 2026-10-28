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
- The all-zero address is also listed in parameter 44. It is not a miner wallet; see the next section.
- What the ledger cannot show: attempts that were refused before reaching the chain. A suspended account's external messages are rejected by validators and leave no trace.

### Side finding: the all-zero address `0:000…0`
Parameter 44 lists, next to the 179 miner wallets, the address made only of zeros. It is not a wallet of anyone: it has never been deployed (status `uninit`), and deploying it would need contract code whose hash is exactly zero, which nobody can produce. Coins sent there cannot be moved by anyone, with or without the suspension.

Many people send coins there anyway. In the latest 20,000 transactions we read (19 Jul to 28 Oct 2026):
| | From the ledger |
|---|---|
| Distinct senders | **18,841** |
| Received in this window | 3,881 TON |
| Transfers below 0.01 TON / below 1 TON / 1 TON or more | 16,685 / 3,268 / 33 (14 with no value) |
| Transfers sent out | **none** |
| Balance today | 10,714 TON |

We do not know why each sender chose this address: as a deliberate burn, as a default or placeholder in an app, by mistake, or as spam. The ledger shows only that the coins arrive and stay. The full history before 19 Jul 2026 was not read. We report the zero address apart so that it does not distort the result for the miner wallets above.

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

## Part 3: total supply and how fast it grows (done, 28 Oct 2026)
The total amount of TON (GRAM) is kept by the network itself, in the field `global_balance` of the masterchain state. We read it from Merkle proofs and check the chain of hashes: block hash, state proof, config proof. The block hash is cross-checked with a second provider (toncenter.com).

| Date (UTC) | Masterchain block | Total supply | Growth, per year |
|---|---|---|---|
| 28 Oct 2026 | 101,885,639 | **5,279,407,873 TON** | |
| 28 Sep 2026 | 95,623,086 | 5,262,300,594 TON | **3.96 %** (last 30 days) |
| 30 Jul 2026 | 82,940,437 | 5,228,155,841 TON | 3.98 % (last 90 days) |
| 28 Oct 2025 | 53,419,437 | 5,148,879,594 TON | 2.54 % (last 12 months) |
| 28 Oct 2024 | 41,478,629 | 5,116,987,617 TON | 0.62 % (Oct 2024 to Oct 2025) |

- New coins come only from block rewards, fixed in configuration parameter 14: 1.7 TON per masterchain block and 1 TON per basechain block. Half of all transaction fees is burned (parameter 5).
- The growth rate went up because blocks became faster, not because the rules changed. Masterchain blocks per second: 0.38 (Oct 2024 to Oct 2025), 1.24 (Oct 2025 to Jul 2026), about 2.4 since July 2026. Every block carries the same reward, so more blocks per day means more new coins per day.
- At the current pace the supply grows by about 208 million TON a year, close to 4 %. This is net of burned fees.
- What this part does not show: the split between rewards and burned fees block by block, and the history of parameter 14. We read the parameters as they are today.

Files: `results/supply/summary.json`; evidence with the raw proofs in `evidence/supply/evidence.json`.

## Coming next
4. Largest holders, matched against public disclosures (for example TON Strategy filings with the SEC).
5. Rumours and facts: public claims about TON, each marked confirmed, not confirmed or opinion, with sources.

## Reproduce
```
python3 -m ton_verify.frozen fetch    # public API tonapi.io, about 1 hour
python3 -m ton_verify.frozen verify   # offline
python3 -m ton_verify.validators fetch    # about 20 minutes
python3 -m ton_verify.validators verify   # offline
pip install -r requirements.txt           # part 3 reads Merkle proofs with pytoniq-core
python3 -m ton_verify.supply fetch        # a few minutes
python3 -m ton_verify.supply verify       # offline: checks every proof
```

Apache 2.0. Gravit Open Network Foundation.
