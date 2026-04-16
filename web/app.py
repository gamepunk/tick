"""
tick Web UI - Streamlit 应用
"""

import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).parent.parent))

from datetime import datetime, timedelta

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from tick.core.models import ASSET_TYPE_NAMES, AssetType, FetchConfig, Interval, Symbol
from tick.datasources.base import DataSourceRegistry
from tick.datasources.router import DataSourceRouter
from tick.utils.indicators import apply_indicators

# get_asset_display_name imported via models"

st.set_page_config(page_title="tick - 行情数据下载工具", page_icon="📈", layout="wide")


def sidebar():
    """侧边栏配置"""
    with st.sidebar:
        st.title("📈 tick")
        st.markdown("行情数据下载工具 v0.2.1")
        st.markdown("---")

        page = st.radio("导航", ["📊 单品种查询", "📈 多品种对比", "🔍 品种搜索"])

        st.markdown("---")
        st.markdown("### 关于")
        st.info("支持股票、基金、期货、加密货币、指数数据")

    return page


def get_asset_options():
    """获取所有资产类型选项"""
    return ["auto"] + AssetType.choices()


def format_asset_option(x):
    """格式化资产类型显示"""
    if x == "auto":
        return "自动识别"
    return ASSET_TYPE_NAMES.get(AssetType(x), x)


def page_single_symbol():
    """单品种查询页面"""
    st.header("📊 单品种查询")

    col1, col2, col3 = st.columns([2, 1, 1])

    with col1:
        symbol_input = st.text_input(
            "品种代码", value="AAPL", help="例如: AAPL, sh600519, BTC-USD, GSPC, GC=F"
        )

    with col2:
        asset_type = st.selectbox(
            "资产类型", options=get_asset_options(), format_func=format_asset_option
        )

    with col3:
        interval = st.selectbox("K线周期", options=[i.value for i in Interval], index=5)

    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input(
            "开始日期", value=datetime.now() - timedelta(days=365)
        )
    with col2:
        end_date = st.date_input("结束日期", value=datetime.now())

    with st.expander("高级选项"):
        col1, col2, col3 = st.columns(3)
        with col1:
            add_indicators = st.checkbox("添加技术指标", value=True)
        with col2:
            indicator_options = ["ma", "boll", "rsi", "macd", "kdj"]
            selected_indicators = (
                st.multiselect(
                    "选择指标", options=indicator_options, default=["ma", "boll"]
                )
                if add_indicators
                else []
            )
        with col3:
            exchange = st.selectbox(
                "交易所（仅加密货币）",
                options=["binance", "okx", "bybit", "kraken", "bitstamp"],
                index=0,
            )

    if st.button("🔍 查询数据", type="primary", use_container_width=True):
        with st.spinner("正在获取数据..."):
            asset = None if asset_type == "auto" else asset_type
            sym = Symbol(
                raw=symbol_input,
                normalized=symbol_input.upper(),
                asset_type=AssetType(asset) if asset else None,
            )

            config = FetchConfig(
                symbol=sym,
                start=start_date.strftime("%Y-%m-%d"),
                end=end_date.strftime("%Y-%m-%d"),
                interval=Interval(interval),
                exchange=exchange,
            )

            datasource = DataSourceRouter.get_datasource(sym)
            if datasource:
                result = datasource.fetch(config)

                if result.success:
                    df = result.data

                    if add_indicators and selected_indicators:
                        df = apply_indicators(df, selected_indicators)

                    st.success(f"✅ 成功获取 {len(df)} 条数据")

                    # 数据摘要
                    if "close" in df.columns:
                        col1, col2, col3, col4 = st.columns(4)
                        with col1:
                            st.metric("最新价", f"{df['close'].iloc[-1]:.2f}")
                        with col2:
                            change = (
                                df["close"].iloc[-1] / df["close"].iloc[0] - 1
                            ) * 100
                            st.metric("涨跌幅", f"{change:.2f}%")
                        with col3:
                            st.metric("最高价", f"{df['high'].max():.2f}")
                        with col4:
                            st.metric("最低价", f"{df['low'].min():.2f}")

                    # K线图
                    fig = go.Figure(
                        data=[
                            go.Candlestick(
                                x=df.index,
                                open=df["open"],
                                high=df["high"],
                                low=df["low"],
                                close=df["close"],
                                name="K线",
                            )
                        ]
                    )

                    # 添加均线
                    if "ma5" in df.columns:
                        fig.add_trace(
                            go.Scatter(
                                x=df.index,
                                y=df["ma5"],
                                name="MA5",
                                line=dict(color="orange"),
                            )
                        )
                    if "ma20" in df.columns:
                        fig.add_trace(
                            go.Scatter(
                                x=df.index,
                                y=df["ma20"],
                                name="MA20",
                                line=dict(color="blue"),
                            )
                        )

                    fig.update_layout(
                        title=f"{symbol_input.upper()} 价格走势",
                        yaxis_title="价格",
                        xaxis_title="日期",
                        height=500,
                    )
                    st.plotly_chart(fig, use_container_width=True)

                    # 技术指标子图
                    if "rsi" in df.columns or "macd" in df.columns:
                        st.subheader("📊 技术指标")

                        if "rsi" in df.columns:
                            fig_rsi = go.Figure()
                            fig_rsi.add_trace(
                                go.Scatter(x=df.index, y=df["rsi"], name="RSI")
                            )
                            fig_rsi.add_hline(
                                y=70,
                                line_dash="dash",
                                line_color="red",
                                annotation_text="超买",
                            )
                            fig_rsi.add_hline(
                                y=30,
                                line_dash="dash",
                                line_color="green",
                                annotation_text="超卖",
                            )
                            fig_rsi.update_layout(title="RSI", height=200)
                            st.plotly_chart(fig_rsi, use_container_width=True)

                        if "macd" in df.columns:
                            fig_macd = go.Figure()
                            colors = [
                                "red" if v < 0 else "green" for v in df["macd_hist"]
                            ]
                            fig_macd.add_trace(
                                go.Bar(
                                    x=df.index,
                                    y=df["macd_hist"],
                                    name="MACD Hist",
                                    marker_color=colors,
                                )
                            )
                            fig_macd.add_trace(
                                go.Scatter(x=df.index, y=df["macd"], name="MACD")
                            )
                            fig_macd.add_trace(
                                go.Scatter(
                                    x=df.index, y=df["macd_signal"], name="Signal"
                                )
                            )
                            fig_macd.update_layout(title="MACD", height=200)
                            st.plotly_chart(fig_macd, use_container_width=True)

                    # 原始数据
                    with st.expander("查看原始数据"):
                        st.dataframe(df, use_container_width=True)

                        csv = df.to_csv()
                        st.download_button(
                            label="📥 下载 CSV",
                            data=csv,
                            file_name=f"{symbol_input.upper()}_{datetime.now():%Y%m%d}.csv",
                            mime="text/csv",
                        )
                else:
                    st.error(f"❌ {result.error_message}")
            else:
                st.error("❌ 无法找到合适的数据源")


