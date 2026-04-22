"""
excel_parser.py
Excel 数据解析工具模块

用于解析 national_aqi_crawler.py 和 weather_alarm_crawler.py 生成的 Excel 文件，
将结果统一转换为标准 DataFrame 格式，供 Streamlit 页面直接使用。
"""

import os
import glob
import pandas as pd


# ==============================
# 标准列名定义
# ==============================
AQI_COLUMNS = [
    'city_name', 'aqi', 'pm25', 'pm10', 'co', 'no2',
    'so2', 'o3', 'pollutant', 'level', 'update_time'
]

ALARM_COLUMNS = [
    'city', 'alarm_type', 'alarm_level', 'alarm_title',
    'publish_time', 'description'
]


# ==============================
# AQI 数据解析
# ==============================
def _find_latest_batch(data_dir: str) -> str:
    """
    在 data_output/aqi/ 目录下，找到最新批次文件夹。
    爬虫按日期创建子文件夹（如 2024-04-22/），本函数返回最新的那个。

    Parameters
    ----------
    data_dir : str
        aqi 数据目录的绝对路径

    Returns
    -------
    str
        最新批次文件夹路径，找不到则返回空字符串
    """
    if not os.path.exists(data_dir):
        return ''

    # 列出所有子目录（按批次/日期存放）
    subdirs = [
        d for d in glob.glob(os.path.join(data_dir, '*'))
        if os.path.isdir(d)
    ]
    if not subdirs:
        return ''

    # 按修改时间排序，取最新的
    subdirs.sort(key=lambda x: os.path.getmtime(x), reverse=True)
    return subdirs[0]


def parse_aqi_excel(file_path: str) -> pd.DataFrame:
    """
    解析单个 AQI Excel 文件（national_aqi_crawler 产出）。

    爬虫产出的 Excel 通常包含以下列（可能 sheet 名不同）：
      城市、AQI、PM2.5、PM10、CO、NO2、SO2、O3、首要污染物、等级、数据时间

    本函数会将列名统一映射为标准列名。

    Parameters
    ----------
    file_path : str
        Excel 文件的绝对路径

    Returns
    -------
    pd.DataFrame
        标准化后的 DataFrame
    """
    if not os.path.exists(file_path):
        return pd.DataFrame(columns=AQI_COLUMNS)

    # 列名映射：爬虫原始列名 → 标准列名
    col_map = {
        '城市': 'city_name', 'AQI': 'aqi', 'PM2.5': 'pm25',
        'PM10': 'pm10', 'CO': 'co', 'NO2': 'no2', 'SO2': 'so2',
        'O3': 'o3', '首要污染物': 'pollutant', '等级': 'level',
        '数据时间': 'update_time', '监测时间': 'update_time',
    }

    try:
        # 读取第一个 sheet
        df = pd.read_excel(file_path, engine='openpyxl')

        # 列名标准化
        df.rename(columns=col_map, inplace=True)

        # 只保留标准列
        existing_cols = [c for c in AQI_COLUMNS if c in df.columns]
        df = df[existing_cols]

        return df

    except Exception as e:
        print(f"[ERROR] 解析 AQI Excel 失败：{file_path}\n  原因：{e}")
        return pd.DataFrame(columns=AQI_COLUMNS)


