# Position Sizing

Sizing matters more than being right once. A strategy can survive many small
losses and still fail from one oversized trade.

## Default caps

| Asset class | Illustrative cap |
|---|---:|
| Memecoin or micro-cap | 1 to 3 percent of bankroll |
| Mid-cap with catalyst | Up to 5 percent |
| Large-cap liquid token | Up to 10 percent |
| Any token below 500M market cap | Hard ceiling: 8 percent |

These are caps, not targets. A score below 60 gets zero suggested size in
`pumpscore`.

## Example allocation frame

A full-time trader might separate capital into:

| Bucket | Purpose |
|---|---|
| Core BTC, ETH, and stablecoin | survival and dry powder |
| Large-cap narrative leaders | beta with liquidity |
| Mid-cap catalyst basket | asymmetric but capped |
| Memecoin basket | lottery exposure with expected failures |
| Airdrop farming | time and gas budget, not conviction size |

Do not borrow against early-stage positions. Do not lock newly listed tokens for
yield unless the lock risk is part of the thesis.

## How `pumpscore size` works

`pumpscore size` maps score bands into a fraction of the asset cap:

- Ignore and Watch: 0 percent.
- Small: 40 percent of the asset cap.
- Medium: 75 percent of the asset cap.
- High conviction: 100 percent of the asset cap.

This is intentionally conservative and user-tunable.
