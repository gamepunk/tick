"""
数据源路由器 - 根据 symbol 自动选择合适的数据源
"""

from typing import Optional

from tick.core.models import AssetType, Symbol
from tick.datasources import (  # noqa: F401 — 触发 @register_datasource 注册，勿删
    akshare_ds,
    ccxt_ds,
    yfinance_ds,
)
from tick.datasources.base import BaseDataSource, DataSourceRegistry


class DataSourceRouter:
    """数据源路由器"""

    @classmethod
    def detect_market(cls, symbol: Symbol) -> str:
        """
        自动识别市场来源

        Returns:
            数据源名称: yfinance, akshare, ccxt
        """
        s = symbol.normalized.upper()
        asset = symbol.asset_type

        # 如果指定了资产类型，优先根据类型判断
        if asset == AssetType.CRYPTO:
            return "ccxt"

        if asset == AssetType.FUTURES:
            # 国内期货
            if s in ("AU", "AG", "CU", "RB", "HC") or (
                any(
                    s.startswith(p)
                    for p in (
                        "AU",
                        "AG",
                        "CU",
                        "AL",
                        "RB",
                        "HC",
                        "SC",
                        "NI",
                        "ZN",
                        "PB",
                    )
                )
                and any(c.isdigit() for c in s)
            ):
                return "akshare"
            return "yfinance"  # 国际期货

        if asset in (AssetType.STOCK, AssetType.INDEX, AssetType.FUND):
            # A股/北交所
            if s.startswith(("SH", "SZ", "BJ")):
                return "akshare"
            return "yfinance"

        # 自动识别逻辑
        # 北交所/A股
        if s.startswith(("SH", "SZ", "BJ")):
            return "akshare"

        # 国内期货
        if s in ("AU", "AG", "CU", "RB", "HC") or (
            any(
                s.startswith(p)
                for p in ("AU", "AG", "CU", "AL", "RB", "HC", "SC", "NI", "ZN", "PB")
            )
            and any(c.isdigit() for c in s)
        ):
            return "akshare"

        # 加密货币
        if s.endswith("-USD") or s.endswith("-USDT"):
            return "ccxt"

        # 加密货币代码
        crypto_codes = {
            "BTC",
            "ETH",
            "SOL",
            "BNB",
            "DOGE",
            "XRP",
            "ADA",
            "AVAX",
            "DOT",
            "MATIC",
        }
        if s in crypto_codes:
            return "ccxt"

        # 国际期货
        if "=F" in s:
            return "yfinance"

        # 港股或美股
        if s.endswith(".HK") or s.endswith(".SS") or s.endswith(".SZ"):
            return "yfinance"

        # 默认使用 yfinance
        return "yfinance"

    @classmethod
    def get_datasource(cls, symbol: Symbol) -> Optional[BaseDataSource]:
        """
        获取适合该 symbol 的数据源实例
        """
        source_name = cls.detect_market(symbol)
        return DataSourceRegistry.create(source_name)

    @classmethod
    def get_source_for_explicit(cls, source_name: str) -> Optional[BaseDataSource]:
        """
        根据显式指定的数据源名称获取实例
        """
        return DataSourceRegistry.create(source_name)
