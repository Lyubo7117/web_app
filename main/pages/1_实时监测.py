"""
1_实时监测.py
Streamlit 多页面应用 — 实时监测页面

功能：
- 根据侧边栏数据源选择，加载爬虫数据或用户上传的 Excel
- 展示最新 AQI 排名（最佳/最差 Top 10）
- folium 全国污染热力分布地图
- 手动刷新按钮
- 调试信息面板（可在排查问题后关闭）
"""

import streamlit as st
import folium
from streamlit_folium import st_folium
import pandas as pd
import sys
import os

# 确保可以导入 utils
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from utils.excel_parser import get_latest_aqi_snapshot, parse_uploaded_excel
from utils.city_coords import CITY_COORDS


# ==============================
# AQI 等级颜色映射
# ==============================
def aqi_color(value: float) -> str:
    """根据 AQI 数值返回 HTML 颜色代码（国标 GB 3095）。"""
    if value <= 50:
        return '#00e400'
    elif value <= 100:
        return '#ffff00'
    elif value <= 150:
        return '#ff7e00'
    elif value <= 200:
        return '#ff0000'
    else:
        return '#99004c'


def aqi_level_text(value: float) -> str:
    """返回 AQI 对应的中文等级文字。"""
    if value <= 50:
        return '优'
    elif value <= 100:
        return '良'
    elif value <= 150:
        return '轻度污染'
    elif value <= 200:
        return '中度污染'
    else:
        return '重度污染'


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
# 加载数据 — 根据侧边栏选择切换数据源
# ==============================
@st.cache_data(ttl=300)
def _load_crawler_data():
    """加载爬虫最新批次数据，返回 (df, run_dir, debug_info)。"""
    return get_latest_aqi_snapshot()


def _load_uploaded_data(uploaded_file):
    """解析用户上传的 Excel（不缓存，每次重新解析）。"""
    df = parse_uploaded_excel(uploaded_file)
    debug = ["数据来源：用户上传的 Excel 文件", f"解析到 {len(df)} 条记录"]
    return df, '', debug


# 从 session_state 获取侧边栏选择的数据源
data_source = st.session_state.get('data_source_select', '使用爬虫最新数据')
uploaded_file = st.session_state.get('uploaded_file', None)

if data_source == '手动上传Excel文件' and uploaded_file is not None:
    df, run_dir, debug_info = _load_uploaded_data(uploaded_file)
else:
    df, run_dir, debug_info = _load_crawler_data()


# ==============================
# 调试信息面板（可折叠）
# ==============================
with st.expander("🔍 调试信息（排查用）", expanded=False):
    for line in debug_info:
        st.text(line)


# ==============================
# 空数据判断
# ==============================
if df.empty:
    st.warning("暂无实时数据，请等待爬虫采集或上传 Excel 文件...")
    st.info(f"数据目录：{run_dir}" if run_dir else "未找到数据目录，请确认爬虫已运行并生成数据。")
    st.stop()


# ==============================
# 数据更新时间
# ==============================
if 'update_time' in df.columns:
    update_time = df['update_time'].max()
else:
    update_time = '未知'
st.markdown(f"**📡 数据来源：** {data_source}")
st.markdown(f"**📡 数据时间：** {update_time}")


# ==============================
# AQI 排名（最佳 / 最差 Top 10）
# ==============================
st.subheader("🏆 城市AQI排名")

# 确保有 aqi 列
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

m = folium.Map(location=[35, 110], zoom_start=4, tiles='CartoDB positron')

for _, row in df.iterrows():
    try:
        city = str(row.get('city_name', ''))
        aqi_val = float(row.get('aqi', 0))
        lat = float(row.get('lat', 0))
        lon = float(row.get('lon', 0))

        # 如果 Excel 中没有经纬度，从字典补充
        if lat == 0.0 and lon == 0.0 and city in CITY_COORDS:
            lat, lon = CITY_COORDS[city]

        if lat == 0.0 and lon == 0.0:
            continue  # 跳过没有坐标的城市
    except (ValueError, TypeError):
        continue

    radius = aqi_val / 10 + 2
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
