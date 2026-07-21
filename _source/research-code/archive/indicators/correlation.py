"""
Correlation module — calculates price correlation of all watchlist pairs
against BTCUSDT spot (the reference). Uses Pearson correlation on close prices
with configurable lookback window.
"""

import pandas as pd
import numpy as np


def calculate_correlation(all_data, ref_key="BTCUSDT_spot", lookback=100):
    """
    Calculate correlation of all pairs vs reference (BTCUSDT spot).
    
    Strategy:
    - For SPOT pairs: use their own SPOT close vs BTC SPOT close
    - For PERP pairs: if same symbol exists in SPOT, use the SPOT pair correlation
      (since PERP tracks spot closely). If PERP-only symbol (e.g. HYPE), use PERP close.
    - For FUTURES: use futures close vs BTC SPOT close
    
    Args:
        all_data: dict { "BTCUSDT_spot": { "1h": df, ... }, ... }
        ref_key: reference pair key (default BTCUSDT_spot)
        lookback: number of candles to use for correlation
    
    Returns:
        dict: { timeframe: [ {pair, symbol, mtype, corr, label, distance_pct, note}, ... ] }
    """
    results = {}
    
    # Get reference data per timeframe
    ref_data = all_data.get(ref_key, {})
    if not ref_data or not isinstance(ref_data, dict):
        return results
    
    # Determine which symbol to use for each pair key
    # Map: pair_key → (symbol_to_correlate, source_key)
    pair_mapping = {}
    for pair_key in all_data.keys():
        parts = pair_key.rsplit("_", 1)
        symbol = parts[0]
        mtype = parts[1] if len(parts) > 1 else "spot"
        
        # Prefer spot data if available for the same symbol
        spot_key = f"{symbol}_spot"
        if mtype != "spot" and spot_key in all_data:
            pair_mapping[pair_key] = (symbol, spot_key, mtype)
        else:
            pair_mapping[pair_key] = (symbol, pair_key, mtype)
    
    for tf in ["15m", "1h", "2h", "4h", "1d", "1w"]:
        ref_df = ref_data.get(tf)
        if ref_df is None or ref_df.empty:
            continue
        
        ref_close = ref_df["close"].tail(lookback).values
        
        tf_results = []
        
        for pair_key, (symbol, source_key, mtype) in pair_mapping.items():
            if pair_key == ref_key:
                continue  # Skip BTC ref itself
            # Skip BTC perp/futures — same symbol as reference, correlation = 1.0
            ref_symbol = ref_key.rsplit("_", 1)[0]
            if symbol == ref_symbol:
                continue
            # Skip perp pair if spot version of same symbol already exists in results
            # (avoid duplicate: ETHUSDT_perp uses ETHUSDT_spot data → same correlation)
            spot_key = f"{symbol}_spot"
            if mtype != "spot" and spot_key in all_data:
                # This perp tracks spot, and spot will be shown separately → skip perp
                continue
            # Skip futures entirely
            if mtype == "futures":
                continue
            
            pair_df = all_data.get(source_key, {}).get(tf)
            if pair_df is None or pair_df.empty:
                continue
            
            pair_close = pair_df["close"].tail(lookback).values
            
            # Need same length
            min_len = min(len(ref_close), len(pair_close))
            if min_len < 10:
                continue
            
            ref_arr = ref_close[-min_len:]
            pair_arr = pair_close[-min_len:]
            
            # Pearson correlation
            corr = np.corrcoef(ref_arr, pair_arr)[0, 1]
            
            # Handle NaN
            if np.isnan(corr):
                continue
            
            # Label
            abs_corr = abs(corr)
            if abs_corr > 0.9:
                label = "Sangat Tinggi"
                emoji = "🟢"
            elif abs_corr > 0.7:
                label = "Tinggi"
                emoji = "🟢"
            elif abs_corr > 0.5:
                label = "Sedang"
                emoji = "🟡"
            elif abs_corr > 0.3:
                label = "Rendah"
                emoji = "🟠"
            else:
                label = "Sangat Rendah"
                emoji = "🔴"
            
            if corr < 0:
                label += " (Negatif)"
            
            # Distance: how far is this pair from BTC in terms of price change
            # Calculate % change over lookback for both
            ref_change_pct = ((ref_arr[-1] - ref_arr[0]) / ref_arr[0]) * 100 if ref_arr[0] != 0 else 0
            pair_change_pct = ((pair_arr[-1] - pair_arr[0]) / pair_arr[0]) * 100 if pair_arr[0] != 0 else 0
            distance_pct = pair_change_pct - ref_change_pct
            
            # Note about pair type
            note = ""
            if mtype == "perp" and source_key != pair_key:
                note = "using spot data (perp tracks spot)"
            elif mtype == "futures":
                note = "quarterly contract"
            
            tf_results.append({
                "pair_key": pair_key,
                "symbol": symbol,
                "mtype": mtype,
                "correlation": round(corr, 3),
                "correlation_label": label,
                "correlation_emoji": emoji,
                "distance_pct": round(distance_pct, 2),
                "ref_change_pct": round(ref_change_pct, 2),
                "pair_change_pct": round(pair_change_pct, 2),
                "note": note,
            })
        
        # Sort by absolute correlation descending (most correlated first)
        tf_results.sort(key=lambda x: abs(x["correlation"]), reverse=True)
        
        results[tf] = tf_results
    
    return results


def format_correlation_section(corr_results):
    """
    Format correlation data as tree-style section for Telegram.
    Only show 1h and 4h as reference (avoid spam), with summary.
    """
    lines = []
    lines.append("🔗 C O R R E L A T I O N   vs   BTCUSDT (SPOT)")
    lines.append("━" * 45)
    
    # Show 1h and 4h as main correlation views
    for tf in ["1h", "4h"]:
        tf_data = corr_results.get(tf)
        if not tf_data:
            continue
        
        lines.append(f"├ 📐 {tf} (lookback 100)")
        for item in tf_data:
            sym = item["symbol"]
            mt = item["mtype"].upper()
            corr = item["correlation"]
            emoji = item["correlation_emoji"]
            label = item["correlation_label"]
            dist = item["distance_pct"]
            dist_emoji = "📈" if dist > 0 else "📉" if dist < 0 else "➖️"
            
            dist_str = f"{dist:+.1f}%" if abs(dist) < 1000 else f"{dist:+.0f}%"
            pair_label = f"{sym}_{mt}" if mt != "SPOT" else sym
            
            note = ""
            if item["note"]:
                note = f" · {item['note']}"
            
            lines.append(f"│  ├ {emoji} {pair_label:16s} r={corr:+.3f} [{label}]{note}")
            lines.append(f"│  │  └ {dist_emoji} Δ vs BTC: {dist_str}")
        
        lines.append("│")
    
    # Summary
    tf_1h = corr_results.get("1h", [])
    if tf_1h:
        most_corr = tf_1h[0] if tf_1h else None
        least_corr = tf_1h[-1] if tf_1h else None
        
        lines.append("├ 📊 Summary (1h)")
        if most_corr:
            lines.append(f"│  ├ Strongest: {most_corr['symbol']} (r={most_corr['correlation']:+.3f})")
        if least_corr:
            lines.append(f"│  └ Weakest:   {least_corr['symbol']} (r={least_corr['correlation']:+.3f})")
    
    lines.append("━" * 45)
    
    return "\n".join(lines)