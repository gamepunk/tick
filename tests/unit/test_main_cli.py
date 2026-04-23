"""
测试 tick/main.py 中的 CLI 命令
使用 click.testing.CliRunner 进行测试
"""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest
from click.testing import CliRunner

from tick.core.models import FetchResult, Interval, Symbol
from tick.main import VERSION, cli, cmd_batch, cmd_config, cmd_fetch, cmd_search

# ═════════════════════════════════════════════════════════════════════════════
# Fixtures
# ═════════════════════════════════════════════════════════════════════════════


@pytest.fixture
def runner():
    """提供 CliRunner 实例"""
    return CliRunner()


@pytest.fixture
def mock_symbol():
    """提供 mock Symbol 对象"""
    return Symbol(raw="AAPL", normalized="AAPL")


@pytest.fixture
def mock_df():
    """提供 mock DataFrame（带 DatetimeIndex，供 standardize_dataframe 使用）"""
    dates = pd.date_range(start="2024-01-01", periods=5, freq="D", name="date")
    return pd.DataFrame(
        {
            "open": [100.0, 101.0, 102.0, 103.0, 104.0],
            "high": [105.0, 106.0, 107.0, 108.0, 109.0],
            "low": [99.0, 100.0, 101.0, 102.0, 103.0],
            "close": [102.0, 103.0, 104.0, 105.0, 106.0],
            "volume": [1_000_000, 1_100_000, 1_200_000, 1_300_000, 1_400_000],
        },
        index=dates,
    )


@pytest.fixture
def mock_datasource(mock_df):
    """提供 mock 数据源"""
    datasource = MagicMock()
    datasource.fetch.return_value = FetchResult(
        symbol=Symbol(raw="AAPL", normalized="AAPL"),
        data=mock_df,
        success=True,
        error_message=None,
    )
    return datasource


# ═════════════════════════════════════════════════════════════════════════════
# 1. main 命令组测试
# ═════════════════════════════════════════════════════════════════════════════


class TestMainCommand:
    """测试 main 命令组"""

    def test_no_args_shows_help(self, runner):
        """测试不带参数时显示帮助信息"""
        result = runner.invoke(cli, [])

        assert result.exit_code == 0
        assert "Usage:" in result.output
        assert "Commands:" in result.output
        assert "tick — 行情数据下载工具" in result.output

    def test_help_display(self, runner):
        """测试 --help 显示"""
        result = runner.invoke(cli, ["--help"])

        assert result.exit_code == 0
        assert "Usage:" in result.output
        assert "Options:" in result.output
        assert "--version" in result.output
        assert "--config" in result.output
        assert "--verbose" in result.output
        assert "Commands:" in result.output

    def test_version_display(self, runner):
        """测试 --version 显示"""
        result = runner.invoke(cli, ["--version"])

        assert result.exit_code == 0
        assert f"tick, version {VERSION}" in result.output


# ═════════════════════════════════════════════════════════════════════════════
# 2. fetch 命令测试
# ═════════════════════════════════════════════════════════════════════════════


