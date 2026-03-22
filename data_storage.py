import sqlite3

import pandas as pd
from om_api import *
# 1. 城市经纬度配置
CITY_CONFIG = {
    "aalborg": {"latitude": 57.048, "longitude": 9.9187},
    "beijing": {"latitude": 39.9042, "longitude": 116.4074},
    "nanning": {"latitude": 22.817, "longitude": 108.315}
}


def get_table_name(city):
    """统一生成表名规则"""
    return f"weather_{city.lower()}"


def initialize_city_table(city, db_path="weather_data.db"):
    """检查并创建特定城市的 Schema"""
    if city.lower() not in CITY_CONFIG:
        print(f"❌ 错误: 城市 {city} 不在配置列表中")
        return False

    table_name = get_table_name(city)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 动态创建属于该城市的表
    create_table_sql = f"""
    CREATE TABLE IF NOT EXISTS {table_name} (
        date TEXT PRIMARY KEY,
        temperature_2m REAL,
        precipitation REAL,
        precipitation_probability REAL,
        wind_speed_10m REAL,
        wind_direction_10m REAL,
        cloud_cover REAL,
        temperature_80m REAL,
        soil_temperature_0cm REAL,
        relative_humidity_2m REAL,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """
    try:
        cursor.execute(create_table_sql)
        cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_date_{city} ON {table_name} (date);")
        conn.commit()
        print(f"✅ 城市 [{city}] 的数据库表 {table_name} 已就绪")
        return True
    except sqlite3.Error as e:
        print(f"❌ 初始化城市 {city} 失败: {e}")
        return False
    finally:
        conn.close()


def upsert_to_db(df, city, db_path="weather_data.db"):
    """将数据存入对应城市的表"""
    # 🛡️ 防御性检查
    if df is None:
        print(f"⚠️ 警告: 城市 {city} 没有新数据可供存储。")
        return

    # 确保表已经创建
    if not initialize_city_table(city, db_path):
        return

    table_name = get_table_name(city)

    # 预处理日期
    save_df = df.copy()
    if 'date' in save_df.columns:
        save_df['date'] = pd.to_datetime(save_df['date']).dt.strftime('%Y-%m-%d %H:%M:%S')

    conn = sqlite3.connect(db_path)

    # 构造 SQL
    cols = ", ".join(save_df.columns)
    placeholders = ", ".join(["?"] * len(save_df.columns))
    upsert_sql = f"INSERT OR REPLACE INTO {table_name} ({cols}) VALUES ({placeholders})"

    try:
        conn.executemany(upsert_sql, save_df.values.tolist())
        conn.commit()
        print(f"🚀 城市 [{city}] 的数据已同步到表 {table_name}")
    except sqlite3.Error as e:
        print(f"❌ 存储城市 {city} 数据时出错: {e}")
    finally:
        conn.close()

if __name__ == '__main__':

    for city in CITY_CONFIG:
        lat, long = CITY_CONFIG[city]["latitude"], CITY_CONFIG[city]["longitude"]
        upsert_to_db(fetch_new_data(lat,long),city)