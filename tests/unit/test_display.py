"""
测试 Rich 显示工具函数
"""
import pytest
import pandas as pd
import numpy as np
from unittest.mock import patch, MagicMock

from tick.utils.display import (
    get_console,
    print_success,
    print_error,
    print_warning,
    print_info,
    print_panel,
    create_progress_bar,
    print_data_summary,
    print_batch_results,
    print_symbol_table,
)


class TestGetConsole:
    """测试 get_console 函数"""
    
    def test_get_console_returns_console_instance(self):
        """测试返回 Console 实例"""
        console = get_console()
        from rich.console import Console
        assert isinstance(console, Console)
    
    def test_get_console_returns_same_instance(self):
        """测试返回的是同一个实例（单例）"""
        console1 = get_console()
        console2 = get_console()
        assert console1 is console2


class TestPrintMessages:
    """测试消息打印函数"""
    
    @patch("tick.utils.display.console.print")
    def test_print_success(self, mock_print):
        """测试打印成功消息"""
        print_success("操作成功")
        mock_print.assert_called_once_with("[green]✅ 操作成功[/]")
    
    @patch("tick.utils.display.console.print")
    def test_print_error(self, mock_print):
        """测试打印错误消息"""
        print_error("操作失败")
        mock_print.assert_called_once_with("[red]❌ 操作失败[/]")
    
    @patch("tick.utils.display.console.print")
    def test_print_warning(self, mock_print):
        """测试打印警告消息"""
        print_warning("注意警告")
        mock_print.assert_called_once_with("[yellow]⚠️ 注意警告[/]")
    
    @patch("tick.utils.display.console.print")
    def test_print_info(self, mock_print):
        """测试打印信息消息"""
        print_info("一般信息")
        mock_print.assert_called_once_with("[dim]一般信息[/]")


class TestPrintPanel:
    """测试 print_panel 函数"""
    
    @patch("tick.utils.display.console.print")
    def test_print_panel_basic(self, mock_print):
        """测试打印基础面板"""
        print_panel("面板内容")
        mock_print.assert_called_once()
        # 验证传参包含 Panel 对象
        call_args = mock_print.call_args[0][0]
        from rich.panel import Panel
        assert isinstance(call_args, Panel)
    
    @patch("tick.utils.display.console.print")
    def test_print_panel_with_title(self, mock_print):
        """测试打印带标题的面板"""
        print_panel("面板内容", title="面板标题")
        mock_print.assert_called_once()
        call_args = mock_print.call_args[0][0]
        from rich.panel import Panel
        assert isinstance(call_args, Panel)
    
    @patch("tick.utils.display.console.print")
    def test_print_panel_with_custom_style(self, mock_print):
        """测试打印自定义样式的面板"""
        print_panel("面板内容", style="red")
        mock_print.assert_called_once()
        call_args = mock_print.call_args[0][0]
        from rich.panel import Panel
        assert isinstance(call_args, Panel)


class TestCreateProgressBar:
    """测试 create_progress_bar 函数"""
    
    def test_create_progress_bar_returns_progress(self):
        """测试返回 Progress 对象"""
        progress = create_progress_bar()
        from rich.progress import Progress
        assert isinstance(progress, Progress)
    
    def test_create_progress_bar_with_description(self):
        """测试自定义描述"""
        progress = create_progress_bar(description="自定义描述")
        from rich.progress import Progress
        assert isinstance(progress, Progress)


class TestPrintDataSummary:
    """测试 print_data_summary 函数"""
    
    @patch("tick.utils.display.console.print")
    def test_print_data_summary_normal(self, mock_print, sample_dataframe):
        """测试正常数据摘要"""
        print_data_summary(sample_dataframe, "AAPL")
        mock_print.assert_called_once()
        # 验证传参包含 Table 对象
        call_args = mock_print.call_args[0][0]
        from rich.table import Table
        assert isinstance(call_args, Table)
    
    @patch("tick.utils.display.console.print")
    def test_print_data_summary_empty_dataframe(self, mock_print):
        """测试空 DataFrame"""
        df = pd.DataFrame()
        print_data_summary(df, "AAPL")
        mock_print.assert_not_called()
    
    @patch("tick.utils.display.console.print")
    def test_print_data_summary_none(self, mock_print):
        """测试 None 数据"""
        print_data_summary(None, "AAPL")
        mock_print.assert_not_called()
    
    @patch("tick.utils.display.console.print")
    def test_print_data_summary_missing_close_column(self, mock_print):
        """测试缺少 close 列"""
        df = pd.DataFrame({
            "open": [100, 101, 102],
            "high": [105, 106, 107],
            "low": [95, 96, 97],
            "volume": [1000, 2000, 3000]
        })
        print_data_summary(df, "AAPL")
        mock_print.assert_not_called()
    
    @patch("tick.utils.display.console.print")
    def test_print_data_summary_positive_change(self, mock_print):
        """测试上涨数据（绿色显示）"""
        dates = pd.date_range("2024-01-01", periods=5, freq="D")
        df = pd.DataFrame({
            "close": [100.0, 102.0, 104.0, 106.0, 110.0]
        }, index=dates)
        print_data_summary(df, "TEST")
        mock_print.assert_called_once()
    
    @patch("tick.utils.display.console.print")
    def test_print_data_summary_negative_change(self, mock_print):
        """测试下跌数据（红色显示）"""
        dates = pd.date_range("2024-01-01", periods=5, freq="D")
        df = pd.DataFrame({
            "close": [110.0, 108.0, 106.0, 104.0, 100.0]
        }, index=dates)
        print_data_summary(df, "TEST")
        mock_print.assert_called_once()


