#!/usr/bin/env python3
"""
tick — 行情数据下载命令行工具
支持：国内外股票、基金、期货、加密货币
"""

import os
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

import click
import pandas as pd
from rich.console import Console
from rich.panel import Panel
from rich.progress import BarColumn, Progress, SpinnerColumn, TextColumn
from rich.table import Table

console = Console()


def get_desktop_path() -> Path:
    """返回当前用户的桌面目录路径，支持多平台和本地化文件夹名称"""
    home = Path.home()

    desktop_names = [
        "Desktop",
        "桌面",
        "Escritorio",
        "Bureau",
        "Schreibtisch",
        "Рабочий стол",
    ]

    desktop = home / "Desktop"
    if desktop.exists() and desktop.is_dir():
        return desktop

    for name in desktop_names:
        candidate = home / name
        if candidate.exists() and candidate.is_dir():
            return candidate

    import platform

    system = platform.system()

    if system == "Windows":
        user_profile = os.environ.get("USERPROFILE")
        if user_profile:
            win_desktop = Path(user_profile) / "Desktop"
            if win_desktop.exists() and win_desktop.is_dir():
                return win_desktop

    return home


# ─────────────────────────────────────────
# 市场符号映射说明
# ─────────────────────────────────────────
SYMBOL_HELP = """
\b
【国际市场 - 通过 yfinance】
  股票:       AAPL, TSLA, 9988.HK (港股), 700.HK
  ETF:        SPY, QQQ, GLD
  期货:       GC=F (黄金), CL=F (原油), ES=F (标普500期货)
  指数:       ^GSPC (标普500), ^DJI (道琼斯), ^HSI (恒生)

【加密货币 - 通过 ccxt（无需 API Key）】
  格式:       BTC-USD, ETH-USD, SOL-USD
  默认交易所: binance（2017年起）
  深度历史:   --exchange kraken 或 --exchange bitstamp（2013/2011年起）

【中国市场 - 通过 akshare】
  A股:        sh600519 (茅台), sz000858 (五粮液)
  场内基金:   sh510300 (沪深300ETF), sz159915 (创业板ETF)
  A股指数:    sh000001 (上证指数), sz399006 (创业板指)
  沪金期货:   AU (主力), AU2506
  加密货币:   BTC (通过币安行情)
  北交所:     bj835305 (北交所股票), bj899050 (北证50指数)

【市场前缀说明】
  sh = 上交所, sz = 深交所, bj = 北交所
  不加前缀 = 自动识别（国际/加密）

【资产类型参数 --asset】
  可选类型:
    stock   - 股票 (A股/港股/美股)
    index   - 指数 (A股/港股/美股指数)
    futures - 期货 (国内期货/国际期货)
    fund    - 基金/ETF
    crypto  - 加密货币
  
  【fetch 命令】单品种指定
    # 美股指数只需输入代码，自动添加 ^ 前缀
    tick fetch GSPC --asset index -s 2024-01-01     # 实际获取 ^GSPC
    tick fetch DJI --asset index -s 2024-01-01      # 实际获取 ^DJI
    tick fetch IXIC --asset index -s 2024-01-01     # 实际获取 ^IXIC
    
    # A股指数无需转换
    tick fetch sh000001 --asset index -s 2024-01-01
  
  【batch / batch-merge 命令】批量指定
    # 统一应用（所有品种同一类型）
    tick batch GSPC DJI sh000001 --asset index -s 2024-01-01
    
    # 一一对应（按顺序匹配）
    tick batch AAPL BTC-USD sh600519 --asset stock --asset crypto --asset stock -s 2024-01-01
    
    # 混合类型批量合并
    tick batch-merge AAPL BTC-USD GSPC --asset stock --asset crypto --asset index -s 2024-01-01
    
  【支持自动转换的美股指数代码】
    GSPC (标普500), DJI (道琼斯), IXIC (纳斯达克), VIX (波动率)
    RUT (罗素2000), FTSE (富时100), N225 (日经225), HSI (恒生)
    等常见指数代码

【加密货币交易所历史深度】
  binance   : 2017-08 起
  okx       : 2017 年起
  bybit     : 2018 年起
  kraken    : 2013 年起（BTC/USD 真实美元）
  bitstamp  : 2011 年起（BTC/USD 真实美元）
"""

ASSET_TYPES = {
    "stock": "股票",
    "fund": "基金/ETF",
    "futures": "期货",
    "crypto": "加密货币",
    "index": "指数",
}

# ccxt 支持的交易所列表（公开端点，无需 API Key）
CCXT_EXCHANGES = ["binance", "okx", "bybit", "kraken", "bitstamp"]

# 各交易所使用 USD 还是 USDT
EXCHANGE_QUOTE = {
    "binance": "USDT",
    "okx": "USDT",
    "bybit": "USDT",
    "kraken": "USD",
    "bitstamp": "USD",
}

# Kraken 使用 XBT 而非 BTC
KRAKEN_SYMBOL_MAP = {
    "BTC": "XBT",
}


def detect_market(symbol: str, asset_type: str | None = None) -> str:
    """自动识别市场来源（支持 --asset 参数指定资产类型）
    
    Args:
        symbol: 品种代码
        asset_type: 可选的资产类型提示 (crypto, stock, index, futures, fund)
    """
    s = symbol.upper()
    
    # 如果指定了资产类型，优先根据类型判断
    if asset_type:
        asset = asset_type.lower()
        
        # 加密货币 → ccxt
        if asset == "crypto":
            return "ccxt"
        
        # 期货 → 根据格式判断数据源
        if asset == "futures":
            # 国内期货格式（如 AU, AG2506）
            if s in ("AU", "AG", "CU", "RB", "HC", "I", "J") or (
                any(
                    s.startswith(p)
                    for p in ("AU", "AG", "CU", "AL", "RB", "HC", "SC", "NI", "ZN", "PB")
                )
                and any(c.isdigit() for c in s)
            ):
                return "akshare_futures"
            # 国际期货（如 GC=F, CL=F）
            return "yfinance"
        
        # 股票、指数、基金 → 根据前缀判断市场
        if asset in ("stock", "index", "fund"):
            # A股/基金/指数（sh/sz/bj 开头）
            if s.startswith(("SH", "SZ", "BJ")):
                return "akshare_cn"
            # 港股或美股 → yfinance
            return "yfinance"
    
    # 自动识别逻辑（原有逻辑）
    # 修复：使用 s 而不是 symbol，支持 SH601633 / sh601633 / Sh601633 等写法
    if s.startswith(("SH", "SZ", "BJ")):
        return "akshare_cn"
    if s in ("AU", "AG", "CU", "RB", "HC", "I", "J") or (
        any(
            s.startswith(p)
            for p in ("AU", "AG", "CU", "AL", "RB", "HC", "SC", "NI", "ZN", "PB")
        )
        and any(c.isdigit() for c in s)
    ):
        return "akshare_futures"
    # 加密货币 → ccxt
    if (
        s.endswith("-USD")
        or s.endswith("-USDT")
        or s
        in ("BTC", "ETH", "SOL", "BNB", "DOGE", "XRP", "ADA", "AVAX", "DOT", "MATIC")
    ):
        return "ccxt"
    if "=F" in s:
        return "yfinance"
    if s.endswith(".HK") or s.endswith(".SS") or s.endswith(".SZ"):
        return "yfinance"
    return "yfinance"


