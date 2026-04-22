"""
alarm_parser.py
气象预警数据解析工具模块

用于从 data_output/alarms/ 目录中查找并解析 weather_alarm_crawler 生成的
预警 Excel 文件，返回标准化 DataFrame，供 Streamlit 页面直接使用。

纯数据处理模块，不依赖 streamlit。
"""

import os
import glob
import pandas as pd


# ==============================
# 标准列名定义
# ==============================
ALARM_COLUMNS = [
    'province', 'city', 'alarm_type', 'alarm_level',
    'publish_time', 'cancel_time'
]

# 原始 Excel 列名 → 标准列名的映射
_COLUMN_MAP = {
    '省份':     'province',
    '城市':     'city',
    '预警类型': 'alarm_type',
    '预警等级': 'alarm_level',
    '发布时间': 'publish_time',
    '解除时间': 'cancel_time',
    # 兼容可能的变体
    '发布日期': 'publish_time',
    '解除日期': 'cancel_time',
}


def get_latest_alarms(data_folder=None):
    """
    从 data_output/alarms/ 目录获取最新批次的气象预警数据。

    查找逻辑：
      1. 默认使用 main/data_output/alarms/ 目录
      2. 筛选以 "全国预警信息_" 开头的 .xlsx 文件
      3. 按修改时间排序，取最新的一个
      4. 使用 pandas 读取并映射为标准列名

    Parameters
    ----------
    data_folder : str, optional
        预警数据目录的绝对路径。
        默认为 None，自动定位到 main/data_output/alarms/

    Returns
    -------
    tuple: (pd.DataFrame, str, list)
        - df: 标准化后的预警 DataFrame（字段：省份、城市、预警类型、预警等级、发布时间、解除时间）
        - latest_file: 最新文件路径（无文件时为空字符串）
        - debug_info: 调试信息列表
    """
    debug_info = []
    empty_df = pd.DataFrame(columns=ALARM_COLUMNS)

    try:
        debug_info.append("=" * 50)
        debug_info.append("[开始] get_latest_alarms 执行")

        # ---- 确定数据目录 ----
        if data_folder is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            data_folder = os.path.join(base_dir, 'data_output', 'alarms')

        debug_info.append(f"[路径] 数据目录 = {data_folder}")
        debug_info.append(f"[路径] 目录是否存在 = {os.path.exists(data_folder)}")

        if not os.path.exists(data_folder):
            debug_info.append("[提示] 预警数据目录不存在，请确认 weather_alarm_crawler 已运行")
            debug_info.append("=" * 50)
            return empty_df, '', debug_info

        # ---- 查找匹配的 xlsx 文件 ----
        all_xlsx = glob.glob(os.path.join(data_folder, '**', '*.xlsx'), recursive=True)
        # 排除临时文件
        all_xlsx = [f for f in all_xlsx if not os.path.basename(f).startswith('~')]
        # 只保留以 "全国预警信息_" 开头的文件
        matched_files = [
            f for f in all_xlsx
            if os.path.basename(f).startswith('全国预警信息_')
        ]

        debug_info.append(f"[统计] 目录下共 {len(all_xlsx)} 个 xlsx 文件")
        debug_info.append(f"[统计] 匹配 '全国预警信息_' 前缀的文件 = {len(matched_files)}")

        if not matched_files:
            debug_info.append("[提示] 没有找到以 '全国预警信息_' 开头的 xlsx 文件，请先运行 weather_alarm_crawler")
            debug_info.append("=" * 50)
            return empty_df, '', debug_info

        # 按修改时间倒序，取最新的
        matched_files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
        latest_file = matched_files[0]
        debug_info.append(f"[文件] 最新文件 = {os.path.basename(latest_file)}")
        debug_info.append(f"[文件] 完整路径 = {latest_file}")

        # ---- 读取 Excel ----
        df = pd.read_excel(latest_file, engine='openpyxl')

        if df.empty:
            debug_info.append("[警告] Excel 文件内容为空")
            debug_info.append("=" * 50)
            return empty_df, latest_file, debug_info

        debug_info.append(f"[解析] 原始列名 = {list(df.columns)}")
        debug_info.append(f"[解析] 原始行数 = {len(df)}")

        # ---- 列名映射 ----
        df.rename(columns=_COLUMN_MAP, inplace=True)

        # 只保留标准列（存在的才留）
        existing_cols = [c for c in ALARM_COLUMNS if c in df.columns]
        df = df[existing_cols]

        # 如果原始数据没有"省份"列，提示一下
        if 'province' not in df.columns and 'city' in df.columns:
            debug_info.append("[提示] 原始数据无'省份'列，省份字段将留空")

        debug_info.append(f"[完成] 解析到 {len(df)} 条预警记录，实际列名 = {list(df.columns)}")
        debug_info.append("=" * 50)

        return df, latest_file, debug_info

    except Exception as e:
        debug_info.append(f"[异常] {type(e).__name__}: {e}")
        debug_info.append("=" * 50)
        return empty_df, '', debug_info
