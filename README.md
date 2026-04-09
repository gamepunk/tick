# tick

行情数据下载命令行工具，支持国内外股票、基金、期货、加密货币、**指数**。

```bash
tick fetch BTC-USD -s 2016-01-01 --exchange kraken --show
tick fetch sh600519 -s 2024-01-01
tick fetch GSPC --asset index -s 2024-01-01    # 标普500指数（自动转为 ^GSPC）
tick fetch sh000001 --asset index -s 2024-01-01 # 上证指数
tick batch AAPL TSLA GC=F -s 2024-01-01 -d ./data
tick batch-merge BTC-USD ETH-USD SOL-USD -s 2020-01-01 -o crypto.csv
```

---

## 安装

```bash
pip install click pandas rich yfinance akshare ccxt
```

克隆后直接运行：

```bash
python tick.py fetch AAPL -s 2024-01-01
```

或者安装为全局命令（配合 `pyproject.toml` / `setup.py`）：

```bash
pip install -e .
tick fetch AAPL -s 2024-01-01
```

---

## 数据源

| 数据源 | 覆盖范围 | 是否需要 Key |
|--------|---------|-------------|
| **ccxt / Binance** | 加密货币，2017 年起 | ❌ 无需 |
| **ccxt / OKX** | 加密货币，2017 年起 | ❌ 无需 |
| **ccxt / Bybit** | 加密货币，2018 年起 | ❌ 无需 |
| **ccxt / Kraken** | 加密货币，**2013 年起** | ❌ 无需 |
| **ccxt / Bitstamp** | 加密货币，**2011 年起** | ❌ 无需 |
| **yfinance** | 美股、港股、ETF、期货 | ❌ 无需 |
| **yfinance** | 国际指数（`^GSPC`, `^DJI` 等） | ❌ 无需 |
| **akshare** | A股、北交所、A股ETF、国内期货、**A股指数** | ❌ 无需 |

> 加密货币数据默认走 ccxt（Binance），可通过 `--exchange` 切换交易所。
> 需要 2017 年以前的数据请使用 `--exchange kraken` 或 `--exchange bitstamp`。

---

## Symbol 格式

### 加密货币（ccxt）

| Symbol | 说明 |
|--------|------|
| `BTC-USD` | 比特币 |
| `ETH-USD` | 以太坊 |
| `SOL-USD` | Solana |
| `BNB-USD` | 币安币 |

### 国际市场（yfinance）

| Symbol | 说明 |
|--------|------|
| `AAPL` | 苹果（美股） |
| `TSLA` | 特斯拉（美股） |
| `0700.HK` | 腾讯（港股） |
| `9988.HK` | 阿里巴巴（港股） |
| `SPY` | 标普500 ETF |
| `QQQ` | 纳斯达克100 ETF |
| `GC=F` | 黄金期货（COMEX） |
| `CL=F` | 原油期货（NYMEX） |
| `ES=F` | 标普500期货（CME） |

### 中国市场（akshare）

| Symbol | 说明 |
|--------|------|
| `sh600519` | 贵州茅台（上交所） |
| `sz000858` | 五粮液（深交所） |
| `bj835305` | 北交所股票（⭐ 新增） |
| `bj899050` | 北证50指数（⭐ 新增） |
| `sh510300` | 沪深300 ETF |
| `sz159915` | 创业板 ETF |
| `AU` | 沪金期货主力 |
| `SC` | 原油期货主力 |

### 指数（yfinance / akshare）⭐ **新增**

**美股指数（yfinance）**

使用 `--asset index` 时，美股指数**无需输入 `^` 前缀**，程序会自动转换：

| 输入代码 | 实际代码 | 名称 | 数据源 |
|----------|----------|------|--------|
| `GSPC` | `^GSPC` | 标普500指数 | yfinance |
| `DJI` | `^DJI` | 道琼斯工业指数 | yfinance |
| `IXIC` | `^IXIC` | 纳斯达克综合指数 | yfinance |
| `VIX` | `^VIX` | 波动率指数（恐慌指数） | yfinance |
| `RUT` | `^RUT` | 罗素2000 | yfinance |
| `FTSE` | `^FTSE` | 富时100（英国） | yfinance |
| `N225` | `^N225` | 日经225（日本） | yfinance |
| `HSI` | `^HSI` | 恒生指数（香港） | yfinance |