class TestFetchCommand:
    """测试 fetch 命令"""

    @patch("tick.main.DataSourceRegistry.create")
    @patch("tick.main.DataSourceRouter.detect_market")
    @patch("tick.main.get_cache")
    def test_fetch_with_all_options(
        self,
        mock_get_cache,
        mock_detect_market,
        mock_create,
        runner,
        mock_datasource,
        mock_df,
    ):
        """测试带所有参数的 fetch 命令"""
        mock_detect_market.return_value = "yfinance"
        mock_create.return_value = mock_datasource

        mock_cache = MagicMock()
        mock_cache.get.return_value = None
        mock_get_cache.return_value = mock_cache

        with runner.isolated_filesystem():
            result = runner.invoke(
                cli,
                [
                    "fetch",
                    "AAPL",
                    "--start",
                    "2024-01-01",
                    "--end",
                    "2024-01-31",
                    "--interval",
                    "1d",
                    "--output",
                    "test_output.csv",
                    "--format",
                    "csv",
                    "--asset",
                    "stock",
                    "--exchange",
                    "binance",
                    "--no-cache",
                ],
            )

        assert result.exit_code == 0
        mock_datasource.fetch.assert_called_once()

    @patch("tick.main.get_config")
    @patch("tick.main.DataSourceRegistry.create")
    @patch("tick.main.DataSourceRouter.detect_market")
    @patch("tick.main.get_cache")
    def test_fetch_success_flow(
        self,
        mock_get_cache,
        mock_detect_market,
        mock_create,
        mock_get_config,
        runner,
        mock_datasource,
        mock_df,
    ):
        """测试成功的 fetch 流程"""
        mock_detect_market.return_value = "yfinance"
        mock_create.return_value = mock_datasource

        mock_cache = MagicMock()
        mock_cache.get.return_value = None
        mock_get_cache.return_value = mock_cache

        mock_config = MagicMock()
        mock_config.get_output_dir.return_value = Path(".")
        mock_get_config.return_value = mock_config

        with runner.isolated_filesystem():
            result = runner.invoke(cli, ["fetch", "AAPL", "--no-cache"])

        assert result.exit_code == 0
        assert "已保存" in result.output or "AAPL" in result.output

    def test_fetch_missing_symbol(self, runner):
        """测试缺少 symbol 参数"""
        result = runner.invoke(cli, ["fetch"])

        assert result.exit_code != 0
        assert "Missing argument" in result.output or "SYMBOL" in result.output

    def test_fetch_invalid_date_format(self, runner):
        """测试无效日期格式 - fetch 命令使用原始字符串，没有日期解析验证"""
        # fetch 命令接受原始字符串日期，验证由数据源处理
        with (
            patch("tick.main.DataSourceRegistry.create") as mock_create,
            patch("tick.main.DataSourceRouter.detect_market") as mock_detect_market,
            patch("tick.main.get_cache") as mock_cache_func,
        ):
            mock_detect_market.return_value = "yfinance"
            mock_create.return_value = None  # 无数据源，触发退出

            mock_cache = MagicMock()
            mock_cache.get.return_value = None
            mock_cache_func.return_value = mock_cache

            result = runner.invoke(
                cli,
                [
                    "fetch",
                    "AAPL",
                    "--start",
                    "invalid-date",
                    "--end",
                    "also-invalid",
                ],
            )

        # 命令会尝试执行，但会因无数据源而失败
        assert result.exit_code != 0

    @patch("tick.main.get_config")
    @patch("tick.main.DataSourceRouter.detect_market")
    @patch("tick.main.get_cache")
    def test_fetch_with_cache_hit(
        self,
        mock_get_cache,
        mock_detect_market,
        mock_get_config,
        runner,
        mock_df,
    ):
        """测试缓存命中情况"""
        mock_detect_market.return_value = "yfinance"

        mock_cache = MagicMock()
        mock_cache.get.return_value = mock_df  # 缓存命中
        mock_get_cache.return_value = mock_cache

        mock_config = MagicMock()
        mock_config.get_output_dir.return_value = Path(".")
        mock_get_config.return_value = mock_config

        with runner.isolated_filesystem():
            result = runner.invoke(cli, ["fetch", "AAPL"])

        assert result.exit_code == 0
        mock_cache.get.assert_called_once()

    @patch("tick.main.DataSourceRegistry.create")
    @patch("tick.main.DataSourceRouter.detect_market")
    @patch("tick.main.get_cache")
    def test_fetch_datasource_failure(
        self,
        mock_get_cache,
        mock_detect_market,
        mock_create,
        runner,
    ):
        """测试数据源获取失败"""
        mock_detect_market.return_value = "yfinance"

        failed_datasource = MagicMock()
        failed_datasource.fetch.return_value = FetchResult(
            symbol=Symbol(raw="INVALID", normalized="INVALID"),
            data=None,
            success=False,
            error_message="无法获取数据",
        )
        mock_create.return_value = failed_datasource

        mock_cache = MagicMock()
        mock_cache.get.return_value = None
        mock_get_cache.return_value = mock_cache

        result = runner.invoke(cli, ["fetch", "INVALID", "--no-cache"])

        assert result.exit_code == 1

    @patch("tick.main.DataSourceRegistry.create")
    @patch("tick.main.DataSourceRouter.detect_market")
    @patch("tick.main.get_cache")
    def test_fetch_no_datasource_found(
        self,
        mock_get_cache,
        mock_detect_market,
        mock_create,
        runner,
    ):
        """测试找不到数据源"""
        mock_detect_market.return_value = "unknown"
        mock_create.return_value = None

        mock_cache = MagicMock()
        mock_cache.get.return_value = None
        mock_get_cache.return_value = mock_cache

        result = runner.invoke(cli, ["fetch", "UNKNOWN"])

        assert result.exit_code == 1


