# tick — 行情数据下载 CLI 工具

支持国内外股票、基金、期货、加密货币数据下载，数据源覆盖 yfinance 和 akshare。

## 安装

```bash
pip install tick
```

## 安装依赖

```bash
pip install yfinance akshare pandas rich click
```

## 用法

```bash
# 安装后使用 tick 命令
tick <command> [options]

# 或直接从源码运行
python3 -m tick.cli <command> [options]
```

---

## 命令说明

### `fetch` — 下载单品种

```
tick fetch <SYMBOL> [选项]

选项：
  -s, --start        开始日期 YYYY-MM-DD（默认1年前）
  -e, --end          结束日期 YYYY-MM-DD（默认今天）
  -i, --interval     K线周期 1d/1wk/1mo（仅 yfinance 有效，默认 1d）
  -o, --output       指定输出文件路径（默认自动命名保存到桌面）
  -f, --format       输出格式 csv/json/parquet（默认 csv）
  --adjust           复权方式 qfq/hfq/""（仅 A股有效，默认 qfq 前复权）
  --pct/--no-pct     是否添加涨跌幅列（默认开启）
  --market           强制指定数据源 yfinance/akshare_cn/akshare_futures
  --show             下载完成后打印数据摘要
```

**加密货币：**

```bash
# 比特币日线，2025年至今
tick fetch BTC-USD -s 2025-01-01

# 以太坊，指定结束日期
tick fetch ETH-USD -s 2024-01-01 -e 2024-12-31

# Solana，保存为 json
tick fetch SOL-USD -s 2025-01-01 -f json

# 币安币，打印摘要
tick fetch BNB-USD -s 2025-01-01 --show

# 比特币周线
tick fetch BTC-USD -s 2023-01-01 -i 1wk

# 以太坊月线
tick fetch ETH-USD -s 2020-01-01 -i 1mo
```

**美股：**

```bash
# 苹果日线
tick fetch AAPL -s 2024-01-01

# 特斯拉，保存为 parquet
tick fetch TSLA -s 2024-01-01 -f parquet

# 英伟达，指定输出路径
tick fetch NVDA -s 2024-01-01 -o nvda_2024.csv

# 谷歌，周线，打印摘要
tick fetch GOOGL -s 2023-01-01 -i 1wk --show

# 微软月线，2020年起
tick fetch MSFT -s 2020-01-01 -i 1mo
```

**港股：**

```bash
# 腾讯
tick fetch 700.HK -s 2024-01-01

# 阿里巴巴
tick fetch 9988.HK -s 2024-01-01

# 美团，保存为 json
tick fetch 3690.HK -s 2024-01-01 -f json
```

**A股（支持复权）：**

```bash
# 贵州茅台，前复权（默认）
tick fetch sh600519 -s 2024-01-01

# 贵州茅台，后复权
tick fetch sh600519 -s 2024-01-01 --adjust hfq

# 贵州茅台，不复权（原始价格）
tick fetch sh600519 -s 2024-01-01 --adjust ""

# 五粮液，前复权，打印摘要
tick fetch sz000858 -s 2024-01-01 --show

# 中国平安
tick fetch sh601318 -s 2023-01-01

# 比亚迪
tick fetch sz002594 -s 2023-01-01 --show
```

**A股 ETF：**

```bash
# 沪深300 ETF
tick fetch sh510300 -s 2024-01-01

# 创业板 ETF
tick fetch sz159915 -s 2024-01-01

# 中概互联 ETF，后复权
tick fetch sh513050 -s 2023-01-01 --adjust hfq

# 科创50 ETF，打印摘要
tick fetch sh588000 -s 2024-01-01 --show
```

**美国 ETF：**

```bash
# 标普500 ETF
tick fetch SPY -s 2024-01-01

# 纳斯达克100 ETF
tick fetch QQQ -s 2024-01-01

# 黄金 ETF
tick fetch GLD -s 2024-01-01

# 原油 ETF
tick fetch USO -s 2024-01-01 --show
```

**国际期货：**

```bash
# 黄金期货（COMEX）
tick fetch GC=F -s 2025-01-01 --show

# 原油期货（WTI）
tick fetch CL=F -s 2025-01-01

# 标普500期货
tick fetch ES=F -s 2025-01-01

# 纳斯达克期货
tick fetch NQ=F -s 2025-01-01

# 白银期货
tick fetch SI=F -s 2025-01-01 --show
```

**国内期货（akshare）：**

```bash
# 沪金期货主力
tick fetch AU --market akshare_futures -s 2025-01-01

# 沪银期货主力
tick fetch AG --market akshare_futures -s 2025-01-01

# 原油期货主力（INE）
tick fetch SC --market akshare_futures -s 2025-01-01

# 螺纹钢期货主力
tick fetch RB --market akshare_futures -s 2025-01-01 --show
```

---

### `batch` — 批量下载

```
tick batch <SYMBOL1> <SYMBOL2> ... [选项]

选项：
  -s, --start      开始日期
  -e, --end        结束日期
  -d, --dir        输出目录（默认桌面）
  -f, --format     输出格式 csv/json/parquet（默认 csv）
  --adjust         复权方式 qfq/hfq/""（仅 A股有效，默认 qfq）
  --pct/--no-pct   是否添加涨跌幅列（默认开启）
```

