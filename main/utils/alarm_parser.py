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
    从 data_output/alarms/ 目录中获取最新的预警Excel文件并解析。
    使用 openpyxl 直接读取原始单元格，绕过 pandas 自动表头识别。
    Excel结构：第1行大标题，第2行元数据，第3行列名，第4行起数据。
    返回 (DataFrame, latest_file, debug_info)
    """
    import re
    import traceback
    from openpyxl import load_workbook

    debug = []
    debug.append("[开始] get_latest_alarms 执行")

    # 路径定位（双路径策略）
    base_dir = os.path.join(os.getcwd(), 'main', 'data_output', 'alarms')
    fallback_dir = os.path.join(os.path.dirname(__file__), '..', 'data_output', 'alarms')

    if data_folder is None:
        if os.path.exists(base_dir):
            alarm_dir = base_dir
            debug.append(f"[路径] 使用工作目录: {alarm_dir}")
        elif os.path.exists(fallback_dir):
            alarm_dir = fallback_dir
            debug.append(f"[路径] 使用备用相对路径: {alarm_dir}")
        else:
            debug.append(f"[路径] 目录不存在: {base_dir} 和 {os.path.normpath(fallback_dir)}")
            return pd.DataFrame(), None, debug
    else:
        alarm_dir = data_folder

    debug.append(f"[路径] 实际使用: {alarm_dir}")
    debug.append(f"[路径] 目录是否存在: {os.path.exists(alarm_dir)}")

    # 查找匹配的Excel文件
    pattern = os.path.join(alarm_dir, '全国预警信息_*.xlsx')
    files = glob.glob(pattern)
    files = [f for f in files if not os.path.basename(f).startswith('~')]

    # 备用：递归搜索子目录
    if not files:
        files = glob.glob(os.path.join(alarm_dir, '**', '全国预警信息_*.xlsx'), recursive=True)
        files = [f for f in files if not os.path.basename(f).startswith('~')]

    debug.append(f"[统计] 匹配 '全国预警信息_*.xlsx' 的文件数: {len(files)}")

    if not files:
        debug.append("[警告] 未找到预警Excel文件")
        return pd.DataFrame(), None, debug

    latest_file = max(files, key=os.path.getmtime)
    debug.append(f"[文件] 最新文件: {os.path.basename(latest_file)}")
    debug.append(f"[文件] 完整路径: {latest_file}")

    try:
        # 使用 openpyxl 直接读取，绕过 pandas 的自动解析
        wb = load_workbook(latest_file, data_only=True)
        ws = wb.active

        # 获取所有行数据
        rows = list(ws.iter_rows(values_only=True))
        if len(rows) < 4:
            debug.append("[错误] Excel 行数不足4行，无法解析")
            return pd.DataFrame(), latest_file, debug

        # 根据实际观察：
        # 第1行：大标题（忽略）
        # 第2行：爬取时间等元数据（忽略）
        # 第3行：真正的列名
        # 第4行开始：数据
        header_row = rows[2]
        data_rows = rows[3:]

        # 清理单元格值
        def clean_val(v):
            if v is None:
                return ''
            return re.sub(r'[\s\n\r]+', '', str(v)).strip()

        columns = [clean_val(c) for c in header_row]
        debug.append(f"[解析] 提取到的列名: {columns[:10]}")

        # 构建 DataFrame
        df = pd.DataFrame(data_rows, columns=columns)
        # 删除全空行
        df = df.dropna(how='all')
        debug.append(f"[解析] 数据行数: {len(df)}")

        # 智能映射需要的列（根据列名中的关键词）
        required = ['省份', '城市', '预警类型', '预警等级', '发布时间', '解除时间']
        col_map = {}
        for req in required:
            for col in df.columns:
                if req in col:
                    col_map[req] = col
                    break

        if len(col_map) == len(required):
            df_out = df[[col_map[r] for r in required]].copy()
            df_out.columns = required
            # 删除省份、城市均为空的行
            df_out = df_out.dropna(subset=['省份', '城市'], how='all')
            debug.append(f"[完成] 解析到 {len(df_out)} 条有效预警记录")
            return df_out, latest_file, debug
        else:
            # 后备：按位置提取前6列
            debug.append(f"[警告] 列名映射失败，使用位置提取。找到的列: {col_map}")
            if len(df.columns) >= 6:
                df_out = df.iloc[:, :6].copy()
                df_out.columns = required
                df_out = df_out.dropna(subset=['省份', '城市'], how='all')
                debug.append(f"[完成] 按位置提取到 {len(df_out)} 条记录")
                return df_out, latest_file, debug
            else:
                debug.append("[错误] 列数不足6，无法提取")
                return pd.DataFrame(), latest_file, debug

    except Exception as e:
        debug.append(f"[异常] {str(e)}")
        debug.append(traceback.format_exc())
        return pd.DataFrame(), latest_file, debug
