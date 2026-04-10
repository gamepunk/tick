"""
配置管理系统
支持 YAML 配置文件和命令行参数合并
"""
import os
from pathlib import Path
from typing import Optional, Dict, Any
from dataclasses import dataclass, field, asdict
import yaml


@dataclass
class CacheConfig:
    """缓存配置"""
    enabled: bool = True
    ttl: int = 3600  # 秒
    max_size: int = 100  # MB
    directory: Optional[str] = None


@dataclass
class DisplayConfig:
    """显示配置"""
    color: bool = True
    progress_bar: bool = True
    table_style: str = "blue"
    verbose: bool = False


@dataclass
class DatasourceConfig:
    """数据源配置"""
    yfinance: Dict[str, Any] = field(default_factory=lambda: {
        "timeout": 30,
        "retries": 3,
    })
    akshare: Dict[str, Any] = field(default_factory=lambda: {
        "adjust": "qfq",
    })
    ccxt: Dict[str, Any] = field(default_factory=lambda: {
        "default_exchange": "binance",
        "rate_limit": 1.0,
        "enableRateLimit": True,
    })


@dataclass
class AppConfig:
    """应用主配置"""
    # 默认输出
    default_output_dir: str = "~/Desktop"
    default_format: str = "csv"
    default_interval: str = "1d"
    default_start: str = "1y"  # 1年前
    
    # 子配置
    cache: CacheConfig = field(default_factory=CacheConfig)
    display: DisplayConfig = field(default_factory=DisplayConfig)
    datasource: DatasourceConfig = field(default_factory=DatasourceConfig)
    
    # 自定义选项
    custom: Dict[str, Any] = field(default_factory=dict)
    
    @classmethod
    def load(cls, config_path: Optional[str] = None) -> "AppConfig":
        """从文件加载配置"""
        if config_path is None:
            config_path = cls._get_default_config_path()
        
        if not config_path or not Path(config_path).exists():
            return cls()  # 返回默认配置
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
            return cls._from_dict(data or {})
        except Exception as e:
            print(f"[yellow]警告: 加载配置文件失败 ({e})，使用默认配置[/]")
            return cls()
    
    def save(self, config_path: Optional[str] = None) -> None:
        """保存配置到文件"""
        if config_path is None:
            config_path = self._get_default_config_path()
        
        if not config_path:
            return
        
        path = Path(config_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(path, 'w', encoding='utf-8') as f:
            yaml.dump(asdict(self), f, default_flow_style=False, allow_unicode=True)
    
    @staticmethod
    def _get_default_config_path() -> Optional[str]:
        """获取默认配置文件路径"""
        if os.name == 'nt':  # Windows
            config_dir = Path(os.environ.get('APPDATA', '~')) / 'tick'
        else:  # macOS/Linux
            config_dir = Path.home() / '.config' / 'tick'
        
        return str(config_dir / 'config.yaml')
    
    @classmethod
    def _from_dict(cls, data: Dict[str, Any]) -> "AppConfig":
        """从字典创建配置对象"""
        # 处理嵌套配置
        cache_data = data.pop('cache', {})
        display_data = data.pop('display', {})
        datasource_data = data.pop('datasource', {})
        
        return cls(
            **{k: v for k, v in data.items() if k in cls.__dataclass_fields__},
            cache=CacheConfig(**cache_data),
            display=DisplayConfig(**display_data),
            datasource=DatasourceConfig(**datasource_data),
        )
    
    def get_cache_dir(self) -> Path:
        """获取缓存目录"""
        if self.cache.directory:
            return Path(self.cache.directory).expanduser()
        
        if os.name == 'nt':
            base = Path(os.environ.get('LOCALAPPDATA', '~')) / 'tick' / 'cache'
        else:
            base = Path.home() / '.cache' / 'tick'
        
        base.mkdir(parents=True, exist_ok=True)
        return base
    
    def get_output_dir(self) -> Path:
        """获取默认输出目录"""
        path = Path(self.default_output_dir).expanduser()
        path.mkdir(parents=True, exist_ok=True)
        return path


# 全局配置实例
_config: Optional[AppConfig] = None


def get_config() -> AppConfig:
    """获取全局配置"""
    global _config
    if _config is None:
        _config = AppConfig.load()
    return _config


def set_config(config: AppConfig) -> None:
    """设置全局配置"""
    global _config
    _config = config


def init_config() -> None:
    """初始化配置文件（如果不存在）"""
    config_path = AppConfig._get_default_config_path()
    if config_path and not Path(config_path).exists():
        config = AppConfig()
        config.save(config_path)
        print(f"[dim]已创建默认配置文件: {config_path}[/]")
