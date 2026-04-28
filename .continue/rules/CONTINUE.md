# tick 项目开发指南

> 本文档由 Continue 自动加载，帮助 AI 编码助手理解 tick 项目的架构、规范和工作流程。
>
> **最后更新**: 基于 v0.3.1 代码分析

---

## 1. Project Overview

**tick** is a market data CLI tool for downloading stock, futures, crypto, and index data. It supports multiple data sources (yfinance for US/international markets, akshare for Chinese markets, ccxt for crypto exchanges) and provides a unified, standardized output format.

### Key Technologies

| Technology | Purpose |
|-----------|---------|
| **Python 3.10+** | Language (`str \| None` syntax) |
| **Click** | CLI framework |
| **pandas / numpy** | Data processing |
| **rich** | Console UI (tables, progress bars, colored output) |
| **yfinance** | US/HK/international stock, futures, index data |
| **akshare** | A-shares, Beijing Exchange, domestic futures |
| **ccxt** | Crypto (Binance, OKX, Kraken, Bitfinex, Coinbase, Gate.io, KuCoin, Huobi, MEXC) |
| **SQLite** | Built-in data caching |
| **pyarrow** | Parquet output support |
| **Streamlit + Plotly** | Web UI |
| **pytest** | Testing (230 tests, 90% coverage) |
| **prompt_toolkit** | Interactive search |
| **PyYAML** | Configuration files |

### High-Level Architecture

The project follows a **layered architecture**:

```
CLI Layer (main.py) →  Core Layer (models/config/exceptions) → DataSource Layer → External APIs
                           ↕
                     Utility Layer (display/cache/formatting/indicators)
```

1. **CLI Layer** (`tick/main.py`): All Click commands (`fetch`, `batch`, `search`, `config`, `cache`, `web`)
2. **Core Layer** (`tick/core/`): Data models, YAML configuration, exception hierarchy, logging
3. **DataSource Layer** (`tick/datasources/`): Abstract base class, registry pattern, router, and 3 concrete implementations
4. **Utility Layer** (`tick/utils/`): Display helpers, SQLite caching, data standardization, technical indicators, interactive search, symbol normalization
5. **Web UI** (`web/`): Standalone Streamlit application with K-line charts, multi-symbol comparison, and search

---

## 2. Getting Started

### Prerequisites

- **Python**: >= 3.10
- **pip**: Latest version recommended

### Installation

```bash
# Basic CLI installation
pip install tick

# With Web UI support
pip install "tick[web]"

# Development installation (includes test dependencies)
pip install "tick[web,dev]"

# Local editable install for development
git clone https://github.com/gamepunk/tick.git
cd tick
pip install -e ".[web,dev]"
```

### Basic Usage

```bash
# Download a single symbol (with auto-displayed summary)
tick fetch AAPL -s 2024-01-01

# Batch download multiple symbols
tick batch AAPL TSLA BTC-USD -s 2024-01-01

# Interactive search
tick search 茅台

# Initialize config file
tick config --init

# Launch Web UI
tick web

# Cache management
tick cache list
tick cache clear --expired
```

### Running Tests

```bash
# All tests with coverage
pytest tests/ -v

# Unit tests only
pytest tests/unit -v

# Integration tests only
pytest tests/integration -v

# HTML coverage report
pytest --cov=tick --cov-report=html
```

### Building & Publishing

```bash
# Build wheel + sdist
python -m build

# Publish to PyPI
python -m twine upload dist/*
```

---

## 3. Project Structure

### Directory Layout

