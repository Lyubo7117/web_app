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


# ══════════════════════════════════════════════════
# 中国地级行政区名称库（用于从预警标题中精确提取）
# ══════════════════════════════════════════════════
_PREFECTURE_CITIES = sorted([
    '北京', '天津', '上海', '重庆',
    '石家庄', '唐山', '秦皇岛', '邯郸', '邢台', '保定',
    '张家口', '承德', '沧州', '廊坊', '衡水',
    '太原', '大同', '阳泉', '长治', '晋城', '朔州',
    '晋中', '运城', '忻州', '临汾', '吕梁',
    '呼和浩特', '包头', '乌海', '赤峰', '通辽',
    '鄂尔多斯', '呼伦贝尔', '巴彦淖尔', '乌兰察布',
    '兴安', '锡林郭勒', '阿拉善',
    '沈阳', '大连', '鞍山', '抚顺', '本溪', '丹东',
    '锦州', '营口', '阜新', '辽阳', '盘锦', '铁岭',
    '朝阳', '葫芦岛',
    '长春', '吉林', '四平', '辽源', '通化', '白山',
    '松原', '白城', '延边',
    '哈尔滨', '齐齐哈尔', '鸡西', '鹤岗', '双鸭山', '大庆',
    '伊春', '佳木斯', '七台河', '牡丹江', '黑河', '绥化',
    '大兴安岭',
    '南京', '无锡', '徐州', '常州', '苏州', '南通',
    '连云港', '淮安', '盐城', '扬州', '镇江', '泰州', '宿迁',
    '杭州', '宁波', '温州', '嘉兴', '湖州', '绍兴',
    '金华', '衢州', '舟山', '台州', '丽水',
    '合肥', '芜湖', '蚌埠', '淮南', '马鞍山', '淮北',
    '铜陵', '安庆', '黄山', '滁州', '阜阳', '宿州',
    '六安', '亳州', '池州', '宣城',
    '福州', '厦门', '莆田', '三明', '泉州', '漳州',
    '南平', '龙岩', '宁德',
    '南昌', '景德镇', '萍乡', '九江', '新余', '鹰潭',
    '赣州', '吉安', '宜春', '抚州', '上饶',
    '济南', '青岛', '淄博', '枣庄', '东营', '烟台',
    '潍坊', '济宁', '泰安', '威海', '日照', '临沂',
    '德州', '聊城', '滨州', '菏泽',
    '郑州', '开封', '洛阳', '平顶山', '安阳', '鹤壁',
    '新乡', '焦作', '濮阳', '许昌', '漯河', '三门峡',
    '南阳', '商丘', '信阳', '周口', '驻马店',
    '武汉', '黄石', '十堰', '宜昌', '襄阳', '鄂州',
    '荆门', '孝感', '荆州', '黄冈', '咸宁', '随州',
    '恩施',
    '长沙', '株洲', '湘潭', '衡阳', '邵阳', '岳阳',
    '常德', '张家界', '益阳', '郴州', '永州', '怀化', '娄底',
    '湘西',
    '广州', '韶关', '深圳', '珠海', '汕头', '佛山',
    '江门', '湛江', '茂名', '肇庆', '惠州', '梅州',
    '汕尾', '河源', '阳江', '清远', '东莞', '中山',
    '潮州', '揭阳', '云浮',
    '南宁', '柳州', '桂林', '梧州', '北海', '防城港',
    '钦州', '贵港', '玉林', '百色', '贺州', '河池',
    '来宾', '崇左',
    '海口', '三亚', '三沙', '儋州',
    '成都', '自贡', '攀枝花', '泸州', '德阳', '绵阳',
    '广元', '遂宁', '内江', '乐山', '南充', '眉山',
    '宜宾', '广安', '达州', '雅安', '巴中', '资阳',
    '阿坝', '甘孜', '凉山',
    '贵阳', '六盘水', '遵义', '安顺', '毕节', '铜仁',
    '黔西南', '黔东南', '黔南',
    '昆明', '曲靖', '玉溪', '保山', '昭通', '丽江',
    '普洱', '临沧',
    '楚雄', '红河', '文山', '西双版纳', '大理', '德宏',
    '怒江', '迪庆',
    '拉萨', '日喀则', '昌都', '林芝', '山南', '那曲',
    '阿里',
    '西安', '铜川', '宝鸡', '咸阳', '渭南', '延安',
    '汉中', '榆林', '安康', '商洛',
    '兰州', '嘉峪关', '金昌', '白银', '天水', '武威',
    '张掖', '平凉', '酒泉', '庆阳', '定西', '陇南',
    '甘南', '临夏',
    '西宁', '海东',
    '海北', '黄南', '海南州', '果洛', '玉树', '海西',
    '银川', '石嘴山', '吴忠', '固原', '中卫',
    '乌鲁木齐', '克拉玛依', '吐鲁番', '哈密',
    '昌吉', '博尔塔拉', '巴音郭勒', '阿克苏', '克孜勒苏',
    '喀什', '和田', '伊犁', '塔城', '阿勒泰',
    '香港', '澳门',
], key=len, reverse=True)