def page_multi_symbol():
    """多品种对比页面"""
    st.header("📈 多品种对比")

    symbols_input = st.text_area(
        "输入品种代码（每行一个）",
        value="AAPL\nTSLA\nBTC-USD",
        height=100,
        help="支持不同市场的品种，例如：AAPL, sh600519, BTC-USD, GSPC",
    )

    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        asset_type = st.selectbox(
            "统一资产类型（可选）",
            options=["auto"] + AssetType.choices(),
            format_func=format_asset_option,
        )
    with col2:
        start_date = st.date_input(
            "开始日期", value=datetime.now() - timedelta(days=90), key="multi_start"
        )
    with col3:
        end_date = st.date_input("结束日期", value=datetime.now(), key="multi_end")

    normalize_price = st.checkbox("标准化价格（首日=100）", value=True)

    if st.button("🔍 对比分析", type="primary", use_container_width=True):
        symbols = [s.strip() for s in symbols_input.split("\n") if s.strip()]

        if len(symbols) < 2:
            st.warning("请输入至少两个品种进行对比")
            return

        all_data = {}
        errors = []

        progress_bar = st.progress(0)
        status_text = st.empty()

        for i, sym_str in enumerate(symbols):
            status_text.text(f"正在获取 {sym_str}... ({i + 1}/{len(symbols)})")

            asset = None if asset_type == "auto" else asset_type
            sym = Symbol(
                raw=sym_str,
                normalized=sym_str.upper(),
                asset_type=AssetType(asset) if asset else None,
            )

            config = FetchConfig(
                symbol=sym,
                start=start_date.strftime("%Y-%m-%d"),
                end=end_date.strftime("%Y-%m-%d"),
                interval=Interval.DAY,
            )

            datasource = DataSourceRouter.get_datasource(sym)
            if datasource:
                result = datasource.fetch(config)
                if result.success:
                    all_data[sym_str.upper()] = result.data
                else:
                    errors.append(f"{sym_str}: {result.error_message}")
            else:
                errors.append(f"{sym_str}: 无法找到数据源")

            progress_bar.progress((i + 1) / len(symbols))

        status_text.empty()
        progress_bar.empty()

        if errors:
            for error in errors:
                st.warning(error)

        if all_data:
            st.success(f"✅ 成功获取 {len(all_data)} 个品种数据")

            # 对比图表
            fig = go.Figure()

            for symbol, df in all_data.items():
                if normalize_price:
                    normalized = df["close"] / df["close"].iloc[0] * 100
                    fig.add_trace(
                        go.Scatter(x=df.index, y=normalized, name=symbol, mode="lines")
                    )
                else:
                    fig.add_trace(
                        go.Scatter(x=df.index, y=df["close"], name=symbol, mode="lines")
                    )

            fig.update_layout(
                title="价格对比" + ("（标准化，首日=100）" if normalize_price else ""),
                yaxis_title="价格" if not normalize_price else "标准化价格",
                xaxis_title="日期",
                height=500,
            )

            st.plotly_chart(fig, use_container_width=True)

            # 收益对比表
            st.subheader("📊 收益对比")

            returns_data = []
            for symbol, df in all_data.items():
                first_price = df["close"].iloc[0]
                last_price = df["close"].iloc[-1]
                total_return = (last_price - first_price) / first_price * 100

                returns_data.append(
                    {
                        "品种": symbol,
                        "起始价": f"{first_price:.2f}",
                        "最新价": f"{last_price:.2f}",
                        "总收益": f"{total_return:.2f}%",
                        "最高价": f"{df['high'].max():.2f}",
                        "最低价": f"{df['low'].min():.2f}",
                        "数据条数": len(df),
                    }
                )

            returns_df = pd.DataFrame(returns_data)

            # 按收益排序
            returns_df["收益数值"] = returns_df["总收益"].str.rstrip("%").astype(float)
            returns_df = returns_df.sort_values("收益数值", ascending=False).drop(
                "收益数值", axis=1
            )

            st.dataframe(returns_df, use_container_width=True)

            # 下载合并数据
            with st.expander("下载合并数据"):
                merged_data = []
                for symbol, df in all_data.items():
                    df_copy = df.copy()
                    df_copy["symbol"] = symbol
                    df_copy["date"] = df_copy.index
                    merged_data.append(
                        df_copy[
                            ["date", "symbol", "open", "high", "low", "close", "volume"]
                        ]
                    )

                merged_df = pd.concat(merged_data, ignore_index=True)
                csv = merged_df.to_csv(index=False)
                st.download_button(
                    label="📥 下载合并 CSV",
                    data=csv,
                    file_name=f"comparison_{datetime.now():%Y%m%d}.csv",
                    mime="text/csv",
                )
        else:
            st.error("❌ 未能获取任何数据")


