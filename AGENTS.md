# AGENTS.md — tick 项目开发指南

> 本文档供 AI 编码助手阅读，帮助理解 tick 项目的架构和开发规范。

## 项目概述

tick 是一个行情数据下载命令行工具，支持国内外股票、基金、期货、加密货币和指数数据的获取。项目采用单文件架构，所有核心功能集中在 `tick/cli.py` 中实现。

**主要功能:**
- 多数据源支持：yfinance（美股/港股/国际指数）、akshare（A股/国内期货/A股指数）、ccxt（加密货币）
- 多种输出格式：CSV、JSON、Parquet
- 批量下载和合并数据（适合制作 Bar Chart Race 可视化）
- 自动识别市场和资产类型
- 丰富的命令行交互界面（使用 rich 库）

## 技术栈

- **语言**: Python 3.10+
- **CLI 框架**: Click
- **数据处理**: pandas, pyarrow（Parquet 支持）
- **数据源**: yfinance, akshare, ccxt
- **UI 美化**: rich（表格、进度条、彩色输出）
- **构建工具**: setuptools
- **CI/CD**: GitHub Actions

## 项目结构

```
tick/
├── tick/
│   ├── __init__.py          # 空文件（包标记）
│   └── cli.py               # 主程序（约 1144 行，包含所有功能）
├── Formula/
│   └── tick.rb              # Homebrew 安装公式
├── .github/workflows/
│   └── python-package.yml   # GitHub Actions CI 配置
├── pyproject.toml           # Python 包配置
├── MANIFEST.in              # 打包包含文件清单
├── README.md                # 详细使用文档（中文）
└── LICENSE                  # MIT 许可证
```

## 代码组织

### 核心模块（cli.py）

| 函数/类 | 职责 |
|---------|------|
|`get_desktop_path()`|获取跨平台桌面路径（支持中英文等多语言）|
|`detect_market(symbol)`|自动识别 symbol 所属市场和数据源|
|`build_ccxt_symbol()`|转换 tick symbol 格式为 ccxt 格式|
|`fetch_ccxt()`|从加密货币交易所获取数据（支持 5 个交易所）|
|`fetch_yfinance()`|获取美股、港股、国际期货和指数数据|
|`fetch_akshare_cn()`|获取 A 股和场内基金数据（支持分时）|
|`fetch_akshare_futures()`|获取国内期货数据|
|`add_pct_column()`|添加涨跌幅列（cum_pct, pct_change）|
|`print_summary()`|打印数据摘要表格|
|`build_filename()`|构建输出文件名|
|`fetch_display_names()`|批量获取品种显示名称|

### CLI 命令

| 命令 | 功能 |
|------|------|
|`tick fetch <SYMBOL>`|下载单个品种数据|
|`tick batch <SYMBOLS...>`|批量下载多个品种（各自保存）|
|`tick batch-merge <SYMBOLS...>`|批量下载并合并为长格式 CSV|
|`tick info <SYMBOL>`|查看品种基本信息（仅 yfinance）|
|`tick symbols`|显示常用品种参考表|
|`tick help-symbols`|显示 Symbol 格式说明|

### 全局常量

```python
ASSET_TYPES = {
    "stock": "股票",
    "fund": "基金/ETF", 
    "futures": "期货",
    "crypto": "加密货币",
}

CCXT_EXCHANGES = ["binance", "okx", "bybit", "kraken", "bitstamp"]

EXCHANGE_QUOTE = {
    "binance": "USDT",
    "okx": "USDT",
    "bybit": "USDT",
    "kraken": "USD",
    "bitstamp": "USD",
}
```

## 开发规范

### 代码风格

1. **注释语言**: 中文（与项目主要语言一致）
2. **字符串引号**: 双引号为主
3. **类型注解**: 使用 Python 3.10+ 语法（如 `str | None`）
4. **分隔线**: 使用 `# ─────────────────────────────────────────` 作为区块分隔

