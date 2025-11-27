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
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-container {
        max-width: 800px;
        margin: 0 auto;
        padding: 20px;
    }
    
    .header {
        text-align: center;
        padding: 20px 0;
        margin-bottom: 30px;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 10px;
    }
    
    .chat-container {
        max-height: 400px;
        overflow-y: auto;
        padding: 20px;
        border: 1px solid #e0e0e0;
        border-radius: 10px;
        background-color: #fafafa;
        margin-bottom: 20px;
    }
    
    .user-message {
        background-color: #e3f2fd;
        padding: 15px;
        margin: 10px 0;
        border-radius: 15px 15px 5px 15px;
        border-left: 4px solid #2196f3;
    }
    
    .assistant-message {
        background-color: #f1f8e9;
        padding: 15px;
        margin: 10px 0;
        border-radius: 15px 15px 15px 5px;
        border-left: 4px solid #4caf50;
    }
    
    .status-indicator {
        display: inline-block;
        padding: 5px 10px;
        border-radius: 15px;
        font-size: 12px;
        margin: 5px 0;
    }
    
    .status-success { background-color: #d4edda; color: #155724; }
    .status-warning { background-color: #fff3cd; color: #856404; }
    .status-info { background-color: #d1ecf1; color: #0c5460; }
    
    .input-section {
        background-color: white;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
    }
    
    .stTextArea > div > div > textarea {
        border-radius: 10px;
        border: 2px solid #e0e0e0;
    }
    
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 10px;
        padding: 12px 30px;
        font-weight: bold;
        width: 100%;
        margin-top: 10px;
    }
    
    .sources-section {
        background-color: #f8f9fa;
        padding: 15px;
        border-radius: 8px;
        margin-top: 10px;
        border: 1px solid #e9ecef;
    }
    
    .source-item {
        background-color: white;
        padding: 10px;
        margin: 5px 0;
        border-radius: 5px;
        border-left: 3px solid #6c757d;
        font-size: 0.9em;
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
    """Display a chat message with proper styling."""
    css_class = "user-message" if role == "user" else "assistant-message"
    
    with st.container():
        st.markdown(f"""
        <div class="chat-message {css_class}">
            <strong>{"You" if role == "user" else "HR Assistant"}:</strong><br>
            {content.replace('\n', '<br>')}
        </div>
        """, unsafe_allow_html=True)
        
        # Display metadata for assistant responses
        if role == "assistant" and metadata:
            # Show mode information
            if metadata.get("mode") == "fallback":
                st.info("🔧 **Fallback Mode**: This response was generated using document search only (No AI providers available)")
            elif metadata.get("provider"):
                provider_name = metadata.get("provider", "unknown")
                model_name = metadata.get("model", "unknown")
                if provider_name in ["openai", "gemini"]:
                    st.success(f"✨ **AI Response**: Generated using {provider_name.title()} ({model_name})")
            
            if metadata.get("chunks_details"):
                with st.expander("📚 Sources and Citations"):
                    for i, chunk in enumerate(metadata["chunks_details"], 1):
                        st.markdown(f"""
                        <div class="citation">
                            <strong>Source {i}:</strong> {chunk.get('filename', 'Unknown')} 
                            (Page {chunk.get('page', 'Unknown')}, Score: {chunk.get('score', 0):.2f})<br>
                            <em>{chunk.get('text', '')[:200]}...</em>
                        </div>
                        """, unsafe_allow_html=True)
            
            # Show token usage or fallback note
            if metadata.get("tokens_used"):
                st.caption(f"Response generated using {metadata['tokens_used']} tokens")
            elif metadata.get("mode") == "fallback":
                st.caption("Response generated using document search (no tokens used)")


def main():
    """Main application function."""
    
    # Header section
    st.markdown("""
    <div class="header">
        <h1>HR Assistant</h1>
        <p>Get instant answers about company policies and procedures</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Simple status indicators
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown('<span class="status-indicator status-success">✓ Ready</span>', unsafe_allow_html=True)
    with col2:
        try:
            stats = components["policy_tool"].get_database_stats()
            if stats and not stats.get("error"):
                doc_count = stats.get('unique_documents', 0)
                st.markdown(f'<span class="status-indicator status-info">{doc_count} Documents</span>', unsafe_allow_html=True)
            else:
                st.markdown('<span class="status-indicator status-warning">No Data</span>', unsafe_allow_html=True)
        except:
            st.markdown('<span class="status-indicator status-warning">Loading...</span>', unsafe_allow_html=True)
    with col3:
        # Check AI provider
        rag_engine = components["rag_engine"]
        active_provider = getattr(rag_engine, 'active_provider', None)
        if active_provider:
            st.markdown('<span class="status-indicator status-success">🤖 AI Ready</span>', unsafe_allow_html=True)
        else:
            st.markdown('<span class="status-indicator status-info">💡 Basic Mode</span>', unsafe_allow_html=True)
    
    # Initialize components
    components = initialize_components()
    if not components:
        st.error("System initialization failed. Please check the logs and try again.")
        return
    
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
    
    # Display conversation history
    if st.session_state.messages:
        st.subheader("Conversation")
        for message in st.session_state.messages:
            display_message(
                message["role"], 
                message["content"], 
                message.get("metadata")
            )
    else:
        st.info("Welcome! Ask me any HR-related question to get started.")
    
    # Chat input
    st.subheader("Ask a Question")
    user_input = st.text_area(
        "Your question:",
        placeholder="e.g., How many vacation days do I get? What's the remote work policy?",
        height=100,
        key="user_input"
    )
    
    col1, col2 = st.columns([1, 4])
    with col1:
        ask_button = st.button("Ask Question", type="primary")
    
    # Process user input
    if ask_button and user_input.strip():
        with st.spinner("Thinking..."):
            try:
                # Add user message to conversation
                st.session_state.messages.append({
                    "role": "user", 
                    "content": user_input
                })
                components["conv_manager"].add_turn(
                    st.session_state.user_id, "user", user_input
                )
                
                # Search for relevant policy chunks
                search_result = components["policy_tool"].search_policies(
                    user_input, top_k=max_results
                )
                
                if show_debug:
                    st.expander("Debug: Search Results").json(search_result)
                
                # Generate response using RAG
                conversation_history = components["conv_manager"].get_history(
                    st.session_state.user_id
                )[:-1]  # Exclude the current question
                
                rag_response = components["rag_engine"].generate_response(
                    user_input,
                    search_result.get("chunks", []),
                    conversation_history
                )
                
                if show_debug:
                    st.expander("Debug: RAG Response").json(rag_response)
                
                # Display and store response
                if rag_response["success"]:
                    response_text = rag_response["response"]
                    
                    # Add assistant response to conversation
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": response_text,
                        "metadata": rag_response
                    })
                    components["conv_manager"].add_turn(
                        st.session_state.user_id, "assistant", response_text
                    )
                    
                else:
                    error_message = f"I apologize, but I encountered an error: {rag_response.get('error', 'Unknown error')}"
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": error_message
                    })
                
                # Clear input and rerun to show new messages
                st.session_state.user_input = ""
                st.rerun()
                
            except Exception as e:
                st.error(f"An error occurred: {e}")
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": "I apologize, but I encountered a technical error. Please try again or contact HR directly."
                })
                st.rerun()
    
    elif ask_button and not user_input.strip():
        st.warning("Please enter a question before clicking 'Ask Question'.")
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #666; font-size: 0.8rem;">
        HR Assistant Agent powered by MCP (Model Context Protocol)<br>
        For urgent matters, please contact HR directly.
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()