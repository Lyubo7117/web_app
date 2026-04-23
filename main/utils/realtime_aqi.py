# -*- coding: utf-8 -*-
"""
实时 AQI 数据获取模块（双数据源）

数据源优先级：
1. 中国天气网 API（d1.weather.com.cn）— 国内环境优先，AQI 为中国标准
2. Open-Meteo Air Quality API（open-meteo.com）— 海外可用，US EPA 标准 AQI

自动检测：如果中国天气网不可达（如 Streamlit Cloud 海外服务器），自动切换到 Open-Meteo。
"""

import requests
import json
import re
import time
import warnings
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

import pandas as pd

warnings.filterwarnings('ignore')

# ═══════════════════════════════════════════════
# 34城市数据库
# ═══════════════════════════════════════════════

CITIES = [
    {"name": "北京",   "code": "101010100", "province": "北京市",   "region": "华北区",   "lat": 39.90, "lon": 116.40},
    {"name": "天津",   "code": "101030100", "province": "天津市",   "region": "华北区",   "lat": 39.13, "lon": 117.20},
    {"name": "石家庄", "code": "101090101", "province": "河北省",   "region": "华北区",   "lat": 38.04, "lon": 114.51},
    {"name": "太原",   "code": "101100101", "province": "山西省",   "region": "华北区",   "lat": 37.87, "lon": 112.55},
    {"name": "呼和浩特","code":"101080101", "province": "内蒙古自治区","region":"华北区",   "lat": 40.84, "lon": 111.75},
    {"name": "沈阳",   "code": "101070101", "province": "辽宁省",   "region": "东北区",   "lat": 41.80, "lon": 123.43},
    {"name": "长春",   "code": "101060101", "province": "吉林省",   "region": "东北区",   "lat": 43.88, "lon": 125.32},
    {"name": "哈尔滨", "code": "101050101", "province": "黑龙江省", "region": "东北区",   "lat": 45.75, "lon": 126.65},
    {"name": "上海",   "code": "101020100", "province": "上海市",   "region": "华东区",   "lat": 31.23, "lon": 121.47},
    {"name": "南京",   "code": "101190101", "province": "江苏省",   "region": "华东区",   "lat": 32.06, "lon": 118.80},
    {"name": "杭州",   "code": "101210101", "province": "浙江省",   "region": "华东区",   "lat": 30.27, "lon": 120.15},
    {"name": "合肥",   "code": "101220101", "province": "安徽省",   "region": "华东区",   "lat": 31.82, "lon": 117.23},
    {"name": "福州",   "code": "101230101", "province": "福建省",   "region": "华东区",   "lat": 26.08, "lon": 119.30},
    {"name": "南昌",   "code": "101240101", "province": "江西省",   "region": "华东区",   "lat": 28.68, "lon": 115.86},
    {"name": "济南",   "code": "101120101", "province": "山东省",   "region": "华东区",   "lat": 36.65, "lon": 116.98},
    {"name": "郑州",   "code": "101180101", "province": "河南省",   "region": "华中区",   "lat": 34.75, "lon": 113.65},
    {"name": "武汉",   "code": "101200101", "province": "湖北省",   "region": "华中区",   "lat": 30.59, "lon": 114.31},
    {"name": "长沙",   "code": "101250101", "province": "湖南省",   "region": "华中区",   "lat": 28.23, "lon": 112.94},
    {"name": "广州",   "code": "101280101", "province": "广东省",   "region": "华南区",   "lat": 23.13, "lon": 113.26},
    {"name": "南宁",   "code": "101300101", "province": "广西壮族自治区","region":"华南区",   "lat": 22.82, "lon": 108.37},
    {"name": "海口",   "code": "101310101", "province": "海南省",   "region": "华南区",   "lat": 20.04, "lon": 110.35},
    {"name": "重庆",   "code": "101040100", "province": "重庆市",   "region": "西南区",   "lat": 29.56, "lon": 106.55},
    {"name": "成都",   "code": "101270101", "province": "四川省",   "region": "西南区",   "lat": 30.57, "lon": 104.07},
    {"name": "贵阳",   "code": "101260101", "province": "贵州省",   "region": "西南区",   "lat": 26.65, "lon": 106.63},
    {"name": "昆明",   "code": "101290101", "province": "云南省",   "region": "西南区",   "lat": 25.04, "lon": 102.71},
    {"name": "拉萨",   "code": "101140101", "province": "西藏自治区","region":"西南区",   "lat": 29.65, "lon": 91.13},
    {"name": "西安",   "code": "101110101", "province": "陕西省",   "region": "西北区",   "lat": 34.26, "lon": 108.94},
    {"name": "兰州",   "code": "101160101", "province": "甘肃省",   "region": "西北区",   "lat": 36.06, "lon": 103.83},
    {"name": "西宁",   "code": "101150101", "province": "青海省",   "region": "西北区",   "lat": 36.62, "lon": 101.78},
    {"name": "银川",   "code": "101170101", "province": "宁夏回族自治区","region":"西北区",   "lat": 38.49, "lon": 106.23},
    {"name": "乌鲁木齐","code":"101130101", "province": "新疆维吾尔自治区","region":"西北区",   "lat": 43.83, "lon": 87.62},
    {"name": "香港",   "code": "101320101", "province": "香港特别行政区","region":"港澳台区",   "lat": 22.32, "lon": 114.17},
    {"name": "澳门",   "code": "101330101", "province": "澳门特别行政区","region":"港澳台区",   "lat": 22.20, "lon": 113.55},
    {"name": "台北",   "code": "101340101", "province": "台湾省",   "region": "港澳台区",   "lat": 25.03, "lon": 121.57},
]


