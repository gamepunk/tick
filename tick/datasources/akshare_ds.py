"""
AkShare 数据源 - A股、北交所、国内期货
"""
import time
from typing import Optional, Dict, Any
import pandas as pd
from tick.datasources.base import BaseDataSource, register_datasource
from tick.core.models import FetchConfig, FetchResult, Symbol
from tick.core.exceptions import FetchError


@register_datasource("akshare")
class AkShareDataSource(BaseDataSource):
    """AkShare 数据源 - 支持A股、北交所、国内期货"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.default_adjust = self.config.get("adjust", "qfq")
    
    def fetch(self, config: FetchConfig) -> FetchResult:
        """获取数据"""
        try:
            import akshare as ak
        except ImportError:
            return FetchResult(
                symbol=config.symbol,
                success=False,
                error_message="请安装 akshare: pip install akshare"
            )
        
        symbol = config.symbol.normalized
        raw_code = symbol[2:] if len(symbol) > 2 else symbol
        prefix = symbol[:2].lower() if len(symbol) > 2 else "sh"
        
        # 判断是否为期货
        if self._is_futures(symbol):
            return self._fetch_futures(ak, config, raw_code)
        
        # 判断是否为分时数据
        interval = config.interval.value if hasattr(config.interval, 'value') else config.interval
        if interval in ("1m", "5m", "15m", "30m", "60m"):
            return self._fetch_intraday(ak, config, raw_code, interval)
        
        # 日线数据
        return self._fetch_daily(ak, config, raw_code)
    
    def _is_futures(self, symbol: str) -> bool:
        """判断是否为期货代码"""
        s = symbol.upper()
        futures_codes = {"AU", "AG", "CU", "AL", "ZN", "PB", "NI", "SN", "RB", "HC", "I", "J", "JM", "SC", "TA", "MA", "PP", "L", "V", "EG", "EB", "PG", "RU", "BU", "FU", "SP", "C", "CS", "A", "M", "Y", "P", "OI", "RM", "SR", "CF", "CY", "FG", "SA", "UR", "PF", "AP", "CJ", "LH", "JD", "PK"}
        
        if s in futures_codes:
            return True
        if any(s.startswith(p) and any(c.isdigit() for c in s) for p in futures_codes):
            return True
        return False
    
    def _fetch_daily(self, ak, config: FetchConfig, raw_code: str) -> FetchResult:
        """获取日线数据"""
        try:
            df = ak.stock_zh_a_hist(
                symbol=raw_code,
                period="daily",
                start_date=config.start.replace("-", ""),
                end_date=config.end.replace("-", ""),
                adjust=config.adjust or self.default_adjust
            )
            
            if df.empty:
                # 尝试获取 ETF 数据
                prefix = config.symbol.normalized[:2].lower()
                df = ak.fund_etf_hist_sina(symbol=f"{prefix}{raw_code}")
        except Exception as e:
            return FetchResult(
                symbol=config.symbol,
                success=False,
                error_message=f"akshare 获取失败: {e}"
            )
        
        if df.empty:
            return FetchResult(
                symbol=config.symbol,
                success=False,
                error_message=f"akshare 未返回数据: {config.symbol.normalized}"
            )
        
        # 标准化列名
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
            metadata={"source": "akshare", "type": "daily", "rows": len(df)}
        )
    
    def _fetch_intraday(self, ak, config: FetchConfig, raw_code: str, interval: str) -> FetchResult:
        """获取分时数据"""
        INTRADAY_MAP = {"1m": "1", "5m": "5", "15m": "15", "30m": "30", "60m": "60"}
        period = INTRADAY_MAP.get(interval, "1")
        
        try:
            df = ak.stock_zh_a_hist_min_em(
                symbol=raw_code,
                start_date=f"{config.start} 09:30:00",
                end_date=f"{config.end} 15:00:00",
                period=period,
                adjust=config.adjust or self.default_adjust
            )
        except Exception as e:
            return FetchResult(
                symbol=config.symbol,
                success=False,
                error_message=f"akshare 分时数据获取失败: {e}"
            )
        
        if df.empty:
            return FetchResult(
                symbol=config.symbol,
                success=False,
                error_message=f"akshare 分时数据为空"
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
        
        # 过滤日期
        df = df[df.index >= pd.Timestamp(config.start)]
        df = df[df.index <= pd.Timestamp(config.end)]
        
        return FetchResult(
            symbol=config.symbol,
            data=df,
            success=True,
            metadata={"source": "akshare", "type": "intraday", "rows": len(df)}
        )
    
    def _fetch_futures(self, ak, config: FetchConfig, symbol: str) -> FetchResult:
        """获取期货数据"""
        try:
            sym_upper = symbol.upper()
            start_fmt = config.start.replace("-", "")
            end_fmt = config.end.replace("-", "")
            
            try:
                df = ak.futures_main_sina(
                    symbol=f"{sym_upper}0",
                    start_date=start_fmt,
                    end_date=end_fmt
                )
            except Exception:
                df = ak.futures_zh_daily_sina(symbol=sym_upper)
            
            if df.empty:
                return FetchResult(
                    symbol=config.symbol,
                    success=False,
                    error_message=f"akshare 期货数据为空: {symbol}"
                )
            
            col_map = {
                "日期": "date", "date": "date",
                "开盘价": "open", "open": "open",
                "最高价": "high", "high": "high",
                "最低价": "low", "low": "low",
                "收盘价": "close", "close": "close",
                "成交量": "volume", "volume": "volume",
            }
            df = df.rename(columns={k: v for k, v in col_map.items() if k in df.columns})
            df["date"] = pd.to_datetime(df["date"])
            df = df.set_index("date")
            
            return FetchResult(
                symbol=config.symbol,
                data=df,
                success=True,
                metadata={"source": "akshare", "type": "futures", "rows": len(df)}
            )
            
        except Exception as e:
            return FetchResult(
                symbol=config.symbol,
                success=False,
                error_message=f"akshare 期货获取失败: {e}"
            )
    
    def validate_symbol(self, symbol: Symbol) -> bool:
        """验证品种代码"""
        s = symbol.normalized
        # A股/北交所代码格式
        if s.startswith(("SH", "SZ", "BJ")) and len(s) >= 6:
            return True
        # 期货代码
        if self._is_futures(s):
            return True
        return False
    
    def search(self, query: str, limit: int = 10) -> list[Dict[str, str]]:
        """搜索A股品种"""
        try:
            import akshare as ak
            
            # 获取A股列表
            df = ak.stock_info_a_code_name()
            
            # 模糊匹配
            mask = df["name"].str.contains(query, case=False, na=False) | \
                   df["code"].str.contains(query, case=False, na=False)
            results = df[mask].head(limit)
            
            return [
                {
                    "symbol": f"sh{row['code']}" if row['code'].startswith('6') else f"sz{row['code']}",
                    "name": row["name"],
                    "type": "stock"
                }
                for _, row in results.iterrows()
            ]
        except Exception:
            return []
