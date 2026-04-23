# -*- coding: utf-8 -*-
"""
实时气象预警数据获取模块（双数据源）

数据源：
1. 中央气象台 API（nmc.cn）— 国内环境，实时中国预警
2. 无海外替代源 — 海外环境 gracefully fallback 到 Excel 缓存

自动检测：如果中央气象台不可达（如 Streamlit Cloud 海外服务器），自动 fallback。
"""

import requests
import json
import re
import time
import warnings
from datetime import datetime, timedelta, timezone

import pandas as pd

warnings.filterwarnings('ignore')


# ═══════════════════════════════════════════════
# 辅助函数
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
# 数据源1: 中央气象台 API
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


def _fetch_all_nmc_alarms():
    """从中央气象台获取全部实时预警"""
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
    debug.insert(0, f"[中央气象台] 获取 {len(all_records)} 条预警，耗时 {elapsed}s")
    return all_records, debug


# ═══════════════════════════════════════════════
# 主入口
# ═══════════════════════════════════════════════

def fetch_realtime_alarms(cache_ttl=600):
    """
    获取全国最新气象预警数据。

    策略：尝试中央气象台 API，海外不可达时返回空 DataFrame（由页面 fallback 到 Excel）。

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

    @st.cache_data(ttl=cache_ttl, show_spinner=False)
    def _do_fetch(_version="v2_nmc_with_version"):  # 改版本号可强制刷新缓存
        debug = []

        try:
            records, nmc_debug = _fetch_all_nmc_alarms()
            debug.extend(nmc_debug)

            if records:
                df = pd.DataFrame(records)
                # 转北京时间（Streamlit Cloud 在 UTC 时区）
                now_beijing = datetime.now(timezone(timedelta(hours=8)))
                fetch_time = now_beijing.strftime("%Y-%m-%d %H:%M")
                debug.append("[路由] 使用数据源: 中央气象台")
                return df, fetch_time, debug

        except Exception as e:
            debug.append(f"[ERROR] 中央气象台不可达：{type(e).__name__}: {str(e)[:80]}")

        # 海外环境：返回空 DataFrame，由页面 fallback 到 Excel
        debug.append("[路由] 中央气象台不可达（海外环境），返回空数据")
        return pd.DataFrame(), "", debug

    return _do_fetch()
