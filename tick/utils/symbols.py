"""
品种代码处理工具
"""
from typing import Optional, List, Dict, Any
from tick.core.models import Symbol, AssetType, US_INDEX_CODES


def normalize_symbol(raw: str, asset_type: Optional[str] = None) -> str:
    """
    标准化品种代码
    
    - 当 asset_type 为 index 时，为美股指数自动添加 ^ 前缀
    - 其他情况保持原样
    """
    if not asset_type or asset_type.lower() != "index":
        return raw.strip()
    
    s = raw.upper().strip()
    
    # 如果已经是 ^ 开头，或者是 A 股指数格式，保持不变
    if s.startswith("^") or s.startswith(("SH", "SZ", "BJ")):
        return raw.strip()
    
    # 为已知的美股指数代码添加 ^ 前缀
    if s in US_INDEX_CODES:
        return f"^{s}"
    
    # 其他情况保持原样
    return raw.strip()


def create_symbol(raw: str, asset_type: Optional[str] = None) -> Symbol:
    """创建 Symbol 对象"""
    normalized = normalize_symbol(raw, asset_type)
    
    at = None
    if asset_type:
        try:
            at = AssetType(asset_type.lower())
        except ValueError:
            pass
    
    return Symbol(
        raw=raw.strip(),
        normalized=normalized,
        asset_type=at
    )


def parse_asset_types(symbols: tuple[str, ...], assets: tuple[str, ...]) -> Dict[str, str]:
    """
    解析 asset 参数与 symbol 的映射关系
    
    Args:
        symbols: 品种代码列表
        assets: 资产类型列表（可为空或单个或多个）
    
    Returns:
        symbol -> asset_type 的映射字典
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


def detect_asset_type(symbol: str, source: str) -> str:
    """检测资产类型"""
    s = symbol.upper()
    
    # 指数识别
    if s.startswith("^"):
        return "index"
    
    # A股指数识别
    if s.startswith(("SH", "SZ")):
        code = s[2:] if len(s) > 2 else s
        if code.startswith(("000", "399")) and len(code) == 6:
            return "index"
    
    # 北交所指数识别
    if s.startswith("BJ"):
        code = s[2:] if len(s) > 2 else s
        if code.startswith("899") and len(code) == 6:
            return "index"
    
    # 加密货币
    if "-USD" in s or "-USDT" in s:
        return "crypto"
    
    # 期货
    if "=F" in s:
        return "futures"
    
    # ETF/Fund
    if s in ("SPY", "QQQ", "GLD", "DIA"):
        return "fund"
    
    if s.startswith(("SH", "SZ")):
        code = s[2:] if len(s) > 2 else s
        if code.startswith(("51", "15", "16", "50", "58")) and len(code) == 6:
            return "fund"
    
    # 默认股票
    return "stock"


def format_asset_summary(symbol_assets: Dict[str, Optional[str]]) -> str:
    """格式化资产类型分布摘要"""
    from tick.core.models import ASSET_TYPE_NAMES
    
    type_counts: Dict[str, int] = {}
    for asset in symbol_assets.values():
        key = asset if asset else "auto"
        type_counts[key] = type_counts.get(key, 0) + 1
    
    parts = []
    for key, count in type_counts.items():
        if key == "auto":
            parts.append(f"自动识别 ({count}个)")
        else:
            name = ASSET_TYPE_NAMES.get(AssetType(key), key)
            parts.append(f"{name} ({count}个)")
    
    return ", ".join(parts)
