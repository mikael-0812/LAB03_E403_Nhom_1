import os
import sys
from dotenv import load_dotenv
from src.core.gemini_provider import GeminiProvider
from src.core.openai_provider import OpenAIProvider
from src.agent.agent import ReActAgent
from src.tools.dynamic_registry import DYNAMIC_TOOLS_SCHEMA
from src.telemetry.logger import logger

# Load environment variables
load_dotenv()

TEST_CASES = [
    {
        "id": "TC1",
        "description": "Fashion: Tìm quần áo có giá < 50.",
        "input": "Hãy tìm những sản phẩm thời trang có giá nhỏ hơn 50 giúp tôi nhé."
    },
    {
        "id": "TC2",
        "description": "Course: Kiểm tra các môn tiên quyết của Course 81.",
        "input": "Cho tôi hỏi môn Course 81 có yêu cầu môn học tiên quyết nào không?"
    },
    {
        "id": "TC3",
        "description": "Restaurant: Tìm nhà hàng xung quanh khu vực District 1.",
        "input": "Liệt kê cho tôi vài quán ăn nằm ở District 1."
    },
    {
        "id": "TC4",
        "description": "Travel: Tra cứu khả dụng khách sạn tại Paris.",
        "input": "Kiểm tra xem ở Paris hiện tại có khách sạn nào trống không?"
    },
    {
        "id": "TC5",
        "description": "Banking: Tra cứu tỷ giá hối đoái của tài khoản ACC011.",
        "input": "Cho tôi biết tỷ giá hối đoái của tài khoản ACC011 là bao nhiêu?"
    }
]

def capture_logs_to_file(logs_buffer, component, action, result):
    """Custom format for capturing logs to comparison_report.txt"""
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    logs_buffer.append(f"[{timestamp}] | [{component}] | [{action}] | [{result}]")

def run_baseline(llm, user_input):
    """Runs the prompt directly against the LLM without tools."""
    system_prompt = "You are a helpful chatbot. Answer the user explicitly and accurately based on your knowledge. If the user asks for real-time data, business-specific actions (like checking balance, searching items, bookings) or anything you cannot fulfill with just pre-trained text, you must end your response with exactly the tag: [UNSUPPORTED]"
    response = llm.generate(user_input, system_prompt=system_prompt)
    return response.get("content", "Error generating response.")