def build_ccxt_symbol(symbol: str, exchange_id: str) -> str:
    """将 tick 格式的 symbol 转换为 ccxt 格式"""
    quote = EXCHANGE_QUOTE.get(exchange_id, "USDT")

    # 提取 base（去掉 -USD / -USDT 后缀）
    s = symbol.upper()
    if s.endswith("-USD") or s.endswith("-USDT"):
        base = s.rsplit("-", 1)[0]
    else:
        base = s

    # Kraken 特殊 symbol 映射（BTC → XBT）
    if exchange_id == "kraken":
        base = KRAKEN_SYMBOL_MAP.get(base, base)

    return f"{base}/{quote}"


def fetch_ccxt(
    symbol: str,
    start: str,
    end: str,
    interval: str,
    exchange_id: str = "binance",
) -> pd.DataFrame:
    """
    通过 ccxt 从指定交易所拉取 OHLCV 数据。
    支持 binance / okx / bybit / kraken / bitstamp，均无需 API Key。
    """
    try:
        import ccxt
    except ImportError:
        raise ImportError("请先安装 ccxt：pip install ccxt")

    interval_map = {
        "1m": "1m",
        "5m": "5m",
        "15m": "15m",
        "30m": "30m",
        "60m": "1h",
        "1d": "1d",
        "1wk": "1w",
        "1mo": "1M",
    }
    tf = interval_map.get(interval, "1d")

    if exchange_id not in dir(ccxt):
        raise ValueError(f"不支持的交易所: {exchange_id}，可选: {CCXT_EXCHANGES}")

    sym = build_ccxt_symbol(symbol, exchange_id)
    exchange = getattr(ccxt, exchange_id)({"enableRateLimit": True})

    since = exchange.parse8601(f"{start}T00:00:00Z")
    end_ts = exchange.parse8601(f"{end}T23:59:59Z")

    all_ohlcv = []
    while since < end_ts:
        ohlcv = exchange.fetch_ohlcv(sym, timeframe=tf, since=since, limit=1000)
        if not ohlcv:
            break
        all_ohlcv.extend(ohlcv)
        since = ohlcv[-1][0] + 1
        time.sleep(0.1)

    if not all_ohlcv:
        raise ValueError(
            f"ccxt ({exchange_id}) 未返回数据: {sym}，"
            f"该交易所可能不支持此币对或时间范围"
        )

    df = pd.DataFrame(
        all_ohlcv, columns=["timestamp", "open", "high", "low", "close", "volume"]
    )
    df["date"] = pd.to_datetime(df["timestamp"], unit="ms")
    df = df.set_index("date").drop(columns=["timestamp"])
    df = df[df.index <= pd.Timestamp(end)]
    return df


def fetch_yfinance(symbol: str, start: str, end: str, interval: str) -> pd.DataFrame:
    import yfinance as yf

    last_exc = None
    for attempt in range(3):
        try:
            ticker = yf.Ticker(symbol)
            df = ticker.history(start=start, end=end, interval=interval)
            if not df.empty:
                break
        except Exception as e:
            last_exc = e
            if "Too Many Requests" in str(e) or "Rate limited" in str(e):
                wait = 10 * (attempt + 1)
                console.print(
                    f"[yellow]⚠️  限流，等待 {wait}s 后重试"
                    f"（第 {attempt + 1}/3 次）...[/]"
                )
                time.sleep(wait)
            else:
                raise
    else:
        raise ValueError(
            f"yfinance 多次重试后仍限流，请使用 --exchange 指定 ccxt 数据源: {symbol}"
        ) from last_exc

    if df.empty:
        raise ValueError(f"yfinance 未返回数据，请检查 symbol: {symbol}")

    df.index = pd.to_datetime(df.index).tz_localize(None)
    df.index.name = "date"
    df.columns = df.columns.str.lower()
    return df.loc[:, ["open", "high", "low", "close", "volume"]]


def fetch_akshare_cn(
    symbol: str, start: str, end: str, adjust: str = "qfq", interval: str = "1d"
) -> pd.DataFrame:
    import akshare as ak

    raw = symbol[2:] if symbol.startswith(("sh", "sz", "bj")) else symbol
    market = symbol[:2] if symbol.startswith(("sh", "sz", "bj")) else "sh"

    INTRADAY_MAP = {"1m": "1", "5m": "5", "15m": "15", "30m": "30", "60m": "60"}
    if interval in INTRADAY_MAP:
        period_str = INTRADAY_MAP[interval]
        start_dt = f"{start} 09:30:00"
        end_dt = f"{end} 15:00:00"
        df = ak.stock_zh_a_hist_min_em(
            symbol=raw,
            start_date=start_dt,
            end_date=end_dt,
            period=period_str,
            adjust=adjust,
        )
        if df.empty:
            raise ValueError(f"akshare 分时未返回数据: {symbol} ({interval})")

        col_map = {
            "时间": "date",
            "开盘": "open",
            "最高": "high",
            "最低": "low",
            "收盘": "close",
            "成交量": "volume",
            "涨跌幅": "pct_change",
        }
        df = df.rename(columns={k: v for k, v in col_map.items() if k in df.columns})
        df["date"] = pd.to_datetime(df["date"])
        df = df.set_index("date")

        # ── 手动过滤日期，防止 akshare 忽略 start_date/end_date 参数 ──
        df = df[df.index >= pd.Timestamp(start)]
        df = df[df.index <= pd.Timestamp(end)]

        return df

    start_fmt = start.replace("-", "")
    end_fmt = end.replace("-", "")

    try:
        df = ak.stock_zh_a_hist(
            symbol=raw,
            period="daily",
            start_date=start_fmt,
            end_date=end_fmt,
            adjust=adjust,
        )
    except Exception:
        df = ak.fund_etf_hist_sina(symbol=f"{market}{raw}")

    if df.empty:
        raise ValueError(f"akshare 未返回数据: {symbol}")

    col_map = {
        "日期": "date",
        "开盘": "open",
        "最高": "high",
        "最低": "low",
        "收盘": "close",
        "成交量": "volume",
        "涨跌幅": "pct_change",
    }
    df = df.rename(columns={k: v for k, v in col_map.items() if k in df.columns})
    df["date"] = pd.to_datetime(df["date"])
    df = df.set_index("date")

    df = df[df.index >= pd.Timestamp(start)]
    df = df[df.index <= pd.Timestamp(end)]

    return df


