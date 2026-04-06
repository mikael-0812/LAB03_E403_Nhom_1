# LAB1: Chatbot vs ReAct Agent

Dự án này mô phỏng sự khác nhau giữa một chatbot LLM thông thường và một ReAct Agent có khả năng gọi tool để xử lý bài toán nhiều bước. Mình đã bổ sung thêm giao diện web để bạn demo trực quan ngay trên trình duyệt, đồng thời vẫn giữ `demo.py` để chạy bằng terminal như bản gốc.

## Tính năng hiện có

- So sánh `Baseline Chatbot` và `ReAct Agent` trên cùng một câu hỏi.
- Chạy nhanh 5 test case mẫu của bài lab.
- Chat tương tác trực tiếp với giao diện web.
- Hiển thị trace `Thought / Action / Observation` của agent.
- Tự động đọc danh sách tools từ `tools.py`.
- Hỗ trợ `OpenAI`, `Gemini` và `Local GGUF`.

## Cấu trúc quan trọng

- `app.py`: giao diện web bằng Streamlit.
- `demo.py`: chương trình CLI để tạo `comparison_report.txt` và chat trong terminal.
- `src/app_runtime.py`: lớp dùng chung để khởi tạo provider, chạy baseline và agent.
- `src/agent/agent.py`: vòng lặp ReAct.
- `tools.py`: các tool đọc dữ liệu từ thư mục `database/`.

## Cài đặt

### 1. Tạo môi trường và cài thư viện

```bash
pip install -r requirements.txt
```

### 2. Tạo file môi trường

```bash
cp .env.example .env
```

Sau đó điền API key nếu bạn dùng OpenAI hoặc Gemini.

Ví dụ:

```env
OPENAI_API_KEY=your_openai_api_key_here
GEMINI_API_KEY=your_gemini_api_key_here
DEFAULT_PROVIDER=openai
DEFAULT_MODEL=gpt-4o
LOCAL_MODEL_PATH=./models/Phi-3-mini-4k-instruct-q4.gguf
```

## Chạy giao diện web

Đây là cách chạy phù hợp nhất để demo LAB1:

```bash
streamlit run app.py
```

Sau khi chạy, giao diện sẽ cho phép:

- chọn provider
- nhập model name
- chạy test case mẫu
- chat tự do
- xem trace của ReAct Agent

## Chạy bản CLI

Nếu bạn muốn giữ cách chạy cũ:

```bash
python demo.py
```

Khi chạy xong, chương trình sẽ:

- tạo hoặc ghi lại `comparison_report.txt`
- chạy qua các test case mẫu
- mở chế độ chat trong terminal

## Chạy với local model

Dự án có hỗ trợ `llama-cpp-python` cho file GGUF.

### 1. Tải model

Tải model `Phi-3-mini-4k-instruct-q4.gguf` từ:

- https://huggingface.co/microsoft/Phi-3-mini-4k-instruct-gguf

### 2. Đặt model vào thư mục

Đặt model tại:

- `./models/Phi-3-mini-4k-instruct-q4.gguf`

Giao diện và CLI sẽ đọc từ `LOCAL_MODEL_PATH`. Nếu chưa cấu hình, hệ thống mặc định dùng đường dẫn trên.

### 3. Cập nhật `.env`

```env
DEFAULT_PROVIDER=local
LOCAL_MODEL_PATH=./models/Phi-3-mini-4k-instruct-q4.gguf
```

## Kiểm tra nhanh

```bash
pytest
```

Hoặc kiểm tra local provider riêng:

```bash
python tests/test_local.py
```

## Gợi ý demo khi nộp bài

Bạn có thể dùng ngay các câu sau trên giao diện:

1. `Hãy tìm những sản phẩm thời trang có giá nhỏ hơn 50 giúp tôi nhé.`
2. `Cho tôi hỏi môn Course 81 có yêu cầu môn học tiên quyết nào không?`
3. `Liệt kê cho tôi vài quán ăn nằm ở District 1.`
4. `Kiểm tra xem ở Paris hiện tại có khách sạn nào trống không?`
5. `Cho tôi biết tỷ giá hối đoái của tài khoản ACC011 là bao nhiêu?`

## Ghi chú

- Nếu dùng `OpenAI` hoặc `Gemini`, hãy chắc chắn API key hợp lệ.
- Nếu dùng `local`, lần chạy đầu có thể chậm do phải nạp model GGUF.
- `llama-cpp-python` có thể cần thời gian cài đặt lâu hơn các thư viện còn lại.
