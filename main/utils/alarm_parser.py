# -*- coding: utf-8 -*-
"""预警数据解析模块 - 修复城市名空白"""

import pandas as pd
import glob
import os
import re
from openpyxl import load_workbook

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
    # 备用：递归搜索子目录
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

        # 第三行是列名，第四行起是数据
        header = [str(c).strip() if c else '' for c in rows[2]]
        data_rows = rows[3:]
        df = pd.DataFrame(data_rows, columns=header)
        df = df.dropna(how='all')
        debug.append(f"[解析] 原始行数: {len(df)}, 列名: {header[:8]}")

        # 清理列名（去除换行符和空格）
        def clean_col(col):
            return re.sub(r'[\s\n\r]+', '', str(col))
        df.columns = [clean_col(c) for c in df.columns]

        required = ['省份', '城市', '预警类型', '预警等级', '发布时间', '解除时间']
        col_map = {}
        for req in required:
            for col in df.columns:
                if req in col:
                    col_map[req] = col
                    break

        if len(col_map) != len(required):
            debug.append(f"[警告] 列名映射不全，实际映射: {col_map}，尝试按位置提取")
            if len(df.columns) >= 6:
                df_out = df.iloc[:, :6].copy()
                df_out.columns = required
            else:
                return pd.DataFrame(), latest_file, debug
        else:
            df_out = df[[col_map[req] for req in required]].copy()
            df_out.columns = required

        # ======== 关键修复：强制填充空白城市名 ========
        df_out['省份'] = df_out['省份'].fillna('').astype(str).str.strip()
        df_out['城市'] = df_out['城市'].fillna('').astype(str).str.strip()

        # 如果"城市"列为空，则用"省份（省级预警）"填充
        df_out['城市'] = df_out.apply(
            lambda row: row['城市'] if row['城市'] != '' else f"{row['省份']}（省级预警）",
            axis=1
        )
        # 如果连省份都为空，标记为"未知地区"
        df_out['省份'] = df_out['省份'].replace('', '未知地区')
        df_out['城市'] = df_out['城市'].replace('', '未知地区')

        df_out = df_out.dropna(subset=['预警类型', '预警等级'], how='all')
        debug.append(f"[完成] 有效记录: {len(df_out)} 条")
        return df_out, latest_file, debug

    except Exception as e:
        debug.append(f"[异常] {str(e)}")
        return pd.DataFrame(), latest_file, debug
