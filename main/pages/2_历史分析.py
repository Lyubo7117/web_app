"""
2_历史分析.py
Streamlit 多页面应用 — 历史趋势与驱动因素分析页面

功能：
- 展示十年空气质量变化趋势图
- 展示规划因素相关性热力图
- 展示随机森林特征重要性图
- 显示核心分析结论
"""

import streamlit as st
import os

# 图片目录：相对于本文件，向上两级到项目根目录，再进入 static/
STATIC_DIR = os.path.join(os.path.dirname(__file__), '..', 'static')


# ==============================
# 自定义侧边栏导航
# ==============================
with st.sidebar:
    st.markdown("### 🌏 导航")
    if st.button("🏠 首页", key="sidebar_home", use_container_width=True):
        st.switch_page("app.py")
    st.markdown("---")
    if st.button("📍 实时监测", key="sidebar_realtime", use_container_width=True):
        st.switch_page("pages/1_实时监测.py")
    if st.button("📈 历史分析", key="sidebar_history", use_container_width=True):
        st.switch_page("pages/2_历史分析.py")
    if st.button("📊 今日快报", key="sidebar_report", use_container_width=True):
        st.switch_page("pages/3_今日快报.py")
    if st.button("🚨 气象预警", key="sidebar_warning", use_container_width=True):
        st.switch_page("pages/4_气象预警.py")

# ==============================
# 蓝色主题 CSS
# ==============================
st.markdown("""
<style>
    .stApp {
        background: linear-gradient(135deg, #f0f8ff 0%, #e6f2ff 100%);
    }
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1a365d 0%, #0f2440 100%);
    }
    /* 隐藏原生侧边栏导航（文件名显示） */
    [data-testid="stSidebarNav"] {
        display: none !important;
    }
    section[data-testid="stSidebar"] * {
        color: #ffffff !important;
    }
    section[data-testid="stSidebar"] button {
        background: #2b6cb0 !important;
        color: white !important;
        border-radius: 8px !important;
    }
    h1, h2, h3 {
        color: #0a2540 !important;
        font-weight: 600 !important;
    }
    .stImage {
        border-radius: 12px;
        box-shadow: 0 4px 12px rgba(0, 49, 102, 0.1);
        border: 1px solid #cce0ff;
    }
    .stAlert {
        border-radius: 10px;
        border-left: 4px solid #2b6cb0;
    }
</style>
""", unsafe_allow_html=True)


# ==============================
# 页面标题
# ==============================
st.title("📈 历史趋势与驱动因素分析（2015-2024）")


# ==============================
# 一、十年空气质量变化趋势
# ==============================
st.header("一、十年空气质量变化趋势")

st.markdown("""
下图展示了 2015—2024 年 34 个省会城市 AQI 的年度变化趋势。
红色粗线为全国年均均值，其余半透明线条为各城市的独立走势。
""")

img1 = os.path.join(STATIC_DIR, '01_趋势总览图.png')
if os.path.exists(img1):
    st.image(img1, use_container_width=True)
else:
    st.warning(f"图片未找到：{img1}")


# ==============================
# 二、规划因素相关性分析
# ==============================
st.header("二、规划因素相关性分析")

st.markdown("""
下图为空气质量指标（AQI、PM2.5）与城市规划因素（建成区面积、人口密度、
绿地覆盖率、第二产业占比）之间的 Pearson 相关系数矩阵。
""")

img2 = os.path.join(STATIC_DIR, '02_相关性热力图.png')
if os.path.exists(img2):
    st.image(img2, use_container_width=True)
else:
    st.warning(f"图片未找到：{img2}")


# ==============================
# 三、随机森林驱动因素重要性
# ==============================
st.header("三、随机森林驱动因素重要性")

st.markdown("""
基于随机森林回归模型，对影响 AQI 的各规划因素进行重要性排序。
""")

img3 = os.path.join(STATIC_DIR, '03_随机森林重要性.png')
if os.path.exists(img3):
    st.image(img3, use_container_width=True)
else:
    st.warning(f"图片未找到：{img3}")


# ==============================
# 四、核心结论
# ==============================
st.header("四、核心结论")

st.success("""
基于 2015—2024 年 34 个省会城市数据，随机森林模型显示建成区面积和人口密度
是影响 AQI 最重要的规划因素。绿地覆盖率与 AQI 呈显著负相关，建议在国土空间
规划中加强生态空间保护和通风廊道建设。
""")


# ==============================
# 制作人信息
# ==============================
st.markdown("---")
st.caption("👨‍💻 制作人：刘宇博 · 江毅 · 张睿 ｜ 大数据与人工智能导论课程项目")
