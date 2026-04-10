"""
文件名生成工具
"""
from typing import Optional


def build_filename(
    symbol: str,
    start: str,
    end: str,
    interval: str,
    adjust: str,
    src: str,
    fmt: str,
    exchange: Optional[str] = None,
    asset_type: Optional[str] = None,
) -> str:
    """构建输出文件名"""
    safe = symbol.replace("=", "").replace("/", "-").replace(":", "")
    start_s = start.replace("-", "")
    end_s = end.replace("-", "")
    
    src_tag = {
        "yfinance": "yf",
        "akshare": "ak",
        "ccxt": "ccxt",
    }.get(src, src)
    
    # ccxt 附加交易所名
    if src == "ccxt" and exchange:
        src_tag = f"ccxt_{exchange}"
    
    parts = [safe, start_s, end_s, interval, src_tag]
    
    if src == "akshare":
        parts.append(adjust if adjust else "raw")
    
    # 指数添加 idx 标识
    if asset_type == "index":
        parts.append("idx")
    
    return f"{'_'.join(parts)}.{fmt}"
