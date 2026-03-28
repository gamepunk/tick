#!/usr/bin/env python3
"""
tick — 行情数据下载命令行工具
支持：国内外股票、基金、期货、加密货币
"""

import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

import click
import pandas as pd
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

console = Console()


def get_desktop_path() -> Path:
    """返回当前用户的桌面目录路径，支持多平台和本地化文件夹名称"""
    home = Path.home()

    # 尝试多种常见的桌面目录名称
    desktop_names = [
        "Desktop",
        "桌面",
        "Escritorio",
        "Bureau",
        "Schreibtisch",
        "Рабочий стол",
    ]

    # 首先检查标准英文桌面目录
    desktop = home / "Desktop"
    if desktop.exists() and desktop.is_dir():
        return desktop

    # 如果不存在，尝试其他常见本地化名称
    for name in desktop_names:
        candidate = home / name
        if candidate.exists() and candidate.is_dir():
            return candidate

    # 如果都找不到，尝试使用平台特定的环境变量
    import platform

    system = platform.system()

    if system == "Windows":
        # Windows: 使用 USERPROFILE\Desktop
        user_profile = os.environ.get("USERPROFILE")
        if user_profile:
            win_desktop = Path(user_profile) / "Desktop"
            if win_desktop.exists() and win_desktop.is_dir():
                return win_desktop

    # 最后回退到 home 目录
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
  加密货币:   BTC-USD, ETH-USD, SOL-USD

【中国市场 - 通过 akshare】
  A股:        sh600519 (茅台), sz000858 (五粮液)
  场内基金:   sh510300 (沪深300ETF), sz159915 (创业板ETF)
  沪金期货:   AU (主力), AU2506
  加密货币:   BTC (通过币安行情)

【市场前缀说明】
  sh = 上交所, sz = 深交所
  不加前缀 = 自动识别（国际/加密）
