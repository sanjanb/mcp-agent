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
    page_title="HR Assistant Agent",
    page_icon="👔",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        padding: 1rem 0;
        border-bottom: 2px solid #f0f0f0;
        margin-bottom: 2rem;
    }
    
    .chat-message {
        padding: 1rem;
        margin: 0.5rem 0;
        border-radius: 8px;
        border-left: 4px solid #007ACC;
        background-color: #f8f9fa;
    }
    
    .user-message {
        background-color: #e3f2fd;
        border-left-color: #2196F3;
    }
    
    .assistant-message {
        background-color: #f1f8e9;
        border-left-color: #4CAF50;
    }
    
    .citation {
        background-color: #fff3e0;
        padding: 0.25rem 0.5rem;
        border-radius: 4px;
        font-size: 0.8rem;
        margin: 0.25rem 0;
    }
    
    .stats-box {
        background-color: #f5f5f5;
        padding: 1rem;
        border-radius: 8px;
        margin: 0.5rem 0;
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
            # Show mode if in fallback
            if metadata.get("mode") == "fallback":
                st.info("🔧 **Fallback Mode**: This response was generated using document search only (OpenAI API unavailable)")
            
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
    
    # Header
    st.markdown("""
    <div class="main-header">
        <h1>HR Assistant Agent</h1>
        <p>Ask me anything about company policies, benefits, and HR procedures!</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Initialize components
    components = initialize_components()
    if not components:
        st.error("System initialization failed. Please check the logs and try again.")
        return
    
    # Sidebar for system status and controls
    with st.sidebar:
        st.header("System Status")
        
        # Health check
        health = components["server"].health_check()
        if health.get("server_status") == "healthy":
            st.success("System is healthy")
        else:
            st.error("System issues detected")
        
        # Database stats
        try:
            stats = components["policy_tool"].get_database_stats()
            if stats and not stats.get("error"):
                st.markdown(f"""
                <div class="stats-box">
                    <h4>📊 Database Statistics</h4>
                    <ul>
                        <li>Total chunks: {stats.get('total_chunks', 0)}</li>
                        <li>Documents: {stats.get('unique_documents', 0)}</li>
                        <li>Collection: {stats.get('collection_name', 'Unknown')}</li>
                    </ul>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.warning("Database statistics unavailable")
        except Exception as e:
            st.warning(f"Could not load database stats: {e}")
        
        # OpenAI API status
        st.markdown("### 🤖 AI Status")
        if components["rag_engine"].client:
            st.success("✅ OpenAI API connected")
        else:
            st.warning("⚠️ OpenAI API not available")
            st.info("💡 **Fallback mode active** - The system will still provide helpful responses using document search, but without AI-generated summaries.")
            with st.expander("How to fix OpenAI connection"):
                st.markdown("""
                1. Get a valid OpenAI API key from https://platform.openai.com/account/api-keys
                2. Set the environment variable:
                   ```
                   # Windows (PowerShell):
                   $env:OPENAI_API_KEY = "your-api-key-here"
                   
                   # Linux/Mac:
                   export OPENAI_API_KEY="your-api-key-here"
                   ```
                3. Restart the Streamlit app
                """)
        
        # Controls
        st.header("Controls")
        if st.button("Clear Conversation"):
            if "user_id" in st.session_state:
                components["conv_manager"].clear_history(st.session_state.user_id)
            st.session_state.messages = []
            st.rerun()
        
        # Settings
        st.header("Settings")
        max_results = st.slider("Max search results", 1, 10, 5)
        show_debug = st.checkbox("Show debug info", False)
    
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