# ═══════════════════════════════════════════════
# 通用工具函数
# ═══════════════════════════════════════════════

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


# ═══════════════════════════════════════════════
# 数据源1: 中国天气网 API
# ═══════════════════════════════════════════════

def _fetch_weathercom_city(city_info, timeout=10):
    """从中国天气网获取单个城市 AQI"""
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

        latest = records[-1]

        def safe(key, default=0):
            v = latest.get(key, "")
            if v == "" or v is None:
                return default
            try:
                return float(v)
            except (ValueError, TypeError):
                return default

        def dominant():
            vals = {
                "PM2.5": safe("t3"), "PM10": safe("t4"),
                "O3": safe("t7"), "NO2": safe("t6"),
                "SO2": safe("t9"), "CO": safe("t5") * 10,
            }
            mx = max(vals, key=vals.get)
            return mx if vals[mx] > 0 else "—"

        aqi_val = safe("t1")

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
            "lat": city_info["lat"],
            "lon": city_info["lon"],
            "datetime": datetime.now().strftime("%Y-%m-%d %H:%M"),
        }
    except Exception:
        return None


def _fetch_all_weathercom():
    """并发获取所有城市的中国天气网数据"""
    debug = []
    results = []
    start = time.time()

    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = {executor.submit(_fetch_weathercom_city, c): c for c in CITIES}
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
    debug.insert(0, f"[中国天气网] 成功获取 {len(results)}/{len(CITIES)} 个城市，耗时 {elapsed}s")
    return results, debug


# ═══════════════════════════════════════════════
# 数据源2: Open-Meteo Air Quality API
# ═══════════════════════════════════════════════

