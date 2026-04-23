"""
3_一键分析.py
Streamlit 多页面应用 — 今日空气质量快报（基于实时数据）

功能：
- 从爬虫最新数据生成今日 AQI 快报
- 关键指标：全国平均 AQI、最优/最差城市
- AQI 等级分布饼图（plotly）
- 首要污染物频次条形图（plotly）
- Top 5 最佳/最差城市表格
- 刷新按钮
"""

import streamlit as st
import sys
import os
import re
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# 确保可以导入 utils
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from utils.realtime_aqi import fetch_realtime_aqi
from utils.excel_parser import get_latest_aqi_snapshot

st.set_page_config(
    page_title="今日快报",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)


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
    div[data-testid="stMetric"] {
        background: white;
        border-radius: 12px;
        padding: 16px;
        box-shadow: 0 2px 8px rgba(0, 49, 102, 0.1);
        border: 1px solid #cce0ff;
    }
    div[data-testid="stDataFrame"] {
        border-radius: 10px;
        overflow: hidden;
        border: 1px solid #cce0ff;
    }
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
    .stAlert {
        border-radius: 10px;
        border-left: 4px solid #2b6cb0;
    }
    /* 表格和文字居中 */
    div[data-testid="stMetric"] {
        text-align: center;
    }
    div[data-testid="stMetric"] label {
        text-align: center;
    }
    div[data-testid="stMetric"] [data-testid="stMetricValue"] {
        text-align: center;
    }
    div[data-testid="stDataFrame"] {
        margin-left: auto;
        margin-right: auto;
    }
    .stMarkdown, .stCaption, .stInfo, .stWarning, .stSuccess {
        text-align: center;
    }
    h1, h2, h3, h4 {
        text-align: center !important;
    }
    p, .stMarkdown p {
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)


# ==============================
# AQI 等级配色
# ==============================
LEVEL_MAP = {
    '优': ('#00e400', '优 (0-50)'),
    '良': ('#ffff00', '良 (51-100)'),
    '轻度污染': ('#ff7e00', '轻度污染 (101-150)'),
    '中度污染': ('#ff0000', '中度污染 (151-200)'),
    '重度污染': ('#99004c', '重度污染 (>200)'),
    '严重污染': ('#7e0023', '严重污染 (>300)'),
}

# 标准 AQI 等级函数
def aqi_to_level(val):
    if val <= 50: return '优'
    elif val <= 100: return '良'
    elif val <= 150: return '轻度污染'
    elif val <= 200: return '中度污染'
    elif val <= 300: return '重度污染'
    else: return '严重污染'


# ==============================
# 页面标题
# ==============================
st.title("📊 今日快报")
st.markdown("自动加载最新爬取数据，生成全国空气质量概览。")
st.markdown("---")


# ==============================
# 加载数据 — 优先实时 API，fallback 到 Excel
# ==============================
@st.cache_data(ttl=600)
def _load_excel_fallback():
    """加载爬虫 Excel 数据（fallback）"""
    return get_latest_aqi_snapshot()

if st.button("🔄 刷新数据"):
    st.cache_data.clear()
    st.rerun()

with st.spinner("📡 正在获取最新空气质量数据..."):
    df, update_time, debug_info, data_source = fetch_realtime_aqi(cache_ttl=600)

    if data_source == "中国天气网":
        data_source_label = "中国天气网（实时）"
    elif data_source == "Open-Meteo":
        data_source_label = "Open-Meteo（US EPA 标准）"
    else:
        data_source_label = "未知"

    if df.empty:
        st.info("实时 API 暂不可用，正在加载本地缓存数据...")
        df, run_dir, debug_info = _load_excel_fallback()
        data_source_label = "本地缓存数据"
        update_time = '未知'

        if not df.empty:
            for col_name in ['datetime', 'update_time', '数据时间']:
                if col_name in df.columns:
                    try:
                        latest_dt = pd.to_datetime(df[col_name]).max()
                        if pd.notna(latest_dt):
                            update_time = latest_dt.strftime('%Y-%m-%d %H:%M')
                    except Exception:
                        pass
                    break




# ==============================
# 空数据判断
# ==============================
if df.empty:
    st.warning("暂无实时数据，等待爬虫更新...")
    st.info(f"数据目录：{run_dir}" if run_dir else "未找到数据目录。")
    st.stop()


# ==============================
# 数据准备
# ==============================
# 确保 aqi 列为数值
df['aqi'] = pd.to_numeric(df['aqi'], errors='coerce')
df_valid = df.dropna(subset=['aqi']).copy()

# 确保 level 列存在
if 'level' not in df_valid.columns:
    df_valid['level'] = df_valid['aqi'].apply(aqi_to_level)

city_count = len(df_valid)


# ==============================
# 解析更新时间
# ==============================
# update_time 已在上方数据加载时设置


# ==============================
# 一、数据来源 & 关键指标
# ==============================
st.subheader("📡 数据概览")
st.markdown(f"数据来源：**{data_source_label}** | 更新时间：**{update_time}** | 覆盖城市：**{city_count}** 个")

avg_aqi = df_valid['aqi'].mean()
best_row = df_valid.loc[df_valid['aqi'].idxmin()]
worst_row = df_valid.loc[df_valid['aqi'].idxmax()]

best_city = best_row.get('city_name', '未知')
best_aqi = best_row.get('aqi', 0)
best_level = best_row.get('level', aqi_to_level(best_aqi))

worst_city = worst_row.get('city_name', '未知')
worst_aqi = worst_row.get('aqi', 0)
worst_level = worst_row.get('level', aqi_to_level(worst_aqi))