# 省份完整名列表（用于排除误匹配）
_PROVINCE_FULL_NAMES = {
    '北京市', '天津市', '上海市', '重庆市',
    '河北省', '山西省', '辽宁省', '吉林省', '黑龙江省',
    '江苏省', '浙江省', '安徽省', '福建省', '江西省', '山东省',
    '河南省', '湖北省', '湖南省', '广东省', '海南省',
    '四川省', '贵州省', '云南省', '陕西省', '甘肃省', '青海省',
    '台湾省',
    '内蒙古自治区', '广西壮族自治区', '西藏自治区',
    '宁夏回族自治区', '新疆维吾尔自治区',
    '香港特别行政区', '澳门特别行政区',
}

# 省份短名→完整名映射
_SHORT_TO_FULL = {
    '北京': '北京市', '天津': '天津市', '上海': '上海市', '重庆': '重庆市',
}


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
        "地质灾害", "山洪灾害", "洪水",
        "渍涝", "大风降温", "强降温",
        "雷雨强风",  # 特殊组合词
    ]
    for kw in keywords:
        if kw in title:
            return kw
    m = re.search(r"发布(.{2,6}?)(?:预警|信号)", title)
    if m:
        return m.group(1)
    return "其他"


# 城市名 → 标准全称 后缀映射（用于自动补全）
# 规则：在标题中找到城市名后，检查紧随其后的字符来决定后缀
_CITY_SUFFIXES = ['自治州', '自治区', '地区', '市', '州', '盟', '县']  # 按长度降序


def _normalize_city_name(raw_city, title):
    """
    将提取到的城市简称补全为标准行政名称。
    例：'兰州' + 标题中有"兰州市" → '兰州市'
        '台州' + 标题中有"台州市" → '台州市'
        '黔西南' + 标题中有"布依族苗族自治州" → '黔西南布依族苗族自治州'
        '延边' + 标题中有"朝鲜族自治州" → '延边朝鲜族自治州'
    """
    if not raw_city or not title:
        return raw_city

    # 在标题中定位 raw_city 的位置
    idx = title.find(raw_city)
    if idx == -1:
        # 找不到就用默认规则：纯地名→补"市"
        if any(raw_city.endswith(s) for s in ['市', '州', '地区', '盟', '县', '旗']):
            return raw_city
        return raw_city + '市'

    # 查看 raw_city 之后紧跟的字符，取最长的合法后缀
    after = title[idx + len(raw_city):]

    # ── 先检查简单后缀 ──
    for suffix in _CITY_SUFFIXES:
        if after.startswith(suffix):
            return raw_city + suffix

    # ── 再检查复合自治州后缀（如"布依族苗族自治州"、"朝鲜族自治州"、"回族自治州"）──
    compound_match = re.match(r'^([\u4e00-\u9fa5]{0,15})自治州', after)
    if compound_match:
        prefix = compound_match.group(1)  # 如 "布依族苗族"、"朝鲜"、"回"
        return raw_city + prefix + '自治州'

    # 没有任何后缀 → 默认补"市"
    if not any(raw_city.endswith(s) for s in ['市', '州', '地区', '盟']):
        return raw_city + '市'
    return raw_city


