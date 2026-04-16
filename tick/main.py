#!/usr/bin/env python3
"""
tick v0.2.0 - 行情数据下载工具
"""

import sys
from pathlib import Path

# 确保可以导入 tick 包
sys.path.insert(0, str(Path(__file__).parent.parent))

from datetime import datetime, timedelta

import click

from tick.core.config import get_config, init_config
from tick.core.models import AssetType, FetchConfig, Interval
from tick.datasources.base import DataSourceRegistry
from tick.datasources.router import DataSourceRouter
from tick.utils.cache import get_cache
from tick.utils.display import (
    console,
    create_progress_bar,
    print_batch_results,
    print_data_summary,
    print_error,
    print_panel,
    print_success,
)
from tick.utils.indicators import apply_indicators
from tick.utils.interactive import interactive_search
from tick.utils.symbols import create_symbol

# 版本号
VERSION = "0.2.0"


@click.group(invoke_without_command=True)
@click.version_option(VERSION, prog_name="tick")
@click.option("--config", "-c", help="配置文件路径")
@click.option("--verbose", "-v", is_flag=True, help="详细输出")
@click.pass_context
def cli(ctx, config, verbose):
    """
    tick — 行情数据下载工具

    支持国内外股票、基金、期货、加密货币、指数数据获取
    """
    ctx.ensure_object(dict)
    ctx.obj["verbose"] = verbose

    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())
        return

    # 初始化配置
    if config:
        from tick.core.config import AppConfig

        cfg = AppConfig.load(config)
        from tick.core.config import set_config

        set_config(cfg)
    else:
        init_config()


@cli.command("web")
def cmd_web():
    """启动 Web UI"""
    from web.run import run_web

    raise SystemExit(run_web())


@cli.command("fetch")
@click.argument("symbol")
@click.option("-s", "--start", help="开始日期 YYYY-MM-DD")
@click.option("-e", "--end", help="结束日期 YYYY-MM-DD")
@click.option(
    "-i",
    "--interval",
    default="1d",
    type=click.Choice([i.value for i in Interval]),
    help="K线周期",
)
@click.option("-o", "--output", help="输出文件路径")
@click.option(
    "-f",
    "--format",
    "fmt",
    default="csv",
    type=click.Choice(["csv", "json", "parquet"]),
    help="输出格式",
)
@click.option("--asset", type=click.Choice(AssetType.choices()), help="资产类型")
@click.option(
    "--exchange",
    default="binance",
    type=click.Choice(["binance", "okx", "bybit", "kraken", "bitstamp"]),
    help="加密货币交易所",
)
@click.option(
    "--adjust",
    default="qfq",
    type=click.Choice(["qfq", "hfq", ""]),
    help="复权方式（仅A股）",
)
@click.option(
    "--indicator",
    multiple=True,
    help="添加技术指标（ma/boll/rsi/macd/kdj/atr/obv/all）",
)
@click.option("--show", is_flag=True, help="打印数据摘要")
@click.option("--no-cache", is_flag=True, help="不使用缓存")
@click.option(
    "--source",
    type=click.Choice(["yfinance", "akshare", "ccxt"]),
    help="指定数据源（覆盖自动检测）",
)
@click.pass_context
def cmd_fetch(
    ctx,
    symbol,
    start,
    end,
    interval,
    output,
    fmt,
    asset,
    exchange,
    adjust,
    indicator,
    show,
    no_cache,
    source,
):
    """下载单个品种数据"""

    # 处理日期默认值
    if not end:
        end = datetime.today().strftime("%Y-%m-%d")
    if not start:
        start = (datetime.today() - timedelta(days=365)).strftime("%Y-%m-%d")

    # 创建 symbol
    sym = create_symbol(symbol, asset)

    # 显示信息
    if source:
        source_name = source
    else:
        source_name = DataSourceRouter.detect_market(sym)
    display_info = f"[bold]Symbol:[/] {sym.raw}"
    if sym.raw != sym.normalized:
        display_info += f" → {sym.normalized}"
    display_info += f"\n[bold]数据源:[/] {source_name}"
    if asset:
        display_info += f"\n[bold]资产类型:[/] {asset}"

    print_panel(display_info, title="tick fetch", style="cyan")

    # 检查缓存
    cache = get_cache()
    if not no_cache:
        cached_df = cache.get(sym.normalized, start, end, interval, source_name)
        if cached_df is not None:
            console.print("[dim]💾 使用缓存数据[/]")
            df = cached_df
        else:
            df = None
    else:
        df = None

    # 获取数据
    if df is None:
        config = FetchConfig(
            symbol=sym,
            start=start,
            end=end,
            interval=Interval(interval),
            exchange=exchange,
            adjust=adjust,
        )

        datasource = DataSourceRegistry.create(source_name)
        if not datasource:
            print_error(f"无法找到数据源: {source_name}")
            sys.exit(1)

        with create_progress_bar() as progress:
            progress.add_task("下载数据...", total=None)
            result = datasource.fetch(config)

        if not result.success:
            print_error(result.error_message or "未知错误")
            sys.exit(1)

        df = result.data
        assert df is not None, "数据获取成功但 data 为空"

        # 缓存数据
        if not no_cache:
            cache.set(sym.normalized, start, end, interval, df, source=source_name)

    # 标准化数据格式
    from tick.utils.data_formatter import format_for_output, standardize_dataframe

    df = standardize_dataframe(df, sym, adjust)

    # 添加技术指标（在标准化后）
    if indicator:
        df = apply_indicators(df, list(indicator))

    # 保存数据
    if not output:
        from tick.utils.filename import build_filename

        filename = build_filename(
            sym.normalized,
            start,
            end,
            interval,
            adjust,
            source_name,
            fmt,
            exchange if source_name == "ccxt" else None,
            asset,
        )
        output = str(get_config().get_output_dir() / filename)

    Path(output).parent.mkdir(parents=True, exist_ok=True)

    # 统一输出格式
    output_data = format_for_output(df, fmt)

    if fmt == "parquet":
        assert isinstance(output_data, bytes)
        with open(output, "wb") as f:
            f.write(output_data)
    else:
        assert isinstance(output_data, str)
        with open(output, "w", encoding="utf-8") as f:
            f.write(output_data)

    print_success(f"已保存 {len(df)} 行 → {output}")

    if show:
        print_data_summary(df, sym.normalized)