```
tick/
├── tick/                         # Main package
│   ├── main.py                   # CLI entry point (Click group + all subcommands)
│   ├── commands/                 # Reserved for future command modules (currently empty)
│   ├── core/                     # Core domain logic
│   │   ├── models.py             # Data models: Symbol, FetchConfig, FetchResult, AssetType, Interval
│   │   ├── config.py             # YAML config management (AppConfig, global singleton)
│   │   ├── exceptions.py         # Exception hierarchy (TickError, FetchError, RateLimitError, etc.)
│   │   └── logger.py             # Rich + RotatingFileHandler logging (TickLogger singleton)
│   ├── datasources/              # Data source implementations
│   │   ├── base.py               # BaseDataSource ABC + DataSourceRegistry (decorator-based)
│   │   ├── router.py             # DataSourceRouter — automatic market detection
│   │   ├── yfinance_ds.py        # Yahoo Finance: US/HK stocks, ETFs, futures, indices
│   │   ├── akshare_ds.py         # A-shares, Beijing Exchange, domestic futures
│   │   └── ccxt_ds.py            # Crypto (11 exchanges via CCXT)
│   └── utils/                    # Utility toolkit
│       ├── symbols.py            # Symbol normalization, asset type detection, create_symbol()
│       ├── display.py            # Rich console output (tables, progress bars, panels)
│       ├── cache.py              # SQLite caching system (DataCache, lazy connection)
│       ├── filename.py           # Output filename generation
│       ├── data_formatter.py     # DataFrame standardization + csv/json/parquet serialization
│       ├── indicators.py         # Technical indicators (MA, BOLL, RSI, MACD, KDJ, ATR, OBV)
│       ├── interactive.py        # Interactive search (prompt_toolkit + graceful degradation)
│       └── dates.py              # Date range resolution
├── web/                          # Web UI (standalone top-level package)
│   ├── app.py                    # Streamlit application
│   └── run.py                    # Streamlit subprocess launcher
├── tests/                        # Test suite
│   ├── conftest.py               # Shared fixtures (temp_dir, mock_config, sample_dataframe, etc.)
│   ├── unit/                     # Unit tests (models, config, CLI, cache, formatter, etc.)
│   └── integration/              # Integration tests (end-to-end fetch/batch, output format validation)
├── pyproject.toml                # Project metadata, dependencies, entry points
├── pytest.ini                    # Pytest configuration (coverage defaults)
├── MANIFEST.in                   # Packaging include rules
├── AGENTS.md                     # Detailed project guide (source of this document)
├── README.md                     # User documentation
└── .github/workflows/python-package.yml  # CI/CD (3.10, 3.11, 3.12)
```

### Key Entry Points

| File | Role |
|------|------|
| `tick/main.py:cli` | CLI entry point (registered in `pyproject.toml` as `tick = "tick.main:cli"`) |
| `web/run.py:run_web()` | Web UI launcher (subprocess calls `streamlit run`) |
| `tests/conftest.py` | Shared test fixtures |

### Important Configuration Files

| File | Purpose |
|------|---------|
| `pyproject.toml` | Project metadata, dependencies, optional `[web]`/`[dev]` extras, entry points |
| `pytest.ini` | Test configuration with coverage defaults |
| `~/.config/tick/config.yaml` (macOS/Linux) | User config (macOS/Linux) |
| `%APPDATA%/tick/config.yaml` (Windows) | User config (Windows) |

---

## 4. Development Workflow

### Coding Standards

1. **Type annotations**: Python 3.10+ syntax (`str | None`, `list[str]`, `dict[str, Any]`)
2. **String quotes**: Double quotes preferred
3. **Comments**: Chinese (中文) for inline comments
4. **Separation lines**: `# ─────────────────────────────────────────`
5. **Import order**: Standard library → Third-party → Internal modules
6. **Module `__init__.py`**: All `__init__.py` files are currently empty (no symbol exports)

### Testing Approach

- **Framework**: pytest with `click.testing.CliRunner` for CLI tests
- **Mocking**: `unittest.mock.MagicMock` / `unittest.mock.patch` for external dependencies
- **Coverage target**: 90%+ (current: 230 tests passing)
- **Test markers**: `unit`, `integration`, `slow` (defined in `pytest.ini`)
- **Key test patterns**:
  - CLI commands: Use `CliRunner` + `patch` to mock data sources and cache
  - Models: Test dataclass construction and validation
  - Data sources: Mock the `fetch()` method to return controlled `FetchResult` objects
  - Integration: Test full end-to-end flow with mocked external calls

### Build & Deployment

