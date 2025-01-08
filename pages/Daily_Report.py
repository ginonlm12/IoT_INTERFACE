import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
from db_connect import get_statistics_by_date, analyze_on_time
import calendar

# Thiết lập giao diện Streamlit
st.set_page_config(
    page_title="Smart Home Dashboard",
    page_icon="📊",
    layout="wide"
)

st.title("📊 Smart Home Report")
st.write("Báo cáo chi tiết hệ thống nhà thông minh.")

# Sidebar: Lựa chọn chế độ báo cáo
report_mode = st.sidebar.radio(
    "Chọn chế độ báo cáo:",
    options=["Daily Report", "Monthly Report"]
)

if report_mode == "Daily Report":
    # Lựa chọn ngày
    st.sidebar.header("Lựa chọn ngày")
    date_input = st.sidebar.date_input("Chọn ngày", datetime.today())

    # Chuyển đổi ngày nhập thành string
    if not date_input:
        date_input = datetime.today()
    date_str = date_input.strftime("%Y-%m-%d")

    # Lấy dữ liệu thống kê
    # print(date_str)
    # print("----")
    statistics_df = get_statistics_by_date(date_str)
    # print("----")
    # print("fan:", statistics_df['fan_on_time'].iloc[0])
    fan_total, fan_power, fan_max_continuous = analyze_on_time(statistics_df['fan_on_time'].iloc[0], "fan")
    # print("led:", statistics_df['led_on_time'].iloc[0])
    led_total, led_power, led_max_continuous = analyze_on_time(statistics_df['led_on_time'].iloc[0], "led")
    #print('statistics_df:', statistics_df)

    if statistics_df is None or statistics_df.empty:
        st.warning("Không có dữ liệu nào cho ngày được chọn.")
    else:
        # Hiển thị tiêu đề báo cáo
        st.header(f"📊 Báo Cáo Thống Kê Ngày {statistics_df.loc[0, 'timestamp']}")

        # Giá trị trung bình
        st.subheader("📈 Giá Trị Trung Bình")
        st.table(statistics_df[["mean_light", "mean_temp"]].rename(columns={
            "mean_light": "Ánh Sáng Trung Bình",
            "mean_temp": "Nhiệt Độ Trung Bình"
        }))

        # Giá trị cực đại và cực tiểu
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("📉 Giá Trị Nhỏ Nhất")
            st.table(statistics_df[["min_light", "min_temp"]].rename(columns={
                "min_light": "Ánh Sáng Nhỏ Nhất",
                "min_temp": "Nhiệt Độ Nhỏ Nhất"
            }))
        with col2:
            st.subheader("📈 Giá Trị Lớn Nhất")
            st.table(statistics_df[["max_light", "max_temp"]].rename(columns={
                "max_light": "Ánh Sáng Lớn Nhất",
                "max_temp": "Nhiệt Độ Lớn Nhất"
            }))

        # Thay đổi lớn nhất
        st.subheader("🔄 Thay Đổi Lớn Nhất Trong Ngày")
        st.table(statistics_df[["max_change_light", "max_change_temp"]].rename(columns={
            "max_change_light": "Thay Đổi Ánh Sáng Lớn Nhất",
            "max_change_temp": "Thay Đổi Nhiệt Độ Lớn Nhất"
        }))

        # Phân tích dữ liệu
        st.subheader("📋 Phân Tích Dữ Liệu")
        analysis = []
        if statistics_df["mean_temp"].iloc[0] > 28:
            analysis.append("Nhiệt độ trung bình cao, có thể cần kiểm tra hệ thống làm mát.")
        elif statistics_df["mean_temp"].iloc[0] < 22:
            analysis.append("Nhiệt độ trung bình thấp, có thể cần tăng nhiệt độ để đảm bảo môi trường thoải mái.")
        else:
            analysis.append("Nhiệt độ trung bình ổn định, phù hợp với môi trường sống.")

        if statistics_df["max_change_light"].iloc[0] > 50:
            analysis.append("Ánh sáng thay đổi lớn trong ngày, có thể do môi trường bên ngoài hoặc điều chỉnh thủ công.")
        else:
            analysis.append("Ánh sáng thay đổi ít, môi trường ánh sáng ổn định.")

        for item in analysis:
            st.markdown(f"- {item}")
    
    # Hiển thị kết quả
    st.subheader("⏱️ Thời gian bật thiết bị và công suất tiêu thụ")

    # Hiển thị thông tin cho Quạt
    st.write(f"- **Tổng thời gian bật quạt:** {fan_total} giây")
    st.write(f"- **Ước tính công suất quạt:** {fan_power} Wh")
    st.write(f"- **Thời gian bật quạt liên tục lâu nhất:** {fan_max_continuous} giây")

    # Hiển thị thông tin cho Đèn
    st.write(f"- **Tổng thời gian bật đèn:** {led_total} giây")
    st.write(f"- **Ước tính công suất đèn:** {led_power} Wh")
    st.write(f"- **Thời gian bật đèn liên tục lâu nhất:** {led_max_continuous} giây")

