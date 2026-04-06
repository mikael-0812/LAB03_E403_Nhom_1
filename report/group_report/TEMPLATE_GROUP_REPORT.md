# Group Report: Lab 3 - Production-Grade Agentic System

- **Tên Nhóm**: Nhóm 1
- **Thành viên Nhóm**: (Các thành viên nhóm)
- **Repo Lab**: `mikael-0812/LAB03_E403_Nhom_1`
- **Ngày Triển Khai**: 2026-04-06

---

## 1. Tóm Tắt Dự Án (Executive Summary)

Dự án này ứng dụng luồng tư duy ReAct (Reasoning and Acting) nhằm vượt qua các giới hạn của Chatbot thuần túy (Baseline). Chúng em đã tích hợp thành công một Agent đa nhiệm có khả năng trỏ tới và sử dụng kho Database JSON khổng lồ tương tự môi trường doanh nghiệp thật (Banking, Courses, Fashion, Restaurants, Travel).

- **Tỷ Lệ Thành Công**: Đạt 100% trên 5 Test Cases tự động (tỷ lệ 5/5).
- **Kết Quả Cốt Lõi**: ReAct Agent đã chứng minh khả năng "tự thân vận động", giải quyết các truy vấn về tỷ giá, tìm kiếm khóa học và kiểm tra khách sạn hoàn toàn dựa trên dữ liệu thật. Cùng lúc đó, phần lớn các câu hỏi này Baseline Chatbot đều phải giơ cờ trắng `[UNSUPPORTED]` do thiếu chức năng truy cập thời gian thực.

---

## 2. Kiến Trúc Hệ Thống & Công Cụ (System Architecture & Tooling)

### 2.1 Cấu Trúc Vòng Lặp ReAct (ReAct Loop)
Hệ thống vận hành bằng vòng lặp **Thought -> Action -> Observation**:
- **Thought**: LLM trích xuất intent từ user và định hình công cụ tương lai.
- **Action**: Dịch JSON arguments và map chính xác vào tập hợp hàm Python.
- **Observation**: Ghi nhận kết quả nội bộ từ CSDL trả về, lặp lại cho đến lúc giải quyết xong hoặc tới điểm Stop `max_steps`.
- **Auto-Stop**: Tích hợp cờ hiệu `[OUT_OF_SCOPE]` để nhận diện các câu nằm ngoài tầm phủ sóng của Tool, cắt cầu dao tránh vòng lặp Vô cực và báo lỗi trực tiếp cho Terminal. Lọc Router thông minh không gọi Agent đối với những câu hỏi đơn giản (e.g. "1+1=2") mà Chatbot đã có khả năng đáp ứng.

### 2.2 Định Nghĩa Công Cụ (Tool Inventory)
Thay vì code tay, hệ thống ứng dụng **Dynamic Registry** với module `inspect` của Python, tự động đọc 14 danh sách hàm trong `tools.py` và auto-gen JSON Prompt tại runtime.

| Tool Name | Input Format | Use Case (Mục đích) |
| :--- | :--- | :--- |
| `currency_exchange` | `json` | Tra cứu tỷ giá chuyển đổi tiền tệ từ `banking.json`. |
| `check_inventory` | `json` | Kiểm tra tồn kho sản phẩm quần áo `fashion.json`. |
| `hotel_availability` | `json` | Kiểm tra khả năng đặt phòng cho điểm đến `travel.json`. |
| `course_prerequisites` | `json` | Check kỹ điều kiện tiên quyết của môn học `course.json`. |
| `location_search` | `json` | Quét quét hệ thống tìm nhà hàng tại khu vực `restaurant.json`. |

### 2.3 LLM Provider Áp Dụng
- **Primary (Chính)**: `gpt-4o` (OpenAI Model) - Setup tự động qua `demo.py`.
- **Secondary (Dự phòng)**: `gemini-1.5-flash` (Google GenAI) / Local GGUF phi-3.

---

## 3. Hệ Thống Viễn Trắc & Giám Sát Hiệu Năng (Telemetry)