# ═════════════════════════════════════════════════════════════════════════════
# 3. batch 命令测试
# ═════════════════════════════════════════════════════════════════════════════


class TestBatchCommand:
    """测试 batch 命令"""

    @patch("tick.main.DataSourceRouter.detect_market")
    @patch("tick.main.DataSourceRouter.get_datasource")
    @patch("tick.main.get_config")
    def test_batch_with_symbols_list(
        self,
        mock_get_config,
        mock_get_datasource,
        mock_detect_market,
        runner,
        mock_datasource,
        mock_df,
    ):
        """测试 symbols 列表解析"""
        mock_detect_market.return_value = "yfinance"
        mock_get_datasource.return_value = mock_datasource

        mock_config = MagicMock()
        mock_config.get_output_dir.return_value = Path(".")
        mock_get_config.return_value = mock_config

        with runner.isolated_filesystem():
            result = runner.invoke(
                cli,
                [
                    "batch",
                    "AAPL",
                    "TSLA",
                    "MSFT",
                    "--start",
                    "2024-01-01",
                    "--end",
                    "2024-01-31",
                    "--interval",
                    "1d",
                    "--format",
                    "csv",
                ],
            )

        assert result.exit_code == 0
        # 三个品种各调用一次 fetch
        assert mock_datasource.fetch.call_count == 3

    @patch("tick.main.DataSourceRouter.detect_market")
    @patch("tick.main.DataSourceRouter.get_datasource")
    @patch("tick.main.get_config")
    def test_batch_with_output_dir(
        self,
        mock_get_config,
        mock_get_datasource,
        mock_detect_market,
        runner,
        mock_datasource,
        mock_df,
    ):
        """测试输出目录参数"""
        mock_detect_market.return_value = "yfinance"
        mock_get_datasource.return_value = mock_datasource

        mock_config = MagicMock()
        mock_config.get_output_dir.return_value = Path("./default_output")
        mock_get_config.return_value = mock_config

        with runner.isolated_filesystem():
            result = runner.invoke(
                cli,
                [
                    "batch",
                    "AAPL",
                    "--dir",
                    "./custom_output",
                    "--format",
                    "csv",
                ],
            )

        assert result.exit_code == 0

    @patch("tick.main.DataSourceRouter.detect_market")
    @patch("tick.main.DataSourceRouter.get_datasource")
    @patch("tick.main.get_config")
    def test_batch_with_multiple_assets(
        self,
        mock_get_config,
        mock_get_datasource,
        mock_detect_market,
        runner,
        mock_datasource,
        mock_df,
    ):
        """测试多个资产类型参数"""
        mock_detect_market.return_value = "yfinance"
        mock_get_datasource.return_value = mock_datasource

        mock_config = MagicMock()
        mock_config.get_output_dir.return_value = Path(".")
        mock_get_config.return_value = mock_config

        with runner.isolated_filesystem():
            result = runner.invoke(
                cli,
                [
                    "batch",
                    "AAPL",
                    "BTC-USD",
                    "--asset",
                    "stock",
                    "--asset",
                    "crypto",
                    "--format",
                    "csv",
                ],
            )

        assert result.exit_code == 0

    def test_batch_missing_symbols(self, runner):
        """测试缺少 symbols 参数"""
        result = runner.invoke(cli, ["batch"])

        assert result.exit_code != 0
        assert "Missing argument" in result.output or "SYMBOLS" in result.output

    @patch("tick.main.DataSourceRouter.detect_market")
    @patch("tick.main.DataSourceRouter.get_datasource")
    @patch("tick.main.get_config")
    def test_batch_partial_failure(
        self,
        mock_get_config,
        mock_get_datasource,
        mock_detect_market,
        runner,
        mock_df,
    ):
        """测试批量下载部分失败"""
        mock_detect_market.return_value = "yfinance"

        success_datasource = MagicMock()
        success_datasource.fetch.return_value = FetchResult(
            symbol=Symbol(raw="AAPL", normalized="AAPL"),
            data=mock_df,
            success=True,
        )

        fail_datasource = MagicMock()
        fail_datasource.fetch.return_value = FetchResult(
            symbol=Symbol(raw="INVALID", normalized="INVALID"),
            data=None,
            success=False,
            error_message="获取失败",
        )

        def get_ds_side_effect(symbol):
            return success_datasource if symbol.raw == "AAPL" else fail_datasource

        mock_get_datasource.side_effect = get_ds_side_effect

        mock_config = MagicMock()
        mock_config.get_output_dir.return_value = Path(".")
        mock_get_config.return_value = mock_config

        with runner.isolated_filesystem():
            result = runner.invoke(cli, ["batch", "AAPL", "INVALID"])

        assert result.exit_code == 0

    @patch("tick.main.DataSourceRouter.detect_market")
    @patch("tick.main.DataSourceRouter.get_datasource")
    @patch("tick.main.get_config")
    def test_batch_with_show_flag(
        self,
        mock_get_config,
        mock_get_datasource,
        mock_detect_market,
        runner,
        mock_datasource,
        mock_df,
    ):
        """测试 batch 带 --show 标志"""
        mock_detect_market.return_value = "yfinance"
        mock_get_datasource.return_value = mock_datasource

        mock_config = MagicMock()
        mock_config.get_output_dir.return_value = Path(".")
        mock_get_config.return_value = mock_config

        with runner.isolated_filesystem():
            result = runner.invoke(
                cli,
                [
                    "batch",
                    "AAPL",
                    "--show",
                    "--format",
                    "csv",
                ],
            )

        assert result.exit_code == 0
        assert "数据行数" in result.output


