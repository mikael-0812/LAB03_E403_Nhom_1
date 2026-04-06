import os
from html import escape
from typing import Dict

import streamlit as st

from src.app_runtime import (
    DYNAMIC_TOOLS_SCHEMA,
    TEST_CASES,
    get_default_model,
    initialize_provider,
    resolve_local_model_path,
    run_agent_with_trace,
    run_baseline,
)


def apply_custom_styles():
    st.markdown(
        """
        <style>
            .stApp {
                background:
                    radial-gradient(circle at top left, rgba(244, 180, 0, 0.18), transparent 32%),
                    radial-gradient(circle at top right, rgba(12, 118, 110, 0.16), transparent 28%),
                    linear-gradient(180deg, #f7f3ea 0%, #fffdf8 42%, #f3efe6 100%);
                color: #1e293b;
                font-family: "Aptos", "Segoe UI", sans-serif;
            }
            .block-container {
                padding-top: 2rem;
                padding-bottom: 2rem;
                max-width: 1180px;
            }
            h1, h2, h3 {
                font-family: "Georgia", "Times New Roman", serif;
                letter-spacing: -0.02em;
            }
            .hero-card {
                padding: 1.5rem 1.6rem;
                border-radius: 24px;
                background: rgba(255, 255, 255, 0.78);
                border: 1px solid rgba(15, 23, 42, 0.08);
                box-shadow: 0 18px 50px rgba(15, 23, 42, 0.08);
                backdrop-filter: blur(6px);
                margin-bottom: 1rem;
            }
            .hero-kicker {
                font-size: 0.86rem;
                text-transform: uppercase;
                letter-spacing: 0.16em;
                color: #0f766e;
                font-weight: 700;
                margin-bottom: 0.65rem;
            }
            .hero-title {
                font-size: 2.5rem;
                line-height: 1.1;
                color: #111827;
                margin: 0 0 0.75rem 0;
            }
            .hero-copy {
                font-size: 1.02rem;
                line-height: 1.75;
                color: #475569;
                margin: 0;
            }
            .metric-grid {
                display: grid;
                grid-template-columns: repeat(3, minmax(0, 1fr));
                gap: 0.9rem;
                margin: 1rem 0 1.4rem 0;
            }
            .metric-card {
                padding: 1rem 1.1rem;
                border-radius: 20px;
                background: rgba(255, 255, 255, 0.82);
                border: 1px solid rgba(15, 23, 42, 0.08);
            }
            .metric-label {
                font-size: 0.84rem;
                text-transform: uppercase;
                letter-spacing: 0.08em;
                color: #64748b;
                margin-bottom: 0.3rem;
            }
            .metric-value {
                font-size: 1.45rem;
                font-weight: 700;
                color: #0f172a;
            }
            .result-shell {
                padding: 1rem 1.1rem;
                border-radius: 20px;
                min-height: 240px;
                border: 1px solid rgba(15, 23, 42, 0.08);
                background: rgba(255, 255, 255, 0.88);
            }
            .result-title {
                font-size: 0.86rem;
                text-transform: uppercase;
                letter-spacing: 0.14em;
                color: #0f766e;
                font-weight: 700;
                margin-bottom: 0.85rem;
            }
            .trace-box {
                padding: 0.9rem 1rem;
                border-radius: 16px;
                background: #0f172a;
                color: #e2e8f0;
                font-family: "Consolas", "Menlo", monospace;
                font-size: 0.85rem;
                line-height: 1.7;
                white-space: pre-wrap;
            }
            .tool-card {
                padding: 0.95rem 1rem;
                border-radius: 18px;
                background: rgba(255, 255, 255, 0.8);
                border: 1px solid rgba(15, 23, 42, 0.08);
                margin-bottom: 0.8rem;
            }
            .tool-name {
                font-weight: 700;
                color: #111827;
                margin-bottom: 0.35rem;
            }
            .tool-desc {
                color: #475569;
                line-height: 1.6;
                font-size: 0.95rem;
            }
            @media (max-width: 900px) {
                .hero-title {
                    font-size: 2rem;
                }
                .metric-grid {
                    grid-template-columns: 1fr;
                }
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


@st.cache_resource(show_spinner=False)
def get_local_llm(model_path: str):
    return initialize_provider(provider="local", local_model_path=model_path)


def get_llm(provider: str, model_name: str, api_key: str, local_model_path: str):
    if provider == "local":
        return get_local_llm(local_model_path)
    return initialize_provider(
        provider=provider,
        model_name=model_name,
        api_key=api_key or None,
    )


def render_result_block(title: str, content: str):
    safe_title = escape(title)
    safe_content = escape(content).replace("\n", "<br>")
    st.markdown(
        f"""
        <div class="result-shell">
            <div class="result-title">{safe_title}</div>
            <div>{safe_content}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_trace_block(trace_lines):
    safe_trace = "<br>".join(escape(line) for line in trace_lines)
    st.markdown(
        f'<div class="trace-box">{safe_trace}</div>',
        unsafe_allow_html=True,
    )


def run_comparison(user_input: str, config: Dict[str, str], always_run_agent: bool):
    llm = get_llm(
        provider=config["provider"],
        model_name=config["model_name"],
        api_key=config["api_key"],
        local_model_path=config["local_model_path"],
    )
    baseline_answer = run_baseline(llm, user_input)

    if always_run_agent or "[UNSUPPORTED]" in baseline_answer:
        agent_answer, trace_lines = run_agent_with_trace(llm, user_input)
    else:
        agent_answer = f"(Dùng lại kết quả chatbot) {baseline_answer}"
        trace_lines = ["Agent không cần gọi tool vì Baseline đã xử lý được yêu cầu."]

    return baseline_answer, agent_answer, trace_lines


def main():
    st.set_page_config(
        page_title="LAB1 ReAct Agent UI",
        page_icon="🧠",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    apply_custom_styles()

    st.markdown(
        """
        <div class="hero-card">
            <div class="hero-kicker">LAB1 Interface</div>
            <h1 class="hero-title">Giao diện demo cho Chatbot vs ReAct Agent</h1>
            <p class="hero-copy">
                Màn hình này giúp bạn chạy nhanh các test case mẫu, so sánh Baseline Chatbot với ReAct Agent
                và theo dõi trace gọi tool trong cùng một nơi. Giao diện giữ nguyên logic dự án hiện có,
                nên bạn có thể vừa demo bài lab vừa tiếp tục phát triển từ mã nguồn cũ.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        f"""
        <div class="metric-grid">
            <div class="metric-card">
                <div class="metric-label">Test Cases</div>
                <div class="metric-value">{len(TEST_CASES)}</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Dynamic Tools</div>
                <div class="metric-value">{len(DYNAMIC_TOOLS_SCHEMA)}</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Luồng Demo</div>
                <div class="metric-value">Baseline + Agent</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    provider_options = {
        "OpenAI": "openai",
        "Gemini": "gemini",
        "Local GGUF": "local",
    }
    env_provider = os.getenv("DEFAULT_PROVIDER", "openai").lower()
    default_provider_index = list(provider_options.values()).index(
        env_provider if env_provider in provider_options.values() else "openai"
    )

    with st.sidebar:
        st.header("Cấu hình")
        provider_label = st.selectbox(
            "Provider",
            list(provider_options.keys()),
            index=default_provider_index,
        )
        provider = provider_options[provider_label]

        if provider == "openai":
            model_name = st.text_input(
                "Model OpenAI",
                value=get_default_model("openai"),
                key="openai_model_name",
            )
            api_key = st.text_input(
                "OPENAI_API_KEY",
                value=os.getenv("OPENAI_API_KEY", ""),
                type="password",
                key="openai_api_key",
            )
            local_model_path = resolve_local_model_path()
        elif provider == "gemini":
            model_name = st.text_input(
                "Model Gemini",
                value=get_default_model("gemini"),
                key="gemini_model_name",
            )
            api_key = st.text_input(
                "GEMINI_API_KEY",
                value=os.getenv("GEMINI_API_KEY", ""),
                type="password",
                key="gemini_api_key",
            )
            local_model_path = resolve_local_model_path()
        else:
            model_name = get_default_model("local")
            api_key = ""
            local_model_path = st.text_input(
                "Đường dẫn model GGUF",
                value=resolve_local_model_path(),
                key="local_model_path",
            )
            st.caption("UI sẽ cache model local để tránh load lại mỗi lần bấm chạy.")

        st.divider()
        always_run_agent = st.checkbox(
            "Luôn chạy ReAct Agent",
            value=True,
            help="Nếu bỏ chọn, Agent chỉ chạy khi Baseline trả về [UNSUPPORTED].",
        )
        st.caption(
            "Mẹo: với provider local, lần chạy đầu có thể chậm hơn vì cần nạp file GGUF."
        )

    config = {
        "provider": provider,
        "model_name": model_name,
        "api_key": api_key,
        "local_model_path": local_model_path,
    }

    test_case_tab, chat_tab, tool_tab = st.tabs(
        ["Chạy test case", "Chat tương tác", "Danh sách tools"]
    )

    with test_case_tab:
        selected_case = st.selectbox(
            "Chọn test case để demo",
            TEST_CASES,
            format_func=lambda item: f"{item['id']} - {item['description']}",
        )
        st.text_area(
            "Nội dung đầu vào",
            value=selected_case["input"],
            height=120,
            disabled=True,
        )

        if st.button("Chạy so sánh", type="primary", use_container_width=True):
            try:
                with st.spinner("Đang chạy Baseline và ReAct Agent..."):
                    baseline_answer, agent_answer, trace_lines = run_comparison(
                        selected_case["input"], config, always_run_agent
                    )

                left, right = st.columns(2)
                with left:
                    render_result_block("Baseline Chatbot", baseline_answer)
                with right:
                    render_result_block("ReAct Agent", agent_answer)

                with st.expander("Xem trace ReAct", expanded=True):
                    render_trace_block(trace_lines)
            except Exception as exc:
                st.error(f"Không thể chạy test case: {exc}")

    with chat_tab:
        if "chat_history" not in st.session_state:
            st.session_state.chat_history = []

        with st.form("chat_form", clear_on_submit=True):
            prompt = st.text_area(
                "Nhập câu hỏi để so sánh hai chế độ",
                placeholder="Ví dụ: Kiểm tra xem ở Paris hiện tại có khách sạn nào trống không?",
                height=120,
            )
            submitted = st.form_submit_button("Gửi yêu cầu", type="primary")

        if submitted:
            if not prompt.strip():
                st.warning("Bạn cần nhập câu hỏi trước khi chạy.")
            else:
                try:
                    with st.spinner("Agent đang xử lý yêu cầu của bạn..."):
                        baseline_answer, agent_answer, trace_lines = run_comparison(
                            prompt, config, always_run_agent
                        )
                    st.session_state.chat_history.insert(
                        0,
                        {
                            "prompt": prompt,
                            "baseline": baseline_answer,
                            "agent": agent_answer,
                            "trace": trace_lines,
                        },
                    )
                except Exception as exc:
                    st.error(f"Không thể xử lý yêu cầu: {exc}")

        for index, item in enumerate(st.session_state.chat_history):
            st.markdown(f"### Yêu cầu {len(st.session_state.chat_history) - index}")
            st.markdown(f"**Bạn hỏi:** {item['prompt']}")
            left, right = st.columns(2)
            with left:
                render_result_block("Baseline Chatbot", item["baseline"])
            with right:
                render_result_block("ReAct Agent", item["agent"])
            with st.expander("Trace chi tiết"):
                render_trace_block(item["trace"])

    with tool_tab:
        st.write(
            "Danh sách dưới đây được sinh động từ `tools.py`, nên khi bạn thêm tool mới, giao diện sẽ tự cập nhật."
        )
        for tool in DYNAMIC_TOOLS_SCHEMA:
            safe_name = escape(tool["name"])
            safe_desc = escape(tool["description"])
            st.markdown(
                f"""
                <div class="tool-card">
                    <div class="tool-name">{safe_name}</div>
                    <div class="tool-desc">{safe_desc}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )


if __name__ == "__main__":
    main()
