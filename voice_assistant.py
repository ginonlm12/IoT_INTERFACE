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

# Function to play audio directly
from tempfile import TemporaryFile

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

def gpt_response_with_function_calling(prompt: str):
    """Get GPT response and execute function calls."""
    async def get_response():
        response = await openai.ChatCompletion.acreate(
            model="gpt-4-0613",
            messages=[
                {"role": "system", "content": "Bạn là trợ lý nhà thông minh, phản hồi và giao tiếp hoàn toàn bằng tiếng Việt."},
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
                    "description": "Bật hoặc tắt đèn.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "status": {"type": "string", "enum": ["bật", "tắt"]}
                        },
                        "required": ["status"]
                    }
                },
                {
                    "name": "toggle_fan",
                    "description": "Bật hoặc tắt quạt.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "status": {"type": "string", "enum": ["bật", "tắt"]}
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
        temperature = 30  # Giả lập nhiệt độ
        if temperature > 35:
            return f"Nhiệt độ hiện tại là {temperature}°C. Cảnh báo: Nhiệt độ quá cao!"
        elif temperature < 15:
            return f"Nhiệt độ hiện tại là {temperature}°C. Cảnh báo: Nhiệt độ quá thấp!"
        else:
            return f"Nhiệt độ hiện tại là {temperature}°C."
    elif function_name == "get_current_light":
        light_percentage = 40  # Giả lập ánh sáng
        if light_percentage > 80:
            return f"Phần trăm ánh sáng hiện tại là {light_percentage}%. Cảnh báo: Ánh sáng quá cao!"
        elif light_percentage < 20:
            return f"Phần trăm ánh sáng hiện tại là {light_percentage}%. Cảnh báo: Ánh sáng quá thấp!"
        else:
            return f"Phần trăm ánh sáng hiện tại là {light_percentage}%"
    elif function_name == "summary_report":
        return "Tóm tắt: Đèn tắt, quạt tắt, nhiệt độ ổn định, ánh sáng ổn định."
    elif function_name == "toggle_light":
        status = parameters.get("status")
        return f"Đèn đã được {status}."
    elif function_name == "toggle_fan":
        status = parameters.get("status")
        return f"Quạt đã được {status}."
    else:
        return "Không nhận diện được yêu cầu. Vui lòng thử lại."

# Streamlit UI
st.set_page_config(page_title="Trợ Lý Nhà Thông Minh", layout="centered")
st.title("Trợ Lý Nhà Thông Minh")
st.markdown(
    """
    <style>
    .stButton>button {
        background-color: #4CAF50;
        color: white;
        border-radius: 8px;
        padding: 10px 20px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# Voice Input Button
if st.button("Ghi Lại Giọng Nói"):
    st.write("Đang ghi âm... Vui lòng nói rõ.")
    user_voice = speech_to_text_google()
    if user_voice:
        st.success(f"Bạn đã nói: {user_voice}")

        # Pass text to GPT model for action inference
        gpt_output = gpt_response_with_function_calling(user_voice)
        st.write(f"Kết Quả GPT: {gpt_output}")

        # Play Response as Voice
        play_audio(gpt_output)
    else:
        st.error("Không thể nhận diện giọng nói. Vui lòng thử lại.")
