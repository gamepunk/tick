"""
测试交互式搜索
"""
import pytest
from unittest.mock import patch, MagicMock

from tick.utils.interactive import (
    search_symbol,
    interactive_search,
    multi_select_symbols,
    confirm_dialog
)


class TestSearchSymbol:
    """测试搜索品种功能"""
    
    @patch('tick.utils.interactive.DataSourceRegistry')
    def test_search_across_datasources(self, mock_registry):
        """测试跨数据源搜索"""
        # 模拟数据源
        mock_source1 = MagicMock()
        mock_source1.search.return_value = [
            {"symbol": "AAPL", "name": "Apple", "type": "stock"},
            {"symbol": "AMZN", "name": "Amazon", "type": "stock"}
        ]
        
        mock_source2 = MagicMock()
        mock_source2.search.return_value = [
            {"symbol": "BTC-USD", "name": "Bitcoin", "type": "crypto"}
        ]
        
        mock_registry.list_sources.return_value = ["yfinance", "ccxt"]
        mock_registry.create.side_effect = [mock_source1, mock_source2]
        
        # 执行搜索
        results = search_symbol("A")
        
        # 验证结果
        assert len(results) == 3
        assert results[0]["symbol"] == "AAPL"
        assert results[0]["source"] == "yfinance"
        assert results[2]["source"] == "ccxt"
        # 验证 limit 传给了数据源
        mock_source1.search.assert_called_once_with("A", limit=10)
    
    @patch('tick.utils.interactive.DataSourceRegistry')
    def test_search_with_source_filter(self, mock_registry):
        """测试指定数据源过滤"""
        mock_source = MagicMock()
        mock_source.search.return_value = [
            {"symbol": "sh600519", "name": "贵州茅台", "type": "stock"}
        ]
        
        mock_registry.list_sources.return_value = ["yfinance", "akshare", "ccxt"]
        mock_registry.create.return_value = mock_source
        
        results = search_symbol("茅台", source="akshare", limit=5)
        
        assert len(results) == 1
        assert results[0]["symbol"] == "sh600519"
        mock_source.search.assert_called_once_with("茅台", limit=5)
        # 只创建了一次 akshare 数据源
        mock_registry.create.assert_called_once_with("akshare")
    
    @patch('tick.utils.interactive.DataSourceRegistry')
    def test_search_with_limit(self, mock_registry):
        """测试限制返回数量"""
        mock_source = MagicMock()
        mock_source.search.return_value = [
            {"symbol": f"SYM{i}", "name": f"Name {i}", "type": "stock"}
            for i in range(20)
        ]
        
        mock_registry.list_sources.return_value = ["yfinance"]
        mock_registry.create.return_value = mock_source
        
        results = search_symbol("test", limit=5)
        
        assert len(results) == 5
    
    @patch('tick.utils.interactive.DataSourceRegistry')
    def test_search_sort_by_relevance(self, mock_registry):
        """测试按匹配度排序"""
        mock_source = MagicMock()
        mock_source.search.return_value = [
            {"symbol": "AMZN", "name": "Amazon"},       # 不匹配
            {"symbol": "AAPL", "name": "Apple Inc"},    # symbol 开头匹配
            {"symbol": "AAP", "name": "Advance Auto"},  # 完全匹配
        ]
        
        mock_registry.list_sources.return_value = ["yfinance"]
        mock_registry.create.return_value = mock_source
        
        results = search_symbol("AAP")
        
        assert len(results) == 3
        # 完全匹配应该排第一
        assert results[0]["symbol"] == "AAP"
        # symbol 开头匹配排第二
        assert results[1]["symbol"] == "AAPL"
        # 不匹配排第三（保持原始顺序）
        assert results[2]["symbol"] == "AMZN"
    
    @patch('tick.utils.interactive.DataSourceRegistry')
    def test_search_empty_results(self, mock_registry):
        """测试搜索结果为空"""
        mock_source = MagicMock()
        mock_source.search.return_value = []
        
        mock_registry.list_sources.return_value = ["yfinance"]
        mock_registry.create.return_value = mock_source
        
        results = search_symbol("XYZ123")
        
        assert len(results) == 0
    
    @patch('tick.utils.interactive.DataSourceRegistry')
    def test_search_datasource_error(self, mock_registry):
        """测试数据源搜索错误处理"""
        mock_source = MagicMock()
        mock_source.search.side_effect = Exception("Search error")
        
        mock_registry.list_sources.return_value = ["yfinance"]
        mock_registry.create.return_value = mock_source
        
        # 不应该抛出异常
        results = search_symbol("AAPL")
        assert len(results) == 0


