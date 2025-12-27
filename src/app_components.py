"""
UI Components
Reusable Streamlit components for sidebar, welcome screen, and chat messages
"""

import streamlit as st
from src.app_config import EXAMPLE_QUERIES


# --- SESSION STATE ---
def initialize_session_state():
    """Initialize session state variables."""
    if "messages" not in st.session_state:
        st.session_state["messages"] = []
    
    if "conversation_started" not in st.session_state:
        st.session_state["conversation_started"] = False


# --- SIDEBAR COMPONENTS ---
def render_sidebar(valid_columns):
    """
    Render the complete sidebar.
    
    Args:
        valid_columns: List of available column names
    """
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        # Dataset info
        render_dataset_info(valid_columns)
        
        # Quick actions
        render_quick_actions()
        
        # Session stats
        render_session_stats()


def render_dataset_info(valid_columns):
    """Render dataset information section."""
    with st.expander("📊 Dataset Info", expanded=True):
        st.markdown("""
        **Australian A-League 2024/2025**
        - Position: Midfielders
        - Metrics: Physical performance
        - Players: ~150+
        """)
        
        if valid_columns:
            st.caption(f"**Available Columns:** {len(valid_columns)}")
            with st.expander("View All Columns"):
                for col in valid_columns[:20]:
                    st.text(f"• {col}")
                if len(valid_columns) > 20:
                    st.caption(f"... and {len(valid_columns) - 20} more")


def render_quick_actions():
    """Render quick action buttons."""
    st.header("🎯 Quick Actions")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🔄 Clear Chat", use_container_width=True):
            st.session_state["messages"] = []
            st.session_state["conversation_started"] = False
            st.rerun()
    
    with col2:
        if st.session_state.get("messages"):
            from src.app_utils import export_conversation
            export_text = export_conversation(st.session_state.messages)
            st.download_button(
                "📥 Export",
                export_text,
                "conversation.txt",
                "text/plain",
                use_container_width=True
            )
        else:
            st.button("📥 Export", disabled=True, use_container_width=True)


def render_session_stats():
    """Render session statistics."""
    messages = st.session_state.get("messages", [])
    
    if messages:
        st.header("📈 Session Stats")
        st.metric("Total Messages", len(messages))
        
        user_msgs = sum(1 for m in messages if m.get("role") == "user")
        st.metric("Your Queries", user_msgs)
        
        charts = sum(1 for m in messages if m.get("image"))
        st.metric("Charts Generated", charts)


# --- WELCOME SCREEN ---
def render_welcome_screen():
    """Render welcome screen with examples."""
    st.markdown("---")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("""
        ### 👋 Welcome to the AI Sports Analyst!
        
        I can help you analyze Australian A-League midfielder performance data through intelligent visualizations:
        
        **🎯 What I can do:**
        - 📊 **Bar Charts**: Rank players by any metric
        - 📈 **Scatter Plots**: Compare two metrics and find correlations
        - 🕸️ **Radar Charts**: Profile individual player strengths
        
        **💡 Try these example queries:**
        """)
        
        selected_example = st.selectbox(
            "Select an example or type your own below:",
            [""] + EXAMPLE_QUERIES,
            key="example_selector"
        )
        
        if selected_example:
            st.session_state["prefilled_query"] = selected_example
    
    with col2:
        st.info("""
        **📚 Tips:**
        - Be specific about metrics
        - Name players exactly
        - Ask for comparisons
        - Request rankings
        """)
        
        st.success("""
        **🎨 Chart Types:**
        - **Bar**: Rankings
        - **Scatter**: Comparisons
        - **Radar**: Player profiles
        """)

    st.markdown("---")


# --- CHAT MESSAGE RENDERING ---
def render_chat_message(msg):
    """
    Render a single chat message.
    
    Args:
        msg: Message dictionary with role, content, image, logs
    """
    with st.chat_message(msg["role"]):
        # Display content
        if msg.get("content"):
            st.markdown(msg["content"])
        
        # Display image if available
        if msg.get("image"):
            col1, col2, col3 = st.columns([1, 3, 1])
            with col2:
                st.image(
                    msg["image"], 
                    caption="📊 Generated Visualization", 
                    use_container_width=True
                )
        
        # Display logs in expander
        if msg.get("logs"):
            with st.expander("🔍 View Processing Logs"):
                st.code(msg["logs"], language="text")