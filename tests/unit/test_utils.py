"""
测试工具函数
"""
import pytest
import pandas as pd
import numpy as np
from tick.utils.symbols import normalize_symbol, create_symbol, detect_asset_type
from tick.utils.filename import build_filename
from tick.utils.indicators import add_moving_averages, add_rsi, add_macd


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
