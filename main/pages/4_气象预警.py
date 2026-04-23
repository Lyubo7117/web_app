"""
4_气象预警.py
Streamlit 多页面应用 — 气象预警监测页面

功能：
- 加载 weather_alarm_crawler 生成的最新预警 Excel 数据
- 展示预警总数、按等级分布统计
- 支持按省份筛选的预警列表
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
# 蓝色主题 CSS
# ==============================
st.markdown("""
<style>
    .stApp {
        background: linear-gradient(135deg, #f0f8ff 0%, #e6f2ff 100%);
    }
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1a365d 0%, #0f2440 100%);
    }
    section[data-testid="stSidebar"] * {
        color: #ffffff !important;
    }
    section[data-testid="stSidebar"] button {
        background: #2b6cb0 !important;
        color: white !important;
        border-radius: 8px !important;
    }
    h1, h2, h3 {
        color: #0a2540 !important;
        font-weight: 600 !important;
    }
    div[data-testid="stMetric"] {
        background: white;
        border-radius: 12px;
        padding: 16px;
        box-shadow: 0 2px 8px rgba(0, 49, 102, 0.1);
        border: 1px solid #cce0ff;
    }
    div[data-testid="stDataFrame"] {
        border-radius: 10px;
        overflow: hidden;
        border: 1px solid #cce0ff;
    }
    div[data-testid="stDataFrame"] th {
        background: #1e4d8c !important;
        color: white !important;
        font-weight: 600 !important;
    }
    div[data-testid="stDataFrame"] td {
        background: white !important;
    }
    .stAlert {
        border-radius: 10px;
        border-left: 4px solid #2b6cb0;
    }
</style>
""", unsafe_allow_html=True)


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
# 空数据判断
# ==============================
if df.empty:
    st.warning("当前没有生效的气象预警")
    st.info("预警数据来自 weather_alarm_crawler，请确认爬虫已运行并生成数据。")
    st.stop()


# ==============================
# 统一列名：兼容中文列名（新版）和英文列名（旧版）
# ==============================
# alarm_parser 最终版返回中文列名，旧版返回英文列名
# 这里统一转换为中文，方便后续处理
_en_to_zh = {
    'province': '省份',
    'city': '城市',
    'alarm_type': '预警类型',
    'alarm_level': '预警等级',
    'publish_time': '发布时间',
    'cancel_time': '解除时间',
}
df = df.rename(columns={k: v for k, v in _en_to_zh.items() if k in df.columns})

# 标准中文列名
DISPLAY_COLUMNS = ['省份', '城市', '预警类型', '预警等级', '发布时间', '解除时间']


# ==============================
# 数据更新时间
# ==============================
time_col = '发布时间' if '发布时间' in df.columns else None
if time_col and not df[time_col].empty:
    try:
        update_time = pd.to_datetime(df[time_col]).max()
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
level_col = '预警等级' if '预警等级' in df.columns else None
if level_col:
    level_counts = df[level_col].value_counts()

    # 按优先级排序：红 > 橙 > 黄 > 蓝 > 其他
    priority = {'红色': 0, '橙色': 1, '黄色': 2, '蓝色': 3}
    sorted_levels = sorted(
        level_counts.index.tolist(),
        key=lambda x: priority.get(str(x), 99)
    )

    # 等级对应 emoji
    level_style = {
        '红色': '🔴',
        '橙色': '🟠',
        '黄色': '🟡',
        '蓝色': '🔵',
    }

    cols = st.columns(min(len(sorted_levels), 4))
    for i, level in enumerate(sorted_levels):
        emoji = level_style.get(str(level), '⚪')
        count = int(level_counts[level])
        with cols[i]:
            st.metric(label=f"{emoji} {level}预警", value=count)
else:
    st.info("数据中未找到预警等级列，无法按等级统计。")


# ==============================
# 按省份筛选
# ==============================
province_col = '省份' if '省份' in df.columns else None
if province_col and df[province_col].nunique() > 1:
    all_provinces = sorted(df[province_col].dropna().unique().tolist())
    selected = st.multiselect(
        label="🏢 按省份筛选",
        options=all_provinces,
        default=all_provinces,
        key="province_filter"
    )
    df_filtered = df[df[province_col].isin(selected)]
else:
    df_filtered = df


# ==============================
# 完整预警表格
# ==============================
st.subheader("📋 预警详情")

# 只显示需要的列
display_columns = ['省份', '城市', '预警类型', '预警等级', '发布时间', '解除时间']
if all(col in df_filtered.columns for col in display_columns):
    df_display = df_filtered[display_columns].reset_index(drop=True)
    st.dataframe(df_display, use_container_width=True, height=400)
else:
    st.warning("表格列名不完整，实际列名：" + str(list(df_filtered.columns)))
    st.dataframe(df_filtered, use_container_width=True, height=400)


# ==============================
# 制作人信息
# ==============================
st.markdown("---")
st.caption("👨‍💻 制作人：刘宇博 · 江毅 · 张睿 ｜ 大数据与人工智能导论课程项目")
