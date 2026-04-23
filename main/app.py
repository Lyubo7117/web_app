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

    /* ---- 列等宽居中 ---- */
    div[data-testid="column"] {
        flex: 1 1 0% !important;
        min-width: 0 !important;
        display: flex;
        flex-direction: column;
        align-items: center;
    }

    /* ---- 纯 HTML 卡片网格 ---- */
    .card-grid {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 20px;
        margin: 20px 0 10px 0;
    }
    @media (max-width: 768px) {
        .card-grid { grid-template-columns: repeat(2, 1fr); }
    }
    @media (max-width: 480px) {
        .card-grid { grid-template-columns: 1fr; }
    }

    .nav-card {
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        min-height: 140px;
        padding: 24px 16px;
        background: rgba(255, 255, 255, 0.6);
        backdrop-filter: blur(4px);
        border-radius: 24px;
        border: 1px solid rgba(255, 255, 255, 0.8);
        box-shadow: 0 8px 16px rgba(0, 40, 80, 0.1);
        transition: all 0.3s ease;
        text-decoration: none !important;
        color: #1a365d !important;
        box-sizing: border-box;
        cursor: pointer;
    }
    .nav-card:hover {
        transform: translateY(-6px);
        box-shadow: 0 16px 24px rgba(27, 79, 140, 0.2);
        background: rgba(255, 255, 255, 0.8);
        border-color: #ffffff;
        text-decoration: none !important;
        color: #0a2540 !important;
    }
    .nav-card .card-icon {
        font-size: 2.4rem;
        margin-bottom: 10px;
    }
    .nav-card .card-title {
        font-size: 1.3rem;
        font-weight: 700;
        color: #0a2540;
        margin-bottom: 8px;
    }
    .nav-card .card-desc-text {
        font-size: 0.85rem;
        color: #4a5568;
        font-weight: 400;
        text-align: center;
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

# ==================== 功能卡片 ====================
# 方案：st.page_link 渲染在每列中，然后用 JS 获取其 href 并注入到 HTML 卡片
# st.html() 支持 <script>，且与主页面共享 DOM
import streamlit.components.v1 as components

# 先渲染 st.page_link（隐藏），获取正确路由
col1, col2, col3, col4 = st.columns(4)
with col1:
    pl1 = st.page_link("pages/1_实时监测.py", label="", icon="")
with col2:
    pl2 = st.page_link("pages/2_历史分析.py", label="", icon="")
with col3:
    pl3 = st.page_link("pages/3_一键分析.py", label="", icon="")
with col4:
    pl4 = st.page_link("pages/4_气象预警.py", label="", icon="")

# HTML 卡片（纯视觉）
st.markdown("""
<div class="card-grid">
    <div class="nav-card" data-idx="0">
        <span class="card-icon">📍</span>
        <span class="card-title">实时监测</span>
        <span class="card-desc-text">最新AQI排名<br>全国热力图 · 实时更新</span>
    </div>
    <div class="nav-card" data-idx="1">
        <span class="card-icon">📈</span>
        <span class="card-title">历史分析</span>
        <span class="card-desc-text">2015-2024趋势<br>相关性热力图 · 驱动因素</span>
    </div>
    <div class="nav-card" data-idx="2">
        <span class="card-icon">📊</span>
        <span class="card-title">今日快报</span>
        <span class="card-desc-text">平均AQI · 等级分布<br>首要污染物统计</span>
    </div>
    <div class="nav-card" data-idx="3">
        <span class="card-icon">🚨</span>
        <span class="card-title">气象预警</span>
        <span class="card-desc-text">预警总数 · 等级分类<br>按省份筛选</span>
    </div>
</div>
""", unsafe_allow_html=True)

# 用 st.html 注入 JS（点击卡片 → 找到对应的 st.page_link 链接 → 触发跳转）
st.html("""
<script>
function setupCardNav() {
    const cards = document.querySelectorAll('.nav-card');
    // 找到所有 st.page_link 渲染的链接（按顺序对应）
    const pageLinks = document.querySelectorAll('[data-testid="stPageLink"] a, [data-testid="stPageLink"] button');
    
    cards.forEach(card => {
        const idx = parseInt(card.dataset.idx);
        if (idx < pageLinks.length) {
            card.style.cursor = 'pointer';
            card.addEventListener('click', () => {
                const link = pageLinks[idx];
                if (link.tagName === 'A') {
                    window.location.href = link.href;
                } else if (link.tagName === 'BUTTON') {
                    link.click();
                }
            });
        }
    });
}

// 等待 Streamlit 渲染完成
setTimeout(setupCardNav, 1000);
setTimeout(setupCardNav, 2000);
setTimeout(setupCardNav, 3000);
</script>
""")

# 隐藏 st.page_link 和空列
st.markdown("""
<style>
    [data-testid="stPageLink"] {
        visibility: hidden !important;
        height: 0 !important;
        overflow: hidden !important;
        margin: 0 !important;
        padding: 0 !important;
        border: none !important;
        min-height: 0 !important;
        max-height: 0 !important;
        pointer-events: none !important;
    }
</style>
""", unsafe_allow_html=True)

st.markdown("---")
st.markdown("""
<div class="footer">
    © 2026 刘宇博 · 江毅 · 张睿 ｜ 大数据与人工智能导论课程项目
</div>
""", unsafe_allow_html=True)
