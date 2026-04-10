# AGENTS.md — tick 项目开发指南

> 本文档供 AI 编码助手阅读，帮助理解 tick 项目的架构和开发规范。

## 项目概述

tick 是一个行情数据下载命令行工具，支持国内外股票、基金、期货、加密货币和指数数据的获取。

**当前版本**: v0.1.0  
**架构**: 模块化架构（已重构）

## 技术栈

- **语言**: Python 3.10+
- **CLI 框架**: Click
- **数据处理**: pandas, pyarrow（Parquet 支持）
- **数据源**: yfinance, akshare, ccxt
- **UI 美化**: rich（表格、进度条、彩色输出）
- **Web UI**: Streamlit + Plotly
- **配置**: YAML
- **测试**: pytest

## 项目结构

```
tick/
├── tick/                       # 主包
│   ├── __init__.py
│   ├── main.py                 # CLI 入口（新版）
│   ├── core/                   # 核心层
│   │   ├── models.py           # 数据模型
│   │   ├── config.py           # 配置管理
│   │   ├── exceptions.py       # 异常定义
│   │   └── logger.py           # 日志系统
│   ├── datasources/            # 数据源层
│   │   ├── base.py             # 抽象基类
│   │   ├── router.py           # 数据源路由
│   │   ├── yfinance_ds.py      # Yahoo Finance
│   │   ├── akshare_ds.py       # A股/北交所
│   │   └── ccxt_ds.py          # 加密货币
│   ├── utils/                  # 工具层
│   │   ├── symbols.py          # 代码处理
│   │   ├── display.py          # 显示工具
│   │   ├── cache.py            # 缓存系统
│   │   ├── filename.py         # 文件名生成
│   │   ├── indicators.py       # 技术指标
│   │   ├── interactive.py      # 交互式搜索
│   │   └── async_fetch.py      # 异步下载
│   └── commands/               # 命令模块
├── web/                        # Web UI
│   ├── app.py                  # Streamlit 应用
│   └── run.py                  # 启动脚本
├── tests/                      # 测试
│   ├── unit/
│   └── integration/
├── pyproject.toml              # 项目配置
└── README.md                   # 用户文档
```

## 核心模块

### 1. 数据模型 (core/models.py)

```python
class Symbol:
    raw: str                      # 原始输入
    normalized: str               # 标准化代码
    asset_type: AssetType         # 资产类型

class FetchConfig:
    symbol: Symbol
    start: str
    end: str
    interval: Interval
    exchange: str

class FetchResult:
    symbol: Symbol
    data: pd.DataFrame
    success: bool
    error_message: str
```

### 2. 数据源基类 (datasources/base.py)

```python
class BaseDataSource(ABC):
    @abstractmethod
    def fetch(self, config: FetchConfig) -> FetchResult:
        pass
    
    @abstractmethod
    def validate_symbol(self, symbol: Symbol) -> bool:
        pass
    
    @abstractmethod
    def search(self, query: str, limit: int) -> list[dict]:
        pass
```

### 3. 数据源注册与路由

```python
# 注册数据源
@register_datasource("yfinance")
class YFinanceDataSource(BaseDataSource):
    ...

# 路由自动选择数据源
source_name = DataSourceRouter.detect_market(symbol)
datasource = DataSourceRegistry.create(source_name)
```

## 开发规范

### 代码风格

1. **类型注解**: 使用 Python 3.10+ 语法（如 `str | None`）
2. **字符串引号**: 双引号为主
3. **注释语言**: 中文
4. **分隔线**: `# ─────────────────────────────────────────`

### 添加新数据源

1. 继承 `BaseDataSource`
2. 实现 `fetch()`, `validate_symbol()`, `search()` 方法
3. 使用 `@register_datasource("name")` 装饰器注册
4. 在 `router.py` 中添加识别规则

### 添加新命令

1. 在 `main.py` 中使用 `@cli.command("name")` 装饰器
2. 使用 `@click.option()` 定义参数
3. 使用 `print_panel()` 等工具函数显示输出

## 测试

```bash
# 运行所有测试
pytest tests/ -v

# 运行单元测试
pytest tests/unit -v

# 运行集成测试
pytest tests/integration -v

# 查看覆盖率
pytest --cov=tick --cov-report=html
```

## 构建和发布

```bash
# 构建
python -m build

# 安装本地开发版
pip install -e ".[web,dev]"

# 发布到 PyPI
python -m twine upload dist/*
```

## 相关资源

- **GitHub**: https://github.com/gamepunk/tick
- **PyPI**: tick

---

*文档版本: v0.1.0 | 最后更新: 2025-04-10*