**中国指数（akshare）**

A股及北交所指数直接输入，无需转换：

| Symbol | 名称 | 交易所 |
|--------|------|--------|
| `sh000001` | 上证指数 | 上交所 |
| `sz399001` | 深证成指 | 深交所 |
| `sz399006` | 创业板指 | 深交所 |
| `sh000300` | 沪深300 | 上交所 |
| `sh000016` | 上证50 | 上交所 |
| `sh000905` | 中证500 | 上交所 |
| `sh000852` | 中证1000 | 上交所 |
| `sh000688` | 科创50 | 上交所 |
| `sz399005` | 中小板指 | 深交所 |
| `sz399415` | 深证100 | 深交所 |
| `bj899050` | 北证50 | 北交所 |

> **注意**：中国指数代码规则
> - `sh` 开头 = 上交所指数（如 `sh000001` 上证指数）
> - `sz` 开头 = 深交所指数（如 `sz399001` 深证成指）
> - `bj` 开头 + `899` = 北交所指数（如 `bj899050` 北证50）
> - 代码以 `000` / `399` / `881-889` / `930` / `899` 等开头会被自动识别为指数

---

## 命令详解

### `fetch` — 下载单个品种

下载指定品种的行情数据并保存到文件。

```bash
tick fetch <SYMBOL> [选项]
```

#### 参数选项

| 选项 | 默认值 | 说明 |
|------|--------|------|
| `-s, --start` | 1 年前 | 开始日期 `YYYY-MM-DD` |
| `-e, --end` | 今天 | 结束日期 `YYYY-MM-DD` |
| `-i, --interval` | `1d` | K线周期：`1m/5m/15m/30m/60m/1d/1wk/1mo` |
| `-o, --output` | 桌面自动命名 | 输出文件路径 |
| `-f, --format` | `csv` | 输出格式：`csv/json/parquet` |
| `--exchange` | `binance` | ccxt 交易所（仅加密货币）：`binance/okx/bybit/kraken/bitstamp` |
| `--market` | 自动识别 | 强制数据源：`yfinance/akshare_cn/akshare_futures/ccxt` |
| `--asset` | 自动识别 | 资产类型提示：`stock/index/futures/fund/crypto` |
| `--adjust` | `qfq` | 复权方式（仅A股）：`qfq/hfq/空字符串` |
| `--show` | 关闭 | 打印数据摘要 |
| `--pct/--no-pct` | 开启 | 是否添加涨跌幅列 |

#### 资产类型 `--asset` 参数说明

`--asset` 参数用于明确指定资产类型，帮助程序更准确地识别数据源：

| 类型值 | 说明 | 示例 Symbol |
|--------|------|-------------|
| `stock` | 股票（A股/港股/美股） | `AAPL`, `sh600519`, `0700.HK` |
| `index` | 指数 | `GSPC`, `sh000001`, `DJI` |
| `futures` | 期货 | `GC=F`, `CL=F`, `AU` |
| `fund` | 基金/ETF | `SPY`, `sh510300`, `QQQ` |
| `crypto` | 加密货币 | `BTC-USD`, `ETH-USD` |

**美股指数的简化输入** ⭐

当使用 `--asset index` 时，美股指数**无需输入 `^` 前缀**，程序会自动转换：

```bash
# ✅ 简化写法（推荐）
tick fetch GSPC --asset index -s 2024-01-01    # 自动转为 ^GSPC
tick fetch DJI --asset index -s 2024-01-01     # 自动转为 ^DJI
tick fetch IXIC --asset index -s 2024-01-01    # 自动转为 ^IXIC

# 传统写法（仍然支持）
tick fetch ^GSPC --asset index -s 2024-01-01
```

> **注意**：A股指数（`sh000001`, `sz399006` 等）无需转换，直接输入即可。

#### 使用示例

**基础用法**

```bash
# 美股，默认 1 年
tick fetch AAPL --show

# 指定日期范围
tick fetch TSLA -s 2024-01-01 -e 2024-12-31

# 保存为不同格式
tick fetch MSFT -s 2024-01-01 -f json
tick fetch GOOGL -s 2024-01-01 -f parquet -o ./data/googl.parquet
```

**加密货币**

