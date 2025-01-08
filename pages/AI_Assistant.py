import streamlit as st
import openai
import time
import pyttsx3
import speech_recognition as sr
import asyncio
from typing import Any, Dict
from gtts import gTTS
import io
from pydub import AudioSegment
from pydub.playback import play
from db_connect import get_latest_temperature, get_latest_light_percentage, get_statistics_by_date, analyze_on_time
from datetime import datetime, timedelta
from toggle import toggle_light, toggle_fan, read_value
from config import topic, openai_key

time = datetime.now()

# Function to play audio directly
from tempfile import TemporaryFile

def generate_prompt_statistics_report(date="2025-01-02"):
    """
    Tạo prompt để báo cáo dựa trên dữ liệu thống kê từ `get_statistics_by_date`.
    
    Parameters:
    - date: Ngày (string dạng 'YYYY-MM-DD') để lấy dữ liệu

    Returns:
    - Prompt dạng string
    """
    print("date:", date)
    formatted_date = date.strftime("%Y-%m-%d")
    statistics_df = get_statistics_by_date(formatted_date)
    
    if statistics_df.empty:
        return f"Không có dữ liệu thống kê cho ngày {date}. Vui lòng thử lại với ngày khác."

    # Lấy dữ liệu từ dataframe
    mean_data = statistics_df.iloc[0][["mean_light", "mean_temp"]]
    min_data = statistics_df.iloc[0][["min_light", "min_temp"]]
    max_data = statistics_df.iloc[0][["max_light", "max_temp"]]
    max_change_data = statistics_df.iloc[0][["max_change_light", "max_change_temp"]]
    fan_on_time = statistics_df.iloc[0]["fan_on_time"]
    led_on_time = statistics_df.iloc[0]["led_on_time"]

    # Tính tổng thời gian bật quạt và đèn, ước tính công suất
    fan_total, fan_power, fan_max_continuous = analyze_on_time(fan_on_time, "fan")
    led_total, led_power, led_max_continuous = analyze_on_time(led_on_time, "led")

    # Xây dựng nội dung báo cáo
    prompt = f"Bạn là trợ lý Smart Livestock Management System. Hãy đưa ra báo cáo chi tiết về ngày {date} như sau:\n\n"
    prompt += f"1. **Thông số trung bình:**\n"
    prompt += f"   - Nhiệt độ: {mean_data['mean_temp']}°C\n"
    prompt += f"   - Ánh sáng: {mean_data['mean_light']}%\n\n"

    prompt += f"2. **Thông số tối thiểu:**\n"
    prompt += f"   - Nhiệt độ: {min_data['min_temp']}°C\n"
    prompt += f"   - Ánh sáng: {min_data['min_light']}%\n\n"

    prompt += f"3. **Thông số tối đa:**\n"
    prompt += f"   - Nhiệt độ: {max_data['max_temp']}°C\n"
    prompt += f"   - Ánh sáng: {max_data['max_light']}%\n\n"

    prompt += f"4. **Biến đổi lớn nhất:**\n"
    prompt += f"   - Nhiệt độ: {max_change_data['max_change_temp']}°C\n"
    prompt += f"   - Ánh sáng: {max_change_data['max_change_light']}%\n\n"

    prompt += f"5. **Năng lượng tiêu thụ:**\n"
    prompt += f"   - Quạt: {fan_power} Wh\n"
    prompt += f"   - Đèn: {led_power} Wh\n\n"

    prompt += f"6. **Thời gian bật thiết bị:**\n"
    prompt += f"   - Thời gian bật quạt: {fan_total} giây\n"
    prompt += f"   - Thời gian bật đèn: {led_total} giây\n"

    prompt += f"7. **Thời gian bật liên tục lâu nhất:**\n"
    prompt += f"   - Quạt: {fan_max_continuous} giây\n"
    prompt += f"   - Đèn: {led_max_continuous} giây\n\n"

    prompt += f"Đưa ra kết luận và lời khuyên dựa trên các thông số trên."

    return prompt

