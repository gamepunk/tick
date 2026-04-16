"""
测试数据源 fetch 方法（Mock 测试）
"""

from datetime import datetime
from unittest.mock import MagicMock, Mock, PropertyMock, call, patch

import pandas as pd
import pytest

from tick.core.models import AssetType, FetchConfig, Interval, Symbol
from tick.datasources.akshare_ds import AkShareDataSource
from tick.datasources.ccxt_ds import CCXTDataSource
from tick.datasources.yfinance_ds import YFinanceDataSource

# ─────────────────────────────────────────
# Fixtures
# ─────────────────────────────────────────


@pytest.fixture
def yfinance_source():
    """YFinanceDataSource fixture"""
    return YFinanceDataSource()


@pytest.fixture
def akshare_source():
    """AkShareDataSource fixture"""
    return AkShareDataSource()


@pytest.fixture
def ccxt_source():
    """CCXTDataSource fixture"""
    return CCXTDataSource()


@pytest.fixture
def aapl_symbol():
    """AAPL Symbol fixture"""
    return Symbol(raw="AAPL", normalized="AAPL", asset_type=AssetType.STOCK)


@pytest.fixture
def sh600519_symbol():
    """贵州茅台 Symbol fixture"""
    return Symbol(raw="sh600519", normalized="SH600519", asset_type=AssetType.STOCK)


@pytest.fixture
def btc_symbol():
    """BTC Symbol fixture"""
    return Symbol(raw="BTC-USD", normalized="BTC-USD", asset_type=AssetType.CRYPTO)


@pytest.fixture
def yfinance_config(aapl_symbol):
    """YFinance FetchConfig fixture"""
    return FetchConfig(
        symbol=aapl_symbol, start="2024-01-01", end="2024-01-31", interval=Interval.DAY
    )


@pytest.fixture
def akshare_daily_config(sh600519_symbol):
    """AkShare 日线 FetchConfig fixture"""
    return FetchConfig(
        symbol=sh600519_symbol,
        start="2024-01-01",
        end="2024-01-31",
        interval=Interval.DAY,
    )


@pytest.fixture
def akshare_intraday_config(sh600519_symbol):
    """AkShare 分时 FetchConfig fixture"""
    return FetchConfig(
        symbol=sh600519_symbol,
        start="2024-01-01",
        end="2024-01-05",
        interval=Interval.MIN5,
    )


@pytest.fixture
def ccxt_config(btc_symbol):
    """CCXT FetchConfig fixture"""
    return FetchConfig(
        symbol=btc_symbol,
        start="2024-01-01",
        end="2024-01-10",
        interval=Interval.DAY,
        exchange="binance",
    )


@pytest.fixture
def mock_yf_history_data():
    """模拟 yfinance history 返回数据"""
    dates = pd.date_range("2024-01-01", periods=10, freq="D", tz="UTC")
    return pd.DataFrame(
        {
            "Open": [
                100.0,
                101.0,
                102.0,
                103.0,
                104.0,
                105.0,
                106.0,
                107.0,
                108.0,
                109.0,
            ],
            "High": [
                110.0,
                111.0,
                112.0,
                113.0,
                114.0,
                115.0,
                116.0,
                117.0,
                118.0,
                119.0,
            ],
            "Low": [90.0, 91.0, 92.0, 93.0, 94.0, 95.0, 96.0, 97.0, 98.0, 99.0],
            "Close": [
                105.0,
                106.0,
                107.0,
                108.0,
                109.0,
                110.0,
                111.0,
                112.0,
                113.0,
                114.0,
            ],
            "Volume": [
                1000000,
                1100000,
                1200000,
                1300000,
                1400000,
                1500000,
                1600000,
                1700000,
                1800000,
                1900000,
            ],
        },
        index=dates,
    )


@pytest.fixture
def mock_akshare_daily_data():
    """模拟 akshare 日线返回数据"""
    return pd.DataFrame(
        {
            "日期": [
                "2024-01-01",
                "2024-01-02",
                "2024-01-03",
                "2024-01-04",
                "2024-01-05",
            ],
            "开盘": [100.0, 101.0, 102.0, 103.0, 104.0],
            "最高": [110.0, 111.0, 112.0, 113.0, 114.0],
            "最低": [90.0, 91.0, 92.0, 93.0, 94.0],
            "收盘": [105.0, 106.0, 107.0, 108.0, 109.0],
            "成交量": [1000000, 1100000, 1200000, 1300000, 1400000],
            "成交额": [100000000, 110000000, 120000000, 130000000, 140000000],
            "涨跌幅": [0.01, 0.02, -0.01, 0.015, -0.005],
        }
    )


