<!-- From: /Users/billow/Developer/tick/AGENTS.md -->
# AGENTS.md — tick 项目开发指南

> 本文档供 AI 编码助手阅读，帮助理解 tick 项目的架构和开发规范。expect the reader to know nothing about the project.

---

## 项目概述

**tick** 是一个行情数据下载命令行工具，支持国内外股票、基金、期货、加密货币和指数数据的获取。

- **当前版本**: v0.3.0
- **许可证**: MIT
- **Python 版本要求**: >= 3.10（实际使用 `str | None` 等 3.10+ 联合语法）
- **CLI 入口**: `tick.main:cli`（通过 `pyproject.toml` 的 `[project.scripts]` 注册）
- **GitHub**: https://github.com/gamepunk/tick

### 支持的数据源

| 数据源 | 覆盖范围 | 是否需要 Key |
|--------|---------|-------------|
| **yfinance** | 美股、港股、ETF、期货、国际指数 | 否 |
| **akshare** | A股、北交所、国内期货、A股指数 | 否 |
| **ccxt** | 加密货币（Binance, OKX, Kraken, Bitfinex 等） | 否 |

### 主要命令

```bash
tick fetch AAPL -s 2024-01-01 --show          # 单品种下载
tick batch AAPL TSLA BTC-USD -s 2024-01-01    # 批量下载
tick search 茅台                               # 交互式搜索
tick config --init                             # 初始化配置
tick web                                       # 启动 Web UI
tick cache list                                # 查看缓存
tick cache clear                               # 清空缓存
```

---

## 技术栈

- **语言**: Python 3.10+
- **CLI 框架**: Click
- **数据处理**: pandas, numpy, pyarrow（Parquet 支持）
- **数据源**: yfinance, akshare, ccxt
- **UI 美化**: rich（表格、进度条、彩色输出、日志）
- **Web UI**: Streamlit + Plotly
- **配置**: YAML（pyyaml）
- **交互式搜索**: prompt_toolkit
- **测试**: pytest, pytest-cov, pytest-asyncio
- **构建**: setuptools, wheel

---

## 项目结构

```
tick/
├── tick/                       # 主包
│   ├── __init__.py             # 空文件
│   ├── main.py                 # CLI 入口（Click Group + 所有子命令）
│   ├── commands/               # 命令模块（当前为空目录，命令集中在 main.py）
│   │   └── __init__.py
│   ├── core/                   # 核心层
│   │   ├── __init__.py         # 空文件
│   │   ├── models.py           # 数据模型（Symbol, FetchConfig, FetchResult, BatchConfig 等）
│   │   ├── config.py           # YAML 配置管理（AppConfig, 全局配置实例）
│   │   ├── exceptions.py       # 异常层次结构（TickError, FetchError, RateLimitError 等）
│   │   └── logger.py           # 基于 Rich + RotatingFileHandler 的日志系统（TickLogger 单例）
│   ├── datasources/            # 数据源层
│   │   ├── __init__.py         # 空文件
│   │   ├── base.py             # BaseDataSource 抽象基类 + DataSourceRegistry 注册表
│   │   ├── router.py           # DataSourceRouter 自动市场识别
│   │   ├── yfinance_ds.py      # Yahoo Finance 数据源（美股、港股、国际期货、指数）
│   │   ├── akshare_ds.py       # A股/北交所/国内期货
│   │   └── ccxt_ds.py          # 加密货币（支持 11 个交易所）
│   └── utils/                  # 工具层
│       ├── __init__.py         # 空文件
│       ├── symbols.py          # 代码标准化、资产类型检测、create_symbol
│       ├── display.py          # Rich 控制台输出（表格、进度条、面板）
│       ├── cache.py            # SQLite 缓存系统（DataCache，懒加载连接）
│       ├── filename.py         # 输出文件名生成
│       ├── data_formatter.py   # DataFrame 标准化 + csv/json/parquet 序列化
│       ├── indicators.py       # 技术指标计算（MA, BOLL, RSI, MACD, KDJ, ATR, OBV）
│       ├── interactive.py      # 交互式搜索（prompt_toolkit + 降级处理）
│       └── dates.py            # 日期范围解析（resolve_date_range）
├── web/                        # Web UI（独立的顶层包）
│   ├── __init__.py             # 空文件
│   ├── app.py                  # Streamlit 应用（单品种、多品种对比、搜索）
│   └── run.py                  # Streamlit 启动脚本（subprocess 调用）
├── tests/                      # 测试
│   ├── conftest.py             # pytest fixtures（temp_dir, mock_config, sample_symbol 等）
│   ├── unit/                   # 单元测试
│   │   ├── test_main_cli.py    # CLI 命令测试（Click Runner + mock，~967 行，最全面的测试文件）
│   │   ├── test_models.py      # 数据模型测试
│   │   ├── test_config.py      # 配置系统测试
│   │   ├── test_cache.py       # 缓存测试
│   │   ├── test_data_formatter.py  # 数据格式化测试
│   │   ├── test_datasources_fetch.py   # 数据源 fetch 测试
│   │   ├── test_display.py     # 显示工具测试
│   │   ├── test_interactive.py # 交互式搜索测试
│   │   ├── test_logger.py      # 日志测试
│   │   ├── test_cli.py         # CLI 通用测试
│   │   └── test_utils.py       # 工具函数测试
│   └── integration/            # 集成/端到端测试
│       ├── test_datasources.py # 数据源路由和具体数据源集成测试
│       └── test_fetch_e2e.py   # fetch/batch 端到端流程测试（含 CSV/JSON/Parquet 格式验证）
├── pyproject.toml              # 项目配置、依赖、entry points
├── pytest.ini                  # pytest 配置（含覆盖率默认参数）
├── MANIFEST.in                 # 打包包含文件
└── README.md                   # 用户文档
```