def play_audio(text: str):
    """Chuyển đổi văn bản thành giọng nói và phát trực tiếp trên Streamlit."""
    tts = gTTS(text, lang="vi")
    with TemporaryFile() as fp:
        tts.write_to_fp(fp)
        fp.seek(0)
        audio = AudioSegment.from_file(fp, format="mp3")
        play(audio)

def speech_to_text_google() -> str:
    """Sử dụng Google Speech-to-Text để nhận diện tiếng Việt."""
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        st.write("Đang lắng nghe...")
        audio = recognizer.listen(source, phrase_time_limit=2)
    try:
        return recognizer.recognize_google(audio, language="vi-VN")  # Thêm `language="vi-VN"`
    except sr.UnknownValueError:
        return "Không nhận diện được giọng nói."
    except sr.RequestError as e:
        return f"Lỗi: {e}"

openai.api_key = openai_key
def gpt_response_with_function_calling(prompt: str):
    """Get GPT response and execute function calls."""
    async def get_response():
        response = await openai.ChatCompletion.acreate(
            model="gpt-4-0613",
            messages=[
                {"role": "system", "content": "Bạn là trợ lý Smart Livestock Management System được xây dựng bởi đội ngũ đến từ Đại học Bách Khoa Hà Nội là Quang, Lâm, Tuấn, Quốc Tuấn, phản hồi và giao tiếp hoàn toàn bằng tiếng Việt."},
                {"role": "user", "content": prompt},
            ],
            functions=[
                {
                    "name": "get_current_temperature",
                    "description": "Xem nhiệt độ hiện tại và đưa ra cảnh báo trạng thái.",
                    "parameters": {"type": "object", "properties": {}}
                },
                {
                    "name": "get_current_light",
                    "description": "Xem phần trăm ánh sáng hiện tại và đưa ra cảnh báo trạng thái.",
                    "parameters": {"type": "object", "properties": {}}
                },
                {
                    "name": "summary_report",
                    "description": "Xem tóm tắt trạng thái tổng quát của hệ thống.",
                    "parameters": {"type": "object", "properties": {}}
                },
                {
                    "name": "toggle_light",
                    "description": "Xem trạng thái đèn hoặc bật hoặc tắt đèn.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "status": {"type": "string", "enum": ["xem", "bật", "tắt"]}
                        },
                        "required": ["status"]
                    }
                },
                {
                    "name": "toggle_fan",
                    "description": "Xem trạng thái quạt hoặc bật hoặc tắt quạt.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "status": {"type": "string", "enum": ["xem", "bật", "tắt"]}
                        },
                        "required": ["status"]
                    }
                }
            ]
        )
        return response

    result = asyncio.run(get_response())
    function_call = result["choices"][0]["message"].get("function_call")
    if function_call:
        function_name = function_call["name"]
        parameters = function_call.get("arguments", {})
        # Gọi hàm tương ứng
        function_result = function_calling(function_name, eval(parameters))
        
        # Tạo một prompt mới để GPT trả lời từ kết quả hàm
        follow_up_prompt = f"Kết quả của {function_name}: {function_result}. Hãy phản hồi chi tiết."
        return gpt_response_with_function_calling(follow_up_prompt)
    else:
        return result["choices"][0]["message"]["content"]

