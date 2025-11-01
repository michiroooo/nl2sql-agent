"""Streamlit UI for NL2SQL Agent."""

from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

sys.path.append(str(Path(__file__).parent.parent / "function"))

from agent import NL2SQLAgent

st.set_page_config(
    page_title="NL2SQL Agent",
    page_icon="🔍",
    layout="wide",
)

st.title("🔍 NL2SQL Database Query Agent")
st.markdown("自然言語でデータベースに質問してください")


@st.cache_resource
def get_agent():
    """Initialize and cache the agent."""
    return NL2SQLAgent()


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
        with st.spinner("処理中..."):
            agent = get_agent()
            result = agent.process_query(prompt)

            if result["success"]:
                response = result["output"]
                st.markdown(response)

                with st.expander("📊 実行された SQL"):
                    st.code(result.get("sql", ""), language="sql")

                if "data" in result and result["data"]:
                    with st.expander("📈 データ詳細"):
                        st.dataframe(result["data"])
            else:
                st.error(f"エラー: {result['error']}")
                response = f"申し訳ございません。エラーが発生しました: {result['error']}"

    st.session_state.messages.append({"role": "assistant", "content": response})

with st.sidebar:
    st.header("📋 データベース情報")

    agent = get_agent()
    schema_info = agent.get_schema_info()

    for table in schema_info.get("tables", []):
        with st.expander(f"📊 {table['name']}"):
            st.markdown(f"**レコード数**: {table.get('row_count', 'N/A')}")
            st.markdown("**カラム**:")
            for col in table.get("columns", []):
                st.text(f"  • {col['name']} ({col['type']})")

    if st.button("🔄 会話履歴をクリア"):
        st.session_state.messages = []
        st.rerun()
