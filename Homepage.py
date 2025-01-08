import streamlit as st

st.set_page_config(
    page_title="Hello",
    page_icon="👋",
)

st.write("# Welcome to QLTT Smart Livestock Management System!👋")

st.sidebar.success("Select a demo above.")

st.markdown(
    """
    Nền tảng của QLTT cho phép bạn:
    
    ### Cập nhật thông tin mới nhất về:
    - [Thiết bị thông minh](https://www.smartthings.com/)
    - [Hệ thống điều khiển](https://www.control4.com/)
    - [IoT trong nhà ở](https://www.iotforall.com/)
    ### Tương tác với trợ lý ảo thông minh:
    - Hỏi đáp về tình trạng nhiệt độ và ánh sáng hiện tại
    - Nghe nhận xét về tình trạng môi trường trong ngày
    - Bật/ tắt đèn theo yêu cầu
"""
)