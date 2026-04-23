# -*- coding: utf-8 -*-
"""
中国省会城市空气质量洞察 - Streamlit 主应用
"""

import streamlit as st

# ==================== 页面全局配置 ====================
st.set_page_config(
    page_title="中国省会城市空气质量洞察",
    page_icon="🌏",
    layout="wide"
)

# ==================== 自定义蓝色主题 CSS ====================
st.markdown("""
<style>
    /* 全局背景 */
    .stApp {
        background: linear-gradient(135deg, #f0f8ff 0%, #e6f2ff 100%);
    }
    
    /* 侧边栏 */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1a365d 0%, #0f2440 100%);
    }
    section[data-testid="stSidebar"] * {
        color: #ffffff !important;
    }
    section[data-testid="stSidebar"] button {
        background: #2b6cb0 !important;
        color: white !important;
        border-radius: 8px !important;
    }
    
    /* 标题样式 */
    h1, h2, h3 {
        color: #0a2540 !important;
        font-weight: 600 !important;
    }
    
    /* 卡片容器 */
    div[data-testid="stMetric"] {
        background: white;
        border-radius: 12px;
        padding: 16px;
        box-shadow: 0 2px 8px rgba(0, 49, 102, 0.1);
        border: 1px solid #cce0ff;
    }
    
    /* 数据表格 */
    div[data-testid="stDataFrame"] {
        border-radius: 10px;
        overflow: hidden;
        border: 1px solid #cce0ff;
    }
    div[data-testid="stDataFrame"] th {
        background: #1e4d8c !important;
        color: white !important;
        font-weight: 600 !important;
    }
    div[data-testid="stDataFrame"] td {
        background: white !important;
    }
    
    /* 按钮 */
    .stButton button {
        background: linear-gradient(135deg, #2b6cb0 0%, #1a365d 100%);
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 8px 20px !important;
        font-weight: 600 !important;
        transition: all 0.3s ease !important;
    }
    .stButton button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(27, 79, 140, 0.3);
    }
    
    /* 信息提示框 */
    .stAlert {
        border-radius: 10px;
        border-left: 4px solid #2b6cb0;
    }
    
    /* 欢迎卡片 */
    .welcome-card {
        background: linear-gradient(135deg, #ffffff 0%, #f5faff 100%);
        border-radius: 16px;
        padding: 24px;
        margin-bottom: 24px;
        border: 1px solid #cce0ff;
        box-shadow: 0 4px 12px rgba(0, 49, 102, 0.08);
    }
</style>
""", unsafe_allow_html=True)

# ==================== 主界面 ====================
st.title("🌏 中国省会城市空气质量实时监测与历史分析")

# ==================== 欢迎区域 ====================
st.markdown("""
<div class="welcome-card">
    <h2 style="margin-top: 0; color: #1a365d;">👋 欢迎使用空气质量洞察平台</h2>
    <p style="font-size: 1.1rem; color: #2d3748; margin-bottom: 8px;">
        实时监测全国31个省会及直辖市的空气质量，提供历史趋势分析与气象预警服务。
    </p>
    <p style="font-size: 0.95rem; color: #4a5568; margin-bottom: 0;">
        👨‍💻 制作人：刘宇博 · 江毅 · 张睿 ｜ 大数据与人工智能导论课程项目
    </p>
</div>
""", unsafe_allow_html=True)

st.markdown("---")

# ==================== 功能导航说明 ====================
st.markdown("""
### 📋 功能模块

| 模块 | 说明 |
|:---|:---|
| **实时监测** | 查看各城市最新 AQI、首要污染物、空气质量等级，支持全国热力图 |
| **历史分析** | 基于2015-2024年历史数据，分析空气质量演变趋势与规划驱动因素 |
| **一键分析** | 基于最新爬取数据，生成今日空气质量快报（平均AQI、等级分布、污染物统计） |
| **气象预警** | 全国气象预警实时监测，按等级分类展示，支持按省份筛选 |
""")

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

    st.markdown("---")
    st.caption("© 2026 刘宇博 · 江毅 · 张睿")
