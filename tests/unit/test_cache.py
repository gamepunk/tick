"""
测试缓存系统
"""
import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
import tempfile
import shutil

from tick.utils.cache import DataCache, get_cache


class TestDataCache:
    """测试数据缓存"""
    
    @pytest.fixture
    def temp_cache_dir(self):
        """临时缓存目录"""
        tmp_dir = tempfile.mkdtemp()
        yield Path(tmp_dir)
        shutil.rmtree(tmp_dir)
    
    @pytest.fixture
    def sample_df(self):
        """示例数据框"""
        return pd.DataFrame({
            'date': pd.date_range('2024-01-01', periods=3),
            'code': ['AAPL'] * 3,
            'open': [100.0, 101.0, 102.0],
            'high': [105.0, 106.0, 107.0],
            'low': [99.0, 100.0, 101.0],
            'close': [101.0, 102.0, 103.0],
            'volume': [1000, 2000, 3000]
        })
    
    @pytest.fixture
    def cache(self, temp_cache_dir):
        """缓存实例"""
        return DataCache(cache_dir=temp_cache_dir)
    
    def test_cache_init(self, temp_cache_dir):
        """测试缓存初始化"""
        cache = DataCache(cache_dir=temp_cache_dir)
        
        # 检查数据库文件创建
        assert cache.db_path.exists()
        assert cache.cache_dir.exists()
    
    def test_cache_set_and_get(self, cache, sample_df):
        """测试缓存设置和获取"""
        symbol = "AAPL"
        start = "2024-01-01"
        end = "2024-01-03"
        interval = "1d"
        
        # 设置缓存
        cache.set(symbol, start, end, interval, sample_df)
        
        # 获取缓存
        cached_df = cache.get(symbol, start, end, interval)
        
        assert cached_df is not None
        assert len(cached_df) == len(sample_df)
        assert list(cached_df.columns) == list(sample_df.columns)
    
    def test_cache_miss(self, cache):
        """测试缓存未命中"""
        result = cache.get("UNKNOWN", "2024-01-01", "2024-01-03", "1d")
        assert result is None
    
    def test_cache_expiration(self, cache, sample_df):
        """测试缓存过期"""
        symbol = "AAPL"
        start = "2024-01-01"
        end = "2024-01-03"
        interval = "1d"
        
        # 设置短过期时间
        cache.set(symbol, start, end, interval, sample_df, ttl=1)
        
        # 立即获取应该命中
        assert cache.get(symbol, start, end, interval) is not None
        
        # 等待过期
        import time
        time.sleep(2)
        
        # 过期后应该返回 None
        assert cache.get(symbol, start, end, interval) is None
    
    def test_cache_clear_symbol(self, cache, sample_df):
        """测试清除特定品种缓存"""
        # 设置两个品种的缓存
        cache.set("AAPL", "2024-01-01", "2024-01-03", "1d", sample_df)
        cache.set("TSLA", "2024-01-01", "2024-01-03", "1d", sample_df)
        
        # 清除 AAPL 缓存
        cache.clear("AAPL")
        
        # AAPL 应该未命中
        assert cache.get("AAPL", "2024-01-01", "2024-01-03", "1d") is None
        
        # TSLA 应该仍然命中
        assert cache.get("TSLA", "2024-01-01", "2024-01-03", "1d") is not None
    
    def test_cache_clear_all(self, cache, sample_df):
        """测试清除所有缓存"""
        cache.set("AAPL", "2024-01-01", "2024-01-03", "1d", sample_df)
        cache.set("TSLA", "2024-01-01", "2024-01-03", "1d", sample_df)
        
        # 清除所有缓存
        cache.clear()
        
        # 都应该未命中
        assert cache.get("AAPL", "2024-01-01", "2024-01-03", "1d") is None
        assert cache.get("TSLA", "2024-01-01", "2024-01-03", "1d") is None
    
    def test_cache_cleanup_expired(self, cache, sample_df):
        """测试清理过期缓存"""
        symbol = "AAPL"
        start = "2024-01-01"
        end = "2024-01-03"
        interval = "1d"
        
        # 设置短过期时间
        cache.set(symbol, start, end, interval, sample_df, ttl=1)
        
        # 等待过期
        import time
        time.sleep(2)
        
        # 清理过期数据
        cache.cleanup_expired()
        
        # 应该返回 None
        assert cache.get(symbol, start, end, interval) is None
    
    def test_cache_different_keys(self, cache, sample_df):
        """测试不同参数生成不同缓存键"""
        symbol = "AAPL"
        
        # 不同日期范围
        cache.set(symbol, "2024-01-01", "2024-01-03", "1d", sample_df)
        cache.set(symbol, "2024-02-01", "2024-02-03", "1d", sample_df)
        
        # 应该分别命中
        assert cache.get(symbol, "2024-01-01", "2024-01-03", "1d") is not None
        assert cache.get(symbol, "2024-02-01", "2024-02-03", "1d") is not None
    
    def test_cache_preserve_data_types(self, cache, sample_df):
        """测试缓存保留数据类型"""
        symbol = "AAPL"
        start = "2024-01-01"
        end = "2024-01-03"
        interval = "1d"
        
        cache.set(symbol, start, end, interval, sample_df)
        cached_df = cache.get(symbol, start, end, interval)
        
        # 检查数据类型
        assert pd.api.types.is_datetime64_any_dtype(cached_df['date'])
        assert pd.api.types.is_float_dtype(cached_df['close'])
        assert pd.api.types.is_integer_dtype(cached_df['volume'])


class TestGetCache:
    """测试全局缓存获取"""
    
    def test_get_cache_singleton(self):
        """测试缓存单例模式"""
        from tick.utils.cache import get_cache, _cache
        
        # 清除全局缓存实例
        import tick.utils.cache
        tick.utils.cache._cache = None
        
        # 获取缓存
        cache1 = get_cache()
        cache2 = get_cache()
        
        # 应该是同一个实例
        assert cache1 is cache2
