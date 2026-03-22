import datetime

import openmeteo_requests

import pandas as pd
import requests_cache
from retry_requests import retry


def fetch_new_data(lat,long):


	# 设置 Open-Meteo 客户端
	cache_session = requests_cache.CachedSession('.cache', expire_after=3600)
	retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
	openmeteo = openmeteo_requests.Client(session=retry_session)

	url = "https://historical-forecast-api.open-meteo.com/v1/forecast"

	# 时间窗口：最近3天
	end_date = datetime.datetime.now().date()
	start_date = end_date - datetime.timedelta(days=3)

	params = {
		"latitude": lat,
		"longitude": long,
		"start_date": start_date,
		"end_date": end_date,
		"hourly": ["temperature_2m", "precipitation", "precipitation_probability",
				   "wind_speed_10m", "wind_direction_10m", "cloud_cover",
				   "temperature_80m", "soil_temperature_0cm", "relative_humidity_2m"],
	}

	try:
		responses = openmeteo.weather_api(url, params=params)
		response = responses[0]

		# 解析每小时数据
		hourly = response.Hourly()
		hourly_data = {"date": pd.date_range(
			start=pd.to_datetime(hourly.Time(), unit="s", utc=True),
			end=pd.to_datetime(hourly.TimeEnd(), unit="s", utc=True),
			freq=pd.Timedelta(seconds=hourly.Interval()),
			inclusive="left"
		)}

		# 遍历变量并存入字典 (按顺序 0-8)
		var_names = ["temperature_2m", "precipitation", "precipitation_probability",
					 "wind_speed_10m", "wind_direction_10m", "cloud_cover",
					 "temperature_80m", "soil_temperature_0cm", "relative_humidity_2m"]

		for i, name in enumerate(var_names):
			hourly_data[name] = hourly.Variables(i).ValuesAsNumpy()

		df = pd.DataFrame(data=hourly_data)
		print(f"✅ 成功获取数据，共 {len(df)} 行")
		return df
	except Exception as e:
		print(f"❌ 获取 数据失败: {e}")
		return None
if __name__ == '__main__':
    fetch_new_data()