# Báo Cáo Cá Nhân: Lab 3 - Chatbot vs ReAct Agent

- **Họ và Tên**: Nguyễn Khánh Huyền
- **Mã Sinh Viên**: 2A202600171
- **Ngày**: 06.04.2026

---

## I. Đóng Góp Kỹ Thuật (15 Điểm)

- **Module Đã Lập Trình**: `tools.py`, `dynamic_registry.py`, `agent.py`, `app_runtime.py`, `demo.py`
- **Các Điểm Nổi Bật Trong Code**:
  - Bổ sung và chỉnh sửa các tool đọc dữ liệu thật từ thư mục `database/` thông qua `load_data()` trong `tools.py`.
  - Kiểm tra và sửa `dynamic_registry.py` để agent có thể sinh schema tool tự động và gọi tool động theo tên.
  - Hoàn thiện ReAct loop trong `agent.py` theo cấu trúc `Thought -> Action -> Observation -> Final Answer`.
  - Sửa `demo.py` để hỗ trợ hai mode chạy: `compare` và `router`.
  - Thêm logic interactive cho bài toán weather/fashion: nếu chưa lấy được thời tiết thực tế thì agent hỏi lại user mô tả thời tiết để tiếp tục gợi ý.

- **Tài Liệu Cấu Trúc**:
  Agent không truy cập database trực tiếp mà đi qua tool. Khi model sinh `Action`, agent gọi `_execute_tool()`, sau đó chuyển sang `execute_dynamic_tool()` trong registry. Registry sẽ gọi đúng hàm trong `tools.py`, và hàm đó mới đọc file JSON trong thư mục `database/`. Cách tách lớp này giúp hệ thống rõ ràng và dễ debug hơn.

---

## II. Case Study Về Sửa Lỗi (10 Điểm)

- **Mô Tả Vấn Đề**: Agent bị lỗi khi chạy trace với thông báo `capture_log_step() got an unexpected keyword argument 'tokens'`.

- **Nguồn Log**: `logs/YYYY-MM-DD.log`
  ```text
  Agent execution Error: capture_log_step() got an unexpected keyword argument 'tokens'
  ```

- **Chẩn Đoán**:
  Trong `agent.py`, tôi có gọi `logger.log_step(..., tokens=...)`, nhưng ở `app_runtime.py` hàm `capture_log_step()` chỉ nhận đúng 3 tham số. Đây là lỗi không nằm ở model hay tool, mà là lỗi không nhất quán giữa lớp agent và lớp telemetry.

- **Giải Pháp**:
  Tôi sửa lại theo hướng đơn giản hơn: bỏ tham số `tokens` ở `logger.log_step()` hoặc cập nhật wrapper để nhận thêm `*args, **kwargs`. Sau khi sửa, agent chạy trace ổn định hơn và tôi mới tiếp tục kiểm tra được luồng tool execution.

---

## III. Nhận Xét Cá Nhân: Chatbot vs ReAct (10 Điểm)

1. **Khả Năng Lập Luận (Reasoning)**:  
   Khối `Thought` giúp agent chia bài toán thành từng bước nhỏ và quyết định khi nào cần dùng tool. So với chatbot thường, agent có khả năng xử lý tốt hơn các câu hỏi cần dữ liệu thật như tra cứu banking, travel, hoặc fashion recommendation theo điều kiện cụ thể.

2. **Độ Tin Cậy (Reliability)**:  
   Agent có thể hoạt động tệ hơn chatbot trong các câu hỏi quá đơn giản hoặc khi thiết kế prompt/tool chưa ổn định. Ví dụ, nếu prompt escalation quá mạnh thì agent có thể gọi `escalate_to_human` ngay cả với lỗi weather API, trong khi chatbot chỉ cần trả lời mềm hơn.

3. **Khả Năng Quan Sát (Observation)**:  
   Observation từ tool là phần quan trọng nhất giúp agent đáng tin cậy hơn chatbot. Khi tool trả dữ liệu thật từ database, agent có thể dựa vào đó để trả lời thay vì tự bịa. Ngược lại, nếu observation là lỗi hoặc `None`, agent buộc phải đổi hướng xử lý, ví dụ hỏi lại user hoặc fallback an toàn.

---

## IV. Cải Tiến Trong Tương Lai (5 Điểm)

- **Khả Năng Mở Rộng (Scalability)**:  
  Tách rõ hơn giữa schema tool và runtime executor, đồng thời chuyển dữ liệu từ file JSON sang service/API riêng để giảm phụ thuộc vào đọc file trực tiếp.

- **Tính An Toàn (Safety)**:  
  Thiết kế rule escalation theo domain, ví dụ banking/payment mới cho phép escalate, còn weather/fashion chỉ nên fallback mềm hoặc hỏi lại user.

- **Hiệu Năng (Performance)**:  
  Chuẩn hóa output của mọi tool theo một format JSON thống nhất như `ok`, `error_type`, `message`, `data` để agent parse và reasoning ổn định hơn khi số lượng tool tăng lên.

---