```bash
# 默认从 Binance 拉取（2017 年起）
tick fetch BTC-USD -s 2018-01-01 --show

# 需要 2017 年以前的数据 → 使用 Kraken（2013 年起）
tick fetch BTC-USD -s 2016-01-01 --exchange kraken --show

# 最早历史数据 → 使用 Bitstamp（2011 年起）
tick fetch BTC-USD -s 2013-01-01 --exchange bitstamp

# 其他加密货币
tick fetch ETH-USD -s 2020-01-01 --exchange kraken
tick fetch SOL-USD -s 2022-01-01
```

**A股**

```bash
# A股日线，前复权
tick fetch sh600519 -s 2020-01-01 --show

# A股不复权
tick fetch sz000858 -s 2024-01-01 --adjust ""

# A股后复权
tick fetch sh601318 -s 2024-01-01 --adjust hfq

# A股 5 分钟分时（仅限最近1年左右）
tick fetch sh600519 -s 2026-03-28 -e 2026-03-28 -i 5m
```

**期货**

```bash
# 国际期货
tick fetch GC=F -s 2024-01-01 --show
tick fetch CL=F -s 2024-01-01
tick fetch ES=F -s 2024-01-01

# 国内期货
tick fetch AU --market akshare_futures -s 2025-01-01
tick fetch AG --market akshare_futures -s 2025-01-01
tick fetch SC --market akshare_futures -s 2025-01-01
```

**指数（⭐ 新增功能，支持 `--asset` 简化输入）**

```bash
# ========== 美股指数（无需 ^ 前缀，使用 --asset index）==========

# 标普500指数 - 只需输入 GSPC，自动转为 ^GSPC
tick fetch GSPC --asset index -s 2024-01-01 --show

# 道琼斯工业指数
tick fetch DJI --asset index -s 2024-01-01 -e 2024-12-31

# 纳斯达克综合指数
tick fetch IXIC --asset index -s 2024-01-01 --show

# 波动率指数（VIX）
tick fetch VIX --asset index -s 2024-01-01

# 罗素2000
tick fetch RUT --asset index -s 2024-01-01

# 恒生指数（港股）
tick fetch HSI --asset index -s 2024-01-01

# ========== A股指数（直接输入，无需转换）==========

# 上证指数
tick fetch sh000001 --asset index -s 2024-01-01 --show

# 深证成指
tick fetch sz399001 --asset index -s 2024-01-01

# 创业板指
tick fetch sz399006 --asset index -s 2024-01-01 --show

# 沪深300
tick fetch sh000300 --asset index -s 2024-01-01

# 上证50
tick fetch sh000016 --asset index -s 2024-01-01

# 中证500
tick fetch sh000905 --asset index -s 2024-01-01

# 中证1000
tick fetch sh000852 --asset index -s 2024-01-01

# 科创50
tick fetch sh000688 --asset index -s 2024-01-01

# ========== 指数分时数据 ==========

# 上证指数 5 分钟线（当日）
tick fetch sh000001 --asset index -s 2026-03-28 -e 2026-03-28 -i 5m

# 创业板指 15 分钟线
tick fetch sz399006 --asset index -s 2026-03-28 -e 2026-03-28 -i 15m

# 沪深300 60 分钟线
tick fetch sh000300 --asset index -s 2026-03-28 -e 2026-03-28 -i 60m

# ========== 北交所（⭐ 新增） ==========

# 北交所股票
tick fetch bj835305 -s 2024-01-01

# 北证50指数
tick fetch bj899050 --asset index -s 2024-01-01

# 北证50指数 5 分钟线
tick fetch bj899050 --asset index -s 2026-03-28 -e 2026-03-28 -i 5m
```

---

### `batch` — 批量下载多个品种

同时下载多个品种，各自保存为独立文件。

```bash
tick batch <SYMBOL1> <SYMBOL2> ... [选项]
```

#### 参数选项

| 选项 | 默认值 | 说明 |
|------|--------|------|
| `-s, --start` | 1 年前 | 开始日期 `YYYY-MM-DD` |
| `-e, --end` | 今天 | 结束日期 `YYYY-MM-DD` |
| `-d, --dir` | 桌面 | 输出目录 |
| `-i, --interval` | `1d` | K线周期 |
| `-f, --format` | `csv` | 输出格式 |
| `--adjust` | `qfq` | 复权方式（仅A股） |
| `--asset` | 自动识别 | 资产类型（可多次使用，详见下方） |
| `--exchange` | `binance` | ccxt 交易所（仅加密货币） |
| `--pct/--no-pct` | 开启 | 是否添加涨跌幅列 |