def fetch_akshare_futures(symbol: str, start: str, end: str) -> pd.DataFrame:
    import akshare as ak

    sym_upper = symbol.upper()
    start_fmt = start.replace("-", "")
    end_fmt = end.replace("-", "")

    try:
        df = ak.futures_main_sina(
            symbol=f"{sym_upper}0", start_date=start_fmt, end_date=end_fmt
        )
    except Exception:
        df = ak.futures_zh_daily_sina(symbol=sym_upper)

    if df.empty:
        raise ValueError(f"akshare 期货未返回数据: {symbol}")

    col_map = {
        "日期": "date",
        "开盘价": "open",
        "最高价": "high",
        "最低价": "low",
        "收盘价": "close",
        "成交量": "volume",
        "date": "date",
        "open": "open",
        "high": "high",
        "low": "low",
        "close": "close",
        "volume": "volume",
    }
    df = df.rename(columns={k: v for k, v in col_map.items() if k in df.columns})
    df["date"] = pd.to_datetime(df["date"])
    df = df.set_index("date")
    return df


def add_pct_column(df: pd.DataFrame, base_price: float | None = None) -> pd.DataFrame:
    """添加相对涨跌幅列（相对首日）"""
    if "close" in df.columns:
        base = base_price or df["close"].iloc[0]
        df["cum_pct"] = ((df["close"] - base) / base * 100).round(4)
        df["pct_change"] = df["close"].pct_change().mul(100).round(4)
    return df


def print_summary(df: pd.DataFrame, symbol: str, fmt: str):
    """打印数据摘要"""
    if "close" in df.columns:
        first_close = df["close"].iloc[0]
        last_close = df["close"].iloc[-1]
        max_close = df["close"].max()
        min_close = df["close"].min()
        total_pct = (last_close - first_close) / first_close * 100

        table = Table(title=f"[bold cyan]{symbol}[/] 数据摘要", border_style="blue")
        table.add_column("指标", style="dim")
        table.add_column("数值", justify="right")

        table.add_row("数据行数", str(len(df)))
        table.add_row("起始日期", str(df.index[0])[:10])
        table.add_row("结束日期", str(df.index[-1])[:10])
        table.add_row("起始价格", f"{first_close:.4f}")
        table.add_row("最新价格", f"{last_close:.4f}")
        table.add_row("区间最高", f"{max_close:.4f}")
        table.add_row("区间最低", f"{min_close:.4f}")
        color = "green" if total_pct >= 0 else "red"
        sign = "+" if total_pct >= 0 else ""
        table.add_row("区间涨跌", f"[{color}]{sign}{total_pct:.2f}%[/]")

        console.print(table)


def build_filename(
    symbol: str,
    start: str,
    end: str,
    interval: str,
    adjust: str,
    src: str,
    fmt: str,
    exchange: str | None = None,
    asset_type: str | None = None,
) -> str:
    safe = symbol.replace("=", "").replace("/", "-").replace(":", "")
    start_s = start.replace("-", "")
    end_s = end.replace("-", "")

    src_tag = {
        "yfinance": "yf",
        "akshare_cn": "ak",
        "akshare_futures": "ak",
        "ccxt": "ccxt",
    }.get(src, src)

    # ccxt 附加交易所名
    if src == "ccxt" and exchange:
        src_tag = f"ccxt_{exchange}"

    parts = [safe, start_s, end_s, interval, src_tag]

    if src == "akshare_cn":
        parts.append(adjust if adjust else "raw")
    
    # 指数添加 idx 标识
    if asset_type == "index":
        parts.append("idx")

    return f"{'_'.join(parts)}.{fmt}"


def _do_fetch(
    symbol: str,
    start: str,
    end: str,
    interval: str,
    src: str,
    adjust: str,
    exchange: str,
) -> pd.DataFrame:
    """统一分发到各数据源，供 fetch 和 batch 命令复用"""
    if src == "ccxt":
        return fetch_ccxt(symbol, start, end, interval, exchange_id=exchange)
    elif src == "yfinance":
        return fetch_yfinance(symbol, start, end, interval)
    elif src == "akshare_cn":
        return fetch_akshare_cn(symbol, start, end, adjust=adjust, interval=interval)
    elif src == "akshare_futures":
        if interval not in ("1d", "1wk", "1mo"):
            raise ValueError("国内期货暂不支持分时数据")
        return fetch_akshare_futures(symbol, start, end)
    else:
        return fetch_yfinance(symbol, start, end, interval)


def get_asset_display_name(asset_type: str | None) -> str:
    """获取资产类型的显示名称"""
    if not asset_type:
        return "自动识别"
    return ASSET_TYPES.get(asset_type.lower(), asset_type)


# 常见美股指数代码映射（用于自动添加 ^ 前缀）
US_INDEX_CODES = {
    "GSPC", "DJI", "IXIC", "VIX", "RUT", "FTSE", "N225", "HSI",
    "NYA", "XAX", "FCHI", "GDAXI", "AEX", "IBEX", "SSMI",
    "NSEI", "KS11", "SSEC", "SZSC", "BSESN", "JKSE", "SET",
    "KLSE", "PCOMP", "TWII", "NZ50", "ASX", "ATX", "BFX",
    "OMX", "IMOEX", "RTSI", "TASI", "EGX30", "MERV", "MXX",
    "BVSP", "IPSA", "COLCAP", "IGBC", 
}