---

## 核心架构

### 1. 数据模型 (`tick/core/models.py`)

```python
class AssetType(str, Enum):      # stock, index, futures, fund, crypto
class Interval(str, Enum):       # 1m, 5m, 15m, 30m, 60m, 1h, 1d, 1wk, 1mo
class DataSource(str, Enum):     # yfinance, akshare, ccxt

@dataclass
class Symbol:
    raw: str                     # 用户原始输入
    normalized: str              # 标准化代码
    asset_type: Optional[AssetType] = None
    market: Optional[str] = None

@dataclass
class FetchConfig:
    symbol: Symbol
    start: Optional[str] = None
    end: Optional[str] = None
    interval: Interval = Interval.DAY
    adjust: str = "qfq"          # A股复权
    exchange: str = "binance"    # 加密货币交易所
    use_cache: bool = True
    cache_ttl: int = 3600
    max_retries: int = 3
    timeout: int = 30

@dataclass
class FetchResult:
    symbol: Symbol
    data: Optional[pd.DataFrame] = None
    success: bool = False
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    fetch_time: Optional[datetime] = None
```

**关键常量**:
- `US_INDEX_CODES`: 已知美股指数代码集合（如 `GSPC`, `DJI`, `IXIC`, `VIX` 等），在 `asset_type="index"` 时自动添加 `^` 前缀
- `CCXT_EXCHANGES`: 支持的加密货币交易所列表（binance, okx, bybit, kraken, bitstamp, bitfinex, coinbase, gateio, kucoin, huobi, mexc）
- `EXCHANGE_QUOTE`: 各交易所默认计价货币映射（Binance 用 USDT，Kraken 用 USD 等）
- `ASSET_TYPE_NAMES`: 资产类型中文名称映射

### 2. 数据源基类 (`tick/datasources/base.py`)

```python
class BaseDataSource(ABC):
    name: str = "base"

    @abstractmethod
    def fetch(self, config: FetchConfig) -> FetchResult: ...

    @abstractmethod
    def validate_symbol(self, symbol: Symbol) -> bool: ...

    @abstractmethod
    def search(self, query: str, limit: int = 10) -> list[dict]: ...
```

**注册机制**:
```python
@register_datasource("yfinance")
class YFinanceDataSource(BaseDataSource):
    ...
```

### 3. 数据源路由 (`tick/datasources/router.py`)

`DataSourceRouter.detect_market(symbol)` 根据 `symbol.normalized` 和 `asset_type` 自动选择数据源：

1. 显式指定 `asset_type=crypto` → `ccxt`
2. 显式指定 `asset_type=futures` 且国内期货前缀 → `akshare`，否则 `yfinance`
3. A股/北交所（`SH*` / `SZ*` / `BJ*`）→ `akshare`
4. 国内期货前缀（`AU`, `RB`, `SC` 等且含数字）→ `akshare`
5. 加密货币后缀（`-USD`, `-USDT`）或已知代码 → `ccxt`
6. 国际期货（`=F`）→ `yfinance`
7. 港股（`.HK`）或 `.SS`/`.SZ` → `yfinance`
8. 默认 → `yfinance`

**重要陷阱**: `router.py` 中通过 `from tick.datasources import akshare_ds, ccxt_ds, yfinance_ds`（带 `noqa: F401`）来触发装饰器注册。如果新增数据源但忘记在此导入，注册不会生效。

### 4. 数据标准化 (`tick/utils/data_formatter.py`)

所有 `fetch` / `batch` 命令最终调用 `standardize_dataframe()`，输出统一列结构：

```
date, code, open, high, low, close[, volume], cum_return, daily_return
```

