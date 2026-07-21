#!/usr/bin/env python3
"""
Meteora pool chart backtest — RSI(2) + upper fractal(3)

Source data: GeckoTerminal OHLCV for Solana pool addresses discovered from
Meteora pool-discovery snapshot.

Rule (LONG):
1) Trend confirmation at RSI trigger bar:
   - Supertrend bullish/up (default: ATR 10, factor 3)
   - close above EMA50 OR EMA200
2) Trigger 1: RSI(2) close > 90
3) Trigger 2: wait for next confirmed upper fractal(3)
   - fractal center = pivot high with 3 bars left/right
   - confirmation bar = center + 3
4) Entry: next candle open after confirmation bar (non-lookahead)
5) TP: high of the fractal center candle
6) SL options:
   - O1: -50% from entry
   - O2: 2x distance from fractal confirmation close to supertrend line
         e.g. confirm close 100, ST line 85 -> dist 15%, SL dist 30%

Outputs summary CSV/MD + trade journal CSV.
"""

from __future__ import annotations

import csv
import json
import math
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import requests

ROOT = Path(__file__).resolve().parent
DISCOVERY_JSON = ROOT / "top20_sol_30m_fee_tvl_age15h.json"
OUTDIR = ROOT / "rsi_fractal_backtest_mhermes_be"
OUTDIR.mkdir(parents=True, exist_ok=True)

NETWORK = "solana"
TFS = {
    "1m": {"timeframe": "minute", "aggregate": 1, "minutes": 1, "max_pages": 3},
    "5m": {"timeframe": "minute", "aggregate": 5, "minutes": 5, "max_pages": 3},
    "15m": {"timeframe": "minute", "aggregate": 15, "minutes": 15, "max_pages": 3},
}
LIMIT = 1000
RSI_LEN = 2
FRACTAL_N = 3
EMA_FAST = 50
EMA_SLOW = 200
ST_ATR_LEN = 10
ST_FACTOR = 3.0
RSI_TRIGGER = 90.0
REQ_SLEEP = 1.05  # GeckoTerminal public API friendly pacing
BE_MODE_SPECS = [
    {"name": "BE1", "gate": "ever_loss", "min_candles": 2, "deep_frac": 0.0, "label": "Any float loss + 2 candles"},
    {"name": "BE50", "gate": "deep50", "min_candles": 2, "deep_frac": 0.50, "label": "Deep 50% of risk + 2 candles"},
    {"name": "BE75", "gate": "deep75", "min_candles": 3, "deep_frac": 0.75, "label": "Deep 75% of risk + 3 candles"},
]
BE_MODE_MAP = {m["name"]: m for m in BE_MODE_SPECS}


def safe_name(text: str) -> str:
    return text.replace("/", "_").replace(" ", "_")


def short_pool_addr(pool_addr: str) -> str:
    return f"{pool_addr[:6]}...{pool_addr[-4:]}" if len(pool_addr) > 12 else pool_addr


def pool_label(pool_name: str, pool_addr: str) -> str:
    return f"{pool_name} [{short_pool_addr(pool_addr)}]"


def fnum(x: Any, default: float = math.nan) -> float:
    try:
        v = float(x)
        return v if math.isfinite(v) else default
    except Exception:
        return default


def load_pools() -> list[dict[str, Any]]:
    data = json.loads(DISCOVERY_JSON.read_text(encoding="utf-8"))
    return data["data"][:20]


