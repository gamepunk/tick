"""
日志系统
支持文件日志、控制台日志、结构化日志
"""
import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional
from logging.handlers import RotatingFileHandler
from rich.logging import RichHandler
from tick.core.config import get_config


class TickLogger:
    """tick 日志管理器"""
    
    _instance: Optional["TickLogger"] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self.logger = logging.getLogger("tick")
        self.logger.setLevel(logging.DEBUG)
        self._setup_handlers()
    
    def _setup_handlers(self):
        """设置日志处理器"""
        config = get_config()
        
        # 清除已有处理器
        self.logger.handlers = []
        
        # 1. 控制台处理器 (Rich)
        console_handler = RichHandler(
            rich_tracebacks=True,
            markup=True,
            show_time=True,
            show_path=False
        )
        console_handler.setLevel(logging.INFO)
        console_format = logging.Formatter(
            "%(message)s",
            datefmt="[%X]"
        )
        console_handler.setFormatter(console_format)
        self.logger.addHandler(console_handler)

        self._setup_file_handlers()

    def _setup_file_handlers(self):
        """设置文件日志处理器，失败时降级为仅控制台日志"""
        log_dir = self._get_log_dir()
        file_format = logging.Formatter(
            "%(asctime)s | %(levelname)-8s | %(name)s | %(filename)s:%(lineno)d | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )

        try:
            log_dir.mkdir(parents=True, exist_ok=True)

            log_file = log_dir / f"tick_{datetime.now():%Y%m%d}.log"
            file_handler = RotatingFileHandler(
                log_file,
                maxBytes=10*1024*1024,  # 10MB
                backupCount=5,
                encoding="utf-8"
            )
            file_handler.setLevel(logging.DEBUG)
            file_handler.setFormatter(file_format)
            self.logger.addHandler(file_handler)

            error_file = log_dir / f"tick_error_{datetime.now():%Y%m%d}.log"
            error_handler = RotatingFileHandler(
                error_file,
                maxBytes=10*1024*1024,
                backupCount=5,
                encoding="utf-8"
            )
            error_handler.setLevel(logging.ERROR)
            error_handler.setFormatter(file_format)
            self.logger.addHandler(error_handler)
        except OSError as exc:
            self.logger.warning(f"日志目录不可写，已降级为仅控制台日志: {exc}")
    
    def _get_log_dir(self) -> Path:
        """获取日志目录"""
        if sys.platform == "win32":
            log_dir = Path.home() / "AppData" / "Local" / "tick" / "logs"
        else:
            log_dir = Path.home() / ".local" / "share" / "tick" / "logs"
        return log_dir
    
    def get_logger(self, name: Optional[str] = None) -> logging.Logger:
        """获取日志记录器"""
        if name:
            return self.logger.getChild(name)
        return self.logger
    
    def set_level(self, level: int):
        """设置日志级别"""
        self.logger.setLevel(level)
    
    def debug(self, msg: str, *args, **kwargs):
        self.logger.debug(msg, *args, **kwargs)
    
    def info(self, msg: str, *args, **kwargs):
        self.logger.info(msg, *args, **kwargs)
    
    def warning(self, msg: str, *args, **kwargs):
        self.logger.warning(msg, *args, **kwargs)
    
    def error(self, msg: str, *args, **kwargs):
        self.logger.error(msg, *args, **kwargs)
    
    def critical(self, msg: str, *args, **kwargs):
        self.logger.critical(msg, *args, **kwargs)


# 全局日志实例
_logger: Optional[TickLogger] = None


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """获取日志记录器"""
    global _logger
    if _logger is None:
        _logger = TickLogger()
    return _logger.get_logger(name)


# 便捷的日志函数
def log_fetch_start(symbol: str, source: str, **kwargs):
    """记录开始下载日志"""
    logger = get_logger("fetch")
    logger.info(f"开始下载 [cyan]{symbol}[/] 从 [green]{source}[/]")
    logger.debug(f"参数: {kwargs}")


def log_fetch_success(symbol: str, rows: int, duration: float):
    """记录下载成功日志"""
    logger = get_logger("fetch")
    logger.info(f"✅ {symbol} 下载成功: {rows} 行, 耗时 {duration:.2f}s")


def log_fetch_error(symbol: str, error: str, source: str):
    """记录下载失败日志"""
    logger = get_logger("fetch")
    logger.error(f"❌ {symbol} 下载失败: {error} (源: {source})")


def log_cache_hit(symbol: str, key: str):
    """记录缓存命中"""
    logger = get_logger("cache")
    logger.debug(f"💾 缓存命中: {symbol} ({key})")


def log_cache_miss(symbol: str, key: str):
    """记录缓存未命中"""
    logger = get_logger("cache")
    logger.debug(f"💨 缓存未命中: {symbol} ({key})")