def get_latest_aqi_snapshot(data_dir: str = None) -> pd.DataFrame:
    """
    从 data_output/aqi/ 目录获取最新批次的 AQI 快照数据。

    会自动：
    1. 找到最新批次文件夹（按日期时间戳子目录）
    2. 递归遍历该目录下所有 Excel 文件（含区域子文件夹）
    3. 取每个城市的最新一条记录，合并为一个 DataFrame
    4. 为每个城市补充经纬度

    Parameters
    ----------
    data_dir : str, optional
        AQI 数据目录路径。默认为 main/data_output/aqi/

    Returns
    -------
    pd.DataFrame
        合并后的 AQI 数据，包含 lat/lon 列
    """
    print("=" * 50)
    print("[DEBUG] get_latest_aqi_snapshot 开始执行")

    if data_dir is None:
        # __file__ = utils/excel_parser.py → 向上一级 = main/
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        data_dir = os.path.join(base_dir, 'data_output', 'aqi')

    print(f"[DEBUG] 数据目录路径：{data_dir}")
    print(f"[DEBUG] 目录是否存在：{os.path.exists(data_dir)}")

    if not os.path.exists(data_dir):
        print(f"[WARN] 数据目录不存在：{data_dir}")
        return pd.DataFrame(columns=AQI_COLUMNS + ['lat', 'lon'])

    # 1. 获取所有时间戳子目录，按名称排序取最新
    runs = [d for d in os.listdir(data_dir)
            if os.path.isdir(os.path.join(data_dir, d))]
    print(f"[DEBUG] 找到批次子目录：{runs}")

    if not runs:
        print(f"[WARN] 未找到批次子目录：{data_dir}")
        return pd.DataFrame(columns=AQI_COLUMNS + ['lat', 'lon'])

    latest_run = sorted(runs)[-1]
    run_dir = os.path.join(data_dir, latest_run)
    print(f"[DEBUG] 最新批次：{latest_run}")
    print(f"[DEBUG] 最新批次完整路径：{run_dir}")

    # 2. 递归遍历该批次目录下所有 Excel（含区域子文件夹）
    all_cities_data = []
    excel_count = 0
    for root, dirs, files in os.walk(run_dir):
        for file in files:
            if file.endswith('.xlsx') and not file.startswith('全国'):
                file_path = os.path.join(root, file)
                excel_count += 1
                print(f"[DEBUG] 正在解析 Excel #{excel_count}：{file_path}")
                try:
                    df_city = parse_aqi_excel(file_path)
                    print(f"[DEBUG]   → 解析结果：{len(df_city)} 行，列名={list(df_city.columns)}")
                    if not df_city.empty and 'update_time' in df_city.columns:
                        latest = df_city.sort_values('update_time').iloc[-1]
                        all_cities_data.append(latest)
                    elif not df_city.empty:
                        all_cities_data.append(df_city.iloc[-1])
                except Exception as e:
                    print(f"[ERROR] 解析失败：{file_path}，错误：{e}")

    print(f"[DEBUG] 遍历 Excel 文件总数：{excel_count}")
    print(f"[DEBUG] 成功解析城市数量：{len(all_cities_data)}")

    if not all_cities_data:
        print(f"[WARN] 批次目录下无有效数据：{run_dir}")
        print("=" * 50)
        return pd.DataFrame(columns=AQI_COLUMNS + ['lat', 'lon'])

    df_snapshot = pd.DataFrame(all_cities_data).reset_index(drop=True)

    # 3. 补充经纬度
    from utils.city_coords import get_lat, get_lon
    df_snapshot['lat'] = df_snapshot['city_name'].apply(get_lat)
    df_snapshot['lon'] = df_snapshot['city_name'].apply(get_lon)

    print(f"[OK] 已加载 AQI 快照：{len(df_snapshot)} 个城市（批次：{latest_run}）")
    print(f"[DEBUG] 城市列表：{list(df_snapshot['city_name'])}")
    print("=" * 50)
    return df_snapshot


def parse_uploaded_excel(uploaded_file) -> pd.DataFrame:
    """
    解析用户通过 Streamlit file_uploader 上传的 Excel 文件。

    自动识别列名并映射为标准格式，同时补充经纬度。

    Parameters
    ----------
    uploaded_file : UploadedFile
        Streamlit 的 file_uploader 返回的对象

    Returns
    -------
    pd.DataFrame
        标准化后的 DataFrame，包含 lat/lon
    """
    try:
        df = pd.read_excel(uploaded_file, engine='openpyxl')

        # 列名映射
        col_map = {
            '城市': 'city_name', 'AQI': 'aqi', 'PM2.5': 'pm25',
            'PM10': 'pm10', 'CO': 'co', 'NO2': 'no2', 'SO2': 'so2',
            'O3': 'o3', '首要污染物': 'pollutant', '等级': 'level',
            '数据时间': 'update_time', '监测时间': 'update_time',
        }
        df.rename(columns=col_map, inplace=True)

        # 保留存在的标准列
        existing_cols = [c for c in AQI_COLUMNS if c in df.columns]
        df = df[existing_cols]

        # 补充经纬度
        from utils.city_coords import get_lat, get_lon
        if 'city_name' in df.columns:
            df['lat'] = df['city_name'].apply(get_lat)
            df['lon'] = df['city_name'].apply(get_lon)
        else:
            df['lat'] = 0.0
            df['lon'] = 0.0

        return df

    except Exception as e:
        print(f"[ERROR] 解析上传文件失败：{e}")
        return pd.DataFrame(columns=AQI_COLUMNS + ['lat', 'lon'])


# ==============================
# 气象预警数据解析
# ==============================
def parse_alarm_excel(file_path: str) -> pd.DataFrame:
    """
    解析气象预警 Excel 文件（weather_alarm_crawler 产出）。

    Parameters
    ----------
    file_path : str
        Excel 文件路径

    Returns
    -------
    pd.DataFrame
        标准化后的预警数据
    """
    if not os.path.exists(file_path):
        return pd.DataFrame(columns=ALARM_COLUMNS)

    col_map = {
        '城市': 'city', '预警类型': 'alarm_type',
        '预警等级': 'alarm_level', '预警标题': 'alarm_title',
        '发布时间': 'publish_time', '预警内容': 'description',
    }

    try:
        df = pd.read_excel(file_path, engine='openpyxl')
        df.rename(columns=col_map, inplace=True)

        existing_cols = [c for c in ALARM_COLUMNS if c in df.columns]
        return df[existing_cols]

    except Exception as e:
        print(f"[ERROR] 解析预警 Excel 失败：{e}")
        return pd.DataFrame(columns=ALARM_COLUMNS)
