"""
核心数据模型
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional

import pandas as pd


class AssetType(str, Enum):
    """资产类型枚举"""

    STOCK = "stock"
    INDEX = "index"
    FUTURES = "futures"
    FUND = "fund"
    CRYPTO = "crypto"

    @classmethod
    def choices(cls) -> list[str]:
        return [member.value for member in cls]


class DataSource(str, Enum):
    """数据源枚举"""

    YFINANCE = "yfinance"
    AKSHARE = "akshare"
    CCXT = "ccxt"


class Interval(str, Enum):
    """K线周期"""

    MIN1 = "1m"
    MIN5 = "5m"
    MIN15 = "15m"
    MIN30 = "30m"
    MIN60 = "60m"
    HOUR = "1h"
    DAY = "1d"
    WEEK = "1wk"
    MONTH = "1mo"


@dataclass
class Symbol:
    """品种代码模型"""

    raw: str  # 用户原始输入
    normalized: str  # 标准化后的代码
    asset_type: Optional[AssetType] = None
    market: Optional[str] = None  # 所属市场

    def __post_init__(self):
        self.raw = self.raw.strip().upper()
        self.normalized = self.normalized.strip().upper()


@dataclass
class FetchConfig:
    """数据获取配置"""

    symbol: Symbol
    start: Optional[str] = None
    end: Optional[str] = None
    interval: Interval = Interval.DAY
    adjust: str = "qfq"  # A股复权方式
    exchange: str = "binance"  # 加密货币交易所

    # 高级选项
    use_cache: bool = True
    cache_ttl: int = 3600  # 缓存有效期（秒）
    max_retries: int = 3
    timeout: int = 30


@dataclass
class FetchResult:
    """数据获取结果"""

    symbol: Symbol
    data: Optional[pd.DataFrame] = None
    success: bool = False
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    fetch_time: Optional[datetime] = None

    def __post_init__(self):
        if self.fetch_time is None:
            self.fetch_time = datetime.now()


@dataclass
class BatchConfig:
    """批量下载配置"""

    symbols: list[Symbol]
    output_dir: Optional[str] = None
    format: str = "csv"
    add_pct: bool = True
    workers: int = 4  # 并发数

    # 每个 symbol 的配置
    default_config: FetchConfig = field(
        default_factory=lambda: FetchConfig(symbol=Symbol(raw="", normalized=""))
    )


# 常量定义
ASSET_TYPE_NAMES = {
    AssetType.STOCK: "股票",
    AssetType.INDEX: "指数",
    AssetType.FUTURES: "期货",
    AssetType.FUND: "基金/ETF",
    AssetType.CRYPTO: "加密货币",
}

# 美股指数代码映射（自动添加 ^ 前缀）
US_INDEX_CODES = {
    "GSPC",
    "DJI",
    "IXIC",
    "VIX",
    "RUT",
    "FTSE",
    "N225",
    "HSI",
    "NYA",
    "XAX",
    "FCHI",
    "GDAXI",
    "AEX",
    "IBEX",
    "SSMI",
    "NSEI",
    "KS11",
    "SSEC",
    "SZSC",
    "BSESN",
    "JKSE",
    "SET",
    "KLSE",
    "PCOMP",
    "TWII",
    "NZ50",
    "ASX",
    "ATX",
    "BFX",
    "OMX",
    "IMOEX",
    "RTSI",
    "TASI",
    "EGX30",
    "MERV",
    "MXX",
    "BVSP",
    "IPSA",
    "COLCAP",
    "IGBC",
}

# CCXT 支持的交易所
CCXT_EXCHANGES = [
    "binance",
    "okx",
    "bybit",
    "kraken",
    "bitstamp",
    "bitfinex",
    "coinbase",
    "gateio",
    "kucoin",
    "huobi",
    "mexc",
]

# 交易所计价货币
EXCHANGE_QUOTE = {
    "binance": "USDT",
    "okx": "USDT",
    "bybit": "USDT",
    "kraken": "USD",
    "bitstamp": "USD",
    "bitfinex": "USD",
    "coinbase": "USD",
    "gateio": "USDT",
    "kucoin": "USDT",
    "huobi": "USDT",
    "mexc": "USDT",
}
