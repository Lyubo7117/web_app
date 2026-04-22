"""
4_气象预警.py
Streamlit 多页面应用 — 气象预警监测页面

功能：
- 加载 weather_alarm_crawler 生成的最新预警 Excel 数据
- 展示预警总数、按等级分布统计
- 支持按省份筛选的预警列表
- 调试信息面板
"""

import streamlit as st
import pandas as pd
import sys
import os

# 确保可以导入 utils
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# 安全导入 alarm_parser，失败时给出提示
try:
    from utils.alarm_parser import get_latest_alarms
except ImportError as e:
    st.error(f"无法导入预警数据解析模块：{e}")
    st.info("请确认 web_app/main/utils/alarm_parser.py 文件存在。")
    st.stop()


# ==============================
# 页面标题
# ==============================
st.title("🚨 全国气象预警实时监测")


# ==============================
# 加载数据
# ==============================
@st.cache_data(ttl=600)
def _load_alarm_data():
    """加载最新预警数据，返回 (df, file_path, debug_info)。"""
    try:
        return get_latest_alarms()
    except Exception as e:
        st.error(f"加载预警数据时出错：{type(e).__name__}: {e}")
        return pd.DataFrame(), '', [f"[异常] {type(e).__name__}: {e}"]


df, file_path, debug_info = _load_alarm_data()


# ==============================
# 调试信息面板（可折叠）
# ==============================
with st.expander("🔍 调试信息（排查用）", expanded=False):
    for line in debug_info:
        st.text(line)


# ==============================
# 空数据判断
# ==============================
if df.empty:
    st.warning("当前没有生效的气象预警")
    st.info("预警数据来自 weather_alarm_crawler，请确认爬虫已运行并生成数据。")
    st.stop()


# ==============================
# 数据更新时间
# ==============================
if 'publish_time' in df.columns and not df['publish_time'].empty:
    try:
        update_time = pd.to_datetime(df['publish_time']).max()
        st.markdown(f"**📡 数据时间：** {update_time}")
    except Exception:
        st.markdown(f"**📡 数据文件：** {os.path.basename(file_path) if file_path else '未知'}")
else:
    st.markdown(f"**📡 数据文件：** {os.path.basename(file_path) if file_path else '未知'}")


# ==============================
# 预警总数
# ==============================
st.metric(label="预警总数", value=len(df))


# ==============================
# 按预警等级分组统计
# ==============================
if 'alarm_level' in df.columns:
    level_counts = df['alarm_level'].value_counts()

    # 按优先级排序：红 > 橙 > 黄 > 蓝 > 其他
    priority = {'红色': 0, '橙色': 1, '黄色': 2, '蓝色': 3}
    sorted_levels = sorted(
        level_counts.index.tolist(),
        key=lambda x: priority.get(str(x), 99)
    )

    # 等级对应 emoji 和颜色
    level_style = {
        '红色': ('🔴', '#ff0000'),
        '橙色': ('🟠', '#ff7e00'),
        '黄色': ('🟡', '#ffff00'),
        '蓝色': ('🔵', '#4488ff'),
    }

    cols = st.columns(min(len(sorted_levels), 4))
    for i, level in enumerate(sorted_levels):
        emoji = level_style.get(str(level), ('⚪', '#888'))[0]
        count = int(level_counts[level])
        with cols[i]:
            st.metric(label=f"{emoji} {level}预警", value=count)
else:
    st.info("数据中未找到 'alarm_level' 列，无法按等级统计。")


# ==============================
# 按省份筛选
# ==============================
if 'province' in df.columns and df['province'].nunique() > 1:
    all_provinces = sorted(df['province'].dropna().unique().tolist())
    selected = st.multiselect(
        label="🏢 按省份筛选",
        options=all_provinces,
        default=all_provinces,
        key="province_filter"
    )
    df_filtered = df[df['province'].isin(selected)]
else:
    df_filtered = df


# ==============================
# 完整预警表格
# ==============================
st.subheader("📋 预警详情")

# 优先展示的列
display_cols = [c for c in ['province', 'city', 'alarm_type', 'alarm_level', 'publish_time', 'cancel_time']
                if c in df_filtered.columns]

# 中文列名映射
col_rename = {
    'province': '省份',
    'city': '城市',
    'alarm_type': '预警类型',
    'alarm_level': '预警等级',
    'publish_time': '发布时间',
    'cancel_time': '解除时间',
}

if display_cols:
    df_display = df_filtered[display_cols].copy()
    df_display.rename(columns=col_rename, inplace=True)
    df_display.reset_index(drop=True, inplace=True)
    st.dataframe(df_display, use_container_width=True, height=400)
else:
    st.dataframe(df_filtered, use_container_width=True, height=400)
