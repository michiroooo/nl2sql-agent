"""Streamlit UI for AG2 Multi-Agent System."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import streamlit as st
from phoenix.otel import register
from openinference.instrumentation.openai import OpenAIInstrumentor

sys.path.append(str(Path(__file__).parent.parent / "function"))

from ag2_orchestrator import MultiAgentOrchestrator

# Initialize Phoenix tracing only once
if "tracer_initialized" not in st.session_state:
    phoenix_endpoint = os.getenv("PHOENIX_COLLECTOR_ENDPOINT", "http://phoenix:4317")

    tracer_provider = register(
        project_name="ag2-multi-agent",
        endpoint=phoenix_endpoint,
    )
    OpenAIInstrumentor().instrument(tracer_provider=tracer_provider)
    st.session_state.tracer_initialized = True

st.set_page_config(
    page_title="AG2 Multi-Agent System",
    page_icon="🤖",
    layout="wide",
)

st.title("🤖 AG2 Multi-Agent System")
st.markdown("複数のエージェントが協力してタスクを解決します")


@st.cache_resource
def get_orchestrator() -> MultiAgentOrchestrator:
    """Initialize and cache orchestrator instance.

    Returns:
        Configured MultiAgentOrchestrator instance.
    """
    return MultiAgentOrchestrator(
        work_dir=Path("/tmp/ag2_workspace"),
    )


if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("質問を入力してください（例：顧客数を教えて）"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("エージェントが協議中..."):
            orchestrator = get_orchestrator()
            result = orchestrator.execute(prompt)

            response = ""
            if result.get("success", False):
                response = result.get("output", "")
                st.markdown(response)

                with st.expander("🗨️ エージェント会話履歴"):
                    for msg in result.get("conversation", []):
                        agent_name = msg.get("name", "unknown")
                        content = msg.get("content", "")

                        if agent_name != "user":
                            st.markdown(f"**{agent_name}**:")
                            st.text(content[:500] + ("..." if len(content) > 500 else ""))
                            st.divider()

                with st.expander("👥 参加エージェント"):
                    agents = result.get("agents_involved", [])
                    st.write(", ".join(agents))
            else:
                error_msg = result.get("error", "Unknown error")
                st.error(f"エラー: {error_msg}")
                response = f"申し訳ございません。エラーが発生しました: {error_msg}"

    st.session_state.messages.append({"role": "assistant", "content": response})

with st.sidebar:
    st.header("🤖 システム情報")

    st.subheader("利用可能なエージェント")
    st.write("**SQL Specialist** 🗄️")
    st.caption("データベースクエリの専門家")

    st.write("**Web Researcher** 🌐")
    st.caption("Web情報収集の専門家")

    st.write("**Data Analyst** 📊")
    st.caption("分析・予測の専門家")

    st.divider()

    st.subheader("サンプルクエリ")

    samples = [
        "顧客数を教えて",
        "2024年で最も売れた商品は？",
        "最新のEコマーストレンドは？",
        "明日の売上を予測して",
    ]

    for sample in samples:
        if st.button(sample, key=sample, use_container_width=True):
            st.session_state.sample_query = sample
            st.rerun()

    st.divider()

    st.divider()

    if st.button("🔄 会話履歴をクリア", use_container_width=True):
        st.session_state.messages = []
        st.rerun()


if "sample_query" in st.session_state:
    sample = st.session_state.sample_query
    del st.session_state.sample_query
    st.session_state.messages.append({"role": "user", "content": sample})

    with st.chat_message("assistant"):
        with st.spinner("エージェントが協議中..."):
            orchestrator = get_orchestrator()
            result = orchestrator.execute(sample)

            if result.get("success", False):
                response = result.get("output", "")
                st.markdown(response)
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": response
                })
            else:
                error_msg = result.get("error", "Unknown error")
                st.error(f"エラー: {error_msg}")
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": f"エラーが発生しました: {error_msg}"
                })
