"""
自定义异常类
"""


class TickError(Exception):
    """基础异常"""
    pass


class DataSourceError(TickError):
    """数据源错误"""
    pass


class FetchError(TickError):
    """数据获取错误"""
    def __init__(self, message: str, symbol: str = None, source: str = None):
        super().__init__(message)
        self.symbol = symbol
        self.source = source


class RateLimitError(FetchError):
    """限流错误"""
    pass


class ValidationError(TickError):
    """数据验证错误"""
    pass


class ConfigError(TickError):
    """配置错误"""
    pass


class SymbolError(TickError):
    """品种代码错误"""
    pass


class CacheError(TickError):
    """缓存错误"""
    pass
