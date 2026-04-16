"""
数据格式化工具 - 统一输出字段格式
"""

import io
from typing import Optional

import pandas as pd

from tick.core.models import Symbol


def standardize_dataframe(
    df: pd.DataFrame,
    symbol: Symbol,
    adjust: Optional[str] = None,
) -> pd.DataFrame:
    """
    标准化数据框格式

    输出固定列顺序:
        date, code, open, high, low, close[, volume], cum_return, daily_return

    - cum_return  : 累积涨跌幅（%），第一天为 0，后续与第一天收盘价比较
    - daily_return: 当日涨跌幅（%），第一天为 0，后续为相邻两日收盘价变化

    Args:
        df     : 原始数据框（各数据源返回的 FetchResult.data）
        symbol : 品种信息
        adjust : 复权方式（仅用于记录，不影响计算）

    Returns:
        标准化后的数据框（date 作为普通列，无 index）
    """
    if df is None or df.empty:
        return df

    result = df.copy()

    # ─────────────────────────────────────────
    # 1. 确保索引是 DatetimeIndex，不是则尝试从列中转换
    # ─────────────────────────────────────────
    if not isinstance(result.index, pd.DatetimeIndex):
        for candidate in ("date", "时间", "timestamp", "index"):
            if candidate in result.columns:
                result[candidate] = pd.to_datetime(result[candidate])
                result = result.set_index(candidate)
                break

    # ─────────────────────────────────────────
    # 2. 统一列名（全部小写，再做映射）
    # ─────────────────────────────────────────
    result.columns = result.columns.str.lower().str.strip()

    column_mapping = {
        # 中文列名
        "开盘": "open",
        "最高": "high",
        "最低": "low",
        "收盘": "close",
        "成交量": "volume",
        "成交额": "amount",
        # 英文变体
        "adj close": "close",
        "adj_close": "close",
        # 涨跌幅列由我们自行计算，旧列直接忽略
        "涨跌幅": "_drop_pct",
        "pct_change": "_drop_pct",
        "change": "_drop_pct",
    }
    result = result.rename(columns=column_mapping)

    # 删除数据源原有的涨跌幅列（后续重新计算）
    dropped = result.drop(columns=["_drop_pct"], errors="ignore")
    result = dropped if isinstance(dropped, pd.DataFrame) else result

    # ─────────────────────────────────────────
    # 3. 将日期索引转为普通列，并统一格式
    # ─────────────────────────────────────────
    result.index.name = "date"
    result = result.reset_index()
    result["date"] = pd.to_datetime(result["date"]).dt.tz_localize(None)

    # ─────────────────────────────────────────
    # 4. 按日期升序排序
    # ─────────────────────────────────────────
    result = result.sort_values("date").reset_index(drop=True)

    # ─────────────────────────────────────────
    # 5. 确保 OHLC 列存在（缺失则填 NaN）
    # ─────────────────────────────────────────
    for col in ("open", "high", "low", "close"):
        if col not in result.columns:
            result[col] = float("nan")

    # ─────────────────────────────────────────
    # 6. 计算 cum_return（累积涨跌幅）
    #    第一天 = 0，后续 = (close - first_close) / first_close * 100
    # ─────────────────────────────────────────
    first_close = result["close"].iloc[0]
    if first_close and first_close != 0:
        result["cum_return"] = (result["close"] - first_close) / first_close * 100
    else:
        result["cum_return"] = float("nan")
    result["cum_return"] = result["cum_return"].round(4)

    # ─────────────────────────────────────────
    # 7. 计算 daily_return（当日涨跌幅）
    #    第一天 = 0，后续 = (close_t - close_{t-1}) / close_{t-1} * 100
    # ─────────────────────────────────────────
    result["daily_return"] = result["close"].pct_change() * 100
    result["daily_return"] = result["daily_return"].fillna(0.0).round(4)

    # ─────────────────────────────────────────
    # 8. 添加 code 列
    # ─────────────────────────────────────────
    result["code"] = symbol.normalized

    # ─────────────────────────────────────────
    # 9. 整理最终列顺序
    #    固定: date, code, open, high, low, close
    #    可选: volume（存在则保留）
    #    指标: cum_return, daily_return
    # ─────────────────────────────────────────
    base_cols = ["date", "code", "open", "high", "low", "close"]
    optional_cols = ["volume"] if "volume" in result.columns else []
    metric_cols = ["cum_return", "daily_return"]

    final_cols = base_cols + optional_cols + metric_cols
    keep_cols = [c for c in final_cols if c in result.columns]
    return result.reindex(columns=keep_cols)


def format_for_output(
    df: pd.DataFrame,
    fmt: str = "csv",
    include_index: bool = False,
) -> "str | bytes":
    """
    将数据框序列化为目标格式

    Args:
        df           : 已标准化的数据框
        fmt          : 输出格式，支持 csv / json / parquet
        include_index: 是否在输出中包含 DataFrame 索引

    Returns:
        csv/json 返回 str，parquet 返回 bytes
    """
    if fmt == "csv":
        csv_str = df.to_csv(index=include_index)
        return csv_str if csv_str is not None else ""

    elif fmt == "json":
        # records 格式：[{date:..., code:..., ...}, ...]
        json_str = df.to_json(
            orient="records",
            date_format="iso",
            force_ascii=False,
            indent=2,
        )
        return json_str if json_str is not None else "[]"

    elif fmt == "parquet":
        buf = io.BytesIO()
        df.to_parquet(buf, index=include_index)
        return buf.getvalue()

    else:
        raise ValueError(f"不支持的输出格式: {fmt}，可选: csv / json / parquet")


def validate_dataframe(df: pd.DataFrame) -> tuple[bool, str]:
    """
    校验数据框是否符合标准格式

    Returns:
        (是否有效, 错误描述)
    """
    if df is None or df.empty:
        return False, "数据为空"

    required_cols = ["date", "code", "open", "high", "low", "close"]
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        return False, f"缺少必要列: {missing}"

    if any(df[col].isna().all() for col in required_cols):
        return False, "必要列中存在全部为 NaN 的列"

    return True, ""