def fetch_ohlcv(pool: str, tf: str) -> list[dict[str, float]]:
    spec = TFS[tf]
    before = None
    seen = set()
    rows: list[list[float]] = []
    for page in range(spec["max_pages"]):
        url = f"https://api.geckoterminal.com/api/v2/networks/{NETWORK}/pools/{pool}/ohlcv/{spec['timeframe']}"
        params = {"aggregate": spec["aggregate"], "limit": LIMIT}
        if before:
            params["before_timestamp"] = before
        r = requests.get(url, params=params, timeout=30, headers={"accept": "application/json"})
        retry_wait = 15
        for _ in range(4):
            if r.status_code != 429:
                break
            print(f"[rate-limit] GeckoTerminal 429; sleep {retry_wait}s", flush=True)
            time.sleep(retry_wait)
            retry_wait *= 2
            r = requests.get(url, params=params, timeout=30, headers={"accept": "application/json"})
        r.raise_for_status()
        payload = r.json()
        chunk = payload.get("data", {}).get("attributes", {}).get("ohlcv_list", []) or []
        if not chunk:
            break
        added = 0
        for row in chunk:
            ts = int(row[0])
            if ts in seen:
                continue
            seen.add(ts)
            rows.append(row)
            added += 1
        oldest = min(int(row[0]) for row in chunk)
        before = oldest - 1
        if added == 0 or len(chunk) < LIMIT:
            break
        time.sleep(REQ_SLEEP)
    rows.sort(key=lambda r: int(r[0]))
    out = []
    for ts, o, h, l, c, v in rows:
        out.append({
            "ts": int(ts),
            "open": float(o),
            "high": float(h),
            "low": float(l),
            "close": float(c),
            "volume": float(v),
        })
    return out


def ema(values: list[float], span: int) -> list[float]:
    alpha = 2.0 / (span + 1.0)
    out = [math.nan] * len(values)
    prev = math.nan
    for i, v in enumerate(values):
        if not math.isfinite(v):
            continue
        prev = v if not math.isfinite(prev) else (alpha * v + (1 - alpha) * prev)
        out[i] = prev
    return out


def rma(values: list[float], length: int) -> list[float]:
    out = [math.nan] * len(values)
    alpha = 1.0 / length
    prev = math.nan
    for i, v in enumerate(values):
        if not math.isfinite(v):
            continue
        prev = v if not math.isfinite(prev) else (prev + alpha * (v - prev))
        out[i] = prev
    return out


def rsi(close: list[float], length: int) -> list[float]:
    gains = [math.nan] * len(close)
    losses = [math.nan] * len(close)
    for i in range(1, len(close)):
        d = close[i] - close[i - 1]
        gains[i] = max(d, 0.0)
        losses[i] = max(-d, 0.0)
    ag = rma(gains, length)
    al = rma(losses, length)
    out = [math.nan] * len(close)
    for i in range(len(close)):
        if not math.isfinite(ag[i]) or not math.isfinite(al[i]):
            continue
        if al[i] == 0:
            out[i] = 100.0
        else:
            rs = ag[i] / al[i]
            out[i] = 100.0 - (100.0 / (1.0 + rs))
    return out


def supertrend(high: list[float], low: list[float], close: list[float], length: int = 10, factor: float = 3.0):
    n = len(close)
    tr = [math.nan] * n
    for i in range(n):
        if i == 0:
            tr[i] = high[i] - low[i]
        else:
            tr[i] = max(high[i] - low[i], abs(high[i] - close[i - 1]), abs(low[i] - close[i - 1]))
    atr = rma(tr, length)
    upper = [math.nan] * n
    lower = [math.nan] * n
    trend = [0] * n
    st = [math.nan] * n
    for i in range(n):
        if not math.isfinite(atr[i]):
            continue
        hl2 = (high[i] + low[i]) / 2.0
        bu = hl2 + factor * atr[i]
        bl = hl2 - factor * atr[i]
        if i == 0 or not math.isfinite(upper[i - 1]):
            upper[i] = bu
            lower[i] = bl
            trend[i] = 1
        else:
            upper[i] = bu if (bu < upper[i - 1] or close[i - 1] > upper[i - 1]) else upper[i - 1]
            lower[i] = bl if (bl > lower[i - 1] or close[i - 1] < lower[i - 1]) else lower[i - 1]
            trend[i] = trend[i - 1]
            if trend[i - 1] == -1 and close[i] > upper[i - 1]:
                trend[i] = 1
            elif trend[i - 1] == 1 and close[i] < lower[i - 1]:
                trend[i] = -1
        st[i] = lower[i] if trend[i] == 1 else upper[i]
    return st, trend


def upper_fractals(high: list[float], n: int = 3) -> list[bool]:
    out = [False] * len(high)
    for i in range(n, len(high) - n):
        window = high[i - n : i + n + 1]
        # require center to be the unique highest high to avoid flat duplicate marks
        if high[i] == max(window) and window.count(high[i]) == 1:
            out[i] = True
    return out


