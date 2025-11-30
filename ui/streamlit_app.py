# -*- coding: utf-8 -*-
"""Streamlit UI for HR Assistant Agent (ASCII-safe)."""

import streamlit as st
import sys
from pathlib import Path
import time

project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

try:
    from tools.policy_rag.mcp_tool import PolicySearchTool
    from tools.policy_rag.rag_engine import RAGEngine, ConversationManager
    from mcp_server.server import MCPServer, MCPRouter
    from tools.resume_screening.mcp_tool import mcp_rank_resumes
except Exception as e:
    st.write("Import error:", e)
    st.stop()

st.set_page_config(page_title="HR Assistant Agent", layout="wide", initial_sidebar_state="expanded")

@st.cache_resource
def initialize_components():
    try:
        server = MCPServer()
        router = MCPRouter(server)
        rag_engine = RAGEngine()
        policy_tool = PolicySearchTool()
        conv_manager = ConversationManager()
        return {
            "server": server,
            "router": router,
            "rag_engine": rag_engine,
            "policy_tool": policy_tool,
            "conv_manager": conv_manager,
        }
    except Exception as exc:
        st.error(f"Failed to initialize components: {exc}")
        return None


def display_message(role, content, metadata=None):
    st.markdown(f"**{'You' if role=='user' else 'HR Assistant'}:**\n\n{content}")
    if role == "assistant" and metadata:
        if metadata.get("chunks_details"):
            with st.expander("Sources and Citations"):
                for i, chunk in enumerate(metadata["chunks_details"], 1):
                    st.write(f"Source {i}: {chunk.get('filename','Unknown')} (Page {chunk.get('page','?')}, Score: {chunk.get('score',0):.2f})")
                    st.write((chunk.get("text", "")[:200] + "...").strip())
        if metadata.get("tokens_used"):
            st.caption(f"Response used {metadata['tokens_used']} tokens")