# ═════════════════════════════════════════════════════════════════════════════
# 4. search 命令测试
# ═════════════════════════════════════════════════════════════════════════════


class TestSearchCommand:
    """测试 search 命令"""

    @patch("tick.utils.interactive.search_symbol")  # 局部导入，需 patch 源模块
    def test_search_with_query(self, mock_search_symbol, runner):
        """测试带查询参数的搜索"""
        mock_search_symbol.return_value = [
            {
                "symbol": "AAPL",
                "name": "Apple Inc.",
                "type": "stock",
                "market": "US",
                "source": "yfinance",
            },
            {
                "symbol": "AAP",
                "name": "Advance Auto Parts",
                "type": "stock",
                "market": "US",
                "source": "yfinance",
            },
        ]

        result = runner.invoke(cli, ["search", "apple"])

        assert result.exit_code == 0
        mock_search_symbol.assert_called_once_with("apple", source=None, limit=10)
        assert "AAPL" in result.output or "Apple" in result.output

    @patch("tick.utils.interactive.search_symbol")
    def test_search_with_source(self, mock_search_symbol, runner):
        """测试指定数据源搜索"""
        mock_search_symbol.return_value = [
            {
                "symbol": "sh600519",
                "name": "贵州茅台",
                "type": "stock",
                "source": "akshare",
            }
        ]

        result = runner.invoke(cli, ["search", "茅台", "--source", "akshare"])

        assert result.exit_code == 0
        mock_search_symbol.assert_called_once_with("茅台", source="akshare", limit=10)
        assert "贵州茅台" in result.output

    @patch("tick.utils.interactive.search_symbol")
    def test_search_with_limit(self, mock_search_symbol, runner):
        """测试限制返回数量"""
        mock_search_symbol.return_value = []

        result = runner.invoke(cli, ["search", "A", "--limit", "5"])

        assert result.exit_code == 0
        mock_search_symbol.assert_called_once_with("A", source=None, limit=5)

    @patch("tick.utils.interactive.search_symbol")  # 局部导入，需 patch 源模块
    def test_search_no_results(self, mock_search_symbol, runner):
        """测试搜索无结果"""
        mock_search_symbol.return_value = []

        result = runner.invoke(cli, ["search", "xyznonexistent"])

        assert result.exit_code == 0
        assert "未找到" in result.output or "No results" in result.output

    @patch("tick.main.interactive_search")
    def test_search_interactive(self, mock_interactive, runner):
        """测试交互式搜索"""
        mock_interactive.return_value = "AAPL"

        # 模拟用户不下载
        result = runner.invoke(cli, ["search"], input="n\n")

        # 交互式模式可能因环境而异
        assert result.exit_code in [0, 1]

    def test_search_with_empty_query(self, runner):
        """测试空查询（进入交互模式）"""
        with patch("tick.main.interactive_search") as mock_interactive:
            mock_interactive.return_value = None

            result = runner.invoke(cli, ["search"])

        # 空查询应该进入交互模式
        assert result.exit_code in [0, 1]