def normalize_symbol(symbol: str, asset_type: str | None = None) -> str:
    """标准化品种代码
    
    - 当 asset_type 为 index 时，为美股指数自动添加 ^ 前缀
    - 其他情况保持原样
    
    Args:
        symbol: 用户输入的品种代码
        asset_type: 资产类型提示
    
    Returns:
        标准化后的代码
    """
    if not asset_type or asset_type.lower() != "index":
        return symbol
    
    s = symbol.upper()
    
    # 如果已经是 ^ 开头，或者是 A 股指数格式，保持不变
    if s.startswith("^") or s.startswith(("SH", "SZ", "BJ")):
        return symbol
    
    # 为已知的美股指数代码添加 ^ 前缀
    if s in US_INDEX_CODES:
        return f"^{s}"
    
    # 其他情况保持原样
    return symbol


def parse_asset_types(symbols: tuple[str, ...], assets: tuple[str, ...] | None) -> dict[str, str | None]:
    """解析 asset 参数与 symbol 的映射关系
    
    Args:
        symbols: 品种代码列表
        assets: 资产类型列表（可为空或单个或多个）
    
    Returns:
        symbol -> asset_type 的映射字典
    
    规则:
        - assets 为空: 所有 symbol 返回 None（自动识别）
        - assets 有1个: 所有 symbol 使用这个类型
        - assets 有多个: 数量必须与 symbols 一致，一一对应
    """
    if not assets:
        return {s: None for s in symbols}
    
    if len(assets) == 1:
        # 单个 asset 应用于所有 symbols
        return {s: assets[0] for s in symbols}
    
    if len(assets) != len(symbols):
        raise ValueError(
            f"--asset 参数数量 ({len(assets)}) 与 symbol 数量 ({len(symbols)}) 不匹配，"
            f"请提供1个（统一应用）或 {len(symbols)} 个（一一对应）"
        )
    
    # 一一对应
    return {s: a for s, a in zip(symbols, assets)}


def format_asset_summary(symbol_assets: dict[str, str | None]) -> str:
    """格式化资产类型分布摘要"""
    type_counts: dict[str, int] = {}
    for asset in symbol_assets.values():
        key = asset if asset else "auto"
        type_counts[key] = type_counts.get(key, 0) + 1
    
    parts = []
    for key, count in type_counts.items():
        if key == "auto":
            parts.append(f"自动识别 ({count}个)")
        else:
            name = ASSET_TYPES.get(key, key)
            parts.append(f"{name} ({count}个)")
    
    return ", ".join(parts)


def fetch_display_names(symbols: list[str]) -> dict[str, str]:
    """批量获取品种的显示名称"""
    name_map: dict[str, str] = {}

    ak_symbols = [s for s in symbols if s.upper().startswith(("SH", "SZ", "BJ"))]
    if ak_symbols:
        try:
            import akshare as ak

            df_names = ak.stock_info_a_code_name()
            code_to_name: dict[str, str] = dict(
                zip(df_names["code"].astype(str), df_names["name"].astype(str))
            )
            for sym in ak_symbols:
                raw = sym[2:]
                name_map[sym] = code_to_name.get(raw, sym)
        except Exception:
            for sym in ak_symbols:
                name_map[sym] = sym

    yf_symbols = [s for s in symbols if s not in name_map]
    if yf_symbols:
        import yfinance as yf

        for sym in yf_symbols:
            try:
                info = yf.Ticker(sym).info
                display = info.get("shortName") or info.get("longName") or sym
                name_map[sym] = str(display)
            except Exception:
                name_map[sym] = sym

    return name_map


# ─────────────────────────────────────────
# CLI 定义
# ─────────────────────────────────────────


@click.group()
@click.version_option("0.1.0", prog_name="tick")
def cli():
    """
    \b
    tick — 行情数据下载工具
    支持国内外股票、基金、期货、加密货币
    """
    pass