@pytest.fixture
def mock_akshare_intraday_data():
    """模拟 akshare 分时返回数据"""
    return pd.DataFrame(
        {
            "时间": [
                "2024-01-01 09:30:00",
                "2024-01-01 10:00:00",
                "2024-01-01 10:30:00",
            ],
            "开盘": [100.0, 101.0, 102.0],
            "最高": [110.0, 111.0, 112.0],
            "最低": [90.0, 91.0, 92.0],
            "收盘": [105.0, 106.0, 107.0],
            "成交量": [100000, 110000, 120000],
            "涨跌幅": [0.01, 0.02, -0.01],
        }
    )


@pytest.fixture
def mock_akshare_futures_data():
    """模拟 akshare 期货返回数据"""
    return pd.DataFrame(
        {
            "日期": ["2024-01-01", "2024-01-02", "2024-01-03"],
            "开盘价": [500.0, 505.0, 502.0],
            "最高价": [510.0, 515.0, 512.0],
            "最低价": [490.0, 495.0, 492.0],
            "收盘价": [505.0, 510.0, 507.0],
            "成交量": [10000, 11000, 12000],
        }
    )


@pytest.fixture
def mock_ccxt_ohlcv_data():
    """模拟 ccxt OHLCV 返回数据"""
    # [timestamp, open, high, low, close, volume]
    return [
        [1704067200000, 42000.0, 43000.0, 41500.0, 42500.0, 1000.0],
        [1704153600000, 42500.0, 43500.0, 42000.0, 43000.0, 1200.0],
        [1704240000000, 43000.0, 44000.0, 42500.0, 43500.0, 1100.0],
        [1704326400000, 43500.0, 44500.0, 43000.0, 44000.0, 1300.0],
        [1704412800000, 44000.0, 45000.0, 43500.0, 44500.0, 1400.0],
    ]


# ─────────────────────────────────────────
# YFinanceDataSource Tests
# ─────────────────────────────────────────


class TestYFinanceDataSourceFetch:
    """测试 YFinanceDataSource.fetch() 方法"""

    @patch("tick.datasources.yfinance_ds.yf")
    def test_fetch_success(
        self, mock_yf, yfinance_source, yfinance_config, mock_yf_history_data
    ):
        """测试成功获取数据"""
        # Mock Ticker 和 history 方法
        mock_ticker = MagicMock()
        mock_ticker.history.return_value = mock_yf_history_data
        mock_yf.Ticker.return_value = mock_ticker

        result = yfinance_source.fetch(yfinance_config)

        assert result.success is True
        assert result.data is not None
        assert len(result.data) == 10
        assert "close" in result.data.columns
        assert "open" in result.data.columns
        assert "high" in result.data.columns
        assert "low" in result.data.columns
        assert "volume" in result.data.columns
        assert result.metadata["source"] == "yfinance"
        assert result.metadata["rows"] == 10

        # 验证 Ticker 被正确调用
        mock_yf.Ticker.assert_called_once_with("AAPL")
        mock_ticker.history.assert_called_once()

    @patch("tick.datasources.yfinance_ds.yf")
    def test_fetch_empty_data(self, mock_yf, yfinance_source, yfinance_config):
        """测试空数据返回"""
        mock_ticker = MagicMock()
        mock_ticker.history.return_value = pd.DataFrame()
        mock_yf.Ticker.return_value = mock_ticker

        result = yfinance_source.fetch(yfinance_config)

        assert result.success is False
        assert result.data is None
        assert "未返回数据" in result.error_message or "未" in result.error_message

    @patch("tick.datasources.yfinance_ds.yf", None)
    def test_fetch_yfinance_not_installed(self, yfinance_source, yfinance_config):
        """测试 yfinance 未安装的情况"""
        result = yfinance_source.fetch(yfinance_config)

        assert result.success is False
        assert "请安装 yfinance" in result.error_message

    @patch("tick.datasources.yfinance_ds.yf")
    def test_fetch_retry_mechanism(
        self, mock_yf, yfinance_config, mock_yf_history_data
    ):
        """测试重试机制"""
        # 创建一个自定义配置，使用更少的重试次数以加快测试
        source = YFinanceDataSource(config={"retries": 3})

        mock_ticker = MagicMock()
        # 前两次抛出异常，第三次成功
        mock_ticker.history.side_effect = [
            Exception("Network error"),
            Exception("Timeout"),
            mock_yf_history_data,
        ]
        mock_yf.Ticker.return_value = mock_ticker

        result = source.fetch(yfinance_config)

        # 应该成功，因为第三次成功了
        assert result.success is True
        assert result.data is not None
        # 验证被调用了 3 次
        assert mock_ticker.history.call_count == 3

    @patch("tick.datasources.yfinance_ds.yf")
    def test_fetch_retry_exhausted(self, mock_yf, yfinance_config):
        """测试重试次数耗尽"""
        source = YFinanceDataSource(config={"retries": 2})

        mock_ticker = MagicMock()
        # 总是抛出异常
        mock_ticker.history.side_effect = Exception("Persistent error")
        mock_yf.Ticker.return_value = mock_ticker

        result = source.fetch(yfinance_config)

        assert result.success is False
        assert "多次重试后失败" in result.error_message
        assert mock_ticker.history.call_count == 2

    @patch("tick.datasources.yfinance_ds.yf")
    def test_fetch_rate_limit(self, mock_yf, yfinance_config, mock_yf_history_data):
        """测试限流处理"""
        source = YFinanceDataSource(config={"retries": 2})

        mock_ticker = MagicMock()
        # 第一次限流，第二次成功
        mock_ticker.history.side_effect = [
            Exception("Too Many Requests"),
            mock_yf_history_data,
        ]
        mock_yf.Ticker.return_value = mock_ticker

        result = source.fetch(yfinance_config)

        # 应该成功
        assert result.success is True
        assert mock_ticker.history.call_count == 2