# ═════════════════════════════════════════════════════════════════════════════
# 5. config 命令测试
# ═════════════════════════════════════════════════════════════════════════════


class TestConfigCommand:
    """测试 config 命令"""

    @patch("tick.main.init_config")
    @patch("tick.core.config.AppConfig._get_default_config_path")
    def test_config_init(self, mock_get_path, mock_init_config, runner):
        """测试 config --init 子命令"""
        mock_get_path.return_value = "~/.config/tick/config.yaml"

        result = runner.invoke(cli, ["config", "--init"])

        assert result.exit_code == 0
        # init_config 被调用：CLI 组 handler 一次 + cmd_config 内一次
        assert mock_init_config.called


# ═════════════════════════════════════════════════════════════════════════════
# 6. web 命令测试
# ═════════════════════════════════════════════════════════════════════════════


class TestWebCommand:
    """测试 web 命令"""

    @patch("web.run.run_web")  # 局部导入，需 patch 源模块
    def test_web_command_invokes_web_runner(self, mock_run_web, runner):
        """测试 web 子命令调用 Web 启动器"""
        mock_run_web.return_value = 0

        result = runner.invoke(cli, ["web"])

        assert result.exit_code == 0
        mock_run_web.assert_called_once()

    @patch("web.run.run_web")  # 局部导入，需 patch 源模块
    def test_web_command_failure(self, mock_run_web, runner):
        """测试 web 命令失败情况"""
        mock_run_web.return_value = 1

        result = runner.invoke(cli, ["web"])

        assert result.exit_code == 1


# ═════════════════════════════════════════════════════════════════════════════
# 7. 参数解析测试
# ═════════════════════════════════════════════════════════════════════════════