elif report_mode == "Monthly Report":
    # Lựa chọn tháng
    st.sidebar.header("Lựa chọn tháng")
    month_input = st.sidebar.date_input("Chọn tháng", datetime.today())
    
    if not month_input:
        month_input = datetime.today()

    # Lấy chuỗi ngày tháng năm theo định dạng "%Y-%m" (ví dụ: "2025-01")
    month_str = month_input.strftime("%Y-%m")

# Tạo start_month từ ngày đầu tiên của tháng
    start_month = datetime.strptime(month_str + "-01", "%Y-%m-%d")

    # Xác định ngày cuối của tháng
    if start_month.month == 12:
        # Nếu tháng là tháng 12, chuyển sang tháng 1 của năm sau
        end_month = start_month.replace(year=start_month.year + 1, month=1, day=1) - timedelta(seconds=1)
    else:
        # Nếu không phải tháng 12, cộng 1 tháng
        end_month = start_month.replace(month=start_month.month + 1, day=1) - timedelta(seconds=1)

    # Lấy danh sách các ngày trong tháng
    days_in_month = pd.date_range(start=start_month, end=end_month, freq='D').strftime('%Y-%m-%d').tolist()

    # Tạo danh sách để chứa dữ liệu
    statistics_list = []

    # Lấy dữ liệu cho tất cả các ngày trong tháng
    for day in days_in_month:
        statistics_df = get_statistics_by_date(day)
        if statistics_df is not None and not statistics_df.empty:
            statistics_list.append(statistics_df)

    if statistics_list:
        # Chuyển danh sách các DataFrame thành một DataFrame duy nhất
        full_month_df = pd.concat(statistics_list)

        # Tính giá trị cực đại, cực tiểu trong tháng cho các trường
        max_data = full_month_df.max()
        min_data = full_month_df.min()

        # Tìm ngày có giá trị lớn nhất và nhỏ nhất
        max_day = full_month_df.loc[full_month_df['mean_light'] == max_data['mean_light']].iloc[0]['timestamp']
        min_day = full_month_df.loc[full_month_df['mean_light'] == min_data['mean_light']].iloc[0]['timestamp']

        # Hiển thị tiêu đề báo cáo tháng
        st.header(f"📊 Báo Cáo Thống Kê Tháng: {month_str}")
        
        # Hiển thị thông tin về giá trị cực đại và cực tiểu trong tháng
        st.subheader("📈 Giá Trị Lớn Nhất và Nhỏ Nhất")
        st.markdown(f"- **Ánh sáng lớn nhất trong tháng:** {max_data['mean_light']} vào ngày {max_day}")
        st.markdown(f"- **Ánh sáng nhỏ nhất trong tháng:** {min_data['mean_light']} vào ngày {min_day}")
        st.markdown(f"- **Nhiệt độ lớn nhất trong tháng:** {max_data['mean_temp']} vào ngày {max_day}")
        st.markdown(f"- **Nhiệt độ nhỏ nhất trong tháng:** {min_data['mean_temp']} vào ngày {min_day}")

        # Thêm các trường khác tương tự như trên
        # Ví dụ: fan_on_time, led_on_time, v.v.

        # Biểu đồ thống kê
        st.subheader("📉 Biểu Đồ Thống Kê Tháng")
        fig = px.line(
            full_month_df,
            x="timestamp",
            y="mean_light",
            title="Biểu đồ Ánh Sáng Trung Bình Trong Tháng",
            labels={"timestamp": "Ngày", "mean_light": "Ánh Sáng Trung Bình"}
        )
        st.plotly_chart(fig, use_container_width=True)

    else:
        st.warning("Không có dữ liệu nào cho tháng này.")