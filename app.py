import os
from html import escape
from typing import Dict, List

import streamlit as st

from src.app_runtime import (
    get_default_model,
    initialize_provider,
    resolve_local_model_path,
    run_agent_with_trace,
)


def apply_chat_styles():
    st.markdown(
        """
        <style>
            :root {
                --chat-max-width: 48rem;
                --sidebar-width: 21rem;
            }
            .stApp {
                background: #f7f7f8;
                color: #111827;
            }
            .main .block-container {
                max-width: var(--chat-max-width);
                padding-top: 1.2rem;
                padding-bottom: 8rem;
            }
            section[data-testid="stSidebar"] {
                background: #202123;
            }
            section[data-testid="stSidebar"] * {
                color: #f3f4f6;
            }
            .chat-shell {
                margin: 0 auto 1.25rem auto;
            }
            .chat-header {
                display: flex;
                align-items: center;
                gap: 0.6rem;
                color: #6b7280;
                font-size: 0.92rem;
                margin-bottom: 0.75rem;
            }
            .chat-welcome {
                min-height: 52vh;
                display: flex;
                align-items: center;
                justify-content: center;
                text-align: center;
                color: #6b7280;
                padding: 1rem;
            }
            .chat-welcome h1 {
                margin: 0 0 0.5rem 0;
                font-size: 2.2rem;
                font-weight: 600;
                color: #111827;
                letter-spacing: -0.03em;
            }
            .chat-welcome p {
                margin: 0;
                font-size: 1rem;
                line-height: 1.7;
            }
            div[data-testid="stChatMessage"] {
                padding-left: 0;
                padding-right: 0;
            }
            div[data-testid="stChatMessageContent"] {
                font-size: 1rem;
                line-height: 1.75;
            }
            div[data-testid="stChatInput"] {
                position: fixed;
                left: 50%;
                bottom: 1rem;
                transform: translateX(-50%);
                width: min(var(--chat-max-width), calc(100vw - 2rem));
                z-index: 1000;
            }
            div[data-testid="stChatInput"] > div {
                border: 1px solid rgba(17, 24, 39, 0.08);
                border-radius: 1.1rem;
                background: rgba(255, 255, 255, 0.96);
                box-shadow: 0 18px 48px rgba(15, 23, 42, 0.12);
                backdrop-filter: blur(10px);
            }
            .trace-caption {
                color: #6b7280;
                font-size: 0.9rem;
            }
            .trace-box {
                padding: 0.95rem 1rem;
                border-radius: 0.9rem;
                background: #111827;
                color: #e5e7eb;
                font-family: "Consolas", "Menlo", monospace;
                font-size: 0.84rem;
                line-height: 1.7;
                white-space: pre-wrap;
            }
            .input-spacer {
                height: 6rem;
            }
            @media (min-width: 1100px) {
                section[data-testid="stSidebar"][aria-expanded="true"] ~ div[data-testid="stAppViewContainer"] div[data-testid="stChatInput"] {
                    left: calc(50% + (var(--sidebar-width) / 2));
                    width: min(var(--chat-max-width), calc(100vw - var(--sidebar-width) - 2rem));
                }
            }
            @media (max-width: 768px) {
                .main .block-container {
                    padding-top: 0.8rem;
                    padding-bottom: 7rem;
                }
                .chat-welcome h1 {
                    font-size: 1.8rem;
                }
                div[data-testid="stChatInput"] {
                    width: calc(100vw - 1rem);
                    bottom: 0.5rem;
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


def build_conversation_prompt(messages: List[Dict[str, str]], latest_user_input: str) -> str:
    if not messages:
        return latest_user_input

    transcript = [
        "Dưới đây là lịch sử hội thoại gần nhất. Hãy giữ đúng ngữ cảnh trước đó khi trả lời.",
        "",
    ]

    for message in messages[-12:]:
        speaker = "User" if message["role"] == "user" else "Assistant"
        transcript.append(f"{speaker}: {message['content']}")

    transcript.append("")
    transcript.append(f"User: {latest_user_input}")
    return "\n".join(transcript)


def render_trace_block(trace_lines: List[str]):
    safe_trace = "<br>".join(escape(line) for line in trace_lines)
    st.caption("Trace ReAct")
    st.markdown(
        f'<div class="trace-box">{safe_trace}</div>',
        unsafe_allow_html=True,
    )


def run_chat_turn(
    user_input: str,
    config: Dict[str, str],
    conversation_history: List[Dict[str, str]],
):
    prompt = build_conversation_prompt(conversation_history, user_input)
    llm = get_llm(
        provider=config["provider"],
        model_name=config["model_name"],
        api_key=config["api_key"],
        local_model_path=config["local_model_path"],
    )
    return run_agent_with_trace(llm, prompt)


def render_assistant_message(answer: str, trace_lines: List[str]):
    st.markdown(answer)
    with st.expander("Trace ReAct", expanded=False):
        render_trace_block(trace_lines)


def main():
    st.set_page_config(
        page_title="LAB1 ReAct Chat",
        page_icon="💬",
        layout="centered",
        initial_sidebar_state="collapsed",
    )
    apply_chat_styles()

    provider_options = {
        "OpenAI": "openai",
        "Gemini": "gemini",
        "Local GGUF": "local",
    }

    if "messages" not in st.session_state:
        st.session_state.messages = []

    with st.sidebar:
        st.subheader("Settings")
        provider_label = st.selectbox(
            "Provider",
            list(provider_options.keys()),
            index=list(provider_options.values()).index(
                os.getenv("DEFAULT_PROVIDER", "openai").lower()
                if os.getenv("DEFAULT_PROVIDER", "openai").lower() in provider_options.values()
                else "openai"
            ),
        )
        provider = provider_options[provider_label]

        if provider == "openai":
            model_name = st.text_input("Model", value=get_default_model("openai"))
            api_key = st.text_input(
                "OPENAI_API_KEY",
                value=os.getenv("OPENAI_API_KEY", ""),
                type="password",
            )
            local_model_path = resolve_local_model_path()
        elif provider == "gemini":
            model_name = st.text_input("Model", value=get_default_model("gemini"))
            api_key = st.text_input(
                "GEMINI_API_KEY",
                value=os.getenv("GEMINI_API_KEY", ""),
                type="password",
            )
            local_model_path = resolve_local_model_path()
        else:
            model_name = get_default_model("local")
            api_key = ""
            local_model_path = st.text_input(
                "GGUF Path",
                value=resolve_local_model_path(),
            )

        st.divider()
        if st.button("Clear conversation", use_container_width=True):
            st.session_state.messages = []
            st.rerun()

    config = {
        "provider": provider,
        "model_name": model_name,
        "api_key": api_key,
        "local_model_path": local_model_path,
    }

    st.markdown(
        """
        <div class="chat-shell">
            <div class="chat-header">LAB1 ReAct Agent</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if not st.session_state.messages:
        st.markdown(
            """
            <div class="chat-welcome">
                <div>
                    <h1>How can I help?</h1>
                    <p>Nhập câu hỏi của bạn để ReAct Agent trả lời và xem trace suy luận.</p>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            if message["role"] == "user":
                st.markdown(message["content"])
            else:
                render_assistant_message(message["content"], message["trace"])

    st.markdown('<div class="input-spacer"></div>', unsafe_allow_html=True)
    prompt = st.chat_input("Message ReAct Agent")

    if prompt:
        st.session_state.messages.append({"role": "user", "content": prompt})

        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            try:
                with st.spinner("Thinking..."):
                    history_context = st.session_state.messages[:-1]
                    answer, trace_lines = run_chat_turn(
                        prompt,
                        config,
                        conversation_history=history_context,
                    )
                render_assistant_message(answer, trace_lines)
            except Exception as exc:
                answer = f"Không thể xử lý yêu cầu: {exc}"
                trace_lines = [f"Error: {exc}"]
                st.error(answer)

        st.session_state.messages.append(
            {
                "role": "assistant",
                "content": answer,
                "trace": trace_lines,
            }
        )


if __name__ == "__main__":
    main()