"""

ASSET_TYPES = {
    "stock": "股票",
    "fund": "基金/ETF",
    "futures": "期货",
    "crypto": "加密货币",
}


def detect_market(symbol: str) -> str:
    """自动识别市场来源"""
    s = symbol.upper()
    if symbol.startswith(("sh", "sz", "bj")):
        return "akshare_cn"
    if s in ("AU", "AG", "CU", "RB", "HC", "I", "J") or (
        any(
            s.startswith(p)
            for p in ("AU", "AG", "CU", "AL", "RB", "HC", "SC", "NI", "ZN", "PB")
        )
        and any(c.isdigit() for c in s)
    ):
        return "akshare_futures"
    if s.endswith("-USD") or s in ("BTC", "ETH", "SOL", "BNB", "DOGE"):
        return "yfinance"
    if "=F" in s:
        return "yfinance"
    if s.endswith(".HK") or s.endswith(".SS") or s.endswith(".SZ"):
        return "yfinance"
    return "yfinance"


def fetch_yfinance(symbol: str, start: str, end: str, interval: str) -> pd.DataFrame:
    import yfinance as yf

    ticker = yf.Ticker(symbol)
    df = ticker.history(start=start, end=end, interval=interval)
    if df.empty:
        raise ValueError(f"yfinance 未返回数据，请检查 symbol: {symbol}")
    df.index = pd.to_datetime(df.index).tz_localize(None)
    df.index.name = "date"

    df.columns = df.columns.str.lower()
    return df.loc[:, ["open", "high", "low", "close", "volume"]]


def fetch_akshare_cn(
    symbol: str, start: str, end: str, adjust: str = "qfq"
) -> pd.DataFrame:
    import akshare as ak

    # 处理前缀
    raw = symbol[2:] if symbol.startswith(("sh", "sz", "bj")) else symbol
    market = symbol[:2] if symbol.startswith(("sh", "sz", "bj")) else "sh"

    start_fmt = start.replace("-", "")
    end_fmt = end.replace("-", "")

    try:
        df = ak.stock_zh_a_hist(
            symbol=raw,
            period="daily",
            start_date=start_fmt,
            end_date=end_fmt,
            adjust=adjust,  # 默认前复权
        )
    except Exception:
        # fallback: ETF/基金
        df = ak.fund_etf_hist_sina(symbol=f"{market}{raw}")

    if df.empty:
        raise ValueError(f"akshare 未返回数据: {symbol}")

    # 统一列名
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
    return df


def fetch_akshare_futures(symbol: str, start: str, end: str) -> pd.DataFrame:
    import akshare as ak

    # 期货主力合约
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
    symbol: str, start: str, end: str, interval: str, adjust: str, src: str, fmt: str
) -> str:
    safe = symbol.replace("=", "").replace("/", "-").replace(":", "")
    start_s = start.replace("-", "")
    end_s = end.replace("-", "")

    # 数据源缩写
    src_tag = {"yfinance": "yf", "akshare_cn": "ak", "akshare_futures": "ak"}.get(
        src, src
    )

    parts = [safe, start_s, end_s, interval, src_tag]

    # 只有 A股才附加复权标识
    if src == "akshare_cn":
        parts.append(adjust if adjust else "raw")

    return f"{'_'.join(parts)}.{fmt}"


# ─────────────────────────────────────────
# CLI 定义
# ─────────────────────────────────────────


@click.group()
@click.version_option("0.0.1", prog_name="tick")
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
    type=click.Choice(["1d", "1wk", "1mo"], case_sensitive=False),
    help="K线周期（仅 yfinance 有效）",
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
    type=click.Choice(["auto", "yfinance", "akshare_cn", "akshare_futures"]),
    help="强制指定数据源（默认自动识别）",
)
@click.option("--show", is_flag=True, help="打印数据摘要")
@click.option(
    "--adjust",
    default="qfq",
    type=click.Choice(["qfq", "hfq", ""], case_sensitive=False),
    help="复权方式：qfq 前复权 / hfq 后复权 / 空字符串不复权（仅 A股有效）",
)
def cmd_fetch(symbol, start, end, interval, output, fmt, pct, market, show, adjust):
    """下载行情数据并保存到文件。

    \b
    示例：
      tick fetch AAPL -s 2024-01-01
      tick fetch BTC-USD -s 2025-01-01 --show
      tick fetch sh600519 -s 2024-01-01 -o maotai.csv
      tick fetch GC=F -s 2025-01-01 --show
      tick fetch AU --market akshare_futures -s 2025-01-01
    """
    # 默认日期
    today = datetime.today().strftime("%Y-%m-%d")
    one_year_ago = (datetime.today() - timedelta(days=365)).strftime("%Y-%m-%d")
    start = start or one_year_ago
    end = end or today

    # 自动识别市场
    src = market if market and market != "auto" else detect_market(symbol)

    console.print(
        Panel(
            f"[bold]Symbol:[/] {symbol}\n"
            f"[bold]数据源:[/] {src}\n"
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
            if src == "yfinance":
                df = fetch_yfinance(symbol, start, end, interval)
            elif src == "akshare_cn":
                df = fetch_akshare_cn(symbol, start, end, adjust=adjust)
            elif src == "akshare_futures":
                df = fetch_akshare_futures(symbol, start, end)
            else:
                df = fetch_yfinance(symbol, start, end, interval)
        except Exception as e:
            console.print(f"[red]❌ 下载失败：{e}[/]")
            sys.exit(1)

    if pct:
        df = add_pct_column(df)

    # 确定输出路径
    if output is None:
        filename = build_filename(symbol, start, end, interval, adjust, src, fmt)
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
def cmd_batch(symbols, start, end, outdir, fmt, pct, adjust):
    """批量下载多个品种。

    \b
    示例：
      tick batch AAPL TSLA BTC-USD -s 2024-01-01
      tick batch sh600519 sh601318 GC=F -d ./data
    """
    today = datetime.today().strftime("%Y-%m-%d")
    one_year_ago = (datetime.today() - timedelta(days=365)).strftime("%Y-%m-%d")
    start = start or one_year_ago
    end = end or today

    # 如果未指定输出目录，使用桌面
    if outdir is None:
        outdir = str(get_desktop_path())

    Path(outdir).mkdir(parents=True, exist_ok=True)
    results = []

    for symbol in symbols:
        src = detect_market(symbol)
        try:
            with console.status(f"下载 [cyan]{symbol}[/] ({src})..."):
                if src == "yfinance":
                    df = fetch_yfinance(symbol, start, end, "1d")
                elif src == "akshare_cn":
                    df = fetch_akshare_cn(symbol, start, end, adjust=adjust)
                elif src == "akshare_futures":
                    df = fetch_akshare_futures(symbol, start, end)
                else:
                    df = fetch_yfinance(symbol, start, end, "1d")

            if pct:
                df = add_pct_column(df)

            out = Path(outdir) / build_filename(
                symbol, start, end, "1d", adjust, src, fmt
            )

            if fmt == "csv":
                df.to_csv(out)
            elif fmt == "json":
                df.to_json(out, orient="index", date_format="iso", indent=2)
            elif fmt == "parquet":
                df.to_parquet(out)

            results.append((symbol, len(df), str(out), "✅"))
        except Exception as e:
            results.append((symbol, 0, str(e), "❌"))

    # 打印结果表格
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
      tick info BTC-USD
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
    type=click.Choice(["stock", "fund", "futures", "crypto"]),
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
            ("BTC-USD", "比特币", "yfinance", "全球"),
            ("ETH-USD", "以太坊", "yfinance", "全球"),
            ("SOL-USD", "Solana", "yfinance", "全球"),
            ("BNB-USD", "币安币", "yfinance", "全球"),
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


@cli.command("help-symbols")
def cmd_help_symbols():
    """显示 Symbol 格式说明。"""
    console.print(
        Panel(SYMBOL_HELP, title="[cyan]Symbol 格式说明[/]", border_style="cyan")
    )
