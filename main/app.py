# -*- coding: utf-8 -*-
"""
中国省会城市空气质量洞察 - Streamlit 主应用
首页展示功能导航卡片，无侧边栏，背景为天气图片（高斯模糊）
"""

import streamlit as st

# ==================== 页面全局配置 ====================
st.set_page_config(
    page_title="中国省会城市空气质量洞察",
    page_icon="🌏",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ==================== 自定义 CSS：高斯模糊背景、强制居中、等宽卡片 ====================
st.markdown("""
<style>
    /* 完全隐藏侧边栏 */
    section[data-testid="stSidebar"] {
        display: none;
    }

    /* 全局背景：天气图片 + 高斯模糊 */
    .stApp {
        background-image: url("https://images.pexels.com/photos/531756/pexels-photo-531756.jpeg?auto=compress&cs=tinysrgb&w=1260&h=750&dpr=2");
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
    }

    /* 添加高斯模糊层（伪元素） */
    .stApp::before {
        content: "";
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: inherit;
        filter: blur(6px);
        z-index: -1;
    }

    /* 主内容区域：半透明白色背景，居中，圆角 */
    .main > div {
        background-color: rgba(255, 255, 255, 0.85);
        border-radius: 30px;
        padding: 2.5rem 3.5rem;
        margin: 3rem auto;
        max-width: 1200px;
        box-shadow: 0 12px 28px rgba(0, 30, 60, 0.25);
        text-align: center;
    }

    /* 所有标题居中 */
    h1, h2, h3 {
        color: #0a2540 !important;
        font-weight: 700 !important;
        text-align: center !important;
    }

    /* 强制列等宽 */
    div[data-testid="column"] {
        flex: 1 1 0% !important;
        min-width: 0;
    }

    /* 卡片链接按钮样式：填满列宽，文字居中 */
    div[data-testid="stVerticalBlock"] > div[data-testid="stHorizontalBlock"] a {
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        width: 100%;
        min-height: 120px;
        background: linear-gradient(145deg, #ffffff 0%, #eef6ff 100%);
        border-radius: 24px;
        padding: 1.5rem 0.5rem;
        text-decoration: none;
        color: #1a365d !important;
        font-weight: 600;
        font-size: 1.4rem;
        border: 1px solid #b8d4f0;
        box-shadow: 0 8px 16px rgba(0, 40, 80, 0.1);
        transition: all 0.3s ease;
        box-sizing: border-box;
        text-align: center;
    }

    div[data-testid="stVerticalBlock"] > div[data-testid="stHorizontalBlock"] a:hover {
        transform: translateY(-6px);
        box-shadow: 0 16px 24px rgba(27, 79, 140, 0.2);
        background: linear-gradient(145deg, #e6f0ff 0%, #d4e6ff 100%);
        border-color: #2b6cb0;
    }

    /* 卡片内描述文字（居中） */
    .card-desc {
        font-size: 0.9rem;
        color: #2d3748;
        margin-top: 8px;
        font-weight: 400;
        text-align: center;
        width: 100%;
    }

    /* 底部信息居中 */
    .footer {
        text-align: center;
        margin-top: 3rem;
        color: #1a365d;
        font-weight: 500;
    }

    /* 欢迎卡片内部文字强制居中 */
    .welcome-card {
        text-align: center;
        margin: 20px 0;
    }
    .welcome-card p {
        text-align: center !important;
        margin-left: auto;
        margin-right: auto;
    }
</style>
""", unsafe_allow_html=True)

# ==================== 主界面 ====================
st.title("🌏 中国省会城市空气质量实时监测与历史分析")

# 欢迎卡片
st.markdown("""
<div style="background: rgba(255,255,255,0.6); border-radius: 24px; padding: 24px 36px; margin: 20px 0; backdrop-filter: blur(4px);">
    <h2 style="margin:0 0 12px 0; color:#0a2540; text-align:center;">👋 欢迎使用空气质量洞察平台</h2>
    <p style="font-size:1.15rem; margin:0 auto 10px auto; color:#1a365d; text-align:center;">
        实时监测全国31个省会及直辖市的空气质量，提供历史趋势分析与气象预警服务。
    </p>
    <p style="margin-top:10px; color:#2c5282; font-weight:500; text-align:center;">
        👨‍💻 制作人：刘宇博 · 江毅 · 张睿 ｜ 大数据与人工智能导论课程项目
    </p>
</div>
""", unsafe_allow_html=True)

st.markdown("---")

# ==================== 功能模块 ====================
st.subheader("📌 功能模块")

# 使用四列等宽（通过 CSS 已强制等宽）
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.page_link("pages/1_实时监测.py", label="📍 实时监测", help="查看最新AQI排名与全国热力图")
    st.markdown("<div class='card-desc'>最新AQI排名 · 全国热力图 · 实时更新</div>", unsafe_allow_html=True)

with col2:
    st.page_link("pages/2_历史分析.py", label="📈 历史分析", help="十年趋势 · 相关性分析 · 驱动因素")
    st.markdown("<div class='card-desc'>2015-2024趋势 · 相关性热力图 · 随机森林重要性</div>", unsafe_allow_html=True)

with col3:
    st.page_link("pages/3_一键分析.py", label="📊 今日快报", help="基于最新数据的空气质量快报")
    st.markdown("<div class='card-desc'>平均AQI · 等级分布 · 首要污染物统计</div>", unsafe_allow_html=True)

with col4:
    st.page_link("pages/4_气象预警.py", label="🚨 气象预警", help="全国预警实时监测")
    st.markdown("<div class='card-desc'>预警总数 · 等级分类 · 按省份筛选</div>", unsafe_allow_html=True)

# ==================== 底部制作人信息 ====================
st.markdown("---")
st.markdown("""
<div class="footer">
    © 2026 刘宇博 · 江毅 · 张睿 ｜ 大数据与人工智能导论课程项目
</div>
""", unsafe_allow_html=True)
