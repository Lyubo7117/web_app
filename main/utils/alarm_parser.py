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
    从 data_output/alarms/ 目录中获取最新的预警 Excel 文件并解析。

    查找逻辑：
      1. 优先使用 os.getcwd() + main/data_output/alarms/（适配 Streamlit Cloud）
      2. 回退到相对于当前文件的路径（适配本地运行）
      3. 筛选以 "全国预警信息_" 开头的 .xlsx 文件
      4. 按修改时间排序取最新，header=2 跳过标题行

    Parameters
    ----------
    data_folder : str, optional
        预警数据目录路径，默认 None 自动定位

    Returns
    -------
    tuple: (pd.DataFrame, str, list)
        - df: 包含 [省份, 城市, 预警类型, 预警等级, 发布时间, 解除时间] 的 DataFrame
        - latest_file: 最新文件路径（无文件时为 None）
        - debug_info: 调试信息列表
    """
    debug = []
    debug.append("=" * 50)
    debug.append("[开始] get_latest_alarms 执行")
    debug.append(f"[路径] os.getcwd() = {os.getcwd()}")

    # ---- 双路径策略定位数据目录 ----
    if data_folder is None:
        # 策略1：基于当前工作目录（Streamlit Cloud 工作目录为仓库根）
        cwd_based = os.path.join(os.getcwd(), 'main', 'data_output', 'alarms')
        # 策略2：基于当前文件相对路径（本地运行备用）
        fallback_dir = os.path.join(os.path.dirname(__file__), '..', 'data_output', 'alarms')

        debug.append(f"[路径] 策略1(工作目录) = {cwd_based}")
        debug.append(f"[路径] 策略2(文件相对) = {os.path.normpath(fallback_dir)}")

        if os.path.exists(cwd_based):
            data_folder = cwd_based
        elif os.path.exists(fallback_dir):
            data_folder = fallback_dir
        else:
            data_folder = cwd_based  # 保持策略1，后续报"目录不存在"

    debug.append(f"[路径] 实际使用 = {data_folder}")
    debug.append(f"[路径] 目录是否存在 = {os.path.exists(data_folder)}")

    if not os.path.exists(data_folder):
        debug.append("[提示] 预警数据目录不存在，请确认 weather_alarm_crawler 已运行")
        debug.append("=" * 50)
        return pd.DataFrame(), None, debug

    # ---- 查找匹配文件 ----
    pattern = os.path.join(data_folder, '全国预警信息_*.xlsx')
    files = glob.glob(pattern)
    # 排除临时文件
    files = [f for f in files if not os.path.basename(f).startswith('~')]

    # 备用：递归搜索子目录
    if not files:
        files = glob.glob(os.path.join(data_folder, '**', '全国预警信息_*.xlsx'), recursive=True)
        files = [f for f in files if not os.path.basename(f).startswith('~')]

    debug.append(f"[统计] 匹配 '全国预警信息_*.xlsx' 的文件数 = {len(files)}")

    if not files:
        debug.append("[警告] 未找到预警 Excel 文件，请先运行 weather_alarm_crawler")
        debug.append("=" * 50)
        return pd.DataFrame(), None, debug

    # 按修改时间取最新
    latest_file = max(files, key=os.path.getmtime)
    debug.append(f"[文件] 最新文件 = {os.path.basename(latest_file)}")
    debug.append(f"[文件] 完整路径 = {latest_file}")

    try:
        # ---- 关键修复：header=2，跳过第1行大标题和第2行空白，第3行为列名 ----
        df = pd.read_excel(latest_file, header=2, engine='openpyxl')
        debug.append(f"[解析] 原始列数 = {len(df.columns)}，行数 = {len(df)}")

        # 清理列名（去除换行符、空格）
        df.columns = [str(c).replace('\n', '').replace('\r', '').strip() for c in df.columns]
        debug.append(f"[解析] 清理后列名 = {list(df.columns)}")

        # ---- 智能列名映射 ----
        REQUIRED_COLS = ['省份', '城市', '预警类型', '预警等级', '发布时间', '解除时间']
        col_found = {}
        for col in df.columns:
            col_s = str(col)
            if '省份' in col_s and '省份' not in col_found:
                col_found['省份'] = col_s
            elif '城市' in col_s and '城市' not in col_found:
                col_found['城市'] = col_s
            elif ('预警类型' in col_s or ('类型' in col_s and '预警' in col_s)) and '预警类型' not in col_found:
                col_found['预警类型'] = col_s
            elif ('预警等级' in col_s or ('等级' in col_s and '预警' in col_s)) and '预警等级' not in col_found:
                col_found['预警等级'] = col_s
            elif '发布时间' in col_s and '发布时间' not in col_found:
                col_found['发布时间'] = col_s
            elif '解除时间' in col_s and '解除时间' not in col_found:
                col_found['解除时间'] = col_s

        debug.append(f"[映射] 找到的列 = {col_found}")

        missing = [k for k in REQUIRED_COLS if k not in col_found]
        if missing:
            debug.append(f"[警告] 未找到列：{missing}，将用空值补充")
            for m in missing:
                df[m] = ''
                col_found[m] = m

        # 提取并重命名为标准列名
        df_clean = df[[col_found[k] for k in REQUIRED_COLS]].copy()
        df_clean.columns = REQUIRED_COLS

        # 删除省份和城市均为空的行
        df_clean = df_clean.dropna(subset=['省份', '城市'], how='all')
        # 删除值为 "nan" 字符串的行
        df_clean = df_clean[~(
            df_clean['省份'].astype(str).str.strip().isin(['', 'nan', 'None']) &
            df_clean['城市'].astype(str).str.strip().isin(['', 'nan', 'None'])
        )]

        debug.append(f"[完成] 有效预警记录 = {len(df_clean)} 条")
        debug.append("=" * 50)

        return df_clean, latest_file, debug

    except Exception as e:
        debug.append(f"[异常] {type(e).__name__}: {e}")
        debug.append("=" * 50)
        return pd.DataFrame(), latest_file, debug
