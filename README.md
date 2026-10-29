# Gravit × TON (GRAM): independent re-check from the public ledger

**Experiment TN-01 · status: research, read-only, public data only · parts 1 to 5 done, 28 Oct 2026**

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
Parameter 44 lists, next to the 179 miner wallets, the address made only of zeros. It is not a wallet of anyone: it has never been deployed (status `uninit`), and deploying it would need a contract whose initial state hashes to exactly zero, which nobody can produce. Coins sent there cannot be moved by anyone, with or without the suspension.

Many people send coins there anyway. In the latest 20,000 transactions we read (19 Jul to 28 Oct 2026):
| | From the ledger |
|---|---|
| Distinct senders | **18,841** |
| Received in this window | 3,881 TON |
| Transfers below 0.01 TON / 0.01 to 1 TON / 1 TON or more | 16,685 / 3,268 / 33 (14 with no value) |
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

## Part 4: the largest accounts (done, 28 Oct 2026)
The 200 largest accounts by balance (toncenter.com), each balance cross-checked with tonapi.io (largest difference 1,223 TON, explained by the seconds between the two reads) and classified with the results of parts 1 and 2. Shares are of the total supply from part 3.

| | From the ledger |
|---|---|
| Largest account | the **Elector**, the protocol contract that holds validator stakes: 1,371,209,613 TON, **25.97 %** |
| Top 10 / top 100 / top 200 accounts | **66.11 %** / 92.23 % / 94.49 % of all TON |
| Held by the Elector, the TON Believers Fund locker (1,245,901,480 TON, 23.60 %) and the suspended miner wallets (20.48 %) | **70.05 %**: staked, locked or suspended |
| Wallets and undeployed addresses among the top 200 | 145 accounts, **23.6 %** |

- Counting accounts makes TON look far more concentrated than the coins anyone can move today: seven tenths of the supply is staked, locked by contract or suspended by the validators' vote.
- The largest freely movable accounts are labelled by tonapi.io: `thedns-tg-channell.ton` (248.2 million TON, 4.70 %), **Telegram** (102.4 million TON, 1.94 %, the same address that owns 108.7 million TON of validator stake in part 2), `tme-funstat.ton` (99.3 million), **Fragment** (95.4 million and 36.4 million).
- Labels are of two kinds. Some are set by the data provider (Elector, TON Believers Fund, Telegram, Fragment). Others, ending in `.ton`, are names the owner registered for the address; anyone can register such a name, so it says nothing about who the owner is.
- 25 of the 200 accounts carry a label. The ledger names no one; everything else is an address.

Files: `results/holders/summary.json`, `accounts.json` (all 200 with kind, label and share).

## Part 5: rumours and facts (28 Oct 2026)
Public claims about TON, each set against what this repository can show from the ledger. **Confirmed**: the ledger shows it. **Not confirmed**: the ledger shows otherwise. **Cannot be checked**: the ledger cannot tell. Sources are listed for every claim.

| Claim | Verdict | What the ledger shows |
|---|---|---|
| "TON is deflationary, fees are burned" | **Not confirmed** | Half of all fees is burned (param 5), but block rewards are far larger: the supply grew by 130.5 million TON in the last 12 months and grows at about 4 % a year now (part 3). |
| "Net inflation is about 0.6 % a year" | **Outdated** | True from Oct 2024 to Oct 2025 (0.62 %). Since July 2026 about 4 % a year, because blocks are about six times as frequent as in 2024 (part 3). |
| "Staking yield rose in 2026" | **Consistent with the ledger** | The block rate doubled: 1.24 masterchain blocks per second on average from Oct 2025 to Jul 2026, about 2.4 since July, and each block carries a fixed reward. TON Strategy reported 2.2 million TON earned in Q1 2026 on 221.2 million staked (about 4 % a year); press reports give about 1.5 % for May alone. The company figures themselves cannot be checked. |
| "About 1.08 billion TON of early miners are frozen until February 2027" | **Confirmed** | 179 wallets, 1,081,391,803 TON, suspended until 21 Feb 2027 06:00 UTC, nothing sent out since the vote (part 1). |
| "Telegram controls the network" | **Partly confirmed** | No single operator holds one third of the stake. The largest holds 16.3 % and is labelled Telegram by tonapi.io; seven operators together hold more than one third (part 2). The ledger cannot prove who owns the address. |
| "Telegram stakes 2.2 million / 28.2 million TON / USD 191 million" | **Not confirmed** | The Telegram-labelled owner has 108.7 million TON in the current validator round and 102.4 million TON in its wallet (parts 2 and 4). |
| "TON Strategy holds about 4.29 % of all Toncoin" (SEC 8-K, 31 Mar 2026) | **Arithmetic consistent; holdings cannot be checked** | 221.9 million TON is 4.2 to 4.3 % of the supply the ledger shows for that period (part 3). The company has not published its addresses. |
| "TON staked through TON Strategy's infrastructure is 26.18 % of the network" (same filing) | **Cannot be checked** | In the current round no stake owner other than the Telegram-labelled one holds more than 5.1 % (part 2). Stake spread across many owners or pools cannot be matched to a company without published addresses. |
| "The network was down for more than seven hours in August 2024" | **Partly confirmed** | The masterchain made no block for **5 h 50 min**, from 27 Aug 2024 22:11:46 to 28 Aug 04:01:52 UTC (blocks 39,987,437 and 39,987,438). Services such as exchanges may have been out longer. |
| "A 40 minute outage on 1 June 2025" | **Longer than reported** | No masterchain block for **67 minutes**, 12:15:31 to 13:22:20 UTC (blocks 48,400,109 and 48,400,110). |
| "A few accounts hold most of TON" | **Confirmed, with a caveat** | The top 10 accounts hold 66 % of the supply, but 70 % of the supply is staked, locked or suspended (part 4). |
| "People burn TON by sending it to the zero address" | **Confirmed as an observation** | 18,841 distinct senders in 100 days; nothing can ever leave that address (part 1). Their motives cannot be seen. |
| "Hacks on TON": TAC bridge, May 2026, about USD 2.8 million; Triple-A hot wallets, 2026 | **Reported by the projects; not a failure of the TON protocol** | Both are incidents of applications built on or connected to TON, described in their own post-mortems. Not re-checked here. |
| "Affluent lost about USD 1 million in a hack" | **No public source found** | We found no report or post-mortem. Until one appears, this is a rumour. |