class TestArgumentParsing:
    """测试参数解析"""

    def test_fetch_interval_choices(self, runner):
        """测试 fetch 命令 interval 选项的有效值"""
        valid_intervals = ["1m", "5m", "15m", "30m", "60m", "1h", "1d", "1wk", "1mo"]

        for interval in valid_intervals:
            with (
                patch("tick.main.DataSourceRegistry.create") as mock_create,
                patch("tick.main.DataSourceRouter.detect_market") as mock_detect_market,
                patch("tick.main.get_cache") as mock_cache_func,
            ):
                mock_detect_market.return_value = "yfinance"
                mock_create.return_value = (
                    None  # 无数据源，命令以 1 退出，但不报 Invalid value
                )

                mock_cache = MagicMock()
                mock_cache.get.return_value = None
                mock_cache_func.return_value = mock_cache

                result = runner.invoke(cli, ["fetch", "AAPL", "--interval", interval])
                # 参数应该被接受（即使后续因无数据源失败）
                assert "Invalid value" not in result.output

    def test_fetch_format_choices(self, runner):
        """测试 fetch 命令 format 选项的有效值"""
        valid_formats = ["csv", "json", "parquet"]

        for fmt in valid_formats:
            with (
                patch("tick.main.DataSourceRegistry.create") as mock_create,
                patch("tick.main.DataSourceRouter.detect_market") as mock_detect_market,
                patch("tick.main.get_cache") as mock_cache_func,
            ):
                mock_detect_market.return_value = "yfinance"
                mock_create.return_value = None

                mock_cache = MagicMock()
                mock_cache.get.return_value = None
                mock_cache_func.return_value = mock_cache

                result = runner.invoke(cli, ["fetch", "AAPL", "--format", fmt])
                assert "Invalid value" not in result.output

    def test_fetch_asset_choices(self, runner):
        """测试 fetch 命令 asset 选项的有效值"""
        valid_assets = ["stock", "index", "futures", "fund", "crypto"]

        for asset in valid_assets:
            with (
                patch("tick.main.DataSourceRegistry.create") as mock_create,
                patch("tick.main.DataSourceRouter.detect_market") as mock_detect_market,
                patch("tick.main.get_cache") as mock_cache_func,
            ):
                mock_detect_market.return_value = "yfinance"
                mock_create.return_value = None

                mock_cache = MagicMock()
                mock_cache.get.return_value = None
                mock_cache_func.return_value = mock_cache

                result = runner.invoke(cli, ["fetch", "AAPL", "--asset", asset])
                assert "Invalid value" not in result.output

    def test_fetch_exchange_choices(self, runner):
        """测试 fetch 命令 exchange 选项的有效值"""
        valid_exchanges = ["binance", "okx", "bybit", "kraken", "bitstamp", "bitfinex"]

        for exchange in valid_exchanges:
            with (
                patch("tick.main.DataSourceRegistry.create") as mock_create,
                patch("tick.main.DataSourceRouter.detect_market") as mock_detect_market,
                patch("tick.main.get_cache") as mock_cache_func,
            ):
                mock_detect_market.return_value = "ccxt"
                mock_create.return_value = None

                mock_cache = MagicMock()
                mock_cache.get.return_value = None
                mock_cache_func.return_value = mock_cache

                result = runner.invoke(
                    cli, ["fetch", "BTC-USD", "--exchange", exchange]
                )
                assert "Invalid value" not in result.output


# ═════════════════════════════════════════════════════════════════════════════
# 8. 集成测试
# ═════════════════════════════════════════════════════════════════════════════


class TestIntegration:
    """集成测试 - 测试命令组合"""

    def test_cli_verbose_flag(self, runner):
        """测试 verbose 标志传递"""
        result = runner.invoke(cli, ["--verbose", "--help"])
        assert result.exit_code == 0

    def test_help_lists_all_commands(self, runner):
        """测试帮助信息包含所有子命令"""
        result = runner.invoke(cli, ["--help"])

        assert result.exit_code == 0
        assert "fetch" in result.output
        assert "batch" in result.output
        assert "search" in result.output
        assert "config" in result.output
        assert "web" in result.output

    @patch("tick.main.get_config")
    @patch("tick.main.DataSourceRegistry.create")
    @patch("tick.main.DataSourceRouter.detect_market")
    @patch("tick.main.get_cache")
    def test_fetch_with_indicators(
        self,
        mock_get_cache,
        mock_detect_market,
        mock_create,
        mock_get_config,
        runner,
        mock_datasource,
        mock_df,
    ):
        """测试带技术指标的 fetch"""
        mock_detect_market.return_value = "yfinance"
        mock_create.return_value = mock_datasource

        mock_cache = MagicMock()
        mock_cache.get.return_value = None
        mock_get_cache.return_value = mock_cache

        mock_config = MagicMock()
        mock_config.get_output_dir.return_value = Path(".")
        mock_get_config.return_value = mock_config

        with runner.isolated_filesystem():
            result = runner.invoke(
                cli,
                [
                    "fetch",
                    "AAPL",
                    "--indicator",
                    "ma",
                    "--indicator",
                    "rsi",
                    "--no-cache",
                ],
            )

        assert result.exit_code == 0

    @patch("tick.main.get_config")
    @patch("tick.main.DataSourceRegistry.create")
    @patch("tick.main.DataSourceRouter.detect_market")
    @patch("tick.main.get_cache")
    def test_fetch_with_show_flag(
        self,
        mock_get_cache,
        mock_detect_market,
        mock_create,
        mock_get_config,
        runner,
        mock_datasource,
        mock_df,
    ):
        """测试带 --show 标志的 fetch"""
        mock_detect_market.return_value = "yfinance"
        mock_create.return_value = mock_datasource

        mock_cache = MagicMock()
        mock_cache.get.return_value = None
        mock_get_cache.return_value = mock_cache

        mock_config = MagicMock()
        mock_config.get_output_dir.return_value = Path(".")
        mock_get_config.return_value = mock_config

        with runner.isolated_filesystem():
            result = runner.invoke(
                cli,
                [
                    "fetch",
                    "AAPL",
                    "--show",
                    "--no-cache",
                ],
            )

        assert result.exit_code == 0