class TestYFinanceDataSourceValidateSymbol:
    """测试 YFinanceDataSource.validate_symbol() 方法"""

    def test_validate_symbol_stock(self, yfinance_source):
        """测试股票代码验证"""
        # 美股代码
        assert (
            yfinance_source.validate_symbol(Symbol(raw="AAPL", normalized="AAPL"))
            is True
        )
        assert (
            yfinance_source.validate_symbol(Symbol(raw="MSFT", normalized="MSFT"))
            is True
        )
        assert (
            yfinance_source.validate_symbol(Symbol(raw="TSLA", normalized="TSLA"))
            is True
        )

    def test_validate_symbol_index(self, yfinance_source):
        """测试指数代码验证"""
        # 美股指数
        assert (
            yfinance_source.validate_symbol(Symbol(raw="^GSPC", normalized="^GSPC"))
            is True
        )
        assert (
            yfinance_source.validate_symbol(Symbol(raw="^DJI", normalized="^DJI"))
            is True
        )
        assert (
            yfinance_source.validate_symbol(Symbol(raw="^IXIC", normalized="^IXIC"))
            is True
        )

    def test_validate_symbol_hk_stock(self, yfinance_source):
        """测试港股代码验证"""
        assert (
            yfinance_source.validate_symbol(Symbol(raw="0700.HK", normalized="0700.HK"))
            is True
        )
        assert (
            yfinance_source.validate_symbol(Symbol(raw="2800.HK", normalized="2800.HK"))
            is True
        )
        assert (
            yfinance_source.validate_symbol(Symbol(raw="9988.HK", normalized="9988.HK"))
            is True
        )

    def test_validate_symbol_futures(self, yfinance_source):
        """测试期货代码验证"""
        assert (
            yfinance_source.validate_symbol(Symbol(raw="GC=F", normalized="GC=F"))
            is True
        )  # 黄金
        assert (
            yfinance_source.validate_symbol(Symbol(raw="SI=F", normalized="SI=F"))
            is True
        )  # 白银
        assert (
            yfinance_source.validate_symbol(Symbol(raw="CL=F", normalized="CL=F"))
            is True
        )  # 原油

    def test_validate_symbol_invalid(self, yfinance_source):
        """测试无效代码"""
        # A股代码不应该通过（不含前缀）
        assert (
            yfinance_source.validate_symbol(Symbol(raw="600519", normalized="600519"))
            is False
        )
        # 包含数字的代码可能不通过
        assert (
            yfinance_source.validate_symbol(Symbol(raw="123", normalized="123"))
            is False
        )


