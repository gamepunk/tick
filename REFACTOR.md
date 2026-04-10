# tick v0.1.0 重构版

## 概述

这是 tick 的模块化重构版本，采用分层架构设计，支持更强大的功能和更好的可维护性。

## 新架构

```
tick/
├── core/               # 核心层
│   ├── models.py       # 数据模型 (Symbol, FetchConfig, FetchResult)
│   ├── config.py       # 配置管理 (YAML配置、缓存目录)
│   └── exceptions.py   # 自定义异常
├── datasources/        # 数据源层
│   ├── base.py         # 抽象基类与注册表
│   ├── router.py       # 智能数据源路由
│   ├── yfinance_ds.py  # Yahoo Finance
│   ├── akshare_ds.py   # A股/北交所
│   └── ccxt_ds.py      # 加密货币
├── utils/              # 工具层
│   ├── symbols.py      # 代码标准化
│   ├── display.py      # Rich 显示
│   ├── cache.py        # SQLite 缓存
│   ├── filename.py     # 文件名生成
│   ├── indicators.py   # 技术指标
│   ├── interactive.py  # 交互式搜索
│   └── async_fetch.py  # 异步下载
├── main.py             # 新 CLI 入口
└── cli.py              # 旧 CLI (保持兼容)
```

## 新功能

### 1. 配置系统
```bash
# 初始化配置文件
tick2 config --init

# 配置文件位置
# macOS/Linux: ~/.config/tick/config.yaml
# Windows: %APPDATA%/tick/config.yaml
```

配置内容：
```yaml
default_output_dir: ~/Desktop
default_format: csv
cache:
  enabled: true
  ttl: 3600
display:
  color: true
  progress_bar: true
```

### 2. 数据缓存
```bash
# 默认使用缓存
tick2 fetch AAPL

# 强制刷新
tick2 fetch AAPL --no-cache
```

### 3. 技术指标
```bash
# 添加单个指标
tick2 fetch AAPL --indicator rsi

# 添加多个指标
tick2 fetch AAPL --indicator ma --indicator boll --indicator macd

# 添加所有指标
tick2 fetch AAPL --indicator all
```

支持的指标：
- `ma` - 移动平均线 (5/10/20/60日)
- `boll` - 布林带
- `rsi` - RSI
- `macd` - MACD
- `kdj` - KDJ
- `atr` - 平均真实波幅
- `obv` - 能量潮
- `all` - 全部指标

### 4. 交互式搜索
```bash
# 交互式搜索并下载
tick2 search

# 搜索并显示结果
tick2 search 茅台
```

### 5. 异步批量下载
```bash
# 使用 4 个并发
tick2 batch AAPL TSLA BTC-USD --workers 4

# 统一指定资产类型
tick2 batch GSPC DJI --asset index

# 分别指定资产类型
tick2 batch AAPL BTC-USD --asset stock --asset crypto
```

## 快速开始

```bash
# 安装（包含所有依赖）
pip install -e ".[web,dev]"

# 初始化配置
tick config --init

# 使用新版 CLI
tick fetch AAPL --show
tick fetch AAPL --indicator rsi
tick search 茅台
tick batch AAPL TSLA BTC-USD --workers 4

# 启动 Web UI
tick-web
```

## 命令对照表

| 功能 | 旧版命令 | 新版命令 |
|------|---------|---------|
| 单品种下载 | `tick fetch AAPL` | `tick fetch AAPL` |
| 批量下载 | `tick batch AAPL TSLA` | `tick batch AAPL TSLA --workers 4` |
| 批量合并 | `tick batch-merge ...` | `tick batch-merge ...` |
| 配置管理 | ❌ 不支持 | `tick config --init` |
| 交互式搜索 | ❌ 不支持 | `tick search` |
| 技术指标 | ❌ 不支持 | `tick fetch AAPL --indicator rsi` |
| Web UI | ❌ 不支持 | `tick-web` |

## 与旧版对比

| 特性 | 旧版 (cli.py) | 新版 (main.py) |
|------|--------------|----------------|
| 代码行数 | ~1400 行 | 模块化分散 |
| 扩展性 | 差 | 好（插件式数据源）|
| 缓存 | 无 | SQLite 缓存 |
| 技术指标 | 无 | 内置 7 种 |
| 配置系统 | 无 | YAML 配置 |
| 异步下载 | 无 | 支持 |
| 交互式搜索 | 无 | 支持 |

## 升级说明

已统一使用 `tick` 命令运行新版 CLI。如需使用旧版，可用：

```bash
tick-legacy fetch AAPL
```

## 后续优化方向

1. **插件系统** - 支持自定义数据源插件
2. **Web UI** - 基于 Streamlit 的图形界面
3. **数据库存储** - PostgreSQL/MySQL 支持
4. **实时监控** - 订阅式实时数据更新
5. **量化回测** - 集成 backtrader