def fmt_ts(ts: int) -> str:
    # Gecko timestamps are UTC seconds; user-facing backtest files use WIB (UTC+7).
    return time.strftime("%Y-%m-%d %H:%M", time.gmtime(ts + 7 * 3600))


def streak_lengths(vals: list[bool], target: bool) -> list[int]:
    runs = []
    cur = 0
    for v in vals:
        if v is target:
            cur += 1
        else:
            if cur:
                runs.append(cur)
            cur = 0
    if cur:
        runs.append(cur)
    return runs


def max_streak(vals: list[bool], target: bool) -> int:
    runs = streak_lengths(vals, target)
    return max(runs) if runs else 0


def min_streak(vals: list[bool], target: bool) -> int:
    runs = streak_lengths(vals, target)
    return min(runs) if runs else 0


def simulate(rows: list[dict[str, float]], pool_name: str, pool_addr: str, tf: str) -> list[dict[str, Any]]:
    n = len(rows)
    close = [r["close"] for r in rows]
    high = [r["high"] for r in rows]
    low = [r["low"] for r in rows]
    open_ = [r["open"] for r in rows]
    ts = [int(r["ts"]) for r in rows]
    rsi2 = rsi(close, RSI_LEN)
    ema50 = ema(close, EMA_FAST)
    ema200 = ema(close, EMA_SLOW)
    st_line, st_trend = supertrend(high, low, close, ST_ATR_LEN, ST_FACTOR)
    fract = upper_fractals(high, FRACTAL_N)

    trades = []
    armed_from = None
    last_entry_bar = -1
    start_bar = max(EMA_FAST, ST_ATR_LEN) + FRACTAL_N + 2
    exit_modes = ["TP_FRACTAL"] + [m["name"] for m in BE_MODE_SPECS]

    for i in range(start_bar, n - FRACTAL_N - 2):
        trend_ok = st_trend[i] == 1 and (close[i] > ema50[i] or close[i] > ema200[i])
        if trend_ok and math.isfinite(rsi2[i]) and rsi2[i] > RSI_TRIGGER and armed_from is None:
            armed_from = i

        center = i - FRACTAL_N
        confirm = i
        entry_bar = confirm + 1
        if armed_from is not None and center > armed_from and fract[center] and entry_bar < n and entry_bar > last_entry_bar:
            # trend still valid at confirmation close; prevents entering after trend died during wait
            if not (st_trend[confirm] == 1 and (close[confirm] > ema50[confirm] or close[confirm] > ema200[confirm])):
                continue
            entry = open_[entry_bar]
            tp = high[center]
            if not (tp > entry > 0):
                # If confirmation opens above target already, skip; no usable upside left.
                armed_from = None
                continue
            st_ref = st_line[confirm]
            dist_pct = max(0.0, (close[confirm] - st_ref) / close[confirm]) if close[confirm] > 0 and math.isfinite(st_ref) else math.nan
            sls = {
                "O1_SL50": entry * 0.5,
                "O2_ST2X": entry * (1.0 - 2.0 * dist_pct) if math.isfinite(dist_pct) else math.nan,
            }
            for opt, sl in sls.items():
                for exit_mode in exit_modes:
                    mode_spec = BE_MODE_MAP.get(exit_mode)
                    if not math.isfinite(sl) or sl <= 0 or sl >= entry:
                        outcome = "INV"
                        exit_bar = entry_bar
                        exit_price = entry
                        bars = 0
                        r_mult = 0.0
                        ever_loss = False
                        recovered = False
                        deep50 = deep75 = False
                        deep50_recovered = deep75_recovered = False
                        loss_bars = profit_bars = 0
                    else:
                        risk = entry - sl
                        deep50_level = entry - 0.50 * risk
                        deep75_level = entry - 0.75 * risk
                        outcome = "EXP"
                        exit_bar = n - 1
                        exit_price = close[-1]
                        ever_loss = False
                        recovered = False
                        deep50 = deep75 = False
                        deep50_recovered = deep75_recovered = False
                        loss_bars = profit_bars = 0
                        went_loss = False
                        hit_deep50 = False
                        hit_deep75 = False
                        # same-bar conservative: SL first, then TP, then optional BE recovery
                        for j in range(entry_bar, n):
                            hold_candles = j - entry_bar
                            if low[j] < entry:
                                ever_loss = True
                                went_loss = True
                            if low[j] <= deep50_level:
                                deep50 = True
                                hit_deep50 = True
                            if low[j] <= deep75_level:
                                deep75 = True
                                hit_deep75 = True
                            if close[j] < entry:
                                loss_bars += 1
                            elif close[j] > entry:
                                profit_bars += 1
                            if low[j] <= sl:
                                outcome = "SL"
                                exit_bar = j
                                exit_price = sl
                                break
                            if high[j] >= tp:
                                outcome = "TP"
                                exit_bar = j
                                exit_price = tp
                                break
                            if mode_spec is not None and hold_candles >= mode_spec["min_candles"]:
                                gate_name = mode_spec["gate"]
                                gate_hit = (
                                    ever_loss if gate_name == "ever_loss"
                                    else deep50 if gate_name == "deep50"
                                    else deep75 if gate_name == "deep75"
                                    else False
                                )
                                if gate_hit and high[j] >= entry:
                                    outcome = exit_mode
                                    exit_bar = j
                                    exit_price = entry
                                    if exit_mode == "BE1":
                                        recovered = True
                                    elif exit_mode == "BE50":
                                        deep50_recovered = True
                                    elif exit_mode == "BE75":
                                        deep75_recovered = True
                                    break
                        bars = exit_bar - entry_bar + 1
                        r_mult = (exit_price - entry) / risk if risk > 0 else 0.0
                    trades.append({
                        "pool": pool_name,
                        "pool_address": pool_addr,
                        "tf": tf,
                        "sl_opt": opt,
                        "exit_mode": exit_mode,
                        "be_mode": exit_mode if exit_mode.startswith("BE") else "",
                        "be_gate": mode_spec["gate"] if mode_spec else "",
                        "be_min_candles": mode_spec["min_candles"] if mode_spec else "",
                        "be_depth_pct": (mode_spec["deep_frac"] * 100.0) if mode_spec else "",
                        "trigger_bar": armed_from,
                        "trigger_time_wib": fmt_ts(ts[armed_from]),
                        "fractal_bar": center,
                        "fractal_time_wib": fmt_ts(ts[center]),
                        "confirm_bar": confirm,
                        "confirm_time_wib": fmt_ts(ts[confirm]),
                        "entry_bar": entry_bar,
                        "entry_time_wib": fmt_ts(ts[entry_bar]),
                        "exit_bar": exit_bar,
                        "exit_time_wib": fmt_ts(ts[exit_bar]),
                        "entry": entry,
                        "tp": tp,
                        "sl": sl,
                        "st_confirm": st_ref,
                        "st_dist_pct": dist_pct * 100.0 if math.isfinite(dist_pct) else math.nan,
                        "rsi_trigger": rsi2[armed_from],
                        "rsi_confirm": rsi2[confirm],
                        "outcome": outcome,
                        "bars_held": bars,
                        "minutes_held": bars * TFS[tf]["minutes"],
                        "R": r_mult,
                        "ever_floating_loss": ever_loss,
                        "loss_then_recovered_entry": recovered,
                        "deep50_loss": deep50,
                        "deep50_then_recovered_entry": deep50_recovered,
                        "deep75_loss": deep75,
                        "deep75_then_recovered_entry": deep75_recovered,
                        "loss_bars": loss_bars,
                        "profit_bars": profit_bars,
                    })
            last_entry_bar = entry_bar
            armed_from = None
    return trades