def main():
    st.title("HR Assistant Agent")
    st.write("Ask questions about company policies, benefits, HR procedures, or track onboarding.")
    tab_policies, tab_resumes, tab_onboarding = st.tabs(["Policies", "Resume Screening", "Onboarding"])
    components = initialize_components()
    if not components:
        st.error("System initialization failed. Check logs and try again.")
        return

    with st.sidebar:
        st.header("System Status")
        health = components["server"].health_check()
        if health.get("server_status") == "healthy":
            st.success("System is healthy")
        else:
            st.error("System issues detected")

        try:
            stats = components["policy_tool"].get_database_stats()
            if stats and not stats.get("error"):
                st.write("Total chunks:", stats.get("total_chunks", 0))
                st.write("Documents:", stats.get("unique_documents", 0))
                st.write("Collection:", stats.get("collection_name", "Unknown"))
            else:
                st.warning("Database statistics unavailable")
        except Exception as exc:
            st.warning(f"Could not load database stats: {exc}")

        st.header("Settings")
        max_results = st.slider("Max search results", 1, 10, 5, key="max_results_slider")
        show_debug = st.checkbox("Show debug info", False)

        st.header("Controls")
        clear_clicked = st.button("Clear Conversation", key="clear_btn")
        if clear_clicked:
            if "user_id" in st.session_state:
                components["conv_manager"].clear_history(st.session_state.user_id)
            st.session_state.messages = []
            st.rerun()

    with tab_policies:
        if "messages" not in st.session_state:
            st.session_state.messages = []
        if "user_id" not in st.session_state:
            st.session_state.user_id = f"user_{int(time.time())}"
        # Ensure user_input key exists before widget instantiation to avoid post-creation mutation errors
        if "user_input" not in st.session_state:
            st.session_state["user_input"] = ""
        if st.session_state.messages:
            st.subheader("Conversation")
            for m in st.session_state.messages:
                display_message(m["role"], m["content"], m.get("metadata"))
        else:
            st.info("Welcome! Ask any HR-related question to get started.")
        st.subheader("Ask a Question")
        user_input = st.text_area(
            "Your question:",
            placeholder="e.g., How many vacation days do I get?",
            height=100,
            key="user_input",
        )
        ask_button = st.button("Ask Question", key="ask_btn")
        if ask_button and user_input.strip():
            with st.spinner("Thinking..."):
                try:
                    st.session_state.messages.append({"role": "user", "content": user_input})
                    components["conv_manager"].add_turn(st.session_state.user_id, "user", user_input)
                    search_result = components["policy_tool"].search_policies(user_input, top_k=max_results)
                    if show_debug:
                        st.expander("Debug: Search Results").json(search_result)
                    conversation_history = components["conv_manager"].get_history(st.session_state.user_id)[:-1]
                    rag_response = components["rag_engine"].generate_response(user_input, search_result.get("chunks", []), conversation_history)
                    if show_debug:
                        st.expander("Debug: RAG Response").json(rag_response)
                    if rag_response["success"]:
                        response_text = rag_response["response"]
                        st.session_state.messages.append({"role": "assistant", "content": response_text, "metadata": rag_response})
                        components["conv_manager"].add_turn(st.session_state.user_id, "assistant", response_text)
                    else:
                        err = rag_response.get("error", "Unknown error")
                        st.session_state.messages.append({"role": "assistant", "content": f"Error: {err}"})
                    # Clear input safely before rerun without triggering mutation error
                    st.session_state["user_input"] = ""
                    st.rerun()
                except Exception as exc:
                    # Suppress raw errors in frontend; log internally instead
                    print(f"Internal error while processing question: {exc}", file=sys.stderr)
                    st.session_state.messages.append({"role": "assistant", "content": "Technical issue encountered. Please retry shortly."})
                    st.rerun()
        elif ask_button and not user_input.strip():
            st.warning("Please enter a question before clicking 'Ask Question'.")

    with tab_resumes:
        st.subheader("Rank Candidates")
        jd_text = st.text_area("Job Description", placeholder="Paste the job description here", key="jd_text")
        skills_input = st.text_input("Target Skills (comma-separated)", value="", key="skills_input")
        skills = [s.strip() for s in skills_input.split(",") if s.strip()] if skills_input else []
        uploaded_files = st.file_uploader("Upload resumes (PDF or TXT)", type=["pdf", "txt"], accept_multiple_files=True)
        rank_btn = st.button("Rank Candidates", key="rank_btn", disabled=not uploaded_files or not jd_text.strip())
        if rank_btn:
            resumes_payload = [{"filename": f.name, "content": f.getvalue()} for f in uploaded_files]
            jd_payload = {"text": jd_text, "skills": skills}
            with st.spinner("Scoring resumes..."):
                ranked = mcp_rank_resumes(resumes_payload, jd_payload)
            st.success(f"Ranked {len(ranked)} candidates")
            for i, cand in enumerate(ranked, start=1):
                st.markdown(f"**{i}. {cand['filename']}** - Score: `{cand['score']:.3f}`")
                if cand.get("matched_skills"):
                    st.caption("Matched skills: " + ", ".join(cand["matched_skills"]))
                with st.expander("Top snippets"):
                    for snip in cand.get("top_snippets", [])[:3]:
                        st.write(snip)

    # Onboarding Tab
    with tab_onboarding:
        st.subheader("Onboarding Tasks")
        from pathlib import Path as _P
        tasks_file = _P(project_root / "data" / "onboarding_tasks.json")
        if "onboarding_role" not in st.session_state:
            st.session_state.onboarding_role = "engineering"
        # Load roles
        try:
            if tasks_file.exists():
                raw = tasks_file.read_text(encoding="utf-8")
                import json as _json
                data = _json.loads(raw)
                roles = list(data.keys())
            else:
                data, roles = {}, []
        except Exception as exc:
            roles, data = [], {}
            print(f"Failed to load onboarding tasks: {exc}", file=sys.stderr)
        role = st.selectbox("Role", roles, index=roles.index(st.session_state.onboarding_role) if roles and st.session_state.onboarding_role in roles else 0, key="onboarding_role_select") if roles else None
        if role:
            st.session_state.onboarding_role = role
            # Call tool to get tasks
            tasks_resp = components["server"].call_tool("onboarding_get_tasks", {"role": role})
            status_resp = components["server"].call_tool("onboarding_get_status", {"role": role})
            if tasks_resp.get("success"):
                tasks = tasks_resp["result"].get("tasks", []) if isinstance(tasks_resp.get("result"), dict) else tasks_resp.get("tasks", [])
                st.caption(f"Progress: {status_resp.get('result', {}).get('percent_complete', 0)}% complete")
                # Prepare checkbox states
                for t in tasks:
                    tid = t.get("id")
                    completed = t.get("completed", False)
                    cb_key = f"onb_task_{role}_{tid}"
                    st.checkbox(f"[{tid}] {t.get('task')}", value=completed, key=cb_key)
                update = st.button("Update Completed Tasks", key="onboarding_update_btn")
                if update:
                    # Iterate tasks; mark newly checked ones
                    changes = 0
                    for t in tasks:
                        tid = t.get("id")
                        cb_key = f"onb_task_{role}_{tid}"
                        desired = st.session_state.get(cb_key, False)
                        if desired and not t.get("completed"):
                            resp = components["server"].call_tool("onboarding_mark_completed", {"role": role, "task_id": tid})
                            if resp.get("success"):
                                changes += 1
                    st.success(f"Updated {changes} task(s)")
                    st.rerun()
            else:
                st.info("No tasks found or role unavailable.")
        else:
            st.info("No onboarding roles available.")

    st.markdown("---")
    st.markdown("HR Assistant Agent powered by MCP (Model Context Protocol)\n\nFor urgent matters, please contact HR directly.")


if __name__ == "__main__":
    main()