**混合品种批量：**

```bash
# 加密货币组合
tick batch BTC-USD ETH-USD SOL-USD BNB-USD -s 2025-01-01 -d ./crypto

# 美股科技股
tick batch AAPL TSLA NVDA GOOGL MSFT -s 2024-01-01 -d ./us_stocks

# A股白酒板块，前复权
tick batch sh600519 sz000858 sz000596 -s 2024-01-01 -d ./baijiu

# A股白酒板块，后复权对比
tick batch sh600519 sz000858 sz000596 -s 2024-01-01 --adjust hfq -d ./baijiu_hfq

# 国际期货组合
tick batch GC=F CL=F SI=F NQ=F -s 2025-01-01 -d ./futures

# 跨市场混合（A股 + 美股 + 加密）
tick batch sh600519 AAPL BTC-USD GC=F -s 2024-01-01 -d ./mixed
```

**指定格式批量：**

```bash
# 全部保存为 json
tick batch AAPL BTC-USD GC=F -s 2025-01-01 -f json -d ./data

# 全部保存为 parquet（适合 pandas 大批量处理）
tick batch AAPL TSLA NVDA GOOGL -s 2020-01-01 -f parquet -d ./data
```

---

### `info` — 查看品种基本信息

仅 yfinance 支持，适用于美股、港股、期货、加密货币。

```bash
# 美股
tick info AAPL
tick info TSLA
tick info NVDA

# 港股
tick info 700.HK
tick info 9988.HK

# 期货
tick info GC=F
tick info CL=F

# 加密货币
tick info BTC-USD
tick info ETH-USD
```

---

### `symbols` — 常用品种参考表

```bash
tick symbols                    # 全部
tick symbols --type stock       # 仅股票
tick symbols --type futures     # 仅期货
tick symbols --type crypto      # 仅加密货币
tick symbols --type fund        # 仅基金/ETF
```

### `help-symbols` — Symbol 格式说明

```bash
tick help-symbols
```

---

## 自动命名规则

不指定 `-o` 时，文件名自动生成，格式为：

```
{symbol}_{start}_{end}_{interval}_{src}[_{adjust}].{fmt}
```

| 字段 | 说明 |
|------|------|
| `symbol` | 品种代码，`=` 删除，`/` 替换为 `-` |
| `start` / `end` | 日期，去掉横线（`20250101`） |
| `interval` | K线周期（`1d` / `1wk` / `1mo`） |
| `src` | 数据源缩写（`yf` / `ak`） |
| `adjust` | 仅 A股附加（`qfq` / `hfq` / `raw`） |

**示例：**

```
BTC-USD_20250101_20250327_1d_yf.csv
sh600519_20240101_20250327_1d_ak_qfq.csv
sh600519_20240101_20250327_1d_ak_hfq.csv
GCF_20250101_20250327_1d_yf.csv
AAPL_20230101_20250327_1wk_yf.csv
sh510300_20240101_20250327_1d_ak_qfq.csv
```

---

## 复权说明

`--adjust` 仅对 A股（`akshare_cn`）有效，其他数据源静默忽略。

| 参数值 | 含义 | 适用场景 |
|--------|------|----------|
| `qfq`（默认） | 前复权 | 数据可视化、涨跌幅计算 |
| `hfq` | 后复权 | 量化回测（历史价格固定不变） |
| `""` | 不复权 | 查看原始交易价格 |

**可视化推荐使用前复权（`qfq`）**：锚定当前真实价格，涨跌幅曲线连续准确，不会因分红拆股产生虚假跳空。

---

## Symbol 格式速查

| 品种 | Symbol 格式 | 数据源 |
|------|------------|--------|
| 美股 | `AAPL`, `TSLA`, `NVDA` | yfinance |
| 港股 | `9988.HK`, `700.HK` | yfinance |
| A股 | `sh600519`, `sz000858` | akshare |
| 美国ETF | `SPY`, `QQQ`, `GLD` | yfinance |
| A股ETF | `sh510300`, `sz159915` | akshare |
| 国际期货 | `GC=F`, `CL=F`, `ES=F` | yfinance |
| 国内期货 | `AU`, `AG`, `SC`, `RB` | akshare |
| 加密货币 | `BTC-USD`, `ETH-USD`, `SOL-USD` | yfinance |

---

## 输出 CSV 格式

```
date,open,high,low,close,volume,cum_pct,pct_change
2025-01-02,2630.0,2665.0,2620.0,2650.0,123456,0.0,0.0
2025-01-03,2650.0,2710.0,2645.0,2698.0,98765,1.81,1.81
...
```

| 列名 | 说明 |
|------|------|
| `date` | 日期 |
| `open` / `high` / `low` / `close` | 开高低收 |
| `volume` | 成交量 |
| `cum_pct` | 相对首日累计涨跌幅（%） |
| `pct_change` | 日涨跌幅（%） |
