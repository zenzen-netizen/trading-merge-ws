# RSI(2) + Fractal(3) Backtest — Meteora SOL Pools (TF30m + MCAP250k + Vol10pct)

Rule: ST bullish + close > EMA50/EMA200; RSI(2)>90; wait confirmed upper fractal(3); entry next candle open; TP=fractal high.
SL O1=-50%; SL O2=2x distance from confirmation close to Supertrend line.
30m fallback: when canonical pool candles are shorter than the EMA/fractal warmup requirement, use Jupiter-backed mint candles aggregated from 15m to synthetic 30m and label the source explicitly.

Discovery variant: min base token market cap 250k; min volume/tvl ratio 0.10; age >= 15h; SOL pairs only; exclude USDC; top 20 by fee_active_tvl_ratio.

## Data coverage
| Pool | TF | Source | Candles | Start WIB | End WIB |
|---|---|---|---:|---|---|
| AAIF-SOL [5bg3we...oCQL] | 1m | pool_canonical | 8 | 2026-07-12 15:46 | 2026-07-19 15:36 |
| AAIF-SOL [5bg3we...oCQL] | 5m | pool_canonical | 6 | 2026-07-12 15:45 | 2026-07-19 15:35 |
| AAIF-SOL [5bg3we...oCQL] | 15m | pool_canonical | 5 | 2026-07-12 15:45 | 2026-07-19 15:30 |
| B2H-SOL [NjhdfD...xmTM] | 1m | pool_canonical | 25 | 2026-07-19 00:06 | 2026-07-19 16:05 |
| B2H-SOL [NjhdfD...xmTM] | 5m | pool_canonical | 20 | 2026-07-19 00:05 | 2026-07-19 16:05 |
| B2H-SOL [NjhdfD...xmTM] | 15m | pool_canonical | 14 | 2026-07-19 00:00 | 2026-07-19 16:00 |
| PONS-SOL [3a2cqM...To43] | 1m | pool_canonical | 41 | 2026-07-19 13:19 | 2026-07-19 15:58 |
| PONS-SOL [3a2cqM...To43] | 5m | pool_canonical | 24 | 2026-07-19 13:15 | 2026-07-19 15:55 |
| PONS-SOL [3a2cqM...To43] | 15m | pool_canonical | 10 | 2026-07-19 13:15 | 2026-07-19 15:45 |
| BULLCAT-SOL [7D7T92...3ZUk] | 1m | pool_canonical | 2678 | 2026-07-15 18:39 | 2026-07-19 17:19 |
| BULLCAT-SOL [7D7T92...3ZUk] | 5m | pool_canonical | 999 | 2026-07-15 18:35 | 2026-07-19 17:15 |
| BULLCAT-SOL [7D7T92...3ZUk] | 15m | pool_canonical | 358 | 2026-07-15 18:30 | 2026-07-19 17:15 |
| BULLCAT-SOL [7D7T92...3ZUk] | 30m | jupiter_proxy_15m_agg30m | 148 | 2026-07-16 17:30 | 2026-07-19 19:00 |
| RAGEGUY-SOL [3pWTxa...vx56] | 1m | pool_canonical | 9 | 2026-05-11 07:20 | 2026-05-15 08:43 |
| RAGEGUY-SOL [3pWTxa...vx56] | 5m | pool_canonical | 8 | 2026-05-11 07:20 | 2026-05-15 08:40 |
| RAGEGUY-SOL [3pWTxa...vx56] | 15m | pool_canonical | 8 | 2026-05-11 07:15 | 2026-05-15 08:30 |
| RAGEGUY-SOL [3pWTxa...vx56] | 30m | jupiter_proxy_15m_agg30m | 100 | 2026-07-14 17:00 | 2026-07-19 19:00 |
| BULLCAT-SOL [AFFuFY...Ugmd] | 1m | pool_canonical | 2253 | 2026-07-15 21:38 | 2026-07-19 17:24 |
| BULLCAT-SOL [AFFuFY...Ugmd] | 5m | pool_canonical | 765 | 2026-07-15 21:35 | 2026-07-19 17:20 |
| BULLCAT-SOL [AFFuFY...Ugmd] | 15m | pool_canonical | 271 | 2026-07-15 21:30 | 2026-07-19 17:15 |
| BULLCAT-SOL [AFFuFY...Ugmd] | 30m | jupiter_proxy_15m_agg30m | 148 | 2026-07-16 17:30 | 2026-07-19 19:00 |
| Tilly-SOL [4SxCFn...L2JE] | 1m | pool_canonical | 25 | 2026-07-19 01:27 | 2026-07-19 15:59 |
| Tilly-SOL [4SxCFn...L2JE] | 5m | pool_canonical | 19 | 2026-07-19 01:25 | 2026-07-19 15:55 |
| Tilly-SOL [4SxCFn...L2JE] | 15m | pool_canonical | 15 | 2026-07-19 01:15 | 2026-07-19 15:45 |
| Tilly-SOL [4SxCFn...L2JE] | 30m | jupiter_proxy_15m_agg30m | 108 | 2026-07-17 13:30 | 2026-07-19 19:00 |
| Mouse-SOL [FbBGvD...XgoG] | 1m | pool_canonical | 1156 | 2026-07-18 14:43 | 2026-07-19 17:24 |
| Mouse-SOL [FbBGvD...XgoG] | 5m | pool_canonical | 319 | 2026-07-18 14:40 | 2026-07-19 17:25 |
| Mouse-SOL [FbBGvD...XgoG] | 15m | pool_canonical | 108 | 2026-07-18 14:30 | 2026-07-19 17:15 |
| Mouse-SOL [FbBGvD...XgoG] | 30m | pool_canonical_insufficient_proxy_insufficient | 10 | 2026-07-19 12:30 | 2026-07-19 17:00 |
| PIE-SOL [a3gRGd...1NfW] | 1m | pool_canonical | 4 | 2026-07-13 19:33 | 2026-07-19 14:51 |
| PIE-SOL [a3gRGd...1NfW] | 5m | pool_canonical | 4 | 2026-07-13 19:30 | 2026-07-19 14:50 |
| PIE-SOL [a3gRGd...1NfW] | 15m | pool_canonical | 9 | 2026-06-29 08:15 | 2026-07-19 14:45 |
| BISCOTTI-SOL [Ft5Cxg...qohk] | 1m | pool_canonical | 1399 | 2026-07-17 21:22 | 2026-07-19 17:24 |
| BISCOTTI-SOL [Ft5Cxg...qohk] | 5m | pool_canonical | 476 | 2026-07-17 21:20 | 2026-07-19 17:20 |
| BISCOTTI-SOL [Ft5Cxg...qohk] | 15m | pool_canonical | 175 | 2026-07-17 21:15 | 2026-07-19 17:15 |
| BISCOTTI-SOL [Ft5Cxg...qohk] | 30m | jupiter_proxy_15m_agg30m | 95 | 2026-07-17 20:00 | 2026-07-19 19:00 |
| Tilly-SOL [BMi3TK...k3kh] | 1m | pool_canonical | 1265 | 2026-07-18 09:24 | 2026-07-19 17:27 |
| Tilly-SOL [BMi3TK...k3kh] | 5m | pool_canonical | 376 | 2026-07-18 09:20 | 2026-07-19 17:25 |
| Tilly-SOL [BMi3TK...k3kh] | 15m | pool_canonical | 129 | 2026-07-18 09:15 | 2026-07-19 17:15 |
| Tilly-SOL [BMi3TK...k3kh] | 30m | jupiter_proxy_15m_agg30m | 108 | 2026-07-17 13:30 | 2026-07-19 19:00 |
| Mouse-SOL [12yWMg...BoKZ] | 1m | pool_canonical | 868 | 2026-07-18 20:03 | 2026-07-19 17:27 |
| Mouse-SOL [12yWMg...BoKZ] | 5m | pool_canonical | 252 | 2026-07-18 20:00 | 2026-07-19 17:25 |
| Mouse-SOL [12yWMg...BoKZ] | 15m | pool_canonical | 86 | 2026-07-18 20:00 | 2026-07-19 17:15 |
| Mouse-SOL [12yWMg...BoKZ] | 30m | pool_canonical_insufficient_proxy_insufficient | 10 | 2026-07-19 12:30 | 2026-07-19 17:00 |
| TOESCOIN-SOL [CpKbsv...MGRH] | 1m | pool_canonical | 3000 | 2026-06-24 05:52 | 2026-07-19 16:59 |
| TOESCOIN-SOL [CpKbsv...MGRH] | 5m | pool_canonical | 3000 | 2026-06-16 00:50 | 2026-07-19 16:55 |
| TOESCOIN-SOL [CpKbsv...MGRH] | 15m | pool_canonical | 3000 | 2026-05-29 04:15 | 2026-07-19 16:45 |
| TOESCOIN-SOL [CpKbsv...MGRH] | 30m | jupiter_proxy_15m_agg30m | 148 | 2026-07-16 17:00 | 2026-07-19 19:00 |
| VORF-SOL [HwCZi8...ZGBd] | 1m | pool_canonical | 167 | 2026-07-18 22:17 | 2026-07-19 15:12 |
| VORF-SOL [HwCZi8...ZGBd] | 5m | pool_canonical | 56 | 2026-07-18 22:15 | 2026-07-19 15:10 |
| VORF-SOL [HwCZi8...ZGBd] | 15m | pool_canonical | 26 | 2026-07-18 22:15 | 2026-07-19 15:00 |
| BULLCAT-SOL [3smCBC...BC4f] | 1m | pool_canonical | 2038 | 2026-07-15 01:01 | 2026-07-19 17:32 |
| BULLCAT-SOL [3smCBC...BC4f] | 5m | pool_canonical | 919 | 2026-07-15 01:00 | 2026-07-19 17:30 |
| BULLCAT-SOL [3smCBC...BC4f] | 15m | pool_canonical | 409 | 2026-07-15 01:00 | 2026-07-19 17:30 |
| BULLCAT-SOL [3smCBC...BC4f] | 30m | jupiter_proxy_15m_agg30m | 148 | 2026-07-16 17:30 | 2026-07-19 19:00 |
| JTVO-SOL [5rtYzK...i1dv] | 1m | pool_canonical | 3000 | 2026-07-02 14:10 | 2026-07-19 16:51 |
| JTVO-SOL [5rtYzK...i1dv] | 5m | pool_canonical | 3000 | 2026-06-26 22:25 | 2026-07-19 16:50 |
| JTVO-SOL [5rtYzK...i1dv] | 15m | pool_canonical | 3000 | 2026-06-04 08:30 | 2026-07-19 16:45 |
| JTVO-SOL [5rtYzK...i1dv] | 30m | jupiter_proxy_15m_agg30m | 129 | 2026-07-16 06:00 | 2026-07-19 19:00 |
| SOLdiers-SOL [6iL24Y...id3S] | 1m | pool_canonical | 3000 | 2026-07-16 06:34 | 2026-07-19 17:34 |
| SOLdiers-SOL [6iL24Y...id3S] | 5m | pool_canonical | 1041 | 2026-07-15 22:50 | 2026-07-19 17:30 |
| SOLdiers-SOL [6iL24Y...id3S] | 15m | pool_canonical | 363 | 2026-07-15 22:45 | 2026-07-19 17:30 |
| SOLdiers-SOL [6iL24Y...id3S] | 30m | jupiter_proxy_15m_agg30m | 148 | 2026-07-16 17:30 | 2026-07-19 19:00 |
| USWR-SOL [qf3ExN...f7iv] | 1m | pool_canonical | 3000 | 2026-07-17 15:37 | 2026-07-19 17:36 |
| USWR-SOL [qf3ExN...f7iv] | 5m | pool_canonical | 3000 | 2026-07-09 07:40 | 2026-07-19 17:35 |
| USWR-SOL [qf3ExN...f7iv] | 15m | pool_canonical | 3000 | 2026-06-18 11:45 | 2026-07-19 17:30 |
| USWR-SOL [qf3ExN...f7iv] | 30m | jupiter_proxy_15m_agg30m | 149 | 2026-07-16 17:30 | 2026-07-19 19:30 |
| NEEGY-SOL [9mZ2tE...WSmf] | 1m | pool_canonical | 865 | 2026-07-18 10:55 | 2026-07-19 17:33 |
| NEEGY-SOL [9mZ2tE...WSmf] | 5m | pool_canonical | 325 | 2026-07-18 10:55 | 2026-07-19 17:30 |
| NEEGY-SOL [9mZ2tE...WSmf] | 15m | pool_canonical | 124 | 2026-07-18 10:45 | 2026-07-19 17:30 |
| NEEGY-SOL [9mZ2tE...WSmf] | 30m | jupiter_proxy_15m_agg30m | 148 | 2026-07-16 17:30 | 2026-07-19 19:30 |
| febu-SOL [2CVnAQ...UEJz] | 1m | pool_canonical | 3000 | 2026-07-13 10:54 | 2026-07-19 16:58 |
| febu-SOL [2CVnAQ...UEJz] | 5m | pool_canonical | 2444 | 2026-07-09 06:25 | 2026-07-19 16:55 |
| febu-SOL [2CVnAQ...UEJz] | 15m | pool_canonical | 971 | 2026-07-09 06:15 | 2026-07-19 16:45 |
| febu-SOL [2CVnAQ...UEJz] | 30m | jupiter_proxy_15m_agg30m | 148 | 2026-07-16 17:30 | 2026-07-19 19:00 |