class TestYFinanceDataSourceGetInfo:
    """测试 YFinanceDataSource.get_info() 方法"""

    @patch("tick.datasources.yfinance_ds.yf")
    def test_get_info_success(self, mock_yf, yfinance_source):
        """测试成功获取品种信息"""
        symbol = Symbol(raw="AAPL", normalized="AAPL")

        mock_ticker = MagicMock()
        mock_ticker.info = {
            "longName": "Apple Inc.",
            "shortName": "Apple",
            "quoteType": "EQUITY",
            "market": "us_market",
            "currency": "USD",
            "regularMarketPrice": 175.50,
            "marketCap": 2800000000000,
            "sector": "Technology",
            "industry": "Consumer Electronics",
        }
        mock_yf.Ticker.return_value = mock_ticker

        info = yfinance_source.get_info(symbol)

        assert info is not None
        assert info["name"] == "Apple Inc."
        assert info["type"] == "EQUITY"
        assert info["market"] == "us_market"
        assert info["currency"] == "USD"
        assert info["price"] == 175.50
        assert info["market_cap"] == 2800000000000
        assert info["sector"] == "Technology"
        assert info["industry"] == "Consumer Electronics"

    @patch("tick.datasources.yfinance_ds.yf")
    def test_get_info_fallback_short_name(self, mock_yf, yfinance_source):
        """测试使用 shortName 作为备选"""
        symbol = Symbol(raw="TSLA", normalized="TSLA")

        mock_ticker = MagicMock()
        mock_ticker.info = {
            "shortName": "Tesla Inc",
            "quoteType": "EQUITY",
            "currency": "USD",
        }
        mock_yf.Ticker.return_value = mock_ticker

        info = yfinance_source.get_info(symbol)

        assert info is not None
        assert info["name"] == "Tesla Inc"

    @patch("tick.datasources.yfinance_ds.yf")
    def test_get_info_failure(self, mock_yf, yfinance_source):
        """测试获取信息失败"""
        symbol = Symbol(raw="INVALID", normalized="INVALID")

        mock_ticker = MagicMock()
        type(mock_ticker).info = PropertyMock(side_effect=Exception("Symbol not found"))
        mock_yf.Ticker.return_value = mock_ticker

        info = yfinance_source.get_info(symbol)

        assert info is None

    @patch("tick.datasources.yfinance_ds.yf", None)
    def test_get_info_not_installed(self, yfinance_source):
        """测试 yfinance 未安装时返回 None"""
        symbol = Symbol(raw="AAPL", normalized="AAPL")

        info = yfinance_source.get_info(symbol)

        assert info is None


# ─────────────────────────────────────────
# AkShareDataSource Tests
# ─────────────────────────────────────────


class TestAkShareDataSourceFetch:
    """测试 AkShareDataSource.fetch() 方法"""

    @patch("tick.datasources.akshare_ds.AkShareDataSource._fetch_daily")
    def test_fetch_daily_routing(
        self, mock_fetch_daily, akshare_source, akshare_daily_config
    ):
        """测试日线数据路由"""
        mock_result = Mock()
        mock_result.success = True
        mock_fetch_daily.return_value = mock_result

        result = akshare_source.fetch(akshare_daily_config)

        mock_fetch_daily.assert_called_once()
        assert result.success is True

    @patch("tick.datasources.akshare_ds.AkShareDataSource._fetch_intraday")
    def test_fetch_intraday_routing(
        self, mock_fetch_intraday, akshare_source, akshare_intraday_config
    ):
        """测试分时数据路由"""
        mock_result = Mock()
        mock_result.success = True
        mock_fetch_intraday.return_value = mock_result

        result = akshare_source.fetch(akshare_intraday_config)

        mock_fetch_intraday.assert_called_once()
        assert result.success is True

    @patch("tick.datasources.akshare_ds.AkShareDataSource._fetch_futures")
    @patch("tick.datasources.akshare_ds.AkShareDataSource._is_futures")
    def test_fetch_futures_routing(
        self, mock_is_futures, mock_fetch_futures, akshare_source
    ):
        """测试期货数据路由"""
        symbol = Symbol(raw="AU", normalized="AU", asset_type=AssetType.FUTURES)
        config = FetchConfig(
            symbol=symbol, start="2024-01-01", end="2024-01-31", interval=Interval.DAY
        )

        mock_is_futures.return_value = True
        mock_result = Mock()
        mock_result.success = True
        mock_fetch_futures.return_value = mock_result

        result = akshare_source.fetch(config)

        mock_is_futures.assert_called_once_with("AU")
        mock_fetch_futures.assert_called_once()
        assert result.success is True

    def test_fetch_akshare_not_installed(self, akshare_source, akshare_daily_config):
        """测试 akshare 未安装的情况"""
        with patch.dict("sys.modules", {"akshare": None}):
            result = akshare_source.fetch(akshare_daily_config)

            assert result.success is False
            assert "请安装 akshare" in result.error_message