def page_search():
    """品种搜索页面"""
    st.header("🔍 品种搜索")

    query = st.text_input(
        "搜索关键词",
        placeholder="输入股票名称、代码或拼音，例如：茅台、AAPL、BTC",
        value="",
    )

    datasource_filter = st.multiselect(
        "数据源筛选",
        options=DataSourceRegistry.list_sources(),
        default=DataSourceRegistry.list_sources(),
    )

    if st.button("🔍 搜索", type="primary"):
        if not query:
            st.warning("请输入搜索关键词")
            return

        with st.spinner("正在搜索..."):
            all_results = []

            for source_name in datasource_filter:
                source = DataSourceRegistry.create(source_name)
                if source:
                    try:
                        results = source.search(query, limit=10)
                        for r in results:
                            r["source"] = source_name
                        all_results.extend(results)
                    except Exception as e:
                        st.warning(f"{source_name} 搜索失败: {e}")

            if all_results:
                st.success(f"✅ 找到 {len(all_results)} 个结果")

                for item in all_results:
                    with st.container():
                        col1, col2, col3, col4 = st.columns([2, 2, 1, 1])
                        with col1:
                            st.markdown(f"**{item.get('symbol', '')}**")
                        with col2:
                            st.text(item.get("name", ""))
                        with col3:
                            st.caption(f"类型: {item.get('type', 'unknown')}")
                        with col4:
                            if st.button(
                                "选择",
                                key=f"select_{item.get('symbol', '')}_{item.get('source', '')}",
                            ):
                                st.session_state["selected_symbol"] = item.get("symbol")
                                st.success(f"已选择 {item.get('symbol')}")

                                # 跳转到单品种查询
                                st.info("请在侧边栏切换到「单品种查询」页面查看")
            else:
                st.info("未找到匹配结果，请尝试其他关键词")

    # 常用品种推荐
    with st.expander("查看常用品种"):
        st.markdown("""
        **美股**: AAPL (苹果), TSLA (特斯拉), MSFT (微软), GOOGL (谷歌), AMZN (亚马逊)

        **港股**: 0700.HK (腾讯), 9988.HK (阿里巴巴), 3690.HK (美团)

        **A股**: sh600519 (茅台), sz000858 (五粮液), sh601318 (中国平安)

        **加密货币**: BTC-USD (比特币), ETH-USD (以太坊), SOL-USD (Solana)

        **指数**: GSPC (标普500), DJI (道琼斯), sh000001 (上证指数), bj899050 (北证50)

        **期货**: GC=F (黄金), CL=F (原油), AU (沪金)
        """)


def main():
    page = sidebar()

    if "📊 单品种查询" in page:
        page_single_symbol()
    elif "📈 多品种对比" in page:
        page_multi_symbol()
    elif "🔍 品种搜索" in page:
        page_search()


if __name__ == "__main__":
    main()
