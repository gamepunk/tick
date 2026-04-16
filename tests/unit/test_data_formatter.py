"""
测试数据格式化工具
"""

import json

import numpy as np
import pandas as pd
import pytest

from tick.core.models import AssetType, Symbol
from tick.utils.data_formatter import (
    format_for_output,
    standardize_dataframe,
    validate_dataframe,
)


class TestStandardizeDataFrame:
    """测试数据框标准化"""

    def test_basic_standardization(self):
        """测试基本标准化"""
        df = pd.DataFrame(
            {
                "Open": [100.0, 101.0],
                "High": [105.0, 106.0],
                "Low": [99.0, 100.0],
                "Close": [101.0, 102.0],
                "Volume": [1000, 2000],
            },
            index=pd.date_range("2024-01-01", periods=2),
        )

        sym = Symbol(raw="AAPL", normalized="AAPL")
        result = standardize_dataframe(df, sym)

        # 检查必要列存在（含指标列）
        required_cols = [
            "date",
            "code",
            "open",
            "high",
            "low",
            "close",
            "volume",
            "cum_return",
            "daily_return",
        ]
        for col in required_cols:
            assert col in result.columns, f"缺少列: {col}"

        # 检查 code 列正确
        assert all(result["code"] == "AAPL")

        # 检查 date 列存在且为 datetime
        assert pd.api.types.is_datetime64_any_dtype(result["date"])

    def test_chinese_column_names(self):
        """测试中文列名转换"""
        df = pd.DataFrame(
            {
                "开盘": [100.0, 101.0],
                "最高": [105.0, 106.0],
                "最低": [99.0, 100.0],
                "收盘": [101.0, 102.0],
                "成交量": [1000, 2000],
            },
            index=pd.date_range("2024-01-01", periods=2),
        )

        sym = Symbol(raw="sh600519", normalized="SH600519")
        result = standardize_dataframe(df, sym)

        assert "open" in result.columns
        assert "high" in result.columns
        assert "low" in result.columns
        assert "close" in result.columns
        assert "volume" in result.columns
        assert "cum_return" in result.columns
        assert "daily_return" in result.columns

    def test_cum_return_and_daily_return(self):
        """测试累积涨跌幅与当日涨跌幅计算"""
        df = pd.DataFrame(
            {
                "close": [100.0, 102.0, 101.0],
                "open": [99.0, 100.0, 101.0],
                "high": [105.0, 106.0, 105.0],
                "low": [98.0, 99.0, 100.0],
                "volume": [1000, 2000, 1500],
            },
            index=pd.date_range("2024-01-01", periods=3),
        )

        sym = Symbol(raw="AAPL", normalized="AAPL")
        result = standardize_dataframe(df, sym)

        # ── cum_return：相对第一天收盘价的累积涨跌幅 ──────────────────
        assert "cum_return" in result.columns
        # 第一天基准 0
        assert abs(result["cum_return"].iloc[0] - 0.0) < 0.0001
        # 第二天：(102-100)/100*100 = 2.0
        assert abs(result["cum_return"].iloc[1] - 2.0) < 0.0001
        # 第三天：(101-100)/100*100 = 1.0
        assert abs(result["cum_return"].iloc[2] - 1.0) < 0.0001

        # ── daily_return：相邻两日收盘价涨跌幅 ───────────────────────
        assert "daily_return" in result.columns
        # 第一天填充为 0
        assert abs(result["daily_return"].iloc[0] - 0.0) < 0.0001
        # 第二天：(102-100)/100*100 = 2.0
        assert abs(result["daily_return"].iloc[1] - 2.0) < 0.0001
        # 第三天：(101-102)/102*100 ≈ -0.9804
        assert abs(result["daily_return"].iloc[2] - (-0.9804)) < 0.001

        # 不应再有旧的 pct_change 列
        assert "pct_change" not in result.columns

    def test_empty_dataframe(self):
        """测试空数据框处理"""
        df = pd.DataFrame()
        sym = Symbol(raw="AAPL", normalized="AAPL")
        result = standardize_dataframe(df, sym)

        # 应该返回空数据框
        assert result is not None
        assert len(result) == 0


class TestFormatForOutput:
    """测试输出格式化"""

    @pytest.fixture
    def sample_df(self):
        """示例数据框"""
        return pd.DataFrame(
            {
                "date": pd.to_datetime(["2024-01-01", "2024-01-02"]),
                "code": ["AAPL", "AAPL"],
                "open": [100.0, 101.0],
                "high": [105.0, 106.0],
                "low": [99.0, 100.0],
                "close": [101.0, 102.0],
                "volume": [1000, 2000],
                "cum_return": [0.0, 0.9901],
                "daily_return": [0.0, 0.9901],
            }
        )

    def test_format_csv(self, sample_df):
        """测试 CSV 格式输出"""
        output = format_for_output(sample_df, fmt="csv")

        assert isinstance(output, str)
        assert "date,code,open,high,low,close,volume" in output
        assert "AAPL" in output

    def test_format_json(self, sample_df):
        """测试 JSON 格式输出（records 格式，带缩进）"""
        output = format_for_output(sample_df, fmt="json")

        assert isinstance(output, str)

        # 必须是合法 JSON，且为 records（列表）格式
        records = json.loads(output)
        assert isinstance(records, list), "JSON 输出应为列表（records 格式）"
        assert len(records) == 2

        # 每条记录包含预期字段
        first = records[0]
        assert "code" in first
        assert first["code"] == "AAPL"
        assert "open" in first
        assert "close" in first

        # 应为带缩进的格式，而非紧凑的 `[{`
        assert "\n" in output, "JSON 输出应包含换行（indent=2）"

    def test_format_parquet(self, sample_df):
        """测试 Parquet 格式输出"""
        output = format_for_output(sample_df, fmt="parquet")

        assert isinstance(output, bytes)
        assert len(output) > 0

    def test_invalid_format(self, sample_df):
        """测试无效格式"""
        with pytest.raises(ValueError, match="不支持的输出格式"):
            format_for_output(sample_df, fmt="xml")


class TestValidateDataFrame:
    """测试数据框验证"""

    def test_valid_dataframe(self):
        """测试有效数据框"""
        df = pd.DataFrame(
            {
                "date": pd.to_datetime(["2024-01-01"]),
                "code": ["AAPL"],
                "open": [100.0],
                "high": [105.0],
                "low": [99.0],
                "close": [101.0],
            }
        )

        is_valid, msg = validate_dataframe(df)
        assert is_valid is True
        assert msg == ""

    def test_empty_dataframe(self):
        """测试空数据框"""
        df = pd.DataFrame()

        is_valid, msg = validate_dataframe(df)
        assert is_valid is False
        assert "数据为空" in msg

    def test_missing_required_columns(self):
        """测试缺少必要列"""
        df = pd.DataFrame(
            {
                "date": pd.to_datetime(["2024-01-01"]),
                "code": ["AAPL"],
                # 缺少 open, high, low, close
            }
        )

        is_valid, msg = validate_dataframe(df)
        assert is_valid is False
        assert "缺少必要列" in msg

    def test_all_nan_values(self):
        """测试全部 NaN 值"""
        df = pd.DataFrame(
            {
                "date": pd.to_datetime(["2024-01-01"]),
                "code": ["AAPL"],
                "open": [np.nan],
                "high": [np.nan],
                "low": [np.nan],
                "close": [np.nan],
            }
        )

        is_valid, msg = validate_dataframe(df)
        assert is_valid is False
        assert "NaN" in msg
