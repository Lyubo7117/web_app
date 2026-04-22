# -*- coding: utf-8 -*-
"""
数据加载工具模块
用于读取成员A生成的实时空气质量数据
"""

import os
import pandas as pd


def load_latest_data():
    """
    读取最新实时空气质量数据。
    
    数据文件路径：../data/current/latest.csv（相对于当前文件所在目录）
    
    Returns:
        pd.DataFrame: 包含实时数据的DataFrame。
                      如果文件不存在，返回包含标准列名的空DataFrame。
    """
    # 获取当前文件所在目录
    current_dir = os.path.dirname(os.path.abspath(__file__))
    # 构建数据文件路径：web_app/utils -> web_app -> data/current/latest.csv
    data_path = os.path.join(current_dir, '..', '..', 'data', 'current', 'latest.csv')
    data_path = os.path.normpath(data_path)
    
    # 标准列名
    columns = [
        'city_name', 'aqi', 'pm25', 'pm10', 'co', 'no2', 
        'so2', 'o3', 'pollutant', 'level', 'lat', 'lon', 'update_time'
    ]
    
    try:
        if os.path.exists(data_path):
            df = pd.read_csv(data_path, encoding='utf-8')
            # 确保列名存在（如果文件列名不对，这里会报错，但至少尝试了）
            return df
        else:
            print(f"数据文件不存在：{data_path}，返回空DataFrame")
            return pd.DataFrame(columns=columns)
    except Exception as e:
        print(f"读取数据文件出错：{e}，返回空DataFrame")
        return pd.DataFrame(columns=columns)


if __name__ == '__main__':
    # 测试代码
    df = load_latest_data()
    print(f"数据形状：{df.shape}")
    print(df.head())