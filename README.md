# tick v0.1.0

行情数据下载命令行工具，支持国内外股票、基金、期货、加密货币、**指数**。

```bash
# 单品种下载
tick fetch BTC-USD -s 2016-01-01 --exchange kraken --show
tick fetch sh600519 -s 2024-01-01
tick fetch GSPC --asset index -s 2024-01-01    # 标普500指数（自动转为 ^GSPC）
tick fetch sh000001 --asset index -s 2024-01-01 # 上证指数

# 批量下载
tick batch AAPL TSLA GC=F -s 2024-01-01 -d ./data
tick batch-merge BTC-USD ETH-USD SOL-USD -s 2020-01-01 -o crypto.csv

# 新增功能
tick fetch AAPL --indicator rsi --show          # 添加技术指标
tick batch AAPL TSLA --workers 4                # 异步并发下载
tick search 茅台                                 # 交互式搜索
tick config --init                               # 初始化配置
tick-web                                         # 启动 Web UI
```

---

## 安装

```bash
# 基础安装
pip install tick

# 完整安装（包含 Web UI 和开发依赖）
pip install "tick[web,dev]"
```

---

## 快速开始

```bash
# 初始化配置（可选）
tick config --init

# 下载美股数据
tick fetch AAPL --show

# 下载A股数据
tick fetch sh600519 -s 2024-01-01

# 下载加密货币
tick fetch BTC-USD --exchange kraken --show

# 启动 Web UI
tick-web
```

---

## 数据源

| 数据源 | 覆盖范围 | 是否需要 Key |
|--------|---------|-------------|
| **ccxt** | 加密货币（Binance, OKX, Kraken 等） | ❌ 无需 |
| **yfinance** | 美股、港股、ETF、期货、国际指数 | ❌ 无需 |
| **akshare** | A股、北交所、国内期货、A股指数 | ❌ 无需 |

---

## Symbol 格式

### 美股（yfinance）
| Symbol | 说明 |
|--------|------|
| `AAPL` | 苹果 |
| `TSLA` | 特斯拉 |
| `SPY` | 标普500 ETF |

### A股（akshare）
| Symbol | 说明 |
|--------|------|
| `sh600519` | 贵州茅台（上交所） |
| `sz000858` | 五粮液（深交所） |
| `sh510300` | 沪深300 ETF |

### 加密货币（ccxt）
| Symbol | 说明 |
|--------|------|
| `BTC-USD` | 比特币 |
| `ETH-USD` | 以太坊 |

### 指数
| Symbol | 说明 |
|--------|------|
| `GSPC` | 标普500指数（--asset index 时自动转为 ^GSPC） |
| `sh000001` | 上证指数 |
| `bj899050` | 北证50指数 |

---

## 命令详解

### `fetch` — 下载单个品种

```bash
tick fetch <SYMBOL> [选项]
```

**选项**:
| 选项 | 说明 |
|------|------|
| `-s, --start` | 开始日期 `YYYY-MM-DD` |
| `-e, --end` | 结束日期 `YYYY-MM-DD` |
| `-i, --interval` | K线周期: `1m/5m/15m/30m/60m/1d/1wk/1mo` |
| `-o, --output` | 输出文件路径 |
| `-f, --format` | 格式: `csv/json/parquet` |
| `--asset` | 资产类型: `stock/index/futures/fund/crypto` |
| `--indicator` | 技术指标: `ma/boll/rsi/macd/kdj/atr/obv/all` |
| `--exchange` | 加密货币交易所 |
| `--adjust` | A股复权: `qfq/hfq/` |
| `--show` | 打印数据摘要 |
| `--no-cache` | 禁用缓存 |

**示例**:
```bash
# 基础用法
tick fetch AAPL --show

# 指定日期
tick fetch TSLA -s 2024-01-01 -e 2024-12-31

# 添加技术指标
tick fetch AAPL --indicator rsi --indicator macd --show

# 下载所有指标
tick fetch AAPL --indicator all

# 美股指数（无需 ^ 前缀）
tick fetch GSPC --asset index -s 2024-01-01
```

### `batch` — 批量下载

```bash
tick batch <SYMBOL1> <SYMBOL2> ... [选项]
```

**选项**:
| 选项 | 说明 |
|------|------|
| `-s, --start` | 开始日期 |
| `-d, --dir` | 输出目录 |
| `-w, --workers` | 并发数 |
| `--asset` | 资产类型（可多次使用） |

**示例**:
```bash
# 统一资产类型
tick batch GSPC DJI IXIC --asset index -s 2024-01-01

# 混合资产类型
tick batch AAPL BTC-USD sh600519 --asset stock --asset crypto --asset stock

# 并发下载
tick batch AAPL TSLA NVDA GOOGL --workers 4
```

### `search` — 交互式搜索

```bash
tick search [QUERY]
```

**示例**:
```bash
# 交互式搜索
tick search

# 直接搜索
tick search 茅台
```

### `config` — 配置管理

```bash
tick config [选项]
```

**示例**:
```bash
# 初始化配置
tick config --init

# 显示配置
tick config --show
```

### `tick-web` — Web UI

```bash
tick-web
```

启动后访问 http://localhost:8501

---

## 技术指标

支持以下技术指标：

| 指标 | 说明 | 列名 |
|------|------|------|
| `ma` | 移动平均线 | ma5, ma10, ma20, ma60 |
| `boll` | 布林带 | bb_upper, bb_middle, bb_lower |
| `rsi` | RSI | rsi |
| `macd` | MACD | macd, macd_signal, macd_hist |
| `kdj` | KDJ | kdj_k, kdj_d, kdj_j |
| `atr` | 平均真实波幅 | atr |
| `obv` | 能量潮 | obv |

---

## 缓存

tick 使用 SQLite 自动缓存下载的数据，默认缓存 1 小时。

```bash
# 使用缓存（默认）
tick fetch AAPL

# 强制刷新
tick fetch AAPL --no-cache
```

---

## 测试

```bash
# 运行测试
pytest tests/ -v

# 查看覆盖率
pytest --cov=tick --cov-report=html
```

---

## 更新日志

### v0.1.0（2025-04-10）
- ✅ **模块化重构**: 全新架构，更易于扩展
- ✅ **配置系统**: YAML 配置文件支持
- ✅ **数据缓存**: SQLite 自动缓存
- ✅ **技术指标**: 支持 7 种常用指标
- ✅ **交互式搜索**: 跨数据源搜索
- ✅ **异步下载**: 并发批量获取
- ✅ **Web UI**: Streamlit 可视化界面
- ✅ **完整测试**: pytest 测试套件

---

## License

MIT

---

**GitHub**: https://github.com/gamepunk/tick
