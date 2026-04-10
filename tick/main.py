#!/usr/bin/env python3
"""
tick v0.1.1 - 重构版行情数据下载工具
"""
import sys
from pathlib import Path

# 确保可以导入 tick 包
sys.path.insert(0, str(Path(__file__).parent.parent))

import click
from datetime import datetime, timedelta
from typing import List, Optional

from tick.core.models import AssetType, Interval, FetchConfig, Symbol
from tick.core.config import get_config, init_config
from tick.datasources.router import DataSourceRouter
from tick.datasources.base import DataSourceRegistry
from tick.utils.symbols import create_symbol
from tick.utils.display import (
    console, print_success, print_error, print_panel, 
    print_data_summary, print_batch_results, create_progress_bar
)
from tick.utils.cache import get_cache
from tick.utils.indicators import apply_indicators
from tick.utils.interactive import interactive_search, multi_select_symbols
from tick.utils.async_fetch import AsyncFetcher


# 版本号
VERSION = "0.1.1"


@click.group(invoke_without_command=True)
@click.version_option(VERSION, prog_name="tick")
@click.option('--config', '-c', help='配置文件路径')
@click.option('--verbose', '-v', is_flag=True, help='详细输出')
@click.pass_context
def cli(ctx, config, verbose):
    """
    tick — 行情数据下载工具（重构版）
    
    支持国内外股票、基金、期货、加密货币、指数数据获取
    """
    ctx.ensure_object(dict)
    ctx.obj['verbose'] = verbose

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
@click.option("-i", "--interval", default="1d", 
              type=click.Choice([i.value for i in Interval]),
              help="K线周期")
@click.option("-o", "--output", help="输出文件路径")
@click.option("-f", "--format", "fmt", default="csv",
              type=click.Choice(["csv", "json", "parquet"]),
              help="输出格式")
@click.option("--asset", type=click.Choice(AssetType.choices()),
              help="资产类型")
@click.option("--exchange", default="binance",
              type=click.Choice(["binance", "okx", "bybit", "kraken", "bitstamp"]),
              help="加密货币交易所")
@click.option("--adjust", default="qfq", type=click.Choice(["qfq", "hfq", ""]),
              help="复权方式（仅A股）")
@click.option("--indicator", multiple=True,
              help="添加技术指标（ma/boll/rsi/macd/kdj/atr/obv/all）")
@click.option("--show", is_flag=True, help="打印数据摘要")
@click.option("--no-cache", is_flag=True, help="不使用缓存")
@click.pass_context
def cmd_fetch(ctx, symbol, start, end, interval, output, fmt, asset, 
              exchange, adjust, indicator, show, no_cache):
    """下载单个品种数据"""
    
    # 处理日期默认值
    if not end:
        end = datetime.today().strftime("%Y-%m-%d")
    if not start:
        start = (datetime.today() - timedelta(days=365)).strftime("%Y-%m-%d")
    
    # 创建 symbol
    sym = create_symbol(symbol, asset)
    
    # 显示信息
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
        cached_df = cache.get(sym.normalized, start, end, interval)
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
            adjust=adjust
        )
        
        datasource = DataSourceRouter.get_datasource(sym)
        if not datasource:
            print_error(f"无法找到合适的数据源: {symbol}")
            sys.exit(1)
        
        with create_progress_bar() as progress:
            task = progress.add_task("下载数据...", total=None)
            result = datasource.fetch(config)
        
        if not result.success:
            print_error(result.error_message)
            sys.exit(1)
        
        df = result.data
        
        # 缓存数据
        if not no_cache:
            cache.set(sym.normalized, start, end, interval, df)
    
    # 添加技术指标
    if indicator:
        df = apply_indicators(df, list(indicator))
    
    # 保存数据
    if not output:
        from tick.utils.filename import build_filename
        filename = build_filename(
            sym.normalized, start, end, interval, 
            adjust, source_name, fmt, 
            exchange if source_name == "ccxt" else None,
            asset
        )
        output = str(get_config().get_output_dir() / filename)
    
    Path(output).parent.mkdir(parents=True, exist_ok=True)
    
    if fmt == "csv":
        df.to_csv(output)
    elif fmt == "json":
        df.to_json(output, orient="index", date_format="iso", indent=2)
    elif fmt == "parquet":
        df.to_parquet(output)
    
    print_success(f"已保存 {len(df)} 行 → {output}")
    
    if show:
        print_data_summary(df, sym.normalized)


@cli.command("batch")
@click.argument("symbols", nargs=-1, required=True)
@click.option("-s", "--start", help="开始日期")
@click.option("-e", "--end", help="结束日期")
@click.option("-d", "--dir", "outdir", help="输出目录")
@click.option("-i", "--interval", default="1d",
              type=click.Choice([i.value for i in Interval]))
@click.option("-f", "--format", "fmt", default="csv",
              type=click.Choice(["csv", "json", "parquet"]))
@click.option("--asset", multiple=True, type=click.Choice(AssetType.choices()),
              help="资产类型（可多次使用）")
@click.option("--workers", "-w", default=4, type=int, help="并发数")
@click.option("--exchange", default="binance",
              type=click.Choice(["binance", "okx", "bybit", "kraken", "bitstamp"]))
@click.option("--adjust", default="qfq", type=click.Choice(["qfq", "hfq", ""]))
def cmd_batch(symbols, start, end, outdir, interval, fmt, asset, workers, exchange, adjust):
    """批量下载多个品种"""
    
    from tick.utils.async_fetch import fetch_with_progress
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
            adjust=adjust
        )
        configs.append(config)
    
    console.print(f"[dim]批量下载 {len(configs)} 个品种，并发数: {workers}[/]")
    
    # 并发下载
    results = []
    
    def fetch_single(config: FetchConfig):
        datasource = DataSourceRouter.get_datasource(config.symbol)
        if not datasource:
            return {
                "symbol": config.symbol.raw,
                "rows": 0,
                "info": "无法找到数据源",
                "status": "❌"
            }
        
        result = datasource.fetch(config)
        
        if result.success:
            # 保存文件
            from tick.utils.filename import build_filename
            source_name = DataSourceRouter.detect_market(config.symbol)
            filename = build_filename(
                config.symbol.normalized, start, end, interval,
                adjust, source_name, fmt,
                exchange if source_name == "ccxt" else None,
                config.symbol.asset_type.value if config.symbol.asset_type else None
            )
            filepath = Path(outdir) / filename
            
            if fmt == "csv":
                result.data.to_csv(filepath)
            elif fmt == "json":
                result.data.to_json(filepath, orient="index", date_format="iso", indent=2)
            elif fmt == "parquet":
                result.data.to_parquet(filepath)
            
            return {
                "symbol": config.symbol.raw,
                "rows": len(result.data),
                "info": str(filepath),
                "status": "✅"
            }
        else:
            return {
                "symbol": config.symbol.raw,
                "rows": 0,
                "info": result.error_message,
                "status": "❌"
            }
    
    # 使用进度条
    with create_progress_bar() as progress:
        task = progress.add_task("下载中...", total=len(configs))
        
        def on_progress(current, total):
            progress.update(task, completed=current)
        
        # 这里简化处理，顺序下载带进度
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
        from tick.utils.interactive import search_symbol
        from tick.utils.display import print_symbol_table
        
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