@cli.command("fetch")
@click.argument("symbol")
@click.option("-s", "--start", default=None, help="开始日期 YYYY-MM-DD（默认1年前）")
@click.option("-e", "--end", default=None, help="结束日期 YYYY-MM-DD（默认今天）")
@click.option(
    "-i",
    "--interval",
    default="1d",
    type=click.Choice(
        ["1m", "5m", "15m", "30m", "60m", "1d", "1wk", "1mo"], case_sensitive=False
    ),
    help="K线周期",
)
@click.option(
    "-o", "--output", default=None, help="输出文件路径（默认自动命名保存到桌面）"
)
@click.option(
    "-f",
    "--format",
    "fmt",
    default="csv",
    type=click.Choice(["csv", "json", "parquet"]),
    help="输出格式",
)
@click.option("--pct/--no-pct", default=True, help="是否添加涨跌幅列")
@click.option(
    "--market",
    default=None,
    type=click.Choice(["auto", "yfinance", "akshare_cn", "akshare_futures", "ccxt"]),
    help="强制指定数据源（默认自动识别）",
)
@click.option(
    "--asset",
    default=None,
    type=click.Choice(["crypto", "stock", "index", "futures", "fund"]),
    help="指定资产类型：加密货币、股票、指数、期货、基金（帮助自动识别数据源）",
)
@click.option(
    "--exchange",
    default="binance",
    type=click.Choice(CCXT_EXCHANGES),
    show_default=True,
    help=(
        "ccxt 交易所（仅加密货币有效）。"
        "binance/okx/bybit 从 2017 年起；"
        "kraken 从 2013 年起；bitstamp 从 2011 年起"
    ),
)
@click.option("--show", is_flag=True, help="打印数据摘要")
@click.option(
    "--adjust",
    default="qfq",
    type=click.Choice(["qfq", "hfq", ""], case_sensitive=False),
    help="复权方式：qfq 前复权 / hfq 后复权 / 空字符串不复权（仅 A股有效）",
)
def cmd_fetch(
    symbol, start, end, interval, output, fmt, pct, market, asset, exchange, show, adjust
):
    """下载行情数据并保存到文件。

    \b
    示例：
      tick fetch AAPL -s 2024-01-01
      tick fetch BTC-USD -s 2016-01-01 --exchange kraken --show
      tick fetch BTC-USD -s 2018-01-01 --exchange binance --show
      tick fetch BTC-USD -s 2018-01-01 --exchange okx
      tick fetch sh600519 -s 2024-01-01 -o maotai.csv
      tick fetch GC=F -s 2025-01-01 --show
      tick fetch AU --market akshare_futures -s 2025-01-01
      tick fetch GSPC --asset index -s 2024-01-01       # 自动转为 ^GSPC
      tick fetch DJI --asset index -s 2024-01-01        # 自动转为 ^DJI
      tick fetch sh000001 --asset index -s 2024-01-01   # A股指数无需转换
    """
    today = datetime.today().strftime("%Y-%m-%d")
    one_year_ago = (datetime.today() - timedelta(days=365)).strftime("%Y-%m-%d")
    start = start or one_year_ago
    end = end or today

    # 标准化 symbol（如为指数自动添加 ^ 前缀）
    original_symbol = symbol
    symbol = normalize_symbol(symbol, asset)

    src = market if market and market != "auto" else detect_market(symbol, asset)

    # 修复：动态构建显示信息
    src_display = {
        "yfinance": "yfinance (雅虎财经)",
        "akshare_cn": "akshare (A股/基金)",
        "akshare_futures": "akshare (期货)",
        "ccxt": f"ccxt ({exchange})",
    }.get(src, src)

    # 仅当使用 ccxt 时显示交易所信息
    exchange_line = f"\n[bold]交易所:[/] [cyan]{exchange}[/]" if src == "ccxt" else ""
    
    # 资产类型显示
    asset_display = get_asset_display_name(asset)
    asset_line = f"\n[bold]资产类型:[/] [cyan]{asset_display}[/]" if asset else ""

    # 如果标准化后有变化，显示原始输入
    symbol_display = f"{original_symbol} → {symbol}" if original_symbol != symbol else symbol

    console.print(
        Panel(
            f"[bold]Symbol:[/] {symbol_display}\n"
            f"[bold]数据源:[/] {src_display}{exchange_line}{asset_line}\n"
            f"[bold]日期:[/] {start} → {end}\n"
            f"[bold]格式:[/] {fmt}",
            title="[cyan]tick fetch[/]",
            border_style="cyan",
        )
    )

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
    ) as progress:
        progress.add_task("正在下载数据...", total=None)
        try:
            df = _do_fetch(symbol, start, end, interval, src, adjust, exchange)
        except Exception as e:
            console.print(f"[red]❌ 下载失败：{e}[/]")
            sys.exit(1)

    if pct:
        df = add_pct_column(df)

    if output is None:
        filename = build_filename(
            symbol,
            start,
            end,
            interval,
            adjust,
            src,
            fmt,
            exchange if src == "ccxt" else None,
            asset,
        )
        output = str(get_desktop_path() / filename)

    Path(output).parent.mkdir(parents=True, exist_ok=True)

    if fmt == "csv":
        df.to_csv(output)
    elif fmt == "json":
        df.to_json(output, orient="index", date_format="iso", indent=2)
    elif fmt == "parquet":
        df.to_parquet(output)

    console.print(f"[green]✅ 已保存 {len(df)} 行 → {output}[/]")

    if show:
        print_summary(df, symbol, fmt)


@cli.command("batch")
@click.argument("symbols", nargs=-1, required=True)
@click.option("-s", "--start", default=None, help="开始日期 YYYY-MM-DD")
@click.option("-e", "--end", default=None, help="结束日期 YYYY-MM-DD")
@click.option("-d", "--dir", "outdir", default=None, help="输出目录（默认桌面）")
@click.option(
    "-i",
    "--interval",
    default="1d",
    type=click.Choice(
        ["1m", "5m", "15m", "30m", "60m", "1d", "1wk", "1mo"], case_sensitive=False
    ),
    help="K线周期",
)
@click.option(
    "-f",
    "--format",
    "fmt",
    default="csv",
    type=click.Choice(["csv", "json", "parquet"]),
    help="输出格式",
)
@click.option("--pct/--no-pct", default=True, help="是否添加涨跌幅列")
@click.option(
    "--adjust",
    default="qfq",
    type=click.Choice(["qfq", "hfq", ""]),
    help="复权方式（仅 A股有效）",
)
@click.option(
    "--asset",
    multiple=True,
    type=click.Choice(["crypto", "stock", "index", "futures", "fund"]),
    help="指定资产类型（可多次使用）：crypto/stock/index/futures/fund。"
         "提供1个则统一应用，提供多个需与 symbol 数量一致",
)
@click.option(
    "--exchange",
    default="binance",
    type=click.Choice(CCXT_EXCHANGES),
    show_default=True,
    help="ccxt 交易所（仅加密货币有效）",
)
def cmd_batch(symbols, start, end, outdir, interval, fmt, pct, adjust, asset, exchange):
    """批量下载多个品种。

    \b
    示例：
      tick batch AAPL TSLA -s 2024-01-01
      tick batch BTC-USD ETH-USD -s 2016-01-01 --exchange kraken
      tick batch sh600519 sh601318 GC=F -d ./data
      tick batch sh600519 sz000858 sz002594 -s 2026-03-28 -e 2026-03-28 -i 5m -d ./intraday
      tick batch GSPC DJI sh000001 --asset index -s 2024-01-01   # GSPC/DJI 自动加 ^
      tick batch AAPL BTC-USD sh600519 --asset stock --asset crypto --asset stock -s 2024-01-01
    """
    today = datetime.today().strftime("%Y-%m-%d")
    one_year_ago = (datetime.today() - timedelta(days=365)).strftime("%Y-%m-%d")
    start = start or one_year_ago
    end = end or today

    # 解析 asset 参数
    try:
        symbol_assets = parse_asset_types(symbols, asset)
    except ValueError as e:
        console.print(f"[red]❌ {e}[/]")
        sys.exit(1)

    # 标准化所有 symbols
    normalized_symbols = tuple(
        normalize_symbol(s, symbol_assets.get(s)) for s in symbols
    )
    # 创建原始 symbol 到标准化 symbol 的映射
    symbol_mapping = dict(zip(symbols, normalized_symbols))

    if outdir is None:
        outdir = str(get_desktop_path())

    Path(outdir).mkdir(parents=True, exist_ok=True)
    results = []

    # 显示资产类型分布
    asset_summary = format_asset_summary(symbol_assets)
    console.print(f"[dim]资产类型分布: {asset_summary}[/]")

    for original_symbol in symbols:
        symbol = symbol_mapping[original_symbol]
        asset_type = symbol_assets.get(original_symbol)
        src = detect_market(symbol, asset_type)
        asset_display = get_asset_display_name(asset_type)
        try:
            # 显示原始 symbol，如果标准化后有变化
            display_symbol = f"{original_symbol}→{symbol}" if original_symbol != symbol else symbol
            with console.status(
                f"下载 [cyan]{display_symbol}[/] "
                f"({asset_display}, {src}{', ' + exchange if src == 'ccxt' else ''}, {interval})..."
            ):
                df = _do_fetch(symbol, start, end, interval, src, adjust, exchange)

            if pct:
                df = add_pct_column(df)

            out = Path(outdir) / build_filename(
                symbol,
                start,
                end,
                interval,
                adjust,
                src,
                fmt,
                exchange if src == "ccxt" else None,
                asset_type,
            )

            if fmt == "csv":
                df.to_csv(out)
            elif fmt == "json":
                df.to_json(out, orient="index", date_format="iso", indent=2)
            elif fmt == "parquet":
                df.to_parquet(out)

            results.append((original_symbol, len(df), str(out), "✅"))
        except Exception as e:
            results.append((original_symbol, 0, str(e), "❌"))

    table = Table(title="批量下载结果", border_style="blue")
    table.add_column("Symbol")
    table.add_column("行数", justify="right")
    table.add_column("文件 / 错误信息")
    table.add_column("状态", justify="center")

    for sym, rows, info, status in results:
        color = "green" if status == "✅" else "red"
        table.add_row(sym, str(rows) if rows else "-", info, f"[{color}]{status}[/]")

    console.print(table)