1. **Build**: `python -m build` (setuptools + wheel)
2. **Publish**: `twine upload dist/*`
3. **CI/CD**: GitHub Actions on push/PR to `main` (Python 3.10, 3.11, 3.12)
   - flake8 linting (E9/F63/F7/F82 as errors, rest as warnings)
   - `pytest tests/ -v`

### Contribution Guidelines

- Fork the repository and create a feature branch
- Ensure all tests pass (`pytest tests/ -v`)
- Maintain or improve code coverage
- Follow the existing code style (type annotations, Chinese comments)
- Update `AGENTS.md` and `README.md` for significant changes
- Version bump in `pyproject.toml`

---

## 5. Key Concepts

### Domain Terminology

| Term | Definition |
|------|-----------|
| **Symbol** | A market instrument identifier (e.g., `AAPL`, `sh600519`, `BTC-USD`) |
| **Normalized** | The API-ready version of a symbol (e.g., `GSPC` → `^GSPC` for indices) |
| **AssetType** | Enum: `stock`, `index`, `futures`, `fund`, `crypto` |
| **Interval** | Kline period: `1m`, `5m`, `15m`, `30m`, `60m`, `1h`, `1d`, `1wk`, `1mo` |
| **DataSource** | The backend providing data: `yfinance`, `akshare`, `ccxt` |
| **FetchConfig** | Immutable configuration for a data fetch operation |
| **FetchResult** | Result of a fetch operation (data, success flag, error message, metadata) |
| **Adjust** | A-share adjustment method: `qfq` (前复权) or `hfq` (后复权) |
| **Standardized DataFrame** | Unified output with columns: `date, code, open, high, low, close[, volume], cum_return, daily_return` |

### Core Abstractions

#### `Symbol` (`tick/core/models.py`)
```python
@dataclass
class Symbol:
    raw: str              # User's original input (e.g., "aapl")
    normalized: str       # API-ready form (e.g., "AAPL")
    asset_type: Optional[AssetType] = None
    market: Optional[str] = None
```

#### `FetchConfig` & `FetchResult` (`tick/core/models.py`)
```python
@dataclass
class FetchConfig:
    symbol: Symbol
    start: Optional[str] = None      # "YYYY-MM-DD"
    end: Optional[str] = None
    interval: Interval = Interval.DAY
    adjust: str = "qfq"              # A-share adjustment
    exchange: str = "binance"        # Crypto exchange
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

#### `BaseDataSource` (`tick/datasources/base.py`)
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

### Design Patterns

1. **Registry Pattern** (`DataSourceRegistry`): Data sources are registered via `@register_datasource("name")` decorator. Registration is triggered by imports in `router.py` (with `noqa: F401`).

2. **Singleton Pattern** (`TickLogger`, global config/cache): Both `logger.py` and `cache.py` use global `_instance = None` + `get_instance()` pattern.

3. **Strategy Pattern** (`DataSourceRouter`): Automatically selects the appropriate data source based on symbol characteristics, using market detection rules.

4. **Template Method** (`BaseDataSource`): Defines the abstract interface; concrete data sources implement the three abstract methods.

5. **Facade Pattern**: `main.py` presents a unified CLI interface that delegates to the datasources, cache, formatters, and display utilities.

### Constant Definitions

Key constants in `tick/core/models.py`:

- **`US_INDEX_CODES`**: Set of known US index codes (e.g., `GSPC`, `DJI`, `IXIC`, `VIX`, `RUT`, `FTSE`, `N225`, `HSI`) — used to auto-add `^` prefix
- **`CCXT_EXCHANGES`**: List of 11 supported crypto exchanges
- **`EXCHANGE_QUOTE`**: Default quote currency per exchange (e.g., `binance` → `USDT`, `kraken` → `USD`)
- **`ASSET_TYPE_NAMES`**: Chinese name mapping for asset types (e.g., `stock` → "股票")

---

## 6. Common Tasks

### Adding a New CLI Command

1. Add a new function in `tick/main.py` with `@cli.command("name")` or `@cli.group("name")`
2. Define arguments with `@click.argument()` and options with `@click.option()`
3. Use display utilities (`print_panel()`, `print_success()`, `print_error()`, `print_warning()`) for output
4. Add tests in `tests/unit/test_main_cli.py` using `CliRunner`
5. **Example** — see `cmd_fetch`, `cmd_batch`, `cmd_search` in `tick/main.py`

### Adding a New Data Source

1. Create a new file in `tick/datasources/` (e.g., `new_ds.py`)
2. Inherit from `BaseDataSource` and implement `fetch()`, `validate_symbol()`, `search()`
3. Decorate with `@register_datasource("newname")`
4. **IMPORTANT**: Import the module in `tick/datasources/router.py` (with `# noqa: F401`) to trigger registration
5. Add routing rules in `DataSourceRouter.detect_market()` to route symbols to your new data source
6. Add unit tests and mock integration tests

