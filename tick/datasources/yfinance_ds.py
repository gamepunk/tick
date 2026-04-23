"""
Yahoo Finance 数据源
"""

import time
from typing import Any, Dict, Optional

import pandas as pd

from tick.core.logger import (
    get_logger,
    log_fetch_error,
    log_fetch_start,
    log_fetch_success,
)
from tick.core.models import FetchConfig, FetchResult, Symbol
from tick.datasources.base import BaseDataSource, register_datasource

try:
    import yfinance as yf
except ImportError:
    yf = None

try:
    import requests
except ImportError:
    requests = None


@register_datasource("yfinance")
class YFinanceDataSource(BaseDataSource):
    """Yahoo Finance 数据源 - 支持美股、港股、国际期货和指数"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.timeout = self.config.get("timeout", 30)
        self.retries = self.config.get("retries", 3)
        self.logger = get_logger("yfinance")
        self._session = self._create_session()

    def _create_session(self) -> Any:
        """创建带有浏览器请求头的 Session，降低被 Yahoo 拒绝的概率"""
        if requests is None:
            return None
        session = requests.Session()
        ua = self.config.get(
            "user_agent",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        )
        session.headers.update({
            "User-Agent": ua,
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
        })
        return session

    def _reset_session(self) -> None:
        """重置 Session（遇到 Cookie/Crumb 问题时使用）"""
        if requests is not None:
            self._session = self._create_session()

    def fetch(self, config: FetchConfig) -> FetchResult:
        """获取数据"""
        start_time = time.time()

        if yf is None:
            error_msg = "请安装 yfinance: pip install yfinance"
            self.logger.error(error_msg)
            return FetchResult(
                symbol=config.symbol,
                success=False,
                error_message=error_msg,
            )

        symbol = config.symbol.normalized
        log_fetch_start(
            symbol,
            "yfinance",
            start=config.start,
            end=config.end,
            interval=config.interval,
        )

        last_error = None
        # 循环前初始化，避免所有 attempt 均抛异常时 df 未绑定
        df = pd.DataFrame()

        # 重试机制：所有异常均重试，限流时额外等待
        for attempt in range(self.retries):
            try:
                self.logger.debug(f"尝试 {attempt + 1}/{self.retries}: {symbol}")
                ticker = yf.Ticker(symbol, session=self._session)
                df = ticker.history(
                    start=config.start,
                    end=config.end,
                    interval=config.interval.value
                    if hasattr(config.interval, "value")
                    else config.interval,
                )

                if not df.empty:
                    break  # 成功拿到数据，退出循环

            except Exception as e:
                last_error = e
                err_str = str(e).lower()
                self.logger.warning(f"尝试 {attempt + 1} 失败: {e}")

                # Cookie / Crumb 验证失败时重置 session
                if "cookie" in err_str or "crumb" in err_str or "forbidden" in err_str or "unauthorized" in err_str:
                    self.logger.info("检测到 Cookie/Crumb 问题，重置 session 后重试...")
                    self._reset_session()
                    time.sleep(2 ** attempt)
                    continue

                if "Too Many Requests" in str(e) or "Rate limited" in str(e):
                    wait = 10 * (attempt + 1)
                    self.logger.info(f"限流，等待 {wait}s...")
                    time.sleep(wait)
                # 其他异常也继续重试，不提前退出

        # 所有尝试均以异常结束
        if last_error is not None and df.empty:
            duration = time.time() - start_time
            log_fetch_error(symbol, f"多次重试后失败: {last_error}", "yfinance")
            return FetchResult(
                symbol=config.symbol,
                success=False,
                error_message=f"yfinance 多次重试后失败: {last_error}",
                metadata={"duration": duration, "retries": self.retries},
            )

        # 所有尝试均返回空数据（无异常）
        if df.empty:
            duration = time.time() - start_time
            log_fetch_error(symbol, "无数据返回", "yfinance")
            return FetchResult(
                symbol=config.symbol,
                success=False,
                error_message=f"yfinance 未返回数据: {symbol}",
                metadata={"duration": duration},
            )

        # 数据处理
        df.index = pd.to_datetime(df.index).tz_localize(None)
        df.index.name = "date"
        df.columns = df.columns.str.lower()

        # 选择标准列
        standard_cols = ["open", "high", "low", "close", "volume"]
        available_cols = [c for c in standard_cols if c in df.columns]
        df = pd.DataFrame(df[available_cols])

        duration = time.time() - start_time
        log_fetch_success(symbol, len(df), duration)

        return FetchResult(
            symbol=config.symbol,
            data=df,
            success=True,
            metadata={"source": "yfinance", "rows": len(df), "duration": duration},
        )

    def validate_symbol(self, symbol: Symbol) -> bool:
        """验证品种代码"""
        s = symbol.normalized
        if s.startswith("^") or s.endswith(".HK") or "=F" in s:
            return True
        if s.isalpha():
            return True
        return False

    def search(self, query: str, limit: int = 10) -> list[Dict[str, str]]:
        """搜索品种（yfinance 暂不支持搜索）"""
        self.logger.debug(f"搜索: {query}")
        return []

    def get_info(self, symbol: Symbol) -> Optional[Dict[str, Any]]:
        """获取品种基本信息"""
        try:
            if yf is None:
                return None

            ticker = yf.Ticker(symbol.normalized, session=self._session)
            info = ticker.info

            return {
                "name": info.get("longName") or info.get("shortName"),
                "type": info.get("quoteType"),
                "market": info.get("market"),
                "currency": info.get("currency"),
                "price": info.get("regularMarketPrice"),
                "market_cap": info.get("marketCap"),
                "sector": info.get("sector"),
                "industry": info.get("industry"),
            }
        except Exception as e:
            self.logger.warning(f"获取信息失败: {e}")
            return None