def _extract_city_from_title(title):
    """
    【核心函数】从预警标题中提取地级市/自治州名称。
    
    匹配策略（按优先级）：
    1. 精确匹配 _PREFECTURE_CITIES 中的已知城市名（按长度降序）
    2. 正则匹配 "XX省(XX市|XX自治州|XX地区)" 中的地名
    
    所有返回值均经过后缀规范化（如 "兰州" → "兰州市"）

    Parameters
    ----------
    title : str
        预警标题全文
    
    Returns
    -------
    str | None
        提取到的标准城市全称（含"市/州/地区"等后缀），未找到返回 None
    """
    if not title or not str(title).strip():
        return None
    title = str(title).strip()
    if len(title) < 4:
        return None

    # ── 策略1: 已知城市库精确查找（按长度降序，长名字优先）──
    # 先收集所有匹配位置，再选最佳（优先选位置靠后的、更长的）
    best_match = None
    best_pos = -1
    for city_name in _PREFECTURE_CITIES:
        idx = title.find(city_name)
        if idx == -1:
            continue
        # 排除纯省份名误匹配（"吉林省延边..." 开头的 "吉林"）
        if idx <= 2 and city_name in _PROVINCE_FULL_NAMES:
            continue
        # 选位置最靠后的（跳过省份前缀后的第一个地名）
        if idx > best_pos:
            best_match = city_name
            best_pos = idx

    if best_match:
        return _normalize_city_name(best_match, title)

    # ── 策略2: 正则提取 "省(XX自治州/XX地区)" 格式 ──
    patterns = [
        r'省([^省市自治区]{2,15}(?:自治州))',
        r'自治区([^省市自治区]{2,10}市)',
        r'自治区([^省市自治区]{2,15}(?:自治州))',
        r'省[^市]{0,3}(塔城|阿勒泰|阿克苏|喀什|和田|哈密|昌吉)地区?',
    ]
    for pat in patterns:
        m = re.search(pat, title)
        if m:
            name = m.group(1).strip()
            if name and len(name) >= 2:
                return _normalize_city_name(name, title)

    # ── 策略3: 兜底 — 去掉省份前缀后的第一个地名 ──
    for prov in _PROVINCE_FULL_NAMES:
        if title.startswith(prov):
            rest = title[len(prov):].strip()
            m = re.match(r'^([\u4e00-\u9fa5]{2,8}(?:市|州|地区|盟))', rest)
            if m:
                return _normalize_city_name(m.group(1).strip(), title)

    return None


def _extract_location(title):
    """
    【重写】从预警标题中提取 (省份, 城市) 二元组。
    替换原来的弱正则为强力的地级市库匹配。
    """
    province = ""
    city = ""

    # 1) 提取省份
    for p in sorted(_PROVINCE_FULL_NAMES, key=len, reverse=True):
        if title.startswith(p) or p[:2] in title[:6] and len(p) > 2:
            province = p
            break
    if not province:
        for short, full in _SHORT_TO_FULL.items():
            if title.startswith(short):
                province = full
                break

    # 2) 提取城市（使用新的强匹配函数）
    extracted = _extract_city_from_title(title)
    if extracted:
        city = extracted
    elif province:
        # 最后兜底：去掉省份后尝试简单正则
        rest = title.replace(province, '').strip()
        m = re.match(r'^([\u4e00-\u9fa5]{2,8}(?:市|州|地区|盟))', rest)
        if m:
            city = m.group(1).strip()

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
    max_pages = 15

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
                    "预警标题": title,  # 保留原始标题供二次提取
            })

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
    """
    import streamlit as st

    @st.cache_data(ttl=cache_ttl, show_spinner=False)
    def _do_fetch(_version="v4_city_suffix_normalize"):
        debug = []

        try:
            records, nmc_debug = _fetch_all_nmc_alarms()
            debug.extend(nmc_debug)

            if records:
                df = pd.DataFrame(records)

                # ===== 关键：对仍然为空的城市名做最终填充 =====
                def _final_fill(row):
                    raw_city = row.get('城市', '')
                    province = row.get('省份', '')
                    title = row.get('预警标题', '')

                    if pd.notna(raw_city) and str(raw_city).strip() and str(raw_city).strip() not in ['nan', 'None']:
                        return str(raw_city).strip()

                    # 用标题再做一次提取（保险）
                    from_title = _extract_city_from_title(str(title))
                    if from_title:
                        return from_title

                    # 省级兜底
                    if pd.notna(province) and str(province).strip() and str(province).strip() not in ['nan', 'None', '', '未知']:
                        return f"{str(province).strip()}（省级预警）"

                    return "未知地区"

                df['城市'] = df.apply(_final_fill, axis=1)

                now_beijing = datetime.now(timezone(timedelta(hours=8)))
                fetch_time = now_beijing.strftime("%Y-%m-%d %H:%M")

                # 统计填充效果
                empty_before = 0  # 无法回溯，跳过
                filled = (df['城市'].str.contains('省级预警') | (df['城市'] == '未知地区')).sum()
                debug.append(f"[填充] 最终仍有 {filled} 条使用省级/未知兜底")

                debug.append("[路由] 使用数据源: 中央气象台")
                return df, fetch_time, debug

        except Exception as e:
            debug.append(f"[ERROR] 中央气象台不可达：{type(e).__name__}: {str(e)[:80]}")

        debug.append("[路由] 中央气象台不可达（海外环境），返回空数据")
        return pd.DataFrame(), "", debug

    return _do_fetch()