# ═════════════════════════════════════════════════════════════════════════════
# 7. cache 命令测试
# ═════════════════════════════════════════════════════════════════════════════


class TestCacheCommand:
    """测试 cache 命令"""

    @patch("tick.main.get_cache")
    def test_cache_list_empty(self, mock_get_cache, runner):
        """测试空缓存列表"""
        mock_cache = MagicMock()
        mock_cache.list_entries.return_value = []
        mock_cache.get_stats.return_value = {"entries": 0, "total_size_kb": 0.0}
        mock_get_cache.return_value = mock_cache

        result = runner.invoke(cli, ["cache", "list"])
        assert result.exit_code == 0
        assert "缓存为空" in result.output

    @patch("tick.main.get_cache")
    def test_cache_list_with_entries(self, mock_get_cache, runner):
        """测试列出缓存条目"""
        mock_cache = MagicMock()
        mock_cache.list_entries.return_value = [
            {
                "symbol": "AAPL",
                "start": "2024-01-01",
                "end": "2024-01-31",
                "interval": "1d",
                "created_at": "2024-01-01 10:00:00",
                "expires_at": "2024-01-02 10:00:00",
                "size_kb": 12.34,
            }
        ]
        mock_cache.get_stats.return_value = {"entries": 1, "total_size_kb": 12.34}
        mock_get_cache.return_value = mock_cache

        result = runner.invoke(cli, ["cache", "list"])
        assert result.exit_code == 0
        assert "AAPL" in result.output
        assert "1d" in result.output

    @patch("tick.main.get_cache")
    def test_cache_list_with_symbol(self, mock_get_cache, runner):
        """测试按 symbol 过滤缓存列表"""
        mock_cache = MagicMock()
        mock_cache.list_entries.return_value = []
        mock_cache.get_stats.return_value = {"entries": 0, "total_size_kb": 0.0}
        mock_get_cache.return_value = mock_cache

        result = runner.invoke(cli, ["cache", "list", "AAPL"])
        assert result.exit_code == 0
        mock_cache.list_entries.assert_called_once_with("AAPL")

    @patch("tick.main.get_cache")
    def test_cache_clear_all(self, mock_get_cache, runner):
        """测试清空所有缓存"""
        mock_cache = MagicMock()
        mock_get_cache.return_value = mock_cache

        result = runner.invoke(cli, ["cache", "clear"])
        assert result.exit_code == 0
        mock_cache.clear.assert_called_once_with()
        assert "已清空所有缓存" in result.output

    @patch("tick.main.get_cache")
    def test_cache_clear_symbol(self, mock_get_cache, runner):
        """测试清除特定品种缓存"""
        mock_cache = MagicMock()
        mock_get_cache.return_value = mock_cache

        result = runner.invoke(cli, ["cache", "clear", "AAPL"])
        assert result.exit_code == 0
        mock_cache.clear.assert_called_once_with("AAPL")
        assert "已清除 AAPL 的缓存" in result.output

    @patch("tick.main.get_cache")
    def test_cache_clear_expired(self, mock_get_cache, runner):
        """测试清理过期缓存"""
        mock_cache = MagicMock()
        mock_get_cache.return_value = mock_cache

        result = runner.invoke(cli, ["cache", "clear", "--expired"])
        assert result.exit_code == 0
        mock_cache.cleanup_expired.assert_called_once()
        assert "已清理过期缓存" in result.output
