"""
数据源抽象基类
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from tick.core.exceptions import FetchError
from tick.core.models import FetchConfig, FetchResult, Symbol


class BaseDataSource(ABC):
    """数据源基类"""

    name: str = "base"

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self._client = None

    @abstractmethod
    def fetch(self, config: FetchConfig) -> FetchResult:
        """
        获取数据

        Args:
            config: 获取配置

        Returns:
            FetchResult: 获取结果
        """
        pass

    @abstractmethod
    def validate_symbol(self, symbol: Symbol) -> bool:
        """验证品种代码是否支持"""
        pass

    @abstractmethod
    def search(self, query: str, limit: int = 10) -> list[Dict[str, str]]:
        """
        搜索品种

        Args:
            query: 搜索关键词
            limit: 返回数量限制

        Returns:
            搜索结果列表
        """
        pass

    def get_info(self, symbol: Symbol) -> Optional[Dict[str, Any]]:
        """获取品种基本信息（可选实现）"""
        return None

    def _handle_error(self, error: Exception, config: FetchConfig) -> FetchError:
        """统一错误处理"""
        if "Rate limit" in str(error) or "Too Many Requests" in str(error):
            return FetchError(
                f"请求限流: {error}", symbol=config.symbol.normalized, source=self.name
            )
        elif "No data" in str(error) or "Empty" in str(error):
            return FetchError(
                f"无数据返回: {error}",
                symbol=config.symbol.normalized,
                source=self.name,
            )
        else:
            return FetchError(
                f"获取失败: {error}", symbol=config.symbol.normalized, source=self.name
            )


class DataSourceRegistry:
    """数据源注册表"""

    _sources: Dict[str, type[BaseDataSource]] = {}

    @classmethod
    def register(cls, name: str, source_class: type[BaseDataSource]):
        """注册数据源"""
        cls._sources[name] = source_class

    @classmethod
    def get(cls, name: str) -> Optional[type[BaseDataSource]]:
        """获取数据源类"""
        return cls._sources.get(name)

    @classmethod
    def list_sources(cls) -> list[str]:
        """列出所有已注册的数据源"""
        return list(cls._sources.keys())

    @classmethod
    def create(
        cls, name: str, config: Optional[Dict] = None
    ) -> Optional[BaseDataSource]:
        """创建数据源实例"""
        source_class = cls.get(name)
        if source_class:
            return source_class(config)
        return None


def register_datasource(name: str):
    """装饰器：注册数据源"""

    def decorator(cls: type[BaseDataSource]):
        DataSourceRegistry.register(name, cls)
        cls.name = name
        return cls

    return decorator
