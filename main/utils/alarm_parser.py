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
    header=1 读取（第1行大标题，第2行列名），含按位置提取后备方案。
    返回 (DataFrame, latest_file, debug_info)
    """
    import re
    import traceback

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
        # 关键：第二行为列名 (header=1)，第一行是大标题合并单元格
        df = pd.read_excel(latest_file, header=1, engine='openpyxl')
        debug.append(f"[解析] 使用header=1，原始列名: {list(df.columns)[:8]}")

        # 清理列名（去除空格和换行）
        def clean_col(col):
            if pd.isna(col):
                return ''
            return re.sub(r'[\s\n\r]+', '', str(col))
        df.columns = [clean_col(c) for c in df.columns]
        debug.append(f"[解析] 清理后列名: {list(df.columns)}")

        # 删除全空行
        df = df.dropna(how='all')
        # 如果第一行仍然是标题残留（不包含"省份"），跳过
        if len(df) > 0 and '省份' not in str(df.iloc[0].values):
            df = df.iloc[1:]

        debug.append(f"[解析] 最终数据行数: {len(df)}")

        # 检查必要列
        required = ['省份', '城市', '预警类型', '预警等级', '发布时间', '解除时间']
        found_cols = [c for c in df.columns if any(r in c for r in required)]
        debug.append(f"[映射] 找到的相关列: {found_cols}")

        if all(any(r in c for c in df.columns) for r in required):
            col_mapping = {}
            for req in required:
                for col in df.columns:
                    if req in col:
                        col_mapping[req] = col
                        break
            df_out = df[[col_mapping[r] for r in required]].copy()
            df_out.columns = required
            # 删除省份和城市均为空的无效行
            df_out = df_out.dropna(subset=['省份', '城市'], how='all')
            debug.append(f"[完成] 解析到 {len(df_out)} 条预警记录")
            return df_out, latest_file, debug
        else:
            # 后备：按位置提取前6列
            if len(df.columns) >= 6:
                df_out = df.iloc[:, :6].copy()
                df_out.columns = required
                debug.append(f"[后备] 按位置提取前6列，得到 {len(df_out)} 条记录")
                return df_out, latest_file, debug
            else:
                debug.append("[错误] 无法解析列名，且列数不足6")
                return pd.DataFrame(), latest_file, debug

    except Exception as e:
        debug.append(f"[异常] {str(e)}")
        debug.append(traceback.format_exc())
        return pd.DataFrame(), latest_file, debug
