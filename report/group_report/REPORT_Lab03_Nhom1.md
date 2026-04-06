# Group Report: Lab 3 - Production-Grade Agentic System

- **Tên Nhóm**: Nhóm 1
- **Thành viên Nhóm**: (Các thành viên nhóm)
- **Repo Lab**: `mikael-0812/LAB03_E403_Nhom_1`
- **Ngày Triển Khai**: 2026-04-06

---

## 1. Tóm Tắt Dự Án (Executive Summary)

Dự án này áp dụng mô hình ReAct (Reasoning and Acting) để mở rộng khả năng của chatbot truyền thống trong các bài toán cần truy xuất dữ liệu và thực hiện hành động thông qua tool. Nhóm đã xây dựng một ReAct Agent có thể kết nối tới các file database JSON theo nhiều domain như Banking, Courses, Fashion, Restaurants và Travel.

- **Kết quả tổng quan**: Hệ thống đã chạy được trên 5 test case chính và cho thấy sự khác biệt rõ giữa Baseline Chatbot và ReAct Agent trong các truy vấn cần dữ liệu thật.
- **Kết quả cốt lõi**: ReAct Agent có thể tra cứu dữ liệu từ database thông qua tool để xử lý các câu hỏi như tỷ giá, thông tin khóa học, khách sạn, nhà hàng hoặc sản phẩm. Trong khi đó, Baseline Chatbot chủ yếu phù hợp với các câu hỏi đơn giản hoặc câu hỏi không cần truy xuất dữ liệu ngoài.

---

## 2. Kiến Trúc Hệ Thống & Công Cụ (System Architecture & Tooling)

### 2.1 Cấu Trúc Vòng Lặp ReAct (ReAct Loop)

Hệ thống được tổ chức theo vòng lặp **Thought -> Action -> Observation -> Final Answer**:

- **Thought**: LLM phân tích yêu cầu người dùng và quyết định có cần dùng tool hay không.
- **Action**: Agent sinh tên tool và tham số đầu vào theo đúng format quy định.
- **Observation**: Kết quả thực thi tool được đưa trở lại prompt để agent suy luận tiếp.
- **Final Answer**: Khi đã đủ thông tin, agent trả lời người dùng.
- **Stop Condition**: Hệ thống có `max_steps` để tránh vòng lặp vô hạn. Ngoài ra, với các yêu cầu nằm ngoài phạm vi tool, agent có thể trả về tag `[OUT_OF_SCOPE]`.

Nhóm cũng bổ sung hai chế độ chạy:
- **Compare mode**: chạy song song Baseline Chatbot và ReAct Agent để so sánh.
- **Router mode**: Baseline xử lý trước, chỉ chuyển sang Agent khi câu hỏi vượt ngoài khả năng trả lời trực tiếp.

### 2.2 Định Nghĩa Công Cụ (Tool Inventory)

Hệ thống sử dụng **Dynamic Registry** để tự động quét các hàm trong `tools.py` và sinh tool schema cho agent tại runtime. Cách làm này giúp tránh việc hardcode toàn bộ danh sách tool trong prompt.

Một số tool tiêu biểu trong hệ thống:

| Tool Name | Input Format | Use Case (Mục đích) |
| :--- | :--- | :--- |
| `currency_exchange` | `json` | Tra cứu tỷ giá của tài khoản từ `banking.json` |
| `check_balance` | `json` | Kiểm tra số dư tài khoản trong `banking.json` |
| `hotel_availability` | `json` | Kiểm tra tình trạng khách sạn trong `travel.json` |
| `prerequisite_check` | `json` | Kiểm tra môn học tiên quyết trong `course.json` |
| `location_search` | `json` | Tìm nhà hàng theo khu vực trong `restaurant.json` |
| `search_fashion` | `json` | Tìm mặt hàng thời trang theo tiêu chí trong `fashion.json` |

### 2.3 LLM Provider Áp Dụng

Hệ thống hỗ trợ nhiều provider:

- **Primary**: `gpt-4o`
- **Secondary**: `gemini-1.5-flash`
- **Optional local mode**: Local GGUF model

Việc khởi tạo model được quản lý tập trung qua `demo.py` và `app_runtime.py`.

---

## 3. Hệ Thống Viễn Trắc & Giám Sát Hiệu Năng (Telemetry)

Nhóm sử dụng logging để theo dõi toàn bộ quá trình chạy của agent trong cả chế độ interactive lẫn test case tự động.

- **Structured Logging**: Log được ghi ra file `.log` và `comparison_report.txt` để phục vụ debug và đối chiếu kết quả.
- **Trace theo bước**: Ghi lại các bước như `AGENT_START`, `STEP_START`, `Thought`, `Action`, `Observation`, `Final Answer`, `AGENT_END`.
- **Báo cáo kết quả**: Kết quả của Baseline Chatbot và ReAct Agent được lưu song song để so sánh.

