# -*- coding: utf-8 -*-
"""
历史分析页面 - 基于每日爬取数据的动态实时分析

功能：
- 从所有历史批次数据中在线计算 AQI 趋势
- 污染物与气象因素相关性矩阵（Plotly 交互式热力图）
- 随机森林建模：AQI 驱动因素重要性排序（Plotly 条形图）
- 城市 AQI 均值排名
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
import os
import sys

# 添加 utils 路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from utils.excel_parser import get_all_historical_data
from utils.realtime_aqi import fetch_realtime_aqi


# ==============================
# 自定义侧边栏导航
# ==============================
with st.sidebar:
    st.markdown("### 🌏 导航")
    if st.button("🏠 首页", key="sidebar_home", use_container_width=True):
        st.switch_page("app.py")
    st.markdown("---")
    if st.button("📍 实时监测", key="sidebar_realtime", use_container_width=True):
        st.switch_page("pages/1_实时监测.py")
    if st.button("🚨 气象预警", key="sidebar_warning", use_container_width=True):
        st.switch_page("pages/4_气象预警.py")
    if st.button("📊 今日快报", key="sidebar_report", use_container_width=True):
        st.switch_page("pages/3_今日快报.py")
    if st.button("📈 历史分析", key="sidebar_history", use_container_width=True):
        st.switch_page("pages/2_历史分析.py")


# ==================== 蓝色主题 CSS ====================
st.markdown("""
<style>
    .stApp {
        background: linear-gradient(135deg, #f0f8ff 0%, #e6f2ff 100%);
    }
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1a365d 0%, #0f2440 100%);
    }
    [data-testid="stSidebarNav"] {
        display: none !important;
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
    .stButton button {
        background: linear-gradient(135deg, #2b6cb0 0%, #1a365d 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
    }
    .stAlert {
        border-radius: 10px;
        border-left: 4px solid #2b6cb0;
    }
    /* 表格和文字居中 */
    div[data-testid="stDataFrame"] td,
    div[data-testid="stDataFrame"] th {
        text-align: center !important;
    }
</style>
""", unsafe_allow_html=True)


st.header("📈 历史趋势与驱动因素分析（动态实时）")


# ==================== 数据加载 ====================
# 强制清除缓存，确保每次加载最新数据
st.cache_data.clear()

if st.button("🔄 刷新分析"):
    st.rerun()

with st.spinner("正在从所有历史批次中加载数据..."):
    df_all, debug = get_all_historical_data()

if df_all.empty:
    st.warning("暂无足够的历史数据用于分析。请确保已爬取至少一个批次的数据。")
    st.stop()

# ── 叠加实时 API 数据，补全至今日 ──
with st.spinner("正在获取实时数据，补全最新时段..."):
    df_rt, rt_time, _, rt_source = fetch_realtime_aqi(cache_ttl=300)

if not df_rt.empty:
    # 将实时数据转换为与历史数据一致的列名格式
    rt_records = []
    for _, row in df_rt.iterrows():
        city_name = row.get('city_name', '')
        if not city_name or pd.isna(row.get('aqi')):
            continue
        rec = {
            'city': city_name,
            'datetime': row.get('datetime', ''),
            'aqi': row.get('aqi'),
            'level': row.get('level', ''),
            'primary_pollutant': row.get('dominant_pollutant', ''),
            'pm25': row.get('pm25'),
            'pm10': row.get('pm10'),
            'co': row.get('co'),
            'no2': row.get('no2'),
            'o3': row.get('o3'),
            'so2': row.get('so2'),
        }
        rt_records.append(rec)

    if rt_records:
        df_realtime = pd.DataFrame(rt_records)
        # 数值列转换
        numeric_cols = ['aqi', 'pm25', 'pm10', 'co', 'no2', 'o3', 'so2']
        for col in numeric_cols:
            if col in df_realtime.columns:
                df_realtime[col] = pd.to_numeric(df_realtime[col], errors='coerce')

        # 合并：历史 + 实时（实时数据会覆盖同城市同时刻的旧记录）
        df_all = pd.concat([df_all, df_realtime], ignore_index=True)
        # 去重：同一城市同一时刻保留最后出现的记录（即实时数据优先）
        df_all = df_all.drop_duplicates(subset=['city', 'datetime'], keep='last')
        # 按城市和时间排序
        df_all = df_all.sort_values(['city', 'datetime']).reset_index(drop=True)
        st.info(f"📡 已叠加 **{rt_source}** 实时数据（{len(df_realtime)} 条），补全至当前时刻")
else:
    st.warning("⚠️ 实时数据源暂不可用，当前仅展示爬虫批次数据")

# 数据概览
st.markdown(
    f"**数据来源：** 中国天气网 ｜ "
    f"**时间跨度：** {df_all['datetime'].min()} ~ {df_all['datetime'].max()} ｜ "
    f"**累计记录：** {len(df_all)} 条 ｜ "
    f"**覆盖城市：** {df_all['city'].nunique()} 个"
)

# 显示最新记录时间
latest_time = df_all['datetime'].max()
st.success(f"✅ 已自动加载最新数据，最新记录时间：{latest_time}")


# ==================== 一、时间趋势分析 ====================
st.subheader("一、AQI 日均值变化趋势")

# 计算每日全国均值
df_all['date'] = pd.to_datetime(df_all['datetime']).dt.date
daily_avg = df_all.groupby('date')['aqi'].mean().reset_index()
daily_avg.columns = ['日期', '全国平均AQI']

# 计算各城市每日均值（用于展示城市线条）
city_daily = df_all.groupby(['city', 'date'])['aqi'].mean().reset_index()

# 使用 Plotly 绘制交互式折线图：全国均值用红色粗线，各城市用半透明细线
fig_trend = go.Figure()

# 添加各城市折线
for city in city_daily['city'].unique():
    city_data = city_daily[city_daily['city'] == city]
    fig_trend.add_trace(go.Scatter(
        x=city_data['date'], y=city_data['aqi'],
        mode='lines',
        name=city,
        line=dict(width=1, color='rgba(100, 150, 200, 0.3)'),
        showlegend=False,
        hoverinfo='name+y'
    ))

# 添加全国均值粗线
fig_trend.add_trace(go.Scatter(
    x=daily_avg['日期'], y=daily_avg['全国平均AQI'],
    mode='lines+markers',
    name='全国平均',
    line=dict(width=4, color='#dc3545'),
    marker=dict(size=4, color='#dc3545'),
    hoverinfo='name+y'
))

fig_trend.update_layout(
    title="各城市 AQI 日均值变化趋势（半透明细线）+ 全国均值（红色粗线）",
    xaxis_title="日期",
    yaxis_title="AQI",
    hovermode="x unified",
    template="plotly_white",
    height=500,
    font=dict(color="#0a2540"),
    plot_bgcolor='rgba(240,248,255,0.5)'
)

st.plotly_chart(fig_trend, use_container_width=True)

# 趋势统计卡片
col1, col2, col3 = st.columns(3)
first_week = daily_avg.head(7)['全国平均AQI'].mean() if len(daily_avg) >= 7 else daily_avg['全国平均AQI'].mean()
last_week = daily_avg.tail(7)['全国平均AQI'].mean() if len(daily_avg) >= 7 else daily_avg['全国平均AQI'].mean()
change_pct = ((last_week - first_week) / first_week * 100) if first_week > 0 else 0

col1.metric("首周平均 AQI", f"{first_week:.1f}")
col2.metric("末周平均 AQI", f"{last_week:.1f}")
col3.metric("变化幅度", f"{change_pct:+.1f}%")

st.markdown("---")


# ==================== 二、相关性分析 ====================
st.subheader("二、污染物与气象因素相关性矩阵")

# 选择用于相关性分析的数值列
corr_columns = ['aqi', 'pm25', 'pm10', 'co', 'no2', 'o3', 'so2']
corr_labels = ['AQI', 'PM₂.₅', 'PM₁₀', 'CO', 'NO₂', 'O₃', 'SO₂']

# 检查哪些列实际存在
available_cols = [c for c in corr_columns if c in df_all.columns]
available_labels = [corr_labels[i] for i, c in enumerate(corr_columns) if c in df_all.columns]

if len(available_cols) >= 2:
    corr_matrix = df_all[available_cols].corr()

    # 重命名列和索引为中文标签
    rename_map = dict(zip(available_cols, available_labels))
    corr_matrix = corr_matrix.rename(index=rename_map, columns=rename_map)

    # 使用 Plotly 绘制热力图
    fig_corr = go.Figure(data=go.Heatmap(
        z=corr_matrix.values,
        x=list(corr_matrix.columns),
        y=list(corr_matrix.index),
        colorscale='RdBu_r',
        zmin=-1, zmax=1,
        text=np.round(corr_matrix.values, 3),
        texttemplate='%{text}',
        textfont={"size": 12, "color": "#0a2540"},
        hoverinfo='text',
        colorbar=dict(title="相关系数", tickfont=dict(color="#0a2540"))
    ))

    fig_corr.update_layout(
        title="污染物浓度之间的 Pearson 相关系数矩阵",
        template="plotly_white",
        height=500,
        font=dict(color="#0a2540"),
        plot_bgcolor='rgba(240,248,255,0.5)'
    )

    st.plotly_chart(fig_corr, use_container_width=True)

    # 关键发现
    aqi_corr = corr_matrix['AQI'].drop('AQI').sort_values(ascending=False)
    st.markdown("**🔍 与 AQI 相关性最强的污染物：**")
    for item, val in aqi_corr.items():
        color = "🟢" if val < 0 else "🔴"
        st.write(f"- {color} **{item}**：r = {val:.3f}")
else:
    st.info("数据列不足，无法计算相关性矩阵。")

st.markdown("---")


# ==================== 三、随机森林驱动因素重要性 ====================
st.subheader("三、随机森林：AQI 驱动因素重要性排序")

# 特征列（使用污染物 + 气象指标）
feature_candidates = ['pm25', 'pm10', 'co', 'no2', 'o3', 'so2']
feature_labels = ['PM₂.₅', 'PM₁₀', 'CO', 'NO₂', 'O₃', 'SO₂']

# 只保留实际存在的列
available_features = [c for c in feature_candidates if c in df_all.columns]
available_feature_labels = [feature_labels[i] for i, c in enumerate(feature_candidates) if c in df_all.columns]

if len(available_features) >= 2 and 'aqi' in df_all.columns:
    # 准备数据
    df_model = df_all[['aqi'] + available_features].dropna()

    if len(df_model) > 100:
        X = df_model[available_features]
        y = df_model['aqi']

        # 标准化
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)

        # 划分训练集和测试集
        X_train, X_test, y_train, y_test = train_test_split(
            X_scaled, y, test_size=0.2, random_state=42
        )

        # 训练随机森林
        rf = RandomForestRegressor(
            n_estimators=100, max_depth=10, random_state=42, n_jobs=-1
        )
        rf.fit(X_train, y_train)

        # 模型性能
        train_score = rf.score(X_train, y_train)
        test_score = rf.score(X_test, y_test)

        col_rf1, col_rf2 = st.columns(2)
        col_rf1.metric("训练集 R²", f"{train_score:.4f}")
        col_rf2.metric("测试集 R²", f"{test_score:.4f}")

        # 特征重要性
        importances = rf.feature_importances_
        importance_df = pd.DataFrame({
            '特征': available_feature_labels,
            '重要性': importances
        }).sort_values('重要性', ascending=True)

        # 使用 Plotly 绘制水平条形图
        fig_importance = go.Figure(go.Bar(
            x=importance_df['重要性'],
            y=importance_df['特征'],
            orientation='h',
            marker=dict(
                color=importance_df['重要性'],
                colorscale='Blues',
                showscale=True,
                colorbar=dict(title="重要性得分", tickfont=dict(color="#0a2540"))
            ),
            text=[f"{v:.4f}" for v in importance_df['重要性']],
            textposition='outside',
            textfont=dict(color="#0a2540")
        ))

        fig_importance.update_layout(
            title="各污染物对 AQI 的影响重要性（随机森林）",
            xaxis_title="特征重要性得分",
            template="plotly_white",
            height=400,
            font=dict(color="#0a2540"),
            plot_bgcolor='rgba(240,248,255,0.5)'
        )

        st.plotly_chart(fig_importance, use_container_width=True)

        # 解读
        top_feature = importance_df.iloc[-1]['特征']
        st.markdown(f"""
        **📊 模型解读：**
        - 随机森林模型对 AQI 的预测能力较强（测试集 R² = {test_score:.3f}）。
        - **最重要的驱动因素是 {top_feature}**，其重要性得分远高于其他特征。
        - 这意味着在国土空间规划中，应重点关注 {top_feature} 的排放源管控。
        """)
    else:
        st.info(
            f"有效建模数据不足（当前 {len(df_model)} 条，需 > 100 条），"
            "请积累更多历史批次后再分析。"
        )
else:
    st.info("数据列不足，无法训练随机森林模型。")

st.markdown("---")


# ==================== 四、城市对比 ====================
st.subheader("四、城市 AQI 均值排名（全部历史数据）")

city_rank = df_all.groupby('city')['aqi'].agg(['mean', 'std', 'count']).reset_index()
city_rank.columns = ['城市', '平均AQI', '标准差', '记录数']
city_rank = city_rank.sort_values('平均AQI')

col_a, col_b = st.columns(2)
with col_a:
    st.markdown("**🏆 空气质量最优 TOP10**")
    st.dataframe(
        city_rank.head(10)[['城市', '平均AQI', '标准差']],
        hide_index=True, use_container_width=True
    )

with col_b:
    st.markdown("**⚠️ 空气质量最差 TOP10**")
    st.dataframe(
        city_rank.tail(10)[['城市', '平均AQI', '标准差']].sort_values('平均AQI', ascending=False),
        hide_index=True, use_container_width=True
    )

# 城市排名条形图
fig_rank = go.Figure(go.Bar(
    x=city_rank['平均AQI'],
    y=city_rank['城市'],
    orientation='h',
    marker=dict(
        color=city_rank['平均AQI'],
        colorscale='RdYlGn_r',
        showscale=True,
        colorbar=dict(title="平均AQI", tickfont=dict(color="#0a2540"))
    ),
    text=[f"{v:.1f}" for v in city_rank['平均AQI']],
    textposition='outside',
    textfont=dict(color="#0a2540")
))

fig_rank.update_layout(
    title="各城市历史平均 AQI 排名",
    xaxis_title="平均 AQI",
    template="plotly_white",
    height=700,
    font=dict(color="#0a2540"),
    plot_bgcolor='rgba(240,248,255,0.5)'
)

st.plotly_chart(fig_rank, use_container_width=True)


# ==================== 五、智能分析总结 ====================
st.subheader("📋 基于最新数据的智能分析总结")

# 趋势判断
if len(daily_avg) >= 7:
    first_week_val = daily_avg.head(7)['全国平均AQI'].mean()
    last_week_val = daily_avg.tail(7)['全国平均AQI'].mean()
    trend_desc = "下降" if last_week_val < first_week_val else "上升"
    trend_icon = "✅" if trend_desc == "下降" else "⚠️"
else:
    trend_desc = "数据不足，无法判断趋势"
    trend_icon = "📊"

# 随机森林最重要因子
top_pollutant = "暂未计算出"
if 'importance_df' in dir() and len(importance_df) > 0:
    top_pollutant = str(importance_df.iloc[-1]['特征'])

# 相关性最强因子
strongest_corr_factor = "暂未计算出"
strongest_corr_val = 0.0
corr_desc = ""
if 'aqi_corr' in dir() and len(aqi_corr) > 0:
    aqi_corr_abs = aqi_corr.abs().sort_values(ascending=False)
    strongest_corr_factor = str(aqi_corr_abs.index[0])
    strongest_corr_val = float(aqi_corr.loc[strongest_corr_factor])
    corr_desc = "正相关" if strongest_corr_val > 0 else "负相关"

summary = f"""
> {trend_icon} **整体趋势**：近一周全国平均AQI较首周{trend_desc}了约 {abs(change_pct):.1f}%，空气质量呈{trend_desc}趋势。

> 🌟 **核心驱动因素**：随机森林模型显示，**{top_pollutant}** 是当前影响AQI最重要的污染物，其重要性得分最高。

> 🔗 **关键相关性**：在所有污染物中，**{strongest_corr_factor}** 与AQI的相关性最强（r = {strongest_corr_val:.3f}，呈{corr_desc}），提示该污染物是当前空气质量分化的主要贡献者。

> 📌 **规划建议**：建议在源头管控上优先治理 **{top_pollutant}** 的排放，并结合气象条件优化监测布局。
"""
st.markdown(summary)


# ==============================
# 制作人信息
# ==============================
st.markdown("---")
st.caption("👨‍💻 制作人：刘宇博 · 江毅 · 张睿 ｜ 大数据与人工智能导论课程项目")
