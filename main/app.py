# -*- coding: utf-8 -*-
"""
中国省会城市空气质量洞察 - Streamlit 主应用

数据源：
- 方式1：从 data_output/aqi/ 读取爬虫最新批次数据（默认）
- 方式2：用户手动上传 Excel 文件
"""

import streamlit as st
import os
import sys

# ==================== 路径设置 ====================
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# ==================== 页面全局配置 ====================
st.set_page_config(
    page_title="中国省会城市空气质量洞察",
    page_icon="🌏",
    layout="wide"
)

# ==================== 主界面 ====================
st.title("🌏 中国省会城市空气质量实时监测与历史分析")
st.markdown("---")

# ==================== 侧边栏 ====================
with st.sidebar:
    st.header("📊 数据状态")

    # --- 数据源选择 ---
    st.markdown("**数据源**")
    data_source = st.radio(
        "选择数据来源",
        options=["使用爬虫最新数据", "手动上传Excel文件"],
        index=0,
        key="data_source_select"
    )

    # --- 上传组件（仅在选择"手动上传"时显示） ---
    if data_source == "手动上传Excel文件":
        uploaded_file = st.file_uploader(
            "请上传 AQI 数据 Excel 文件",
            type=["xlsx", "xls"],
            key="aqi_uploader"
        )
        if uploaded_file:
            st.session_state['uploaded_file'] = uploaded_file
            st.success(f"已加载文件：{uploaded_file.name}")
        else:
            st.session_state.pop('uploaded_file', None)
    else:
        st.session_state.pop('uploaded_file', None)
        st.info("将从 data_output/aqi/ 读取最新批次数据")

    # --- 分隔线 ---
    st.markdown("---")

    # --- 数据状态信息 ---
    if data_source == "使用爬虫最新数据":
        # 检查数据目录是否存在
        data_dir = os.path.normpath(os.path.join(current_dir, 'data_output', 'aqi'))
        if os.path.exists(data_dir):
            import glob
            subdirs = glob.glob(os.path.join(data_dir, '*'))
            batch_count = len([d for d in subdirs if os.path.isdir(d)])
            if batch_count > 0:
                st.success(f"已检测到 {batch_count} 个数据批次")
            else:
                st.warning("数据目录为空，请先运行爬虫")
        else:
            st.warning("数据目录不存在，请先运行爬虫创建数据")
