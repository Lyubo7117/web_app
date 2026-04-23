# -*- coding: utf-8 -*-
"""预警数据解析模块 - 完整修复版（后缀补全 + 空城市填充）"""

import pandas as pd
import glob
import os
import re
from openpyxl import load_workbook


# ══════════════════════════════════════
# 中国地级行政区名称库
# ══════════════════════════════════════
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
    '昌吉', '博尔塔拉', '巴音郭楞', '阿克苏', '克孜勒苏',
    '喀什', '和田', '伊犁', '塔城', '阿勒泰',
    '香港', '澳门',
], key=len, reverse=True)

# 省份短名列表（用于排除误匹配）
_PROVINCE_SHORT = [
    '北京', '天津', '上海', '重庆', '河北', '山西', '内蒙古',
    '辽宁', '吉林', '黑龙江', '江苏', '浙江', '安徽', '福建',
    '江西', '山东', '河南', '湖北', '湖南', '广东', '广西',
    '海南', '四川', '贵州', '云南', '西藏', '陕西', '甘肃',
    '青海', '宁夏', '新疆',
]

# 后缀列表（按长度降序）
_CITY_SUFFIXES = ['自治州', '自治区', '地区', '市', '州', '盟', '县']


# ══════════════════════════════════════
# 核心工具函数
# ══════════════════════════════════════

def _normalize_city_name(raw_city, text):
    """
    将城市简称补全为标准行政全称。
    '兰州' + "兰州市..." → '兰州市'
    '黔西南' + "布依族苗族自治州..." → '黔西南布依族苗族自治州'
    """
    if not raw_city or not text:
        return raw_city
    idx = text.find(raw_city)
    if idx == -1:
        # 文本中找不到原词，用默认规则
        if any(raw_city.endswith(s) for s in ['市', '州', '地区', '盟', '县', '旗']):
            return raw_city
        return raw_city + '市'

    after = text[idx + len(raw_city):]

    # 先检查简单后缀
    for suffix in _CITY_SUFFIXES:
        if after.startswith(suffix):
            return raw_city + suffix

    # 再检查复合自治州后缀
    compound_match = re.match(r'^([\u4e00-\u9fa5]{0,15})自治州', after)
    if compound_match:
        prefix = compound_match.group(1)
        return raw_city + prefix + '自治州'

    # 没有后缀 → 默认补"市"
    if not any(raw_city.endswith(s) for s in ['市', '州', '地区', '盟']):
        return raw_city + '市'
    return raw_city


def _extract_city_from_text(text):
    """
    从文本中提取城市名（已含后缀补全）。
    返回标准全称或 None。
    """
    if not text or pd.isna(text):
        return None
    text = str(text).strip()
    if len(text) < 4:
        return None

    # 策略1: 城市库精确查找
    best_match = None
    best_pos = -1
    for city in _PREFECTURE_CITIES:
        idx = text.find(city)
        if idx == -1:
            continue
        if idx <= 2 and city in _PROVINCE_SHORT:
            continue
        if idx > best_pos:
            best_match = city
            best_pos = idx

    if best_match:
        return _normalize_city_name(best_match, text)

    # 策略2: 正则提取
    patterns = [
        r'省([^省市自治区]{2,15}(?:自治州))',
        r'省([^省市自治区]{2,10}市)',
        r'自治区([^省市自治区]{2,10}市)',
        r'自治区([^省市自治区]{2,15}(?:自治州))',
    ]
    for pat in patterns:
        m = re.search(pat, text)
        if m:
            name = m.group(1).strip()
            if name and len(name) >= 2:
                return _normalize_city_name(name, text)

    return None


# ══════════════════════════════════════
# 主函数
# ══════════════════════════════════════

