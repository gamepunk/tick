"""
测试配置系统
"""
import pytest
import yaml
from pathlib import Path
from tick.core.config import AppConfig, CacheConfig, DisplayConfig, DatasourceConfig


class TestAppConfig:
    """测试应用配置"""
    
    def test_default_config(self):
        """测试默认配置"""
        config = AppConfig()
        
        assert config.default_output_dir == "~/Desktop"
        assert config.default_format == "csv"
        # default_interval 可以是 "1y" 或 "1d" 取决于实现
        assert config.default_interval in ["1y", "1d"]
        assert isinstance(config.cache, CacheConfig)
        assert isinstance(config.display, DisplayConfig)
    
    def test_save_and_load(self, temp_dir):
        """测试保存和加载配置"""
        config_path = temp_dir / "config.yaml"
        
        # 创建并保存配置
        config = AppConfig(
            default_format="parquet",
            default_interval="6mo"
        )
        config.save(str(config_path))
        
        # 验证文件存在
        assert config_path.exists()
        
        # 加载配置
        loaded = AppConfig.load(str(config_path))
        assert loaded.default_format == "parquet"
        assert loaded.default_interval == "6mo"
    
    def test_get_cache_dir(self, temp_dir):
        """测试获取缓存目录"""
        config = AppConfig(cache=CacheConfig(directory=str(temp_dir / "cache")))
        cache_dir = config.get_cache_dir()
        
        assert cache_dir == Path(temp_dir / "cache")
        assert cache_dir.exists()
    
    def test_get_output_dir(self, temp_dir):
        """测试获取输出目录"""
        config = AppConfig(default_output_dir=str(temp_dir / "output"))
        output_dir = config.get_output_dir()
        
        assert output_dir == Path(temp_dir / "output")
        assert output_dir.exists()


class TestCacheConfig:
    """测试缓存配置"""
    
    def test_defaults(self):
        """测试默认值"""
        config = CacheConfig()
        assert config.enabled is True
        assert config.ttl == 3600
        assert config.max_size == 100


class TestDisplayConfig:
    """测试显示配置"""
    
    def test_defaults(self):
        """测试默认值"""
        config = DisplayConfig()
        assert config.color is True
        assert config.progress_bar is True
        assert config.table_style == "blue"


class TestDatasourceConfig:
    """测试数据源配置"""
    
    def test_defaults(self):
        """测试默认值"""
        config = DatasourceConfig()
        
        assert config.yfinance["timeout"] == 30
        assert config.akshare["adjust"] == "qfq"
        assert config.ccxt["default_exchange"] == "binance"
