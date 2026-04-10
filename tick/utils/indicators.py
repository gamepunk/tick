"""
技术指标计算
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Optional


def add_moving_averages(df: pd.DataFrame, periods: List[int] = [5, 10, 20, 60]) -> pd.DataFrame:
    """添加移动平均线"""
    for period in periods:
        df[f"ma{period}"] = df["close"].rolling(window=period).mean()
    return df


def add_bollinger_bands(df: pd.DataFrame, period: int = 20, std: float = 2.0) -> pd.DataFrame:
    """添加布林带"""
    df["bb_middle"] = df["close"].rolling(window=period).mean()
    rolling_std = df["close"].rolling(window=period).std()
    df["bb_upper"] = df["bb_middle"] + (rolling_std * std)
    df["bb_lower"] = df["bb_middle"] - (rolling_std * std)
    df["bb_width"] = (df["bb_upper"] - df["bb_lower"]) / df["bb_middle"]
    df["bb_position"] = (df["close"] - df["bb_lower"]) / (df["bb_upper"] - df["bb_lower"])
    return df


def add_rsi(df: pd.DataFrame, period: int = 14) -> pd.DataFrame:
    """添加 RSI 指标"""
    delta = df["close"].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    df["rsi"] = 100 - (100 / (1 + rs))
    return df


def add_macd(df: pd.DataFrame, fast: int = 12, slow: int = 26, signal: int = 9) -> pd.DataFrame:
    """添加 MACD 指标"""
    ema_fast = df["close"].ewm(span=fast).mean()
    ema_slow = df["close"].ewm(span=slow).mean()
    df["macd"] = ema_fast - ema_slow
    df["macd_signal"] = df["macd"].ewm(span=signal).mean()
    df["macd_hist"] = df["macd"] - df["macd_signal"]
    return df


def add_kdj(df: pd.DataFrame, n: int = 9, m1: int = 3, m2: int = 3) -> pd.DataFrame:
    """添加 KDJ 指标"""
    low_list = df["low"].rolling(window=n, min_periods=n).min()
    high_list = df["high"].rolling(window=n, min_periods=n).max()
    rsv = (df["close"] - low_list) / (high_list - low_list) * 100
    
    df["kdj_k"] = rsv.ewm(alpha=1/m1, adjust=False).mean()
    df["kdj_d"] = df["kdj_k"].ewm(alpha=1/m2, adjust=False).mean()
    df["kdj_j"] = 3 * df["kdj_k"] - 2 * df["kdj_d"]
    return df


def add_atr(df: pd.DataFrame, period: int = 14) -> pd.DataFrame:
    """添加 ATR (平均真实波幅)"""
    high_low = df["high"] - df["low"]
    high_close = np.abs(df["high"] - df["close"].shift())
    low_close = np.abs(df["low"] - df["close"].shift())
    tr = np.maximum(high_low, np.maximum(high_close, low_close))
    df["atr"] = tr.rolling(window=period).mean()
    return df


def add_obv(df: pd.DataFrame) -> pd.DataFrame:
    """添加 OBV (能量潮)"""
    obv = [0]
    for i in range(1, len(df)):
        if df["close"].iloc[i] > df["close"].iloc[i-1]:
            obv.append(obv[-1] + df["volume"].iloc[i])
        elif df["close"].iloc[i] < df["close"].iloc[i-1]:
            obv.append(obv[-1] - df["volume"].iloc[i])
        else:
            obv.append(obv[-1])
    df["obv"] = obv
    return df


def add_all_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """添加所有常用技术指标"""
    df = df.copy()
    
    # 价格相关
    df = add_moving_averages(df)
    df = add_bollinger_bands(df)
    
    # 动量指标
    df = add_rsi(df)
    df = add_macd(df)
    df = add_kdj(df)
    
    # 波动率/成交量
    df = add_atr(df)
    df = add_obv(df)
    
    return df


INDICATOR_FUNCTIONS = {
    "ma": add_moving_averages,
    "boll": add_bollinger_bands,
    "rsi": add_rsi,
    "macd": add_macd,
    "kdj": add_kdj,
    "atr": add_atr,
    "obv": add_obv,
    "all": add_all_indicators,
}


def apply_indicators(df: pd.DataFrame, indicators: List[str]) -> pd.DataFrame:
    """
    应用指定的技术指标
    
    Args:
        df: 原始数据
        indicators: 指标名称列表
    """
    df = df.copy()
    
    for indicator in indicators:
        func = INDICATOR_FUNCTIONS.get(indicator.lower())
        if func:
            df = func(df)
    
    return df