class TestAkShareDataSourceFetchDaily:
    """测试 AkShareDataSource._fetch_daily() 方法"""

    def test_fetch_daily_success(
        self, akshare_source, akshare_daily_config, mock_akshare_daily_data
    ):
        """测试成功获取日线数据"""
        mock_ak = MagicMock()
        mock_ak.stock_zh_a_hist.return_value = mock_akshare_daily_data

        result = akshare_source._fetch_daily(mock_ak, akshare_daily_config, "600519")

        assert result.success is True
        assert result.data is not None
        assert len(result.data) == 5
        assert "close" in result.data.columns
        assert "open" in result.data.columns
        assert "high" in result.data.columns
        assert "low" in result.data.columns
        assert "volume" in result.data.columns
        assert result.metadata["source"] == "akshare"
        assert result.metadata["type"] == "daily"

    def test_fetch_daily_etf_fallback(
        self, akshare_source, akshare_daily_config, mock_akshare_daily_data
    ):
        """测试 ETF 数据回退"""
        mock_ak = MagicMock()
        # 第一次调用返回空，触发 ETF 回退
        mock_ak.stock_zh_a_hist.return_value = pd.DataFrame()
        mock_ak.fund_etf_hist_sina.return_value = mock_akshare_daily_data

        result = akshare_source._fetch_daily(mock_ak, akshare_daily_config, "600519")

        assert result.success is True
        assert result.data is not None
        mock_ak.fund_etf_hist_sina.assert_called_once()

    def test_fetch_daily_empty_data(self, akshare_source, akshare_daily_config):
        """测试空数据返回"""
        mock_ak = MagicMock()
        mock_ak.stock_zh_a_hist.return_value = pd.DataFrame()
        mock_ak.fund_etf_hist_sina.return_value = pd.DataFrame()

        result = akshare_source._fetch_daily(mock_ak, akshare_daily_config, "600519")

        assert result.success is False
        assert "未返回数据" in result.error_message or "未" in result.error_message

    def test_fetch_daily_exception(self, akshare_source, akshare_daily_config):
        """测试异常情况"""
        mock_ak = MagicMock()
        mock_ak.stock_zh_a_hist.side_effect = Exception("Network error")

        result = akshare_source._fetch_daily(mock_ak, akshare_daily_config, "600519")

        assert result.success is False
        assert "获取失败" in result.error_message


class TestAkShareDataSourceFetchIntraday:
    """测试 AkShareDataSource._fetch_intraday() 方法"""

    def test_fetch_intraday_success(
        self, akshare_source, akshare_intraday_config, mock_akshare_intraday_data
    ):
        """测试成功获取分时数据"""
        mock_ak = MagicMock()
        mock_ak.stock_zh_a_hist_min_em.return_value = mock_akshare_intraday_data

        result = akshare_source._fetch_intraday(
            mock_ak, akshare_intraday_config, "600519", "5m"
        )

        assert result.success is True
        assert result.data is not None
        assert len(result.data) == 3
        assert result.metadata["source"] == "akshare"
        assert result.metadata["type"] == "intraday"

    def test_fetch_intraday_empty_data(self, akshare_source, akshare_intraday_config):
        """测试空数据返回"""
        mock_ak = MagicMock()
        mock_ak.stock_zh_a_hist_min_em.return_value = pd.DataFrame()

        result = akshare_source._fetch_intraday(
            mock_ak, akshare_intraday_config, "600519", "5m"
        )

        assert result.success is False
        assert "分时数据为空" in result.error_message or "空" in result.error_message

    def test_fetch_intraday_exception(self, akshare_source, akshare_intraday_config):
        """测试异常情况"""
        mock_ak = MagicMock()
        mock_ak.stock_zh_a_hist_min_em.side_effect = Exception("API error")

        result = akshare_source._fetch_intraday(
            mock_ak, akshare_intraday_config, "600519", "5m"
        )

        assert result.success is False
        assert "分时数据获取失败" in result.error_message


