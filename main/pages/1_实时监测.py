"""
1_实时监测.py
Streamlit 多页面应用 - 实时监测页面

功能：
- 优先调用实时 API 获取最新 AQI 数据，失败时 fallback 到本地 Excel
- 展示最新 AQI 排名（最佳/最差 Top 10）
- folium 全国污染热力分布地图
- 手动刷新按钮
"""

import streamlit as st
import folium
from streamlit_folium import st_folium
import pandas as pd
import sys
import os

# 确保可以导入 utils
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from utils.realtime_aqi import fetch_realtime_aqi
from utils.excel_parser import get_latest_aqi_snapshot
from utils.city_coords import CITY_COORDS


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
    div[data-testid="stDataFrame"] th {
        background: #1e4d8c !important;
        color: white !important;
        font-weight: 600 !important;
    }
    div[data-testid="stDataFrame"] td {
        background: white !important;
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
</style>
""", unsafe_allow_html=True)


# ==============================
# AQI 等级颜色映射
# ==============================
def aqi_color(value):
    if value <= 50:    return '#00e400'
    elif value <= 100: return '#ffff00'
    elif value <= 150: return '#ff7e00'
    elif value <= 200: return '#ff0000'
    else:              return '#99004c'


def aqi_level_text(value):
    if value <= 50:    return '优'
    elif value <= 100: return '良'
    elif value <= 150: return '轻度污染'
    elif value <= 200: return '中度污染'
    else:              return '重度污染'


# ==============================
# 手动刷新按钮
# ==============================
if 'last_refresh' not in st.session_state:
    st.session_state.last_refresh = 0

if st.button("🔄 手动刷新数据"):
    st.cache_data.clear()
    st.session_state.last_refresh += 1
    st.rerun()


# ==============================
# 加载数据 — 优先实时 API，fallback 到 Excel
# ==============================
@st.cache_data(ttl=300)
def _load_excel_fallback():
    """加载爬虫 Excel 数据（fallback）"""
    return get_latest_aqi_snapshot()


# 优先使用实时 API（双数据源自动切换）
with st.spinner("📡 正在获取最新空气质量数据..."):
    df, update_time, debug_info, data_source = fetch_realtime_aqi(cache_ttl=600)

    if data_source == "中国天气网":
        data_source_label = "中国天气网（实时）"
    elif data_source == "Open-Meteo":
        data_source_label = "Open-Meteo（US EPA 标准）"
    else:
        data_source_label = "未知"

    # 实时 API 失败时 fallback 到 Excel
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

city_count = len(df)


# ==============================
# 空数据判断
# ==============================
if df.empty:
    st.warning("暂无实时数据，请稍后重试...")
    st.stop()


# ==============================
# 数据信息栏
# ==============================
st.markdown("#### 📡 数据信息")
col_a, col_b, col_c = st.columns(3)
col_a.metric("数据来源", data_source_label)
col_b.metric("更新时间", update_time)
col_c.metric("覆盖城市", f"{city_count} 个")


# ==============================
# AQI 排名（最佳 / 最差 Top 10）
# ==============================
st.subheader("🏆 城市AQI排名")

if 'aqi' not in df.columns:
    st.error("数据中缺少 'aqi' 列，无法排序。")
    st.stop()

df_sorted = df.dropna(subset=['aqi']).sort_values('aqi', ascending=False)

left_col, right_col = st.columns(2)

with left_col:
    st.markdown("#### 🟢 空气最佳 Top 10")
    best = df_sorted.tail(10).iloc[::-1]
    display_cols = [c for c in ['city_name', 'aqi', 'level'] if c in best.columns]
    best_display = best[display_cols].copy()
    best_display.columns = ['城市', 'AQI', '等级'][:len(display_cols)]
    best_display.reset_index(drop=True, inplace=True)
    best_display.index += 1
    st.dataframe(best_display, use_container_width=True, height=360)

with right_col:
    st.markdown("#### 🔴 空气最差 Top 10")
    worst = df_sorted.head(10)
    display_cols = [c for c in ['city_name', 'aqi', 'level'] if c in worst.columns]
    worst_display = worst[display_cols].copy()
    worst_display.columns = ['城市', 'AQI', '等级'][:len(display_cols)]
    worst_display.reset_index(drop=True, inplace=True)
    worst_display.index += 1
    st.dataframe(worst_display, use_container_width=True, height=360)


# ==============================
# folium 全国污染热力分布地图
# ==============================
st.subheader("🗺️ 全国空气质量分布")

df_map = df.copy()
df_map = df_map[df_map['aqi'].notna()]

if df_map.empty:
    st.warning("暂无有效的AQI数据，无法生成热力图")
    st.stop()

m = folium.Map(location=[35, 110], zoom_start=4, tiles='CartoDB positron')

for _, row in df_map.iterrows():
    try:
        city = str(row.get('city_name', ''))
        aqi_val = float(row.get('aqi', 0))
        lat = float(row.get('lat', 0))
        lon = float(row.get('lon', 0))

        # 如果数据中没有经纬度，从字典补充
        if lat == 0.0 and lon == 0.0 and city in CITY_COORDS:
            lat, lon = CITY_COORDS[city]

        if lat == 0.0 and lon == 0.0:
            continue
    except (ValueError, TypeError):
        continue

    radius = aqi_val / 5 + 5
    color = aqi_color(aqi_val)
    level = aqi_level_text(aqi_val)

    folium.CircleMarker(
        location=[lat, lon],
        radius=radius,
        color=color,
        fill=True,
        fill_color=color,
        fill_opacity=0.6,
        popup=folium.Popup(
            f"<b>{city}</b><br>AQI: {int(aqi_val)} ({level})",
            max_width=200
        ),
        tooltip=f"{city}: AQI {int(aqi_val)}",
    ).add_to(m)

st_folium(m, width=1100, height=550)


# ==============================
# 颜色图例
# ==============================
st.markdown("""
<style>
.legend-container {
    display: flex; gap: 24px; flex-wrap: wrap;
    justify-content: center; margin-top: 8px;
}
.legend-item { display: flex; align-items: center; gap: 6px; font-size: 14px; }
.legend-dot { width: 16px; height: 16px; border-radius: 50%; border: 1px solid #ccc; }
</style>
<div class="legend-container">
    <div class="legend-item"><div class="legend-dot" style="background:#00e400"></div> 优 (0-50)</div>
    <div class="legend-item"><div class="legend-dot" style="background:#ffff00"></div> 良 (51-100)</div>
    <div class="legend-item"><div class="legend-dot" style="background:#ff7e00"></div> 轻度污染 (101-150)</div>
    <div class="legend-item"><div class="legend-dot" style="background:#ff0000"></div> 中度污染 (151-200)</div>
    <div class="legend-item"><div class="legend-dot" style="background:#99004c"></div> 重度污染 (>200)</div>
</div>
""", unsafe_allow_html=True)


# ==============================
# 制作人信息
# ==============================
st.markdown("---")
st.caption("👨‍💻 制作人：刘宇博 · 江毅 · 张睿 ｜ 大数据与人工智能导论课程项目")