@cli.command("info")
@click.argument("symbol")
def cmd_info(symbol):
    """查看品种基本信息（仅 yfinance 支持）。

    \b
    示例：
      tick info AAPL
      tick info GC=F
    """
    import yfinance as yf

    with console.status(f"获取 [cyan]{symbol}[/] 基本信息..."):
        try:
            t = yf.Ticker(symbol)
            info = t.info
        except Exception as e:
            console.print(f"[red]❌ {e}[/]")
            return

    fields = [
        ("名称", "longName"),
        ("类型", "quoteType"),
        ("市场", "market"),
        ("货币", "currency"),
        ("当前价", "regularMarketPrice"),
        ("52W 最高", "fiftyTwoWeekHigh"),
        ("52W 最低", "fiftyTwoWeekLow"),
        ("市值", "marketCap"),
        ("行业", "industry"),
        ("交易所", "exchange"),
    ]

    table = Table(title=f"[bold cyan]{symbol}[/] 基本信息", border_style="blue")
    table.add_column("字段", style="dim")
    table.add_column("值")

    for label, key in fields:
        val = info.get(key)
        if val is not None:
            if isinstance(val, float):
                val = f"{val:,.2f}"
            elif isinstance(val, int) and val > 1_000_000:
                val = f"{val / 1e8:.2f} 亿"
            table.add_row(label, str(val))

    console.print(table)


@cli.command("symbols")
@click.option(
    "--type",
    "asset_type",
    type=click.Choice(["stock", "fund", "futures", "crypto", "index"]),
    help="筛选资产类型",
)
def cmd_symbols(asset_type):
    """显示常用品种参考表。"""
    data = {
        "stock": [
            ("AAPL", "苹果", "yfinance", "美股"),
            ("TSLA", "特斯拉", "yfinance", "美股"),
            ("9988.HK", "阿里巴巴", "yfinance", "港股"),
            ("700.HK", "腾讯", "yfinance", "港股"),
            ("sh600519", "贵州茅台", "akshare", "A股"),
            ("sz000858", "五粮液", "akshare", "A股"),
            ("sh601318", "中国平安", "akshare", "A股"),
            ("bj835305", "北交所示例股", "akshare", "北交所"),
        ],
        "fund": [
            ("SPY", "标普500 ETF", "yfinance", "美国"),
            ("QQQ", "纳斯达克100 ETF", "yfinance", "美国"),
            ("GLD", "黄金 ETF", "yfinance", "美国"),
            ("sh510300", "沪深300 ETF", "akshare", "A股"),
            ("sz159915", "创业板 ETF", "akshare", "A股"),
            ("sh513050", "中概互联 ETF", "akshare", "A股"),
        ],
        "futures": [
            ("GC=F", "黄金期货", "yfinance", "COMEX"),
            ("CL=F", "原油期货", "yfinance", "NYMEX"),
            ("ES=F", "标普500期货", "yfinance", "CME"),
            ("AU", "沪金期货主力", "akshare", "上期所"),
            ("AG", "沪银期货主力", "akshare", "上期所"),
            ("SC", "原油期货主力", "akshare", "INE"),
        ],
        "crypto": [
            ("BTC-USD", "比特币 (Binance, 2017+)", "ccxt/binance", "全球"),
            ("BTC-USD", "比特币 (Kraken, 2013+)", "ccxt/kraken", "全球"),
            ("BTC-USD", "比特币 (Bitstamp, 2011+)", "ccxt/bitstamp", "全球"),
            ("ETH-USD", "以太坊", "ccxt/binance", "全球"),
            ("SOL-USD", "Solana", "ccxt/binance", "全球"),
            ("BNB-USD", "币安币", "ccxt/binance", "全球"),
        ],
        "index": [
            ("^GSPC", "标普500", "yfinance", "美股"),
            ("^DJI", "道琼斯工业指数", "yfinance", "美股"),
            ("^IXIC", "纳斯达克综合指数", "yfinance", "美股"),
            ("^HSI", "恒生指数", "yfinance", "港股"),
            ("sh000001", "上证指数", "akshare", "A股"),
            ("sh000300", "沪深300", "akshare", "A股"),
            ("sz399006", "创业板指", "akshare", "A股"),
            ("sz399001", "深证成指", "akshare", "A股"),
            ("bj899050", "北证50", "akshare", "北交所"),
        ],
    }

    types_to_show = [asset_type] if asset_type else list(data.keys())

    for t in types_to_show:
        table = Table(
            title=f"{ASSET_TYPES[t]}",
            border_style="blue",
            show_header=True,
        )
        table.add_column("Symbol", style="cyan")
        table.add_column("名称")
        table.add_column("数据源")
        table.add_column("市场")

        for row in data[t]:
            table.add_row(*row)

        console.print(table)
        console.print()