class TestAkShareDataSourceFetchFutures:
    """测试 AkShareDataSource._fetch_futures() 方法"""

    def test_fetch_futures_success_main_contract(
        self, akshare_source, mock_akshare_futures_data
    ):
        """测试成功获取期货主力合约数据"""
        symbol = Symbol(raw="AU", normalized="AU", asset_type=AssetType.FUTURES)
        config = FetchConfig(
            symbol=symbol, start="2024-01-01", end="2024-01-31", interval=Interval.DAY
        )

        mock_ak = MagicMock()
        mock_ak.futures_main_sina.return_value = mock_akshare_futures_data

        result = akshare_source._fetch_futures(mock_ak, config, "AU")

        assert result.success is True
        assert result.data is not None
        assert len(result.data) == 3
        assert result.metadata["source"] == "akshare"
        assert result.metadata["type"] == "futures"

    def test_fetch_futures_fallback_daily(
        self, akshare_source, mock_akshare_futures_data
    ):
        """测试期货日数据回退"""
        symbol = Symbol(raw="RB", normalized="RB", asset_type=AssetType.FUTURES)
        config = FetchConfig(
            symbol=symbol, start="2024-01-01", end="2024-01-31", interval=Interval.DAY
        )

        mock_ak = MagicMock()
        mock_ak.futures_main_sina.side_effect = Exception("API error")
        mock_ak.futures_zh_daily_sina.return_value = mock_akshare_futures_data

        result = akshare_source._fetch_futures(mock_ak, config, "RB")

        assert result.success is True
        assert result.data is not None
        mock_ak.futures_zh_daily_sina.assert_called_once_with(symbol="RB")

    def test_fetch_futures_empty_data(self, akshare_source):
        """测试空数据返回"""
        symbol = Symbol(raw="CF", normalized="CF", asset_type=AssetType.FUTURES)
        config = FetchConfig(
            symbol=symbol, start="2024-01-01", end="2024-01-31", interval=Interval.DAY
        )

        mock_ak = MagicMock()
        mock_ak.futures_main_sina.return_value = pd.DataFrame()

        result = akshare_source._fetch_futures(mock_ak, config, "CF")

        assert result.success is False
        assert "期货数据为空" in result.error_message or "空" in result.error_message

    def test_fetch_futures_exception(self, akshare_source):
        """测试异常情况"""
        symbol = Symbol(raw="CU", normalized="CU", asset_type=AssetType.FUTURES)
        config = FetchConfig(
            symbol=symbol, start="2024-01-01", end="2024-01-31", interval=Interval.DAY
        )

        mock_ak = MagicMock()
        mock_ak.futures_main_sina.side_effect = Exception("API error")
        mock_ak.futures_zh_daily_sina.side_effect = Exception("API error")

        result = akshare_source._fetch_futures(mock_ak, config, "CU")

        assert result.success is False
        assert "期货获取失败" in result.error_message


class TestAkShareDataSourceIsFutures:
    """测试 AkShareDataSource._is_futures() 方法"""

    def test_is_futures_pure_code(self, akshare_source):
        """测试纯期货代码识别"""
        # 贵金属
        assert akshare_source._is_futures("AU") is True  # 黄金
        assert akshare_source._is_futures("AG") is True  # 白银
        # 金属
        assert akshare_source._is_futures("RB") is True  # 螺纹钢
        assert akshare_source._is_futures("HC") is True  # 热卷
        # 化工
        assert akshare_source._is_futures("TA") is True  # PTA
        assert akshare_source._is_futures("MA") is True  # 甲醇
        # 农产品
        assert akshare_source._is_futures("CF") is True  # 棉花
        assert akshare_source._is_futures("SR") is True  # 白糖

    def test_is_futures_with_contract_month(self, akshare_source):
        """测试带合约月份的期货代码"""
        assert akshare_source._is_futures("AU2506") is True
        assert akshare_source._is_futures("RB2412") is True
        assert akshare_source._is_futures("CF2501") is True
        assert akshare_source._is_futures("TA2505") is True

    def test_is_futures_invalid(self, akshare_source):
        """测试非期货代码"""
        assert akshare_source._is_futures("SH600519") is False
        assert akshare_source._is_futures("AAPL") is False
        assert akshare_source._is_futures("123") is False