def summarize(trades: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups = {}
    for t in trades:
        key = (t["pool_address"], t["tf"], t["sl_opt"], t["exit_mode"])
        groups.setdefault(key, []).append(t)
    out = []
    for (pool_addr, tf, opt, exit_mode), arr in sorted(groups.items()):
        valid = [t for t in arr if t["outcome"] != "INV"]
        pool_name = arr[0]["pool"]
        pool = pool_label(pool_name, pool_addr)
        wins = sum(1 for t in valid if t["outcome"] == "TP")
        sls = sum(1 for t in valid if t["outcome"] == "SL")
        bes = sum(1 for t in valid if t["outcome"].startswith("BE"))
        exp = sum(1 for t in valid if t["outcome"] == "EXP")
        n = len(valid)
        denom = wins + sls
        ever_loss = sum(1 for t in valid if t["ever_floating_loss"])
        deep50 = sum(1 for t in valid if t.get("deep50_loss"))
        deep50_rec = sum(1 for t in valid if t.get("deep50_then_recovered_entry"))
        deep75 = sum(1 for t in valid if t.get("deep75_loss"))
        deep75_rec = sum(1 for t in valid if t.get("deep75_then_recovered_entry"))
        gate_hit = ever_loss
        gate_rec = sum(1 for t in valid if t["outcome"].startswith("BE"))
        avg_bars = sum(t["bars_held"] for t in valid) / n if n else 0
        avg_min = sum(t["minutes_held"] for t in valid) / n if n else 0
        avg_r = sum(t["R"] for t in valid) / n if n else 0
        out.append({
            "pool": pool,
            "pool_name": pool_name,
            "pool_address": pool_addr,
            "tf": tf,
            "sl_opt": opt,
            "exit_mode": exit_mode,
            "trades": n,
            "TP": wins,
            "SL": sls,
            "BE": bes,
            "EXP": exp,
            "win_rate_resolved_pct": (wins / denom * 100.0) if denom else 0.0,
            "sl_rate_resolved_pct": (sls / denom * 100.0) if denom else 0.0,
            "be_rate_pct": (bes / n * 100.0) if n else 0.0,
            "be_gate_hit": gate_hit,
            "be_gate_recovered": gate_rec,
            "be_gate_recovery_rate_pct": (gate_rec / gate_hit * 100.0) if gate_hit else 0.0,
            "ever_floating_loss": ever_loss,
            "ever_floating_loss_pct": (ever_loss / n * 100.0) if n else 0.0,
            "deep50_loss": deep50,
            "deep50_then_recovered_entry": deep50_rec,
            "deep50_recovery_rate_pct": (deep50_rec / deep50 * 100.0) if deep50 else 0.0,
            "deep75_loss": deep75,
            "deep75_then_recovered_entry": deep75_rec,
            "deep75_recovery_rate_pct": (deep75_rec / deep75 * 100.0) if deep75 else 0.0,
            "max_consec_win": max_streak([t["outcome"] == "TP" for t in valid if t["outcome"] in ("TP", "SL")], True),
            "min_consec_win": min_streak([t["outcome"] == "TP" for t in valid if t["outcome"] in ("TP", "SL")], True),
            "max_consec_loss": max_streak([t["outcome"] == "TP" for t in valid if t["outcome"] in ("TP", "SL")], False),
            "min_consec_loss": min_streak([t["outcome"] == "TP" for t in valid if t["outcome"] in ("TP", "SL")], False),
            "avg_bars_held": avg_bars,
            "avg_minutes_held": avg_min,
            "avg_R": avg_r,
            "sum_R": sum(t["R"] for t in valid),
        })
    return out


def write_csv(path: Path, rows: list[dict[str, Any]]):
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)