@cli.command("batch-merge")
@click.argument("symbols", nargs=-1, required=True)
@click.option("-s", "--start", default=None, help="开始日期 YYYY-MM-DD（默认1年前）")
@click.option("-e", "--end", default=None, help="结束日期 YYYY-MM-DD（默认今天）")
@click.option(
    "-o", "--output", default=None, help="输出文件路径（默认保存到桌面，自动命名）"
)
@click.option(
    "-f",
    "--format",
    "fmt",
    default="csv",
    type=click.Choice(["csv", "json", "parquet"]),
    help="输出格式（默认 csv）",
)
@click.option(
    "-i",
    "--interval",
    default="1d",
    type=click.Choice(
        ["1m", "5m", "15m", "30m", "60m", "1d", "1wk", "1mo"], case_sensitive=False
    ),
    help="K线周期",
)
@click.option(
    "--value-col",
    default="close",
    type=click.Choice(["close", "open", "high", "low", "volume"]),
    help="Bar Chart Race 排序依据列（默认 close 收盘价）",
)
@click.option(
    "--category-map",
    default=None,
    help="强制指定类别，格式：SYMBOL:TYPE,SYMBOL2:TYPE",
)
@click.option(
    "--adjust",
    default="qfq",
    type=click.Choice(["qfq", "hfq", ""]),
    help="复权方式（仅 A股有效，默认 qfq）",
)
@click.option(
    "--asset",
    multiple=True,
    type=click.Choice(["crypto", "stock", "index", "futures", "fund"]),
    help="指定资产类型（可多次使用）：crypto/stock/index/futures/fund。"
         "提供1个则统一应用，提供多个需与 symbol 数量一致",
)
@click.option(
    "--exchange",
    default="binance",
    type=click.Choice(CCXT_EXCHANGES),
    show_default=True,
    help="ccxt 交易所（仅加密货币有效）",
)
def cmd_batch_merge(
    symbols,
    start,
    end,
    output,
    fmt,
    interval,
    value_col,
    category_map,
    adjust,
    asset,
    exchange,
):
    """
    批量下载多个品种，合并为长格式CSV（适合 Observable Bar Chart Race）。

    \b
    示例：
      tick batch-merge AAPL BTC-USD GC=F sh510300 -s 2024-01-01
      tick batch-merge BTC-USD ETH-USD SOL-USD -s 2016-01-01 --exchange kraken
      tick batch-merge BTC-USD ETH-USD SOL-USD BNB-USD -s 2024-01-01 -o crypto_race.csv
      tick batch-merge sh600519 sz000858 sz002594 -s 2026-03-28 -e 2026-03-28 -i 5m
      tick batch-merge GSPC DJI sh000001 --asset index -s 2024-01-01   # 自动转为 ^GSPC ^DJI
      tick batch-merge AAPL BTC-USD sh600519 --asset stock --asset crypto --asset stock -s 2024-01-01
    """
    today = datetime.today().strftime("%Y-%m-%d")
    one_year_ago = (datetime.today() - timedelta(days=365)).strftime("%Y-%m-%d")
    start = start or one_year_ago
    end = end or today

    # 解析 asset 参数
    try:
        symbol_assets = parse_asset_types(symbols, asset)
    except ValueError as e:
        console.print(f"[red]❌ {e}[/]")
        sys.exit(1)

    # 标准化所有 symbols
    normalized_symbols = tuple(
        normalize_symbol(s, symbol_assets.get(s)) for s in symbols
    )
    # 创建原始 symbol 到标准化 symbol 的映射
    symbol_mapping = dict(zip(symbols, normalized_symbols))
    # 更新 symbols 为元组
    symbols = normalized_symbols

    custom_categories: dict[str, str] = {}
    if category_map:
        for mapping in category_map.split(","):
            if ":" in mapping:
                sym, cat = mapping.split(":", 1)
                custom_categories[sym.upper()] = cat.lower()

    # 修复：分析实际数据源分布（传入 asset 参数）
    src_list = [detect_market(s, symbol_assets.get(s)) for s in symbols]
    src_summary = {}
    for s in src_list:
        src_summary[s] = src_summary.get(s, 0) + 1

    has_crypto = "ccxt" in src_summary

    # 构建数据源说明
    src_descriptions = []
    for src, count in src_summary.items():
        desc = {
            "yfinance": f"雅虎财经 ({count}个)",
            "akshare_cn": f"akshare-A股 ({count}个)",
            "akshare_futures": f"akshare-期货 ({count}个)",
            "ccxt": f"ccxt-{exchange} ({count}个)",
        }.get(src, f"{src} ({count}个)")
        src_descriptions.append(desc)

    # 修复：仅在包含加密货币时显示交易所信息
    exchange_line = f"\n[bold]加密交易所:[/] [cyan]{exchange}[/]" if has_crypto else ""
    
    # 资产类型分布
    asset_summary = format_asset_summary(symbol_assets)
    asset_line = f"\n[bold]资产类型:[/] {asset_summary}" if asset_summary else ""

    console.print(
        Panel(
            f"[bold]资产数量:[/] {len(symbols)} 个\n"
            f"[bold]数据源分布:[/] {', '.join(src_descriptions)}"
            f"{exchange_line}{asset_line}\n"
            f"[bold]日期范围:[/] {start} → {end}\n"
            f"[bold]K线周期:[/] {interval}\n"
            f"[bold]排序列:[/] {value_col}\n"
            f"[bold]复权方式:[/] {adjust if adjust else '不复权'}",
            title="[cyan]tick batch-merge[/]",
            border_style="cyan",
        )
    )

    def detect_asset_type(symbol: str, src: str) -> str:
        s = symbol.upper()
        if s in custom_categories:
            cat = custom_categories[s]
            if cat in ASSET_TYPES:
                return cat
            for key, val in ASSET_TYPES.items():
                if cat == val or cat in val:
                    return key
        
        # 指数识别（美股指数以 ^ 开头）
        if s.startswith("^"):
            return "index"
        
        # A股指数识别（000/399 开头的 sh/sz 代码，或 899 开头的 bj 代码）
        if s.startswith(("SH", "SZ")):
            code = s[2:] if len(s) > 2 else s
            if code.startswith(("000", "399")) and len(code) == 6:
                return "index"
        
        # 北交所指数识别（899 开头的 bj 代码）
        if s.startswith("BJ"):
            code = s[2:] if len(s) > 2 else s
            if code.startswith("899") and len(code) == 6:
                return "index"
        
        if (
            "-USD" in s
            or "-USDT" in s
            or s in ["BTC", "ETH", "SOL", "BNB", "DOGE", "XRP", "ADA"]
        ):
            return "crypto"
        elif "=F" in s:
            return "futures"
        # 修复：同样使用大写检测，保持一致性
        elif s.startswith(("SH", "SZ", "BJ")):
            code = s[2:] if len(s) > 2 else s
            if (
                code.startswith(("51", "15", "16", "50", "58")) and len(code) == 6
            ) or "ETF" in s:
                return "fund"
            return "stock"
        elif src == "akshare_futures":
            return "futures"
        else:
            etf_keywords = ["SPY", "QQQ", "DIA", "IWM", "GLD", "USO", "TLT", "VTI"]
            if s in etf_keywords:
                return "fund"
            return "stock"

    all_frames: list[pd.DataFrame] = []
    failed_symbols: list[tuple[str, str]] = []

    console.print("[dim]正在获取品种名称...[/]")
    display_names = fetch_display_names(list(symbols))

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
    ) as progress:
        for symbol in symbols:
            asset_type = symbol_assets.get(symbol)
            src = detect_market(symbol, asset_type)
            # 优先使用传入的 asset 参数，否则自动检测
            if asset_type:
                asset_type_key = asset_type
            else:
                asset_type_key = detect_asset_type(symbol, src)
            asset_type_name = ASSET_TYPES.get(asset_type_key, asset_type_key)

            progress.add_task(f"下载 {symbol} ({asset_type_name})...", total=None)

            try:
                df = _do_fetch(symbol, start, end, interval, src, adjust, exchange)

                if df.empty or value_col not in df.columns:
                    failed_symbols.append((symbol, "无数据或缺少指定列"))
                    continue

                df = add_pct_column(df)

                is_intraday = interval in ("1m", "5m", "15m", "30m", "60m")
                dt_fmt = "%Y-%m-%d %H:%M:%S" if is_intraday else "%Y-%m-%d"

                ohlcv_cols = ["open", "high", "low", "close", "volume"]
                pct_cols = ["cum_pct", "pct_change"]
                available_cols = [c for c in ohlcv_cols + pct_cols if c in df.columns]

                temp_data: dict[str, object] = {
                    "date": pd.DatetimeIndex(df.index).strftime(dt_fmt),
                    "name": symbol,
                    "display_name": display_names.get(symbol, symbol),
                    "category": asset_type_name,
                }
                for col in available_cols:
                    temp_data[col] = df[col].astype(float)

                temp_df = pd.DataFrame(temp_data)
                all_frames.append(temp_df)

            except Exception as e:
                failed_symbols.append((symbol, str(e)))
                continue

    if not all_frames:
        console.print("[red]❌ 没有成功下载任何数据[/]")
        return

    result_df = pd.concat(all_frames, ignore_index=True)
    result_df = result_df.sort_values(["date", value_col], ascending=[True, False])

    if output is None:
        safe_start = start.replace("-", "")
        safe_end = end.replace("-", "")
        adjust_tag = adjust if adjust else "raw"
        # 修复：文件名中包含实际数据源信息，而非固定的 exchange
        src_tag = "mixed" if len(src_summary) > 1 else list(src_summary.keys())[0]
        if src_tag == "ccxt":
            filename = f"tick_merge_{safe_start}_{safe_end}_{interval}_{exchange}_{adjust_tag}.{fmt}"
        else:
            filename = f"tick_merge_{safe_start}_{safe_end}_{interval}_{src_tag}_{adjust_tag}.{fmt}"
        output = str(get_desktop_path() / filename)

    Path(output).parent.mkdir(parents=True, exist_ok=True)

    if fmt == "csv":
        result_df.to_csv(output, index=False)
    elif fmt == "json":
        result_df.to_json(output, orient="records", date_format="iso", indent=2)
    elif fmt == "parquet":
        result_df.to_parquet(output, index=False)

    category_counts = result_df.groupby("category")["name"].nunique().to_dict()

    table = Table(title="合并数据摘要", border_style="green")
    table.add_column("指标", style="dim")
    table.add_column("数值", justify="right")
    table.add_row("总数据行", f"{len(result_df)} 行")
    table.add_row("日期范围", f"{result_df['date'].min()} 至 {result_df['date'].max()}")
    table.add_row("排序列", value_col)
    # 修复：摘要中显示实际使用的数据源
    table.add_row("数据源", ", ".join(src_descriptions))
    if has_crypto:
        table.add_row("加密交易所", exchange)
    table.add_row("输出格式", fmt)
    table.add_row("输出文件", output)
    console.print(table)

    cat_table = Table(title="资产类别分布", border_style="blue")
    cat_table.add_column("类别", style="cyan")
    cat_table.add_column("品种数量", justify="right")
    for cat, count in category_counts.items():
        cat_table.add_row(cat, str(count))
    console.print(cat_table)

    if failed_symbols:
        console.print("\n[yellow]⚠️  以下品种下载失败：[/]")
        for sym, err in failed_symbols:
            console.print(f"  [red]• {sym}:[/] {err}")

    console.print("\n[dim]数据预览（前10行）：[/]")
    console.print(result_df.head(10).to_string(index=False))
    console.print(f"\n[green]✅ 已保存到：{output}[/]")


@cli.command("help-symbols")
def cmd_help_symbols():
    """显示 Symbol 格式说明。"""
    console.print(
        Panel(SYMBOL_HELP, title="[cyan]Symbol 格式说明[/]", border_style="cyan")
    )


if __name__ == "__main__":
    cli()
