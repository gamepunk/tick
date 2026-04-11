"""
数据格式化工具 - 统一输出字段格式
"""
import pandas as pd
from typing import Optional
from tick.core.models import Symbol


def standardize_dataframe(
    df: pd.DataFrame,
    symbol: Symbol,
    adjust: Optional[str] = None
) -> pd.DataFrame:
    """
    标准化数据框格式
    
    统一输出字段: date, code, open, high, low, close, volume, pct_change
    
    Args:
        df: 原始数据
        symbol: 品种信息
        adjust: 复权方式
        
    Returns:
        标准化后的数据框
    """
    if df is None or df.empty:
        return df
    
    # 复制数据避免修改原始数据
    result = df.copy()
    
    # 确保索引是日期
    if not isinstance(result.index, pd.DatetimeIndex):
        if 'date' in result.columns:
            result['date'] = pd.to_datetime(result['date'])
            result = result.set_index('date')
        elif '时间' in result.columns:
            result['date'] = pd.to_datetime(result['时间'])
            result = result.set_index('date')
    
    # 标准化列名（小写）
    result.columns = result.columns.str.lower()
    
    # 统一列名映射
    column_mapping = {
        # 中文列名
        '开盘': 'open',
        '最高': 'high',
        '最低': 'low',
        '收盘': 'close',
        '成交量': 'volume',
        '成交额': 'amount',
        '涨跌幅': 'pct_change',
        # 可能的英文变体
        'adj close': 'close',
        'adj_close': 'close',
    }
    
    result = result.rename(columns=column_mapping)
    
    # 确保必要的列存在
    required_cols = ['open', 'high', 'low', 'close', 'volume']
    for col in required_cols:
        if col not in result.columns:
            result[col] = None
    
    # 计算涨跌幅（如果没有）
    if 'pct_change' not in result.columns:
        result['pct_change'] = result['close'].pct_change() * 100
    
    # 添加 code 列
    result['code'] = symbol.normalized
    
    # 添加 adjust 列（记录复权方式）
    if adjust:
        result['adjust'] = adjust
    
    # 重置索引使 date 成为列
    result = result.reset_index()
    
    # 统一列名 date
    if 'index' in result.columns:
        result = result.rename(columns={'index': 'date'})
    elif 'timestamp' in result.columns:
        result = result.rename(columns={'timestamp': 'date'})
    
    # 确保 date 列格式统一
    result['date'] = pd.to_datetime(result['date'])
    
    # 选择标准字段（按固定顺序）
    standard_cols = ['date', 'code', 'open', 'high', 'low', 'close', 'volume']
    
    # 可选字段
    optional_cols = ['pct_change', 'amount', 'adjust']
    for col in optional_cols:
        if col in result.columns:
            standard_cols.append(col)
    
    # 只保留标准字段
    result = result[[col for col in standard_cols if col in result.columns]]
    
    # 按日期排序
    result = result.sort_values('date')
    
    return result


def format_for_output(
    df: pd.DataFrame,
    fmt: str = "csv",
    include_index: bool = False
) -> str | bytes:
    """
    格式化数据为输出格式
    
    Args:
        df: 数据框
        fmt: 输出格式 (csv, json, parquet)
        include_index: 是否包含索引
        
    Returns:
        格式化后的数据
    """
    if fmt == "csv":
        return df.to_csv(index=include_index)
    elif fmt == "json":
        # 统一 JSON 格式为 records 格式，便于阅读
        return df.to_json(orient="records", date_format="iso")
    elif fmt == "parquet":
        import io
        buffer = io.BytesIO()
        df.to_parquet(buffer, index=include_index)
        return buffer.getvalue()
    else:
        raise ValueError(f"不支持的格式: {fmt}")


def validate_dataframe(df: pd.DataFrame) -> tuple[bool, str]:
    """
    验证数据框是否符合标准格式
    
    Returns:
        (是否有效, 错误信息)
    """
    if df is None or df.empty:
        return False, "数据为空"
    
    required_cols = ['date', 'code', 'open', 'high', 'low', 'close']
    missing_cols = [col for col in required_cols if col not in df.columns]
    
    if missing_cols:
        return False, f"缺少必要列: {missing_cols}"
    
    # 检查是否有 NaN 值
    if df[required_cols].isna().all().any():
        return False, "必要列包含全部 NaN 值"
    
    return True, ""
