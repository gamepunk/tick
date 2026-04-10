"""
Yahoo Finance 数据源
"""
import time
import logging
from typing import Optional, Dict, Any
import pandas as pd
from tick.datasources.base import BaseDataSource, register_datasource
from tick.core.models import FetchConfig, FetchResult, Symbol
from tick.core.exceptions import FetchError
from tick.core.logger import log_fetch_start, log_fetch_success, log_fetch_error, get_logger


@register_datasource("yfinance")
class YFinanceDataSource(BaseDataSource):
    """Yahoo Finance 数据源 - 支持美股、港股、国际期货和指数"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.timeout = self.config.get("timeout", 30)
        self.retries = self.config.get("retries", 3)
        self.logger = get_logger("yfinance")
    
    def fetch(self, config: FetchConfig) -> FetchResult:
        """获取数据"""
        start_time = time.time()
        
        try:
            import yfinance as yf
        except ImportError:
            error_msg = "请安装 yfinance: pip install yfinance"
            self.logger.error(error_msg)
            return FetchResult(
                symbol=config.symbol,
                success=False,
                error_message=error_msg
            )
        
        symbol = config.symbol.normalized
        log_fetch_start(symbol, "yfinance", 
                       start=config.start, end=config.end, 
                       interval=config.interval)
        
        last_error = None
        
        # 重试机制
        for attempt in range(self.retries):
            try:
                self.logger.debug(f"尝试 {attempt + 1}/{self.retries}: {symbol}")
                ticker = yf.Ticker(symbol)
                df = ticker.history(
                    start=config.start,
                    end=config.end,
                    interval=config.interval.value if hasattr(config.interval, 'value') else config.interval
                )
                
                if not df.empty:
                    break
                    
            except Exception as e:
                last_error = e
                self.logger.warning(f"尝试 {attempt + 1} 失败: {e}")
                if "Too Many Requests" in str(e) or "Rate limited" in str(e):
                    wait = 10 * (attempt + 1)
                    self.logger.info(f"限流，等待 {wait}s...")
                    time.sleep(wait)
                else:
                    break
        else:
            duration = time.time() - start_time
            log_fetch_error(symbol, f"多次重试后失败: {last_error}", "yfinance")
            return FetchResult(
                symbol=config.symbol,
                success=False,
                error_message=f"yfinance 多次重试后失败: {last_error}",
                metadata={"duration": duration, "retries": self.retries}
            )
        
        if df.empty:
            duration = time.time() - start_time
            log_fetch_error(symbol, "无数据返回", "yfinance")
            return FetchResult(
                symbol=config.symbol,
                success=False,
                error_message=f"yfinance 未返回数据: {symbol}",
                metadata={"duration": duration}
            )
        
        # 数据处理
        df.index = pd.to_datetime(df.index).tz_localize(None)
        df.index.name = "date"
        df.columns = df.columns.str.lower()
        
        # 选择标准列
        standard_cols = ["open", "high", "low", "close", "volume"]
        available_cols = [c for c in standard_cols if c in df.columns]
        df = df[available_cols]
        
        duration = time.time() - start_time
        log_fetch_success(symbol, len(df), duration)
        
        return FetchResult(
            symbol=config.symbol,
            data=df,
            success=True,
            metadata={"source": "yfinance", "rows": len(df), "duration": duration}
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
        """搜索品种"""
        self.logger.debug(f"搜索: {query}")
        return []
    
    def get_info(self, symbol: Symbol) -> Optional[Dict[str, Any]]:
        """获取品种基本信息"""
        try:
            import yfinance as yf
            ticker = yf.Ticker(symbol.normalized)
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
