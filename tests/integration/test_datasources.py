"""
集成测试：数据源
"""
import pytest
import pandas as pd
from unittest.mock import Mock, patch, MagicMock
from tick.core.models import Symbol, AssetType, FetchConfig, Interval
from tick.datasources.yfinance_ds import YFinanceDataSource
from tick.datasources.akshare_ds import AkShareDataSource
from tick.datasources.ccxt_ds import CCXTDataSource
from tick.datasources.router import DataSourceRouter


class TestDataSourceRouter:
    """测试数据源路由"""
    
    def test_detect_yfinance_stock(self):
        """测试识别美股"""
        sym = Symbol(raw="AAPL", normalized="AAPL")
        assert DataSourceRouter.detect_market(sym) == "yfinance"
    
    def test_detect_yfinance_index(self):
        """测试识别美股指数"""
        sym = Symbol(raw="^GSPC", normalized="^GSPC")
        assert DataSourceRouter.detect_market(sym) == "yfinance"
    
    def test_detect_akshare_a_stock(self):
        """测试识别A股"""
        sym = Symbol(raw="sh600519", normalized="SH600519")
        assert DataSourceRouter.detect_market(sym) == "akshare"
    
    def test_detect_akshare_bj_stock(self):
        """测试识别北交所"""
        sym = Symbol(raw="bj835305", normalized="BJ835305")
        assert DataSourceRouter.detect_market(sym) == "akshare"
    
    def test_detect_ccxt_crypto(self):
        """测试识别加密货币"""
        sym = Symbol(raw="BTC-USD", normalized="BTC-USD")
        assert DataSourceRouter.detect_market(sym) == "ccxt"
    
    def test_detect_with_asset_type(self):
        """测试使用资产类型提示"""
        # GSPC 没有 ^ 前缀，但指定了 index
        sym = Symbol(raw="GSPC", normalized="GSPC", asset_type=AssetType.INDEX)
        assert DataSourceRouter.detect_market(sym) == "yfinance"


class TestYFinanceDataSource:
    """测试 Yahoo Finance 数据源"""
    
    @patch("tick.datasources.yfinance_ds.yf")
    def test_fetch_success(self, mock_yf, sample_config):
        """测试成功获取数据"""
        # 模拟返回数据
        mock_ticker = MagicMock()
        mock_ticker.history.return_value = pd.DataFrame({
            "Open": [100.0],
            "High": [110.0],
            "Low": [90.0],
            "Close": [105.0],
            "Volume": [1000000]
        }, index=pd.DatetimeIndex(["2024-01-01"], tz="UTC"))
        mock_yf.Ticker.return_value = mock_ticker
        
        ds = YFinanceDataSource()
        result = ds.fetch(sample_config)
        
        assert result.success is True
        assert result.data is not None
        assert "close" in result.data.columns
    
    def test_validate_symbol(self):
        """测试代码验证"""
        ds = YFinanceDataSource()
        
        assert ds.validate_symbol(Symbol(raw="AAPL", normalized="AAPL")) is True
        assert ds.validate_symbol(Symbol(raw="^GSPC", normalized="^GSPC")) is True
        assert ds.validate_symbol(Symbol(raw="0700.HK", normalized="0700.HK")) is True
        assert ds.validate_symbol(Symbol(raw="GC=F", normalized="GC=F")) is True


class TestAkShareDataSource:
    """测试 AkShare 数据源"""
    
    def test_is_futures(self):
        """测试期货识别"""
        ds = AkShareDataSource()
        
        assert ds._is_futures("AU") is True
        assert ds._is_futures("AG2506") is True
        assert ds._is_futures("sh600519") is False
    
    def test_validate_symbol(self):
        """测试代码验证"""
        ds = AkShareDataSource()
        
        assert ds.validate_symbol(Symbol(raw="sh600519", normalized="SH600519")) is True
        assert ds.validate_symbol(Symbol(raw="bj835305", normalized="BJ835305")) is True
        assert ds.validate_symbol(Symbol(raw="AU", normalized="AU")) is True


class TestCCXTDataSource:
    """测试 CCXT 数据源"""
    
    def test_to_ccxt_symbol(self):
        """测试代码格式转换"""
        ds = CCXTDataSource()
        
        # Binance 使用 USDT
        assert ds._to_ccxt_symbol("BTC-USD", "binance") == "BTC/USDT"
        
        # Kraken 使用 USD，且 BTC 转为 XBT
        assert ds._to_ccxt_symbol("BTC-USD", "kraken") == "XBT/USD"
        
        # 无后缀的代码
        assert ds._to_ccxt_symbol("ETH", "binance") == "ETH/USDT"
    
    def test_validate_symbol(self):
        """测试代码验证"""
        ds = CCXTDataSource()
        
        assert ds.validate_symbol(Symbol(raw="BTC-USD", normalized="BTC-USD")) is True
        assert ds.validate_symbol(Symbol(raw="ETH-USDT", normalized="ETH-USDT")) is True
        assert ds.validate_symbol(Symbol(raw="BTC", normalized="BTC")) is True