def get_latest_alarms(data_folder=None):
    debug = []
    debug.append("[开始] get_latest_alarms 执行")

    base_dir = os.path.join(os.getcwd(), 'main', 'data_output', 'alarms')
    fallback_dir = os.path.join(os.path.dirname(__file__), '..', 'data_output', 'alarms')
    alarm_dir = base_dir if os.path.exists(base_dir) else fallback_dir

    if not os.path.exists(alarm_dir):
        debug.append(f"[错误] 目录不存在: {alarm_dir}")
        return pd.DataFrame(), None, debug

    pattern = os.path.join(alarm_dir, '全国预警信息_*.xlsx')
    files = glob.glob(pattern)
    if not files:
        files = glob.glob(os.path.join(alarm_dir, '**', '全国预警信息_*.xlsx'), recursive=True)
        files = [f for f in files if not os.path.basename(f).startswith('~')]

    if not files:
        debug.append("[警告] 未找到预警Excel文件")
        return pd.DataFrame(), None, debug

    latest_file = max(files, key=os.path.getmtime)
    debug.append(f"[文件] 最新文件: {os.path.basename(latest_file)}")

    try:
        wb = load_workbook(latest_file, data_only=True)
        ws = wb.active
        rows = list(ws.iter_rows(values_only=True))
        if len(rows) < 4:
            debug.append("[错误] Excel 行数不足4行")
            return pd.DataFrame(), latest_file, debug

        # 解析表头和数据
        header = [str(c).strip() if c else '' for c in rows[2]]
        data_rows = rows[3:]
        df = pd.DataFrame(data_rows, columns=header)
        df = df.dropna(how='all')
        debug.append(f"[解析] 原始行数: {len(df)}, 列名: {list(df.columns[:8])}")

        # 清理列名
        df.columns = [re.sub(r'[\s\n\r]+', '', str(c)) for c in df.columns]

        required = ['省份', '城市', '预警类型', '预警等级', '发布时间', '解除时间']
        col_map = {}
        for req in required:
            for col in df.columns:
                if req in col:
                    col_map[req] = col
                    break

        if len(col_map) != len(required):
            debug.append(f"[警告] 列名映射不全: {col_map}，按位置提取")
            if len(df.columns) >= 6:
                df_out = df.iloc[:, :6].copy()
                df_out.columns = required
            else:
                return pd.DataFrame(), latest_file, debug
        else:
            df_out = df[[col_map[req] for req in required]].copy()
            df_out.columns = required

        # ── 类型转换 ──
        df_out['省份'] = df_out['省份'].fillna('').astype(str).str.strip()
        df_out['城市'] = df_out['城市'].fillna('').astype(str).str.strip()

        # 保留原始 DataFrame 引用（用于提取非标准列文本）
        _orig_df = df

        # ── 城市名智能填充 ──
        extract_count = 0
        suffix_count = 0
        province_fill_count = 0
        unknown_count = 0

        def _fill_city_smart(row):
            nonlocal extract_count, suffix_count, province_fill_count, unknown_count

            raw_city = row['城市']
            province = row['省份']

            # 第1级: 已有有效城市名 → 做后缀补全
            if raw_city and raw_city not in ['nan', 'None', '—', '']:
                # 拼接该行所有文本用于后缀匹配
                full_text = ''
                for col in df_out.columns:
                    val = row.get(col, '')
                    if pd.notna(val) and str(val).strip():
                        full_text += str(val).strip()
                for col in _orig_df.columns:
                    if col not in required:
                        val = row.get(col, '') if col in row.index else ''
                        if pd.notna(val) and str(val).strip() and len(str(val)) > 3:
                            full_text += str(val).strip()

                normalized = _normalize_city_name(raw_city, full_text)
                if normalized != raw_city:
                    suffix_count += 1
                return normalized

            # 第2级: 城市为空 → 从该行所有文本中提取
            full_text = ''
            for col in df_out.columns:
                val = row.get(col, '')
                if pd.notna(val) and str(val).strip():
                    full_text += str(val).strip()
            for col in _orig_df.columns:
                if col not in required:
                    val = row.get(col, '') if col in row.index else ''
                    if pd.notna(val) and str(val).strip() and len(str(val)) > 3:
                        full_text += str(val).strip()

            extracted = _extract_city_from_text(full_text)
            if extracted:
                extract_count += 1
                return extracted

            # 第3级: 省级兜底
            if province and province not in ['nan', 'None', '', '未知地区']:
                province_fill_count += 1
                return f"{province}（省级预警）"

            unknown_count += 1
            return "未知地区"

        df_out['城市'] = df_out.apply(_fill_city_smart, axis=1)
        df_out['省份'] = df_out['省份'].replace('', '未知地区')
        df_out = df_out.dropna(subset=['预警类型', '预警等级'], how='all')

        debug.append(f"[填充] 后缀补全={suffix_count}, 空城市提取={extract_count}, "
                     f"省级兜底={province_fill_count}, 未知={unknown_count}")
        debug.append(f"[完成] 有效记录: {len(df_out)} 条")
        sample = df_out['城市'].head(15).tolist()
        debug.append(f"[样例] {sample}")

        return df_out, latest_file, debug

    except Exception as e:
        debug.append(f"[异常] {str(e)}")
        import traceback
        debug.append(traceback.format_exc())
        return pd.DataFrame(), latest_file, debug