def main():
    provider = os.getenv("DEFAULT_PROVIDER", "openai").lower()
    
    print(f"Initializing LLM with {provider} provider...")
    try:
        if provider == "openai":
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                print("WARNING: OPENAI_API_KEY not found.")
            llm = OpenAIProvider(model_name=os.getenv("DEFAULT_MODEL", "gpt-4o"), api_key=api_key)
        else:
            api_key = os.getenv("GEMINI_API_KEY")
            if not api_key or api_key == "your_gemini_api_key_here":
                print("WARNING: GEMINI_API_KEY not found.")
            llm = GeminiProvider(model_name=os.getenv("DEFAULT_MODEL", "gemini-1.5-flash"), api_key=api_key)
    except Exception as e:
        print(f"Failed to initialize LLM Provider: {str(e)}")
        sys.exit(1)

    print("Initializing ReAct Agent...")
    agent = ReActAgent(llm=llm, tools=DYNAMIC_TOOLS_SCHEMA)

    with open("comparison_report.txt", "w", encoding="utf-8") as report_file:
        report_file.write("=== BÁO CÁO SO SÁNH CHATBOT TRUYỀN THỐNG VÀ REACT AGENT ===\n")
        
        for tc in TEST_CASES:
            logger.log_event("TEST_CASE_START", {"id": tc['id'], "description": tc['description'], "input": tc['input']})
            print(f"\n{'='*50}\nRunning {tc['id']}: {tc['description']}")
            report_file.write(f"\n{'='*50}\n")
            report_file.write(f"Test Case {tc['id']}: {tc['description']}\n")
            report_file.write(f"USER INPUT: {tc['input']}\n")
            report_file.write(f"{'-'*50}\n")
            
            # --- BASELINE RUN ---
            print("\n[BASELINE CHATBOT]")
            report_file.write("[BASELINE CHATBOT RESULT]\n")
            try:
                baseline_ans = run_baseline(llm, tc['input'])
                logger.log_event("BASELINE_END", {"final_answer": baseline_ans})
                print(baseline_ans)
                report_file.write(baseline_ans + "\n")
            except Exception as e:
                error_msg = f"API Error: {str(e)}"
                print(error_msg)
                report_file.write(error_msg + "\n")
                
            report_file.write(f"\n{'-'*50}\n")
            
            # --- REACT AGENT RUN ---
            print("\n[REACT AGENT TRACE]")
            report_file.write("[REACT AGENT TRACE & RESULT]\n")

            try:
                # Capture standard output locally for the report
                # By hijacking the logger temporarily
                original_log_step = logger.log_step
                logs_buffer = []

                def custom_log_step(component, action, result):
                    original_log_step(component, action, result)
                    capture_logs_to_file(logs_buffer, component, action, result)

                logger.log_step = custom_log_step

                # Run Agent
                agent_ans = agent.run(tc['input'])

                # Restore logger
                logger.log_step = original_log_step

                for log_line in logs_buffer:
                    report_file.write(log_line + "\n")
                    
                report_file.write(f"\n>> Final Answer: {agent_ans}\n")
                print(f"\n>> Agent Final Answer: {agent_ans}")
                
            except Exception as e:
                error_msg = f"Agent execution Error: {str(e)}"
                print(error_msg)
                report_file.write(error_msg + "\n")

    print("\n[DONE] Kết quả đã được lưu tại comparison_report.txt")
    
    print("\n" + "="*50)
    print("Bắt đầu chế độ tương tác (Nhập 'exit' hoặc 'quit' để thoát)")
    print("="*50)
    
    with open("comparison_report.txt", "a", encoding="utf-8") as report_file:
        while True:
            try:
                user_input = input("\nBạn: ")
                if not user_input.strip():
                    continue
                if user_input.strip().lower() in ['exit', 'quit']:
                    break
                
                logger.log_event("USER_REQUEST_INTERACTIVE", {"input": user_input})    
                report_file.write(f"\n{'='*50}\nUSER INPUT (Interactive): {user_input}\n{'-'*50}\n")
                
                # BASELINE CHATBOT LOGIC
                print("\n[BASELINE CHATBOT]")
                report_file.write("[BASELINE CHATBOT RESULT]\n")
                baseline_ans = run_baseline(llm, user_input)
                logger.log_event("BASELINE_END", {"final_answer": baseline_ans})
                print(baseline_ans)
                report_file.write(baseline_ans + "\n")
                report_file.write(f"\n{'-'*50}\n")
                
                if "[UNSUPPORTED]" not in baseline_ans:
                    print("\n[REACT AGENT]")
                    msg = f">> Agent Final Answer: (Sử dụng kết quả Chatbot) {baseline_ans}"
                    print(msg)
                    report_file.write(f"[REACT AGENT RESULT]\n{msg}\n")
                else:
                    print("\n[REACT AGENT ĐANG XỬ LÝ...]")
                    report_file.write("[REACT AGENT TRACE & RESULT]\n")
                    
                    original_log_step = logger.log_step
                    logs_buffer = []
                    def custom_log_step(component, action, result):
                        original_log_step(component, action, result)
                        capture_logs_to_file(logs_buffer, component, action, result)
                    logger.log_step = custom_log_step
                    
                    agent_ans = agent.run(user_input)
                    
                    logger.log_step = original_log_step
                    for log_line in logs_buffer:
                        report_file.write(log_line + "\n")
                        
                    report_file.write(f"\n>> Final Answer: {agent_ans}\n")
                    print(f"\n>> Trả lời: {agent_ans}")
                    
                    if "[OUT_OF_SCOPE]" in agent_ans:
                        print("\n[SYSTEM] Yêu cầu nằm ngoài phạm vi công cụ hiện có. Dừng hệ thống.")
                        report_file.write("[SYSTEM] OUT_OF_SCOPE Detected. Terminating.\n")
                        break
                
            except KeyboardInterrupt:
                print("\nĐã thoát chế độ tương tác.")
                break
            except Exception as e:
                print(f"\nLỗi: {str(e)}")

if __name__ == "__main__":
    main()
