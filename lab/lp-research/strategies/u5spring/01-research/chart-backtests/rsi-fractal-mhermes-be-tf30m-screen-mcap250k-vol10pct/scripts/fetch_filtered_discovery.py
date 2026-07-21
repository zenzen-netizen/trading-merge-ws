#!/usr/bin/env python3
from __future__ import annotations

import json
import time
from pathlib import Path
from urllib.parse import urlencode

import requests

BASE = "https://pool-discovery-api.datapi.meteora.ag/pools"
ROOT = Path(__file__).resolve().parents[1]
OUT_JSON = ROOT / "filtered-top20-sol-30m-fee-tvl-age15h-mcap250k-vol10pct.json"
OUT_MD = ROOT / "filtered-top20-sol-30m-fee-tvl-age15h-mcap250k-vol10pct.md"

PAGE_SIZE = 1000
TAKE_TOP = 20
TIMEFRAME = "30m"
CATEGORY = "top"
MIN_AGE_HOURS = 15
MIN_MCAP = 250_000
MIN_VOLUME_TVL_RATIO = 0.10
SOL_MINT = "So11111111111111111111111111111111111111112"
USDC_MINTS = {
    "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
    "Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB",
}


def is_sol_pair(pool: dict) -> bool:
    tx = (pool or {}).get("token_x") or {}
    ty = (pool or {}).get("token_y") or {}
    addrs = {tx.get("address"), ty.get("address")}
    syms = {str(tx.get("symbol") or "").upper(), str(ty.get("symbol") or "").upper()}
    return SOL_MINT in addrs or "SOL" in syms or "WSOL" in syms


def has_usdc(pool: dict) -> bool:
    tx = (pool or {}).get("token_x") or {}
    ty = (pool or {}).get("token_y") or {}
    addrs = {tx.get("address"), ty.get("address")}
    syms = {str(tx.get("symbol") or "").upper(), str(ty.get("symbol") or "").upper()}
    return bool(addrs & USDC_MINTS) or "USDC" in syms


def base_token(pool: dict) -> dict:
    tx = (pool or {}).get("token_x") or {}
    ty = (pool or {}).get("token_y") or {}
    if tx.get("address") == SOL_MINT or str(tx.get("symbol") or "").upper() in {"SOL", "WSOL"}:
        return ty
    return tx


def age_hours_ms(created_at_ms: int | float | None) -> float | None:
    if not created_at_ms:
        return None
    return round((time.time() * 1000 - float(created_at_ms)) / 3_600_000, 1)


def fetch() -> dict:
    now_ms = int(time.time() * 1000)
    min_created_at = now_ms - MIN_AGE_HOURS * 3_600_000
    filters = "&&".join([
        f"base_token_market_cap>={MIN_MCAP}",
        f"volume_tvl_ratio>={MIN_VOLUME_TVL_RATIO}",
        f"base_token_created_at<={min_created_at}",
    ])
    params = {
        "page_size": PAGE_SIZE,
        "timeframe": TIMEFRAME,
        "category": CATEGORY,
        "filter_by": filters,
    }
    r = requests.get(BASE, params=params, timeout=60)
    r.raise_for_status()
    payload = r.json()
    rows = payload.get("data") or []

    filtered = []
    for pool in rows:
        if not is_sol_pair(pool):
            continue
        if has_usdc(pool):
            continue
        b = base_token(pool)
        pool["__base_token_market_cap"] = b.get("market_cap")
        pool["__base_token_symbol"] = b.get("symbol")
        pool["__age_hours"] = age_hours_ms(b.get("created_at"))
        filtered.append(pool)

    filtered.sort(key=lambda p: float(p.get("fee_active_tvl_ratio") or 0.0), reverse=True)
    top = filtered[:TAKE_TOP]

    return {
        "source": {
            "endpoint": BASE,
            "page_size": PAGE_SIZE,
            "timeframe": TIMEFRAME,
            "category": CATEGORY,
            "minTokenAgeHours": MIN_AGE_HOURS,
            "minBaseTokenMarketCap": MIN_MCAP,
            "minVolumeTvlRatio": MIN_VOLUME_TVL_RATIO,
            "post_filter": "only SOL pairs; exclude USDC pairs; sort by fee_active_tvl_ratio desc; take top 20",
            "query": urlencode(params),
        },
        "total": payload.get("total"),
        "raw_rows": len(rows),
        "filtered_count": len(filtered),
        "data": top,
    }


def fmt_num(x: float | int | None, digits: int = 2) -> str:
    if x is None:
        return "-"
    return f"{float(x):,.{digits}f}"


def write_md(obj: dict):
    lines = []
    lines.append("# Meteora raw discovery — SOL pairs, 30m, top 20 by fee/TVL, min age 15h, min mcap 250k, min vol/tvl 10%")
    lines.append("")
    lines.append("Rule: only SOL pairs; exclude USDC; token age >= 15h; base token market cap >= 250k; volume/tvl ratio >= 0.10; sort by fee_active_tvl_ratio desc; top 20.")
    lines.append("")
    lines.append("| # | Pool | Pair | Address | Age(h) | Base MCAP | Fee/TVL | Vol/TVL | TVL | Volume | Volatility |")
    lines.append("|---|------|------|---------|--------:|----------:|--------:|--------:|-----:|--------:|-----------:|")
    for i, pool in enumerate(obj["data"], 1):
        tx = pool.get("token_x") or {}
        ty = pool.get("token_y") or {}
        pair = f"{tx.get('symbol','?')}/{ty.get('symbol','?')}"
        lines.append(
            f"| {i} | {pool.get('name','?')} | {pair} | `{pool.get('pool_address','')}` | "
            f"{fmt_num(pool.get('__age_hours'),1)} | {fmt_num(pool.get('__base_token_market_cap'))} | "
            f"{fmt_num(pool.get('fee_active_tvl_ratio'),4)} | {fmt_num(pool.get('volume_tvl_ratio'),4)} | "
            f"{fmt_num(pool.get('tvl'))} | {fmt_num(pool.get('volume'))} | {fmt_num(pool.get('volatility'),4)} |"
        )
    lines.append("")
    lines.append(f"- Total raw pools from API after server-side mcap/vol/age filter: {obj.get('total')}")
    lines.append(f"- Rows returned in this page: {obj.get('raw_rows')}")
    lines.append(f"- SOL non-USDC candidates after post-filter: {obj.get('filtered_count')}")
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")


def main():
    obj = fetch()
    OUT_JSON.write_text(json.dumps(obj, indent=2), encoding="utf-8")
    write_md(obj)
    print(f"WROTE {OUT_JSON}")
    print(f"WROTE {OUT_MD}")
    print(f"filtered_count={obj['filtered_count']} top_saved={len(obj['data'])}")


if __name__ == "__main__":
    main()
