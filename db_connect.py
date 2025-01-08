from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from datetime import datetime
import pandas as pd
from config import uri_mongodb, topic

uri = uri_mongodb
client = MongoClient(uri, server_api=ServerApi('1'))
db = client["iot_database"]
    
from datetime import datetime
import pandas as pd

def get_statistics_by_date(date, topic=topic):
    collection = db["env_monitor"]

    # Truy vấn MongoDB để lấy bản ghi có timestamp trong ngày
    result = collection.find(
        {
            "topic": topic,
        },
    )
    
    start_date = datetime.strptime(date, "%Y-%m-%d")  # date là kiểu string
    end_date = start_date.replace(hour=23, minute=59, second=59, microsecond=999999)

    filtered_results = [
        record for record in result
        if start_date <= datetime.strptime(record["timestamp"], "%Y-%m-%d %H:%M:%S") <= end_date
    ]
    if filtered_results:
        max_record = max(filtered_results, key=lambda x: datetime.strptime(x["timestamp"], "%Y-%m-%d %H:%M:%S"))
        # print("max: ", max_record)
        data = []
        data.append({
                "mean_light": max_record.get("mean_data", {}).get("light"),
                "mean_temp": max_record.get("mean_data", {}).get("temp"),
                "min_light": max_record.get("min_data", {}).get("light"),
                "min_temp": max_record.get("min_data", {}).get("temp"),
                "max_light": max_record.get("max_data", {}).get("light"),
                "max_temp": max_record.get("max_data", {}).get("temp"),
                "max_change_light": max_record.get("max_change_data", {}).get("light"),
                "max_change_temp": max_record.get("max_change_data", {}).get("temp"),
                "timestamp": max_record.get("timestamp"),
                # Lấy thêm các trường fan_on_time và led_on_time, nếu không có thì trả về danh sách rỗng
                "fan_on_time": max_record.get("fan_on_time", []),
                "led_on_time": max_record.get("led_on_time", [])
        })

        # print("data:", data)
        df = pd.DataFrame(data)
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        return df
    else:
        # Trả về DataFrame rỗng nếu không có dữ liệu
        return pd.DataFrame(
            columns=[
                "mean_light", "mean_temp",
                "min_light", "min_temp",
                "max_light", "max_temp",
                "max_change_light", "max_change_temp", "timestamp",
                "fan_on_time", "led_on_time"
            ]
        )

def get_environment_values_by_date(date, topic=topic):
    collection = db["mqtt_messages"]
    
    # Chuyển ngày string thành datetime để lọc
    start_date = datetime.strptime(date, "%Y-%m-%d")
    end_date = start_date.replace(hour=23, minute=59, second=59, microsecond=999999)
    
    # Truy vấn MongoDB
    results = collection.find({
        "topic": topic,
        "date": date  # Sử dụng "date" thay vì "timestamp" vì date là một chuỗi
    })
    
    # Chuyển đổi kết quả sang danh sách dictionary
    environment_values = []
    for record in results:
        environment_values.append({
            "time": record.get("time"),   # Lấy thời gian
            "date": record.get("date"),   # Lấy ngày
            "light": record.get("light"), # Giá trị ánh sáng
            "temp": record.get("temp"),   # Giá trị nhiệt độ
            "fan": record.get("fan"),     # Trạng thái quạt
            "led": record.get("led"),     # Trạng thái đèn LED
        })
    
    # Chuyển danh sách sang DataFrame
    if environment_values:
        df = pd.DataFrame(environment_values)
        # Kết hợp cột 'date' và 'time' thành cột 'timestamp'
        df["timestamp"] = pd.to_datetime(df["date"] + " " + df["time"])
        # Sắp xếp theo 'timestamp'
        df = df.set_index("timestamp").sort_index()
        # Loại bỏ cột 'date' và 'time' nếu không cần thiết
        df.drop(columns=["date", "time"], inplace=True)
    else:
        # Trả về DataFrame rỗng nếu không có dữ liệu
        df = pd.DataFrame(columns=["light", "temp", "fan", "led", "timestamp"])
    
    return df

