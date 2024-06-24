import os
import requests
from PIL import Image
from io import BytesIO
import google.generativeai as genai

import re
from datetime import datetime


def check_image_quake(url="https://github.com/louis70109/ideas-tree/blob/master/images/%E5%8F%B0%E5%8C%97_%E5%A4%A7%E7%9B%B4%E7%BE%8E%E5%A0%A4%E6%A5%B5%E9%99%90%E5%85%AC%E5%9C%92/default.png"):
    genai.configure(api_key=os.getenv('GEMINI_API_KEY'))

    response = requests.get(url)
    if response.status_code == 200:
        image_data = response.content
        image = Image.open(BytesIO(image_data))

        model = genai.GenerativeModel('gemini-pro-vision')
        response = model.generate_content([
            "請問以下地震有什麼需要注意的？針對“管理資訊，避免 FOMO“的主題，提供20字內的敘述，關於提防災害指南。",
            image
        ])
        return response.text
    return 'None'


def get_weather_data(location):
    url = "https://opendata.cwa.gov.tw/api/v1/rest/datastore/F-C0032-001"
    params = {
        "Authorization": os.getenv('OPEN_API_KEY'),
        "format": "JSON",
        "locationName": location
    }
    headers = {
        "accept": "application/json"
    }

    response = requests.get(url, params=params, headers=headers)
    data = response.json()

    return data


def simplify_data(data):
    location_data = data['records']['location'][0]
    weather_elements = location_data['weatherElement']

    simplified_data = {
        'location': location_data['locationName'],
    }

    for element in weather_elements:
        element_name = element['elementName']
        for time in element['time']:

            start_time = time['startTime']
            if start_time not in simplified_data:
                simplified_data[start_time] = {}

            parameter = time['parameter']
            parameter_str = parameter['parameterName']
            if 'parameterUnit' in parameter:
                parameter_str += f" {parameter['parameterUnit']}"

            end_time = time['endTime']
            if end_time not in simplified_data[start_time]:
                simplified_data[start_time][end_time] = {}

            simplified_data[start_time][end_time][element_name] = parameter_str

    return simplified_data


def get_current_weather(simplified_data):
    try:
        # 獲取當前的日期和時間
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # 遍歷所有的時間段
        for start_time in simplified_data:
            if start_time == 'location':
                continue
            for end_time in simplified_data[start_time]:
                # 如果當前時間在這個時間段內，則返回對應的天氣資訊
                if start_time <= now <= end_time:
                    return simplified_data[start_time][end_time]
                else:
                    # 如果沒有找到符合的時間段，則返回第一個天氣資訊
                    return simplified_data[start_time][end_time]
    except Exception as e:
        print(f"An error occurred: {e}")

    # 如果沒有找到任何天氣資訊，則返回None
    return None


def check_location_in_message(message):
    locations = [
        "臺北市", "臺中市", "臺南市", "高雄市",
        "新北市", "桃園市", "新竹市", "苗栗縣",
        "彰化縣", "南投縣", "雲林縣", "嘉義市",
        "嘉義縣", "屏東縣", "宜蘭縣", "花蓮縣",
        "臺東縣", "澎湖縣"
    ]

    # 將訊息中的 "台" 替換為 "臺"
    corrected_message = re.sub("台", "臺", message)
    local = corrected_message.split("_")

    for location in locations:
        if re.search(local[0], location):
            return location
        else:
            location

    return locations[0]