class TestAkShareDataSourceValidateSymbol:
    """测试 AkShareDataSource.validate_symbol() 方法"""

    def test_validate_a_share(self, akshare_source):
        """测试A股代码验证"""
        assert (
            akshare_source.validate_symbol(
                Symbol(raw="sh600519", normalized="SH600519")
            )
            is True
        )
        assert (
            akshare_source.validate_symbol(
                Symbol(raw="sz000001", normalized="SZ000001")
            )
            is True
        )
        assert (
            akshare_source.validate_symbol(
                Symbol(raw="sz300750", normalized="SZ300750")
            )
            is True
        )

    def test_validate_bj_stock(self, akshare_source):
        """测试北交所代码验证"""
        assert (
            akshare_source.validate_symbol(
                Symbol(raw="bj835305", normalized="BJ835305")
            )
            is True
        )
        assert (
            akshare_source.validate_symbol(
                Symbol(raw="bj430047", normalized="BJ430047")
            )
            is True
        )

    def test_validate_futures(self, akshare_source):
        """测试期货代码验证"""
        assert akshare_source.validate_symbol(Symbol(raw="AU", normalized="AU")) is True
        assert akshare_source.validate_symbol(Symbol(raw="RB", normalized="RB")) is True

    def test_validate_invalid(self, akshare_source):
        """测试无效代码"""
        assert (
            akshare_source.validate_symbol(Symbol(raw="AAPL", normalized="AAPL"))
            is False
        )
        assert (
            akshare_source.validate_symbol(Symbol(raw="BTC-USD", normalized="BTC-USD"))
            is False
        )


# ─────────────────────────────────────────
# CCXTDataSource Tests
# ─────────────────────────────────────────


class TestCCXTDataSourceFetch:
    """测试 CCXTDataSource.fetch() 方法"""

    def test_fetch_success(self, ccxt_source, ccxt_config, mock_ccxt_ohlcv_data):
        """测试成功获取数据"""
        mock_ccxt = MagicMock()
        mock_exchange = MagicMock()
        # 第一次返回数据，第二次返回空列表终止循环
        mock_exchange.fetch_ohlcv.side_effect = [mock_ccxt_ohlcv_data, []]
        mock_exchange.parse8601.side_effect = [
            1704067200000,  # start: 2024-01-01
            1706745599000,  # end:   2024-02-01 23:59:59（足够大，确保循环能跑起来）
        ]
        mock_ccxt.binance.return_value = mock_exchange

        with patch.dict("sys.modules", {"ccxt": mock_ccxt}):
            result = ccxt_source.fetch(ccxt_config)

        assert result.success is True
        assert result.data is not None
        assert len(result.data) == 5
        assert "close" in result.data.columns
        assert "open" in result.data.columns
        assert "high" in result.data.columns
        assert "low" in result.data.columns
        assert "volume" in result.data.columns
        assert result.metadata["source"] == "ccxt"
        assert result.metadata["exchange"] == "binance"

    def test_fetch_ccxt_not_installed(self, ccxt_source, ccxt_config):
        """测试 ccxt 未安装的情况"""
        with patch.dict("sys.modules", {"ccxt": None}):
            result = ccxt_source.fetch(ccxt_config)

            assert result.success is False
            assert "请安装 ccxt" in result.error_message

    def test_fetch_unsupported_exchange(self, ccxt_source, btc_symbol):
        """测试不支持的交易所"""
        config = FetchConfig(
            symbol=btc_symbol,
            start="2024-01-01",
            end="2024-01-10",
            interval=Interval.DAY,
            exchange="unsupported_exchange",
        )

        result = ccxt_source.fetch(config)

        assert result.success is False
        assert "不支持的交易所" in result.error_message

    def test_fetch_empty_data(self, ccxt_source, ccxt_config):
        """测试空数据返回"""
        mock_ccxt = MagicMock()
        mock_exchange = MagicMock()
        # 第一次就返回空列表，直接 break
        mock_exchange.fetch_ohlcv.side_effect = [[]]
        mock_exchange.parse8601.side_effect = [
            1704067200000,
            1706745599000,
        ]
        mock_ccxt.binance.return_value = mock_exchange

        with patch.dict("sys.modules", {"ccxt": mock_ccxt}):
            result = ccxt_source.fetch(ccxt_config)

        assert result.success is False
        assert "未返回数据" in result.error_message or "未" in result.error_message

    def test_fetch_exception(self, ccxt_source, ccxt_config):
        """测试获取异常"""
        mock_ccxt = MagicMock()
        mock_exchange = MagicMock()
        mock_exchange.fetch_ohlcv.side_effect = Exception("API error")
        mock_exchange.parse8601.side_effect = [
            1704067200000,
            1706745599000,
        ]
        mock_ccxt.binance.return_value = mock_exchange

        with patch.dict("sys.modules", {"ccxt": mock_ccxt}):
            result = ccxt_source.fetch(ccxt_config)

        assert result.success is False
        assert "获取失败" in result.error_message

    def test_fetch_pagination(self, ccxt_source, btc_symbol):
        """测试数据分页获取"""
        config = FetchConfig(
            symbol=btc_symbol,
            start="2024-01-01",
            end="2024-01-31",
            interval=Interval.DAY,
            exchange="binance",
        )

        # 模拟分批返回数据
        batch1 = [
            [1704067200000, 42000.0, 43000.0, 41500.0, 42500.0, 1000.0],
        ]
        batch2 = [
            [1704153600000, 42500.0, 43500.0, 42000.0, 43000.0, 1200.0],
        ]

        mock_ccxt = MagicMock()
        mock_exchange = MagicMock()
        mock_exchange.fetch_ohlcv.side_effect = [batch1, batch2, []]  # 第三次返回空结束
        mock_exchange.parse8601.side_effect = [
            1704067200000,  # start
            1706745599000,  # end
        ]
        mock_ccxt.binance.return_value = mock_exchange

        with patch.dict("sys.modules", {"ccxt": mock_ccxt}):
            result = ccxt_source.fetch(config)

        assert result.success is True
        assert result.data is not None
        assert mock_exchange.fetch_ohlcv.call_count == 3


