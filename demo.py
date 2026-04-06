import os
import sys
from dotenv import load_dotenv
from src.app_runtime import (
    TEST_CASES,
    get_default_model,
    initialize_provider,
    run_agent_with_trace,
    run_baseline,
)
from src.telemetry.logger import logger

# Load environment variables
load_dotenv()

def main():
    provider = os.getenv("DEFAULT_PROVIDER", "openai").lower()
    
    print(f"Initializing LLM with {provider} provider...")
    try:
        if provider == "openai" and not os.getenv("OPENAI_API_KEY"):
            print("WARNING: OPENAI_API_KEY not found.")
        if provider in {"gemini", "google"} and not os.getenv("GEMINI_API_KEY"):
            print("WARNING: GEMINI_API_KEY not found.")

        llm = initialize_provider(
            provider=provider,
            model_name=os.getenv("DEFAULT_MODEL", get_default_model(provider)),
        )
    except Exception as e:
        print(f"Failed to initialize LLM Provider: {str(e)}")
        sys.exit(1)

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
                agent_ans, trace_lines = run_agent_with_trace(llm, tc['input'])
                for log_line in trace_lines:
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

                    agent_ans, trace_lines = run_agent_with_trace(llm, user_input)
                    for log_line in trace_lines:
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
