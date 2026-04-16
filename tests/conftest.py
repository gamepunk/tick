"""
Pytest 配置和 fixtures
"""

import shutil

# 添加项目根目录到路径
import sys
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from tick.core.config import AppConfig, set_config
from tick.core.models import AssetType, FetchConfig, Interval, Symbol


@pytest.fixture
def temp_dir():
    """临时目录 fixture"""
    tmp = tempfile.mkdtemp()
    yield Path(tmp)
    shutil.rmtree(tmp)


@pytest.fixture
def mock_config(temp_dir):
    """测试配置 fixture"""
    config = AppConfig(
        default_output_dir=str(temp_dir / "output"),
    )
    set_config(config)
    return config


@pytest.fixture
def sample_symbol():
    """示例 Symbol fixture"""
    return Symbol(raw="AAPL", normalized="AAPL", asset_type=AssetType.STOCK)


@pytest.fixture
def sample_config(sample_symbol):
    """示例 FetchConfig fixture"""
    return FetchConfig(
        symbol=sample_symbol,
        start="2024-01-01",
        end="2024-01-31",
        interval=Interval.DAY,
    )


@pytest.fixture
def sample_dataframe():
    """示例 DataFrame fixture"""
    dates = pd.date_range("2024-01-01", "2024-01-31", freq="D")
    np.random.seed(42)
    data = {
        "open": np.random.uniform(100, 110, len(dates)),
        "high": np.random.uniform(110, 120, len(dates)),
        "low": np.random.uniform(90, 100, len(dates)),
        "close": np.random.uniform(100, 110, len(dates)),
        "volume": np.random.randint(1000000, 10000000, len(dates)),
    }
    df = pd.DataFrame(data, index=dates)
    df.index.name = "date"
    return df


@pytest.fixture
def mock_yfinance_data():
    """模拟 yfinance 返回数据"""
    dates = pd.date_range("2024-01-01", periods=10, freq="D", tz="UTC")
    data = {
        "Open": [100.0] * 10,
        "High": [110.0] * 10,
        "Low": [90.0] * 10,
        "Close": [105.0] * 10,
        "Volume": [1000000] * 10,
    }
    return pd.DataFrame(data, index=dates)
