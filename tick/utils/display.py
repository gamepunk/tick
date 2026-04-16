"""
显示工具 - Rich 控制台输出
"""

from typing import Any, Dict, List, Optional

import pandas as pd
from rich.console import Console
from rich.panel import Panel
from rich.progress import BarColumn, Progress, SpinnerColumn, TextColumn
from rich.table import Table

# 全局控制台
console = Console()


def get_console() -> Console:
    """获取全局控制台实例"""
    return console


def print_success(message: str):
    """打印成功消息"""
    console.print(f"[green]✅ {message}[/]")


def print_error(message: str):
    """打印错误消息"""
    console.print(f"[red]❌ {message}[/]")


def print_warning(message: str):
    """打印警告消息"""
    console.print(f"[yellow]⚠️ {message}[/]")


def print_info(message: str):
    """打印信息消息"""
    console.print(f"[dim]{message}[/]")


def print_panel(content: str, title: Optional[str] = None, style: str = "cyan"):
    """打印面板"""
    console.print(
        Panel(content, title=f"[bold]{title}[/]" if title else None, border_style=style)
    )


def create_progress_bar(description: str = "Processing..."):
    """创建进度条"""
    return Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        transient=True,
    )


def print_data_summary(df: pd.DataFrame, symbol: str, source: Optional[str] = None):
    """打印数据摘要表格"""
    if df is None or df.empty or "close" not in df.columns:
        return

    first_close = df["close"].iloc[0]
    last_close = df["close"].iloc[-1]
    max_close = df["close"].max()
    min_close = df["close"].min()
    total_pct = (last_close - first_close) / first_close * 100

    title = f"[bold cyan]{symbol}[/] 数据摘要"
    if source:
        title += f" ([dim]{source}[/])"
    table = Table(title=title, border_style="blue")
    table.add_column("指标", style="dim")
    table.add_column("数值", justify="right")

    table.add_row("数据行数", str(len(df)))
    if "date" in df.columns:
        table.add_row("起始日期", str(df["date"].iloc[0])[:10])
        table.add_row("结束日期", str(df["date"].iloc[-1])[:10])
    else:
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


def print_batch_results(results: List[Dict[str, Any]]):
    """打印批量下载结果"""
    table = Table(title="批量下载结果", border_style="blue")
    table.add_column("Symbol")
    table.add_column("行数", justify="right")
    table.add_column("文件 / 错误信息")
    table.add_column("状态", justify="center")

    for r in results:
        symbol = r.get("symbol", "")
        rows = r.get("rows", 0)
        info = r.get("info", "")
        status = r.get("status", "❌")

        color = "green" if status == "✅" else "red"
        table.add_row(symbol, str(rows) if rows else "-", info, f"[{color}]{status}[/]")

    console.print(table)


def print_symbol_table(symbols: List[Dict[str, str]], title: str = "品种列表"):
    """打印品种列表"""
    table = Table(title=title, border_style="blue")
    table.add_column("Symbol", style="cyan")
    table.add_column("名称")
    table.add_column("类型")
    table.add_column("市场")

    for s in symbols:
        table.add_row(
            s.get("symbol", ""),
            s.get("name", ""),
            s.get("type", ""),
            s.get("market", ""),
        )

    console.print(table)
