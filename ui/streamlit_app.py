"""
Streamlit UI for HR Assistant Agent.
Provides a simple chat interface for employees to ask HR questions.
"""

import streamlit as st
import sys
import os
from pathlib import Path
import json
from datetime import datetime
import time

# Add the project root to the path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

# Import our modules
try:
    from tools.policy_rag.mcp_tool import PolicySearchTool
    from tools.policy_rag.rag_engine import RAGEngine, ConversationManager
    from mcp_server.server import MCPServer, MCPRouter
except ImportError as e:
    st.error(f"Failed to import required modules: {e}")
    st.error("Please make sure all dependencies are installed and the project structure is correct.")
    st.stop()

# Page configuration
st.set_page_config(
    page_title="HR Assistant",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for minimalist black/white theme (Groq-like)
st.markdown("""
<style>
    :root {
        --bg: #0b0b0b;
        --panel: #121212;
        --text: #f5f5f5;
        --muted: #bdbdbd;
        --border: #1f1f1f;
        --accent: #ffffff;
    }

    html, body, .main, .block-container { background-color: var(--bg) !important; }
    .block-container { max-width: 960px; padding-top: 24px; }

    body, .main, .block-container, .sidebar-content {
        color: var(--text);
        font-family: ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial, "Apple Color Emoji", "Segoe UI Emoji";
    }

    .header {
        text-align: left;
        padding: 8px 0 20px 0;
        margin-bottom: 12px;
    }
    .header h1 { font-size: 24px; font-weight: 600; margin: 0; color: var(--text); }
    .header p { margin: 6px 0 0 0; color: var(--muted); font-size: 14px; }

    .status-row { display: flex; gap: 8px; margin: 8px 0 16px 0; }
    .badge {
        border: 1px solid var(--border);
        color: var(--muted);
        padding: 6px 10px;
        border-radius: 999px;
        font-size: 12px;
        background: var(--panel);
    }

    .chat-container {
        height: 58vh;
        overflow-y: auto;
        padding: 12px;
        border: 1px solid var(--border);
        border-radius: 12px;
        background-color: var(--panel);
        margin-bottom: 12px;
    }

    .user-message, .assistant-message {
        padding: 12px 14px;
        margin: 10px 0;
        border-radius: 10px;
        border: 1px solid var(--border);
        background: transparent;
    }
    .user-message strong, .assistant-message strong { color: var(--muted); font-weight: 500; }

    .input-section {
        position: sticky;
        bottom: 0;
        background: var(--panel);
        padding: 12px;
        border-radius: 12px;
        border: 1px solid var(--border);
        box-shadow: 0 -8px 16px rgba(0,0,0,0.25);
    }

    .typing-indicator { color: var(--muted); font-size: 12px; padding: 6px 0; }
    .pulse { display: inline-block; width: 6px; height: 6px; border-radius: 50%; background: var(--text); animation: pulse 1s infinite; margin-left: 6px; }
    @keyframes pulse { 0% { opacity: 0.2 } 50% { opacity: 1 } 100% { opacity: 0.2 } }

    .stTextArea > div > div > textarea {
        background: transparent !important;
        color: var(--text) !important;
        border-radius: 10px !important;
        border: 1px solid var(--border) !important;
    }

    .stButton > button {
        background: var(--accent) !important;
        color: #000 !important;
        border: 1px solid var(--border) !important;
        border-radius: 8px !important;
        padding: 10px 16px !important;
        font-weight: 600 !important;
        width: 100% !important;
        margin-top: 10px !important;
    }

    /* Ensure readable text on white/light backgrounds */
    .stAlert {
        background: #ffffff !important;
        color: #000 !important;
        border: 1px solid var(--border) !important;
    }
    .stAlert * { color: #000 !important; }

    .streamlit-expanderHeader, .streamlit-expanderHeader * {
        color: #000 !important;
    }
    .streamlit-expanderHeader {
        background: #ffffff !important;
        border: 1px solid var(--border) !important;
        border-radius: 8px !important;
    }

    .source-item {
        background: transparent;
        border: 1px dashed var(--border);
        border-radius: 8px;
        padding: 10px;
        color: var(--muted);
    }

    .footer { color: var(--muted); font-size: 12px; text-align: center; padding: 12px 0; }
    
    /* Mobile tweaks */
    @media (max-width: 768px) {
        .chat-container { height: 50vh; }
        .stButton > button { padding: 12px 14px !important; }
    }
</style>
""", unsafe_allow_html=True)


@st.cache_resource
def initialize_components():
    """Initialize all system components with caching."""
    try:
        # Initialize MCP components
        server = MCPServer()
        router = MCPRouter(server)
        
        # Initialize RAG components
        rag_engine = RAGEngine()
        policy_tool = PolicySearchTool()
        conv_manager = ConversationManager()
        
        return {
            "server": server,
            "router": router,
            "rag_engine": rag_engine,
            "policy_tool": policy_tool,
            "conv_manager": conv_manager
        }
    except Exception as e:
        st.error(f"Failed to initialize components: {e}")
        return None


def display_message(role, content, metadata=None):
    """Display a chat message with clean styling (no images/emojis)."""
    css_class = "user-message" if role == "user" else "assistant-message"
    
    st.markdown(f"""
    <div class="{css_class}">
        {content.replace('\n', '<br>')}
    </div>
    """, unsafe_allow_html=True)
    
    # Show sources for assistant responses (simplified)
    if role == "assistant" and metadata:
        # AI provider indicator
        if metadata.get("provider"):
            provider_name = metadata.get("provider", "unknown").title()
            st.caption(f"✨ AI response from {provider_name}")
        elif metadata.get("mode") == "fallback":
            st.caption("💡 Response based on document search")
        
        # Show sources if available
        if metadata.get("chunks_details"):
            with st.expander(f"📚 Sources ({len(metadata['chunks_details'])})"):
                for i, chunk in enumerate(metadata["chunks_details"], 1):
                    filename = chunk.get('filename', 'Unknown')
                    page = chunk.get('page', '?')
                    score = chunk.get('score', 0)
                    text_preview = chunk.get('text', '')[:150] + "..."
                    
                    st.markdown(f"""
                    <div class="source-item">
                        <strong>Source {i}:</strong> {filename} (Page {page})<br>
                        <small>Relevance: {score:.1%}</small><br>
                        <em>{text_preview}</em>
                    </div>
                    """, unsafe_allow_html=True)


def main():
    """Main application function."""
    
    # Initialize components first
    components = initialize_components()
    if not components:
        st.error("System initialization failed. Please check the logs and try again.")
        return
    
    # Header section
    st.markdown("""
    <div class="header">
        <h1>HR Assistant</h1>
        <p>Minimalist chat for company policies and HR help</p>
    </div>
    """, unsafe_allow_html=True)

    # Minimal status badges
    stats = None
    try:
        stats = components["policy_tool"].get_database_stats()
    except Exception:
        pass
    rag_engine = components["rag_engine"]
    active_provider = getattr(rag_engine, 'active_provider', None)

    st.markdown("""
    <div class="status-row" role="status" aria-label="System status">
        <span class="badge">Docs: %s</span>
        <span class="badge">Provider: %s</span>
        <span class="badge">Mode: %s</span>
    </div>
    """ % (
        (stats.get('unique_documents', 0) if stats else 0),
        (active_provider.title() if active_provider else "Auto"),
        ("AI" if active_provider else "Basic")
    ), unsafe_allow_html=True)
    
    # Simplified sidebar
    with st.sidebar:
        st.header("System Info")
        
        # Health check
        health = components["server"].health_check()
        if health.get("server_status") == "healthy":
            st.success("✅ System Healthy")
        else:
            st.error("❌ System Issues")
        
        # Quick stats
        try:
            stats = components["policy_tool"].get_database_stats()
            if stats and not stats.get("error"):
                total_chunks = stats.get('total_chunks', 0)
                unique_docs = stats.get('unique_documents', 0)
                st.info(f"📚 {unique_docs} documents loaded\n📄 {total_chunks} searchable sections")
            else:
                st.warning("No documents loaded")
        except Exception:
            st.warning("Database unavailable")
        
        # AI Status
        rag_engine = components["rag_engine"]
        active_provider = getattr(rag_engine, 'active_provider', None)
        
        if active_provider:
            provider_name = active_provider.title()
            st.success(f"🤖 AI: {provider_name}")
        else:
            st.info("💡 Basic search mode")
            with st.expander("Need AI responses?"):
                st.markdown("""
                Add API keys to enable AI responses:
                - OpenAI: Set `OPENAI_API_KEY`
                - Gemini: Set `GEMINI_API_KEY`
                
                Restart app after adding keys.
                """)
        
        # Simple controls
        st.markdown("---")
        if st.button("🗑️ Clear Chat"):
            if "user_id" in st.session_state:
                components["conv_manager"].clear_history(st.session_state.user_id)
            st.session_state.messages = []
            st.rerun()
        
        # Settings
        with st.expander("⚙️ Settings"):
            max_results = st.slider("Search results", 1, 10, 5)
            show_debug = st.checkbox("Debug mode", False)
    
    # Initialize session state
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    if "user_id" not in st.session_state:
        st.session_state.user_id = f"user_{int(time.time())}"
    
    # Chat conversation display
    st.markdown('<div class="chat-container" id="chat">', unsafe_allow_html=True)
    
    if st.session_state.messages:
        for message in st.session_state.messages:
            display_message(
                message["role"], 
                message["content"], 
                message.get("metadata")
            )
    else:
        st.markdown("""
        <div style="text-align: center; padding: 40px; color: #666;">
            <h3>Welcome to HR Assistant</h3>
            <p>Ask me about company policies, benefits, vacation time, or any HR-related question.</p>
            <p><strong>Try asking:</strong><br>
            - "How many vacation days do I get?"<br>
            - "What's the remote work policy?"<br>
            - "How do I submit a time off request?"</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Input section (sticky bottom)
    st.markdown('<div class="input-section" role="form" aria-label="Ask a question">', unsafe_allow_html=True)
    user_input = st.text_area(
        "Ask your question:",
        placeholder="Type your HR question here...",
        height=80,
        key="user_input",
        label_visibility="collapsed",
        help="Press Enter to send, Shift+Enter for newline. Commands: /clear, /help, /provider openai|gemini|auto"
    )
    send = st.button("Send", type="primary", use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # Keyboard-first UX: interpret commands
    def handle_command(text: str):
        t = text.strip()
        if t.lower() == "/clear":
            if "user_id" in st.session_state:
                components["conv_manager"].clear_history(st.session_state.user_id)
            st.session_state.messages = []
            st.rerun()
        if t.lower() == "/help":
            st.session_state.messages.append({
                "role": "assistant",
                "content": "Commands: /clear, /help, /provider openai|gemini|auto"
            })
            st.rerun()
        if t.lower().startswith("/provider"):
            parts = t.split()
            if len(parts) >= 2:
                choice = parts[1].lower()
                if choice in ["openai", "gemini", "auto"]:
                    try:
                        components["rag_engine"].set_provider(choice)
                        st.session_state.messages.append({
                            "role": "assistant",
                            "content": f"Provider set to {choice.title()}"
                        })
                        st.rerun()
                    except Exception as e:
                        st.session_state.messages.append({
                            "role": "assistant",
                            "content": f"Unable to set provider: {e}"
                        })
                        st.rerun()

    if send and user_input.strip():
        # Commands first
        if user_input.strip().startswith("/"):
            handle_command(user_input)
        else:
            # Process the question
            with st.spinner("🤔 Thinking..."):
                try:
                    # Add user message
                    st.session_state.messages.append({
                        "role": "user", 
                        "content": user_input
                    })
                    components["conv_manager"].add_turn(
                        st.session_state.user_id, "user", user_input
                    )
                    
                    # Search and generate response
                    search_result = components["policy_tool"].search_policies(
                        user_input, top_k=max_results
                    )
                    
                    conversation_history = components["conv_manager"].get_history(
                        st.session_state.user_id
                    )[:-1]
                    
                    # Streaming responses: simulate token-by-token
                    rag_response = components["rag_engine"].generate_response(
                        user_input,
                        search_result.get("chunks", []),
                        conversation_history
                    )
                    placeholder = st.empty()
                    accumulated = ""
                    if rag_response.get("success"):
                        full_text = rag_response.get("response", "")
                        words = full_text.split()
                        for w in words:
                            accumulated += (w + " ")
                            placeholder.markdown(f"<div class='assistant-message'>{accumulated}</div>", unsafe_allow_html=True)
                            time.sleep(0.02)
                        # finalize message
                        placeholder.empty()
                        st.session_state.messages.append({
                            "role": "assistant",
                            "content": full_text,
                            "metadata": rag_response
                        })
                        components["conv_manager"].add_turn(
                            st.session_state.user_id, "assistant", full_text
                        )
                    else:
                        st.session_state.messages.append({
                            "role": "assistant",
                            "content": f"Using fallback. Error: {rag_response.get('error', 'Unknown error')}"
                        })
                    
                    # Refresh to show new messages
                    st.rerun()
                    
                except Exception as e:
                    st.warning(f"Something went wrong, retry available. {e}")
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": "I apologize, but I encountered a technical error. Please try again."
                    })
                    st.rerun()
    elif send and not user_input.strip():
        st.warning("Please enter a question first.")
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Simple footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #888; font-size: 0.85rem; padding: 20px;">
        💼 HR Assistant • Powered by AI • For urgent matters, contact HR directly
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()