- `cum_return`: 累积涨跌幅（%），首日 = 0，后续相对首日收盘价
- `daily_return`: 当日涨跌幅（%），首日 = 0，后续为相邻两日收盘价变化

标准化流程：
1. 将非 DatetimeIndex 转为 DatetimeIndex（支持 `date`/`时间`/`timestamp`/`index` 列）
2. 统一列名为小写，映射中文列名（开盘→open，最高→high 等）
3. 丢弃数据源原有的涨跌幅列，重新计算
4. 日期索引转为普通列，去除时区，升序排序
5. 确保 OHLC 列存在（缺失填 NaN）
6. 计算 cum_return 和 daily_return
7. 添加 code 列

### 5. 缓存系统 (`tick/utils/cache.py`)

- 基于 **SQLite** 实现，默认 TTL = 3600 秒（1小时）
- 缓存键使用 MD5 hash，格式为 `{symbol}:{source}:{start}:{end}:{interval}`（**v0.2.0 已加入 `source` 防止不同数据源碰撞**）
- 数据使用 Python `pickle` 序列化存储为 BLOB
- 缓存失败不阻塞主流程（静默 pass）
- 全局实例通过 `get_cache()` 获取，连接懒加载
- 支持按 symbol 过滤列出、清理过期、清空全部等操作

### 6. 配置系统 (`tick/core/config.py`)

- 默认配置文件路径:
  - macOS/Linux: `~/.config/tick/config.yaml`
  - Windows: `%APPDATA%/tick/config.yaml`
- 默认输出目录: `~/Desktop`
- 包含子配置: `CacheConfig`（enabled, ttl, max_size, directory）、`DisplayConfig`（color, progress_bar, table_style, verbose）、`DatasourceConfig`（yfinance/akshare/ccxt 各自参数）
- 全局实例通过 `get_config()` / `set_config()` 访问
- `init_config()` 在配置文件不存在时自动创建默认配置

### 7. 日志系统 (`tick/core/logger.py`)

- **单例模式** (`TickLogger`)
- 控制台: `RichHandler`（INFO 级别，显示时间，不显示路径）
- 文件日志: `RotatingFileHandler`（DEBUG 级别，10MB 切分，保留 5 个备份）
- 错误日志: 单独的 error 文件（ERROR 级别）
- 默认日志目录:
  - macOS/Linux: `~/.local/share/tick/logs/`
  - Windows: `%LOCALAPPDATA%/tick/logs/`
- 文件日志初始化失败时自动降级为仅控制台日志
- 提供便捷的日志函数：`log_fetch_start`, `log_fetch_success`, `log_fetch_error`, `log_cache_hit`, `log_cache_miss`

### 8. 技术指标 (`tick/utils/indicators.py`)

支持指标及对应列名：

| 指标 | 函数 | 添加的列 |
|------|------|---------|
| `ma` | `add_moving_averages` | ma5, ma10, ma20, ma60 |
| `boll` | `add_bollinger_bands` | bb_middle, bb_upper, bb_lower, bb_width, bb_position |
| `rsi` | `add_rsi` | rsi |
| `macd` | `add_macd` | macd, macd_signal, macd_hist |
| `kdj` | `add_kdj` | kdj_k, kdj_d, kdj_j |
| `atr` | `add_atr` | atr |
| `obv` | `add_obv` | obv |
| `all` | `add_all_indicators` | 上述所有 |

通过 `apply_indicators(df, ["ma", "rsi"])` 应用。

---

## 代码风格规范

1. **类型注解**: 使用 Python 3.10+ 语法（`str | None`、`list[str]`、`dict[str, Any]`）
2. **字符串引号**: 双引号为主
3. **注释语言**: 中文
4. **分隔线风格**: `# ─────────────────────────────────────────`
5. **导入顺序**: 标准库 → 第三方库 → 项目内部模块
6. **模块 `__init__.py`**: tick/ 及其子包的 `__init__.py` 目前均为空文件，不暴露任何符号

---

## 构建和测试命令

### 运行测试

```bash
# 运行所有测试（带覆盖率）
pytest tests/ -v

# 仅运行单元测试
pytest tests/unit -v

# 仅运行集成测试
pytest tests/integration -v

# 查看 HTML 覆盖率报告
pytest --cov=tick --cov-report=html
```

### 测试配置 (`pytest.ini`)

```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = 
    -v
    --tb=short
    --strict-markers
    --cov=tick
    --cov-report=term-missing
    --cov-report=html:htmlcov
markers =
    unit: 单元测试
    integration: 集成测试
    slow: 慢速测试
```

### 当前测试状态（v0.3.0）

