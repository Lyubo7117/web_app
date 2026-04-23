# -*- coding: utf-8 -*-
"""
轻量级实时 AQI 数据获取模块
直接调用中国天气网 API，不走 Excel，返回 pandas DataFrame。

供 Streamlit 应用在页面加载时调用，确保数据实时。
失败时自动 fallback 到本地 Excel 数据。
"""

import requests
import json
import re
import time
import warnings
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed

import pandas as pd

warnings.filterwarnings('ignore')

# ═══════════════════════════════════════════════
# 34城市数据库（与 national_aqi_crawler.py 保持一致）
# ═══════════════════════════════════════════════

CITIES = [
    {"name": "北京",   "code": "101010100", "province": "北京市",   "region": "华北区"},
    {"name": "天津",   "code": "101030100", "province": "天津市",   "region": "华北区"},
    {"name": "石家庄", "code": "101090101", "province": "河北省",   "region": "华北区"},
    {"name": "太原",   "code": "101100101", "province": "山西省",   "region": "华北区"},
    {"name": "呼和浩特","code":"101080101", "province": "内蒙古自治区","region":"华北区"},
    {"name": "沈阳",   "code": "101070101", "province": "辽宁省",   "region": "东北区"},
    {"name": "长春",   "code": "101060101", "province": "吉林省",   "region": "东北区"},
    {"name": "哈尔滨", "code": "101050101", "province": "黑龙江省", "region": "东北区"},
    {"name": "上海",   "code": "101020100", "province": "上海市",   "region": "华东区"},
    {"name": "南京",   "code": "101190101", "province": "江苏省",   "region": "华东区"},
    {"name": "杭州",   "code": "101210101", "province": "浙江省",   "region": "华东区"},
    {"name": "合肥",   "code": "101220101", "province": "安徽省",   "region": "华东区"},
    {"name": "福州",   "code": "101230101", "province": "福建省",   "region": "华东区"},
    {"name": "南昌",   "code": "101240101", "province": "江西省",   "region": "华东区"},
    {"name": "济南",   "code": "101120101", "province": "山东省",   "region": "华东区"},
    {"name": "郑州",   "code": "101180101", "province": "河南省",   "region": "华中区"},
    {"name": "武汉",   "code": "101200101", "province": "湖北省",   "region": "华中区"},
    {"name": "长沙",   "code": "101250101", "province": "湖南省",   "region": "华中区"},
    {"name": "广州",   "code": "101280101", "province": "广东省",   "region": "华南区"},
    {"name": "南宁",   "code": "101300101", "province": "广西壮族自治区","region":"华南区"},
    {"name": "海口",   "code": "101310101", "province": "海南省",   "region": "华南区"},
    {"name": "重庆",   "code": "101040100", "province": "重庆市",   "region": "西南区"},
    {"name": "成都",   "code": "101270101", "province": "四川省",   "region": "西南区"},
    {"name": "贵阳",   "code": "101260101", "province": "贵州省",   "region": "西南区"},
    {"name": "昆明",   "code": "101290101", "province": "云南省",   "region": "西南区"},
    {"name": "拉萨",   "code": "101140101", "province": "西藏自治区","region":"西南区"},
    {"name": "西安",   "code": "101110101", "province": "陕西省",   "region": "西北区"},
    {"name": "兰州",   "code": "101160101", "province": "甘肃省",   "region": "西北区"},
    {"name": "西宁",   "code": "101150101", "province": "青海省",   "region": "西北区"},
    {"name": "银川",   "code": "101170101", "province": "宁夏回族自治区","region":"西北区"},
    {"name": "乌鲁木齐","code":"101130101", "province": "新疆维吾尔自治区","region":"西北区"},
    {"name": "香港",   "code": "101320101", "province": "香港特别行政区","region":"港澳台区"},
    {"name": "澳门",   "code": "101330101", "province": "澳门特别行政区","region":"港澳台区"},
    {"name": "台北",   "code": "101340101", "province": "台湾省",   "region": "港澳台区"},
]

# 经纬度（供地图使用）
CITY_COORDS = {
    "北京": (39.90, 116.40), "天津": (39.13, 117.20), "石家庄": (38.04, 114.51),
    "太原": (37.87, 112.55), "呼和浩特": (40.84, 111.75), "沈阳": (41.80, 123.43),
    "长春": (43.88, 125.32), "哈尔滨": (45.75, 126.65), "上海": (31.23, 121.47),
    "南京": (32.06, 118.80), "杭州": (30.27, 120.15), "合肥": (31.82, 117.23),
    "福州": (26.08, 119.30), "南昌": (28.68, 115.86), "济南": (36.65, 116.98),
    "郑州": (34.75, 113.65), "武汉": (30.59, 114.31), "长沙": (28.23, 112.94),
    "广州": (23.13, 113.26), "南宁": (22.82, 108.37), "海口": (20.04, 110.35),
    "重庆": (29.56, 106.55), "成都": (30.57, 104.07), "贵阳": (26.65, 106.63),
    "昆明": (25.04, 102.71), "拉萨": (29.65, 91.13), "西安": (34.26, 108.94),
    "兰州": (36.06, 103.83), "西宁": (36.62, 101.78), "银川": (38.49, 106.23),
    "乌鲁木齐": (43.83, 87.62), "香港": (22.32, 114.17), "澳门": (22.20, 113.55),
    "台北": (25.03, 121.57),
}


