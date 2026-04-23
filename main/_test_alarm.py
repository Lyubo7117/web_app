# -*- coding: utf-8 -*-
"""Test realtime_alarm city extraction against real data"""
import sys, io, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, os.path.dirname(__file__))
from utils.realtime_alarm import _extract_location

test_cases = [
    ("云南省", None, "云南省气象台发布冰雹黄色预警信号"),
    ("新疆维吾尔自治区", "塔城", "新疆维吾尔自治区塔城地区气象台发布大风蓝色预警信号"),
    ("云南省", "玉溪", "云南省玉溪市澄江市气象台发布雷电黄色预警信号"),
    ("新疆维吾尔自治区", "塔城", "新疆维吾尔自治区塔城地区托里县气象台发布大风蓝色预警信号"),
    ("甘肃", "天水", "甘肃省天水市秦州区气象台发布大风蓝色预警信号"),
    ("云南", None, "云南省气象台发布雷电黄色预警信号"),
    ("新疆维吾尔自治区", "塔城", "新疆维吾尔自治区塔城地区气象台发布大风蓝色预警信号"),
    ("甘肃", "平凉", "甘肃省平凉市崆峒区气象台发布雷电黄色预警信号"),
    ("贵州", None, "贵州省气象台发布雷电黄色预警信号"),
    ("广西壮族自治区", "百色", "广西壮族自治区百色市西林县气象台发布大风黄色预警信号"),
    ("福建", "漳州", "福建省漳州市诏安县气象台发布雷电黄色预警信号"),
    ("河北", "衡水", "河北省衡水市深州市气象台发布大风蓝色预警信号"),
    ("贵州", None, "贵州省气象台发布雷雨强风黄色预警信号"),
    ("甘肃", "陇南", "甘肃省陇南市成县气象台发布雷电黄色预警信号"),
    ("辽宁", "铁岭", "辽宁省铁岭市昌图县气象台发布大风黄色预警信号"),
    ("云南", "曲靖", "云南省曲靖市陆良县气象台发布暴雨黄色预警信号"),
    ("福建", "漳州", "福建省漳州市南靖县气象台发布雷电黄色预警信号"),
    ("吉林", "延边", "吉林省延边朝鲜族自治州安图县气象台发布森林火险黄色预警信号"),
]

ok = fail = 0
for exp_prov, exp_city, title in test_cases:
    prov, city = _extract_location(title)
    
    # 宽松匹配省份
    if exp_prov:
        prov_ok = (exp_prov in str(prov)) if prov else False
    else:
        prov_ok = True
    
    # 宽松匹配城市
    if exp_city:
        city_ok = (exp_city in str(city)) if city else False
    else:
        city_ok = True  # 无预期城市时允许为空
    
    status = "[OK]" if (prov_ok and city_ok) else "[FAIL]"
    if prov_ok and city_ok: ok += 1
    else: fail += 1
    
    t_short = title[:50] + ".." if len(title) > 50 else title
    print(f"{status} prov={str(prov):<20} city={str(city):<10} | {t_short}")

print("")
print(f"Total: {ok}/{len(test_cases)} passed, {fail} failed")