## Summary
| Pool | TF | Source | SL | Exit | Tr | TP | BE | BE% | SL | EXP | WR% | BE Gate Hit | BE Gate Rec | BE Gate% | Wstreak | Lstreak | AvgHold | SumR |
|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Mouse-SOL [12yWMg...BoKZ] | 1m | pool_canonical | O1_SL50 | BE1 | 5 | 2 | 3 | 60.0 | 0 | 0 | 100.0 | 5 | 3 | 60.0 | 2/2 | 0/0 | 17m | 0.22 |
| Mouse-SOL [12yWMg...BoKZ] | 1m | pool_canonical | O1_SL50 | BE50 | 5 | 2 | 2 | 40.0 | 1 | 0 | 66.7 | 5 | 2 | 40.0 | 1/1 | 1/1 | 31m | -0.78 |
| Mouse-SOL [12yWMg...BoKZ] | 1m | pool_canonical | O1_SL50 | BE75 | 5 | 3 | 0 | 0.0 | 2 | 0 | 60.0 | 5 | 0 | 0.0 | 1/2 | 2/2 | 41m | -1.73 |
| Mouse-SOL [12yWMg...BoKZ] | 1m | pool_canonical | O1_SL50 | TP_FRACTAL | 5 | 3 | 0 | 0.0 | 2 | 0 | 60.0 | 5 | 0 | 0.0 | 1/2 | 2/2 | 41m | -1.73 |
| Mouse-SOL [12yWMg...BoKZ] | 1m | pool_canonical | O2_ST2X | BE1 | 5 | 2 | 3 | 60.0 | 0 | 0 | 100.0 | 5 | 3 | 60.0 | 2/2 | 0/0 | 17m | 0.45 |
| Mouse-SOL [12yWMg...BoKZ] | 1m | pool_canonical | O2_ST2X | BE50 | 5 | 3 | 1 | 20.0 | 1 | 0 | 75.0 | 5 | 1 | 20.0 | 1/2 | 1/1 | 28m | -0.53 |
| Mouse-SOL [12yWMg...BoKZ] | 1m | pool_canonical | O2_ST2X | BE75 | 5 | 3 | 1 | 20.0 | 1 | 0 | 75.0 | 5 | 1 | 20.0 | 1/2 | 1/1 | 28m | -0.53 |
| Mouse-SOL [12yWMg...BoKZ] | 1m | pool_canonical | O2_ST2X | TP_FRACTAL | 5 | 3 | 0 | 0.0 | 2 | 0 | 60.0 | 5 | 0 | 0.0 | 1/2 | 2/2 | 32m | -1.53 |
| Mouse-SOL [12yWMg...BoKZ] | 5m | pool_canonical | O1_SL50 | BE1 | 2 | 1 | 0 | 0.0 | 1 | 0 | 50.0 | 2 | 0 | 0.0 | 1/1 | 1/1 | 40m | -0.75 |
| Mouse-SOL [12yWMg...BoKZ] | 5m | pool_canonical | O1_SL50 | BE50 | 2 | 1 | 0 | 0.0 | 1 | 0 | 50.0 | 2 | 0 | 0.0 | 1/1 | 1/1 | 40m | -0.75 |
| Mouse-SOL [12yWMg...BoKZ] | 5m | pool_canonical | O1_SL50 | BE75 | 2 | 1 | 0 | 0.0 | 1 | 0 | 50.0 | 2 | 0 | 0.0 | 1/1 | 1/1 | 40m | -0.75 |
| Mouse-SOL [12yWMg...BoKZ] | 5m | pool_canonical | O1_SL50 | TP_FRACTAL | 2 | 1 | 0 | 0.0 | 1 | 0 | 50.0 | 2 | 0 | 0.0 | 1/1 | 1/1 | 40m | -0.75 |
| Mouse-SOL [12yWMg...BoKZ] | 5m | pool_canonical | O2_ST2X | BE1 | 2 | 1 | 0 | 0.0 | 1 | 0 | 50.0 | 2 | 0 | 0.0 | 1/1 | 1/1 | 40m | -0.57 |
| Mouse-SOL [12yWMg...BoKZ] | 5m | pool_canonical | O2_ST2X | BE50 | 2 | 1 | 0 | 0.0 | 1 | 0 | 50.0 | 2 | 0 | 0.0 | 1/1 | 1/1 | 40m | -0.57 |
| Mouse-SOL [12yWMg...BoKZ] | 5m | pool_canonical | O2_ST2X | BE75 | 2 | 1 | 0 | 0.0 | 1 | 0 | 50.0 | 2 | 0 | 0.0 | 1/1 | 1/1 | 40m | -0.57 |
| Mouse-SOL [12yWMg...BoKZ] | 5m | pool_canonical | O2_ST2X | TP_FRACTAL | 2 | 1 | 0 | 0.0 | 1 | 0 | 50.0 | 2 | 0 | 0.0 | 1/1 | 1/1 | 40m | -0.57 |
| febu-SOL [2CVnAQ...UEJz] | 15m | pool_canonical | O1_SL50 | BE1 | 19 | 5 | 12 | 63.2 | 1 | 1 | 83.3 | 18 | 12 | 66.7 | 5/5 | 1/1 | 133m | 0.34 |
| febu-SOL [2CVnAQ...UEJz] | 15m | pool_canonical | O1_SL50 | BE50 | 19 | 14 | 2 | 10.5 | 2 | 1 | 87.5 | 18 | 2 | 11.1 | 6/8 | 1/1 | 235m | 4.26 |
| febu-SOL [2CVnAQ...UEJz] | 15m | pool_canonical | O1_SL50 | BE75 | 19 | 14 | 1 | 5.3 | 3 | 1 | 82.4 | 18 | 1 | 5.6 | 6/8 | 1/2 | 268m | 3.26 |
| febu-SOL [2CVnAQ...UEJz] | 15m | pool_canonical | O1_SL50 | TP_FRACTAL | 19 | 15 | 0 | 0.0 | 3 | 1 | 83.3 | 18 | 0 | 0.0 | 7/8 | 1/2 | 306m | 4.05 |
| febu-SOL [2CVnAQ...UEJz] | 15m | pool_canonical | O2_ST2X | BE1 | 19 | 5 | 12 | 63.2 | 1 | 1 | 83.3 | 18 | 12 | 66.7 | 5/5 | 1/1 | 96m | 0.58 |
| febu-SOL [2CVnAQ...UEJz] | 15m | pool_canonical | O2_ST2X | BE50 | 19 | 12 | 4 | 21.1 | 2 | 1 | 85.7 | 18 | 4 | 22.2 | 6/6 | 1/1 | 174m | 3.51 |
| febu-SOL [2CVnAQ...UEJz] | 15m | pool_canonical | O2_ST2X | BE75 | 19 | 15 | 1 | 5.3 | 2 | 1 | 88.2 | 18 | 1 | 5.6 | 7/8 | 1/1 | 231m | 8.21 |
| febu-SOL [2CVnAQ...UEJz] | 15m | pool_canonical | O2_ST2X | TP_FRACTAL | 19 | 15 | 0 | 0.0 | 3 | 1 | 83.3 | 18 | 0 | 0.0 | 7/8 | 1/2 | 240m | 7.21 |
| febu-SOL [2CVnAQ...UEJz] | 1m | pool_canonical | O1_SL50 | BE1 | 16 | 8 | 7 | 43.8 | 1 | 0 | 88.9 | 12 | 7 | 58.3 | 3/5 | 1/1 | 22m | -0.15 |
| febu-SOL [2CVnAQ...UEJz] | 1m | pool_canonical | O1_SL50 | BE50 | 16 | 14 | 0 | 0.0 | 1 | 1 | 93.3 | 12 | 0 | 0.0 | 7/7 | 1/1 | 32m | 0.74 |
| febu-SOL [2CVnAQ...UEJz] | 1m | pool_canonical | O1_SL50 | BE75 | 16 | 14 | 0 | 0.0 | 1 | 1 | 93.3 | 12 | 0 | 0.0 | 7/7 | 1/1 | 32m | 0.74 |
| febu-SOL [2CVnAQ...UEJz] | 1m | pool_canonical | O1_SL50 | TP_FRACTAL | 16 | 14 | 0 | 0.0 | 1 | 1 | 93.3 | 12 | 0 | 0.0 | 7/7 | 1/1 | 32m | 0.74 |
| febu-SOL [2CVnAQ...UEJz] | 1m | pool_canonical | O2_ST2X | BE1 | 16 | 8 | 4 | 25.0 | 4 | 0 | 66.7 | 12 | 4 | 33.3 | 3/5 | 1/2 | 10m | 2.61 |
| febu-SOL [2CVnAQ...UEJz] | 1m | pool_canonical | O2_ST2X | BE50 | 16 | 10 | 2 | 12.5 | 4 | 0 | 71.4 | 12 | 2 | 16.7 | 2/5 | 1/1 | 10m | 3.95 |
| febu-SOL [2CVnAQ...UEJz] | 1m | pool_canonical | O2_ST2X | BE75 | 16 | 12 | 0 | 0.0 | 4 | 0 | 75.0 | 12 | 0 | 0.0 | 2/6 | 1/1 | 10m | 6.34 |
| febu-SOL [2CVnAQ...UEJz] | 1m | pool_canonical | O2_ST2X | TP_FRACTAL | 16 | 12 | 0 | 0.0 | 4 | 0 | 75.0 | 12 | 0 | 0.0 | 2/6 | 1/1 | 10m | 6.34 |
| febu-SOL [2CVnAQ...UEJz] | 30m | jupiter_proxy_15m_agg30m | O1_SL50 | BE1 | 2 | 0 | 1 | 50.0 | 1 | 0 | 0.0 | 2 | 1 | 50.0 | 0/0 | 1/1 | 570m | -1.00 |
| febu-SOL [2CVnAQ...UEJz] | 30m | jupiter_proxy_15m_agg30m | O1_SL50 | BE50 | 2 | 0 | 0 | 0.0 | 1 | 1 | 0.0 | 2 | 0 | 0.0 | 0/0 | 1/1 | 915m | -1.40 |
| febu-SOL [2CVnAQ...UEJz] | 30m | jupiter_proxy_15m_agg30m | O1_SL50 | BE75 | 2 | 0 | 0 | 0.0 | 1 | 1 | 0.0 | 2 | 0 | 0.0 | 0/0 | 1/1 | 915m | -1.40 |
| febu-SOL [2CVnAQ...UEJz] | 30m | jupiter_proxy_15m_agg30m | O1_SL50 | TP_FRACTAL | 2 | 0 | 0 | 0.0 | 1 | 1 | 0.0 | 2 | 0 | 0.0 | 0/0 | 1/1 | 915m | -1.40 |
| febu-SOL [2CVnAQ...UEJz] | 30m | jupiter_proxy_15m_agg30m | O2_ST2X | BE1 | 2 | 0 | 1 | 50.0 | 1 | 0 | 0.0 | 2 | 1 | 50.0 | 0/0 | 1/1 | 195m | -1.00 |
| febu-SOL [2CVnAQ...UEJz] | 30m | jupiter_proxy_15m_agg30m | O2_ST2X | BE50 | 2 | 0 | 0 | 0.0 | 1 | 1 | 0.0 | 2 | 0 | 0.0 | 0/0 | 1/1 | 540m | -1.36 |
| febu-SOL [2CVnAQ...UEJz] | 30m | jupiter_proxy_15m_agg30m | O2_ST2X | BE75 | 2 | 0 | 0 | 0.0 | 1 | 1 | 0.0 | 2 | 0 | 0.0 | 0/0 | 1/1 | 540m | -1.36 |
| febu-SOL [2CVnAQ...UEJz] | 30m | jupiter_proxy_15m_agg30m | O2_ST2X | TP_FRACTAL | 2 | 0 | 0 | 0.0 | 1 | 1 | 0.0 | 2 | 0 | 0.0 | 0/0 | 1/1 | 540m | -1.36 |
| febu-SOL [2CVnAQ...UEJz] | 5m | pool_canonical | O1_SL50 | BE1 | 44 | 14 | 28 | 63.6 | 2 | 0 | 87.5 | 37 | 28 | 75.7 | 1/13 | 2/2 | 70m | 1.60 |
| febu-SOL [2CVnAQ...UEJz] | 5m | pool_canonical | O1_SL50 | BE50 | 44 | 34 | 5 | 11.4 | 4 | 1 | 89.5 | 37 | 5 | 13.5 | 1/17 | 1/1 | 124m | 6.27 |
| febu-SOL [2CVnAQ...UEJz] | 5m | pool_canonical | O1_SL50 | BE75 | 44 | 35 | 3 | 6.8 | 5 | 1 | 87.5 | 37 | 3 | 8.1 | 1/18 | 1/2 | 136m | 5.49 |
| febu-SOL [2CVnAQ...UEJz] | 5m | pool_canonical | O1_SL50 | TP_FRACTAL | 44 | 37 | 0 | 0.0 | 6 | 1 | 86.0 | 37 | 0 | 0.0 | 1/19 | 1/2 | 166m | 5.31 |
| febu-SOL [2CVnAQ...UEJz] | 5m | pool_canonical | O2_ST2X | BE1 | 44 | 14 | 24 | 54.5 | 6 | 0 | 70.0 | 37 | 24 | 64.9 | 1/6 | 1/3 | 34m | 1.83 |
| febu-SOL [2CVnAQ...UEJz] | 5m | pool_canonical | O2_ST2X | BE50 | 44 | 30 | 5 | 11.4 | 9 | 0 | 76.9 | 37 | 5 | 13.5 | 1/13 | 1/4 | 50m | 9.68 |
| febu-SOL [2CVnAQ...UEJz] | 5m | pool_canonical | O2_ST2X | BE75 | 44 | 33 | 1 | 2.3 | 10 | 0 | 76.7 | 37 | 1 | 2.7 | 1/13 | 1/3 | 51m | 10.36 |
| febu-SOL [2CVnAQ...UEJz] | 5m | pool_canonical | O2_ST2X | TP_FRACTAL | 44 | 34 | 0 | 0.0 | 10 | 0 | 77.3 | 37 | 0 | 0.0 | 1/14 | 1/3 | 52m | 10.67 |
| RAGEGUY-SOL [3pWTxa...vx56] | 30m | jupiter_proxy_15m_agg30m | O1_SL50 | BE1 | 1 | 1 | 0 | 0.0 | 0 | 0 | 100.0 | 1 | 0 | 0.0 | 1/1 | 0/0 | 90m | 0.08 |
| RAGEGUY-SOL [3pWTxa...vx56] | 30m | jupiter_proxy_15m_agg30m | O1_SL50 | BE50 | 1 | 1 | 0 | 0.0 | 0 | 0 | 100.0 | 1 | 0 | 0.0 | 1/1 | 0/0 | 90m | 0.08 |
| RAGEGUY-SOL [3pWTxa...vx56] | 30m | jupiter_proxy_15m_agg30m | O1_SL50 | BE75 | 1 | 1 | 0 | 0.0 | 0 | 0 | 100.0 | 1 | 0 | 0.0 | 1/1 | 0/0 | 90m | 0.08 |
| RAGEGUY-SOL [3pWTxa...vx56] | 30m | jupiter_proxy_15m_agg30m | O1_SL50 | TP_FRACTAL | 1 | 1 | 0 | 0.0 | 0 | 0 | 100.0 | 1 | 0 | 0.0 | 1/1 | 0/0 | 90m | 0.08 |
| RAGEGUY-SOL [3pWTxa...vx56] | 30m | jupiter_proxy_15m_agg30m | O2_ST2X | BE1 | 1 | 1 | 0 | 0.0 | 0 | 0 | 100.0 | 1 | 0 | 0.0 | 1/1 | 0/0 | 90m | 0.17 |
| RAGEGUY-SOL [3pWTxa...vx56] | 30m | jupiter_proxy_15m_agg30m | O2_ST2X | BE50 | 1 | 1 | 0 | 0.0 | 0 | 0 | 100.0 | 1 | 0 | 0.0 | 1/1 | 0/0 | 90m | 0.17 |
| RAGEGUY-SOL [3pWTxa...vx56] | 30m | jupiter_proxy_15m_agg30m | O2_ST2X | BE75 | 1 | 1 | 0 | 0.0 | 0 | 0 | 100.0 | 1 | 0 | 0.0 | 1/1 | 0/0 | 90m | 0.17 |
| RAGEGUY-SOL [3pWTxa...vx56] | 30m | jupiter_proxy_15m_agg30m | O2_ST2X | TP_FRACTAL | 1 | 1 | 0 | 0.0 | 0 | 0 | 100.0 | 1 | 0 | 0.0 | 1/1 | 0/0 | 90m | 0.17 |
| BULLCAT-SOL [3smCBC...BC4f] | 15m | pool_canonical | O1_SL50 | BE1 | 6 | 1 | 5 | 83.3 | 0 | 0 | 100.0 | 5 | 5 | 100.0 | 1/1 | 0/0 | 128m | 0.45 |
| BULLCAT-SOL [3smCBC...BC4f] | 15m | pool_canonical | O1_SL50 | BE50 | 6 | 3 | 2 | 33.3 | 1 | 0 | 75.0 | 5 | 2 | 40.0 | 1/2 | 1/1 | 168m | 0.20 |
| BULLCAT-SOL [3smCBC...BC4f] | 15m | pool_canonical | O1_SL50 | BE75 | 6 | 4 | 1 | 16.7 | 1 | 0 | 80.0 | 5 | 1 | 20.0 | 2/2 | 1/1 | 170m | 0.82 |
| BULLCAT-SOL [3smCBC...BC4f] | 15m | pool_canonical | O1_SL50 | TP_FRACTAL | 6 | 5 | 0 | 0.0 | 1 | 0 | 83.3 | 5 | 0 | 0.0 | 2/3 | 1/1 | 288m | 1.40 |
| BULLCAT-SOL [3smCBC...BC4f] | 15m | pool_canonical | O2_ST2X | BE1 | 6 | 1 | 5 | 83.3 | 0 | 0 | 100.0 | 5 | 5 | 100.0 | 1/1 | 0/0 | 128m | 0.38 |
| BULLCAT-SOL [3smCBC...BC4f] | 15m | pool_canonical | O2_ST2X | BE50 | 6 | 4 | 1 | 16.7 | 1 | 0 | 80.0 | 5 | 1 | 20.0 | 2/2 | 1/1 | 170m | 0.82 |
| BULLCAT-SOL [3smCBC...BC4f] | 15m | pool_canonical | O2_ST2X | BE75 | 6 | 4 | 1 | 16.7 | 1 | 0 | 80.0 | 5 | 1 | 20.0 | 2/2 | 1/1 | 170m | 0.82 |
| BULLCAT-SOL [3smCBC...BC4f] | 15m | pool_canonical | O2_ST2X | TP_FRACTAL | 6 | 5 | 0 | 0.0 | 1 | 0 | 83.3 | 5 | 0 | 0.0 | 2/3 | 1/1 | 288m | 1.35 |
| BULLCAT-SOL [3smCBC...BC4f] | 1m | pool_canonical | O1_SL50 | BE1 | 4 | 0 | 3 | 75.0 | 1 | 0 | 0.0 | 4 | 3 | 75.0 | 0/0 | 1/1 | 35m | -1.00 |
| BULLCAT-SOL [3smCBC...BC4f] | 1m | pool_canonical | O1_SL50 | BE50 | 4 | 3 | 0 | 0.0 | 1 | 0 | 75.0 | 4 | 0 | 0.0 | 3/3 | 1/1 | 68m | 0.17 |
| BULLCAT-SOL [3smCBC...BC4f] | 1m | pool_canonical | O1_SL50 | BE75 | 4 | 3 | 0 | 0.0 | 1 | 0 | 75.0 | 4 | 0 | 0.0 | 3/3 | 1/1 | 68m | 0.17 |
| BULLCAT-SOL [3smCBC...BC4f] | 1m | pool_canonical | O1_SL50 | TP_FRACTAL | 4 | 3 | 0 | 0.0 | 1 | 0 | 75.0 | 4 | 0 | 0.0 | 3/3 | 1/1 | 68m | 0.17 |
| BULLCAT-SOL [3smCBC...BC4f] | 1m | pool_canonical | O2_ST2X | BE1 | 4 | 0 | 2 | 50.0 | 2 | 0 | 0.0 | 4 | 2 | 50.0 | 0/0 | 2/2 | 14m | -2.00 |
| BULLCAT-SOL [3smCBC...BC4f] | 1m | pool_canonical | O2_ST2X | BE50 | 4 | 0 | 1 | 25.0 | 3 | 0 | 0.0 | 4 | 1 | 25.0 | 0/0 | 3/3 | 22m | -3.00 |
| BULLCAT-SOL [3smCBC...BC4f] | 1m | pool_canonical | O2_ST2X | BE75 | 4 | 1 | 0 | 0.0 | 3 | 0 | 25.0 | 4 | 0 | 0.0 | 1/1 | 1/2 | 24m | -2.43 |
| BULLCAT-SOL [3smCBC...BC4f] | 1m | pool_canonical | O2_ST2X | TP_FRACTAL | 4 | 1 | 0 | 0.0 | 3 | 0 | 25.0 | 4 | 0 | 0.0 | 1/1 | 1/2 | 24m | -2.43 |
| BULLCAT-SOL [3smCBC...BC4f] | 30m | jupiter_proxy_15m_agg30m | O1_SL50 | BE1 | 2 | 1 | 1 | 50.0 | 0 | 0 | 100.0 | 1 | 1 | 100.0 | 1/1 | 0/0 | 90m | 0.51 |
| BULLCAT-SOL [3smCBC...BC4f] | 30m | jupiter_proxy_15m_agg30m | O1_SL50 | BE50 | 2 | 2 | 0 | 0.0 | 0 | 0 | 100.0 | 1 | 0 | 0.0 | 2/2 | 0/0 | 105m | 0.98 |
| BULLCAT-SOL [3smCBC...BC4f] | 30m | jupiter_proxy_15m_agg30m | O1_SL50 | BE75 | 2 | 2 | 0 | 0.0 | 0 | 0 | 100.0 | 1 | 0 | 0.0 | 2/2 | 0/0 | 105m | 0.98 |
| BULLCAT-SOL [3smCBC...BC4f] | 30m | jupiter_proxy_15m_agg30m | O1_SL50 | TP_FRACTAL | 2 | 2 | 0 | 0.0 | 0 | 0 | 100.0 | 1 | 0 | 0.0 | 2/2 | 0/0 | 105m | 0.98 |
| BULLCAT-SOL [3smCBC...BC4f] | 30m | jupiter_proxy_15m_agg30m | O2_ST2X | BE1 | 2 | 1 | 1 | 50.0 | 0 | 0 | 100.0 | 1 | 1 | 100.0 | 1/1 | 0/0 | 90m | 0.38 |
| BULLCAT-SOL [3smCBC...BC4f] | 30m | jupiter_proxy_15m_agg30m | O2_ST2X | BE50 | 2 | 2 | 0 | 0.0 | 0 | 0 | 100.0 | 1 | 0 | 0.0 | 2/2 | 0/0 | 105m | 0.72 |
| BULLCAT-SOL [3smCBC...BC4f] | 30m | jupiter_proxy_15m_agg30m | O2_ST2X | BE75 | 2 | 2 | 0 | 0.0 | 0 | 0 | 100.0 | 1 | 0 | 0.0 | 2/2 | 0/0 | 105m | 0.72 |
| BULLCAT-SOL [3smCBC...BC4f] | 30m | jupiter_proxy_15m_agg30m | O2_ST2X | TP_FRACTAL | 2 | 2 | 0 | 0.0 | 0 | 0 | 100.0 | 1 | 0 | 0.0 | 2/2 | 0/0 | 105m | 0.72 |
| BULLCAT-SOL [3smCBC...BC4f] | 5m | pool_canonical | O1_SL50 | BE1 | 6 | 2 | 4 | 66.7 | 0 | 0 | 100.0 | 5 | 4 | 80.0 | 2/2 | 0/0 | 28m | 0.54 |
| BULLCAT-SOL [3smCBC...BC4f] | 5m | pool_canonical | O1_SL50 | BE50 | 6 | 5 | 1 | 16.7 | 0 | 0 | 100.0 | 5 | 1 | 20.0 | 5/5 | 0/0 | 102m | 1.43 |
| BULLCAT-SOL [3smCBC...BC4f] | 5m | pool_canonical | O1_SL50 | BE75 | 6 | 5 | 1 | 16.7 | 0 | 0 | 100.0 | 5 | 1 | 20.0 | 5/5 | 0/0 | 102m | 1.43 |
| BULLCAT-SOL [3smCBC...BC4f] | 5m | pool_canonical | O1_SL50 | TP_FRACTAL | 6 | 6 | 0 | 0.0 | 0 | 0 | 100.0 | 5 | 0 | 0.0 | 6/6 | 0/0 | 108m | 1.75 |
| BULLCAT-SOL [3smCBC...BC4f] | 5m | pool_canonical | O2_ST2X | BE1 | 6 | 2 | 4 | 66.7 | 0 | 0 | 100.0 | 5 | 4 | 80.0 | 2/2 | 0/0 | 28m | 0.48 |
| BULLCAT-SOL [3smCBC...BC4f] | 5m | pool_canonical | O2_ST2X | BE50 | 6 | 5 | 1 | 16.7 | 0 | 0 | 100.0 | 5 | 1 | 20.0 | 5/5 | 0/0 | 89m | 1.31 |
| BULLCAT-SOL [3smCBC...BC4f] | 5m | pool_canonical | O2_ST2X | BE75 | 6 | 6 | 0 | 0.0 | 0 | 0 | 100.0 | 5 | 0 | 0.0 | 6/6 | 0/0 | 108m | 2.23 |
| BULLCAT-SOL [3smCBC...BC4f] | 5m | pool_canonical | O2_ST2X | TP_FRACTAL | 6 | 6 | 0 | 0.0 | 0 | 0 | 100.0 | 5 | 0 | 0.0 | 6/6 | 0/0 | 108m | 2.23 |
| Tilly-SOL [4SxCFn...L2JE] | 30m | jupiter_proxy_15m_agg30m | O1_SL50 | BE1 | 2 | 1 | 1 | 50.0 | 0 | 0 | 100.0 | 2 | 1 | 50.0 | 1/1 | 0/0 | 75m | 1.40 |
| Tilly-SOL [4SxCFn...L2JE] | 30m | jupiter_proxy_15m_agg30m | O1_SL50 | BE50 | 2 | 1 | 1 | 50.0 | 0 | 0 | 100.0 | 2 | 1 | 50.0 | 1/1 | 0/0 | 75m | 1.40 |
| Tilly-SOL [4SxCFn...L2JE] | 30m | jupiter_proxy_15m_agg30m | O1_SL50 | BE75 | 2 | 1 | 1 | 50.0 | 0 | 0 | 100.0 | 2 | 1 | 50.0 | 1/1 | 0/0 | 150m | 1.40 |
| Tilly-SOL [4SxCFn...L2JE] | 30m | jupiter_proxy_15m_agg30m | O1_SL50 | TP_FRACTAL | 2 | 1 | 0 | 0.0 | 1 | 0 | 50.0 | 2 | 0 | 0.0 | 1/1 | 1/1 | 390m | 0.40 |
| Tilly-SOL [4SxCFn...L2JE] | 30m | jupiter_proxy_15m_agg30m | O2_ST2X | BE1 | 1 | 1 | 0 | 0.0 | 0 | 0 | 100.0 | 1 | 0 | 0.0 | 1/1 | 0/0 | 30m | 1.98 |
| Tilly-SOL [4SxCFn...L2JE] | 30m | jupiter_proxy_15m_agg30m | O2_ST2X | BE50 | 1 | 1 | 0 | 0.0 | 0 | 0 | 100.0 | 1 | 0 | 0.0 | 1/1 | 0/0 | 30m | 1.98 |
| Tilly-SOL [4SxCFn...L2JE] | 30m | jupiter_proxy_15m_agg30m | O2_ST2X | BE75 | 1 | 1 | 0 | 0.0 | 0 | 0 | 100.0 | 1 | 0 | 0.0 | 1/1 | 0/0 | 30m | 1.98 |
| Tilly-SOL [4SxCFn...L2JE] | 30m | jupiter_proxy_15m_agg30m | O2_ST2X | TP_FRACTAL | 1 | 1 | 0 | 0.0 | 0 | 0 | 100.0 | 1 | 0 | 0.0 | 1/1 | 0/0 | 30m | 1.98 |
| JTVO-SOL [5rtYzK...i1dv] | 15m | pool_canonical | O1_SL50 | BE1 | 50 | 12 | 34 | 68.0 | 4 | 0 | 75.0 | 44 | 34 | 77.3 | 1/11 | 1/3 | 655m | -2.56 |
| JTVO-SOL [5rtYzK...i1dv] | 15m | pool_canonical | O1_SL50 | BE50 | 50 | 35 | 5 | 10.0 | 10 | 0 | 77.8 | 44 | 5 | 11.4 | 2/20 | 1/6 | 1313m | -3.89 |
| JTVO-SOL [5rtYzK...i1dv] | 15m | pool_canonical | O1_SL50 | BE75 | 50 | 38 | 2 | 4.0 | 10 | 0 | 79.2 | 44 | 2 | 4.5 | 2/21 | 1/6 | 1458m | -3.18 |
| JTVO-SOL [5rtYzK...i1dv] | 15m | pool_canonical | O1_SL50 | TP_FRACTAL | 50 | 40 | 0 | 0.0 | 10 | 0 | 80.0 | 44 | 0 | 0.0 | 2/23 | 1/6 | 1484m | -2.99 |
| JTVO-SOL [5rtYzK...i1dv] | 15m | pool_canonical | O2_ST2X | BE1 | 50 | 11 | 30 | 60.0 | 9 | 0 | 55.0 | 44 | 30 | 68.2 | 1/5 | 1/4 | 151m | -3.25 |
| JTVO-SOL [5rtYzK...i1dv] | 15m | pool_canonical | O2_ST2X | BE50 | 50 | 23 | 13 | 26.0 | 14 | 0 | 62.2 | 44 | 13 | 29.5 | 1/10 | 1/5 | 322m | -3.85 |
| JTVO-SOL [5rtYzK...i1dv] | 15m | pool_canonical | O2_ST2X | BE75 | 50 | 28 | 5 | 10.0 | 17 | 0 | 62.2 | 44 | 5 | 11.4 | 1/11 | 1/5 | 402m | -4.17 |
| JTVO-SOL [5rtYzK...i1dv] | 15m | pool_canonical | O2_ST2X | TP_FRACTAL | 50 | 30 | 0 | 0.0 | 20 | 0 | 60.0 | 44 | 0 | 0.0 | 1/8 | 1/6 | 416m | -6.41 |
| JTVO-SOL [5rtYzK...i1dv] | 1m | pool_canonical | O1_SL50 | BE1 | 26 | 11 | 14 | 53.8 | 1 | 0 | 91.7 | 21 | 14 | 66.7 | 4/7 | 1/1 | 43m | -0.43 |
| JTVO-SOL [5rtYzK...i1dv] | 1m | pool_canonical | O1_SL50 | BE50 | 26 | 16 | 0 | 0.0 | 9 | 1 | 64.0 | 21 | 0 | 0.0 | 1/4 | 1/3 | 256m | -8.54 |
| JTVO-SOL [5rtYzK...i1dv] | 1m | pool_canonical | O1_SL50 | BE75 | 26 | 16 | 0 | 0.0 | 9 | 1 | 64.0 | 21 | 0 | 0.0 | 1/4 | 1/3 | 256m | -8.54 |
| JTVO-SOL [5rtYzK...i1dv] | 1m | pool_canonical | O1_SL50 | TP_FRACTAL | 26 | 16 | 0 | 0.0 | 9 | 1 | 64.0 | 21 | 0 | 0.0 | 1/4 | 1/3 | 256m | -8.54 |
| JTVO-SOL [5rtYzK...i1dv] | 1m | pool_canonical | O2_ST2X | BE1 | 26 | 11 | 12 | 46.2 | 3 | 0 | 78.6 | 21 | 12 | 57.1 | 1/7 | 1/1 | 5m | 4.34 |
| JTVO-SOL [5rtYzK...i1dv] | 1m | pool_canonical | O2_ST2X | BE50 | 26 | 12 | 4 | 15.4 | 10 | 0 | 54.5 | 21 | 4 | 19.0 | 1/4 | 1/3 | 11m | -2.29 |
| JTVO-SOL [5rtYzK...i1dv] | 1m | pool_canonical | O2_ST2X | BE75 | 26 | 12 | 1 | 3.8 | 13 | 0 | 48.0 | 21 | 1 | 4.8 | 1/3 | 1/4 | 13m | -5.29 |
| JTVO-SOL [5rtYzK...i1dv] | 1m | pool_canonical | O2_ST2X | TP_FRACTAL | 26 | 12 | 0 | 0.0 | 14 | 0 | 46.2 | 21 | 0 | 0.0 | 1/2 | 1/4 | 14m | -6.29 |
| JTVO-SOL [5rtYzK...i1dv] | 5m | pool_canonical | O1_SL50 | BE1 | 41 | 18 | 21 | 51.2 | 2 | 0 | 90.0 | 36 | 21 | 58.3 | 3/11 | 1/1 | 174m | -1.18 |
| JTVO-SOL [5rtYzK...i1dv] | 5m | pool_canonical | O1_SL50 | BE50 | 41 | 33 | 2 | 4.9 | 6 | 0 | 84.6 | 36 | 2 | 5.6 | 1/23 | 1/2 | 544m | -3.71 |
| JTVO-SOL [5rtYzK...i1dv] | 5m | pool_canonical | O1_SL50 | BE75 | 41 | 35 | 0 | 0.0 | 6 | 0 | 85.4 | 36 | 0 | 0.0 | 1/25 | 1/2 | 596m | -3.15 |
| JTVO-SOL [5rtYzK...i1dv] | 5m | pool_canonical | O1_SL50 | TP_FRACTAL | 41 | 35 | 0 | 0.0 | 6 | 0 | 85.4 | 36 | 0 | 0.0 | 1/25 | 1/2 | 596m | -3.15 |
| JTVO-SOL [5rtYzK...i1dv] | 5m | pool_canonical | O2_ST2X | BE1 | 41 | 16 | 18 | 43.9 | 7 | 0 | 69.6 | 36 | 18 | 50.0 | 1/3 | 1/2 | 42m | -0.72 |
| JTVO-SOL [5rtYzK...i1dv] | 5m | pool_canonical | O2_ST2X | BE50 | 41 | 20 | 6 | 14.6 | 15 | 0 | 57.1 | 36 | 6 | 16.7 | 1/4 | 1/3 | 122m | -7.50 |
| JTVO-SOL [5rtYzK...i1dv] | 5m | pool_canonical | O2_ST2X | BE75 | 41 | 21 | 2 | 4.9 | 18 | 0 | 53.8 | 36 | 2 | 5.6 | 1/4 | 1/4 | 165m | -9.82 |
| JTVO-SOL [5rtYzK...i1dv] | 5m | pool_canonical | O2_ST2X | TP_FRACTAL | 41 | 23 | 0 | 0.0 | 18 | 0 | 56.1 | 36 | 0 | 0.0 | 1/4 | 1/4 | 170m | -9.29 |
| SOLdiers-SOL [6iL24Y...id3S] | 15m | pool_canonical | O1_SL50 | BE1 | 8 | 4 | 4 | 50.0 | 0 | 0 | 100.0 | 7 | 4 | 57.1 | 4/4 | 0/0 | 49m | 1.33 |
| SOLdiers-SOL [6iL24Y...id3S] | 15m | pool_canonical | O1_SL50 | BE50 | 8 | 6 | 1 | 12.5 | 1 | 0 | 85.7 | 7 | 1 | 14.3 | 1/5 | 1/1 | 317m | 1.45 |
| SOLdiers-SOL [6iL24Y...id3S] | 15m | pool_canonical | O1_SL50 | BE75 | 8 | 6 | 1 | 12.5 | 1 | 0 | 85.7 | 7 | 1 | 14.3 | 1/5 | 1/1 | 317m | 1.45 |
| SOLdiers-SOL [6iL24Y...id3S] | 15m | pool_canonical | O1_SL50 | TP_FRACTAL | 8 | 6 | 0 | 0.0 | 1 | 1 | 85.7 | 7 | 0 | 0.0 | 1/5 | 1/1 | 330m | 1.09 |
| SOLdiers-SOL [6iL24Y...id3S] | 15m | pool_canonical | O2_ST2X | BE1 | 8 | 4 | 4 | 50.0 | 0 | 0 | 100.0 | 7 | 4 | 57.1 | 4/4 | 0/0 | 49m | 1.32 |
| SOLdiers-SOL [6iL24Y...id3S] | 15m | pool_canonical | O2_ST2X | BE50 | 8 | 6 | 0 | 0.0 | 1 | 1 | 85.7 | 7 | 0 | 0.0 | 1/5 | 1/1 | 339m | 1.09 |
| SOLdiers-SOL [6iL24Y...id3S] | 15m | pool_canonical | O2_ST2X | BE75 | 8 | 6 | 0 | 0.0 | 1 | 1 | 85.7 | 7 | 0 | 0.0 | 1/5 | 1/1 | 339m | 1.09 |
| SOLdiers-SOL [6iL24Y...id3S] | 15m | pool_canonical | O2_ST2X | TP_FRACTAL | 8 | 6 | 0 | 0.0 | 1 | 1 | 85.7 | 7 | 0 | 0.0 | 1/5 | 1/1 | 339m | 1.09 |
| SOLdiers-SOL [6iL24Y...id3S] | 1m | pool_canonical | O1_SL50 | BE1 | 36 | 12 | 22 | 61.1 | 1 | 1 | 92.3 | 31 | 22 | 71.0 | 2/10 | 1/1 | 52m | -0.28 |
| SOLdiers-SOL [6iL24Y...id3S] | 1m | pool_canonical | O1_SL50 | BE50 | 36 | 31 | 2 | 5.6 | 1 | 2 | 96.9 | 31 | 2 | 6.5 | 9/22 | 1/1 | 90m | 2.79 |
| SOLdiers-SOL [6iL24Y...id3S] | 1m | pool_canonical | O1_SL50 | BE75 | 36 | 33 | 0 | 0.0 | 1 | 2 | 97.1 | 31 | 0 | 0.0 | 10/23 | 1/1 | 92m | 3.99 |
| SOLdiers-SOL [6iL24Y...id3S] | 1m | pool_canonical | O1_SL50 | TP_FRACTAL | 36 | 33 | 0 | 0.0 | 1 | 2 | 97.1 | 31 | 0 | 0.0 | 10/23 | 1/1 | 92m | 3.99 |
| SOLdiers-SOL [6iL24Y...id3S] | 1m | pool_canonical | O2_ST2X | BE1 | 36 | 8 | 16 | 44.4 | 12 | 0 | 40.0 | 31 | 16 | 51.6 | 1/2 | 1/5 | 8m | -6.25 |
| SOLdiers-SOL [6iL24Y...id3S] | 1m | pool_canonical | O2_ST2X | BE50 | 36 | 15 | 9 | 25.0 | 12 | 0 | 55.6 | 31 | 9 | 29.0 | 1/5 | 1/4 | 14m | -1.66 |
| SOLdiers-SOL [6iL24Y...id3S] | 1m | pool_canonical | O2_ST2X | BE75 | 36 | 16 | 6 | 16.7 | 14 | 0 | 53.3 | 31 | 6 | 19.4 | 1/5 | 1/4 | 16m | 0.32 |
| SOLdiers-SOL [6iL24Y...id3S] | 1m | pool_canonical | O2_ST2X | TP_FRACTAL | 36 | 20 | 0 | 0.0 | 16 | 0 | 55.6 | 31 | 0 | 0.0 | 1/7 | 1/4 | 18m | 0.74 |
| SOLdiers-SOL [6iL24Y...id3S] | 30m | jupiter_proxy_15m_agg30m | O1_SL50 | BE1 | 2 | 1 | 0 | 0.0 | 0 | 1 | 100.0 | 2 | 0 | 0.0 | 1/1 | 0/0 | 510m | -0.44 |
| SOLdiers-SOL [6iL24Y...id3S] | 30m | jupiter_proxy_15m_agg30m | O1_SL50 | BE50 | 2 | 1 | 0 | 0.0 | 0 | 1 | 100.0 | 2 | 0 | 0.0 | 1/1 | 0/0 | 510m | -0.44 |
| SOLdiers-SOL [6iL24Y...id3S] | 30m | jupiter_proxy_15m_agg30m | O1_SL50 | BE75 | 2 | 1 | 0 | 0.0 | 0 | 1 | 100.0 | 2 | 0 | 0.0 | 1/1 | 0/0 | 510m | -0.44 |
| SOLdiers-SOL [6iL24Y...id3S] | 30m | jupiter_proxy_15m_agg30m | O1_SL50 | TP_FRACTAL | 2 | 1 | 0 | 0.0 | 0 | 1 | 100.0 | 2 | 0 | 0.0 | 1/1 | 0/0 | 510m | -0.44 |
| SOLdiers-SOL [6iL24Y...id3S] | 30m | jupiter_proxy_15m_agg30m | O2_ST2X | BE1 | 2 | 1 | 0 | 0.0 | 0 | 1 | 100.0 | 2 | 0 | 0.0 | 1/1 | 0/0 | 510m | -0.10 |
| SOLdiers-SOL [6iL24Y...id3S] | 30m | jupiter_proxy_15m_agg30m | O2_ST2X | BE50 | 2 | 1 | 0 | 0.0 | 0 | 1 | 100.0 | 2 | 0 | 0.0 | 1/1 | 0/0 | 510m | -0.10 |
| SOLdiers-SOL [6iL24Y...id3S] | 30m | jupiter_proxy_15m_agg30m | O2_ST2X | BE75 | 2 | 1 | 0 | 0.0 | 0 | 1 | 100.0 | 2 | 0 | 0.0 | 1/1 | 0/0 | 510m | -0.10 |
| SOLdiers-SOL [6iL24Y...id3S] | 30m | jupiter_proxy_15m_agg30m | O2_ST2X | TP_FRACTAL | 2 | 1 | 0 | 0.0 | 0 | 1 | 100.0 | 2 | 0 | 0.0 | 1/1 | 0/0 | 510m | -0.10 |
| SOLdiers-SOL [6iL24Y...id3S] | 5m | pool_canonical | O1_SL50 | BE1 | 21 | 4 | 17 | 81.0 | 0 | 0 | 100.0 | 21 | 17 | 81.0 | 4/4 | 0/0 | 40m | 0.88 |
| SOLdiers-SOL [6iL24Y...id3S] | 5m | pool_canonical | O1_SL50 | BE50 | 21 | 14 | 5 | 23.8 | 2 | 0 | 87.5 | 21 | 5 | 23.8 | 4/10 | 2/2 | 219m | 1.78 |
| SOLdiers-SOL [6iL24Y...id3S] | 5m | pool_canonical | O1_SL50 | BE75 | 21 | 16 | 2 | 9.5 | 2 | 1 | 88.9 | 21 | 2 | 9.5 | 5/11 | 2/2 | 228m | 3.03 |
| SOLdiers-SOL [6iL24Y...id3S] | 5m | pool_canonical | O1_SL50 | TP_FRACTAL | 21 | 17 | 0 | 0.0 | 2 | 2 | 89.5 | 21 | 0 | 0.0 | 5/12 | 2/2 | 264m | 3.90 |
| SOLdiers-SOL [6iL24Y...id3S] | 5m | pool_canonical | O2_ST2X | BE1 | 21 | 3 | 16 | 76.2 | 2 | 0 | 60.0 | 21 | 16 | 76.2 | 1/2 | 2/2 | 28m | -1.02 |
| SOLdiers-SOL [6iL24Y...id3S] | 5m | pool_canonical | O2_ST2X | BE50 | 21 | 10 | 6 | 28.6 | 5 | 0 | 66.7 | 21 | 6 | 28.6 | 1/4 | 1/2 | 72m | -0.23 |
| SOLdiers-SOL [6iL24Y...id3S] | 5m | pool_canonical | O2_ST2X | BE75 | 21 | 11 | 4 | 19.0 | 6 | 0 | 64.7 | 21 | 4 | 19.0 | 1/4 | 2/2 | 73m | -0.85 |
| SOLdiers-SOL [6iL24Y...id3S] | 5m | pool_canonical | O2_ST2X | TP_FRACTAL | 21 | 12 | 0 | 0.0 | 9 | 0 | 57.1 | 21 | 0 | 0.0 | 1/5 | 2/3 | 98m | -2.92 |
| BULLCAT-SOL [7D7T92...3ZUk] | 15m | pool_canonical | O1_SL50 | BE1 | 3 | 1 | 2 | 66.7 | 0 | 0 | 100.0 | 3 | 2 | 66.7 | 1/1 | 0/0 | 40m | 0.25 |
| BULLCAT-SOL [7D7T92...3ZUk] | 15m | pool_canonical | O1_SL50 | BE50 | 3 | 3 | 0 | 0.0 | 0 | 0 | 100.0 | 3 | 0 | 0.0 | 3/3 | 0/0 | 100m | 1.08 |
| BULLCAT-SOL [7D7T92...3ZUk] | 15m | pool_canonical | O1_SL50 | BE75 | 3 | 3 | 0 | 0.0 | 0 | 0 | 100.0 | 3 | 0 | 0.0 | 3/3 | 0/0 | 100m | 1.08 |
| BULLCAT-SOL [7D7T92...3ZUk] | 15m | pool_canonical | O1_SL50 | TP_FRACTAL | 3 | 3 | 0 | 0.0 | 0 | 0 | 100.0 | 3 | 0 | 0.0 | 3/3 | 0/0 | 100m | 1.08 |
| BULLCAT-SOL [7D7T92...3ZUk] | 15m | pool_canonical | O2_ST2X | BE1 | 3 | 1 | 2 | 66.7 | 0 | 0 | 100.0 | 3 | 2 | 66.7 | 1/1 | 0/0 | 40m | 0.21 |
| BULLCAT-SOL [7D7T92...3ZUk] | 15m | pool_canonical | O2_ST2X | BE50 | 3 | 3 | 0 | 0.0 | 0 | 0 | 100.0 | 3 | 0 | 0.0 | 3/3 | 0/0 | 100m | 1.37 |
| BULLCAT-SOL [7D7T92...3ZUk] | 15m | pool_canonical | O2_ST2X | BE75 | 3 | 3 | 0 | 0.0 | 0 | 0 | 100.0 | 3 | 0 | 0.0 | 3/3 | 0/0 | 100m | 1.37 |
| BULLCAT-SOL [7D7T92...3ZUk] | 15m | pool_canonical | O2_ST2X | TP_FRACTAL | 3 | 3 | 0 | 0.0 | 0 | 0 | 100.0 | 3 | 0 | 0.0 | 3/3 | 0/0 | 100m | 1.37 |
| BULLCAT-SOL [7D7T92...3ZUk] | 1m | pool_canonical | O1_SL50 | BE1 | 22 | 10 | 12 | 54.5 | 0 | 0 | 100.0 | 20 | 12 | 60.0 | 10/10 | 0/0 | 13m | 0.70 |
| BULLCAT-SOL [7D7T92...3ZUk] | 1m | pool_canonical | O1_SL50 | BE50 | 22 | 18 | 2 | 9.1 | 2 | 0 | 90.0 | 20 | 2 | 10.0 | 4/8 | 1/1 | 54m | -0.17 |
| BULLCAT-SOL [7D7T92...3ZUk] | 1m | pool_canonical | O1_SL50 | BE75 | 22 | 18 | 0 | 0.0 | 4 | 0 | 81.8 | 20 | 0 | 0.0 | 4/8 | 1/3 | 72m | -2.17 |
| BULLCAT-SOL [7D7T92...3ZUk] | 1m | pool_canonical | O1_SL50 | TP_FRACTAL | 22 | 18 | 0 | 0.0 | 4 | 0 | 81.8 | 20 | 0 | 0.0 | 4/8 | 1/3 | 72m | -2.17 |
| BULLCAT-SOL [7D7T92...3ZUk] | 1m | pool_canonical | O2_ST2X | BE1 | 22 | 9 | 8 | 36.4 | 5 | 0 | 64.3 | 20 | 8 | 40.0 | 1/5 | 1/3 | 7m | -3.00 |
| BULLCAT-SOL [7D7T92...3ZUk] | 1m | pool_canonical | O2_ST2X | BE50 | 22 | 10 | 4 | 18.2 | 8 | 0 | 55.6 | 20 | 4 | 20.0 | 1/4 | 1/2 | 9m | -5.59 |
| BULLCAT-SOL [7D7T92...3ZUk] | 1m | pool_canonical | O2_ST2X | BE75 | 22 | 10 | 3 | 13.6 | 9 | 0 | 52.6 | 20 | 3 | 15.0 | 1/4 | 1/3 | 9m | -6.59 |
| BULLCAT-SOL [7D7T92...3ZUk] | 1m | pool_canonical | O2_ST2X | TP_FRACTAL | 22 | 10 | 0 | 0.0 | 12 | 0 | 45.5 | 20 | 0 | 0.0 | 1/4 | 2/3 | 11m | -9.59 |
| BULLCAT-SOL [7D7T92...3ZUk] | 30m | jupiter_proxy_15m_agg30m | O1_SL50 | BE1 | 2 | 1 | 1 | 50.0 | 0 | 0 | 100.0 | 1 | 1 | 100.0 | 1/1 | 0/0 | 90m | 0.51 |
| BULLCAT-SOL [7D7T92...3ZUk] | 30m | jupiter_proxy_15m_agg30m | O1_SL50 | BE50 | 2 | 2 | 0 | 0.0 | 0 | 0 | 100.0 | 1 | 0 | 0.0 | 2/2 | 0/0 | 105m | 0.98 |
| BULLCAT-SOL [7D7T92...3ZUk] | 30m | jupiter_proxy_15m_agg30m | O1_SL50 | BE75 | 2 | 2 | 0 | 0.0 | 0 | 0 | 100.0 | 1 | 0 | 0.0 | 2/2 | 0/0 | 105m | 0.98 |
| BULLCAT-SOL [7D7T92...3ZUk] | 30m | jupiter_proxy_15m_agg30m | O1_SL50 | TP_FRACTAL | 2 | 2 | 0 | 0.0 | 0 | 0 | 100.0 | 1 | 0 | 0.0 | 2/2 | 0/0 | 105m | 0.98 |
| BULLCAT-SOL [7D7T92...3ZUk] | 30m | jupiter_proxy_15m_agg30m | O2_ST2X | BE1 | 2 | 1 | 1 | 50.0 | 0 | 0 | 100.0 | 1 | 1 | 100.0 | 1/1 | 0/0 | 90m | 0.38 |
| BULLCAT-SOL [7D7T92...3ZUk] | 30m | jupiter_proxy_15m_agg30m | O2_ST2X | BE50 | 2 | 2 | 0 | 0.0 | 0 | 0 | 100.0 | 1 | 0 | 0.0 | 2/2 | 0/0 | 105m | 0.72 |
| BULLCAT-SOL [7D7T92...3ZUk] | 30m | jupiter_proxy_15m_agg30m | O2_ST2X | BE75 | 2 | 2 | 0 | 0.0 | 0 | 0 | 100.0 | 1 | 0 | 0.0 | 2/2 | 0/0 | 105m | 0.72 |
| BULLCAT-SOL [7D7T92...3ZUk] | 30m | jupiter_proxy_15m_agg30m | O2_ST2X | TP_FRACTAL | 2 | 2 | 0 | 0.0 | 0 | 0 | 100.0 | 1 | 0 | 0.0 | 2/2 | 0/0 | 105m | 0.72 |
| BULLCAT-SOL [7D7T92...3ZUk] | 5m | pool_canonical | O1_SL50 | BE1 | 11 | 3 | 7 | 63.6 | 1 | 0 | 75.0 | 10 | 7 | 70.0 | 3/3 | 1/1 | 70m | -0.05 |
| BULLCAT-SOL [7D7T92...3ZUk] | 5m | pool_canonical | O1_SL50 | BE50 | 11 | 8 | 0 | 0.0 | 3 | 0 | 72.7 | 10 | 0 | 0.0 | 2/3 | 1/1 | 330m | -0.95 |
| BULLCAT-SOL [7D7T92...3ZUk] | 5m | pool_canonical | O1_SL50 | BE75 | 11 | 8 | 0 | 0.0 | 3 | 0 | 72.7 | 10 | 0 | 0.0 | 2/3 | 1/1 | 330m | -0.95 |
| BULLCAT-SOL [7D7T92...3ZUk] | 5m | pool_canonical | O1_SL50 | TP_FRACTAL | 11 | 8 | 0 | 0.0 | 3 | 0 | 72.7 | 10 | 0 | 0.0 | 2/3 | 1/1 | 330m | -0.95 |
| BULLCAT-SOL [7D7T92...3ZUk] | 5m | pool_canonical | O2_ST2X | BE1 | 11 | 2 | 6 | 54.5 | 3 | 0 | 40.0 | 10 | 6 | 60.0 | 2/2 | 3/3 | 67m | 0.16 |
| BULLCAT-SOL [7D7T92...3ZUk] | 5m | pool_canonical | O2_ST2X | BE50 | 11 | 4 | 4 | 36.4 | 3 | 0 | 57.1 | 10 | 4 | 40.0 | 2/2 | 1/2 | 107m | 1.41 |
| BULLCAT-SOL [7D7T92...3ZUk] | 5m | pool_canonical | O2_ST2X | BE75 | 11 | 7 | 1 | 9.1 | 3 | 0 | 70.0 | 10 | 1 | 10.0 | 2/3 | 1/1 | 173m | 2.60 |
| BULLCAT-SOL [7D7T92...3ZUk] | 5m | pool_canonical | O2_ST2X | TP_FRACTAL | 11 | 7 | 0 | 0.0 | 4 | 0 | 63.6 | 10 | 0 | 0.0 | 2/3 | 1/2 | 175m | 1.60 |
| NEEGY-SOL [9mZ2tE...WSmf] | 15m | pool_canonical | O1_SL50 | BE1 | 1 | 0 | 0 | 0.0 | 1 | 0 | 0.0 | 1 | 0 | 0.0 | 0/0 | 1/1 | 420m | -1.00 |
| NEEGY-SOL [9mZ2tE...WSmf] | 15m | pool_canonical | O1_SL50 | BE50 | 1 | 0 | 0 | 0.0 | 1 | 0 | 0.0 | 1 | 0 | 0.0 | 0/0 | 1/1 | 420m | -1.00 |
| NEEGY-SOL [9mZ2tE...WSmf] | 15m | pool_canonical | O1_SL50 | BE75 | 1 | 0 | 0 | 0.0 | 1 | 0 | 0.0 | 1 | 0 | 0.0 | 0/0 | 1/1 | 420m | -1.00 |
| NEEGY-SOL [9mZ2tE...WSmf] | 15m | pool_canonical | O1_SL50 | TP_FRACTAL | 1 | 0 | 0 | 0.0 | 1 | 0 | 0.0 | 1 | 0 | 0.0 | 0/0 | 1/1 | 420m | -1.00 |
| NEEGY-SOL [9mZ2tE...WSmf] | 15m | pool_canonical | O2_ST2X | BE1 | 1 | 0 | 0 | 0.0 | 1 | 0 | 0.0 | 1 | 0 | 0.0 | 0/0 | 1/1 | 15m | -1.00 |
| NEEGY-SOL [9mZ2tE...WSmf] | 15m | pool_canonical | O2_ST2X | BE50 | 1 | 0 | 0 | 0.0 | 1 | 0 | 0.0 | 1 | 0 | 0.0 | 0/0 | 1/1 | 15m | -1.00 |
| NEEGY-SOL [9mZ2tE...WSmf] | 15m | pool_canonical | O2_ST2X | BE75 | 1 | 0 | 0 | 0.0 | 1 | 0 | 0.0 | 1 | 0 | 0.0 | 0/0 | 1/1 | 15m | -1.00 |
| NEEGY-SOL [9mZ2tE...WSmf] | 15m | pool_canonical | O2_ST2X | TP_FRACTAL | 1 | 0 | 0 | 0.0 | 1 | 0 | 0.0 | 1 | 0 | 0.0 | 0/0 | 1/1 | 15m | -1.00 |
| NEEGY-SOL [9mZ2tE...WSmf] | 1m | pool_canonical | O1_SL50 | BE1 | 7 | 3 | 4 | 57.1 | 0 | 0 | 100.0 | 6 | 4 | 66.7 | 3/3 | 0/0 | 5m | 0.33 |
| NEEGY-SOL [9mZ2tE...WSmf] | 1m | pool_canonical | O1_SL50 | BE50 | 7 | 5 | 1 | 14.3 | 0 | 1 | 100.0 | 6 | 1 | 16.7 | 5/5 | 0/0 | 20m | 0.30 |
| NEEGY-SOL [9mZ2tE...WSmf] | 1m | pool_canonical | O1_SL50 | BE75 | 7 | 6 | 0 | 0.0 | 0 | 1 | 100.0 | 6 | 0 | 0.0 | 6/6 | 0/0 | 20m | 0.49 |
| NEEGY-SOL [9mZ2tE...WSmf] | 1m | pool_canonical | O1_SL50 | TP_FRACTAL | 7 | 6 | 0 | 0.0 | 0 | 1 | 100.0 | 6 | 0 | 0.0 | 6/6 | 0/0 | 20m | 0.49 |
| NEEGY-SOL [9mZ2tE...WSmf] | 1m | pool_canonical | O2_ST2X | BE1 | 7 | 3 | 4 | 57.1 | 0 | 0 | 100.0 | 6 | 4 | 66.7 | 3/3 | 0/0 | 5m | 1.59 |
| NEEGY-SOL [9mZ2tE...WSmf] | 1m | pool_canonical | O2_ST2X | BE50 | 7 | 4 | 1 | 14.3 | 2 | 0 | 66.7 | 6 | 1 | 16.7 | 1/3 | 1/1 | 7m | -0.10 |
| NEEGY-SOL [9mZ2tE...WSmf] | 1m | pool_canonical | O2_ST2X | BE75 | 7 | 4 | 0 | 0.0 | 3 | 0 | 57.1 | 6 | 0 | 0.0 | 1/3 | 1/1 | 8m | -1.10 |
| NEEGY-SOL [9mZ2tE...WSmf] | 1m | pool_canonical | O2_ST2X | TP_FRACTAL | 7 | 4 | 0 | 0.0 | 3 | 0 | 57.1 | 6 | 0 | 0.0 | 1/3 | 1/1 | 8m | -1.10 |
| NEEGY-SOL [9mZ2tE...WSmf] | 30m | jupiter_proxy_15m_agg30m | O1_SL50 | BE1 | 5 | 1 | 3 | 60.0 | 1 | 0 | 50.0 | 5 | 3 | 60.0 | 1/1 | 1/1 | 126m | -0.13 |
| NEEGY-SOL [9mZ2tE...WSmf] | 30m | jupiter_proxy_15m_agg30m | O1_SL50 | BE50 | 5 | 4 | 0 | 0.0 | 1 | 0 | 80.0 | 5 | 0 | 0.0 | 4/4 | 1/1 | 192m | 4.46 |
| NEEGY-SOL [9mZ2tE...WSmf] | 30m | jupiter_proxy_15m_agg30m | O1_SL50 | BE75 | 5 | 4 | 0 | 0.0 | 1 | 0 | 80.0 | 5 | 0 | 0.0 | 4/4 | 1/1 | 192m | 4.46 |
| NEEGY-SOL [9mZ2tE...WSmf] | 30m | jupiter_proxy_15m_agg30m | O1_SL50 | TP_FRACTAL | 5 | 4 | 0 | 0.0 | 1 | 0 | 80.0 | 5 | 0 | 0.0 | 4/4 | 1/1 | 192m | 4.46 |
| NEEGY-SOL [9mZ2tE...WSmf] | 30m | jupiter_proxy_15m_agg30m | O2_ST2X | BE1 | 3 | 0 | 2 | 66.7 | 0 | 1 | 0.0 | 3 | 2 | 66.7 | 0/0 | 0/0 | 370m | -0.67 |
| NEEGY-SOL [9mZ2tE...WSmf] | 30m | jupiter_proxy_15m_agg30m | O2_ST2X | BE50 | 3 | 2 | 0 | 0.0 | 0 | 1 | 100.0 | 3 | 0 | 0.0 | 2/2 | 0/0 | 410m | 1.93 |
| NEEGY-SOL [9mZ2tE...WSmf] | 30m | jupiter_proxy_15m_agg30m | O2_ST2X | BE75 | 3 | 2 | 0 | 0.0 | 0 | 1 | 100.0 | 3 | 0 | 0.0 | 2/2 | 0/0 | 410m | 1.93 |
| NEEGY-SOL [9mZ2tE...WSmf] | 30m | jupiter_proxy_15m_agg30m | O2_ST2X | TP_FRACTAL | 3 | 2 | 0 | 0.0 | 0 | 1 | 100.0 | 3 | 0 | 0.0 | 2/2 | 0/0 | 410m | 1.93 |
| NEEGY-SOL [9mZ2tE...WSmf] | 5m | pool_canonical | O1_SL50 | BE1 | 3 | 1 | 2 | 66.7 | 0 | 0 | 100.0 | 3 | 2 | 66.7 | 1/1 | 0/0 | 63m | 0.11 |
| NEEGY-SOL [9mZ2tE...WSmf] | 5m | pool_canonical | O1_SL50 | BE50 | 3 | 1 | 1 | 33.3 | 1 | 0 | 50.0 | 3 | 1 | 33.3 | 1/1 | 1/1 | 127m | -0.89 |
| NEEGY-SOL [9mZ2tE...WSmf] | 5m | pool_canonical | O1_SL50 | BE75 | 3 | 2 | 0 | 0.0 | 1 | 0 | 66.7 | 3 | 0 | 0.0 | 1/1 | 1/1 | 130m | -0.43 |
| NEEGY-SOL [9mZ2tE...WSmf] | 5m | pool_canonical | O1_SL50 | TP_FRACTAL | 3 | 2 | 0 | 0.0 | 1 | 0 | 66.7 | 3 | 0 | 0.0 | 1/1 | 1/1 | 130m | -0.43 |
| NEEGY-SOL [9mZ2tE...WSmf] | 5m | pool_canonical | O2_ST2X | BE1 | 3 | 1 | 1 | 33.3 | 1 | 0 | 50.0 | 3 | 1 | 33.3 | 1/1 | 1/1 | 35m | -0.79 |
| NEEGY-SOL [9mZ2tE...WSmf] | 5m | pool_canonical | O2_ST2X | BE50 | 3 | 1 | 1 | 33.3 | 1 | 0 | 50.0 | 3 | 1 | 33.3 | 1/1 | 1/1 | 48m | -0.79 |
| NEEGY-SOL [9mZ2tE...WSmf] | 5m | pool_canonical | O2_ST2X | BE75 | 3 | 1 | 1 | 33.3 | 1 | 0 | 50.0 | 3 | 1 | 33.3 | 1/1 | 1/1 | 48m | -0.79 |
| NEEGY-SOL [9mZ2tE...WSmf] | 5m | pool_canonical | O2_ST2X | TP_FRACTAL | 3 | 1 | 0 | 0.0 | 2 | 0 | 33.3 | 3 | 0 | 0.0 | 1/1 | 2/2 | 70m | -1.79 |
| BULLCAT-SOL [AFFuFY...Ugmd] | 15m | pool_canonical | O1_SL50 | BE1 | 3 | 0 | 3 | 100.0 | 0 | 0 | 0.0 | 3 | 3 | 100.0 | 0/0 | 0/0 | 45m | 0.00 |
| BULLCAT-SOL [AFFuFY...Ugmd] | 15m | pool_canonical | O1_SL50 | BE50 | 3 | 2 | 0 | 0.0 | 1 | 0 | 66.7 | 3 | 0 | 0.0 | 2/2 | 1/1 | 145m | -0.20 |
| BULLCAT-SOL [AFFuFY...Ugmd] | 15m | pool_canonical | O1_SL50 | BE75 | 3 | 2 | 0 | 0.0 | 1 | 0 | 66.7 | 3 | 0 | 0.0 | 2/2 | 1/1 | 145m | -0.20 |
| BULLCAT-SOL [AFFuFY...Ugmd] | 15m | pool_canonical | O1_SL50 | TP_FRACTAL | 3 | 2 | 0 | 0.0 | 1 | 0 | 66.7 | 3 | 0 | 0.0 | 2/2 | 1/1 | 145m | -0.20 |
| BULLCAT-SOL [AFFuFY...Ugmd] | 15m | pool_canonical | O2_ST2X | BE1 | 3 | 0 | 3 | 100.0 | 0 | 0 | 0.0 | 3 | 3 | 100.0 | 0/0 | 0/0 | 45m | 0.00 |
| BULLCAT-SOL [AFFuFY...Ugmd] | 15m | pool_canonical | O2_ST2X | BE50 | 3 | 2 | 0 | 0.0 | 1 | 0 | 66.7 | 3 | 0 | 0.0 | 2/2 | 1/1 | 125m | -0.07 |
| BULLCAT-SOL [AFFuFY...Ugmd] | 15m | pool_canonical | O2_ST2X | BE75 | 3 | 2 | 0 | 0.0 | 1 | 0 | 66.7 | 3 | 0 | 0.0 | 2/2 | 1/1 | 125m | -0.07 |
| BULLCAT-SOL [AFFuFY...Ugmd] | 15m | pool_canonical | O2_ST2X | TP_FRACTAL | 3 | 2 | 0 | 0.0 | 1 | 0 | 66.7 | 3 | 0 | 0.0 | 2/2 | 1/1 | 125m | -0.07 |
| BULLCAT-SOL [AFFuFY...Ugmd] | 1m | pool_canonical | O1_SL50 | BE1 | 25 | 10 | 14 | 56.0 | 1 | 0 | 90.9 | 21 | 14 | 66.7 | 10/10 | 1/1 | 26m | -0.18 |
| BULLCAT-SOL [AFFuFY...Ugmd] | 1m | pool_canonical | O1_SL50 | BE50 | 25 | 19 | 2 | 8.0 | 4 | 0 | 82.6 | 21 | 2 | 9.5 | 3/10 | 1/1 | 80m | -2.03 |
| BULLCAT-SOL [AFFuFY...Ugmd] | 1m | pool_canonical | O1_SL50 | BE75 | 25 | 21 | 0 | 0.0 | 4 | 0 | 84.0 | 21 | 0 | 0.0 | 3/10 | 1/1 | 102m | -1.84 |
| BULLCAT-SOL [AFFuFY...Ugmd] | 1m | pool_canonical | O1_SL50 | TP_FRACTAL | 25 | 21 | 0 | 0.0 | 4 | 0 | 84.0 | 21 | 0 | 0.0 | 3/10 | 1/1 | 102m | -1.84 |
| BULLCAT-SOL [AFFuFY...Ugmd] | 1m | pool_canonical | O2_ST2X | BE1 | 25 | 7 | 9 | 36.0 | 9 | 0 | 43.8 | 21 | 9 | 42.9 | 1/2 | 1/4 | 6m | -6.77 |
| BULLCAT-SOL [AFFuFY...Ugmd] | 1m | pool_canonical | O2_ST2X | BE50 | 25 | 12 | 1 | 4.0 | 12 | 0 | 50.0 | 21 | 1 | 4.8 | 1/3 | 1/3 | 10m | -7.32 |
| BULLCAT-SOL [AFFuFY...Ugmd] | 1m | pool_canonical | O2_ST2X | BE75 | 25 | 12 | 0 | 0.0 | 13 | 0 | 48.0 | 21 | 0 | 0.0 | 1/3 | 1/3 | 11m | -8.32 |
| BULLCAT-SOL [AFFuFY...Ugmd] | 1m | pool_canonical | O2_ST2X | TP_FRACTAL | 25 | 12 | 0 | 0.0 | 13 | 0 | 48.0 | 21 | 0 | 0.0 | 1/3 | 1/3 | 11m | -8.32 |
| BULLCAT-SOL [AFFuFY...Ugmd] | 30m | jupiter_proxy_15m_agg30m | O1_SL50 | BE1 | 2 | 1 | 1 | 50.0 | 0 | 0 | 100.0 | 1 | 1 | 100.0 | 1/1 | 0/0 | 90m | 0.51 |
| BULLCAT-SOL [AFFuFY...Ugmd] | 30m | jupiter_proxy_15m_agg30m | O1_SL50 | BE50 | 2 | 2 | 0 | 0.0 | 0 | 0 | 100.0 | 1 | 0 | 0.0 | 2/2 | 0/0 | 105m | 0.98 |
| BULLCAT-SOL [AFFuFY...Ugmd] | 30m | jupiter_proxy_15m_agg30m | O1_SL50 | BE75 | 2 | 2 | 0 | 0.0 | 0 | 0 | 100.0 | 1 | 0 | 0.0 | 2/2 | 0/0 | 105m | 0.98 |
| BULLCAT-SOL [AFFuFY...Ugmd] | 30m | jupiter_proxy_15m_agg30m | O1_SL50 | TP_FRACTAL | 2 | 2 | 0 | 0.0 | 0 | 0 | 100.0 | 1 | 0 | 0.0 | 2/2 | 0/0 | 105m | 0.98 |
| BULLCAT-SOL [AFFuFY...Ugmd] | 30m | jupiter_proxy_15m_agg30m | O2_ST2X | BE1 | 2 | 1 | 1 | 50.0 | 0 | 0 | 100.0 | 1 | 1 | 100.0 | 1/1 | 0/0 | 90m | 0.38 |
| BULLCAT-SOL [AFFuFY...Ugmd] | 30m | jupiter_proxy_15m_agg30m | O2_ST2X | BE50 | 2 | 2 | 0 | 0.0 | 0 | 0 | 100.0 | 1 | 0 | 0.0 | 2/2 | 0/0 | 105m | 0.72 |
| BULLCAT-SOL [AFFuFY...Ugmd] | 30m | jupiter_proxy_15m_agg30m | O2_ST2X | BE75 | 2 | 2 | 0 | 0.0 | 0 | 0 | 100.0 | 1 | 0 | 0.0 | 2/2 | 0/0 | 105m | 0.72 |
| BULLCAT-SOL [AFFuFY...Ugmd] | 30m | jupiter_proxy_15m_agg30m | O2_ST2X | TP_FRACTAL | 2 | 2 | 0 | 0.0 | 0 | 0 | 100.0 | 1 | 0 | 0.0 | 2/2 | 0/0 | 105m | 0.72 |
| BULLCAT-SOL [AFFuFY...Ugmd] | 5m | pool_canonical | O1_SL50 | BE1 | 13 | 5 | 8 | 61.5 | 0 | 0 | 100.0 | 12 | 8 | 66.7 | 5/5 | 0/0 | 49m | 0.52 |
| BULLCAT-SOL [AFFuFY...Ugmd] | 5m | pool_canonical | O1_SL50 | BE50 | 13 | 11 | 1 | 7.7 | 1 | 0 | 91.7 | 12 | 1 | 8.3 | 5/6 | 1/1 | 195m | 0.73 |
| BULLCAT-SOL [AFFuFY...Ugmd] | 5m | pool_canonical | O1_SL50 | BE75 | 13 | 11 | 1 | 7.7 | 1 | 0 | 91.7 | 12 | 1 | 8.3 | 5/6 | 1/1 | 195m | 0.73 |
| BULLCAT-SOL [AFFuFY...Ugmd] | 5m | pool_canonical | O1_SL50 | TP_FRACTAL | 13 | 11 | 0 | 0.0 | 2 | 0 | 84.6 | 12 | 0 | 0.0 | 2/6 | 1/1 | 207m | -0.27 |
| BULLCAT-SOL [AFFuFY...Ugmd] | 5m | pool_canonical | O2_ST2X | BE1 | 13 | 5 | 6 | 46.2 | 2 | 0 | 71.4 | 12 | 6 | 50.0 | 2/3 | 2/2 | 42m | -1.21 |
| BULLCAT-SOL [AFFuFY...Ugmd] | 5m | pool_canonical | O2_ST2X | BE50 | 13 | 6 | 5 | 38.5 | 2 | 0 | 75.0 | 12 | 5 | 41.7 | 3/3 | 2/2 | 52m | -0.40 |
| BULLCAT-SOL [AFFuFY...Ugmd] | 5m | pool_canonical | O2_ST2X | BE75 | 13 | 9 | 1 | 7.7 | 3 | 0 | 75.0 | 12 | 1 | 8.3 | 1/5 | 1/1 | 78m | -0.48 |
| BULLCAT-SOL [AFFuFY...Ugmd] | 5m | pool_canonical | O2_ST2X | TP_FRACTAL | 13 | 9 | 0 | 0.0 | 4 | 0 | 69.2 | 12 | 0 | 0.0 | 1/3 | 1/1 | 78m | -1.48 |
| Tilly-SOL [BMi3TK...k3kh] | 15m | pool_canonical | O1_SL50 | BE1 | 2 | 0 | 2 | 100.0 | 0 | 0 | 0.0 | 2 | 2 | 100.0 | 0/0 | 0/0 | 45m | 0.00 |
| Tilly-SOL [BMi3TK...k3kh] | 15m | pool_canonical | O1_SL50 | BE50 | 2 | 0 | 0 | 0.0 | 1 | 1 | 0.0 | 2 | 0 | 0.0 | 0/0 | 1/1 | 292m | -1.82 |
| Tilly-SOL [BMi3TK...k3kh] | 15m | pool_canonical | O1_SL50 | BE75 | 2 | 0 | 0 | 0.0 | 1 | 1 | 0.0 | 2 | 0 | 0.0 | 0/0 | 1/1 | 292m | -1.82 |
| Tilly-SOL [BMi3TK...k3kh] | 15m | pool_canonical | O1_SL50 | TP_FRACTAL | 2 | 0 | 0 | 0.0 | 1 | 1 | 0.0 | 2 | 0 | 0.0 | 0/0 | 1/1 | 292m | -1.82 |
| Tilly-SOL [BMi3TK...k3kh] | 15m | pool_canonical | O2_ST2X | BE1 | 2 | 0 | 2 | 100.0 | 0 | 0 | 0.0 | 2 | 2 | 100.0 | 0/0 | 0/0 | 45m | 0.00 |
| Tilly-SOL [BMi3TK...k3kh] | 15m | pool_canonical | O2_ST2X | BE50 | 2 | 0 | 1 | 50.0 | 0 | 1 | 0.0 | 2 | 1 | 50.0 | 0/0 | 0/0 | 428m | -0.65 |
| Tilly-SOL [BMi3TK...k3kh] | 15m | pool_canonical | O2_ST2X | BE75 | 2 | 0 | 1 | 50.0 | 0 | 1 | 0.0 | 2 | 1 | 50.0 | 0/0 | 0/0 | 428m | -0.65 |
| Tilly-SOL [BMi3TK...k3kh] | 15m | pool_canonical | O2_ST2X | TP_FRACTAL | 2 | 0 | 0 | 0.0 | 0 | 2 | 0.0 | 2 | 0 | 0.0 | 0/0 | 0/0 | 645m | -1.53 |
| Tilly-SOL [BMi3TK...k3kh] | 1m | pool_canonical | O1_SL50 | BE1 | 13 | 4 | 7 | 53.8 | 2 | 0 | 66.7 | 11 | 7 | 63.6 | 1/3 | 1/1 | 8m | -0.84 |
| Tilly-SOL [BMi3TK...k3kh] | 1m | pool_canonical | O1_SL50 | BE50 | 13 | 8 | 1 | 7.7 | 4 | 0 | 66.7 | 11 | 1 | 9.1 | 1/6 | 1/3 | 35m | -0.44 |
| Tilly-SOL [BMi3TK...k3kh] | 1m | pool_canonical | O1_SL50 | BE75 | 13 | 9 | 0 | 0.0 | 4 | 0 | 69.2 | 11 | 0 | 0.0 | 1/7 | 1/3 | 35m | -0.24 |
| Tilly-SOL [BMi3TK...k3kh] | 1m | pool_canonical | O1_SL50 | TP_FRACTAL | 13 | 9 | 0 | 0.0 | 4 | 0 | 69.2 | 11 | 0 | 0.0 | 1/7 | 1/3 | 35m | -0.24 |
| Tilly-SOL [BMi3TK...k3kh] | 1m | pool_canonical | O2_ST2X | BE1 | 13 | 4 | 7 | 53.8 | 2 | 0 | 66.7 | 11 | 7 | 63.6 | 1/3 | 1/1 | 5m | 0.45 |
| Tilly-SOL [BMi3TK...k3kh] | 1m | pool_canonical | O2_ST2X | BE50 | 13 | 7 | 4 | 30.8 | 2 | 0 | 77.8 | 11 | 4 | 36.4 | 1/5 | 1/1 | 10m | 3.90 |
| Tilly-SOL [BMi3TK...k3kh] | 1m | pool_canonical | O2_ST2X | BE75 | 13 | 8 | 2 | 15.4 | 3 | 0 | 72.7 | 11 | 2 | 18.2 | 1/6 | 1/2 | 12m | 3.09 |
| Tilly-SOL [BMi3TK...k3kh] | 1m | pool_canonical | O2_ST2X | TP_FRACTAL | 13 | 8 | 0 | 0.0 | 5 | 0 | 61.5 | 11 | 0 | 0.0 | 1/6 | 1/4 | 12m | 1.09 |
| Tilly-SOL [BMi3TK...k3kh] | 30m | jupiter_proxy_15m_agg30m | O1_SL50 | BE1 | 2 | 1 | 1 | 50.0 | 0 | 0 | 100.0 | 2 | 1 | 50.0 | 1/1 | 0/0 | 75m | 1.40 |
| Tilly-SOL [BMi3TK...k3kh] | 30m | jupiter_proxy_15m_agg30m | O1_SL50 | BE50 | 2 | 1 | 1 | 50.0 | 0 | 0 | 100.0 | 2 | 1 | 50.0 | 1/1 | 0/0 | 75m | 1.40 |
| Tilly-SOL [BMi3TK...k3kh] | 30m | jupiter_proxy_15m_agg30m | O1_SL50 | BE75 | 2 | 1 | 1 | 50.0 | 0 | 0 | 100.0 | 2 | 1 | 50.0 | 1/1 | 0/0 | 150m | 1.40 |
| Tilly-SOL [BMi3TK...k3kh] | 30m | jupiter_proxy_15m_agg30m | O1_SL50 | TP_FRACTAL | 2 | 1 | 0 | 0.0 | 1 | 0 | 50.0 | 2 | 0 | 0.0 | 1/1 | 1/1 | 390m | 0.40 |
| Tilly-SOL [BMi3TK...k3kh] | 30m | jupiter_proxy_15m_agg30m | O2_ST2X | BE1 | 1 | 1 | 0 | 0.0 | 0 | 0 | 100.0 | 1 | 0 | 0.0 | 1/1 | 0/0 | 30m | 1.98 |
| Tilly-SOL [BMi3TK...k3kh] | 30m | jupiter_proxy_15m_agg30m | O2_ST2X | BE50 | 1 | 1 | 0 | 0.0 | 0 | 0 | 100.0 | 1 | 0 | 0.0 | 1/1 | 0/0 | 30m | 1.98 |
| Tilly-SOL [BMi3TK...k3kh] | 30m | jupiter_proxy_15m_agg30m | O2_ST2X | BE75 | 1 | 1 | 0 | 0.0 | 0 | 0 | 100.0 | 1 | 0 | 0.0 | 1/1 | 0/0 | 30m | 1.98 |
| Tilly-SOL [BMi3TK...k3kh] | 30m | jupiter_proxy_15m_agg30m | O2_ST2X | TP_FRACTAL | 1 | 1 | 0 | 0.0 | 0 | 0 | 100.0 | 1 | 0 | 0.0 | 1/1 | 0/0 | 30m | 1.98 |
| Tilly-SOL [BMi3TK...k3kh] | 5m | pool_canonical | O1_SL50 | BE1 | 6 | 1 | 4 | 66.7 | 1 | 0 | 50.0 | 6 | 4 | 66.7 | 1/1 | 1/1 | 107m | -0.06 |
| Tilly-SOL [BMi3TK...k3kh] | 5m | pool_canonical | O1_SL50 | BE50 | 6 | 1 | 3 | 50.0 | 2 | 0 | 33.3 | 6 | 3 | 50.0 | 1/1 | 2/2 | 161m | -1.06 |
| Tilly-SOL [BMi3TK...k3kh] | 5m | pool_canonical | O1_SL50 | BE75 | 6 | 3 | 1 | 16.7 | 2 | 0 | 60.0 | 6 | 1 | 16.7 | 1/2 | 1/1 | 192m | 0.67 |
| Tilly-SOL [BMi3TK...k3kh] | 5m | pool_canonical | O1_SL50 | TP_FRACTAL | 6 | 3 | 0 | 0.0 | 3 | 0 | 50.0 | 6 | 0 | 0.0 | 1/2 | 1/2 | 270m | -0.33 |
| Tilly-SOL [BMi3TK...k3kh] | 5m | pool_canonical | O2_ST2X | BE1 | 6 | 1 | 2 | 33.3 | 3 | 0 | 25.0 | 6 | 2 | 33.3 | 1/1 | 1/2 | 31m | -2.29 |
| Tilly-SOL [BMi3TK...k3kh] | 5m | pool_canonical | O2_ST2X | BE50 | 6 | 1 | 1 | 16.7 | 4 | 0 | 20.0 | 6 | 1 | 16.7 | 1/1 | 1/3 | 113m | -3.29 |
| Tilly-SOL [BMi3TK...k3kh] | 5m | pool_canonical | O2_ST2X | BE75 | 6 | 1 | 1 | 16.7 | 4 | 0 | 20.0 | 6 | 1 | 16.7 | 1/1 | 1/3 | 113m | -3.29 |
| Tilly-SOL [BMi3TK...k3kh] | 5m | pool_canonical | O2_ST2X | TP_FRACTAL | 6 | 1 | 0 | 0.0 | 5 | 0 | 16.7 | 6 | 0 | 0.0 | 1/1 | 1/4 | 164m | -4.29 |
| TOESCOIN-SOL [CpKbsv...MGRH] | 15m | pool_canonical | O1_SL50 | BE1 | 48 | 14 | 32 | 66.7 | 2 | 0 | 87.5 | 42 | 32 | 76.2 | 2/9 | 1/1 | 313m | -0.97 |
| TOESCOIN-SOL [CpKbsv...MGRH] | 15m | pool_canonical | O1_SL50 | BE50 | 48 | 39 | 3 | 6.2 | 6 | 0 | 86.7 | 42 | 3 | 7.1 | 2/18 | 1/3 | 957m | -1.92 |
| TOESCOIN-SOL [CpKbsv...MGRH] | 15m | pool_canonical | O1_SL50 | BE75 | 48 | 41 | 1 | 2.1 | 6 | 0 | 87.2 | 42 | 1 | 2.4 | 2/18 | 1/3 | 980m | -1.22 |
| TOESCOIN-SOL [CpKbsv...MGRH] | 15m | pool_canonical | O1_SL50 | TP_FRACTAL | 48 | 42 | 0 | 0.0 | 6 | 0 | 87.5 | 42 | 0 | 0.0 | 2/19 | 1/3 | 1057m | -0.95 |
| TOESCOIN-SOL [CpKbsv...MGRH] | 15m | pool_canonical | O2_ST2X | BE1 | 48 | 14 | 27 | 56.2 | 7 | 0 | 66.7 | 42 | 27 | 64.3 | 1/4 | 1/2 | 95m | -2.18 |
| TOESCOIN-SOL [CpKbsv...MGRH] | 15m | pool_canonical | O2_ST2X | BE50 | 48 | 26 | 12 | 25.0 | 10 | 0 | 72.2 | 42 | 12 | 28.6 | 1/8 | 1/2 | 212m | -0.26 |
| TOESCOIN-SOL [CpKbsv...MGRH] | 15m | pool_canonical | O2_ST2X | BE75 | 48 | 29 | 4 | 8.3 | 15 | 0 | 65.9 | 42 | 4 | 9.5 | 1/10 | 1/3 | 257m | -4.29 |
| TOESCOIN-SOL [CpKbsv...MGRH] | 15m | pool_canonical | O2_ST2X | TP_FRACTAL | 48 | 29 | 0 | 0.0 | 19 | 0 | 60.4 | 42 | 0 | 0.0 | 1/10 | 1/4 | 307m | -8.29 |
| TOESCOIN-SOL [CpKbsv...MGRH] | 1m | pool_canonical | O1_SL50 | BE1 | 15 | 2 | 12 | 80.0 | 1 | 0 | 66.7 | 13 | 12 | 92.3 | 1/1 | 1/1 | 12m | -0.94 |
| TOESCOIN-SOL [CpKbsv...MGRH] | 1m | pool_canonical | O1_SL50 | BE50 | 15 | 11 | 0 | 0.0 | 4 | 0 | 73.3 | 13 | 0 | 0.0 | 2/9 | 4/4 | 119m | -2.17 |
| TOESCOIN-SOL [CpKbsv...MGRH] | 1m | pool_canonical | O1_SL50 | BE75 | 15 | 11 | 0 | 0.0 | 4 | 0 | 73.3 | 13 | 0 | 0.0 | 2/9 | 4/4 | 119m | -2.17 |
| TOESCOIN-SOL [CpKbsv...MGRH] | 1m | pool_canonical | O1_SL50 | TP_FRACTAL | 15 | 11 | 0 | 0.0 | 4 | 0 | 73.3 | 13 | 0 | 0.0 | 2/9 | 4/4 | 119m | -2.17 |
| TOESCOIN-SOL [CpKbsv...MGRH] | 1m | pool_canonical | O2_ST2X | BE1 | 15 | 2 | 11 | 73.3 | 2 | 0 | 50.0 | 13 | 11 | 84.6 | 1/1 | 2/2 | 4m | -1.73 |
| TOESCOIN-SOL [CpKbsv...MGRH] | 1m | pool_canonical | O2_ST2X | BE50 | 15 | 8 | 3 | 20.0 | 4 | 0 | 66.7 | 13 | 3 | 23.1 | 1/7 | 4/4 | 14m | 0.69 |
| TOESCOIN-SOL [CpKbsv...MGRH] | 1m | pool_canonical | O2_ST2X | BE75 | 15 | 9 | 0 | 0.0 | 6 | 0 | 60.0 | 13 | 0 | 0.0 | 2/5 | 1/5 | 17m | -0.25 |
| TOESCOIN-SOL [CpKbsv...MGRH] | 1m | pool_canonical | O2_ST2X | TP_FRACTAL | 15 | 9 | 0 | 0.0 | 6 | 0 | 60.0 | 13 | 0 | 0.0 | 2/5 | 1/5 | 17m | -0.25 |
| TOESCOIN-SOL [CpKbsv...MGRH] | 30m | jupiter_proxy_15m_agg30m | O1_SL50 | BE1 | 2 | 0 | 2 | 100.0 | 0 | 0 | 0.0 | 2 | 2 | 100.0 | 0/0 | 0/0 | 390m | 0.00 |
| TOESCOIN-SOL [CpKbsv...MGRH] | 30m | jupiter_proxy_15m_agg30m | O1_SL50 | BE50 | 2 | 2 | 0 | 0.0 | 0 | 0 | 100.0 | 2 | 0 | 0.0 | 2/2 | 0/0 | 555m | 0.09 |
| TOESCOIN-SOL [CpKbsv...MGRH] | 30m | jupiter_proxy_15m_agg30m | O1_SL50 | BE75 | 2 | 2 | 0 | 0.0 | 0 | 0 | 100.0 | 2 | 0 | 0.0 | 2/2 | 0/0 | 555m | 0.09 |
| TOESCOIN-SOL [CpKbsv...MGRH] | 30m | jupiter_proxy_15m_agg30m | O1_SL50 | TP_FRACTAL | 2 | 2 | 0 | 0.0 | 0 | 0 | 100.0 | 2 | 0 | 0.0 | 2/2 | 0/0 | 555m | 0.09 |
| TOESCOIN-SOL [CpKbsv...MGRH] | 30m | jupiter_proxy_15m_agg30m | O2_ST2X | BE1 | 2 | 0 | 2 | 100.0 | 0 | 0 | 0.0 | 2 | 2 | 100.0 | 0/0 | 0/0 | 390m | 0.00 |
| TOESCOIN-SOL [CpKbsv...MGRH] | 30m | jupiter_proxy_15m_agg30m | O2_ST2X | BE50 | 2 | 1 | 1 | 50.0 | 0 | 0 | 100.0 | 2 | 1 | 50.0 | 1/1 | 0/0 | 420m | 0.14 |
| TOESCOIN-SOL [CpKbsv...MGRH] | 30m | jupiter_proxy_15m_agg30m | O2_ST2X | BE75 | 2 | 2 | 0 | 0.0 | 0 | 0 | 100.0 | 2 | 0 | 0.0 | 2/2 | 0/0 | 555m | 0.33 |
| TOESCOIN-SOL [CpKbsv...MGRH] | 30m | jupiter_proxy_15m_agg30m | O2_ST2X | TP_FRACTAL | 2 | 2 | 0 | 0.0 | 0 | 0 | 100.0 | 2 | 0 | 0.0 | 2/2 | 0/0 | 555m | 0.33 |
| TOESCOIN-SOL [CpKbsv...MGRH] | 5m | pool_canonical | O1_SL50 | BE1 | 32 | 12 | 18 | 56.2 | 2 | 0 | 85.7 | 28 | 18 | 64.3 | 2/6 | 1/1 | 199m | -1.17 |
| TOESCOIN-SOL [CpKbsv...MGRH] | 5m | pool_canonical | O1_SL50 | BE50 | 32 | 24 | 0 | 0.0 | 8 | 0 | 75.0 | 28 | 0 | 0.0 | 2/11 | 1/4 | 776m | -5.28 |
| TOESCOIN-SOL [CpKbsv...MGRH] | 5m | pool_canonical | O1_SL50 | BE75 | 32 | 24 | 0 | 0.0 | 8 | 0 | 75.0 | 28 | 0 | 0.0 | 2/11 | 1/4 | 776m | -5.28 |
| TOESCOIN-SOL [CpKbsv...MGRH] | 5m | pool_canonical | O1_SL50 | TP_FRACTAL | 32 | 24 | 0 | 0.0 | 8 | 0 | 75.0 | 28 | 0 | 0.0 | 2/11 | 1/4 | 776m | -5.28 |
| TOESCOIN-SOL [CpKbsv...MGRH] | 5m | pool_canonical | O2_ST2X | BE1 | 32 | 11 | 14 | 43.8 | 7 | 0 | 61.1 | 28 | 14 | 50.0 | 1/4 | 1/3 | 27m | 7.04 |
| TOESCOIN-SOL [CpKbsv...MGRH] | 5m | pool_canonical | O2_ST2X | BE50 | 32 | 17 | 3 | 9.4 | 12 | 0 | 58.6 | 28 | 3 | 10.7 | 1/4 | 1/4 | 61m | 5.95 |
| TOESCOIN-SOL [CpKbsv...MGRH] | 5m | pool_canonical | O2_ST2X | BE75 | 32 | 17 | 2 | 6.2 | 13 | 0 | 56.7 | 28 | 2 | 7.1 | 1/4 | 1/5 | 62m | 4.95 |
| TOESCOIN-SOL [CpKbsv...MGRH] | 5m | pool_canonical | O2_ST2X | TP_FRACTAL | 32 | 18 | 0 | 0.0 | 14 | 0 | 56.2 | 28 | 0 | 0.0 | 1/5 | 1/5 | 68m | 4.77 |
| Mouse-SOL [FbBGvD...XgoG] | 1m | pool_canonical | O1_SL50 | BE1 | 11 | 5 | 5 | 45.5 | 0 | 1 | 100.0 | 8 | 5 | 62.5 | 5/5 | 0/0 | 5m | 0.40 |
| Mouse-SOL [FbBGvD...XgoG] | 1m | pool_canonical | O1_SL50 | BE50 | 11 | 7 | 2 | 18.2 | 1 | 1 | 87.5 | 8 | 2 | 25.0 | 3/4 | 1/1 | 26m | -0.11 |
| Mouse-SOL [FbBGvD...XgoG] | 1m | pool_canonical | O1_SL50 | BE75 | 11 | 8 | 0 | 0.0 | 2 | 1 | 80.0 | 8 | 0 | 0.0 | 4/4 | 2/2 | 40m | -0.80 |
| Mouse-SOL [FbBGvD...XgoG] | 1m | pool_canonical | O1_SL50 | TP_FRACTAL | 11 | 8 | 0 | 0.0 | 2 | 1 | 80.0 | 8 | 0 | 0.0 | 4/4 | 2/2 | 40m | -0.80 |
| Mouse-SOL [FbBGvD...XgoG] | 1m | pool_canonical | O2_ST2X | BE1 | 11 | 4 | 5 | 45.5 | 2 | 0 | 66.7 | 8 | 5 | 62.5 | 1/3 | 1/1 | 3m | -1.50 |
| Mouse-SOL [FbBGvD...XgoG] | 1m | pool_canonical | O2_ST2X | BE50 | 11 | 5 | 3 | 27.3 | 3 | 0 | 62.5 | 8 | 3 | 37.5 | 1/2 | 1/1 | 11m | -2.22 |
| Mouse-SOL [FbBGvD...XgoG] | 1m | pool_canonical | O2_ST2X | BE75 | 11 | 5 | 1 | 9.1 | 5 | 0 | 50.0 | 8 | 1 | 12.5 | 1/2 | 1/2 | 15m | -4.22 |
| Mouse-SOL [FbBGvD...XgoG] | 1m | pool_canonical | O2_ST2X | TP_FRACTAL | 11 | 6 | 0 | 0.0 | 5 | 0 | 54.5 | 8 | 0 | 0.0 | 1/2 | 1/2 | 15m | -3.75 |
| Mouse-SOL [FbBGvD...XgoG] | 5m | pool_canonical | O1_SL50 | BE1 | 5 | 1 | 4 | 80.0 | 0 | 0 | 100.0 | 4 | 4 | 100.0 | 1/1 | 0/0 | 40m | 0.36 |
| Mouse-SOL [FbBGvD...XgoG] | 5m | pool_canonical | O1_SL50 | BE50 | 5 | 2 | 2 | 40.0 | 1 | 0 | 66.7 | 4 | 2 | 50.0 | 1/1 | 1/1 | 72m | -0.25 |
| Mouse-SOL [FbBGvD...XgoG] | 5m | pool_canonical | O1_SL50 | BE75 | 5 | 3 | 0 | 0.0 | 2 | 0 | 60.0 | 4 | 0 | 0.0 | 1/2 | 2/2 | 98m | -1.09 |
| Mouse-SOL [FbBGvD...XgoG] | 5m | pool_canonical | O1_SL50 | TP_FRACTAL | 5 | 3 | 0 | 0.0 | 2 | 0 | 60.0 | 4 | 0 | 0.0 | 1/2 | 2/2 | 98m | -1.09 |
| Mouse-SOL [FbBGvD...XgoG] | 5m | pool_canonical | O2_ST2X | BE1 | 5 | 1 | 4 | 80.0 | 0 | 0 | 100.0 | 4 | 4 | 100.0 | 1/1 | 0/0 | 40m | 0.23 |
| Mouse-SOL [FbBGvD...XgoG] | 5m | pool_canonical | O2_ST2X | BE50 | 5 | 2 | 2 | 40.0 | 1 | 0 | 66.7 | 4 | 2 | 50.0 | 1/1 | 1/1 | 93m | -0.32 |
| Mouse-SOL [FbBGvD...XgoG] | 5m | pool_canonical | O2_ST2X | BE75 | 5 | 2 | 1 | 20.0 | 2 | 0 | 50.0 | 4 | 1 | 25.0 | 1/1 | 2/2 | 97m | -1.32 |
| Mouse-SOL [FbBGvD...XgoG] | 5m | pool_canonical | O2_ST2X | TP_FRACTAL | 5 | 3 | 0 | 0.0 | 2 | 0 | 60.0 | 4 | 0 | 0.0 | 1/2 | 2/2 | 98m | -1.16 |
| BISCOTTI-SOL [Ft5Cxg...qohk] | 15m | pool_canonical | O1_SL50 | BE1 | 3 | 1 | 1 | 33.3 | 0 | 1 | 100.0 | 3 | 1 | 33.3 | 1/1 | 0/0 | 120m | -0.54 |
| BISCOTTI-SOL [Ft5Cxg...qohk] | 15m | pool_canonical | O1_SL50 | BE50 | 3 | 1 | 1 | 33.3 | 0 | 1 | 100.0 | 3 | 1 | 33.3 | 1/1 | 0/0 | 240m | -0.54 |
| BISCOTTI-SOL [Ft5Cxg...qohk] | 15m | pool_canonical | O1_SL50 | BE75 | 3 | 2 | 0 | 0.0 | 0 | 1 | 100.0 | 3 | 0 | 0.0 | 2/2 | 0/0 | 255m | 0.07 |
| BISCOTTI-SOL [Ft5Cxg...qohk] | 15m | pool_canonical | O1_SL50 | TP_FRACTAL | 3 | 2 | 0 | 0.0 | 0 | 1 | 100.0 | 3 | 0 | 0.0 | 2/2 | 0/0 | 255m | 0.07 |
| BISCOTTI-SOL [Ft5Cxg...qohk] | 15m | pool_canonical | O2_ST2X | BE1 | 3 | 1 | 1 | 33.3 | 0 | 1 | 100.0 | 3 | 1 | 33.3 | 1/1 | 0/0 | 120m | -0.66 |
| BISCOTTI-SOL [Ft5Cxg...qohk] | 15m | pool_canonical | O2_ST2X | BE50 | 3 | 2 | 0 | 0.0 | 0 | 1 | 100.0 | 3 | 0 | 0.0 | 2/2 | 0/0 | 255m | -0.30 |
| BISCOTTI-SOL [Ft5Cxg...qohk] | 15m | pool_canonical | O2_ST2X | BE75 | 3 | 2 | 0 | 0.0 | 0 | 1 | 100.0 | 3 | 0 | 0.0 | 2/2 | 0/0 | 255m | -0.30 |
| BISCOTTI-SOL [Ft5Cxg...qohk] | 15m | pool_canonical | O2_ST2X | TP_FRACTAL | 3 | 2 | 0 | 0.0 | 0 | 1 | 100.0 | 3 | 0 | 0.0 | 2/2 | 0/0 | 255m | -0.30 |
| BISCOTTI-SOL [Ft5Cxg...qohk] | 1m | pool_canonical | O1_SL50 | BE1 | 13 | 5 | 8 | 61.5 | 0 | 0 | 100.0 | 11 | 8 | 72.7 | 5/5 | 0/0 | 5m | 0.95 |
| BISCOTTI-SOL [Ft5Cxg...qohk] | 1m | pool_canonical | O1_SL50 | BE50 | 13 | 9 | 3 | 23.1 | 1 | 0 | 90.0 | 11 | 3 | 27.3 | 4/5 | 1/1 | 54m | 1.08 |
| BISCOTTI-SOL [Ft5Cxg...qohk] | 1m | pool_canonical | O1_SL50 | BE75 | 13 | 11 | 1 | 7.7 | 1 | 0 | 91.7 | 11 | 1 | 9.1 | 5/6 | 1/1 | 56m | 2.28 |
| BISCOTTI-SOL [Ft5Cxg...qohk] | 1m | pool_canonical | O1_SL50 | TP_FRACTAL | 13 | 12 | 0 | 0.0 | 1 | 0 | 92.3 | 11 | 0 | 0.0 | 6/6 | 1/1 | 56m | 2.63 |
| BISCOTTI-SOL [Ft5Cxg...qohk] | 1m | pool_canonical | O2_ST2X | BE1 | 13 | 5 | 7 | 53.8 | 1 | 0 | 83.3 | 11 | 7 | 63.6 | 1/4 | 1/1 | 5m | 1.13 |
| BISCOTTI-SOL [Ft5Cxg...qohk] | 1m | pool_canonical | O2_ST2X | BE50 | 13 | 8 | 2 | 15.4 | 3 | 0 | 72.7 | 11 | 2 | 18.2 | 1/4 | 1/2 | 7m | -0.01 |
| BISCOTTI-SOL [Ft5Cxg...qohk] | 1m | pool_canonical | O2_ST2X | BE75 | 13 | 9 | 0 | 0.0 | 4 | 0 | 69.2 | 11 | 0 | 0.0 | 1/4 | 1/2 | 8m | -0.59 |
| BISCOTTI-SOL [Ft5Cxg...qohk] | 1m | pool_canonical | O2_ST2X | TP_FRACTAL | 13 | 9 | 0 | 0.0 | 4 | 0 | 69.2 | 11 | 0 | 0.0 | 1/4 | 1/2 | 8m | -0.59 |
| BISCOTTI-SOL [Ft5Cxg...qohk] | 30m | jupiter_proxy_15m_agg30m | O1_SL50 | BE1 | 2 | 1 | 1 | 50.0 | 0 | 0 | 100.0 | 2 | 1 | 50.0 | 1/1 | 0/0 | 60m | 0.21 |
| BISCOTTI-SOL [Ft5Cxg...qohk] | 30m | jupiter_proxy_15m_agg30m | O1_SL50 | BE50 | 2 | 1 | 0 | 0.0 | 0 | 1 | 100.0 | 2 | 0 | 0.0 | 1/1 | 0/0 | 210m | 0.01 |
| BISCOTTI-SOL [Ft5Cxg...qohk] | 30m | jupiter_proxy_15m_agg30m | O1_SL50 | BE75 | 2 | 1 | 0 | 0.0 | 0 | 1 | 100.0 | 2 | 0 | 0.0 | 1/1 | 0/0 | 210m | 0.01 |
| BISCOTTI-SOL [Ft5Cxg...qohk] | 30m | jupiter_proxy_15m_agg30m | O1_SL50 | TP_FRACTAL | 2 | 1 | 0 | 0.0 | 0 | 1 | 100.0 | 2 | 0 | 0.0 | 1/1 | 0/0 | 210m | 0.01 |
| BISCOTTI-SOL [Ft5Cxg...qohk] | 30m | jupiter_proxy_15m_agg30m | O2_ST2X | BE1 | 1 | 0 | 1 | 100.0 | 0 | 0 | 0.0 | 1 | 1 | 100.0 | 0/0 | 0/0 | 90m | 0.00 |
| BISCOTTI-SOL [Ft5Cxg...qohk] | 30m | jupiter_proxy_15m_agg30m | O2_ST2X | BE50 | 1 | 0 | 0 | 0.0 | 0 | 1 | 0.0 | 1 | 0 | 0.0 | 0/0 | 0/0 | 390m | -0.14 |
| BISCOTTI-SOL [Ft5Cxg...qohk] | 30m | jupiter_proxy_15m_agg30m | O2_ST2X | BE75 | 1 | 0 | 0 | 0.0 | 0 | 1 | 0.0 | 1 | 0 | 0.0 | 0/0 | 0/0 | 390m | -0.14 |
| BISCOTTI-SOL [Ft5Cxg...qohk] | 30m | jupiter_proxy_15m_agg30m | O2_ST2X | TP_FRACTAL | 1 | 0 | 0 | 0.0 | 0 | 1 | 0.0 | 1 | 0 | 0.0 | 0/0 | 0/0 | 390m | -0.14 |
| BISCOTTI-SOL [Ft5Cxg...qohk] | 5m | pool_canonical | O1_SL50 | BE1 | 7 | 4 | 3 | 42.9 | 0 | 0 | 100.0 | 5 | 3 | 60.0 | 4/4 | 0/0 | 45m | 1.51 |
| BISCOTTI-SOL [Ft5Cxg...qohk] | 5m | pool_canonical | O1_SL50 | BE50 | 7 | 5 | 1 | 14.3 | 0 | 1 | 100.0 | 5 | 1 | 20.0 | 5/5 | 0/0 | 130m | 1.51 |
| BISCOTTI-SOL [Ft5Cxg...qohk] | 5m | pool_canonical | O1_SL50 | BE75 | 7 | 5 | 1 | 14.3 | 0 | 1 | 100.0 | 5 | 1 | 20.0 | 5/5 | 0/0 | 130m | 1.51 |
| BISCOTTI-SOL [Ft5Cxg...qohk] | 5m | pool_canonical | O1_SL50 | TP_FRACTAL | 7 | 6 | 0 | 0.0 | 0 | 1 | 100.0 | 5 | 0 | 0.0 | 6/6 | 0/0 | 134m | 1.99 |
| BISCOTTI-SOL [Ft5Cxg...qohk] | 5m | pool_canonical | O2_ST2X | BE1 | 7 | 4 | 3 | 42.9 | 0 | 0 | 100.0 | 5 | 3 | 60.0 | 4/4 | 0/0 | 45m | 1.20 |
| BISCOTTI-SOL [Ft5Cxg...qohk] | 5m | pool_canonical | O2_ST2X | BE50 | 7 | 5 | 1 | 14.3 | 1 | 0 | 83.3 | 5 | 1 | 20.0 | 5/5 | 1/1 | 107m | 1.63 |
| BISCOTTI-SOL [Ft5Cxg...qohk] | 5m | pool_canonical | O2_ST2X | BE75 | 7 | 6 | 0 | 0.0 | 1 | 0 | 85.7 | 5 | 0 | 0.0 | 6/6 | 1/1 | 111m | 1.93 |
| BISCOTTI-SOL [Ft5Cxg...qohk] | 5m | pool_canonical | O2_ST2X | TP_FRACTAL | 7 | 6 | 0 | 0.0 | 1 | 0 | 85.7 | 5 | 0 | 0.0 | 6/6 | 1/1 | 111m | 1.93 |
| USWR-SOL [qf3ExN...f7iv] | 15m | pool_canonical | O1_SL50 | BE1 | 81 | 25 | 56 | 69.1 | 0 | 0 | 100.0 | 81 | 56 | 69.1 | 25/25 | 0/0 | 41m | 0.39 |
| USWR-SOL [qf3ExN...f7iv] | 15m | pool_canonical | O1_SL50 | BE50 | 81 | 81 | 0 | 0.0 | 0 | 0 | 100.0 | 81 | 0 | 0.0 | 81/81 | 0/0 | 206m | 1.71 |
| USWR-SOL [qf3ExN...f7iv] | 15m | pool_canonical | O1_SL50 | BE75 | 81 | 81 | 0 | 0.0 | 0 | 0 | 100.0 | 81 | 0 | 0.0 | 81/81 | 0/0 | 206m | 1.71 |
| USWR-SOL [qf3ExN...f7iv] | 15m | pool_canonical | O1_SL50 | TP_FRACTAL | 81 | 81 | 0 | 0.0 | 0 | 0 | 100.0 | 81 | 0 | 0.0 | 81/81 | 0/0 | 206m | 1.71 |
| USWR-SOL [qf3ExN...f7iv] | 15m | pool_canonical | O2_ST2X | BE1 | 81 | 25 | 55 | 67.9 | 1 | 0 | 96.2 | 81 | 55 | 67.9 | 8/17 | 1/1 | 41m | 4.90 |
| USWR-SOL [qf3ExN...f7iv] | 15m | pool_canonical | O2_ST2X | BE50 | 81 | 71 | 7 | 8.6 | 3 | 0 | 95.9 | 81 | 7 | 8.6 | 1/43 | 1/1 | 181m | 19.56 |
| USWR-SOL [qf3ExN...f7iv] | 15m | pool_canonical | O2_ST2X | BE75 | 81 | 76 | 2 | 2.5 | 3 | 0 | 96.2 | 81 | 2 | 2.5 | 1/47 | 1/1 | 201m | 24.57 |
| USWR-SOL [qf3ExN...f7iv] | 15m | pool_canonical | O2_ST2X | TP_FRACTAL | 81 | 78 | 0 | 0.0 | 3 | 0 | 96.3 | 81 | 0 | 0.0 | 1/49 | 1/1 | 201m | 33.22 |
| USWR-SOL [qf3ExN...f7iv] | 1m | pool_canonical | O1_SL50 | BE1 | 65 | 18 | 47 | 72.3 | 0 | 0 | 100.0 | 63 | 47 | 74.6 | 18/18 | 0/0 | 12m | 0.03 |
| USWR-SOL [qf3ExN...f7iv] | 1m | pool_canonical | O1_SL50 | BE50 | 65 | 65 | 0 | 0.0 | 0 | 0 | 100.0 | 63 | 0 | 0.0 | 65/65 | 0/0 | 76m | 0.18 |
| USWR-SOL [qf3ExN...f7iv] | 1m | pool_canonical | O1_SL50 | BE75 | 65 | 65 | 0 | 0.0 | 0 | 0 | 100.0 | 63 | 0 | 0.0 | 65/65 | 0/0 | 76m | 0.18 |
| USWR-SOL [qf3ExN...f7iv] | 1m | pool_canonical | O1_SL50 | TP_FRACTAL | 65 | 65 | 0 | 0.0 | 0 | 0 | 100.0 | 63 | 0 | 0.0 | 65/65 | 0/0 | 76m | 0.18 |
| USWR-SOL [qf3ExN...f7iv] | 1m | pool_canonical | O2_ST2X | BE1 | 65 | 18 | 42 | 64.6 | 5 | 0 | 78.3 | 63 | 42 | 66.7 | 1/9 | 1/2 | 6m | -0.89 |
| USWR-SOL [qf3ExN...f7iv] | 1m | pool_canonical | O2_ST2X | BE50 | 65 | 37 | 17 | 26.2 | 11 | 0 | 77.1 | 63 | 17 | 27.0 | 2/8 | 1/3 | 14m | -2.42 |
| USWR-SOL [qf3ExN...f7iv] | 1m | pool_canonical | O2_ST2X | BE75 | 65 | 44 | 6 | 9.2 | 15 | 0 | 74.6 | 63 | 6 | 9.5 | 1/6 | 1/2 | 17m | -4.79 |
| USWR-SOL [qf3ExN...f7iv] | 1m | pool_canonical | O2_ST2X | TP_FRACTAL | 65 | 48 | 0 | 0.0 | 17 | 0 | 73.8 | 63 | 0 | 0.0 | 1/7 | 1/2 | 19m | -5.95 |
| USWR-SOL [qf3ExN...f7iv] | 30m | jupiter_proxy_15m_agg30m | O1_SL50 | BE1 | 1 | 1 | 0 | 0.0 | 0 | 0 | 100.0 | 1 | 0 | 0.0 | 1/1 | 0/0 | 660m | 0.01 |
| USWR-SOL [qf3ExN...f7iv] | 30m | jupiter_proxy_15m_agg30m | O1_SL50 | BE50 | 1 | 1 | 0 | 0.0 | 0 | 0 | 100.0 | 1 | 0 | 0.0 | 1/1 | 0/0 | 660m | 0.01 |
| USWR-SOL [qf3ExN...f7iv] | 30m | jupiter_proxy_15m_agg30m | O1_SL50 | BE75 | 1 | 1 | 0 | 0.0 | 0 | 0 | 100.0 | 1 | 0 | 0.0 | 1/1 | 0/0 | 660m | 0.01 |
| USWR-SOL [qf3ExN...f7iv] | 30m | jupiter_proxy_15m_agg30m | O1_SL50 | TP_FRACTAL | 1 | 1 | 0 | 0.0 | 0 | 0 | 100.0 | 1 | 0 | 0.0 | 1/1 | 0/0 | 660m | 0.01 |
| USWR-SOL [qf3ExN...f7iv] | 30m | jupiter_proxy_15m_agg30m | O2_ST2X | BE1 | 1 | 1 | 0 | 0.0 | 0 | 0 | 100.0 | 1 | 0 | 0.0 | 1/1 | 0/0 | 660m | 0.14 |
| USWR-SOL [qf3ExN...f7iv] | 30m | jupiter_proxy_15m_agg30m | O2_ST2X | BE50 | 1 | 1 | 0 | 0.0 | 0 | 0 | 100.0 | 1 | 0 | 0.0 | 1/1 | 0/0 | 660m | 0.14 |
| USWR-SOL [qf3ExN...f7iv] | 30m | jupiter_proxy_15m_agg30m | O2_ST2X | BE75 | 1 | 1 | 0 | 0.0 | 0 | 0 | 100.0 | 1 | 0 | 0.0 | 1/1 | 0/0 | 660m | 0.14 |
| USWR-SOL [qf3ExN...f7iv] | 30m | jupiter_proxy_15m_agg30m | O2_ST2X | TP_FRACTAL | 1 | 1 | 0 | 0.0 | 0 | 0 | 100.0 | 1 | 0 | 0.0 | 1/1 | 0/0 | 660m | 0.14 |
| USWR-SOL [qf3ExN...f7iv] | 5m | pool_canonical | O1_SL50 | BE1 | 106 | 35 | 71 | 67.0 | 0 | 0 | 100.0 | 104 | 71 | 68.3 | 35/35 | 0/0 | 23m | 0.21 |
| USWR-SOL [qf3ExN...f7iv] | 5m | pool_canonical | O1_SL50 | BE50 | 106 | 106 | 0 | 0.0 | 0 | 0 | 100.0 | 104 | 0 | 0.0 | 106/106 | 0/0 | 137m | 0.87 |
| USWR-SOL [qf3ExN...f7iv] | 5m | pool_canonical | O1_SL50 | BE75 | 106 | 106 | 0 | 0.0 | 0 | 0 | 100.0 | 104 | 0 | 0.0 | 106/106 | 0/0 | 137m | 0.87 |
| USWR-SOL [qf3ExN...f7iv] | 5m | pool_canonical | O1_SL50 | TP_FRACTAL | 106 | 106 | 0 | 0.0 | 0 | 0 | 100.0 | 104 | 0 | 0.0 | 106/106 | 0/0 | 137m | 0.87 |
| USWR-SOL [qf3ExN...f7iv] | 5m | pool_canonical | O2_ST2X | BE1 | 106 | 35 | 68 | 64.2 | 3 | 0 | 92.1 | 104 | 68 | 65.4 | 2/21 | 1/1 | 22m | 6.91 |
| USWR-SOL [qf3ExN...f7iv] | 5m | pool_canonical | O2_ST2X | BE50 | 106 | 78 | 21 | 19.8 | 7 | 0 | 91.8 | 104 | 21 | 20.2 | 2/26 | 1/2 | 73m | 22.71 |
| USWR-SOL [qf3ExN...f7iv] | 5m | pool_canonical | O2_ST2X | BE75 | 106 | 92 | 5 | 4.7 | 9 | 0 | 91.1 | 104 | 5 | 4.8 | 2/30 | 1/3 | 105m | 28.98 |
| USWR-SOL [qf3ExN...f7iv] | 5m | pool_canonical | O2_ST2X | TP_FRACTAL | 106 | 97 | 0 | 0.0 | 9 | 0 | 91.5 | 104 | 0 | 0.0 | 2/33 | 1/3 | 110m | 31.01 |

## Notes
- `pool_canonical` = canonical pool candles (Meteora 30m endpoint for 30m, GeckoTerminal pool candles for 1m/5m/15m).
- `jupiter_proxy_15m_agg30m` = Jupiter-backed mint candles from Meridian chart-indicator API, aggregated from 15m into synthetic 30m because canonical pool 30m history was too short.
- `BE1` = any floating loss, but BE only allowed after >=2 candles.
- `BE50` = trade must first go <=50% of risk underwater, BE only allowed after >=2 candles.
- `BE75` = trade must first go <=75% of risk underwater, BE only allowed after >=3 candles.
- Exit `BE` rows mean the mode-specific BE gate was satisfied and price returned to entry after the minimum candle gate; TP is still checked first on each candle.
- Win/loss streak is calculated per pool × timeframe × SL option × exit mode, sorted chronologically.
- Same-candle conflict is conservative: SL checked before TP, then optional BE.