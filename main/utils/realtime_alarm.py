# -*- coding: utf-8 -*-
"""
轻量级实时气象预警数据获取模块
直接调用中央气象台 API，不走 Excel，返回 pandas DataFrame。

供 Streamlit 应用在页面加载时调用，确保数据实时。
失败时自动 fallback 到本地 Excel 数据。
"""

import requests
import json
import re
import time
import warnings
from datetime import datetime

import pandas as pd

warnings.filterwarnings('ignore')


# ═══════════════════════════════════════════════
# 辅助函数（从 weather_alarm_crawler.py 提取核心逻辑）
# ═══════════════════════════════════════════════

def _extract_level(title):
    """从预警标题中提取预警等级"""
    for kw in ["红色预警信号", "橙色预警信号", "黄色预警信号", "蓝色预警信号", "白色预警信号"]:
        if kw in title:
            return kw.replace("预警信号", "")
    for lv in ["红色", "橙色", "黄色", "蓝色", "白色"]:
        if lv in title:
            return lv
    return "未知"


def _extract_type(title):
    """从预警标题中提取预警类型"""
    keywords = [
        "台风", "暴雨", "暴雪", "寒潮", "大风", "沙尘暴", "高温",
        "干旱", "雷电", "冰雹", "霜冻", "大雾", "霾", "道路结冰",
        "森林火险", "雷雨大风", "强对流", "低温", "雪灾",
        "高温", "臭氧", "海啸", "地质灾害", "山洪灾害", "洪水",
        "渍涝", "大风降温", "强降温", "紫外线", "空气重污染",
        "高温中暑", "干热风", "龙卷风", "干雾",
    ]
    for kw in keywords:
        if kw in title:
            return kw
    m = re.search(r"发布(.{2,6}?)(?:预警|信号)", title)
    if m:
        return m.group(1)
    return "其他"


def _extract_location(title):
    """从预警标题中提取省份和城市"""
    provinces = [
        "北京市", "天津市", "上海市", "重庆市",
        "河北省", "山西省", "辽宁省", "吉林省", "黑龙江省",
        "江苏省", "浙江省", "安徽省", "福建省", "江西省", "山东省",
        "河南省", "湖北省", "湖南省", "广东省", "海南省",
        "四川省", "贵州省", "云南省", "陕西省", "甘肃省", "青海省",
        "台湾省",
        "内蒙古自治区", "广西壮族自治区", "西藏自治区",
        "宁夏回族自治区", "新疆维吾尔自治区",
        "香港特别行政区", "澳门特别行政区",
    ]
    short_map = {"北京": "北京市", "天津": "天津市", "上海": "上海市", "重庆": "重庆市"}

    province = ""
    for p in provinces:
        if title.startswith(p) or p in title[:10]:
            province = p
            break
    if not province:
        for short, full in short_map.items():
            if title.startswith(short):
                province = full
                break

    city = ""
    if province:
        remaining = title.replace(province, "").replace(short_map.get(province[:2], ""), "")
        m = re.match(r"([\u4e00-\u9fa5]{1,6}?(?:市|州|区|县))", remaining)
        if m:
            city = m.group(1)

    return province, city


# ═══════════════════════════════════════════════
# API 请求
# ═══════════════════════════════════════════════

def _fetch_alarm_page(page=1, page_size=50, timeout=20):
    """从中央气象台获取一页预警数据"""
    url = "http://www.nmc.cn/rest/findAlarm"
    params = {
        "pageNo": page,
        "pageSize": page_size,
        "signaltype": "",
        "signallevel": "",
        "province": "",
        "_": int(time.time() * 1000),
    }
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Referer": "http://www.nmc.cn/publish/alarm.html",
        "Accept": "application/json, text/javascript, */*; q=0.01",
    }
    resp = requests.get(url, params=params, headers=headers, timeout=timeout)
    resp.encoding = "utf-8"
    text = resp.text.strip()
    # 处理 JSONP
    if text.startswith("var") or text.startswith("callback"):
        m = re.search(r"\((\{.*\})\)", text, re.DOTALL)
        if m:
            text = m.group(1)
    return json.loads(text)


def fetch_realtime_alarms(cache_ttl=600):
    """
    获取全国最新气象预警数据（爬取所有页）。

    Parameters
    ----------
    cache_ttl : int
        缓存时间（秒），默认 600 秒（10 分钟）。

    Returns
    -------
    tuple[DataFrame, str, list[str]]
        (df, fetch_time, debug_info)
        df 列：省份, 城市, 预警类型, 预警等级, 发布时间, 预警标题
    """
    import streamlit as st

    @st.cache_data(ttl=cache_ttl)
    def _do_fetch():
        debug = []
        all_records = []
        start = time.time()
        page = 1
        max_pages = 10

        while page <= max_pages:
            try:
                api_data = _fetch_alarm_page(page=page, page_size=50)
                try:
                    page_list = api_data["data"]["page"]["list"]
                except (KeyError, TypeError):
                    break

                if not page_list:
                    break

                for item in page_list:
                    title = item.get("title", "")
                    if not title:
                        continue
                    province, city = _extract_location(title)
                    all_records.append({
                        "省份": province,
                        "城市": city,
                        "预警类型": _extract_type(title),
                        "预警等级": _extract_level(title),
                        "发布时间": item.get("issuetime", ""),
                        "预警标题": title,
                    })

                # 检查是否还有下一页
                try:
                    total = api_data["data"]["page"]["totalPage"]
                    if page >= total:
                        break
                except (KeyError, TypeError):
                    pass

                page += 1
                time.sleep(0.3)

            except requests.exceptions.Timeout:
                debug.append(f"[WARN] 第 {page} 页请求超时")
                page += 1
                time.sleep(1)
            except Exception as e:
                debug.append(f"[ERROR] 第 {page} 页获取失败：{type(e).__name__}")
                break

        elapsed = round(time.time() - start, 1)
        debug.insert(0, f"[实时API] 获取 {len(all_records)} 条预警，耗时 {elapsed}s")

        df = pd.DataFrame(all_records)
        fetch_time = datetime.now().strftime("%Y-%m-%d %H:%M")
        return df, fetch_time, debug

    return _do_fetch()
