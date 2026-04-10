"""
测试核心数据模型
"""
import pytest
from datetime import datetime
from tick.core.models import (
    Symbol, AssetType, DataSource, Interval, FetchConfig, 
    FetchResult, ASSET_TYPE_NAMES, US_INDEX_CODES
)


class TestAssetType:
    """测试 AssetType 枚举"""
    
    def test_choices(self):
        """测试 choices 方法"""
        choices = AssetType.choices()
        assert "stock" in choices
        assert "index" in choices
        assert "futures" in choices
        assert "fund" in choices
        assert "crypto" in choices
    
    def test_from_string(self):
        """测试从字符串创建"""
        assert AssetType("stock") == AssetType.STOCK
        assert AssetType("index") == AssetType.INDEX


class TestSymbol:
    """测试 Symbol 模型"""
    
    def test_creation(self):
        """测试创建 Symbol"""
        sym = Symbol(raw="AAPL", normalized="AAPL")
        assert sym.raw == "AAPL"
        assert sym.normalized == "AAPL"
    
    def test_uppercase_normalization(self):
        """测试自动转大写"""
        sym = Symbol(raw="aapl", normalized="aapl")
        assert sym.raw == "AAPL"
        assert sym.normalized == "AAPL"
    
    def test_with_asset_type(self):
        """测试带资产类型"""
        sym = Symbol(
            raw="AAPL",
            normalized="AAPL",
            asset_type=AssetType.STOCK,
            market="US"
        )
        assert sym.asset_type == AssetType.STOCK
        assert sym.market == "US"


class TestFetchConfig:
    """测试 FetchConfig 模型"""
    
    def test_default_values(self):
        """测试默认值"""
        sym = Symbol(raw="TEST", normalized="TEST")
        config = FetchConfig(symbol=sym)
        
        assert config.interval == Interval.DAY
        assert config.adjust == "qfq"
        assert config.exchange == "binance"
        assert config.use_cache is True
    
    def test_custom_values(self):
        """测试自定义值"""
        sym = Symbol(raw="BTC", normalized="BTC")
        config = FetchConfig(
            symbol=sym,
            start="2024-01-01",
            end="2024-12-31",
            interval=Interval.HOUR,
            exchange="kraken"
        )
        
        assert config.start == "2024-01-01"
        assert config.interval == Interval.HOUR
        assert config.exchange == "kraken"


class TestFetchResult:
    """测试 FetchResult 模型"""
    
    def test_success_result(self):
        """测试成功结果"""
        sym = Symbol(raw="AAPL", normalized="AAPL")
        result = FetchResult(
            symbol=sym,
            data=None,
            success=True,
            metadata={"rows": 100}
        )
        
        assert result.success is True
        assert result.fetch_time is not None
        assert result.metadata["rows"] == 100
    
    def test_error_result(self):
        """测试错误结果"""
        sym = Symbol(raw="INVALID", normalized="INVALID")
        result = FetchResult(
            symbol=sym,
            success=False,
            error_message="Symbol not found"
        )
        
        assert result.success is False
        assert result.error_message == "Symbol not found"


class TestConstants:
    """测试常量"""
    
    def test_asset_type_names(self):
        """测试资产类型名称映射"""
        assert ASSET_TYPE_NAMES[AssetType.STOCK] == "股票"
        assert ASSET_TYPE_NAMES[AssetType.INDEX] == "指数"
        assert ASSET_TYPE_NAMES[AssetType.CRYPTO] == "加密货币"
    
    def test_us_index_codes(self):
        """测试美股指数代码集合"""
        assert "GSPC" in US_INDEX_CODES
        assert "DJI" in US_INDEX_CODES
        assert "IXIC" in US_INDEX_CODES
        assert "VIX" in US_INDEX_CODES