Mọi log từ lúc Agent suy nghĩ chạy trong Interactive mode hay Auto_Test mode đều được track chuẩn Enterprise và ghi đè vào `comparison_report.txt` lẫn `logs/*.log`.

- **Audit JSON Logs**: Logging toàn bộ dưới dạng file `.log` JSON-lines phục vụ cho data streaming sau này.
- **Quản lý Token**: Đã tích hợp trích xuất `usage.total_tokens` trực tiếp vào hàm `log_step`.
- **Đầu ra Terminal**: Tracking từng bước với format `[TIMESTAMP] | [COMPONENT] | [ACTION] | [RESULT] | [Tokens: X]`

---

## 4. Phân Tích Lỗi Tiêu Biểu (Root Cause Analysis - RCA)

### Case Study: Lỗi Sai Tham Số Argument trong Bước Tra Cứu Tỷ Giá (Banking)
- **Input**: "Cho tôi biết tỷ giá hối đoái của tài khoản ACC011 là bao nhiêu?"
- **Observation Giai Đoạn 1**: Agent gọi Tool `currency_exchange({"account_id": "ACC011"})` nhưng Tool báo lỗi ValueError vi phạm chữ ký hàm `got an unexpected keyword argument 'account_id'`.
- **Phân Tích Cội Nguồn (Root Cause)**: Do định nghĩa hàm bị khuyết đối số truyền vào hoặc quá mơ hồ, LLM tự động suy diễn nên đã truyền bậy key `account_id` vào JSON string.
- **Tính Tự Phục Hồi Của Agent (Resilience)**: Thay vì sập toàn bộ script, ở `STEP_START: 2`, LLM tự đọc được mã lỗi trong *Observation*, sau đó tự nhận thức ở phần *Thought*: "It seems there is an issue with the argument... I will try calling the currency_exchange tool without any parameters...". Nhờ cơ chế nhận diện lỗi thông minh, nó đã tự động sửa sai ở Action kế tiếp và thành công trả về kết quả 0.84!

---

## 5. Đánh Giá Khác Biệt (Ablation Studies & Chatbot vs Agent)

### Thực Nghiệm Chatbot Cố Định vs ReAct Framework
| Case (Tình huống) | Kết quả Chatbot Truyền thống | Kết quả ReAct Agent | Người Chiến Thắng |
| :--- | :--- | :--- | :--- |
| Simple Q (Nền tảng) | Trả lời thành công (1+1=2) | Bypass luồng tool Agent (giữ nguyên kết quả Chatbot) | **Hoà (Draw)** |
| Multi-step Data | "Xin lỗi, tôi không thể cung cấp thông tin tỷ giá... `[UNSUPPORTED]`" | Trace thành công file JSON banking, fetch chính xác số liệu `0.84` | **Agent** |
| Out of Domain Range | Áo tưởng (Hallucinated) | Cắt cầu dao thông minh `[OUT_OF_SCOPE]` | **Agent** |

---

## 6. Đánh Giá Độ Sẵn Sàng (Production Readiness Review)

Hệ thống đã sẵn sàng được đưa lên môi trường Server ứng dụng (Production) với 3 lý do:

1. **Auto-Scaling (Khả Năng Nâng Cấp)**: Không cần đụng vào Prompt hay code Agent, Dev mới chỉ cần viết thêm hàm Python vào `tools.py` kèm Docstring chuẩn là Agent chủ động thu nạp thêm trí tuệ do cơ chế *Dynamic Rule Mapping*.
2. **Cơ Chế Bảo Vệ Hành Vi (Guardrails)**: Giới hạn cứng `max_steps=7` để chặn đứng vấn đề infinite loops gây đốt sạch tiền billing Tokens. Tự động `break` phiên session nếu nhận diện `[OUT_OF_SCOPE]` giúp tránh các cuộc tấn công prompt.
3. **Tracking Nhạy Bén**: Từng token, từng milli-giây trả về đều được log JSON giúp doanh nghiệp ước lượng biểu phí rõ ràng.