class TestInteractiveSearch:
    """测试交互式搜索"""
    
    @patch('tick.utils.interactive.prompt')
    @patch('tick.utils.interactive.search_symbol')
    @patch('tick.utils.interactive.radiolist_dialog')
    def test_interactive_search_with_results(self, mock_dialog, mock_search, mock_prompt):
        """测试交互式搜索有结果"""
        mock_prompt.return_value = "苹果"
        mock_search.return_value = [
            {"symbol": "AAPL", "name": "Apple Inc", "type": "stock"},
            {"symbol": "sh600519", "name": "贵州茅台", "type": "stock"}
        ]
        mock_dialog.return_value.run.return_value = 0
        
        result = interactive_search()
        
        assert result == "AAPL"
    
    @patch('tick.utils.interactive.prompt')
    @patch('tick.utils.interactive.search_symbol')
    def test_interactive_search_no_input(self, mock_search, mock_prompt):
        """测试无输入"""
        mock_prompt.return_value = ""
        
        result = interactive_search()
        
        assert result is None
        mock_search.assert_not_called()
    
    @patch('tick.utils.interactive.prompt')
    @patch('tick.utils.interactive.search_symbol')
    def test_interactive_search_no_results(self, mock_search, mock_prompt):
        """测试无搜索结果"""
        mock_prompt.return_value = "XYZ"
        mock_search.return_value = []
        
        result = interactive_search()
        
        assert result is None


class TestMultiSelectSymbols:
    """测试多选品种"""
    
    @patch('tick.utils.interactive.checkboxlist_dialog')
    def test_multi_select_with_dialog(self, mock_dialog):
        """测试使用对话框多选"""
        mock_dialog.return_value.run.return_value = ["AAPL", "TSLA"]
        
        result = multi_select_symbols()
        
        assert len(result) == 2
        assert "AAPL" in result
        assert "TSLA" in result
    
    @patch('tick.utils.interactive.console')
    @patch('builtins.input')
    def test_multi_select_fallback(self, mock_input, mock_console):
        """测试降级到简单输入"""
        from tick.utils.interactive import multi_select_symbols
        
        # 模拟对话框失败
        with patch('tick.utils.interactive.checkboxlist_dialog', side_effect=Exception):
            mock_input.return_value = "1,3"
            
            result = multi_select_symbols()
            
            assert len(result) == 2


class TestConfirmDialog:
    """测试确认对话框"""
    
    @patch('prompt_toolkit.shortcuts.yes_no_dialog')
    def test_confirm_dialog_yes(self, mock_dialog):
        """测试确认"""
        mock_dialog.return_value.run.return_value = True
        
        result = confirm_dialog("确认删除？")
        
        assert result is True
    
    @patch('prompt_toolkit.shortcuts.yes_no_dialog')
    def test_confirm_dialog_no(self, mock_dialog):
        """测试取消"""
        mock_dialog.return_value.run.return_value = False
        
        result = confirm_dialog("确认删除？")
        
        assert result is False
    
    @patch('builtins.input')
    def test_confirm_dialog_fallback(self, mock_input):
        """测试降级到简单输入"""
        with patch('prompt_toolkit.shortcuts.yes_no_dialog', side_effect=Exception):
            mock_input.return_value = "y"
            
            result = confirm_dialog("确认删除？")
            
            assert result is True
    
    @patch('builtins.input')
    def test_confirm_dialog_default_yes(self, mock_input):
        """测试默认确认"""
        with patch('prompt_toolkit.shortcuts.yes_no_dialog', side_effect=Exception):
            mock_input.return_value = ""  # 空输入
            
            result = confirm_dialog("确认删除？", default=True)
            
            assert result is True
