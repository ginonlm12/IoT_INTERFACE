import requests
from config import token, server_address
server_address = server_address  # Thay bằng địa chỉ server của bạn
token = token  # Thay bằng token của bạn

pin = "V27"  # Virtual đèn
value = 0  # 1 để bật, 0 để tắt
# Light turn
def toggle_light(value,  token, server_address = "blynk.cloud", pin = "V27"):
    """
    Gửi yêu cầu HTTP để bật/tắt đèn trên Blynk.

    Args:
        server_address (str): Địa chỉ server Blynk (ví dụ: blynk.cloud).
        token (str): Auth token của bạn.
        pin (str): Virtual pin (ví dụ: V1).
        value (int): Giá trị để set, 1 để bật, 0 để tắt.

    Returns:
        Response: Đối tượng response từ server.
    """
    url = f"https://{server_address}/external/api/update?token={token}&{pin}={value}"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            print(f"Successfully set {pin} to {value}.")
        else:
            print(f"Failed to set {pin}. Status code: {response.status_code}. Message: {response.text}")
        return response
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
        return None

# fan turn
def toggle_fan(value, token, server_address = "blynk.cloud", pin = "V26"):
    """
    Gửi yêu cầu HTTP để bật/tắt đèn trên Blynk.

    Args:
        server_address (str): Địa chỉ server Blynk (ví dụ: blynk.cloud).
        token (str): Auth token của bạn.
        pin (str): Virtual pin (ví dụ: V1).
        value (int): Giá trị để set, 1 để bật, 0 để tắt.

    Returns:
        Response: Đối tượng response từ server.
    """
    url = f"https://{server_address}/external/api/update?token={token}&{pin}={value}"
    try:
        response = requests.get(url)
        
        if response.status_code == 200:
            print(f"Successfully set {pin} to {value}.")
        else:
            print(f"Failed to set {pin}. Status code: {response.status_code}. Message: {response.text}")
        return response
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
        return None

device = {"fan": "v26", "light": "v27"}  # Thay bằng các thiết bị của bạn
url1 = "https://{server_address}/external/api/get?token={token}&{pin}"
url2 = "https://{server_address}/external/api/get?token={token}&{pin}={value}"

def read_value(pin):
    url1 = f"https://{server_address}/external/api/get?token={token}&{pin}"
    try:
        response = requests.get(url1)
        if response.status_code == 200:
            value = response.text
            return value
        else:
            print(f"Failed to read value from {pin}. Status code: {response.status_code}. Message: {response.text}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
        return None
