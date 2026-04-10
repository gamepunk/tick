"""
tick Web UI - Streamlit 应用
"""
import streamlit as st
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta

from tick.core.models import Symbol, AssetType, FetchConfig, Interval
from tick.datasources.router import DataSourceRouter
from tick.utils.indicators import apply_indicators

# 页面配置
st.set_page_config(
    page_title="tick - 行情数据下载工具",
    page_icon="📈",
    layout="wide"
)


def sidebar():
    """侧边栏配置"""
    with st.sidebar:
        st.title("📈 tick")
        st.markdown("行情数据下载工具")
        st.markdown("---")
        
        page = st.radio(
            "导航",
            ["📊 单品种查询", "📈 多品种对比", "🔍 品种搜索"]
        )
        
    return page


def page_single_symbol():
    """单品种查询页面"""
    st.header("📊 单品种查询")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        symbol_input = st.text_input("品种代码", value="AAPL")
    
    with col2:
        asset_type = st.selectbox(
            "资产类型",
            options=["auto", "stock", "index", "crypto"],
            format_func=lambda x: "自动识别" if x == "auto" else x
        )
    
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("开始日期", value=datetime.now() - timedelta(days=365))
    with col2:
        end_date = st.date_input("结束日期", value=datetime.now())
    
    add_indicators = st.checkbox("添加技术指标", value=True)
    
    if st.button("🔍 查询数据", type="primary"):
        with st.spinner("正在获取数据..."):
            asset = None if asset_type == "auto" else asset_type
            sym = Symbol(raw=symbol_input, normalized=symbol_input.upper(),
                        asset_type=AssetType(asset) if asset else None)
            
            config = FetchConfig(
                symbol=sym,
                start=start_date.strftime("%Y-%m-%d"),
                end=end_date.strftime("%Y-%m-%d"),
                interval=Interval.DAY
            )
            
            datasource = DataSourceRouter.get_datasource(sym)
            if datasource:
                result = datasource.fetch(config)
                
                if result.success:
                    df = result.data
                    if add_indicators:
                        df = apply_indicators(df, ["ma", "boll"])
                    
                    # 显示图表
                    fig = go.Figure(data=[
                        go.Candlestick(
                            x=df.index,
                            open=df['open'],
                            high=df['high'],
                            low=df['low'],
                            close=df['close']
                        )
                    ])
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # 显示数据
                    st.dataframe(df)
                else:
                    st.error(result.error_message)


def page_multi_symbol():
    """多品种对比页面"""
    st.header("📈 多品种对比")
    st.info("功能开发中...")


def page_search():
    """品种搜索页面"""
    st.header("🔍 品种搜索")
    st.info("功能开发中...")


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