### Adding a New Technical Indicator

1. Add the calculation function in `tick/utils/indicators.py`
2. Add it to the `INDICATOR_FUNCTIONS` dictionary
3. Add it to `add_all_indicators()` if it should be included in the "all" option
4. Update `README.md` with the new indicator name and column names

### Understanding the Data Flow

When a user runs `tick fetch AAPL`:

1. **CLI Parsing**: Click parses arguments → creates `FetchConfig`
2. **Date Resolution**: `resolve_date_range()` fills in default start/end dates
3. **Symbol Creation**: `create_symbol()` normalizes the symbol (e.g., handles `^` prefix for indices)
4. **Market Detection**: `DataSourceRouter.detect_market()` determines the data source
5. **Cache Check**: `DataCache.get()` checks if cached data exists (unless `--no-cache`)
6. **Data Fetch**: If cache miss, `BaseDataSource.fetch()` downloads from external API
7. **Cache Store**: Result is written to SQLite cache
8. **Standardization**: `standardize_dataframe()` converts to unified column format
9. **Indicators**: Optional technical indicators are computed (`apply_indicators()`)
10. **Output**: Data is written to CSV/JSON/Parquet file
11. **Display**: `print_data_summary()` shows a summary table (unless `--no-show`)

### Understanding the Standardized Output

Every fetch/batch command produces DataFrames with this unified structure:

```
date, code, open, high, low, close[, volume], cum_return, daily_return
```

- `cum_return`: Cumulative return (%) — first day = 0, subsequent days relative to first close
- `daily_return`: Daily change (%) — first day = 0, subsequent days from previous close

The standardization process in `data_formatter.py`:
1. Converts to DatetimeIndex (handles `date`/`时间`/`timestamp`/`index` columns)
2. Lowercases and maps column names (including Chinese → English)
3. Drops source-provided pct_change columns (recalculates its own)
4. Removes timezone, sorts ascending by date
5. Fills missing OHLC columns with NaN
6. Calculates `cum_return` and `daily_return`

### Market Detection Rules (DataSourceRouter)

The router checks symbols in this priority order:

1. `AssetType.CRYPTO` → `ccxt`
2. `AssetType.FUTURES` → `akshare` (domestic prefixes) or `yfinance` (international)
3. `AssetType.STOCK/INDEX/FUND` → `akshare` (SH/SZ/BJ prefix) or `yfinance`
4. Auto-detect: `SH`/`SZ`/`BJ` prefix → `akshare`
5. Auto-detect: Domestic futures prefixes + digits → `akshare`
6. Auto-detect: `-USD` / `-USDT` suffix or known crypto codes → `ccxt`
7. Auto-detect: `=F` suffix → `yfinance`
8. Auto-detect: `.HK` / `.SS` / `.SZ` suffix → `yfinance`
9. Default → `yfinance`

---

## 7. Troubleshooting

### Common Issues

| Issue | Solution |
|-------|----------|
| `ModuleNotFoundError: No module named 'plotly'` | Install web deps: `pip install "tick[web]"` |
| `tick: command not found` | Need `pip install -e .` for local development (no `__main__.py`) |
| Missing `tick/cache` commands | Ensure you're using v0.2.0+ (cache was added in v0.1.0) |
| yfinance returns no data | Check if the symbol exists; try with `--asset index` for indices; the DS has auto-retry logic |
| akshare Chinese market data fails | Could be network issues (China firewall); the DS has exponential backoff retry |
| ccxt returns limited data | Exchanges only return recent N candles; check `metadata.warning` field |
| `pip install -e .` fails | Ensure you have setuptools≥61.0 and wheel installed |
| Tests fail with network errors | Tests should mock external APIs; if they don't, check your internet connection |
| Web UI doesn't start | Ensure streamlit and plotly are installed: `pip install "tick[web]"` |