def _aqi_level(aqi):
    """AQI 数值 → 等级文字"""
    try:
        aqi = float(aqi)
    except (ValueError, TypeError):
        return "—"
    if aqi <= 50:   return "优"
    if aqi <= 100:  return "良"
    if aqi <= 150:  return "轻度污染"
    if aqi <= 200:  return "中度污染"
    if aqi <= 300:  return "重度污染"
    return "严重污染"


def _aqi_color(aqi):
    """AQI 数值 → 颜色代码"""
    try:
        aqi = float(aqi)
    except (ValueError, TypeError):
        return "#cccccc"
    if aqi <= 50:   return "#00e400"
    if aqi <= 100:  return "#ffff00"
    if aqi <= 150:  return "#ff7e00"
    if aqi <= 200:  return "#ff0000"
    if aqi <= 300:  return "#99004c"
    return "#7e0023"


def _fetch_city_aqi(city_info, timeout=15):
    """
    获取单个城市的最新 AQI 数据。
    返回 dict 或 None（失败时）。
    """
    url = f"https://d1.weather.com.cn/aqi_all/{city_info['code']}.html"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Referer": "https://www.weather.com.cn/air/",
        "Accept": "*/*",
    }
    try:
        resp = requests.get(url, headers=headers, timeout=timeout, verify=False)
        resp.encoding = "utf-8"
        match = re.search(r"setAirData\((\{.*\})\)", resp.text, re.DOTALL)
        if not match:
            return None
        data = json.loads(match.group(1))

        records = data.get("data", [])
        if not records:
            return None

        # 取最新一条（列表末尾）
        latest = records[-1]
        now = datetime.now()

        def safe(key, default=0):
            v = latest.get(key, "")
            if v == "" or v is None:
                return default
            try:
                return float(v)
            except (ValueError, TypeError):
                return default

        # 首要污染物
        def dominant():
            vals = {
                "PM2.5": safe("t3"), "PM10": safe("t4"),
                "O3": safe("t7"), "NO2": safe("t6"),
                "SO2": safe("t9"), "CO": safe("t5") * 10,
            }
            mx = max(vals, key=vals.get)
            return mx if vals[mx] > 0 else "—"

        aqi_val = safe("t1")
        coords = CITY_COORDS.get(city_info["name"], (0, 0))

        return {
            "city_name": city_info["name"],
            "province": city_info["province"],
            "region": city_info["region"],
            "aqi": aqi_val,
            "level": _aqi_level(aqi_val),
            "color": _aqi_color(aqi_val),
            "pm25": safe("t3"),
            "pm10": safe("t4"),
            "co": safe("t5"),
            "no2": safe("t6"),
            "o3": safe("t7"),
            "so2": safe("t9"),
            "temperature": safe("t10"),
            "humidity": safe("t11"),
            "dominant_pollutant": dominant(),
            "lat": coords[0],
            "lon": coords[1],
            "datetime": now.strftime("%Y-%m-%d %H:%M"),
        }

    except Exception:
        return None


def fetch_realtime_aqi(cache_ttl=600):
    """
    并发获取全国 34 城市最新 AQI 数据。

    Parameters
    ----------
    cache_ttl : int
        缓存时间（秒），默认 600 秒（10 分钟）。
        Streamlit @st.cache_data 自动管理缓存。

    Returns
    -------
    tuple[DataFrame, str, list[str]]
        (df, fetch_time, debug_info)
        df 列：city_name, province, region, aqi, level, color,
               pm25, pm10, co, no2, o3, so2, temperature, humidity,
               dominant_pollutant, lat, lon, datetime
    """
    import streamlit as st

    @st.cache_data(ttl=cache_ttl)
    def _do_fetch():
        debug = []
        results = []
        start = time.time()

        # 并发获取（8线程，约 3-8 秒完成）
        with ThreadPoolExecutor(max_workers=8) as executor:
            futures = {executor.submit(_fetch_city_aqi, c): c for c in CITIES}
            for future in as_completed(futures):
                city = futures[future]["name"]
                try:
                    row = future.result()
                    if row:
                        results.append(row)
                    else:
                        debug.append(f"[WARN] {city}：数据获取失败")
                except Exception as e:
                    debug.append(f"[FAIL] {city}：{type(e).__name__}: {str(e)[:60]}")

        elapsed = round(time.time() - start, 1)
        debug.insert(0, f"[实时API] 成功获取 {len(results)}/{len(CITIES)} 个城市，耗时 {elapsed}s")

        if not results:
            debug.append("[ERROR] 所有城市获取失败")
            return pd.DataFrame(), "", debug

        df = pd.DataFrame(results)
        fetch_time = df["datetime"].iloc[0] if "datetime" in df.columns else datetime.now().strftime("%Y-%m-%d %H:%M")
        return df, fetch_time, debug

    return _do_fetch()