class TestCCXTDataSourceToCCXTSymbol:
    """测试 CCXTDataSource._to_ccxt_symbol() 方法"""

    def test_to_ccxt_symbol_binance(self, ccxt_source):
        """测试 Binance 代码转换"""
        assert ccxt_source._to_ccxt_symbol("BTC-USD", "binance") == "BTC/USDT"
        assert ccxt_source._to_ccxt_symbol("ETH-USDT", "binance") == "ETH/USDT"
        assert ccxt_source._to_ccxt_symbol("SOL", "binance") == "SOL/USDT"

    def test_to_ccxt_symbol_kraken(self, ccxt_source):
        """测试 Kraken 代码转换（BTC -> BTC）"""
        assert ccxt_source._to_ccxt_symbol("BTC-USD", "kraken") == "BTC/USD"
        assert ccxt_source._to_ccxt_symbol("ETH", "kraken") == "ETH/USD"

    def test_to_ccxt_symbol_other_exchanges(self, ccxt_source):
        """测试其他交易所代码转换"""
        assert ccxt_source._to_ccxt_symbol("BTC", "okx") == "BTC/USDT"
        assert ccxt_source._to_ccxt_symbol("BTC", "bybit") == "BTC/USDT"
        assert ccxt_source._to_ccxt_symbol("BTC", "bitstamp") == "BTC/USD"
        assert ccxt_source._to_ccxt_symbol("BTC", "bitfinex") == "BTC/USD"


class TestCCXTDataSourceValidateSymbol:
    """测试 CCXTDataSource.validate_symbol() 方法"""

    def test_validate_with_suffix(self, ccxt_source):
        """测试带后缀的代码"""
        assert (
            ccxt_source.validate_symbol(Symbol(raw="BTC-USD", normalized="BTC-USD"))
            is True
        )
        assert (
            ccxt_source.validate_symbol(Symbol(raw="ETH-USDT", normalized="ETH-USDT"))
            is True
        )
        assert (
            ccxt_source.validate_symbol(Symbol(raw="SOL-USD", normalized="SOL-USD"))
            is True
        )

    def test_validate_common_crypto(self, ccxt_source):
        """测试常见加密货币代码"""
        assert ccxt_source.validate_symbol(Symbol(raw="BTC", normalized="BTC")) is True
        assert ccxt_source.validate_symbol(Symbol(raw="ETH", normalized="ETH")) is True
        assert ccxt_source.validate_symbol(Symbol(raw="SOL", normalized="SOL")) is True
        assert ccxt_source.validate_symbol(Symbol(raw="BNB", normalized="BNB")) is True
        assert (
            ccxt_source.validate_symbol(Symbol(raw="DOGE", normalized="DOGE")) is True
        )
        assert ccxt_source.validate_symbol(Symbol(raw="XRP", normalized="XRP")) is True
        assert ccxt_source.validate_symbol(Symbol(raw="ADA", normalized="ADA")) is True

    def test_validate_invalid(self, ccxt_source):
        """测试无效代码"""
        assert (
            ccxt_source.validate_symbol(Symbol(raw="AAPL", normalized="AAPL")) is False
        )
        assert (
            ccxt_source.validate_symbol(Symbol(raw="SH600519", normalized="SH600519"))
            is False
        )