#### `--asset` 批量指定规则

`--asset` 参数支持灵活批量指定：

- **统一应用**：提供 1 个 asset，所有品种统一使用该类型
  ```bash
  # 美股指数自动加 ^ 前缀
  tick batch GSPC DJI IXIC --asset index -s 2024-01-01
  
  # A股指数直接输入
  tick batch sh000001 sz399001 sz399006 --asset index -s 2024-01-01
  ```

- **一一对应**：提供多个 asset，数量与 symbol 数量一致
  ```bash
  tick batch AAPL BTC-USD sh600519 --asset stock --asset crypto --asset stock -s 2024-01-01
  
  # 混合类型（美股指数自动加 ^）
  tick batch AAPL BTC-USD GSPC --asset stock --asset crypto --asset index -s 2024-01-01
  ```

#### 使用示例

```bash
# 混合资产批量下载
tick batch AAPL TSLA BTC-USD GC=F -s 2024-01-01 -d ./data

# 加密货币批量，使用 Kraken 历史数据
tick batch BTC-USD ETH-USD SOL-USD -s 2016-01-01 --exchange kraken -d ./crypto

# A股批量下载
tick batch sh600519 sz000858 sz002594 -s 2024-01-01 -d ./a_shares

# A股分时数据批量
tick batch sh600519 sz000858 sz002594 -s 2026-03-28 -e 2026-03-28 -i 5m -d ./intraday

# ========== 指数批量下载（⭐ 新增） ==========

# 美股三大指数批量下载（无需 ^ 前缀）
tick batch GSPC DJI IXIC --asset index -s 2024-01-01 -d ./us_indices

# A股主要指数批量下载
tick batch sh000001 sz399001 sz399006 -s 2024-01-01 -d ./cn_indices

# 宽基指数批量
tick batch sh000300 sh000016 sh000905 sh000852 -s 2024-01-01 -d ./indices

# 中美指数对比批量下载
tick batch GSPC DJI sh000001 sz399001 --asset index -s 2024-01-01 -d ./global_indices

# ========== 使用 --asset 参数指定资产类型（⭐ 新增） ==========

# 统一指定所有品种为指数类型（美股指数自动加 ^）
tick batch GSPC DJI sh000001 --asset index -s 2024-01-01 -d ./indices

# 一一对应指定不同类型
tick batch AAPL BTC-USD sh600519 --asset stock --asset crypto --asset stock -s 2024-01-01

# 混合类型：美股指数自动加 ^，其他不变
tick batch AAPL BTC-USD GSPC --asset stock --asset crypto --asset index -s 2024-01-01
```

---

### `batch-merge` — 批量下载并合并为长格式