class TestPrintBatchResults:
    """测试 print_batch_results 函数"""
    
    @patch("tick.utils.display.console.print")
    def test_print_batch_results_basic(self, mock_print):
        """测试基础批量结果"""
        results = [
            {"symbol": "AAPL", "rows": 100, "info": "data/aapl.csv", "status": "✅"},
            {"symbol": "GOOGL", "rows": 150, "info": "data/googl.csv", "status": "✅"},
        ]
        print_batch_results(results)
        mock_print.assert_called_once()
        call_args = mock_print.call_args[0][0]
        from rich.table import Table
        assert isinstance(call_args, Table)
    
    @patch("tick.utils.display.console.print")
    def test_print_batch_results_with_errors(self, mock_print):
        """测试包含错误的批量结果"""
        results = [
            {"symbol": "AAPL", "rows": 100, "info": "data/aapl.csv", "status": "✅"},
            {"symbol": "INVALID", "rows": 0, "info": "Symbol not found", "status": "❌"},
        ]
        print_batch_results(results)
        mock_print.assert_called_once()
        call_args = mock_print.call_args[0][0]
        from rich.table import Table
        assert isinstance(call_args, Table)
    
    @patch("tick.utils.display.console.print")
    def test_print_batch_results_empty(self, mock_print):
        """测试空结果列表"""
        print_batch_results([])
        mock_print.assert_called_once()
        call_args = mock_print.call_args[0][0]
        from rich.table import Table
        assert isinstance(call_args, Table)
    
    @patch("tick.utils.display.console.print")
    def test_print_batch_results_missing_fields(self, mock_print):
        """测试缺失字段的结果"""
        results = [
            {"symbol": "AAPL"},  # 缺少其他字段
        ]
        print_batch_results(results)
        mock_print.assert_called_once()
        call_args = mock_print.call_args[0][0]
        from rich.table import Table
        assert isinstance(call_args, Table)


class TestPrintSymbolTable:
    """测试 print_symbol_table 函数"""
    
    @patch("tick.utils.display.console.print")
    def test_print_symbol_table_basic(self, mock_print):
        """测试基础品种列表"""
        symbols = [
            {"symbol": "AAPL", "name": "Apple Inc.", "type": "股票", "market": "US"},
            {"symbol": "GOOGL", "name": "Alphabet Inc.", "type": "股票", "market": "US"},
        ]
        print_symbol_table(symbols)
        mock_print.assert_called_once()
        call_args = mock_print.call_args[0][0]
        from rich.table import Table
        assert isinstance(call_args, Table)
    
    @patch("tick.utils.display.console.print")
    def test_print_symbol_table_with_title(self, mock_print):
        """测试自定义标题"""
        symbols = [
            {"symbol": "AAPL", "name": "Apple Inc.", "type": "股票", "market": "US"},
        ]
        print_symbol_table(symbols, title="美股列表")
        mock_print.assert_called_once()
        call_args = mock_print.call_args[0][0]
        from rich.table import Table
        assert isinstance(call_args, Table)
    
    @patch("tick.utils.display.console.print")
    def test_print_symbol_table_empty(self, mock_print):
        """测试空列表"""
        print_symbol_table([])
        mock_print.assert_called_once()
        call_args = mock_print.call_args[0][0]
        from rich.table import Table
        assert isinstance(call_args, Table)
    
    @patch("tick.utils.display.console.print")
    def test_print_symbol_table_missing_fields(self, mock_print):
        """测试缺失字段的品种"""
        symbols = [
            {"symbol": "AAPL"},  # 缺少其他字段
        ]
        print_symbol_table(symbols)
        mock_print.assert_called_once()
        call_args = mock_print.call_args[0][0]
        from rich.table import Table
        assert isinstance(call_args, Table)


class TestIntegration:
    """集成测试 - 验证实际输出"""
    
    def test_print_success_actual_output(self, capsys):
        """测试成功消息实际输出"""
        print_success("测试成功")
        captured = capsys.readouterr()
        assert "测试成功" in captured.out
    
    def test_print_error_actual_output(self, capsys):
        """测试错误消息实际输出"""
        print_error("测试错误")
        captured = capsys.readouterr()
        assert "测试错误" in captured.out
    
    def test_print_warning_actual_output(self, capsys):
        """测试警告消息实际输出"""
        print_warning("测试警告")
        captured = capsys.readouterr()
        assert "测试警告" in captured.out
    
    def test_print_info_actual_output(self, capsys):
        """测试信息消息实际输出"""
        print_info("测试信息")
        captured = capsys.readouterr()
        assert "测试信息" in captured.out
    
    def test_print_panel_actual_output(self, capsys):
        """测试面板实际输出"""
        print_panel("测试内容", title="测试标题")
        captured = capsys.readouterr()
        assert "测试内容" in captured.out
        assert "测试标题" in captured.out
