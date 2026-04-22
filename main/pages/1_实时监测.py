"""
1_实时监测.py
Streamlit 多页面应用 — 实时监测页面

功能：
- 展示最新 AQI 排名（最佳/最差 Top 10）
- folium 全国污染热力分布地图
- 手动刷新按钮
"""

import streamlit as st
import folium
from streamlit_folium import st_folium
import pandas as pd

# 导入数据加载工具
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from utils.data_loader import load_latest_data


# ==============================
# AQI 等级颜色映射
# ==============================
def aqi_color(value: float) -> str:
    """
    根据 AQI 数值返回对应的 HTML 颜色代码。
    参考国标 GB 3095-2012 空气质量等级划分。
    """
    if value <= 50:
        return '#00e400'   # 优 — 绿色
    elif value <= 100:
        return '#ffff00'   # 良 — 黄色
    elif value <= 150:
        return '#ff7e00'   # 轻度污染 — 橙色
    elif value <= 200:
        return '#ff0000'   # 中度污染 — 红色
    else:
        return '#99004c'   # 重度及以上 — 紫色


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
    st.cache_data.clear()          # 清除所有缓存数据
    st.session_state.last_refresh += 1
    st.rerun()                     # 重新加载页面


# ==============================
# 加载数据
# ==============================
@st.cache_data(ttl=300)  # 缓存 5 分钟，手动刷新时会被清除
def _load_data():
    return load_latest_data()


df = _load_data()


# ==============================
# 空数据判断
# ==============================
if df.empty:
    st.warning("暂无实时数据，请等待成员A采集...")
    st.stop()


# ==============================
# 数据更新时间
# ==============================
update_time = df['update_time'].max() if 'update_time' in df.columns else '未知'
st.markdown(f"**📡 数据更新时间：** {update_time}")


# ==============================
# AQI 排名（最佳 / 最差 Top 10）
# ==============================
st.subheader("🏆 城市AQI排名")

df_sorted = df.sort_values('aqi', ascending=False)

left_col, right_col = st.columns(2)

with left_col:
    st.markdown("#### 🟢 空气最佳 Top 10")
    best = df_sorted.tail(10).iloc[::-1][['city_name', 'aqi', 'level']]
    best.columns = ['城市', 'AQI', '等级']
    best.reset_index(drop=True, inplace=True)
    best.index += 1
    st.dataframe(best, use_container_width=True, height=360)

with right_col:
    st.markdown("#### 🔴 空气最差 Top 10")
    worst = df_sorted.head(10)[['city_name', 'aqi', 'level']]
    worst.columns = ['城市', 'AQI', '等级']
    worst.reset_index(drop=True, inplace=True)
    worst.index += 1
    st.dataframe(worst, use_container_width=True, height=360)


# ==============================
# folium 全国污染热力分布地图
# ==============================
st.subheader("🗺️ 全国空气质量分布")

# 创建底图，中心点设在中国中部，缩放级别 4（全国视野）
m = folium.Map(location=[35, 110], zoom_start=4, tiles='CartoDB positron')

# 为每个城市添加 CircleMarker
for _, row in df.iterrows():
    try:
        lat = float(row.get('lat', 0))
        lon = float(row.get('lon', 0))
        aqi_val = float(row.get('aqi', 0))
        city = str(row.get('city_name', ''))
    except (ValueError, TypeError):
        continue

    # 半径与 AQI 成正比：半径 = aqi / 10 + 2
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
        popup=folium.Popup(f"<b>{city}</b><br>AQI: {int(aqi_val)} ({level})", max_width=200),
        tooltip=f"{city}: AQI {int(aqi_val)}",
    ).add_to(m)

# 使用 streamlit-folium 嵌入地图
st_folium(m, width=1100, height=550)


# ==============================
# 颜色图例
# ==============================
st.markdown("""
<style>
.legend-container {
    display: flex;
    gap: 24px;
    flex-wrap: wrap;
    justify-content: center;
    margin-top: 8px;
}
.legend-item {
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: 14px;
}
.legend-dot {
    width: 16px;
    height: 16px;
    border-radius: 50%;
    border: 1px solid #ccc;
}
</style>
<div class="legend-container">
    <div class="legend-item"><div class="legend-dot" style="background:#00e400"></div> 优 (0-50)</div>
    <div class="legend-item"><div class="legend-dot" style="background:#ffff00"></div> 良 (51-100)</div>
    <div class="legend-item"><div class="legend-dot" style="background:#ff7e00"></div> 轻度污染 (101-150)</div>
    <div class="legend-item"><div class="legend-dot" style="background:#ff0000"></div> 中度污染 (151-200)</div>
    <div class="legend-item"><div class="legend-dot" style="background:#99004c"></div> 重度污染 (>200)</div>
</div>
""", unsafe_allow_html=True)
