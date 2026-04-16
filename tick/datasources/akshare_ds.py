"""
AkShare 数据源 - A股、北交所、国内期货
"""

from typing import Any, Dict, Optional

import pandas as pd

from tick.core.models import FetchConfig, FetchResult, Symbol
from tick.datasources.base import BaseDataSource, register_datasource


@register_datasource("akshare")
class AkShareDataSource(BaseDataSource):
    """AkShare 数据源 - 支持A股、北交所、国内期货"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.default_adjust = self.config.get("adjust", "qfq")

    def fetch(self, config: FetchConfig) -> FetchResult:
        """获取数据"""
        # ── 前置校验 ────────────────────────────────────────────
        if not config.start or not config.end:
            return FetchResult(
                symbol=config.symbol,
                success=False,
                error_message="start / end 日期不能为空",
            )

        try:
            import akshare as ak
        except ImportError:
            return FetchResult(
                symbol=config.symbol,
                success=False,
                error_message="请安装 akshare: pip install akshare",
            )

        symbol = config.symbol.normalized
        raw_code = symbol[2:] if len(symbol) > 2 else symbol

        # 判断是否为期货
        if self._is_futures(symbol):
            return self._fetch_futures(ak, config, raw_code)

        # 判断是否为分时数据
        interval = (
            config.interval.value
            if hasattr(config.interval, "value")
            else config.interval
        )
        if interval in ("1m", "5m", "15m", "30m", "60m"):
            return self._fetch_intraday(ak, config, raw_code, interval)

        # 日线数据
        return self._fetch_daily(ak, config, raw_code)

    # ─────────────────────────────────────────
    # 辅助方法
    # ─────────────────────────────────────────

    def _is_futures(self, symbol: str) -> bool:
        """判断是否为期货代码"""
        s = symbol.upper()
        futures_prefixes = {
            "AU",
            "AG",
            "CU",
            "AL",
            "ZN",
            "PB",
            "NI",
            "SN",
            "RB",
            "HC",
            "I",
            "J",
            "JM",
            "SC",
            "TA",
            "MA",
            "PP",
            "L",
            "V",
            "EG",
            "EB",
            "PG",
            "RU",
            "BU",
            "FU",
            "SP",
            "C",
            "CS",
            "A",
            "M",
            "Y",
            "P",
            "OI",
            "RM",
            "SR",
            "CF",
            "CY",
            "FG",
            "SA",
            "UR",
            "PF",
            "AP",
            "CJ",
            "LH",
            "JD",
            "PK",
        }
        if s in futures_prefixes:
            return True
        if any(
            s.startswith(p) and any(c.isdigit() for c in s) for p in futures_prefixes
        ):
            return True
        return False

    def _fetch_daily(self, ak, config: FetchConfig, raw_code: str) -> FetchResult:
        """获取日线数据"""
        assert config.start and config.end  # 已在 fetch() 顶部校验

        try:
            df = ak.stock_zh_a_hist(
                symbol=raw_code,
                period="daily",
                start_date=config.start.replace("-", ""),
                end_date=config.end.replace("-", ""),
                adjust=config.adjust or self.default_adjust,
            )

            if df.empty:
                # 尝试作为 ETF 获取
                prefix = config.symbol.normalized[:2].lower()
                df = ak.fund_etf_hist_sina(symbol=f"{prefix}{raw_code}")
        except Exception as e:
            return FetchResult(
                symbol=config.symbol,
                success=False,
                error_message=f"akshare 获取失败: {e}",
            )

        if df.empty:
            return FetchResult(
                symbol=config.symbol,
                success=False,
                error_message=f"akshare 未返回数据: {config.symbol.normalized}",
            )

        col_map = {
            "日期": "date",
            "开盘": "open",
            "最高": "high",
            "最低": "low",
            "收盘": "close",
            "成交量": "volume",
            "成交额": "amount",
            "涨跌幅": "pct_change",
        }
        df = df.rename(columns={k: v for k, v in col_map.items() if k in df.columns})
        df["date"] = pd.to_datetime(df["date"])
        df = df.set_index("date")

        return FetchResult(
            symbol=config.symbol,
            data=df,
            success=True,
            metadata={"source": "akshare", "type": "daily", "rows": len(df)},
        )

    def _fetch_intraday(
        self, ak, config: FetchConfig, raw_code: str, interval: str
    ) -> FetchResult:
        """获取分时数据"""
        assert config.start and config.end

        INTRADAY_MAP = {"1m": "1", "5m": "5", "15m": "15", "30m": "30", "60m": "60"}
        period = INTRADAY_MAP.get(interval, "1")

        try:
            df = ak.stock_zh_a_hist_min_em(
                symbol=raw_code,
                start_date=f"{config.start} 09:30:00",
                end_date=f"{config.end} 15:00:00",
                period=period,
                adjust=config.adjust or self.default_adjust,
            )
        except Exception as e:
            return FetchResult(
                symbol=config.symbol,
                success=False,
                error_message=f"akshare 分时数据获取失败: {e}",
            )

        if df.empty:
            return FetchResult(
                symbol=config.symbol,
                success=False,
                error_message="akshare 分时数据为空",
            )

        col_map = {
            "时间": "date",
            "开盘": "open",
            "最高": "high",
            "最低": "low",
            "收盘": "close",
            "成交量": "volume",
            "涨跌幅": "pct_change",
        }
        df = df.rename(columns={k: v for k, v in col_map.items() if k in df.columns})
        df["date"] = pd.to_datetime(df["date"])
        df = df.set_index("date")

        # 过滤日期范围
        # 注意：结束边界取次日 00:00，确保结束日当天数据不被截断
        start_dt = pd.Timestamp(config.start)
        end_dt = pd.Timestamp(config.end) + pd.Timedelta(days=1)
        df = df[(df.index >= start_dt) & (df.index < end_dt)]

        return FetchResult(
            symbol=config.symbol,
            data=df,
            success=True,
            metadata={"source": "akshare", "type": "intraday", "rows": len(df)},
        )

    def _fetch_futures(self, ak, config: FetchConfig, symbol: str) -> FetchResult:
        """获取期货数据"""
        assert config.start and config.end

        try:
            sym_upper = symbol.upper()
            start_fmt = config.start.replace("-", "")
            end_fmt = config.end.replace("-", "")

            try:
                df = ak.futures_main_sina(
                    symbol=f"{sym_upper}0",
                    start_date=start_fmt,
                    end_date=end_fmt,
                )
            except Exception:
                df = ak.futures_zh_daily_sina(symbol=sym_upper)

            if df.empty:
                return FetchResult(
                    symbol=config.symbol,
                    success=False,
                    error_message=f"akshare 期货数据为空: {symbol}",
                )

            col_map = {
                "日期": "date",
                "date": "date",
                "开盘价": "open",
                "open": "open",
                "最高价": "high",
                "high": "high",
                "最低价": "low",
                "low": "low",
                "收盘价": "close",
                "close": "close",
                "成交量": "volume",
                "volume": "volume",
            }
            df = df.rename(
                columns={k: v for k, v in col_map.items() if k in df.columns}
            )
            df["date"] = pd.to_datetime(df["date"])
            df = df.set_index("date")

            return FetchResult(
                symbol=config.symbol,
                data=df,
                success=True,
                metadata={"source": "akshare", "type": "futures", "rows": len(df)},
            )

        except Exception as e:
            return FetchResult(
                symbol=config.symbol,
                success=False,
                error_message=f"akshare 期货获取失败: {e}",
            )

    # ─────────────────────────────────────────
    # validate / search
    # ─────────────────────────────────────────

    def validate_symbol(self, symbol: Symbol) -> bool:
        """验证品种代码"""
        s = symbol.normalized
        if s.startswith(("SH", "SZ", "BJ")) and len(s) >= 6:
            return True
        if self._is_futures(s):
            return True
        return False

    def search(self, query: str, limit: int = 10) -> list[Dict[str, str]]:
        """搜索 A 股品种"""
        try:
            import akshare as ak

            df = ak.stock_info_a_code_name()

            mask = df["name"].str.contains(query, case=False, na=False) | df[
                "code"
            ].str.contains(query, case=False, na=False)
            matched = df[mask].head(limit)

            results: list[Dict[str, str]] = []
            for _, row in matched.iterrows():
                code = str(row["code"])
                market = "sh" if code.startswith("6") else "sz"
                results.append(
                    {
                        "symbol": f"{market}{code}",
                        "name": str(row["name"]),
                        "type": "stock",
                        "market": market.upper(),
                    }
                )
            return results
        except Exception:
            return []
