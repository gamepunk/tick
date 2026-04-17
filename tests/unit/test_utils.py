"""
测试工具函数
"""
import pytest
import pandas as pd
import numpy as np
from tick.utils.dates import resolve_date_range
from tick.utils.symbols import normalize_symbol, create_symbol, detect_asset_type
from tick.utils.filename import build_filename
from tick.utils.indicators import (
    add_moving_averages,
    add_rsi,
    add_macd,
    add_bollinger_bands,
    add_atr,
    add_obv,
    apply_indicators,
)


class TestSymbolUtils:
    """测试 Symbol 工具函数"""
    
    def test_normalize_symbol_stock(self):
        """测试股票代码标准化"""
        assert normalize_symbol("AAPL") == "AAPL"
        assert normalize_symbol("aapl") == "aapl"
    
    def test_normalize_symbol_index(self):
        """测试指数代码标准化"""
        # 美股指数自动加 ^
        assert normalize_symbol("GSPC", "index") == "^GSPC"
        assert normalize_symbol("DJI", "index") == "^DJI"
        
        # 已有 ^ 的不变
        assert normalize_symbol("^GSPC", "index") == "^GSPC"
        
        # A股指数不变
        assert normalize_symbol("sh000001", "index") == "sh000001"
    
    def test_create_symbol(self):
        """测试创建 Symbol 对象"""
        sym = create_symbol("AAPL", "stock")
        assert sym.raw == "AAPL"
        assert sym.asset_type.value == "stock"
    
    def test_detect_asset_type(self):
        """测试资产类型检测"""
        # 指数
        assert detect_asset_type("^GSPC", "yfinance") == "index"
        assert detect_asset_type("sh000001", "akshare") == "index"
        assert detect_asset_type("bj899050", "akshare") == "index"
        
        # 加密货币
        assert detect_asset_type("BTC-USD", "ccxt") == "crypto"
        
        # 期货
        assert detect_asset_type("GC=F", "yfinance") == "futures"
        
        # ETF
        assert detect_asset_type("SPY", "yfinance") == "fund"
        assert detect_asset_type("sh510300", "akshare") == "fund"
        
        # 默认股票
        assert detect_asset_type("AAPL", "yfinance") == "stock"


class TestFilenameUtils:
    """测试文件名工具"""
    
    def test_build_filename_basic(self):
        """测试基础文件名生成"""
        filename = build_filename(
            symbol="AAPL",
            start="2024-01-01",
            end="2024-12-31",
            interval="1d",
            adjust="qfq",
            src="yfinance",
            fmt="csv"
        )
        
        assert "AAPL" in filename
        assert "20240101" in filename
        assert "yf" in filename
        assert filename.endswith(".csv")
    
    def test_build_filename_with_exchange(self):
        """测试带交易所的文件名"""
        filename = build_filename(
            symbol="BTC-USD",
            start="2024-01-01",
            end="2024-12-31",
            interval="1d",
            adjust="",
            src="ccxt",
            fmt="csv",
            exchange="kraken"
        )
        
        assert "ccxt_kraken" in filename
    
    def test_build_filename_index(self):
        """测试指数文件名"""
        filename = build_filename(
            symbol="^GSPC",
            start="2024-01-01",
            end="2024-12-31",
            interval="1d",
            adjust="",
            src="yfinance",
            fmt="csv",
            asset_type="index"
        )
        
        assert "idx" in filename


class TestIndicators:
    """测试技术指标"""
    
    def test_add_moving_averages(self, sample_dataframe):
        """测试移动平均线"""
        df = add_moving_averages(sample_dataframe, periods=[5, 10])
        
        assert "ma5" in df.columns
        assert "ma10" in df.columns
        # 前几行应该是 NaN（因为滚动窗口）
        assert df["ma5"].iloc[:4].isna().all()
    
    def test_add_rsi(self, sample_dataframe):
        """测试 RSI"""
        df = add_rsi(sample_dataframe, period=14)
        
        assert "rsi" in df.columns
        # RSI 应该在 0-100 之间
        assert df["rsi"].dropna().between(0, 100).all()
    
    def test_add_macd(self, sample_dataframe):
        """测试 MACD"""
        df = add_macd(sample_dataframe)
        
        assert "macd" in df.columns
        assert "macd_signal" in df.columns
        assert "macd_hist" in df.columns


