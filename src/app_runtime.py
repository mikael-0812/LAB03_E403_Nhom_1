import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from dotenv import load_dotenv

from src.agent.agent import ReActAgent
from src.telemetry.logger import logger
from src.tools.dynamic_registry import DYNAMIC_TOOLS_SCHEMA

load_dotenv()

TEST_CASES = [
    {
        "id": "TC1",
        "description": "Fashion: Tìm quần áo có giá < 50.",
        "input": "Hãy tìm những sản phẩm thời trang có giá nhỏ hơn 50 giúp tôi nhé.",
    },
    {
        "id": "TC2",
        "description": "Course: Kiểm tra các môn tiên quyết của Course 81.",
        "input": "Cho tôi hỏi môn Course 81 có yêu cầu môn học tiên quyết nào không?",
    },
    {
        "id": "TC3",
        "description": "Restaurant: Tìm nhà hàng xung quanh khu vực District 1.",
        "input": "Liệt kê cho tôi vài quán ăn nằm ở District 1.",
    },
    {
        "id": "TC4",
        "description": "Travel: Tra cứu khả dụng khách sạn tại Paris.",
        "input": "Kiểm tra xem ở Paris hiện tại có khách sạn nào trống không?",
    },
    {
        "id": "TC5",
        "description": "Banking: Tra cứu tỷ giá hối đoái của tài khoản ACC011.",
        "input": "Cho tôi biết tỷ giá hối đoái của tài khoản ACC011 là bao nhiêu?",
    },
]

DEFAULT_MODELS = {
    "openai": "gpt-4o",
    "gemini": "gemini-1.5-flash",
    "local": "Phi-3-mini-4k-instruct-q4.gguf",
}


def _candidate_local_paths(explicit_path: Optional[str] = None) -> List[Path]:
    env_path = os.getenv("LOCAL_MODEL_PATH")
    default_name = "Phi-3-mini-4k-instruct-q4.gguf"
    candidates = [
        explicit_path,
        env_path,
        f"./models/{default_name}",
    ]
    ordered: List[Path] = []
    for candidate in candidates:
        if not candidate:
            continue
        path = Path(candidate)
        if path not in ordered:
            ordered.append(path)
    return ordered


def resolve_local_model_path(explicit_path: Optional[str] = None) -> str:
    candidates = _candidate_local_paths(explicit_path)
    for candidate in candidates:
        if candidate.exists():
            return str(candidate)
    if not candidates:
        return "./models/Phi-3-mini-4k-instruct-q4.gguf"
    return str(candidates[0])


def get_default_model(provider: str) -> str:
    provider_key = provider.lower()
    env_default = os.getenv("DEFAULT_MODEL")
    if env_default and os.getenv("DEFAULT_PROVIDER", "").lower() == provider_key:
        return env_default
    return DEFAULT_MODELS.get(provider_key, DEFAULT_MODELS["openai"])


def initialize_provider(
    provider: str,
    model_name: Optional[str] = None,
    api_key: Optional[str] = None,
    local_model_path: Optional[str] = None,
):
    provider_key = provider.lower()

    if provider_key == "openai":
        from src.core.openai_provider import OpenAIProvider

        return OpenAIProvider(
            model_name=model_name or get_default_model("openai"),
            api_key=api_key or os.getenv("OPENAI_API_KEY"),
        )

    if provider_key in {"gemini", "google"}:
        from src.core.gemini_provider import GeminiProvider

        return GeminiProvider(
            model_name=model_name or get_default_model("gemini"),
            api_key=api_key or os.getenv("GEMINI_API_KEY"),
        )

    if provider_key == "local":
        from src.core.local_provider import LocalProvider

        resolved_path = resolve_local_model_path(local_model_path)
        return LocalProvider(model_path=resolved_path)

    raise ValueError(f"Unsupported provider: {provider}")


def run_baseline(llm, user_input: str) -> str:
    system_prompt = (
        "You are a helpful chatbot. Answer the user explicitly and accurately based on "
        "your knowledge. If the user asks for real-time data, business-specific actions "
        "(like checking balance, searching items, bookings) or anything you cannot fulfill "
        "with just pre-trained text, you must end your response with exactly the tag: "
        "[UNSUPPORTED]"
    )
    response = llm.generate(user_input, system_prompt=system_prompt)
    return response.get("content", "Error generating response.")


def run_agent_with_trace(llm, user_input: str) -> Tuple[str, List[str]]:
    agent = ReActAgent(llm=llm, tools=DYNAMIC_TOOLS_SCHEMA)
    trace_lines: List[str] = []
    original_log_step = logger.log_step

    def capture_log_step(component: str, action: str, result: str):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        line = f"[{timestamp}] | [{component}] | [{action}] | [{result}]"
        trace_lines.append(line)
        logger.log_event("step", {"component": component, "action": action, "result": result})

    logger.log_step = capture_log_step
    try:
        final_answer = agent.run(user_input)
    finally:
        logger.log_step = original_log_step

    return final_answer, trace_lines


def append_case_report(
    report_path: str,
    case_id: str,
    description: str,
    user_input: str,
    baseline_answer: str,
    agent_answer: str,
    trace_lines: List[str],
):
    report_file = Path(report_path)
    header = "=== BÁO CÁO SO SÁNH CHATBOT TRUYỀN THỐNG VÀ REACT AGENT ===\n"
    if not report_file.exists():
        report_file.write_text(header, encoding="utf-8")

    with report_file.open("a", encoding="utf-8") as handle:
        handle.write(f"\n{'=' * 50}\n")
        handle.write(f"Test Case {case_id}: {description}\n")
        handle.write(f"USER INPUT: {user_input}\n")
        handle.write(f"{'-' * 50}\n")
        handle.write("[BASELINE CHATBOT RESULT]\n")
        handle.write(baseline_answer + "\n")
        handle.write(f"\n{'-' * 50}\n")
        handle.write("[REACT AGENT TRACE & RESULT]\n")
        for line in trace_lines:
            handle.write(line + "\n")
        handle.write(f"\n>> Final Answer: {agent_answer}\n")
