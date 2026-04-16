"""
交互式搜索工具
"""
from typing import List, Dict, Optional
from prompt_toolkit import prompt
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.shortcuts import checkboxlist_dialog, radiolist_dialog
from rich.console import Console
from tick.datasources.base import DataSourceRegistry

console = Console()


def search_symbol(query: str) -> List[Dict[str, str]]:
    """
    跨数据源搜索品种
    
    Args:
        query: 搜索关键词（支持中文/英文/代码）
        
    Returns:
        搜索结果列表
    """
    results = []
    
    # 从各数据源搜索
    for source_name in DataSourceRegistry.list_sources():
        source = DataSourceRegistry.create(source_name)
        if source:
            try:
                source_results = source.search(query, limit=10)
                for r in source_results:
                    r["source"] = source_name
                results.extend(source_results)
            except Exception:
                pass
    
    return results


def interactive_search() -> Optional[str]:
    """
    交互式搜索并选择品种
    
    Returns:
        选中的 symbol 或 None
    """
    console.print("[dim]输入关键词搜索（支持中文名称、拼音首字母、代码）[/]")
    
    try:
        query = prompt(
            "搜索: ",
            completer=WordCompleter([
                "茅台", "五粮液", "茅台", "AAPL", "BTC", "黄金", "标普500"
            ])
        )
    except ImportError:
        # 如果没有 prompt_toolkit，使用简单输入
        query = input("搜索: ")
    
    if not query.strip():
        return None
    
    # 搜索
    console.print("[dim]搜索中...[/]")
    results = search_symbol(query)
    
    if not results:
        console.print("[yellow]未找到匹配结果[/]")
        return None
    
    # 使用 radiolist 选择
    choices = [
        (i, f"{r['symbol']:12} {r['name']:20} ({r.get('source', 'unknown')})")
        for i, r in enumerate(results)
    ]
    
    try:
        selected = radiolist_dialog(
            title="选择品种",
            text="找到以下结果：",
            values=choices
        ).run()
        
        if selected is not None:
            return results[selected]["symbol"]
    except Exception:
        # 降级到简单选择
        console.print("\n[dim]找到以下结果：[/]")
        for i, r in enumerate(results[:10], 1):
            console.print(f"  {i}. {r['symbol']:12} {r['name']:20}")
        
        try:
            idx = int(input("\n选择编号 (0 取消): ")) - 1
            if 0 <= idx < len(results):
                return results[idx]["symbol"]
        except ValueError:
            pass
    
    return None


def multi_select_symbols() -> List[str]:
    """
    多选品种
    
    Returns:
        选中的 symbol 列表
    """
    # 预定义一些常用品种
    common_symbols = [
        ("AAPL", "苹果 (AAPL)"),
        ("TSLA", "特斯拉 (TSLA)"),
        ("BTC-USD", "比特币 (BTC-USD)"),
        ("ETH-USD", "以太坊 (ETH-USD)"),
        ("sh600519", "贵州茅台"),
        ("sz399006", "创业板指"),
        ("GSPC", "标普500"),
        ("DJI", "道琼斯"),
    ]
    
    try:
        selected = checkboxlist_dialog(
            title="选择品种",
            text="选择要下载的品种（可多选）：",
            values=common_symbols
        ).run()
        
        return list(selected) if selected else []
    except Exception:
        # 降级处理
        console.print("\n[dim]常用品种：[/]")
        for i, (sym, name) in enumerate(common_symbols, 1):
            console.print(f"  {i}. {name}")
        
        console.print("\n[dim]输入编号（逗号分隔，如：1,3,5）或 symbol：[/]")
        user_input = input("> ").strip()
        
        results = []
        for part in user_input.split(","):
            part = part.strip()
            if part.isdigit():
                idx = int(part) - 1
                if 0 <= idx < len(common_symbols):
                    results.append(common_symbols[idx][0])
            else:
                results.append(part.upper())
        
        return results


def confirm_dialog(message: str, default: bool = True) -> bool:
    """确认对话框"""
    try:
        from prompt_toolkit.shortcuts import yes_no_dialog
        return yes_no_dialog(title="确认", text=message).run()
    except Exception:
        # 降级到简单输入
        default_str = "Y/n" if default else "y/N"
        result = input(f"{message} [{default_str}]: ").strip().lower()
        if not result:
            return default
        return result in ("y", "yes")
