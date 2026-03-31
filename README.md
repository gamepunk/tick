# tick

行情数据下载 CLI 工具，支持国内外股票、基金、期货、加密货币。

数据源：[yfinance](https://github.com/ranaroussi/yfinance)（国际市场）· [akshare](https://github.com/akfamily/akshare)（中国市场）

---

## 安装

```bash
pip install tick
pip install yfinance akshare pandas rich click
```

---

## 命令概览

| 命令 | 说明 |
|------|------|
| `tick fetch <SYMBOL>` | 下载单品种行情数据 |
| `tick batch <SYMBOL...>` | 批量下载多品种，每个品种单独存为一个文件 |
| `tick batch-merge <SYMBOL...>` | 批量下载并合并为长格式，适合 Bar Chart Race |
| `tick info <SYMBOL>` | 查看品种基本信息（仅 yfinance） |
| `tick symbols` | 显示常用品种参考表 |
| `tick help-symbols` | 显示 Symbol 格式说明 |
| `tick market-cap` | 获取 A股市值排名（支持从低到高排序） |

---

## K 线周期说明

三个下载命令均支持以下周期，通过 `-i, --interval` 指定：

| 周期 | 说明 | 回溯限制 |
|------|------|----------|
| `1m` | 1 分钟 | yfinance 最近 7 天；akshare A 股近几个月 |
| `5m` | 5 分钟 | yfinance 最近 60 天；akshare A 股近几个月 |
| `15m` | 15 分钟 | yfinance 最近 60 天；akshare A 股近几个月 |
| `30m` | 30 分钟 | yfinance 最近 60 天；akshare A 股近几个月 |
| `60m` | 60 分钟 | yfinance 最近 730 天；akshare A 股近几个月 |
| `1d` | 日线（默认） | 无限制 |
| `1wk` | 周线 | 无限制 |
| `1mo` | 月线 | 无限制 |

> 国内期货（akshare_futures）暂不支持分时数据，仅支持 `1d` 及以上。  
> A 股分时数据（1m/5m/15m/30m/60m）通过 akshare 支持，日期格式为 `YYYY-MM-DD HH:MM:SS`。

---

## fetch — 下载单品种

```bash
tick fetch <SYMBOL> [选项]
```

| 选项 | 默认 | 说明 |
|------|------|------|
| `-s, --start` | 1 年前 | 开始日期 `YYYY-MM-DD` |
| `-e, --end` | 今天 | 结束日期 `YYYY-MM-DD` |
| `-i, --interval` | `1d` | K 线周期（见上方说明） |
| `-o, --output` | 自动命名到桌面 | 输出文件路径 |
| `-f, --format` | `csv` | 输出格式 `csv` / `json` / `parquet` |
| `--adjust` | `qfq` | 复权方式，仅 A 股有效（见下方说明） |
| `--market` | 自动识别 | 强制指定数据源 `yfinance` / `akshare_cn` / `akshare_futures` |
| `--show` | — | 下载完成后打印数据摘要 |
| `--pct / --no-pct` | 开启 | 是否添加涨跌幅列 |

### 加密货币

```bash
# 比特币日线，2025 年至今，打印摘要
tick fetch BTC-USD -s 2025-01-01 --show

# 以太坊，指定起止日期
tick fetch ETH-USD -s 2024-01-01 -e 2024-12-31

# Solana，保存为 JSON
tick fetch SOL-USD -s 2025-01-01 -f json

# 比特币周线
tick fetch BTC-USD -s 2023-01-01 -i 1wk

# 以太坊月线，查看多年走势
tick fetch ETH-USD -s 2020-01-01 -i 1mo --show

# 比特币今日 5 分钟分时（yfinance 支持最近 60 天）
tick fetch BTC-USD -s 2026-03-28 -e 2026-03-28 -i 5m --show
```

### 美股

```bash
# 苹果日线
tick fetch AAPL -s 2024-01-01

# 英伟达，指定输出路径
tick fetch NVDA -s 2024-01-01 -o ./data/nvda_2024.csv

# 谷歌，周线，打印摘要
tick fetch GOOGL -s 2023-01-01 -i 1wk --show

# 微软，月线，从 2020 年起，保存为 parquet
tick fetch MSFT -s 2020-01-01 -i 1mo -f parquet

# 特斯拉，不添加涨跌幅列
tick fetch TSLA -s 2024-01-01 --no-pct

# 苹果今日 1 分钟分时（yfinance 支持最近 7 天）
tick fetch AAPL -s 2026-03-28 -e 2026-03-28 -i 1m
```

### 港股

```bash
# 腾讯
tick fetch 700.HK -s 2024-01-01

# 阿里巴巴，保存为 JSON
tick fetch 9988.HK -s 2024-01-01 -f json

# 美团，打印摘要
tick fetch 3690.HK -s 2024-01-01 --show

# 小米，周线
tick fetch 1810.HK -s 2023-01-01 -i 1wk

# 腾讯今日 5 分钟分时
tick fetch 700.HK -s 2026-03-28 -e 2026-03-28 -i 5m
```

### A 股

```bash
# 贵州茅台，前复权（默认）
tick fetch sh600519 -s 2024-01-01

# 贵州茅台，后复权（适合量化回测）
tick fetch sh600519 -s 2024-01-01 --adjust hfq

# 贵州茅台，不复权（原始价格）
tick fetch sh600519 -s 2024-01-01 --adjust ""

# 五粮液，前复权，打印摘要
tick fetch sz000858 -s 2024-01-01 --show

# 比亚迪，3 年日线，保存为 parquet
tick fetch sz002594 -s 2022-01-01 -f parquet

# 宁德时代，周线
tick fetch sz300750 -s 2022-01-01 -i 1wk --show

# 茅台今日 5 分钟分时（akshare 支持近几个月）
tick fetch sh600519 -s 2026-03-28 -e 2026-03-28 -i 5m --show

# 比亚迪今日 1 分钟分时
tick fetch sz002594 -s 2026-03-28 -e 2026-03-28 -i 1m
```

### A 股 ETF

```bash
# 沪深 300 ETF
tick fetch sh510300 -s 2024-01-01

# 创业板 ETF
tick fetch sz159915 -s 2024-01-01

# 中概互联 ETF，后复权
tick fetch sh513050 -s 2023-01-01 --adjust hfq

# 科创 50 ETF，打印摘要
tick fetch sh588000 -s 2024-01-01 --show

# 黄金 ETF（A 股）
tick fetch sh518880 -s 2024-01-01 --show
```

### 国际期货

```bash
# 黄金期货（COMEX），打印摘要
tick fetch GC=F -s 2025-01-01 --show

# 原油期货（WTI）
tick fetch CL=F -s 2025-01-01

# 标普 500 期货
tick fetch ES=F -s 2025-01-01

# 纳斯达克 100 期货
tick fetch NQ=F -s 2025-01-01 --show

# 白银期货
tick fetch SI=F -s 2024-01-01

# 铜期货，保存为 parquet
tick fetch HG=F -s 2024-01-01 -f parquet

# 黄金期货今日 15 分钟分时
tick fetch GC=F -s 2026-03-28 -e 2026-03-28 -i 15m
```

### 国内期货

```bash
# 沪金期货主力
tick fetch AU --market akshare_futures -s 2025-01-01

# 沪银期货主力
tick fetch AG --market akshare_futures -s 2025-01-01

# 原油期货主力（INE）
tick fetch SC --market akshare_futures -s 2025-01-01

# 螺纹钢期货主力，打印摘要
tick fetch RB --market akshare_futures -s 2025-01-01 --show

# 铜期货主力
tick fetch CU --market akshare_futures -s 2024-01-01
```

---

## batch — 批量下载

```bash
tick batch <SYMBOL...> [选项]
```

选项与 `fetch` 基本一致，额外增加 `-d, --dir`（输出目录，默认桌面）。每个品种单独存为一个文件。

### 日线批量

```bash
# 主流加密货币
tick batch BTC-USD ETH-USD SOL-USD BNB-USD XRP-USD -s 2025-01-01 -d ./crypto

# 美股七巨头
tick batch AAPL MSFT NVDA GOOGL AMZN META TSLA -s 2024-01-01 -d ./magnificent7

# A 股白酒板块
tick batch sh600519 sz000858 sz000596 sh600779 sz002304 -s 2024-01-01 -d ./baijiu

# A 股新能源车
tick batch sz002594 sz300750 sh601127 sh600104 sz000625 -s 2023-01-01 -d ./nev

# 国际期货组合
tick batch GC=F CL=F SI=F NQ=F ES=F HG=F -s 2024-01-01 -d ./futures
```

### 分时批量

```bash
# A 股今日 5 分钟分时，白酒板块
tick batch sh600519 sz000858 sz000596 sh600779 sz002304 \
  -s 2026-03-28 -e 2026-03-28 -i 5m -d ./intraday

# A 股今日 1 分钟分时，新能源车
tick batch sz002594 sz300750 sh601127 sh600104 sz000625 \
  -s 2026-03-28 -e 2026-03-28 -i 1m -d ./intraday

# 美股今日 1 分钟分时（仅支持最近 7 天）
tick batch AAPL TSLA NVDA GOOGL MSFT \
  -s 2026-03-28 -e 2026-03-28 -i 1m -d ./us_intraday

# 加密货币近 7 天 5 分钟分时
tick batch BTC-USD ETH-USD SOL-USD \
  -s 2026-03-24 -e 2026-03-28 -i 5m -d ./crypto_intraday
```

### 跨市场组合

```bash
# A 股 + 美股 + 加密货币混合
tick batch sh600519 sh601318 AAPL TSLA BTC-USD ETH-USD -s 2024-01-01 -d ./mixed

# 全球黄金相关资产对比
tick batch GLD GC=F sh518880 sh600547 -s 2024-01-01 -d ./gold

# 中美科技股对比
tick batch AAPL MSFT NVDA sh600519 sz300750 sz002594 -s 2023-01-01 -d ./tech
```

### 指定格式

```bash
# 全部保存为 JSON
tick batch AAPL BTC-USD GC=F -s 2025-01-01 -f json -d ./data

# 全部保存为 parquet（适合 pandas 大批量处理）
tick batch AAPL TSLA NVDA GOOGL MSFT -s 2020-01-01 -f parquet -d ./data

# A 股后复权，适合量化回测
tick batch sh600519 sz000858 sz002594 sz300750 -s 2020-01-01 --adjust hfq -d ./backtest
```

---

## batch-merge — 合并为长格式

批量下载多品种，输出为适合 [Observable Bar Chart Race](https://observablehq.com/@d3/bar-chart-race) 的长格式文件。自动批量获取品种名称（A 股一次性拉取全量名称表，无需逐个请求）。

```bash
tick batch-merge <SYMBOL...> [选项]
```

| 选项 | 默认 | 说明 |
|------|------|------|
| `-s, --start` | 1 年前 | 开始日期 `YYYY-MM-DD` |
| `-e, --end` | 今天 | 结束日期 `YYYY-MM-DD` |
| `-i, --interval` | `1d` | K 线周期（见上方说明） |
| `-o, --output` | 自动命名到桌面 | 输出文件路径 |
| `-f, --format` | `csv` | 输出格式 `csv` / `json` / `parquet` |
| `--value-col` | `close` | Bar Chart Race 排序依据列 `close` / `open` / `high` / `low` / `volume` |
| `--adjust` | `qfq` | 复权方式（仅 A 股有效） |
| `--category-map` | 自动识别 | 强制指定类别，格式：`SYMBOL:TYPE,...` |

品种类别自动识别为：股票 / 基金ETF / 期货 / 加密货币。

### 输出格式

日线模式下，每行对应一个品种在某一天的完整数据；分时模式下，`date` 列保留完整时间戳。

```
date,name,display_name,category,open,high,low,close,volume,cum_pct,pct_change

# 日线（date 格式：YYYY-MM-DD）
2024-01-02,sz002594,比亚迪,股票,236.50,241.80,234.20,239.60,1823400,0.0,0.0
2024-01-02,BTC-USD,Bitcoin,加密货币,42580.10,43210.50,42100.30,43105.20,28450000000,0.0,0.0

# 分时（date 格式：YYYY-MM-DD HH:MM:SS）
2026-03-28 09:35:00,sz002594,比亚迪,股票,238.20,239.50,237.80,238.90,324100,0.0,0.0
2026-03-28 09:40:00,sz002594,比亚迪,股票,238.90,240.10,238.50,239.60,218400,0.29,0.29
```

| 列名 | 说明 |
|------|------|
| `date` | 日期（日线：`YYYY-MM-DD`；分时：`YYYY-MM-DD HH:MM:SS`） |
| `name` | 原始 Symbol 代码（如 `sz002594`） |
| `display_name` | 品种名称（如 `比亚迪`、`Apple Inc.`） |
| `category` | 资产类别（股票 / 基金ETF / 期货 / 加密货币） |
| `open` / `high` / `low` / `close` | 开高低收价格 |
| `volume` | 成交量 |
| `cum_pct` | 相对区间首日（首根 K 线）累计涨跌幅（%） |
| `pct_change` | 逐根 K 线涨跌幅（%） |

### 日线示例

```bash
# 混合资产对比，自动识别类别
tick batch-merge AAPL BTC-USD GC=F sh510300 -s 2024-01-01

# 主流加密货币赛道对比
tick batch-merge BTC-USD ETH-USD SOL-USD BNB-USD XRP-USD -s 2024-01-01 -o crypto_race.csv

# A 股新能源车板块（20 只）
tick batch-merge \
  sz002594 sz300750 sh601127 sh600104 sz000625 \
  sh600418 sh601633 sz002920 sh600006 sh601238 \
  sz000550 sh600715 sz002056 sh600609 sz000800 \
  sz002190 sh601689 sz002925 sh600761 sz300014 \
  -s 2024-01-01 -o auto_race.csv

# 全球主要股指 ETF 对比
tick batch-merge SPY QQQ GLD TLT IWM EEM VTI -s 2023-01-01 -o etf_race.csv

# A 股白酒板块，按成交量排序
tick batch-merge sh600519 sz000858 sz000596 sh600779 sz002304 \
  -s 2024-01-01 --value-col volume -o baijiu_volume.csv

# 中美科技龙头对比，保存为 parquet
tick batch-merge AAPL MSFT NVDA GOOGL sz300750 sz002594 sh600519 \
  -s 2023-01-01 -f parquet -o tech_compare.parquet

# 全球黄金资产横向对比
tick batch-merge GC=F GLD sh518880 sh600547 \
  -s 2024-01-01 --category-map "sh600547:stock" -o gold_race.csv
```

### 分时示例

```bash
# A 股汽车板块今日 5 分钟分时，合并为单个 CSV
tick batch-merge \
  sz002594 sz300750 sh601127 sh600104 sz000625 \
  sh600418 sh601633 sz002920 sh600006 sh601238 \
  sz000550 sh600715 sz002056 sh600609 sz000800 \
  sz002190 sh601689 sz002925 sh600761 sz300014 \
  -s 2026-03-28 -e 2026-03-28 -i 5m -o auto_intraday.csv

# A 股白酒板块今日 1 分钟分时
tick batch-merge sh600519 sz000858 sz000596 sh600779 sz002304 \
  -s 2026-03-28 -e 2026-03-28 -i 1m -o baijiu_intraday.csv

# 美股科技股今日 5 分钟分时（yfinance，最近 60 天内有效）
tick batch-merge AAPL MSFT NVDA GOOGL TSLA \
  -s 2026-03-28 -e 2026-03-28 -i 5m -o us_intraday.csv

# 加密货币近 7 天 5 分钟分时
tick batch-merge BTC-USD ETH-USD SOL-USD BNB-USD \
  -s 2026-03-24 -e 2026-03-28 -i 5m -o crypto_intraday.csv

# 混合资产今日 15 分钟分时
tick batch-merge AAPL BTC-USD sz002594 sz300750 \
  -s 2026-03-28 -e 2026-03-28 -i 15m -o mixed_intraday.csv
```

### 自动命名规则

不指定 `-o` 时，文件名格式为：

```
tick_merge_{start}_{end}_{interval}_merge_{adjust}.{fmt}
```

示例：

```
tick_merge_20240101_20250329_1d_merge_qfq.csv
tick_merge_20260328_20260328_5m_merge_qfq.csv
tick_merge_20260328_20260328_1m_merge_qfq.csv
tick_merge_20240101_20250329_1d_merge_hfq.parquet
```

---

## market-cap — A股市值排名

获取全 A 股实时市值排名，支持从低到高或从高到低排序，可按市值范围筛选。

```bash
tick market-cap [选项]
```

| 选项             | 默认      | 说明                                  |
| -------------- | ------- | ----------------------------------- |
| `-n, --limit`  | `100`   | 获取前 N 名                             |
| `--asc/--desc` | `asc`   | 排序方向：`--asc` 从低到高（默认），`--desc` 从高到低 |
| `--min-cap`    | —       | 最小市值（亿元）                            |
| `--max-cap`    | —       | 最大市值（亿元）                            |
| `-o, --output` | 自动命名到桌面 | 输出文件路径                              |
| `-f, --format` | `csv`   | 输出格式 `csv` / `json` / `parquet`     |
| `--show`       | —       | 在终端打印预览表格                           |


```bash
# 获取市值最低的 50 只股票（默认从低到高）
tick market-cap -n 50

# 获取市值最高的 20 只股票
tick market-cap -n 20 --desc

# 获取市值在 10-100 亿之间的股票（小盘股）
tick market-cap --min-cap 10 --max-cap 100 -o small_cap.csv

# 获取市值大于 1000 亿的股票（大盘股）
tick market-cap --min-cap 1000 --desc -n 50 -o large_cap.csv

# 仅预览，不保存文件
tick market-cap -n 10 --show

# 输出为 JSON
tick market-cap -n 30 -f json

# 输出为 Parquet（适合数据分析）
tick market-cap -n 1000 -f parquet -o all_stocks.parquet
```

a_market_cap_{sort}_{limit}[_{min}-{max}].{fmt}

示例：
- a_market_cap_asc_100.csv
- a_market_cap_desc_20.csv
- a_market_cap_asc_100_10-100.csv

| 列名 | 说明 |
|------|------|
| `序号` | 排名序号 |
| `股票代码` | A 股代码 |
| `股票名称` | 中文名称 |
| `总市值(亿元)` | 总市值 |
| `流通市值(亿元)` | 流通市值 |

---


## info — 品种基本信息

仅支持 yfinance（美股、港股、期货、加密货币）。

```bash
# 美股
tick info AAPL
tick info NVDA
tick info TSLA

# 港股
tick info 700.HK
tick info 9988.HK

# 期货
tick info GC=F    # 黄金
tick info CL=F    # 原油
tick info ES=F    # 标普 500 期货

# 加密货币
tick info BTC-USD
tick info ETH-USD
tick info SOL-USD
```

---

## symbols — 常用品种参考表

```bash
tick symbols                    # 全部类别
tick symbols --type stock       # 股票
tick symbols --type fund        # 基金/ETF
tick symbols --type futures     # 期货
tick symbols --type crypto      # 加密货币
```

---

## Symbol 格式速查

| 品种 | 格式示例 | 数据源 |
|------|----------|--------|
| 美股 | `AAPL` `TSLA` `NVDA` `MSFT` | yfinance |
| 港股 | `700.HK` `9988.HK` `3690.HK` | yfinance |
| A 股 | `sh600519` `sz000858` `sz002594` | akshare |
| 美国 ETF | `SPY` `QQQ` `GLD` `TLT` | yfinance |
| A 股 ETF | `sh510300` `sz159915` `sh518880` | akshare |
| 国际期货 | `GC=F` `CL=F` `ES=F` `NQ=F` | yfinance |
| 国内期货 | `AU` `AG` `SC` `RB` `CU` | akshare |
| 加密货币 | `BTC-USD` `ETH-USD` `SOL-USD` | yfinance |

前缀说明：`sh` = 上交所，`sz` = 深交所，无前缀 = 自动识别。

---

## 复权说明（仅 A 股）

| 参数 | 含义 | 适用场景 |
|------|------|----------|
| `qfq`（默认） | 前复权 | 可视化、涨跌幅计算 |
| `hfq` | 后复权 | 量化回测（历史价格固定不变） |
| `""` | 不复权 | 查看原始交易价格 |

> 可视化推荐前复权（`qfq`）：锚定当前真实价格，涨跌幅曲线连续，不因分红拆股产生跳空。

---

## fetch / batch 自动命名规则

不指定 `-o` 时，文件名格式为：

```
{symbol}_{start}_{end}_{interval}_{src}[_{adjust}].{fmt}
```

| 字段 | 说明 |
|------|------|
| `symbol` | 品种代码，`=` 删除，`/` 替换为 `-` |
| `start` / `end` | 日期，去掉横线（`20260328`） |
| `interval` | K 线周期（`1m` / `5m` / `1d` / `1wk` 等） |
| `src` | 数据源缩写（`yf` = yfinance，`ak` = akshare） |
| `adjust` | 仅 A 股附加（`qfq` / `hfq` / `raw`） |

示例：

```
BTC-USD_20250101_20250329_1d_yf.csv
sh600519_20240101_20250329_1d_ak_qfq.csv
sh600519_20260328_20260328_5m_ak_qfq.csv
AAPL_20260328_20260328_1m_yf.csv
GCF_20250101_20250329_1d_yf.csv
AAPL_20230101_20250329_1wk_yf.csv
```

---

## 输出列说明

### fetch / batch

| 列名 | 说明 |
|------|------|
| `date` | 日期或时间戳（索引） |
| `open` / `high` / `low` / `close` | 开高低收价格 |
| `volume` | 成交量 |
| `cum_pct` | 相对区间首根 K 线累计涨跌幅（%） |
| `pct_change` | 逐根 K 线涨跌幅（%） |

### batch-merge

| 列名 | 说明 |
|------|------|
| `date` | 日期（日线：`YYYY-MM-DD`；分时：`YYYY-MM-DD HH:MM:SS`） |
| `name` | 原始 Symbol 代码 |
| `display_name` | 品种名称（中文名或英文简称） |
| `category` | 资产类别（股票 / 基金ETF / 期货 / 加密货币） |
| `open` / `high` / `low` / `close` | 开高低收价格 |
| `volume` | 成交量 |
| `cum_pct` | 相对区间首根 K 线累计涨跌幅（%） |
| `pct_change` | 逐根 K 线涨跌幅（%） |
