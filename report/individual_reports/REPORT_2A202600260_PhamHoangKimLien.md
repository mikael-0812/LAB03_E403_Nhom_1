# Báo Cáo Cá Nhân: Lab 3 - Chatbot vs ReAct Agent

- **Họ và Tên**: Liên Phạm
- **Mã Sinh Viên**: 2A202600260
- **Ngày**: 06/04/2026

---

## I. Đóng Góp Kỹ Thuật (15 Điểm)

*Mô tả các đóng góp cụ thể của bạn vào mã nguồn (ví dụ: phát triển một tool cụ thể, sửa lỗi parser, v.v.).*

- **Module Đã Lập Trình**: `src/tools/dynamic_registry.py`, `src/agent/react_agent.py`
- **Các Điểm Nổi Bật Trong Code**: 
  - Triển khai tính năng tự động khám phá công cụ (tool discovery) trong `dynamic_registry.py` sử dụng thư viện `inspect` của Python để tự động đăng ký các tool từ `mock_apis.py` mà không cần hardcode.
  - Xây dựng logic định tuyến (routing) để bỏ qua vòng lặp ReAct đối với các câu hỏi cơ bản và trực tiếp gọi chatbot tiêu chuẩn.
- **Tài Liệu Cấu Trúc**: 
  Dynamic registry quét module `tools` và trích xuất các hàm được decorator định nghĩa là tool, đọc tham số và docstring của chúng. Trong quá trình chạy ReAct loop, agent được cung cấp một file json schema miêu tả toàn bộ tool auto-generated này để agent có thể chọn đúng công cụ thích hợp. Nếu câu hỏi không khớp với tool nào, agent sẽ tự động dừng an toàn hoặc chuyển hướng sang phiên chat tiêu chuẩn.

---

## II. Case Study Về Sửa Lỗi (10 Điểm)

*Phân tích một lỗi cụ thể bạn gặp phải trong quá trình làm bài lab qua hệ thống log.*

- **Mô Tả Vấn Đề**: Agent bị kẹt trong vòng lặp vô hạn khi liên tục dự đoán `Action: search_database(None)` mà không tạo ra tiến độ gì mới.
- **Nguồn Log**: `logs/YYYY-MM-DD.log`
  ```text
  [WARNING] ReAct Loop iteration 4: Action search_database(None) failed: Missing required argument 'query'.
  [INFO] Agent Thought: I should try searching the database again to see if it works.
  [WARNING] ReAct Loop iteration 5: Action search_database(None) failed: Missing required argument 'query'.
  ```
- **Chẩn Đoán**: LLM không trích xuất đúng tham số entity từ câu prompt của người dùng do phần mô tả schema của tool chưa đủ rõ ràng về định dạng kỳ vọng của tham số `query`. Do đó, nó truyền `None` và bị lỗi, nhưng khả năng tự sửa cấu trúc (auto-correction) của model qua prompt mặc định là chưa đủ mạnh.
- **Giải Pháp**: Cập nhật lại docstring của hàm trong `mock_apis.py` để bổ sung mô tả gợi ý loại biến (type hint) chi tiết nhất cho tham số `query`. Đồng thời, thêm một ví dụ phủ định (negative example) riêng vào ReAct system prompt nhằm hướng dẫn agent cách xử lý khi một tool trả về lỗi.

---

## III. Nhận Xét Cá Nhân: Chatbot vs ReAct (10 Điểm)

*Đánh giá sự khác biệt về khả năng lập luận.*

1.  **Khả Năng Lập Luận (Reasoning)**: Khối `Thought` (Suy nghĩ) đóng vai trò như một "bản nháp", cho phép agent ReAct lập kế hoạch cho bước đi tiếp theo, chia nhỏ các truy vấn phức tạp gồm nhiều bước và nhìn nhận lại xem liệu mình đã có đủ thông tin hay chưa. Ngược lại, Chatbot tiêu chuẩn thường dễ bị ảo giác (hallucinate) sinh ra những thông tin không có thực vì không có bộ não hay nền tảng kiến thức nội bộ thực sự để kiểm chứng.
2.  **Độ Tin Cậy (Reliability)**: Thực tếAgent còn hoạt động *tệ hơn* Chatbot khi đối mặt với những câu thoại giao tiếp quá mức cơ bản (như "Xin chào, bạn khỏe không?"). ReAct agent đôi lúc cố gắng tìm kiếm một công cụ giải thích cách "trả lời câu chào" rồi thất bại, trong khi Chatbot thường phản hồi một cách tự nhiên. Hiện tượng này khẳng định sự quan trọng của bộ định tuyến (bypass router) để phân loại tin nhắn.
3.  **Khả Năng Quan Sát (Observation)**: Phản hồi từ môi trường (các observation dưới dạng JSON lấy từ `mock_apis`) liên kết agent một cách hiệu quả với thực tế. Khi observation không thể trả về dữ liệu, agent đã phản hồi rất chuẩn xác trong thought như "Tìm kiếm không đem lại kết quả gì, tôi phải báo cho người dùng", thay vì cố gắng tự chế số liệu giả, mở ra một bước tiến cực lớn về độ cậy của dữ liệu thật.

---

## IV. Cải Tiến Trong Tương Lai (5 Điểm)

*Làm thế nào để mở rộng quy mô hệ thống AI Agent này để áp dụng cho môi trường Production?*

- **Khả Năng Mở Rộng (Scalability)**: Tách ReAct agent khỏi luồng thực thi đồng bộ bằng cách thêm một hàng đợi sự kiện event queue (ví dụ: Celery/RabbitMQ). Các tool tốn nhiều thời gian xử lý (như cạo dữ liệu web crawl) nên được thực thi bất đồng bộ.
- **Tính An Toàn (Safety)**: Tích hợp một hệ thống đa tác vụ dual-agent setup, trong đó bao gồm một LLM giám sát với chi phí rẻ hơn đóng vai trò (màng lọc an toàn). Nhiệm vụ của LLM supervisor là kiểm duyệt các `Action` của Agent có thể gây nguy hiểm (chẳng hạn như kiểm tra và ngăn chặn các hành vi `drop_table` làm mất mát dữ liệu).
- **Hiệu Năng (Performance)**: Khi số lượng tool ngày càng vượt mốc con số hàng nghìn, hãy đem lưu cấu trúc của toàn bộ tools vào Vector Database, thay vì đưa toàn bộ tool schema vào thẳng system prompt. Tích hợp chạy semantic search lên yêu cầu của người dùng để chỉ đưa về nhóm top K tool schema mang lại liên kết tốt nhất đổ vào luồng suy nghĩ của Agent nhằm giảm tải.
