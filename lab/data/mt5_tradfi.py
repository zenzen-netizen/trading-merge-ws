"""MetaTrader 5 helper for Bybit TradFi market data.

Goal:
- Connect to an already logged-in MT5 terminal.
- Auto-detect the Gold symbol for Bybit TradFi (e.g. XAUUSD+, XAUUSD, or a variant).
- Fetch real-time quote and OHLC data.
- Return both JSON-serializable payloads and pandas DataFrames.

Notes:
- This module uses the official MetaTrader5 Python package.
- It does not scrape any website.
- It expects the MT5 terminal to already be installed and logged in.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple, Union
import math
import re

import pandas as pd

try:
    import MetaTrader5 as mt5
except Exception:  # pragma: no cover - import error handled at runtime
    mt5 = None


# --- Exceptions ------------------------------------------------------------


class MT5Error(RuntimeError):
    """Base MT5 helper error."""


class MT5ConnectionError(MT5Error):
    """Raised when MT5 initialization or login fails."""


class MT5SymbolNotFound(MT5Error):
    """Raised when the requested symbol cannot be auto-detected."""


class MT5DataError(MT5Error):
    """Raised when data retrieval returns empty / invalid payload."""


# --- Config ----------------------------------------------------------------


DEFAULT_GOLD_ALIASES = [
    "XAUUSD+",
    "XAUUSD",
    "XAUUSDm",
    "XAUUSD.a",
    "XAUUSD#",
    "GOLD",
    "XAU",
]

# MT5 timeframe constants mapping.
_TIMEFRAME_MAP = {
    "M1": lambda m5: m5.TIMEFRAME_M1,
    "M2": lambda m5: m5.TIMEFRAME_M2,
    "M3": lambda m5: m5.TIMEFRAME_M3,
    "M4": lambda m5: m5.TIMEFRAME_M4,
    "M5": lambda m5: m5.TIMEFRAME_M5,
    "M6": lambda m5: m5.TIMEFRAME_M6,
    "M10": lambda m5: m5.TIMEFRAME_M10,
    "M12": lambda m5: m5.TIMEFRAME_M12,
    "M15": lambda m5: m5.TIMEFRAME_M15,
    "M20": lambda m5: m5.TIMEFRAME_M20,
    "M30": lambda m5: m5.TIMEFRAME_M30,
    "H1": lambda m5: m5.TIMEFRAME_H1,
    "H2": lambda m5: m5.TIMEFRAME_H2,
    "H3": lambda m5: m5.TIMEFRAME_H3,
    "H4": lambda m5: m5.TIMEFRAME_H4,
    "H6": lambda m5: m5.TIMEFRAME_H6,
    "H8": lambda m5: m5.TIMEFRAME_H8,
    "H12": lambda m5: m5.TIMEFRAME_H12,
    "D1": lambda m5: m5.TIMEFRAME_D1,
    "W1": lambda m5: m5.TIMEFRAME_W1,
    "MN1": lambda m5: m5.TIMEFRAME_MN1,
}

_TIMEFRAME_ALIASES = {
    "1m": "M1", "2m": "M2", "3m": "M3", "4m": "M4", "5m": "M5",
    "6m": "M6", "10m": "M10", "12m": "M12", "15m": "M15", "20m": "M20",
    "30m": "M30", "1h": "H1", "2h": "H2", "3h": "H3", "4h": "H4",
    "6h": "H6", "8h": "H8", "12h": "H12", "1d": "D1", "1w": "W1",
    "1mn": "MN1", "1mo": "MN1",
}


# --- Helpers ---------------------------------------------------------------


def _require_mt5() -> Any:
    if mt5 is None:
        raise MT5ConnectionError(
            "MetaTrader5 Python package is not installed or cannot be imported."
        )
    return mt5


def _norm_symbol(text: str) -> str:
    return re.sub(r"[^A-Z0-9]", "", (text or "").upper())


def _utc_ms(dt: Optional[datetime] = None) -> int:
    if dt is None:
        dt = datetime.now(timezone.utc)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return int(dt.timestamp() * 1000)


def _obj_to_dict(obj: Any) -> Dict[str, Any]:
    if obj is None:
        return {}
    if hasattr(obj, "_asdict"):
        return dict(obj._asdict())
    if isinstance(obj, dict):
        return dict(obj)
    return {k: getattr(obj, k) for k in dir(obj) if not k.startswith("_")}


def _jsonable(value: Any) -> Any:
    if isinstance(value, pd.Timestamp):
        return value.isoformat()
    if isinstance(value, datetime):
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.isoformat()
    if isinstance(value, (pd.Series, pd.Index)):
        return value.tolist()
    if isinstance(value, pd.DataFrame):
        return value.to_dict(orient="records")
    if isinstance(value, (list, tuple)):
        return [_jsonable(v) for v in value]
    if isinstance(value, dict):
        return {k: _jsonable(v) for k, v in value.items()}
    if hasattr(value, "item"):
        try:
            return value.item()
        except Exception:
            pass
    if isinstance(value, float) and math.isnan(value):
        return None
    return value


def _timeframe_constant(tf: Union[str, int]) -> int:
    m5 = _require_mt5()
    if isinstance(tf, int):
        return tf
    tf_key = str(tf).strip().lower()
    tf_norm = _TIMEFRAME_ALIASES.get(tf_key, str(tf).strip().upper())
    if tf_norm not in _TIMEFRAME_MAP:
        raise ValueError(f"Unsupported timeframe: {tf}")
    return _TIMEFRAME_MAP[tf_norm](m5)


@dataclass
class Quote:
    symbol: str
    bid: Optional[float]
    ask: Optional[float]
    last: Optional[float]
    time: Optional[int]
    time_msc: Optional[int]
    spread: Optional[float] = None
    volume: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "symbol": self.symbol,
            "bid": self.bid,
            "ask": self.ask,
            "last": self.last,
            "time": self.time,
            "time_msc": self.time_msc,
            "spread": self.spread,
            "volume": self.volume,
            "timestamp_utc": (
                datetime.fromtimestamp((self.time_msc or self.time or 0) / 1000, tz=timezone.utc).isoformat()
                if (self.time_msc or self.time)
                else None
            ),
        }


# --- Main client -----------------------------------------------------------


class MT5TradFiClient:
    """Thin wrapper around MetaTrader5 for Bybit TradFi data."""

    def __init__(
        self,
        terminal_path: Optional[str] = None,
        login: Optional[int] = None,
        password: Optional[str] = None,
        server: Optional[str] = None,
        portable: bool = False,
    ) -> None:
        self._mt5 = _require_mt5()
        self.terminal_path = terminal_path
        self.login = login
        self.password = password
        self.server = server
        self.portable = portable
        self.connected = False

    def connect(self) -> None:
        """Initialize the MT5 terminal (it must already be logged in)."""
        init_ok = False
        if self.terminal_path:
            init_ok = self._mt5.initialize(
                path=self.terminal_path,
                portable=self.portable,
            )
        else:
            init_ok = self._mt5.initialize(portable=self.portable)

        if not init_ok:
            err = self._mt5.last_error()
            raise MT5ConnectionError(f"MT5 initialize() failed: {err}")

        # Optional re-login if credentials were supplied.
        if self.login is not None:
            login_ok = self._mt5.login(
                login=self.login,
                password=self.password or "",
                server=self.server or "",
            )
            if not login_ok:
                err = self._mt5.last_error()
                self._mt5.shutdown()
                raise MT5ConnectionError(f"MT5 login() failed: {err}")

        self.connected = True

    def shutdown(self) -> None:
        try:
            self._mt5.shutdown()
        finally:
            self.connected = False

    def ensure_connected(self) -> None:
        if not self.connected:
            self.connect()

    def account_info(self) -> Dict[str, Any]:
        self.ensure_connected()
        info = self._mt5.account_info()
        if info is None:
            raise MT5ConnectionError(f"MT5 account_info() failed: {self._mt5.last_error()}")
        return _obj_to_dict(info)

    def symbols(self) -> List[Dict[str, Any]]:
        self.ensure_connected()
        syms = self._mt5.symbols_get()
        if syms is None:
            raise MT5DataError(f"MT5 symbols_get() failed: {self._mt5.last_error()}")
        return [_obj_to_dict(s) for s in syms]

    def detect_gold_symbol(
        self,
        preferred: Optional[Sequence[str]] = None,
        strict_bybit: bool = True,
    ) -> str:
        """Auto-detect the gold symbol.

        Search order:
        1. Preferred aliases in order.
        2. Exact/normalized matches against all visible symbols.
        3. Fuzzy matches using description/path/base fields.

        If strict_bybit=True, prefer symbols whose path/description mentions Bybit.
        """
        self.ensure_connected()
        symbols = self._mt5.symbols_get()
        if not symbols:
            raise MT5DataError(f"MT5 symbols_get() returned no symbols: {self._mt5.last_error()}")

        preferred_list = list(preferred or DEFAULT_GOLD_ALIASES)
        visible = [s for s in symbols if getattr(s, "visible", True)]

        # 1) Exact symbol match.
        for alias in preferred_list:
            for s in visible:
                if getattr(s, "name", "") == alias or getattr(s, "symbol", "") == alias:
                    return getattr(s, "name", getattr(s, "symbol", alias))

        # 2) Normalized match, allowing suffix variants.
        alias_norms = [_norm_symbol(a) for a in preferred_list]
        for s in visible:
            sym = getattr(s, "name", getattr(s, "symbol", ""))
            if _norm_symbol(sym) in alias_norms:
                return sym
            # common suffix variant, e.g. XAUUSDplus -> XAUUSD
            for an in alias_norms:
                if _norm_symbol(sym).startswith(an) or an.startswith(_norm_symbol(sym)):
                    return sym

        # 3) Fuzzy match for gold by metadata.
        scored: List[Tuple[int, str]] = []
        for s in visible:
            sym = getattr(s, "name", getattr(s, "symbol", ""))
            desc = " ".join(
                str(getattr(s, field, ""))
                for field in ("description", "path", "currency_base", "currency_profit", "currency_margin")
            ).upper()
            sym_u = sym.upper()
            score = 0
            if "XAU" in sym_u:
                score += 60
            if "GOLD" in sym_u:
                score += 45
            if "XAU" in desc:
                score += 30
            if "GOLD" in desc:
                score += 25
            if "BYBIT" in desc:
                score += 20
            if "TRADFI" in desc:
                score += 10
            if strict_bybit and "BYBIT" in desc:
                score += 20
            if score > 0:
                scored.append((score, sym))

        if scored:
            scored.sort(key=lambda x: (-x[0], x[1]))
            return scored[0][1]

        raise MT5SymbolNotFound(
            "Could not auto-detect a gold symbol. Tried aliases: " + ", ".join(preferred_list)
        )

    def _select_symbol(self, symbol: str) -> str:
        self.ensure_connected()
        info = self._mt5.symbol_info(symbol)
        if info is None:
            raise MT5SymbolNotFound(f"MT5 symbol not found: {symbol}")
        # Ensure the symbol is in Market Watch.
        if not self._mt5.symbol_select(symbol, True):
            raise MT5SymbolNotFound(f"MT5 symbol_select() failed for {symbol}: {self._mt5.last_error()}")
        return symbol

    def resolve_symbol(self, symbol: Optional[str] = None, preferred: Optional[Sequence[str]] = None) -> str:
        if symbol:
            return self._select_symbol(symbol)
        detected = self.detect_gold_symbol(preferred=preferred)
        return self._select_symbol(detected)

    def get_quote(self, symbol: Optional[str] = None) -> Dict[str, Any]:
        resolved = self.resolve_symbol(symbol)
        tick = self._mt5.symbol_info_tick(resolved)
        if tick is None:
            raise MT5DataError(f"MT5 symbol_info_tick() returned no data for {resolved}: {self._mt5.last_error()}")
        tick_d = _obj_to_dict(tick)
        q = Quote(
            symbol=resolved,
            bid=tick_d.get("bid"),
            ask=tick_d.get("ask"),
            last=tick_d.get("last") if tick_d.get("last", 0) not in (None, 0) else None,
            time=tick_d.get("time"),
            time_msc=tick_d.get("time_msc"),
            spread=tick_d.get("spread"),
            volume=tick_d.get("volume"),
        )
        payload = q.to_dict()
        payload["raw_tick"] = _jsonable(tick_d)
        return payload

    def get_ohlc(
        self,
        timeframe: Union[str, int],
        symbol: Optional[str] = None,
        count: int = 500,
        start_pos: int = 0,
        end_time: Optional[datetime] = None,
    ) -> Tuple[Dict[str, Any], pd.DataFrame]:
        """Fetch OHLC data and return both JSON payload and DataFrame.

        Args:
            timeframe: e.g. 'M15', 'H1', '1h', '4h', '1d'
            symbol: optional override, otherwise auto-detect gold symbol
            count: number of bars to fetch
            start_pos: bar position for copy_rates_from_pos
            end_time: optional end datetime for copy_rates_from
        """
        resolved = self.resolve_symbol(symbol)
        tf = _timeframe_constant(timeframe)

        if end_time is not None:
            if end_time.tzinfo is None:
                end_time = end_time.replace(tzinfo=timezone.utc)
            rates = self._mt5.copy_rates_from(resolved, tf, end_time, count)
        else:
            rates = self._mt5.copy_rates_from_pos(resolved, tf, start_pos, count)

        if rates is None or len(rates) == 0:
            raise MT5DataError(
                f"MT5 rate fetch failed for {resolved}/{timeframe}: {self._mt5.last_error()}"
            )

        df = pd.DataFrame(rates)

        # MetaTrader5 usually returns a structured array with named columns.
        # If the source is a plain tuple/list matrix, normalize the common MT5 layout.
        if "time" not in df.columns and 0 in df.columns:
            common_cols = [
                "time", "open", "high", "low", "close",
                "tick_volume", "spread", "real_volume", "volume",
            ]
            if len(df.columns) >= 5:
                rename_map = {old: common_cols[i] for i, old in enumerate(df.columns[: len(common_cols)])}
                df = df.rename(columns=rename_map)

        if "time" in df.columns:
            df["time"] = pd.to_datetime(df["time"], unit="s", utc=True)
            df = df.rename(columns={"time": "timestamp_utc"})
            df = df.set_index("timestamp_utc")
        # Normalize numeric columns.
        for col in ["open", "high", "low", "close", "tick_volume", "spread", "real_volume", "volume"]:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")

        # JSON-safe structure.
        payload = {
            "symbol": resolved,
            "timeframe": str(timeframe),
            "count": int(len(df)),
            "bars": _jsonable(df.reset_index()),
        }
        return payload, df

    def fetch_market(
        self,
        timeframe: Union[str, int],
        symbol: Optional[str] = None,
        count: int = 500,
        start_pos: int = 0,
        end_time: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """Convenience wrapper returning quote + OHLC in one payload."""
        quote = self.get_quote(symbol=symbol)
        ohlc_json, ohlc_df = self.get_ohlc(
            timeframe=timeframe,
            symbol=quote["symbol"],
            count=count,
            start_pos=start_pos,
            end_time=end_time,
        )
        return {
            "ok": True,
            "symbol": quote["symbol"],
            "quote": quote,
            "ohlc": ohlc_json,
            "dataframe": ohlc_df,
        }


# --- Module-level helpers --------------------------------------------------


def connect(
    terminal_path: Optional[str] = None,
    login: Optional[int] = None,
    password: Optional[str] = None,
    server: Optional[str] = None,
    portable: bool = False,
) -> MT5TradFiClient:
    client = MT5TradFiClient(
        terminal_path=terminal_path,
        login=login,
        password=password,
        server=server,
        portable=portable,
    )
    client.connect()
    return client


def detect_gold_symbol(
    terminal_path: Optional[str] = None,
    login: Optional[int] = None,
    password: Optional[str] = None,
    server: Optional[str] = None,
    preferred: Optional[Sequence[str]] = None,
    strict_bybit: bool = True,
) -> str:
    client = connect(
        terminal_path=terminal_path,
        login=login,
        password=password,
        server=server,
    )
    try:
        return client.detect_gold_symbol(preferred=preferred, strict_bybit=strict_bybit)
    finally:
        client.shutdown()


def get_quote(
    symbol: Optional[str] = None,
    terminal_path: Optional[str] = None,
    login: Optional[int] = None,
    password: Optional[str] = None,
    server: Optional[str] = None,
) -> Dict[str, Any]:
    client = connect(terminal_path=terminal_path, login=login, password=password, server=server)
    try:
        return client.get_quote(symbol=symbol)
    finally:
        client.shutdown()


def get_ohlc(
    timeframe: Union[str, int],
    symbol: Optional[str] = None,
    count: int = 500,
    start_pos: int = 0,
    end_time: Optional[datetime] = None,
    terminal_path: Optional[str] = None,
    login: Optional[int] = None,
    password: Optional[str] = None,
    server: Optional[str] = None,
) -> Tuple[Dict[str, Any], pd.DataFrame]:
    client = connect(terminal_path=terminal_path, login=login, password=password, server=server)
    try:
        return client.get_ohlc(
            timeframe=timeframe,
            symbol=symbol,
            count=count,
            start_pos=start_pos,
            end_time=end_time,
        )
    finally:
        client.shutdown()


def fetch_market(
    timeframe: Union[str, int],
    symbol: Optional[str] = None,
    count: int = 500,
    start_pos: int = 0,
    end_time: Optional[datetime] = None,
    terminal_path: Optional[str] = None,
    login: Optional[int] = None,
    password: Optional[str] = None,
    server: Optional[str] = None,
) -> Dict[str, Any]:
    client = connect(terminal_path=terminal_path, login=login, password=password, server=server)
    try:
        return client.fetch_market(
            timeframe=timeframe,
            symbol=symbol,
            count=count,
            start_pos=start_pos,
            end_time=end_time,
        )
    finally:
        client.shutdown()


__all__ = [
    "MT5Error",
    "MT5ConnectionError",
    "MT5SymbolNotFound",
    "MT5DataError",
    "MT5TradFiClient",
    "connect",
    "detect_gold_symbol",
    "get_quote",
    "get_ohlc",
    "fetch_market",
]