### Symbol 格式规则

| 市场 | 格式示例 | 数据源 |
|------|---------|--------|
| 美股 | `AAPL`, `TSLA` | yfinance |
| 港股 | `0700.HK`, `9988.HK` | yfinance |
| A股 | `sh600519`, `sz000858` | akshare |
| 加密货币 | `BTC-USD`, `ETH-USD` | ccxt |
| 国际期货 | `GC=F`, `CL=F` | yfinance |
| 美股指数 | `^GSPC`, `^DJI` | yfinance |
| A股指数 | `sh000001`, `sz399006` | akshare |
| 国内期货 | `AU`, `AG` | akshare |

### 文件名生成规则

```
{symbol}_{start}_{end}_{interval}_{source_tag}_{adjust}.{format}

# 示例
AAPL_20240101_20250101_1d_yf.csv              # 美股
BTC-USD_20160101_20250101_1d_ccxt_kraken.csv  # 加密货币（Kraken）
sh600519_20240101_20250101_1d_ak_qfq.csv      # A股（前复权）
^GSPC_20240101_20250101_1d_yf_idx.csv         # 美股指数
```

## 构建和发布

### 本地开发安装

```bash
# 克隆后本地运行
python tick.py fetch AAPL -s 2024-01-01

# 可编辑模式安装
pip install -e .
tick fetch AAPL -s 2024-01-01
```

### 打包发布

```bash
# 构建分发包
python -m build

# 发布到 PyPI（需权限）
python -m twine upload dist/*
```

### Homebrew 发布

Formula 位于 `Formula/tick.rb`，更新版本时需修改：
- `url`: 新的 tar.gz 地址
- `sha256`: 新包的校验和

## 测试

当前项目**没有正式的测试套件**。CI 配置中虽然包含 pytest 步骤，但主要依赖：
1. 手动测试各种 symbol 和参数组合
2. 使用 `tick symbols` 和 `tick help-symbols` 验证基础功能
3. 分别测试各个数据源（yfinance、akshare、ccxt）

**建议添加测试时:**
- 为 `detect_market()` 添加单元测试（覆盖各种 symbol 格式）
- 为 `build_filename()` 添加边界测试
- 为数据获取函数添加 mock 测试（避免真实 API 调用）

## 添加新功能注意事项

### 添加新的数据源

1. 实现 `fetch_<source>()` 函数
2. 在 `detect_market()` 中添加识别规则
3. 在 `_do_fetch()` 中添加分发逻辑
4. 在 `build_filename()` 中添加 source_tag 映射
5. 更新 `README.md` 的文档

### 添加新的 CLI 命令

1. 使用 `@cli.command("name")` 装饰器
2. 使用 `@click.option()` 定义参数
3. 命令函数名使用 `cmd_<name>` 命名规范
4. 在 docstring 中添加使用示例（包含 `\b` 防止 rewrap）

### 添加新的资产类型

1. 更新 `ASSET_TYPES` 字典
2. 更新 `detect_asset_type()` 函数
3. 更新 `tick symbols` 命令的数据
4. 更新 README 中的相关表格

## 常见问题处理

### yfinance 限流

代码已内置 3 次重试机制（间隔 10/20/30 秒）。如仍限流，建议用户使用 ccxt 数据源。

### 加密货币历史数据深度

- Binance/OKX/Bybit: 2017 年起
- Kraken: 2013 年起  
- Bitstamp: 2011 年起

需要在帮助文档中提示用户选择合适的交易所。

### A股分时数据限制

akshare 的 `stock_zh_a_hist_min_em` 接口通常只支持最近 1 年的分时数据。

## 相关资源

- **GitHub**: https://github.com/gamepunk/tick
- **Python 包**: tick (PyPI)
- **Homebrew**: Formula/tick.rb

---

*文档版本: v0.2.0 | 最后更新: 2026-04-09*