### Debugging Tips

- **Enable verbose mode**: `tick --verbose fetch AAPL`
- **Check logs**:
  - macOS/Linux: `~/.local/share/tick/logs/`
  - Windows: `%LOCALAPPDATA%/tick/logs/`
- **Check cache entries**: `tick cache list`
- **Clear cache to force refresh**: `tick cache clear`
- **Disable cache**: `tick fetch AAPL --no-cache`
- **Rich console output**: The `Console` object in `tick/utils/display.py` can be used for debugging output
- **Test specific functionality**: `pytest tests/unit/test_main_cli.py::TestFetchCommand -v`

### Development Traps

1. **DataSource registration**: New data sources must be both decorated with `@register_datasource()` **AND** imported in `router.py`
2. **Symbol normalization**: Always use `Symbol.normalized` for API calls, not `Symbol.raw`
3. **Index symbols**: US index codes auto-get `^` prefix when `asset_type="index"`
4. **Cache key collisions**: v0.2.0 fixed this by including `source` in the cache key
5. **Async code removed**: v0.2.0 removed `utils/async_fetch.py`; batch uses sequential fetching
6. **akshare intraday boundary**: Uses `pd.Timedelta(days=1)` to ensure end-of-day data isn't truncated
7. **Log directory fallback**: If system `~/.local/share/` is not writable, logs degrade to console-only
8. **CLI entry point**: Must use `pip install -e .` for the `tick` command to work; there is no `__main__.py`
9. **`__init__.py`**: All are empty files — they do not re-export any symbols
10. **`--workers` removed**: Batch download no longer supports concurrency (sequential only)

---

## 8. References

### Documentation

- **Project README**: `README.md` (user-facing documentation with examples)
- **AGENTS.md**: Detailed project guide for AI assistants (this document's source)
- **tests/COVERAGE.md**: Test coverage documentation

### External Resources

- **GitHub Repository**: [https://github.com/gamepunk/tick](https://github.com/gamepunk/tick)
- **PyPI**: [https://pypi.org/project/tick](https://pypi.org/project/tick)
- **Click Documentation**: [https://click.palletsprojects.com/](https://click.palletsprojects.com/)
- **Rich Documentation**: [https://rich.readthedocs.io/](https://rich.readthedocs.io/)
- **pandas Documentation**: [https://pandas.pydata.org/](https://pandas.pydata.org/)
- **yfinance**: [https://github.com/ranaroussi/yfinance](https://github.com/ranaroussi/yfinance)
- **akshare**: [https://github.com/akfamily/akshare](https://github.com/akfamily/akshare)
- **ccxt**: [https://github.com/ccxt/ccxt](https://github.com/ccxt/ccxt)
- **Streamlit**: [https://streamlit.io/](https://streamlit.io/)
- **Plotly**: [https://plotly.com/python/](https://plotly.com/python/)

### Key Dependencies

| Package | Version (approx.) | Purpose |
|---------|-------------------|---------|
| click | ≥8.0 | CLI framework |
| pandas | ≥1.5 | Data manipulation |
| rich | ≥13.0 | Terminal UI |
| pyyaml | ≥6.0 | Configuration |
| yfinance | ≥0.2.0 | Yahoo Finance data |
| akshare | ≥1.0 | Chinese market data |
| ccxt | ≥4.0 | Crypto exchange data |
| pyarrow | ≥12.0 | Parquet support |
| prompt_toolkit | ≥3.0 | Interactive prompts |
| streamlit | ≥1.0 (optional) | Web UI |
| plotly | ≥5.0 (optional) | Web charts |
| pytest | ≥7.0 (dev) | Testing |
| pytest-cov | ≥4.0 (dev) | Coverage |
| setuptools | ≥61.0 | Build system |
| wheel | latest | Build system |