class TestIndicatorsExtended:
    """扩展的技术指标测试"""

    # ─────────────────────────────────────────
    # 移动平均线 (add_moving_averages) 扩展测试
    # ─────────────────────────────────────────

    def test_add_moving_averages_different_periods(self, sample_dataframe):
        """测试不同周期参数"""
        df = add_moving_averages(sample_dataframe, periods=[5, 15, 30])
        
        assert "ma5" in df.columns
        assert "ma15" in df.columns
        assert "ma30" in df.columns
        # 数据足够，这些列应该有非 NaN 值
        assert df["ma5"].iloc[5:].notna().any()

    def test_add_moving_averages_insufficient_data(self):
        """测试数据不足时的处理"""
        # 创建只有 3 行的数据，但请求 5 日 MA
        df = pd.DataFrame({
            "open": [100, 101, 102],
            "high": [105, 106, 107],
            "low": [95, 96, 97],
            "close": [102, 103, 104],
            "volume": [1000000, 1100000, 1200000]
        })
        df = add_moving_averages(df, periods=[5])
        
        assert "ma5" in df.columns
        # 所有值都应该是 NaN，因为数据不足 5 天
        assert df["ma5"].isna().all()

    def test_add_moving_averages_custom_periods(self, sample_dataframe):
        """测试自定义周期列表"""
        custom_periods = [3, 7, 21, 100]
        df = add_moving_averages(sample_dataframe, periods=custom_periods)
        
        for period in custom_periods:
            assert f"ma{period}" in df.columns

    # ─────────────────────────────────────────
    # RSI (add_rsi) 扩展测试
    # ─────────────────────────────────────────

    def test_add_rsi_different_periods(self, sample_dataframe):
        """测试不同周期的 RSI"""
        for period in [7, 14, 21]:
            df = add_rsi(sample_dataframe.copy(), period=period)
            assert "rsi" in df.columns
            # RSI 应该在 0-100 之间
            valid_rsi = df["rsi"].dropna()
            assert (valid_rsi >= 0).all() and (valid_rsi <= 100).all()

    def test_add_rsi_insufficient_data(self):
        """测试数据不足时的处理"""
        df = pd.DataFrame({
            "close": [100, 101, 102, 103, 104]
        })
        df = add_rsi(df, period=14)
        
        assert "rsi" in df.columns
        # 所有值都应该是 NaN
        assert df["rsi"].isna().all()

    def test_add_rsi_value_range(self, sample_dataframe):
        """验证 RSI 值范围 (0-100)"""
        df = add_rsi(sample_dataframe, period=14)
        valid_rsi = df["rsi"].dropna()
        
        assert len(valid_rsi) > 0
        assert (valid_rsi >= 0).all()
        assert (valid_rsi <= 100).all()

    # ─────────────────────────────────────────
    # MACD (add_macd) 扩展测试
    # ─────────────────────────────────────────

    def test_add_macd_default_params(self, sample_dataframe):
        """测试 MACD 默认参数"""
        df = add_macd(sample_dataframe)
        
        assert "macd" in df.columns
        assert "macd_signal" in df.columns
        assert "macd_hist" in df.columns
        # 应该有有效值（EMA 计算没有 NaN 问题）
        assert df["macd"].notna().any()

    def test_add_macd_custom_params(self, sample_dataframe):
        """测试 MACD 自定义参数"""
        df = add_macd(sample_dataframe.copy(), fast=8, slow=21, signal=5)
        
        assert "macd" in df.columns
        assert "macd_signal" in df.columns
        assert "macd_hist" in df.columns

    def test_add_macd_insufficient_data(self):
        """测试数据不足时的处理"""
        df = pd.DataFrame({
            "close": [100, 101, 102]
        })
        df = add_macd(df)
        
        # EMA 计算在数据不足时仍然会产生结果（指数加权）
        assert "macd" in df.columns
        assert "macd_signal" in df.columns

    # ─────────────────────────────────────────
    # 布林带 (add_bollinger_bands) 测试
    # ─────────────────────────────────────────

    def test_add_bollinger_bands_basic(self, sample_dataframe):
        """测试布林带基本计算"""
        df = add_bollinger_bands(sample_dataframe)
        
        assert "bb_upper" in df.columns
        assert "bb_middle" in df.columns
        assert "bb_lower" in df.columns
        assert "bb_width" in df.columns
        assert "bb_position" in df.columns

    def test_add_bollinger_bands_validity(self, sample_dataframe):
        """验证上轨 > 中轨 > 下轨"""
        df = add_bollinger_bands(sample_dataframe)
        
        # 去除 NaN 值进行比较
        valid = df.dropna()
        assert len(valid) > 0
        
        # 上轨应该大于等于中轨
        assert (valid["bb_upper"] >= valid["bb_middle"]).all()
        # 中轨应该大于等于下轨
        assert (valid["bb_middle"] >= valid["bb_lower"]).all()

    def test_add_bollinger_bands_custom_params(self, sample_dataframe):
        """测试布林带自定义参数"""
        df = add_bollinger_bands(sample_dataframe.copy(), period=10, std=1.5)
        
        assert "bb_upper" in df.columns
        assert "bb_middle" in df.columns
        assert "bb_lower" in df.columns

    # ─────────────────────────────────────────
    # ATR (add_atr) 测试
    # ─────────────────────────────────────────

    def test_add_atr_basic(self, sample_dataframe):
        """测试 ATR 基本计算"""
        df = add_atr(sample_dataframe)
        
        assert "atr" in df.columns

    def test_add_atr_positive(self, sample_dataframe):
        """验证 ATR 为正数"""
        df = add_atr(sample_dataframe)
        
        valid_atr = df["atr"].dropna()
        assert len(valid_atr) > 0
        # ATR 必须为正
        assert (valid_atr > 0).all()

    def test_add_atr_custom_period(self, sample_dataframe):
        """测试 ATR 自定义周期"""
        df = add_atr(sample_dataframe.copy(), period=7)
        
        assert "atr" in df.columns

    # ─────────────────────────────────────────
    # OBV (add_obv) 测试
    # ─────────────────────────────────────────

    def test_add_obv_basic(self, sample_dataframe):
        """测试 OBV 基本计算"""
        df = add_obv(sample_dataframe)
        
        assert "obv" in df.columns
        # 第一行 OBV 应该为 0
        assert df["obv"].iloc[0] == 0

    def test_add_obv_direction(self):
        """验证 OBV 变化方向"""
        # 构造上涨数据：收盘价持续上升
        df_up = pd.DataFrame({
            "close": [100, 105, 110, 115],
            "volume": [1000, 1000, 1000, 1000]
        })
        df_up = add_obv(df_up)
        
        # 上涨时 OBV 应该增加
        assert df_up["obv"].iloc[3] > df_up["obv"].iloc[0]
        
        # 构造下跌数据：收盘价持续下降
        df_down = pd.DataFrame({
            "close": [100, 95, 90, 85],
            "volume": [1000, 1000, 1000, 1000]
        })
        df_down = add_obv(df_down)
        
        # 下跌时 OBV 应该减少
        assert df_down["obv"].iloc[3] < df_down["obv"].iloc[0]
        
        # 构造平盘数据：收盘价不变
        df_flat = pd.DataFrame({
            "close": [100, 100, 100, 100],
            "volume": [1000, 1000, 1000, 1000]
        })
        df_flat = add_obv(df_flat)
        
        # 平盘时 OBV 应该不变
        assert df_flat["obv"].iloc[3] == df_flat["obv"].iloc[0]

    # ─────────────────────────────────────────
    # 批量添加指标 (apply_indicators) 测试
    # ─────────────────────────────────────────

    def test_apply_indicators_batch(self, sample_dataframe):
        """测试批量添加指标"""
        df = apply_indicators(sample_dataframe.copy(), indicators=["ma", "rsi", "macd"])
        
        # 检查是否添加了相应的指标
        assert any(col.startswith("ma") for col in df.columns)
        assert "rsi" in df.columns
        assert "macd" in df.columns

    def test_apply_indicators_invalid_name(self, sample_dataframe):
        """测试无效指标名称处理"""
        df_original = sample_dataframe.copy()
        df = apply_indicators(df_original, indicators=["invalid_indicator", "rsi"])
        
        # 无效指标应该被忽略，RSI 应该被添加
        assert "rsi" in df.columns

    def test_apply_indicators_empty_list(self, sample_dataframe):
        """测试空列表"""
        df_original = sample_dataframe.copy()
        df = apply_indicators(df_original, indicators=[])
        
        # 不应该添加任何新列
        assert list(df.columns) == list(df_original.columns)

    def test_apply_indicators_all(self, sample_dataframe):
        """测试添加所有指标"""
        df = apply_indicators(sample_dataframe.copy(), indicators=["all"])
        
        # 检查各种指标是否被添加
        assert any(col.startswith("ma") for col in df.columns)
        assert "rsi" in df.columns
        assert "macd" in df.columns
        assert "bb_upper" in df.columns
        assert "atr" in df.columns
        assert "obv" in df.columns


class TestDateUtils:
    """测试日期工具函数"""

    def test_resolve_date_range_with_values(self):
        """测试传入具体日期"""
        start, end = resolve_date_range("2024-01-01", "2024-12-31")
        assert start == "2024-01-01"
        assert end == "2024-12-31"

    def test_resolve_date_range_defaults(self):
        """测试自动填充默认值"""
        from datetime import datetime, timedelta

        start, end = resolve_date_range(None, None)
        expected_end = datetime.today().strftime("%Y-%m-%d")
        expected_start = (datetime.today() - timedelta(days=365)).strftime("%Y-%m-%d")
        assert end == expected_end
        assert start == expected_start

    def test_resolve_date_range_custom_days(self):
        """测试自定义默认天数"""
        from datetime import datetime, timedelta

        start, end = resolve_date_range(None, "2024-06-01", default_days=30)
        # 当 start 为 None 时，基于 today 计算，而不是基于 end
        expected_start = (datetime.today() - timedelta(days=30)).strftime("%Y-%m-%d")
        assert start == expected_start
        assert end == "2024-06-01"