def get_recent_environment_values(last_timestamp, topic=topic):
    collection = db["mqtt_messages"]
    now = datetime.now()

    # Tách last_timestamp thành date và time
    last_date = last_timestamp.strftime("%Y-%m-%d")
    last_time = last_timestamp.strftime("%H:%M:%S")
    current_date = now.strftime("%Y-%m-%d")
    current_time = now.strftime("%H:%M:%S")

    # Truy vấn dữ liệu từ MongoDB
    results = collection.find({
        "topic": topic,
        "$or": [
            {
                "date": {"$gt": last_date}
            },
            {
                "date": last_date,
                "time": {"$gte": last_time}
            }
        ],
        "$and": [
            {
                "date": {"$lte": current_date}
            },
            {
                "time": {"$lte": current_time}
            }
        ]
    })

    # Chuyển đổi kết quả MongoDB thành DataFrame
    data = []
    for record in results:
        data.append({
            "timestamp": f"{record['date']} {record['time']}",
            "light": record.get("light", 0),
            "temp": record.get("temp", 0.0),
            "fan": record.get("fan", 0),
            "led": record.get("led", 0),
        })

    if data:
        df = pd.DataFrame(data)
        df["timestamp"] = pd.to_datetime(df["timestamp"])  # Kết hợp date và time thành timestamp
        return df.set_index("timestamp")
    else:
        return pd.DataFrame(columns=["timestamp", "light", "temp", "fan", "led"]).set_index("timestamp")

def get_latest_temperature():
    collection = db["mqtt_messages"]
    latest_record = collection.find_one({}, sort=[("date", -1), ("time", -1)])
    if latest_record:
        temperature = latest_record.get("temp", "Không có dữ liệu")
        print(temperature)
        time = latest_record.get("time", "Không có dữ liệu")
        print(time)
        date = latest_record.get("date", "Không có dữ liệu")
        return temperature, time, date
    return "Không có dữ liệu", "Không có dữ liệu", "Không có dữ liệu"

def get_latest_light_percentage():
    collection = db["mqtt_messages"]
    latest_record = collection.find_one({}, sort=[("date", -1), ("time", -1)])
    if latest_record:
        light = latest_record.get("light", "Không có dữ liệu")
        time = latest_record.get("time", "Không có dữ liệu")
        date = latest_record.get("date", "Không có dữ liệu")
        return light, time, date
    return "Không có dữ liệu", "Không có dữ liệu", "Không có dữ liệu"

def analyze_on_time(on_time_list, device_name):
    # print("------------------:", on_time_list)
    # Kiểm tra nếu danh sách rỗng (nếu on_time_list là một Series hoặc DataFrame)
    if isinstance(on_time_list, pd.Series) and on_time_list.empty:
        return 0, 0,0  # Không có thời gian bật
    
    # Nếu là list bình thường
    if isinstance(on_time_list, list) and len(on_time_list) == 0:
        return 0, 0, 0  # Không có thời gian bật

    # Tính tổng thời gian bật thiết bị (giả sử mỗi phần tử là 1 giây)
    total_on_time = len(on_time_list)
    
    # Ước tính công suất tiêu thụ
    # Giả sử quạt có công suất 10W và đèn có công suất 5W
    if device_name == "fan":
        power_watt = 10  # Quạt có công suất 10W
    elif device_name == "led":
        power_watt = 5  # Đèn có công suất 5W
    else:
        power_watt = 0  # Nếu không phải fan hoặc led, không tính công suất
    
    # Ước tính công suất (Wh)
    estimated_power = (total_on_time / 60) * power_watt  # Công suất tính theo phút
    
    # Tính thời gian bật liên tục lâu nhất
    max_continuous_on_time = 0
    current_continuous_time = 0
    for i in range(1, len(on_time_list)):
        current_time = datetime.strptime(on_time_list[i], "%H:%M:%S")
        previous_time = datetime.strptime(on_time_list[i-1], "%H:%M:%S")
        
        # Nếu thời gian liên tiếp, tăng thời gian liên tục
        if (current_time - previous_time).seconds == 1:
            current_continuous_time += 1
        else:
            max_continuous_on_time = max(max_continuous_on_time, current_continuous_time)
            current_continuous_time = 1  # Reset for new sequence
    
    # Lấy thời gian bật liên tục lâu nhất
    max_continuous_on_time = max(max_continuous_on_time, current_continuous_time)
    
    return total_on_time, estimated_power, max_continuous_on_time