Hiện tại hệ thống đã có nền tảng telemetry tương đối rõ ràng, tuy nhiên phần token usage và cost tracking vẫn còn ở mức cơ bản và chưa hoàn toàn đồng nhất giữa các provider.

---

## 4. Phân Tích Lỗi Tiêu Biểu (Root Cause Analysis - RCA)

### Case Study: Lỗi Trace Logger Khi Chạy Agent

- **Input**: một số test case khi chạy agent với trace
- **Observation**: hệ thống gặp lỗi:
  `capture_log_step() got an unexpected keyword argument 'tokens'`

- **Phân Tích Cội Nguồn (Root Cause)**:  
  Trong `agent.py`, agent có gọi `logger.log_step(..., tokens=...)`, nhưng ở `app_runtime.py`, hàm wrapper `capture_log_step()` chỉ nhận đúng 3 tham số cơ bản. Điều này gây ra lỗi không nhất quán giữa lớp telemetry và agent runtime.

- **Ảnh Hưởng**:  
  Lỗi này làm agent bị dừng sớm trước khi hoàn thành tool execution, khiến việc kiểm tra các test case tiếp theo bị gián đoạn.

- **Cách Khắc Phục**:  
  Nhóm sửa theo một trong hai hướng:
  - bỏ tham số `tokens` khỏi `logger.log_step()`, hoặc
  - sửa wrapper để nhận thêm `*args, **kwargs`.

Sau khi sửa, trace của agent hoạt động ổn định hơn và có thể tiếp tục dùng để phân tích các lỗi khác trong ReAct loop.

---

## 5. Đánh Giá Khác Biệt (Ablation Studies & Chatbot vs Agent)

### So Sánh Baseline Chatbot và ReAct Agent

| Case (Tình huống) | Kết quả Chatbot Truyền thống | Kết quả ReAct Agent | Người Chiến Thắng |
| :--- | :--- | :--- | :--- |
| Câu hỏi đơn giản, không cần tool | Trả lời trực tiếp, nhanh | Có thể xử lý được nhưng không cần thiết | **Chatbot** |
| Truy vấn cần dữ liệu thật | Thường trả `[UNSUPPORTED]` hoặc trả lời chung chung | Có thể gọi tool và truy xuất đúng dữ liệu | **Agent** |
| Trường hợp ngoài phạm vi | Dễ trả lời mơ hồ hoặc không nhất quán | Có thể dừng bằng `[OUT_OF_SCOPE]` hoặc fallback rõ ràng hơn | **Agent** |

### Nhận xét

- **Chatbot** phù hợp với các câu hỏi một bước, không cần dữ liệu ngoài.
- **ReAct Agent** thể hiện rõ lợi thế ở các bài toán nhiều bước hoặc cần gọi tool.
- Tuy nhiên, Agent cũng nhạy cảm hơn với lỗi parser, lỗi tool spec, hoặc lỗi trong telemetry/logging.

---

## 6. Đánh Giá Độ Sẵn Sàng (Production Readiness Review)

Hệ thống hiện tại có một số đặc điểm phù hợp với định hướng production prototype, nhưng vẫn cần cải thiện thêm trước khi triển khai thực tế.

1. **Khả năng mở rộng**  
   Việc dùng dynamic registry giúp dễ thêm tool mới. Chỉ cần bổ sung hàm mới vào `tools.py` với docstring và tham số rõ ràng là agent có thể nhìn thấy tool mới thông qua schema sinh tự động.

2. **Guardrails cơ bản**  
   Hệ thống có `max_steps` để giảm nguy cơ loop vô hạn, đồng thời có cơ chế `[OUT_OF_SCOPE]` để dừng an toàn khi câu hỏi nằm ngoài phạm vi xử lý.

3. **Khả năng quan sát hệ thống**  
   Logging theo từng bước giúp nhóm dễ xác định lỗi nằm ở model, parser, tool hay runtime wrapper. Đây là một điểm mạnh khi phát triển agent system theo hướng thực nghiệm.

4. **Những điểm cần cải thiện thêm**  
   - Chuẩn hóa output của tất cả tool theo cùng một schema JSON.
   - Tách rõ hơn giữa tool metadata và runtime executor.
   - Xử lý tốt hơn các case fallback thay vì escalate quá sớm.
   - Cải thiện quản lý hội thoại nhiều lượt trong interactive mode.

---

## 7. Kết Luận

Qua bài lab này, nhóm nhận thấy ReAct Agent có lợi thế rõ rệt so với chatbot truyền thống trong các bài toán cần truy xuất dữ liệu và tương tác với môi trường thông qua tool. Tuy nhiên, để agent hoạt động ổn định, không chỉ cần model tốt mà còn cần một hạ tầng nhất quán giữa prompt, parser, tool schema, logging và runtime execution.

Bài học lớn nhất của nhóm là: chất lượng của một agent system không chỉ nằm ở câu trả lời cuối cùng, mà còn nằm ở cách hệ thống suy luận, gọi tool, phản ứng với observation, và xử lý lỗi trong toàn bộ vòng lặp.