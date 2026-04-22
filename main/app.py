# -*- coding: utf-8 -*-
"""
中国省会城市空气质量洞察 - Streamlit 主应用
"""

import streamlit as st
import os
import sys

# ==================== 路径设置 ====================
# 确保当前目录在 Python 路径中，以便正确导入 utils 模块
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# ==================== 页面全局配置 ====================
st.set_page_config(
    page_title="中国省会城市空气质量洞察",
    page_icon="🌏",
    layout="wide"
)

# ==================== 主界面 ====================
st.title("🌏 中国省会城市空气质量实时监测与历史分析")
st.markdown("---")

# ==================== 侧边栏 - 数据状态 ====================
with st.sidebar:
    st.header("📊 数据状态")
    st.info("等待成员A接入实时数据...")
    # TODO: 接入实际数据后，可替换为：
    # from utils.data_loader import load_latest_data
    # df = load_latest_data()
    # if not df.empty:
    #     st.success(f"最近更新：{df['update_time'].max()}")

# ==================== 欢迎说明 ====================
st.markdown("""
### 欢迎使用本应用

本应用面向中国省会城市的空气质量数据，提供两大核心功能模块：

| 模块 | 说明 |
|:---|:---|
| **实时监测** | 查看各城市最新 AQI、首要污染物、空气质量等级等实时数据 |
| **历史分析** | 基于十年历史数据，探索空气质量的时间趋势与空间分布特征 |

请通过**顶部导航栏**切换不同页面。
""")