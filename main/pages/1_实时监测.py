# -*- coding: utf-8 -*-
"""
1_实时监测.py
Streamlit 多页面应用 - 实时监测页面

功能：
- 优先调用实时 API 获取最新 AQI 数据（双数据源自动切换）
- 展示最新 AQI 排名（最佳/最差 Top 10）
- folium 全国污染热力分布地图（高德中文底图 + 九段线）
- 右下角 AQI 图例（独立浮动层）
- 手动刷新按钮
"""

import streamlit as st
import folium
from streamlit_folium import st_folium
import pandas as pd
import sys
import os
import json
import urllib.request

# 确保可以导入 utils
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from utils.realtime_aqi import fetch_realtime_aqi          # [修1] 实时数据源
from utils.excel_parser import get_latest_aqi_snapshot       # [修2] 正确的函数名（非 get_latest_snapshot）
from utils.city_coords import CITY_COORDS                    # [修3] 城市坐标字典（非 get_city_coords）


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
    if st.button("🚨 气象预警", key="sidebar_warning", use_container_width=True):
        st.switch_page("pages/4_气象预警.py")
    if st.button("📊 今日快报", key="sidebar_report", use_container_width=True):
        st.switch_page("pages/3_今日快报.py")
    if st.button("📈 历史分析", key="sidebar_history", use_container_width=True):
        st.switch_page("pages/2_历史分析.py")


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
    /* 隐藏原生侧边栏导航 */
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
    /* 表格和文字居中 */
    div[data-testid="stMetric"] { text-align: center; }
    div[data-testid="stDataFrame"] { margin-left: auto; margin-right: auto; }
    div[data-testid="stDataFrame"] td,
    div[data-testid="stDataFrame"] th {
        text-align: center !important;
    }
    .stMarkdown, .stCaption, .stInfo, .stWarning, .stSuccess {
        text-align: center;
    }
    h1, h2, h3, h4 { text-align: center !important; }
    p, .stMarkdown p { text-align: center; }

    /* 图例浮动层样式 */
    .aqi-legend-float {
        position: fixed !important;
        bottom: 100px !important;   /* 上移到可见区域 */
        right: 28px !important;
        width: 195px;
        border: 2px solid #1a365d;
        z-index: 99999 !important;
        font-size: 13px;
        background-color: rgba(255,255,255,0.94);
        border-radius: 10px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.2);
        padding: 12px 14px;
        line-height: 1.9;
    }
    /* 地图容器：消除多余留白 */
    div[data-testid="stFolium"] {
        padding: 0 !important;
        margin: 0 !important;
        background: transparent !important;
    }
    div[data-testid="stFolium"] > iframe {
        display: block;
        border-radius: 8px;
    }
    .aqi-legend-float b {
        display: block;
        margin-bottom: 4px;
        color: #1a365d;
        font-size: 14px;
    }
    .aqi-legend-float .lg-item i {
        display: inline-block;
        width: 20px; height: 14px;
        border-radius: 3px;
        margin-right: 6px;
        vertical-align: middle;
        border: 1px solid rgba(0,0,0,0.15);
    }
