# -*- coding: utf-8 -*-
"""本地/CI 预建历史数据 pickle 缓存（供 Streamlit 页面直接加载）"""
import sys, os, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from utils.excel_parser import get_all_historical_data

start = time.time()
print("[缓存构建] 开始解析最近15天历史 xlsx 文件...", flush=True)
df, debug = get_all_historical_data(max_days=15)
elapsed = time.time() - start

print(f"[缓存构建] 完成！耗时 {elapsed:.1f}s")
print(f"  记录数: {len(df)}")
if 'city' in df.columns:
    print(f"  城市数: {df['city'].nunique()}")
if 'datetime' in df.columns and len(df) > 0:
    print(f"  时间范围: {df['datetime'].min()} ~ {df['datetime'].max()}")

for line in debug[-8:]:
    print("  ", line)
