"""Opt-in current-narrative finder over free, keyless, read-only public endpoints.

This is the *only* module in pumpscore that may touch the network, and it is
strictly opt-in. The deterministic core (model, score, checklist, lifecycle,
sizing, io) never imports it and never makes a request. There are no API keys,
no auth headers, no scraping, and no wallet data here. We only read two public
category endpoints and rank categories by momentum, to answer one question:
"what narrative is hot right now?"

Network access uses the standard library (``urllib``). If you are offline, or a
host is unreachable, the CLI degrades to a clear, actionable message instead of
crashing. The parsing layer is pure and is exercised in CI with a fixture, so no
test ever makes a live call.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

# Free, keyless, read-only public category endpoints.
# CoinGecko: market-cap weighted categories with 24h change.
# DefiLlama: TVL-weighted categories with 1d / 7d change.
COINGECKO_CATEGORIES_URL = "https://api.coingecko.com/api/v3/coins/categories"
DEFILLAMA_CATEGORIES_URL = "https://api.llama.fi/categories"

SOURCES: tuple[str, ...] = ("coingecko", "defillama")

DEFAULT_TIMEOUT_SECONDS = 20.0
# Polite, honest identifier. No key, no token.
_USER_AGENT = (
    "pump-research-framework/0.2 (+https://github.com/baronguyen001/pump-research-framework)"
)


class NarrativeError(RuntimeError):
    """Raised when a narrative source cannot be reached or parsed."""


@dataclass(frozen=True)
class NarrativeRow:
    """One ranked category row, normalized across sources."""

    name: str
    change_24h: float | None
    change_7d: float | None
    market_cap_usd: float | None
    source: str


def _coerce_float(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    # Reject NaN / inf so downstream sorting and formatting stay deterministic.
    if result != result or result in (float("inf"), float("-inf")):
        return None
    return result


def parse_coingecko(payload: Any) -> list[NarrativeRow]:
    """Parse a CoinGecko ``/coins/categories`` payload into rows. Pure, offline."""
    if not isinstance(payload, list):
        raise NarrativeError("CoinGecko payload must be a list of categories")
    rows: list[NarrativeRow] = []
    for item in payload:
        if not isinstance(item, dict):
            continue
        name = str(item.get("name") or item.get("id") or "").strip()
        if not name:
            continue
        rows.append(
            NarrativeRow(
                name=name,
                change_24h=_coerce_float(item.get("market_cap_change_24h")),
                change_7d=None,
                market_cap_usd=_coerce_float(item.get("market_cap")),
                source="coingecko",
            )
        )
    return rows


def parse_defillama(payload: Any) -> list[NarrativeRow]:
    """Parse a DefiLlama ``/categories`` payload into rows. Pure, offline.

    DefiLlama returns a mapping of category name -> details containing TVL and
    percentage change fields. Field naming has varied over time, so we probe a
    few known spellings and fall back to ``None`` when absent.
    """
    if not isinstance(payload, dict):
        raise NarrativeError("DefiLlama payload must be a mapping of categories")
    rows: list[NarrativeRow] = []
    for raw_name, raw_details in payload.items():
        name = str(raw_name).strip()
        if not name:
            continue
        details = raw_details if isinstance(raw_details, dict) else {}
        change_24h = _coerce_float(
            details.get("change_1d") if "change_1d" in details else details.get("change24h")
        )
        change_7d = _coerce_float(
            details.get("change_7d") if "change_7d" in details else details.get("change7d")
        )
        tvl = _coerce_float(details.get("tvl") if "tvl" in details else details.get("totalTvl"))
        rows.append(
            NarrativeRow(
                name=name,
                change_24h=change_24h,
                change_7d=change_7d,
                market_cap_usd=tvl,
                source="defillama",
            )
        )
    return rows


def _sort_key(row: NarrativeRow) -> tuple[float, float, str]:
    # Prefer 24h momentum; break ties with 7d; rows missing both sink to the
    # bottom but stay in stable name order so output is deterministic.
    primary = row.change_24h if row.change_24h is not None else float("-inf")
    secondary = row.change_7d if row.change_7d is not None else float("-inf")
    return (primary, secondary, row.name)


def rank_narratives(rows: list[NarrativeRow], top: int = 15) -> list[NarrativeRow]:
    """Rank category rows by momentum, highest first. Pure, deterministic."""
    if top <= 0:
        return []
    ranked = sorted(rows, key=_sort_key, reverse=True)
    return ranked[:top]


def _http_get_json(url: str, timeout: float) -> Any:
    """Fetch JSON over HTTPS with stdlib urllib. The opt-in network boundary."""
    from urllib.error import HTTPError, URLError
    from urllib.request import Request, urlopen

    request = Request(url, headers={"User-Agent": _USER_AGENT, "Accept": "application/json"})
    try:
        with urlopen(request, timeout=timeout) as response:  # noqa: S310 (https only, no user input)
            charset = response.headers.get_content_charset() or "utf-8"
            body = response.read().decode(charset, errors="replace")
    except HTTPError as exc:  # pragma: no cover - network path
        raise NarrativeError(f"Source returned HTTP {exc.code} for {url}") from exc
    except (URLError, TimeoutError, OSError) as exc:  # pragma: no cover - network path
        raise NarrativeError(
            "Could not reach the narrative source. You may be offline, or the "
            f"public endpoint is down: {url}"
        ) from exc
    try:
        return json.loads(body)
    except json.JSONDecodeError as exc:  # pragma: no cover - network path
        raise NarrativeError(f"Source did not return valid JSON: {url}") from exc


def fetch_narratives(
    source: str = "coingecko",
    top: int = 15,
    timeout: float = DEFAULT_TIMEOUT_SECONDS,
) -> list[NarrativeRow]:
    """Fetch and rank live category momentum from a public source.

    This is the opt-in network entry point. Raises ``NarrativeError`` with a
    clear message when offline or the source is unreachable.
    """
    if source not in SOURCES:
        allowed = ", ".join(SOURCES)
        raise NarrativeError(f"Unknown source '{source}'. Use one of: {allowed}")
    url = COINGECKO_CATEGORIES_URL if source == "coingecko" else DEFILLAMA_CATEGORIES_URL
    payload = _http_get_json(url, timeout=timeout)
    rows = parse_coingecko(payload) if source == "coingecko" else parse_defillama(payload)
    return rank_narratives(rows, top=top)


def _fmt_pct(value: float | None) -> str:
    return "n/a" if value is None else f"{value:+.2f}%"


def _fmt_usd(value: float | None) -> str:
    if value is None:
        return "n/a"
    for unit, scale in (("T", 1e12), ("B", 1e9), ("M", 1e6), ("K", 1e3)):
        if abs(value) >= scale:
            return f"${value / scale:.2f}{unit}"
    return f"${value:.0f}"


def format_table(rows: list[NarrativeRow], source: str) -> str:
    """Render ranked rows as a plain-text table. Pure, offline."""
    size_header = "MarketCap" if source == "coingecko" else "TVL"
    lines = [
        f"Hot narratives by momentum (source: {source})",
        "",
        f"{'#':>2}  {'Category':<28} {'24h':>9} {'7d':>9} {size_header:>11}",
        f"{'--':>2}  {'-' * 28} {'-' * 9} {'-' * 9} {'-' * 11}",
    ]
    for index, row in enumerate(rows, start=1):
        lines.append(
            f"{index:>2}  {row.name[:28]:<28} "
            f"{_fmt_pct(row.change_24h):>9} {_fmt_pct(row.change_7d):>9} "
            f"{_fmt_usd(row.market_cap_usd):>11}"
        )
    if not rows:
        lines.append("(no categories returned)")
    lines.append("")
    lines.append(
        "Momentum is not a buy signal. Use it to pick which narratives to "
        "research with the four-layer framework, not to chase green numbers."
    )
    return "\n".join(lines) + "\n"