@cli.command("batch")
@click.argument("symbols", nargs=-1, required=True)
@click.option("-s", "--start", help="开始日期")
@click.option("-e", "--end", help="结束日期")
@click.option("-d", "--dir", "outdir", help="输出目录")
@click.option(
    "-i", "--interval", default="1d", type=click.Choice([i.value for i in Interval])
)
@click.option(
    "-f",
    "--format",
    "fmt",
    default="csv",
    type=click.Choice(["csv", "json", "parquet"]),
)
@click.option(
    "--asset",
    multiple=True,
    type=click.Choice(AssetType.choices()),
    help="资产类型（可多次使用）",
)
@click.option(
    "--exchange",
    default="binance",
    type=click.Choice(["binance", "okx", "bybit", "kraken", "bitstamp"]),
)
@click.option("--adjust", default="qfq", type=click.Choice(["qfq", "hfq", ""]))
def cmd_batch(symbols, start, end, outdir, interval, fmt, asset, exchange, adjust):
    """批量下载多个品种"""

    from tick.utils.symbols import parse_asset_types

    # 处理日期
    if not end:
        end = datetime.today().strftime("%Y-%m-%d")
    if not start:
        start = (datetime.today() - timedelta(days=365)).strftime("%Y-%m-%d")

    # 解析 asset
    symbol_assets = parse_asset_types(symbols, asset)

    # 创建输出目录
    if not outdir:
        outdir = get_config().get_output_dir()
    Path(outdir).mkdir(parents=True, exist_ok=True)

    # 准备配置
    configs = []
    for raw_sym in symbols:
        asset_type = symbol_assets.get(raw_sym)
        sym = create_symbol(raw_sym, asset_type)
        config = FetchConfig(
            symbol=sym,
            start=start,
            end=end,
            interval=Interval(interval),
            exchange=exchange,
            adjust=adjust,
        )
        configs.append(config)

    console.print(f"[dim]批量下载 {len(configs)} 个品种[/]")

    results = []

    def fetch_single(config: FetchConfig):
        datasource = DataSourceRouter.get_datasource(config.symbol)
        if not datasource:
            return {
                "symbol": config.symbol.raw,
                "rows": 0,
                "info": "无法找到数据源",
                "status": "❌",
            }

        result = datasource.fetch(config)

        if result.success:
            # 保存文件
            from tick.utils.filename import build_filename

            source_name = DataSourceRouter.detect_market(config.symbol)
            filename = build_filename(
                config.symbol.normalized,
                start,
                end,
                interval,
                adjust,
                source_name,
                fmt,
                exchange if source_name == "ccxt" else None,
                config.symbol.asset_type.value if config.symbol.asset_type else None,
            )
            filepath = Path(outdir) / filename

            from tick.utils.data_formatter import (
                format_for_output,
                standardize_dataframe,
            )

            assert result.data is not None, "数据获取成功但 data 为空"
            df = standardize_dataframe(result.data, config.symbol, config.adjust)
            output_data = format_for_output(df, fmt)

            if fmt == "parquet":
                assert isinstance(output_data, bytes)
                with open(filepath, "wb") as f:
                    f.write(output_data)
            else:
                assert isinstance(output_data, str)
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(output_data)

            return {
                "symbol": config.symbol.raw,
                "rows": len(df),
                "info": str(filepath),
                "status": "✅",
            }
        else:
            return {
                "symbol": config.symbol.raw,
                "rows": 0,
                "info": result.error_message,
                "status": "❌",
            }

    with create_progress_bar() as progress:
        task = progress.add_task("下载中...", total=len(configs))
        for config in configs:
            results.append(fetch_single(config))
            progress.advance(task)

    print_batch_results(results)


@cli.command("search")
@click.argument("query", required=False)
def cmd_search(query):
    """交互式搜索品种"""
    if not query:
        result = interactive_search()
        if result:
            console.print(f"\n[green]选中: {result}[/]")
            # 询问是否下载
            if click.confirm("是否立即下载?"):
                ctx = click.get_current_context()
                ctx.invoke(cmd_fetch, symbol=result)
    else:
        from tick.utils.display import print_symbol_table
        from tick.utils.interactive import search_symbol

        with console.status("[dim]搜索中...[/]"):
            results = search_symbol(query)

        if results:
            print_symbol_table(results, title=f"搜索结果: {query}")
        else:
            console.print("[yellow]未找到匹配结果[/]")


@cli.command("config")
@click.option("--init", is_flag=True, help="初始化配置文件")
@click.option("--show", is_flag=True, help="显示当前配置")
def cmd_config(init, show):
    """配置管理"""
    from tick.core.config import AppConfig

    if init:
        init_config()
        config_path = AppConfig._get_default_config_path()
        print_success(f"配置文件已创建: {config_path}")

    if show:
        config = get_config()
        console.print(config)


if __name__ == "__main__":
    cli()
