import time
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from db_connect import get_environment_values_by_date, get_recent_environment_values
from config import topic


# Thiết lập giao diện Streamlit
st.set_page_config(
    page_title="Smart Livestock Management System Dashboard",
    page_icon="📊",
    layout="wide"
)

st.title("📊 Smart Livestock Management System Dashboard")
st.write("Trực quan hóa dữ liệu môi trường từ hệ thống chăn nuôi thông minh.")


### Sidebar: Chọn chế độ
st.sidebar.header("Lựa chọn chế độ hiển thị")
mode = st.sidebar.radio("Chọn chế độ:", ["Theo ngày", "Thời gian thực"])

# Lựa chọn topic mặc định
topic = topic


# Chế độ: Theo ngày
if mode == "Theo ngày":
    st.sidebar.header("Lựa chọn ngày")
    date_input = st.sidebar.date_input("Chọn ngày", datetime.today())
    if not date_input:
        date_input = datetime.today()
    date_str = date_input.strftime("%Y-%m-%d")

    # Lấy dữ liệu đầy đủ
    data = get_environment_values_by_date(date_str, topic)

    if data.empty:
        st.warning("Không có dữ liệu nào cho ngày được chọn.")
    else:
        # Chuyển đổi dữ liệu đầy đủ thành DataFrame
        df = pd.DataFrame(data)
        df.reset_index(inplace=True)  # Chuyển index 'timestamp' thành cột thông thường
        df["time"] = df["timestamp"].dt.time  # Lấy phần thời gian từ 'timestamp'

        # Lọc dữ liệu mỗi 10 giây để hiển thị biểu đồ
        df_chart = df[df["timestamp"].dt.second % 10 == 0]

        # Đồ thị ánh sáng theo ngày (Bar Chart)
        st.subheader("💡 Đồ Thị Ánh Sáng Theo Ngày")
        fig_light_day = px.bar(
            df_chart,
            x="time",
            y="light",
            title=f"Ánh sáng theo ngày ({date_str})",
            labels={"time": "Thời Gian", "light": "Ánh Sáng (%)"},
            color="light",
            color_continuous_scale="Viridis"
        )
        st.plotly_chart(fig_light_day, use_container_width=True)

        # Đồ thị nhiệt độ theo ngày (Line Chart)
        st.subheader("🌡️ Đồ Thị Nhiệt Độ Theo Ngày")
        fig_temp_day = px.line(
            df_chart,
            x="time",
            y="temp",
            title=f"Nhiệt độ theo ngày ({date_str})",
            labels={"time": "Thời Gian", "temp": "Nhiệt Độ (°C)"},
            markers=True
        )
        st.plotly_chart(fig_temp_day, use_container_width=True)

        # Hiển thị bảng dữ liệu chi tiết (không lọc mỗi 10 giây)
        st.subheader("📋 Dữ Liệu Chi Tiết")
        st.dataframe(
            df.style.format({
                "temp": "{:.2f}", 
                "light": "{:.0f}", 
                "fan": "{:.0f}", 
                "led": "{:.0f}"
            })
        )

        # Tính số giờ bật thiết bị (không lọc mỗi 10 giây)
        led_on_time = df["led"].sum() / 60  # Giả sử dữ liệu mỗi phút
        fan_on_time = df["fan"].sum() / 60
        st.subheader("🕒 Thời gian bật thiết bị trong ngày")
        st.write(f"- **Số giờ bật đèn (LED):** {led_on_time:.2f} phút")
        st.write(f"- **Số giờ bật quạt (Fan):** {fan_on_time:.2f} phút")