</style>
""", unsafe_allow_html=True)


# ==============================
# AQI 等级颜色映射
# ==============================
def aqi_color(value):
    try:
        v = float(value)
    except (ValueError, TypeError):
        return '#cccccc'
    if v <= 50:    return '#00e400'
    elif v <= 100: return '#ffff00'
    elif v <= 150: return '#ff7e00'
    elif v <= 200: return '#ff0000'
    elif v <= 300: return '#99004c'
    else:              return '#7e0023'


def aqi_level_text(value):
    try:
        v = float(value)
    except (ValueError, TypeError):
        return "—"
    if v <= 50:    return '优'
    elif v <= 100: return '良'
    elif v <= 150: return '轻度污染'
    elif v <= 200: return '中度污染'
    elif v <= 300: return '重度污染'
    else:              return '严重污染'


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

# 空数据判断
if df.empty:
    st.warning("暂无实时数据，请稍后重试...")
    st.stop()

# 数据信息栏
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

# 只对有有效数据的城市排序
df_valid = df[df['aqi'].notna() & (df['aqi'] > 0)].copy()
df_sorted = df_valid.sort_values('aqi', ascending=False)

left_col, right_col = st.columns(2)

with left_col:
    st.markdown("#### 🟢 空气最佳 Top 10")
    best = df_sorted.tail(10).iloc[::-1] if len(df_sorted) >= 10 else df_sorted.iloc[::-1]
    # [修4] 使用正确的列名 city_name（非 city）
    display_cols = [c for c in ['city_name', 'aqi', 'level', 'dominant_pollutant'] if c in best.columns]
    col_labels = ['城市', 'AQI', '等级', '首要污染物'][:len(display_cols)]
    best_display = best[display_cols].copy()
    if 'aqi' in best_display.columns:
        best_display['aqi'] = best_display['aqi'].apply(lambda x: int(x) if pd.notna(x) else '—')
    best_display.columns = col_labels
    best_display.reset_index(drop=True, inplace=True)
    best_display.index += 1
    st.dataframe(best_display, use_container_width=True, height=360)

with right_col:
    st.markdown("#### 🔴 空气最差 Top 10")
    worst = df_sorted.head(10) if len(df_sorted) >= 10 else df_sorted
    display_cols = [c for c in ['city_name', 'aqi', 'level', 'dominant_pollutant'] if c in worst.columns]
    col_labels = ['城市', 'AQI', '等级', '首要污染物'][:len(display_cols)]
    worst_display = worst[display_cols].copy()
    if 'aqi' in worst_display.columns:
        worst_display['aqi'] = worst_display['aqi'].apply(lambda x: int(x) if pd.notna(x) else '—')
    worst_display.columns = col_labels
    worst_display.reset_index(drop=True, inplace=True)
    worst_display.index += 1
    st.dataframe(worst_display, use_container_width=True, height=360)


# ==============================
# 加载 GeoJSON（国界线 + 十段线）
# ==============================
@st.cache_data(ttl=86400, show_spinner=False)
def _load_china_boundary():
    url = 'https://geo.datav.aliyun.com/areas_v3/bound/100000.json'
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    resp = urllib.request.urlopen(req, timeout=15)
    return json.loads(resp.read().decode('utf-8'))

@st.cache_data(ttl=86400, show_spinner=False)
def _load_ten_dash_line():
    url = 'https://raw.githubusercontent.com/gmt-china/china-geospatial-data/master/ten-dash-line.gmt'
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    resp = urllib.request.urlopen(req, timeout=15)
    gmt_text = resp.read().decode('utf-8')

    segments = []
    current = []
    for line in gmt_text.strip().split('\n'):
        line = line.strip()
        if line.startswith('#') or line.startswith('@'):
            continue
        if not line:
            if current:
                segments.append(current)
                current = []
            continue
        parts = line.split()
        if len(parts) >= 2:
            try:
                current.append([float(parts[0]), float(parts[1])])
            except ValueError:
                pass
    if current:
        segments.append(current)

    return {
        "type": "FeatureCollection",
        "features": [{
            "type": "Feature",
            "properties": {"name": "ten_dash_line"},
            "geometry": {"type": "LineString", "coordinates": seg}
        } for seg in segments if len(seg) >= 2]
    }


# ==============================
# folium 全国污染热力分布地图
# ==============================
st.subheader("🗺️ 全国空气质量分布")

df_map = df.copy()
df_map = df_map[df_map['aqi'].notna()]

if df_map.empty:
    st.warning("暂无有效的AQI数据，无法生成热力图")
    st.stop()

# [修5] tiles=None 后用 TileLayer 添加高德底图（不能直接传 URL 给 tiles 参数）
m = folium.Map(location=[38, 108], zoom_start=4, tiles=None, control_scale=True)

amap_url = 'https://webrd0{s}.is.autonavi.com/appmaptile?lang=zh_cn&size=1&scale=1&style=8&x={x}&y={y}&z={z}'
folium.TileLayer(
    tiles=amap_url, attr='&copy; 高德地图', name='高德地图（中文）',
    subdomains='1234', max_zoom=18, overlay=False, control=True, show=True
).add_to(m)

# 备用底图 CartoDB
cartodb_url = 'https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}{y}{r}.png'
folium.TileLayer(
    tiles=cartodb_url, attr='&copy; CartoDB', name='CartoDB（英文）',
    max_zoom=18, overlay=False, control=True, show=False
).add_to(m)

# 中国国界线
try:
    boundary_data = _load_china_boundary()
    folium.GeoJson(
        boundary_data, name='国界线',
        style_function=lambda x: {
            'fillColor': 'transparent', 'color': '#666666',
            'weight': 1.2, 'fillOpacity': 0,
        }, show=True
    ).add_to(m)
except Exception:
    pass

# 南海十段线（默认关闭）
try:
    dash_data = _load_ten_dash_line()
    folium.GeoJson(
        dash_data, name='十段线',
        style_function=lambda x: {
            'color': '#666666', 'weight': 2, 'dashArray': '6, 4',
        }, show=False
    ).add_to(m)
except Exception:
    pass

# AQI 圆点标记
for _, row in df_map.iterrows():
    try:
        # [修4] 正确列名 city_name
        city = str(row.get('city_name', ''))
        aqi_val = float(row.get('aqi', 0))
        lat = float(row.get('lat', 0))
        lon = float(row.get('lon', 0))

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
        location=[lat, lon], radius=radius,
        color=color, fill=True, fill_color=color, fill_opacity=0.6,
        popup=folium.Popup(
            f"<b>{city}</b><br>AQI: {int(aqi_val)} ({level})",
            max_width=200
        ),
        tooltip=f"{city}: AQI {int(aqi_val)}",
    ).add_to(m)

folium.LayerControl().add_to(m)

# 自动缩放：让地图紧贴所有城市标记
all_locs = [[row['lat'], row['lon']] for _, row in df_map.iterrows()
            if pd.notna(row.get('lat')) and pd.notna(row.get('lon'))
            and float(row.get('lat', 0)) != 0 and float(row.get('lon', 0)) != 0]
if all_locs:
    m.fit_bounds(all_locs, padding=(40, 40))

st_folium(m, use_container_width=True, height=450)

# ==============================
# 右下角 AQI 图例 — 独立 st.markdown 浮动层（确保可见）
# ==============================
st.markdown("""
<div class="aqi-legend-float">
<b>📊 空气质量等级 (AQI)</b>
<div class="lg-item"><i style="background:#00e400;"></i> 优 (0–50)</div>
<div class="lg-item"><i style="background:#ffff00;"></i> 良 (51–100)</div>
<div class="lg-item"><i style="background:#ff7e00;"></i> 轻度污染 (101–150)</div>
<div class="lg-item"><i style="background:#ff0000;"></i> 中度污染 (151–200)</div>
<div class="lg-item"><i style="background:#99004c;"></i> 重度污染 (201–300)</div>
<div class="lg-item"><i style="background:#7e0023;"></i> 严重污染 (>300)</div>
</div>
""", unsafe_allow_html=True)


# ==============================
# 制作人信息
# ==============================
st.markdown("---")
st.caption("👨‍💻 制作人：刘宇博 · 江毅 · 张睿 ｜ 大数据与人工智能导论课程项目")
