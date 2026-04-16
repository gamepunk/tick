"""
CCXT 数据源 - 加密货币
"""

import time
from typing import Any, Dict, Optional

import pandas as pd

from tick.core.models import (
    CCXT_EXCHANGES,
    EXCHANGE_QUOTE,
    FetchConfig,
    FetchResult,
    Symbol,
)
from tick.datasources.base import BaseDataSource, register_datasource


@register_datasource("ccxt")
class CCXTDataSource(BaseDataSource):
    """CCXT 数据源 - 支持加密货币"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.default_exchange = self.config.get("default_exchange", "binance")
        self.rate_limit = self.config.get("rate_limit", 1.0)

    def fetch(self, config: FetchConfig) -> FetchResult:
        """获取数据"""
        if not config.start or not config.end:
            return FetchResult(
                symbol=config.symbol,
                success=False,
                error_message="start / end 日期不能为空",
            )

        try:
            import ccxt
        except ImportError:
            return FetchResult(
                symbol=config.symbol,
                success=False,
                error_message="请安装 ccxt: pip install ccxt",
            )

        exchange_id = config.exchange or self.default_exchange
        if exchange_id not in CCXT_EXCHANGES:
            return FetchResult(
                symbol=config.symbol,
                success=False,
                error_message=f"不支持的交易所: {exchange_id}",
            )

        # 转换 symbol 格式
        ccxt_symbol = self._to_ccxt_symbol(config.symbol.normalized, exchange_id)

        # 初始化交易所
        exchange = getattr(ccxt, exchange_id)(
            {
                "enableRateLimit": self.config.get("enableRateLimit", True),
            }
        )

        # 转换时间周期
        interval_map = {
            "1m": "1m",
            "5m": "5m",
            "15m": "15m",
            "30m": "30m",
            "60m": "1h",
            "1d": "1d",
            "1wk": "1w",
            "1mo": "1M",
        }
        timeframe = interval_map.get(
            config.interval.value
            if hasattr(config.interval, "value")
            else config.interval,
            "1d",
        )

        # 获取数据
        try:
            since = exchange.parse8601(f"{config.start}T00:00:00Z")
            end_ts = exchange.parse8601(f"{config.end}T23:59:59Z")

            all_ohlcv = []
            while since < end_ts:
                ohlcv = exchange.fetch_ohlcv(
                    ccxt_symbol, timeframe=timeframe, since=since, limit=1000
                )
                if not ohlcv:
                    break
                all_ohlcv.extend(ohlcv)
                since = ohlcv[-1][0] + 1
                time.sleep(0.1)

            if not all_ohlcv:
                return FetchResult(
                    symbol=config.symbol,
                    success=False,
                    error_message=f"ccxt ({exchange_id}) 未返回数据: {ccxt_symbol}",
                )

            df = pd.DataFrame(
                all_ohlcv,
                columns=["timestamp", "open", "high", "low", "close", "volume"],
            )
            df["date"] = pd.to_datetime(df["timestamp"], unit="ms")
            df = pd.DataFrame(df.set_index("date").drop(columns=["timestamp"]))
            end_dt = pd.Timestamp(config.end) + pd.Timedelta(days=1)
            df = pd.DataFrame(df[df.index < end_dt])

            metadata = {
                "source": "ccxt",
                "exchange": exchange_id,
                "symbol": ccxt_symbol,
                "rows": len(df),
            }

            # 检查数据是否覆盖请求的起始日期
            if not df.empty:
                earliest = df.index[0]
                requested_start = pd.Timestamp(config.start)
                if earliest > requested_start:
                    metadata["warning"] = (
                        f"{exchange_id} API 仅返回最近 {len(df)} 条数据，"
                        f"最早日期为 {earliest.date()}，未覆盖请求的 {config.start}"
                    )

            return FetchResult(
                symbol=config.symbol,
                data=df,
                success=True,
                metadata=metadata,
            )

        except Exception as e:
            return FetchResult(
                symbol=config.symbol, success=False, error_message=f"ccxt 获取失败: {e}"
            )

    def _to_ccxt_symbol(self, symbol: str, exchange_id: str) -> str:
        """将 tick symbol 转换为 ccxt 格式"""
        quote = EXCHANGE_QUOTE.get(exchange_id, "USDT")

        # 提取 base
        s = symbol.upper()
        if s.endswith("-USD") or s.endswith("-USDT"):
            base = s.rsplit("-", 1)[0]
        else:
            base = s

        return f"{base}/{quote}"

    def validate_symbol(self, symbol: Symbol) -> bool:
        """验证品种代码"""
        s = symbol.normalized.upper()
        # 加密货币格式
        if s.endswith("-USD") or s.endswith("-USDT"):
            return True
        # 常见加密货币代码
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
            return True
        return False

    def search(self, query: str, limit: int = 10) -> list[Dict[str, str]]:
        """搜索加密货币（简化实现）"""
        # 返回一些主流币种
        popular = [
            {"symbol": "BTC-USD", "name": "比特币", "type": "crypto"},
            {"symbol": "ETH-USD", "name": "以太坊", "type": "crypto"},
            {"symbol": "SOL-USD", "name": "Solana", "type": "crypto"},
            {"symbol": "BNB-USD", "name": "币安币", "type": "crypto"},
            {"symbol": "DOGE-USD", "name": "狗狗币", "type": "crypto"},
            {"symbol": "XRP-USD", "name": "瑞波币", "type": "crypto"},
        ]

        query = query.upper()
        results = [
            p for p in popular if query in p["symbol"] or query in p["name"].upper()
        ]
        return results[:limit]