def _fetch_openmeteo_city(city_info, timeout=15):
    """从 Open-Meteo 获取单个城市的空气质量数据"""
    url = "https://air-quality-api.open-meteo.com/v1/air-quality"
    params = {
        "latitude": city_info["lat"],
        "longitude": city_info["lon"],
        "current": "pm10,pm2_5,carbon_monoxide,nitrogen_dioxide,sulphur_dioxide,ozone,us_aqi",
        "timezone": "auto",
    }
    try:
        resp = requests.get(url, params=params, timeout=timeout)
        data = resp.json()
        if "current" not in data:
            return None

        c = data["current"]
        aqi_val = c.get("us_aqi")

        # 首要污染物判定（基于 US EPA IAQI）
        pollutants = {
            "PM2.5": c.get("pm2_5", 0),
            "PM10": c.get("pm10", 0),
            "O3": c.get("ozone", 0),
            "NO2": c.get("nitrogen_dioxide", 0),
            "SO2": c.get("sulphur_dioxide", 0),
            "CO": c.get("carbon_monoxide", 0),
        }
        # 简化：取浓度最大的作为首要污染物
        mx = max(pollutants, key=pollutants.get)
        dominant = mx if pollutants[mx] > 0 else "—"

        # 解析时间
        time_str = c.get("time", "")
        try:
            dt = datetime.fromisoformat(time_str.replace("Z", "+00:00"))
            dt_str = dt.strftime("%Y-%m-%d %H:%M")
        except Exception:
            dt_str = datetime.now().strftime("%Y-%m-%d %H:%M")

        return {
            "city_name": city_info["name"],
            "province": city_info["province"],
            "region": city_info["region"],
            "aqi": aqi_val,
            "level": _aqi_level(aqi_val),
            "color": _aqi_color(aqi_val),
            "pm25": c.get("pm2_5"),
            "pm10": c.get("pm10"),
            "co": c.get("carbon_monoxide"),
            "no2": c.get("nitrogen_dioxide"),
            "o3": c.get("ozone"),
            "so2": c.get("sulphur_dioxide"),
            "temperature": None,
            "humidity": None,
            "dominant_pollutant": dominant,
            "lat": city_info["lat"],
            "lon": city_info["lon"],
            "datetime": dt_str,
        }
    except Exception:
        return None


def _fetch_all_openmeteo():
    """并发获取所有城市的 Open-Meteo 数据"""
    debug = []
    results = []
    start = time.time()

    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = {executor.submit(_fetch_openmeteo_city, c): c for c in CITIES}
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
    debug.insert(0, f"[Open-Meteo] 成功获取 {len(results)}/{len(CITIES)} 个城市，耗时 {elapsed}s")
    return results, debug


# ═══════════════════════════════════════════════
# 主入口：自动选择数据源
# ═══════════════════════════════════════════════

def fetch_realtime_aqi(cache_ttl=600):
    """
    获取全国 34 城市最新 AQI 数据（自动选择数据源）。

    策略：
    1. 优先尝试中国天气网（国内网络环境）
    2. 如果中国天气网全部失败（海外环境），自动切换到 Open-Meteo

    Parameters
    ----------
    cache_ttl : int
        缓存时间（秒），默认 600 秒（10 分钟）。

    Returns
    -------
    tuple[DataFrame, str, list[str]]
        (df, fetch_time, debug_info)
    """
    import streamlit as st

    @st.cache_data(ttl=cache_ttl)
    def _do_fetch():
        debug = []

        # ── 尝试数据源1: 中国天气网 ──
        results, wc_debug = _fetch_all_weathercom()
        debug.extend(wc_debug)

        if len(results) >= len(CITIES) * 0.5:  # 成功获取一半以上城市
            df = pd.DataFrame(results)
            fetch_time = df["datetime"].iloc[0] if "datetime" in df.columns else ""
            debug.append("[路由] 使用数据源: 中国天气网")
            return df, fetch_time, debug, "中国天气网"

        # ── 数据源1 失败，切换到数据源2: Open-Meteo ──
        debug.append("[路由] 中国天气网不可达，切换到 Open-Meteo")
        results2, om_debug = _fetch_all_openmeteo()
        debug.extend(om_debug)

        if results2:
            df = pd.DataFrame(results2)
            fetch_time = df["datetime"].iloc[0] if "datetime" in df.columns else ""
            debug.append("[路由] 使用数据源: Open-Meteo（US EPA 标准）")
            return df, fetch_time, debug, "Open-Meteo"

        # ── 全部失败 ──
        debug.append("[ERROR] 所有数据源均不可用")
        return pd.DataFrame(), "", debug, "无"

    return _do_fetch()