将多个品种合并为一个 CSV 文件，适合 [Observable Bar Chart Race](https://observablehq.com/@d3/bar-chart-race) 等可视化场景。

```bash
tick batch-merge <SYMBOL1> <SYMBOL2> ... [选项]
```

#### 输出格式

每行包含一个品种在一个时间点的数据：

```csv
date,name,display_name,category,open,high,low,close,volume,cum_pct,pct_change
2024-01-02,AAPL,Apple Inc.,股票,185.2,186.9,183.4,185.6,82000000,0.0,0.0
2024-01-02,BTC-USD,Bitcoin,加密货币,42800,43500,42100,43200,18000000000,0.0,0.0
2024-01-02,sh000001,上证指数,指数,2970.5,2980.2,2960.1,2975.3,150000000,0.0,0.0
```

#### 参数选项

| 选项 | 默认值 | 说明 |
|------|--------|------|
| `-s, --start` | 1 年前 | 开始日期 `YYYY-MM-DD` |
| `-e, --end` | 今天 | 结束日期 `YYYY-MM-DD` |
| `-o, --output` | 桌面自动命名 | 输出文件路径 |
| `-f, --format` | `csv` | 输出格式：`csv/json/parquet` |
| `-i, --interval` | `1d` | K线周期 |
| `--value-col` | `close` | Bar Chart Race 排序依据列：`close/open/high/low/volume` |
| `--category-map` | 自动识别 | 强制指定类别，格式：`SYMBOL:TYPE,SYMBOL2:TYPE` |
| `--adjust` | `qfq` | 复权方式（仅A股） |
| `--asset` | 自动识别 | 资产类型（可多次使用，与 batch 命令相同规则） |
| `--exchange` | `binance` | ccxt 交易所（仅加密货币） |

> **💡 提示**：`--asset` 参数比 `--category-map` 更简洁，推荐优先使用。例如：
> ```bash
> tick batch-merge GSPC DJI sh000001 --asset index -s 2024-01-01
> ```

#### 使用示例

```bash
# 混合资产对比
tick batch-merge AAPL BTC-USD GC=F sh510300 -s 2024-01-01

# 加密货币赛道，带早期历史
tick batch-merge BTC-USD ETH-USD SOL-USD -s 2016-01-01 --exchange kraken -o crypto_race.csv

# A股今日 5 分钟分时合并
tick batch-merge sh600519 sz000858 sz002594 -s 2026-03-28 -e 2026-03-28 -i 5m -o intraday.csv

# 按成交量排序
tick batch-merge AAPL TSLA NVDA -s 2024-01-01 --value-col volume

# ========== 指数合并示例（⭐ 新增） ==========

# 美股三大指数对比（无需 ^ 前缀）
tick batch-merge GSPC DJI IXIC --asset index -s 2024-01-01 -o us_indices_race.csv

# A股主要指数对比
tick batch-merge sh000001 sz399001 sz399006 sh000300 -s 2024-01-01 -o cn_indices_race.csv

# 中美指数对比（适合制作对比可视化）
tick batch-merge GSPC DJI sh000001 sz399006 --asset index -s 2024-01-01 -o global_comparison.csv

# 宽基指数对比
tick batch-merge sh000300 sh000016 sh000905 sh000852 -s 2024-01-01 -o china_broad_indices.csv

# 强制指定类别（指数 vs 股票对比，使用 --asset 更简洁）
tick batch-merge GSPC sh000001 AAPL sh600519 --asset index --asset index --asset stock --asset stock -s 2024-01-01

# ========== 使用 --asset 参数指定资产类型（⭐ 新增，推荐） ==========

# 统一指定所有品种为指数类型（美股指数自动加 ^）
tick batch-merge GSPC DJI sh000001 --asset index -s 2024-01-01 -o indices_race.csv

# 混合资产类型，一一对应（美股指数自动加 ^）
tick batch-merge AAPL BTC-USD GSPC --asset stock --asset crypto --asset index -s 2024-01-01
```

---

### `info` — 查看品种基本信息

查看股票、ETF、期货、指数的基本信息（仅支持 yfinance 数据源）。

```bash
tick info <SYMBOL>
```

#### 使用示例

```bash
# 美股基本信息
tick info AAPL
tick info TSLA
tick info SPY

# 期货基本信息
tick info GC=F
tick info CL=F

# 港股基本信息
tick info 0700.HK
tick info 9988.HK

# 指数基本信息（部分信息可能有限，使用完整代码）
tick info ^GSPC
tick info ^VIX

# 或使用 fetch 配合 --show 查看指数数据摘要
tick fetch GSPC --asset index -s 2024-01-01 --show
```

---

### `symbols` — 查看常用品种列表

显示内置的常用品种参考表。

```bash
tick symbols                    # 显示全部
tick symbols --type stock       # 仅股票
tick symbols --type fund        # 仅基金/ETF
tick symbols --type futures     # 仅期货
tick symbols --type crypto      # 仅加密货币
tick symbols --type index       # 仅指数（⭐ 新增）
```

#### 使用示例

```bash
# 查看所有支持的指数
tick symbols --type index

# 输出示例：
# ┏━━━━━━━━━━┳━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━┳━━━━━━━┓
# ┃ Symbol   ┃ 名称         ┃ 数据源          ┃ 市场  ┃
# ┡━━━━━━━━━━╇━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━╇━━━━━━━┩
# │ ^GSPC    │ 标普500指数  │ yfinance        │ 美股  │
# │ ^DJI     │ 道琼斯指数   │ yfinance        │ 美股  │
# │ ^IXIC    │ 纳斯达克指数 │ yfinance        │ 美股  │
# │ ^VIX     │ 波动率指数   │ yfinance        │ 美股  │
# │ sh000001 │ 上证指数     │ akshare         │ A股   │
# │ sz399006 │ 创业板指     │ akshare         │ A股   │
# │ ...      │ ...          │ ...             │ ...   │
# └──────────┴──────────────┴─────────────────┴───────┘
```

---

### `help-symbols` — 查看 Symbol 格式说明

显示详细的 Symbol 格式帮助文档。

```bash
tick help-symbols
```

---

## K线周期说明

| 周期 | 说明 | 限制 |
|------|------|------|
| `1m/5m/15m/30m/60m` | 分时数据 | yfinance 最多回溯 7~60 天；国内期货不支持；A股指数分时仅限近期数据 |
| `1d` | 日线 | 所有数据源均支持，历史数据最完整 |
| `1wk` | 周线 | 所有数据源均支持 |
| `1mo` | 月线 | 所有数据源均支持 |

### 分时数据限制说明

| 数据源 | 分时数据限制 |
|--------|-------------|
| yfinance | 1m 数据最多 7 天，60m 数据最多 730 天 |
| akshare (A股) | 通常支持最近 1 年的分时数据 |
| akshare (指数) | 1m 数据只能返回当天，其他周期返回近期数据 |
| ccxt | 无明确限制，取决于交易所 API |

---

## 输出文件命名规则

自动命名格式：

```
{symbol}_{start}_{end}_{interval}_{数据源}.{格式}

# 示例
AAPL_20240101_20250101_1d_yf.csv                    # 美股
tick_merge_20240101_20250101_1d_mixed_raw.csv       # batch-merge 合并数据
BTC-USD_20160101_20250101_1d_ccxt_kraken.csv          # 加密货币（Kraken）
sh600519_20240101_20250101_1d_ak_qfq.csv              # A股（前复权）
^GSPC_20240101_20250101_1d_yf_idx.csv                 # 美股指数（使用 --asset index 时）
sh000001_20240101_20250101_1d_ak_idx.csv              # A股指数（使用 --asset index 时）
```

---

## 实战示例

### 示例 1：制作美股与A股指数对比图

```bash
# 下载中美主要指数 2024 年数据（美股指数无需 ^ 前缀）
tick batch-merge GSPC DJI IXIC sh000001 sz399001 --asset index -s 2024-01-01 -e 2024-12-31 -o us_cn_indices_2024.csv

# 数据将包含以下列：
# date, name, display_name, category, open, high, low, close, volume, cum_pct, pct_change
# 可直接用于 Observable Bar Chart Race 制作动态排名可视化
```

### 示例 2：追踪加密货币与美股相关性

```bash
# 下载比特币、以太坊与标普500、纳指同期数据
tick batch-merge BTC-USD ETH-USD GSPC IXIC --asset crypto --asset crypto --asset index --asset index -s 2023-01-01 --exchange kraken -o crypto_vs_stocks.csv

# 分析加密货币与美股指数的相关性走势
```

### 示例 3：A股宽基指数轮动分析

```bash
# 下载主要宽基指数数据
tick batch sh000300 sh000016 sh000905 sh000852 sz399006 --asset index -s 2023-01-01 -d ./china_indices

# 或者合并为一个文件便于对比
tick batch-merge sh000300 sh000016 sh000905 sh000852 sz399006 --asset index -s 2023-01-01 -o china_broad_indices.csv

# 分析各指数的相对强弱和轮动效应
```

### 示例 4：恐慌指数（VIX）与标普500对比

```bash
# 下载 VIX 和标普500 数据（无需 ^ 前缀）
tick batch VIX GSPC --asset index -s 2024-01-01 -d ./vix_analysis

# 合并分析
tick batch-merge VIX GSPC --asset index -s 2024-01-01 -o vix_vs_sp500.csv

# 可用于分析市场恐慌情绪与大盘走势的负相关性
```

### 示例 5：日内交易分析（指数分时数据）

```bash
# 获取当日上证指数和创业板指 5 分钟线
tick batch sh000001 sz399006 -s 2026-03-28 -e 2026-03-28 -i 5m -d ./intraday

# 合并分析
tick batch-merge sh000001 sz399006 -s 2026-03-28 -e 2026-03-28 -i 5m -o intraday_indices.csv

# 可用于日内趋势分析和量化策略回测
```

---

## 常见问题

**Q: yfinance 提示 Too Many Requests？**

yfinance 会自动重试 3 次（间隔 10/20/30 秒）。加密货币建议直接用 `--market ccxt`，完全没有限流问题。

**Q: 拉不到 2017 年以前的加密货币数据？**

Binance/OKX 均在 2017 年上线。需要更早数据请使用：
```bash
tick fetch BTC-USD -s 2016-01-01 --exchange kraken    # 2013 年起
tick fetch BTC-USD -s 2013-01-01 --exchange bitstamp  # 2011 年起
```

**Q: Kraken 的 BTC 价格和 Binance 对得上吗？**

Kraken 币对是 `XBT/USD`（真实美元），Binance 是 `BTC/USDT`（稳定币），价格接近但不完全相同，正常现象。

**Q: A股分时数据支持多久回溯？**

akshare 的 `stock_zh_a_hist_min_em` 接口通常支持最近 1 年的分时数据，具体取决于接口限制。

**Q: 指数数据为什么显示不全或报错？**

- **美股指数（yfinance）**：部分指数如 `^GSPC` 可能在某些时间段数据受限，可尝试缩短日期范围
- **A股指数（akshare）**：确保使用正确的代码格式（`sh000001` 而非 `000001`）
- **指数分时数据**：1分钟数据通常只能获取当天，其他周期可获取近期数据

**Q: 如何区分股票和指数？**

系统会自动识别：
- `^` 开头 → 国际指数（yfinance）
- `sh`/`sz` + `000`/`399`/`881-889` 开头 → A股指数（akshare）
- 其他 `sh`/`sz` 开头 → A股股票

推荐使用 `--asset` 参数明确指定：
```bash
# 美股指数（自动添加 ^ 前缀）
tick fetch GSPC --asset index -s 2024-01-01

# A股指数
tick fetch sh000001 --asset index -s 2024-01-01

# 混合批量下载
tick batch AAPL GSPC sh600519 --asset stock --asset index --asset stock -s 2024-01-01
```

**Q: batch-merge 中指数和股票混在一起如何区分？**

系统会自动将指数归类为 `index` 类别，在输出文件的 `category` 列中体现：
```csv
date,name,display_name,category,close,...
2024-01-02,^GSPC,S&P 500,index,4783.45,...
2024-01-02,AAPL,Apple Inc.,股票,185.92,...
2024-01-02,sh000001,上证指数,index,2970.53,...
```

推荐使用 `--asset` 参数（更简洁）：
```bash
tick batch-merge GSPC AAPL sh000001 --asset index --asset stock --asset index -s 2024-01-01
```

或使用 `--category-map` 强制指定：
```bash
tick batch-merge GSPC AAPL sh000001 --category-map GSPC:index,AAPL:stock,sh000001:index -s 2024-01-01
```

---

## 依赖

```
click
pandas
rich
yfinance      # 美股、港股、ETF、期货、国际指数
akshare       # A股、国内期货、A股指数
ccxt          # 加密货币（多交易所）
```

---

## 更新日志

### v0.3.0（2026-04-09）
- ✅ **新增 `--asset` 参数**：支持 `fetch`/`batch`/`batch-merge` 命令，明确指定资产类型
- ✅ **美股指数简化输入**：使用 `--asset index` 时，美股指数无需输入 `^` 前缀（如 `GSPC` 自动转为 `^GSPC`）
- ✅ **批量资产指定**：支持统一指定（1个类型应用于所有品种）或一一对应（多个类型按顺序匹配）
- ✅ **新增北交所支持**：支持北交所股票（`bj` 前缀）和北证50指数（`bj899050`）

### v0.2.0（2026-04-08）
- ✅ **新增指数支持**：美股指数（`^GSPC`, `^DJI`, `^IXIC`, `^VIX` 等）和 A股指数（`sh000001`, `sz399006`, `sh000300` 等）
- ✅ **指数分时数据**：支持 A股指数 5m/15m/30m/60m 分时数据
- ✅ **自动识别**：自动区分股票代码和指数代码
- ✅ **batch-merge 支持指数**：可在同一文件中混合股票、加密货币、期货和指数数据

