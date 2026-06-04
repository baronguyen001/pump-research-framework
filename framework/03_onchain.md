# Layer 3: On-Chain

Purpose: check whether wallet behavior, holder distribution, and liquidity
support the story.

| Public tool | Use |
|---|---|
| Dune | custom on-chain queries |
| Arkham | wallet and entity intelligence |
| Cielo | wallet PnL and activity tracking |
| Nansen guides | smart-money label methodology |
| DexScreener | pair liquidity, age, volume, and links |
| GeckoTerminal | DEX pair data |
| Etherscan and Solscan | holders and transactions |
| Helius docs | Solana parsed transaction workflows |

Strong signals worth 20 or more points:

- Several historically profitable wallets accumulate during the same week.
- Holder count grows steadily rather than in one suspicious burst.
- Liquidity increases and is not removed during small pullbacks.
- Top holder concentration is reasonable after excluding LP, burn, and exchange
  wallets.
- Volume to market-cap ratio stays elevated across several days.

Weak or red-flag signals:

- One wallet cluster appears to control the story.
- Liquidity is unlocked or disappears on every rally.
- A whale buy looks like insider setup rather than broad accumulation.
- Supply sits with the team, fresh wallets, or unknown deployer links.

The open-source sibling
[wallet-cluster-detector](https://github.com/baronguyen001/wallet-cluster-detector)
implements this layer as a real case study. This repo only describes the manual
research model and never ships wallet lists.

How to wire this layer to your own data: export holder, liquidity, and wallet
activity tables from public explorers or dashboards. Keep wallet identifiers out
of public examples unless they are already documented public entities.