def read_ohlcv_csv(path: Path) -> list[dict[str, float]]:
    rows = []
    with path.open("r", newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            rows.append({
                "ts": int(float(r["ts"])),
                "open": float(r["open"]),
                "high": float(r["high"]),
                "low": float(r["low"]),
                "close": float(r["close"]),
                "volume": float(r["volume"]),
            })
    return rows


def md_report(summary: list[dict[str, Any]], trades: list[dict[str, Any]], data_counts: list[dict[str, Any]]) -> str:
    lines = []
    lines.append("# RSI(2) + Fractal(3) Backtest — Meteora SOL Pools")
    lines.append("")
    lines.append("Rule: ST bullish + close > EMA50/EMA200; RSI(2)>90; wait confirmed upper fractal(3); entry next candle open; TP=fractal high.")
    lines.append("SL O1=-50%; SL O2=2x distance from confirmation close to Supertrend line.")
    lines.append("")
    lines.append("## Data coverage")
    lines.append("| Pool | TF | Candles | Start WIB | End WIB |")
    lines.append("|---|---|---:|---|---|")
    for d in data_counts:
        lines.append(f"| {d['pool']} | {d['tf']} | {d['candles']} | {d['start']} | {d['end']} |")
    lines.append("")
    lines.append("## Summary")
    lines.append("| Pool | TF | SL | Exit | Tr | TP | BE | BE% | SL | EXP | WR% | BE Gate Hit | BE Gate Rec | BE Gate% | Wstreak | Lstreak | AvgHold | SumR |")
    lines.append("|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|")
    for s in summary:
        lines.append(
            f"| {s['pool']} | {s['tf']} | {s['sl_opt']} | {s['exit_mode']} | {s['trades']} | {s['TP']} | {s['BE']} | {s['be_rate_pct']:.1f} | {s['SL']} | {s['EXP']} | "
            f"{s['win_rate_resolved_pct']:.1f} | {s['be_gate_hit']} | {s['be_gate_recovered']} | {s['be_gate_recovery_rate_pct']:.1f} | "
            f"{s['min_consec_win']}/{s['max_consec_win']} | {s['min_consec_loss']}/{s['max_consec_loss']} | {s['avg_minutes_held']:.0f}m | {s['sum_R']:.2f} |"
        )
    lines.append("")
    lines.append("## Notes")
    lines.append("- `BE1` = any floating loss, but BE only allowed after >=2 candles.")
    lines.append("- `BE50` = trade must first go <=50% of risk underwater, BE only allowed after >=2 candles.")
    lines.append("- `BE75` = trade must first go <=75% of risk underwater, BE only allowed after >=3 candles.")
    lines.append("- Exit `BE` rows mean the mode-specific BE gate was satisfied and price returned to entry after the minimum candle gate; TP is still checked first on each candle.")
    lines.append("- Win/loss streak is calculated per pool × timeframe × SL option × exit mode, sorted chronologically.")
    lines.append("- Same-candle conflict is conservative: SL checked before TP, then optional BE.")
    return "\n".join(lines)


def main():
    pools = load_pools()
    all_trades: list[dict[str, Any]] = []
    data_counts = []
    for p in pools:
        pool = p["pool_address"]
        name = p.get("name") or pool[:8]
        label = pool_label(name, pool)
        for tf in TFS:
            print(f"[fetch] {label} {tf} {pool}", flush=True)
            cache_path = OUTDIR / f"ohlcv_{safe_name(name)}_{pool[:8]}_{tf}.csv"
            if cache_path.exists() and cache_path.stat().st_size > 0:
                rows = read_ohlcv_csv(cache_path)
                print(f"[cache] {label} {tf}: {len(rows)} candles", flush=True)
            else:
                rows = fetch_ohlcv(pool, tf)
                write_csv(cache_path, rows)
            if rows:
                data_counts.append({
                    "pool": label,
                    "tf": tf,
                    "candles": len(rows),
                    "start": fmt_ts(int(rows[0]["ts"])),
                    "end": fmt_ts(int(rows[-1]["ts"])),
                })
            print(f"[run] {label} {tf}: {len(rows)} candles", flush=True)
            if len(rows) < max(EMA_FAST + FRACTAL_N + 5, 70):
                print(f"[skip] {label} {tf}: not enough candles for EMA50/fractal warmup", flush=True)
                continue
            all_trades.extend(simulate(rows, name, pool, tf))
            time.sleep(REQ_SLEEP)

    summary = summarize(all_trades)
    write_csv(OUTDIR / "trade_journal.csv", all_trades)
    write_csv(OUTDIR / "summary.csv", summary)
    (OUTDIR / "report.md").write_text(md_report(summary, all_trades, data_counts), encoding="utf-8")
    print(f"DONE trades={len(all_trades)} summary_rows={len(summary)} out={OUTDIR}")


if __name__ == "__main__":
    main()