# Chế độ: Thời gian thực
elif mode == "Thời gian thực":
    # Khởi tạo giá trị mặc định cho "stream" nếu chưa tồn tại
    if "stream" not in st.session_state:
        st.session_state.stream = True

    # Khởi tạo dữ liệu ban đầu (5 phút gần nhất hoặc tối đa 100 dòng)
    if "data" not in st.session_state:
        st.session_state.data = get_recent_environment_values(
            datetime.now() - timedelta(minutes=5),
            topic
        )
        # st.write("Dữ liệu ban đầu:", st.session_state.data)

    def toggle_streaming():
        """Bật hoặc tắt chế độ streaming."""
        st.session_state.stream = not st.session_state.stream

    # Sidebar với nút Start và Stop
    #st.sidebar.button(
    #    "Start streaming", disabled=st.session_state.stream, on_click=toggle_streaming
    #)
    #st.sidebar.button(
    #    "Stop streaming", disabled=not st.session_state.stream, on_click=toggle_streaming
    #)

    # Hàm hiển thị và cập nhật dữ liệu
    def show_latest_data():
        """Cập nhật dữ liệu và hiển thị đồ thị."""
        # Kiểm tra nếu DataFrame rỗng
        if st.session_state.data.empty:
            st.warning("Không có dữ liệu ban đầu. Đang chờ dữ liệu mới...")
            return

        # Lấy timestamp cuối cùng
        last_timestamp = st.session_state.data.index[-1]

        # Lấy dữ liệu mới
        recent_data = get_recent_environment_values(last_timestamp, topic)

        # Cập nhật dữ liệu vào session_state
        if not recent_data.empty:
            st.session_state.data = pd.concat([st.session_state.data, recent_data])
            st.session_state.data = st.session_state.data[-100:]  # Chỉ giữ 100 dòng gần nhất

        # Hiển thị đồ thị ánh sáng theo thời gian thực
        st.subheader("💡 Đồ Thị Ánh Sáng Theo Thời Gian Thực")
        fig_light_real_time = px.bar(
            st.session_state.data,
            x=st.session_state.data.index,
            y="light",
            title="Ánh sáng theo thời gian thực",
            labels={"index": "Thời Gian", "light": "Ánh Sáng (%)"},
            color="light",
            color_continuous_scale="Viridis"
        )
        st.plotly_chart(fig_light_real_time, use_container_width=True)
        
        st.subheader("🌡️ Đồ Thị Nhiệt Độ Theo Thời Gian Thực")
        fig_temp_real_time = px.line(
            st.session_state.data,
            x=st.session_state.data.index,
            y="temp",
            title="Nhiệt độ theo thời gian thực",
            labels={"index": "Thời Gian", "temp": "Nhiệt Độ (°C)"},
            markers=True
        )
        st.plotly_chart(fig_temp_real_time, use_container_width=True)

        # Hiển thị đồ thị trạng thái quạt và đèn
        st.subheader("🔄 Trạng Thái Thiết Bị Thời Gian Thực")

        # Chia thành 2 cột
        col1, col2 = st.columns(2)

        with col1:
            # Biểu đồ trạng thái quạt
            st.write("**Trạng Thái Quạt**")
            fig_fan_status = px.bar(
                st.session_state.data,
                x=st.session_state.data.index,
                y="fan",
                title="Trạng thái quạt theo thời gian",
                labels={"index": "Thời Gian", "fan": "Trạng Thái (0: Tắt, 1: Bật)"},
            )
            fig_fan_status.update_yaxes(dtick=1, title="Trạng Thái")
            st.plotly_chart(fig_fan_status, use_container_width=True)

        with col2:
            # Biểu đồ trạng thái đèn
            st.write("**Trạng Thái Đèn**")
            fig_led_status = px.bar(
                st.session_state.data,
                x=st.session_state.data.index,
                y="led",
                title="Trạng thái đèn theo thời gian",
                labels={"index": "Thời Gian", "led": "Trạng Thái (0: Tắt, 1: Bật)"},
            )
            fig_led_status.update_yaxes(dtick=1, title="Trạng Thái")
            st.plotly_chart(fig_led_status, use_container_width=True)
            
        # Hiển thị bảng dữ liệu
        st.subheader("📋 Dữ Liệu Trạng Thái Thiết Bị")
        st.dataframe(
            st.session_state.data.style.format({
                "light": "{:.0f}",
                "temp": "{:.2f}",
                "fan": "{:.0f}",
                "led": "{:.0f}",
            }),
            use_container_width=True
        )

    # Nếu streaming được bật, cập nhật liên tục
    if st.session_state.stream:
        show_latest_data()
        time.sleep(1)  # Tạm dừng 2 giây trước khi làm mới
        st.rerun()
    else:
        show_latest_data()