m1, m2, m3 = st.columns(3)
m1.metric("🇨🇳 全国平均 AQI", f"{avg_aqi:.0f}", delta=f"{'↓' if avg_aqi <= 100 else '↑'} {'良好' if avg_aqi <= 100 else '需关注'}")
m2.metric("🌿 空气最优城市", f"{best_city}", delta=f"AQI {int(best_aqi)} ({best_level})")
m3.metric("⚠️ 空气最差城市", f"{worst_city}", delta=f"AQI {int(worst_aqi)} ({worst_level})")

st.markdown("---")


# ==============================
# 二、AQI 等级城市数量分布（饼图）
# ==============================
st.subheader("🥧 AQI 等级分布")

level_counts = df_valid['level'].value_counts().reset_index()
level_counts.columns = ['等级', '城市数']

# 确保颜色和排序一致
level_order = ['优', '良', '轻度污染', '中度污染', '重度污染', '严重污染']
level_counts['排序'] = level_counts['等级'].apply(lambda x: level_order.index(x) if x in level_order else 99)
level_counts = level_counts.sort_values('排序')

colors = []
labels = []
for _, row in level_counts.iterrows():
    lv = row['等级']
    if lv in LEVEL_MAP:
        colors.append(LEVEL_MAP[lv][0])
        labels.append(LEVEL_MAP[lv][1])
    else:
        colors.append('#999999')
        labels.append(lv)

fig_pie = px.pie(
    level_counts, values='城市数', names=labels,
    color_discrete_sequence=colors,
    hole=0.4,
)
fig_pie.update_layout(
    margin=dict(t=20, b=20, l=20, r=20),
    height=420,
    showlegend=True,
    legend=dict(orientation='h', yanchor='bottom', y=-0.05),
    font=dict(size=13),
)
fig_pie.update_traces(textposition='inside', textinfo='percent+label')

st.plotly_chart(fig_pie, use_container_width=True)

st.markdown("---")


# ==============================
# 三、首要污染物频次条形图
# ==============================
st.subheader("🏭 首要污染物统计")

pollutant_col = None
for col_name in ['dominant_pollutant', 'primary_pollutant', 'pollutant', '首要污染物']:
    if col_name in df_valid.columns:
        pollutant_col = col_name
        break

if pollutant_col:
    # 过滤无效值
    pollutant_df = df_valid[df_valid[pollutant_col].notna()].copy()
    pollutant_df[pollutant_col] = pollutant_df[pollutant_col].astype(str).str.strip()

    # 过滤 "优" / "无" / "-" 等非污染物值
    exclude_vals = {'优', '无', '-', '—', 'nan', '', 'None', 'NaN'}
    pollutant_df = pollutant_df[~pollutant_df[pollutant_col].isin(exclude_vals)]

    if not pollutant_df.empty:
        poll_counts = pollutant_df[pollutant_col].value_counts().reset_index()
        poll_counts.columns = ['污染物', '频次']
        poll_counts = poll_counts.sort_values('频次', ascending=True)

        fig_bar = px.bar(
            poll_counts, x='频次', y='污染物',
            orientation='h',
            color='频次',
            color_continuous_scale='Reds',
            text='频次',
        )
        fig_bar.update_layout(
            margin=dict(t=20, b=20, l=80, r=20),
            height=max(300, len(poll_counts) * 40 + 60),
            xaxis_title='城市数量',
            yaxis_title='',
            showlegend=False,
            font=dict(size=13),
        )
        fig_bar.update_traces(textposition='outside')

        st.plotly_chart(fig_bar, use_container_width=True)
    else:
        st.info('当前所有城市空气质量均达到"优"等级，无首要污染物。')
else:
    st.info("数据中未找到首要污染物列，无法生成统计图。")

st.markdown("---")


# ==============================
# 四、AQI Top 5 最佳 & 最差城市表格
# ==============================
st.subheader("🏆 城市AQI排行榜")

left_col, right_col = st.columns(2)

with left_col:
    st.markdown("#### 🟢 空气最佳 Top 5")
    best5 = df_valid.nsmallest(5, 'aqi')
    display_cols = [c for c in ['city_name', 'aqi', 'level', 'dominant_pollutant'] if c in best5.columns]
    col_labels = ['城市', 'AQI', '等级', '首要污染物'][:len(display_cols)]
    best5_display = best5[display_cols].copy()
    best5_display.columns = col_labels
    best5_display.reset_index(drop=True, inplace=True)
    best5_display.index += 1
    st.dataframe(best5_display, use_container_width=True, height=240)

with right_col:
    st.markdown("#### 🔴 空气最差 Top 5")
    worst5 = df_valid.nlargest(5, 'aqi')
    display_cols = [c for c in ['city_name', 'aqi', 'level', 'dominant_pollutant'] if c in worst5.columns]
    col_labels = ['城市', 'AQI', '等级', '首要污染物'][:len(display_cols)]
    worst5_display = worst5[display_cols].copy()
    worst5_display.columns = col_labels
    worst5_display.reset_index(drop=True, inplace=True)
    worst5_display.index += 1
    st.dataframe(worst5_display, use_container_width=True, height=240)


st.markdown("---")
st.info("💡 本报告基于中国天气网实时爬取数据自动生成，每日自动更新。历史深度分析请查看「历史分析」页面。")


# ==============================
# 制作人信息
# ==============================
st.markdown("---")
st.caption("👨‍💻 制作人：刘宇博 · 江毅 · 张睿 ｜ 大数据与人工智能导论课程项目")