- **230 个测试全部通过**
- **代码覆盖率 90%**
- 主要使用 `unittest.mock.MagicMock` + `click.testing.CliRunner` 进行 CLI 测试
- 数据源 fetch 流程通过 mock 数据源完成端到端测试，避免依赖外部网络

### 测试文件组织

| 目录 | 说明 |
|------|------|
| `tests/unit/` | 单元测试，覆盖模型、配置、工具函数、CLI 命令参数解析 |
| `tests/integration/` | 集成测试，覆盖 fetch/batch 完整流程、数据格式输出、数据源路由 |
| `tests/conftest.py` | 共享 fixtures（`temp_dir`, `mock_config`, `sample_symbol`, `sample_dataframe`, `mock_yfinance_data` 等） |

### 本地开发安装

```bash
# 本地开发安装（含 web + dev 依赖）
pip install -e ".[web,dev]"

# 构建 wheel / sdist
python -m build

# 发布到 PyPI
python -m twine upload dist/*
```

### 关键配置 (`pyproject.toml`)

```toml
[project.scripts]
tick = "tick.main:cli"

[project.optional-dependencies]
web = ["streamlit", "plotly"]
dev = ["pytest", "pytest-cov", "pytest-asyncio"]

[tool.setuptools]
packages = ["tick", "tick.core", "tick.datasources", "tick.utils", "web"]
```

---

## CI/CD

GitHub Actions 工作流位于 `.github/workflows/python-package.yml`：

- 触发条件: `push` / `pull_request` 到 `main` 分支
- 运行环境: `ubuntu-latest`
- Python 版本矩阵: `3.10`, `3.11`, `3.12`
- 步骤:
  1. 安装依赖（含 flake8, pytest）
  2. flake8 语法检查（E9, F63, F7, F82 为错误，其余为警告）
  3. 运行 `pytest tests/ -v`

---

## 常见开发陷阱

1. **入口点**: CLI 入口为 `tick.main:cli`，没有 `__main__.py`。需要 `pip install -e` 才能使用 `tick` 命令。

2. **数据源注册**: 新数据源必须使用 `@register_datasource("name")` 装饰器，**并且**在 `router.py` 中导入以触发注册。

3. **代码标准化**: 始终使用 `Symbol.normalized` 进行 API 调用，而非 `Symbol.raw`。美股指数会在 `normalize_symbol()` 中自动添加 `^` 前缀。

4. **网络依赖**: yfinance、akshare、ccxt 可能因网络问题或 API 速率限制而失败。yfinance 已在 `fetch()` 中实现全异常重试逻辑（限流时额外等待）。

5. **异步代码已移除**: v0.2.0 已删除 `utils/async_fetch.py`，`batch` 命令采用**顺序下载**（`--workers` 参数已移除）。

6. **缓存 key 碰撞**: v0.2.0 修复了不同数据源使用相同 symbol 时的缓存碰撞问题，现在缓存键已包含 `source` 字段。

7. **Web UI 依赖**: `tick web` 命令需要额外安装 `[web]` 依赖（streamlit, plotly），否则会报 `ModuleNotFoundError`。

8. **akshare 分时数据边界**: `_fetch_intraday()` 中结束日期使用 `pd.Timedelta(days=1)` 确保结束日当天数据不被截断。

9. **日志与缓存目录**: 这些目录在首次运行时会自动创建，但如果系统目录不可写，日志会自动降级为控制台输出。

10. **ccxt 数据范围警告**: ccxt 交易所可能仅返回最近 N 条数据而非完整日期范围，此时 `FetchResult.metadata` 中会包含 `"warning"` 字段提示用户。

---

## 如何添加新数据源

1. 在 `tick/datasources/` 下新建文件（如 `new_ds.py`）
2. 继承 `BaseDataSource`，实现 `fetch()`, `validate_symbol()`, `search()`
3. 使用 `@register_datasource("newname")` 装饰器注册
4. 在 `tick/datasources/router.py` 中 `import` 新模块（`noqa: F401`）
5. 在 `DataSourceRouter.detect_market()` 中添加识别规则
6. 添加对应的单元测试和 mock 集成测试

---

## 如何添加新 CLI 命令

1. 在 `tick/main.py` 中使用 `@cli.command("name")` 或 `@cli.group("name")` 装饰器
2. 使用 `@click.option()` / `@click.argument()` 定义参数
3. 使用 `print_panel()`, `print_success()`, `print_error()`, `print_warning()` 等工具函数显示输出
4. 在 `tests/unit/test_main_cli.py` 中添加 `CliRunner` 测试

---

## 相关资源

- **GitHub**: https://github.com/gamepunk/tick
- **PyPI**: https://pypi.org/project/tick

---

*文档版本: v0.3.0 | 最后更新: 2026-04-24*