def function_calling(function_name: str, parameters: Dict[str, Any]) -> Any:
    """Thực hiện chức năng tương ứng."""
    if function_name == "get_current_temperature":
        temperature, time, date = get_latest_temperature()
        string = f"Bạn là trợ lý ảo Smart Livestock Management System đưa ra lời khuyên về nhiệt độ. Nhiệt độ ở thời điêm hiện tại, {time}, {date} là {temperature}°C."
        if temperature > 35:
            return string + f"Cảnh báo: Nhiệt độ quá cao!"
        elif temperature < 15:
            return string + f"Cảnh báo: Nhiệt độ quá thấp!"
        else:
            return string
    elif function_name == "get_current_light":
        light_percentage, time, date = get_latest_light_percentage()
        string = f"Bạn là trợ lý ảo Smart Livestock Management System đưa ra lời khuyên về ánh sáng. Ánh sáng ở thời điêm hiện tại, {time}, {date} là {light_percentage}°C."
        if light_percentage > 90:
            return string + f"Cảnh báo: Ánh sáng quá cao!"
        elif light_percentage < 60:
            return string + f"Cảnh báo: Ánh sáng quá thấp!"
        else:
            return string
    elif function_name == "summary_report":
        return generate_prompt_statistics_report(datetime.today())
    elif function_name == "toggle_light":
        time = datetime.now()
        string = f"Bạn là trợ lý ảo Smart Livestock Management System bật, tắt đèn. Thời gian hiện tại là {time}."
        status = parameters.get("status")
        if "bật" in status:
            toggle_light(1)
            return string  + f"Đèn đã được {status}. Hãy thông báo người dùng."
        elif "tắt" in status:
            toggle_light(0)
            return string  + f"Đèn đã được {status}. Hãy thông báo người dùng."
        else:
            
            value = read_value("V27")
            print(value)
            return f"Đèn đang ở trạng thái {value}. (0 là đang tắt và 1 đang là bật, các trạng thái khác là lỗi)"
    elif function_name == "toggle_fan":
        time = datetime.now()
        string = f"Bạn là trợ lý ảo Smart Livestock Management System bật, tắt quạt. Thời gian hiện tại là {time}."
        status = parameters.get("status")
        if "bật" in status:
            toggle_fan(1)
            return string + f"Quạt đã được điều chỉnh để {status} bằng hiệu lệnh.."
        elif "tắt" in status:
            toggle_fan(0)
            return string + f"Quạt đã được điều chỉnh để {status} bằng hiệu lệnh.."
        else:
            value = read_value("V26")
            return f"Quạt đang ở trạng thái {value}. (0 là đang tắt và 1 đang là bật, các trạng thái khác là lỗi)"
    
    else:
        return "Không nhận diện được yêu cầu. Vui lòng thử lại."
    
# Initialize session state for conversation history
if "conversation_history" not in st.session_state:
    st.session_state["conversation_history"] = []  # List to store messages

# Function to update conversation history
def update_conversation_history(user_message: str, assistant_response: str):
    st.session_state["conversation_history"].append({"role": "user", "message": user_message})
    st.session_state["conversation_history"].append({"role": "assistant", "message": assistant_response})

# Display conversation history
st.subheader("🗨️ Conversation History")
with st.container():
    for message in st.session_state["conversation_history"]:
        if message["role"] == "user":
            st.markdown(f"**🧑 User:** {message['message']}")
        else:
            st.markdown(f"**🤖 Assistant:** {message['message']}")

# Voice Input Button
if st.button("🎤 Ghi Lại Giọng Nói"):
    st.write("Đang ghi âm... Vui lòng nói rõ.")
    user_voice = speech_to_text_google()
    
    if user_voice:
        st.success(f"Bạn đã nói: {user_voice}")
        if user_voice == "Không nhận diện được giọng nói.":
            user_voice = "Bạn hãy đóng vai bạn là trợ lý ảo Smart Livestock Management System có hỗ trợ giọng nói, tuy nhiên, do lỗi kĩ thuật nên chưa thể ghi lại giọng nói, hãy trả lời người dùng yêu cầu họ nói lại."
        
        # Pass text to GPT model for action inference
        gpt_output = gpt_response_with_function_calling(user_voice)
        
        # Update conversation history
        update_conversation_history(user_voice, gpt_output)
        
        # Display assistant response
        # st.write(f"🧠 Kết Quả GPT: {gpt_output}")
        
        # Play Response as Voice
        st.markdown("### AI đang trả lời...")
        play_audio(gpt_output)
        st.write(f"🧠 Kết Quả GPT: {gpt_output}")
    else:
        st.error("Không thể nhận diện giọng nói. Vui lòng thử lại.")