Sources: TON Strategy 8-K, Q1 2026, [sec.gov](https://www.sec.gov/Archives/edgar/data/1566610/000149315226022417/ex99-1.htm); TON Strategy yield, [BeInCrypto](https://beincrypto.com/ton-strategy-staking-yield-jumps/); fee burn proposal, [The Block](https://www.theblock.co/post/232879/ton-foundation-proposes-burning-50-of-validator-rewards); 0.6 % inflation, [CoinShares](https://coinshares.com/insights/research-data/the-open-network-ton-an-institutional-research-note/) and [MEXC](https://www.mexc.com/price/TON/tokenomics); outage August 2024, [The Block](https://www.theblock.co/post/313367/ton-blockchain-now-down-six-hours) and [Decrypt](https://decrypt.co/246736/telegram-linked-ton-blockchain-down-binance-bybit-suspend-trading); outage June 2025, [CryptoNews](https://cryptonews.com.au/news/ton-blockchain-briefly-halts-block-production-in-swift-40-minute-outage-129278); TAC bridge, [post-mortem](https://tac.build/blog/post-mortem-report-tac-bridge); centralisation debate, [Blockworks](https://blockworks.co/news/empire-newsletter-ton-outage-centralization). Telegram stake figures: see part 2.

Files: `results/outages/summary.json`.

## Addendum: node update v2026.10 and who receives new blocks (29 Oct 2026)

On 19 Oct 2026 TON released node v2026.10 (mandatory). Its first item: "Removed validators and collators from public overlays, improving their stability." A public Telegram post (@investkingyru, "Децентрализация по пропускам") argued that independent nodes now depend on validators for timely data. We checked each claim against the release, the source code at tag `v2026.10` (commit `857b8a5`) and the open issue tracker.

| Claim | Verdict | Evidence |
|---|---|---|
| Validators and collators left the public overlays on 19 Oct | **Confirmed** | [release v2026.10](https://github.com/ton-blockchain/ton/releases/tag/v2026.10), [PR #2576](https://github.com/ton-blockchain/ton/pull/2576) |
| They re-open the public overlays only shortly before their term ends | **Confirmed**: at most the last 600 s | [`validator/full-node.cpp` L72, L392–L424](https://github.com/ton-blockchain/ton/blob/857b8a57a178e6ae0fe7fa86e7d81c5233de8560/validator/full-node.cpp#L392-L424) |
| New blocks are broadcast only to fast-sync and custom overlays | **Confirmed** | [`send_broadcast`](https://github.com/ton-blockchain/ton/blob/857b8a57a178e6ae0fe7fa86e7d81c5233de8560/validator/full-node.cpp#L539-L561) |
| A node gets fast-sync only if a validator admits it | **Confirmed**: `add-fast-sync-overlay-client`, at most **5** slots per validator, no public request path in the code | [`full-node.h` L189](https://github.com/ton-blockchain/ton/blob/857b8a57a178e6ae0fe7fa86e7d81c5233de8560/validator/full-node.h#L189) |
| Independent liteservers now fall behind | **Reported by several operators**, issue open, no maintainer reply as of 29 Oct: up to 4,764 s / ~3,900 blocks of lag since 21 Oct, while TON Core's public liteservers stay 1–4 s behind | [issue #2612](https://github.com/ton-blockchain/ton/issues/2612) |
| Own validator costs "almost 1 million GRAM" | **About right**: formal minimum 300,000 GRAM (config param 17), but the smallest elected stake today is **822,708 GRAM** (374 validators, median 1.74 million) | `results/v2026_10/snapshot.json` |
| Delay and delivery figures quoted from the TON Dev Chat | **Not checked**: no public archive | n/a |
| "A private chain like Canton" | **Opinion**. Blocks and state stay public; what changed is who gets them first | n/a |

Link to Part 2: seven operators hold more than a third of the stake. Since v2026.10 the validators also decide which outside nodes receive new blocks without delay.

## Reproduce
```
python3 -m ton_verify.frozen fetch    # public API tonapi.io, about 1 hour
python3 -m ton_verify.frozen verify   # offline
python3 -m ton_verify.validators fetch    # about 20 minutes
python3 -m ton_verify.validators verify   # offline
pip install -r requirements.txt           # part 3 reads Merkle proofs with pytoniq-core
python3 -m ton_verify.supply fetch        # a few minutes
python3 -m ton_verify.supply verify       # offline: checks every proof
python3 -m ton_verify.holders fetch       # about 5 minutes
python3 -m ton_verify.holders verify      # offline
python3 -m ton_verify.outages fetch       # a few minutes
python3 -m ton_verify.outages verify      # offline
```

Apache 2.0. Gravit Open Network Foundation.
