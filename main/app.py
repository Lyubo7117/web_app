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

# ==================== 自定义 CSS ====================
st.markdown("""
<style>
    /* 隐藏侧边栏 */
    section[data-testid="stSidebar"] {
        display: none;
    }

    /* 全局背景 + 高斯模糊 */
    .stApp {
        background-image: url("https://images.pexels.com/photos/531756/pexels-photo-531756.jpeg?auto=compress&cs=tinysrgb&w=1260&h=750&dpr=2");
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
    }
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

    /* 主内容区：毛玻璃 */
    .main > div {
        background-color: rgba(255, 255, 255, 0.85);
        border-radius: 30px;
        padding: 2.5rem 3.5rem;
        margin: 3rem auto;
        max-width: 1200px;
        box-shadow: 0 12px 28px rgba(0, 30, 60, 0.25);
        text-align: center;
        backdrop-filter: blur(4px);
    }

    h1, h2, h3 {
        color: #0a2540 !important;
        font-weight: 700 !important;
        text-align: center !important;
    }

    /* 卡片网格 */
    .card-grid {
        display: flex;
        flex-wrap: wrap;
        justify-content: space-between;
        gap: 20px;
        margin: 30px 0;
    }

    /* 单个卡片：毛玻璃 + 无下划线 */
    .card {
        flex: 1 1 0px;
        min-width: 180px;
        background: rgba(255, 255, 255, 0.6);
        backdrop-filter: blur(4px);
        border-radius: 24px;
        padding: 24px 12px 16px 12px;
        text-decoration: none !important;
        color: #1a365d !important;
        border: 1px solid rgba(255, 255, 255, 0.8);
        box-shadow: 0 8px 16px rgba(0, 40, 80, 0.1);
        transition: all 0.3s ease;
        display: flex;
        flex-direction: column;
        align-items: center;
        text-align: center;
    }

    .card:hover {
        transform: translateY(-6px);
        box-shadow: 0 16px 24px rgba(27, 79, 140, 0.2);
        background: rgba(255, 255, 255, 0.8);
        border-color: #ffffff;
        text-decoration: none !important;
    }

    /* 卡片标题 */
    .card-title {
        font-size: 1.6rem;
        font-weight: 700;
        margin-bottom: 12px;
        color: #0a2540;
    }

    /* 卡片描述 */
    .card-desc {
        font-size: 0.95rem;
        color: #2d3748;
        font-weight: 400;
        line-height: 1.5;
    }

    /* 底部 */
    .footer {
        text-align: center;
        margin-top: 3rem;
        color: #1a365d;
        font-weight: 500;
    }
</style>
""", unsafe_allow_html=True)

# ==================== 主界面 ====================
st.title("🌏 中国省会城市空气质量实时监测与历史分析")

# 欢迎卡片（毛玻璃效果）
st.markdown("""
<div style="background: rgba(255,255,255,0.6); border-radius: 24px; padding: 24px 36px; margin: 20px 0; backdrop-filter: blur(4px); border: 1px solid rgba(255,255,255,0.8);">
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
st.subheader("📌 功能模块")

# ==================== 自定义 HTML 卡片（毛玻璃、无下划线、等宽） ====================
st.markdown("""
<div class="card-grid">
    <a class="card" href="/1_实时监测" target="_self">
        <div class="card-title">📍 实时监测</div>
        <div class="card-desc">最新AQI排名 · 全国热力图 · 实时更新</div>
    </a>
    <a class="card" href="/2_历史分析" target="_self">
        <div class="card-title">📈 历史分析</div>
        <div class="card-desc">2015-2024趋势 · 相关性热力图 · 随机森林重要性</div>
    </a>
    <a class="card" href="/3_一键分析" target="_self">
        <div class="card-title">📊 今日快报</div>
        <div class="card-desc">平均AQI · 等级分布 · 首要污染物统计</div>
    </a>
    <a class="card" href="/4_气象预警" target="_self">
        <div class="card-title">🚨 气象预警</div>
        <div class="card-desc">预警总数 · 等级分类 · 按省份筛选</div>
    </a>
</div>
""", unsafe_allow_html=True)

st.markdown("---")
st.markdown("""
<div class="footer">
    © 2026 刘宇博 · 江毅 · 张睿 ｜ 大数据与人工智能导论课程项目
</div>
""", unsafe_allow_html=True)
