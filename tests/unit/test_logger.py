"""
测试日志系统
"""
import pytest
import logging
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock

from tick.core.logger import (
    TickLogger,
    get_logger,
    log_fetch_start,
    log_fetch_success,
    log_fetch_error,
    log_cache_hit,
    log_cache_miss
)


class TestTickLogger:
    """测试日志管理器"""
    
    @pytest.fixture
    def temp_log_dir(self):
        """临时日志目录"""
        tmp_dir = tempfile.mkdtemp()
        yield Path(tmp_dir)
        shutil.rmtree(tmp_dir)
    
    def test_logger_singleton(self):
        """测试日志单例模式"""
        logger1 = TickLogger()
        logger2 = TickLogger()
        
        # 应该是同一个实例
        assert logger1 is logger2
    
    def test_logger_get_logger(self):
        """测试获取日志记录器"""
        logger = TickLogger()
        
        # 获取根记录器
        root = logger.get_logger()
        assert root.name == "tick"
        
        # 获取子记录器
        child = logger.get_logger("fetch")
        assert child.name == "tick.fetch"
    
    def test_logger_levels(self):
        """测试日志级别方法"""
        logger = TickLogger()
        
        # 测试各级别日志
        with patch.object(logger.logger, 'debug') as mock_debug, \
             patch.object(logger.logger, 'info') as mock_info, \
             patch.object(logger.logger, 'warning') as mock_warning, \
             patch.object(logger.logger, 'error') as mock_error:
            
            logger.debug("debug message")
            logger.info("info message")
            logger.warning("warning message")
            logger.error("error message")
            
            mock_debug.assert_called_once_with("debug message")
            mock_info.assert_called_once_with("info message")
            mock_warning.assert_called_once_with("warning message")
            mock_error.assert_called_once_with("error message")
    
    def test_set_level(self):
        """测试设置日志级别"""
        logger = TickLogger()
        
        logger.set_level(logging.DEBUG)
        assert logger.logger.level == logging.DEBUG
        
        logger.set_level(logging.ERROR)
        assert logger.logger.level == logging.ERROR


class TestLogHelpers:
    """测试日志辅助函数"""
    
    def test_log_fetch_start(self):
        """测试记录开始下载日志"""
        with patch('tick.core.logger.get_logger') as mock_get_logger:
            mock_logger = MagicMock()
            mock_get_logger.return_value = mock_logger
            
            log_fetch_start("AAPL", "yfinance", start="2024-01-01", end="2024-12-31")
            
            mock_logger.info.assert_called()
            mock_logger.debug.assert_called()
    
    def test_log_fetch_success(self):
        """测试记录下载成功日志"""
        with patch('tick.core.logger.get_logger') as mock_get_logger:
            mock_logger = MagicMock()
            mock_get_logger.return_value = mock_logger
            
            log_fetch_success("AAPL", 100, 1.5)
            
            mock_logger.info.assert_called_once()
            call_args = mock_logger.info.call_args[0][0]
            assert "AAPL" in call_args
            assert "100" in call_args
            assert "1.5" in call_args
    
    def test_log_fetch_error(self):
        """测试记录下载失败日志"""
        with patch('tick.core.logger.get_logger') as mock_get_logger:
            mock_logger = MagicMock()
            mock_get_logger.return_value = mock_logger
            
            log_fetch_error("AAPL", "Network error", "yfinance")
            
            mock_logger.error.assert_called_once()
            call_args = mock_logger.error.call_args[0][0]
            assert "AAPL" in call_args
            assert "Network error" in call_args
    
    def test_log_cache_hit(self):
        """测试记录缓存命中日志"""
        with patch('tick.core.logger.get_logger') as mock_get_logger:
            mock_logger = MagicMock()
            mock_get_logger.return_value = mock_logger
            
            log_cache_hit("AAPL", "key123")
            
            mock_logger.debug.assert_called_once()
    
    def test_log_cache_miss(self):
        """测试记录缓存未命中日志"""
        with patch('tick.core.logger.get_logger') as mock_get_logger:
            mock_logger = MagicMock()
            mock_get_logger.return_value = mock_logger
            
            log_cache_miss("AAPL", "key123")
            
            mock_logger.debug.assert_called_once()


class TestGetLogger:
    """测试获取日志记录器"""
    
    def test_get_logger_returns_logger(self):
        """测试 get_logger 返回日志记录器"""
        logger = get_logger()
        assert isinstance(logger, logging.Logger)
        assert logger.name == "tick"
    
    def test_get_logger_with_name(self):
        """测试带名称获取日志记录器"""
        logger = get_logger("fetch")
        assert logger.name == "tick.fetch"
    
    def test_get_logger_singleton(self):
        """测试日志记录器单例"""
        # 清除全局实例
        import tick.core.logger
        tick.core.logger._logger = None
        
        logger1 = get_logger()
        logger2 = get_logger()
        
        # 应该是同一个 TickLogger 实例返回的记录器
        assert logger1.name == logger2.name
