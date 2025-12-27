"""
Application Configuration and Styling
Contains page config, CSS, and UI constants
"""

import streamlit as st

# --- PAGE CONFIGURATION ---
def setup_page():
    """Configure Streamlit page settings."""
    st.set_page_config(
        page_title="SkillCorner AI Analyst", 
        page_icon="⚽", 
        layout="wide",
        initial_sidebar_state="expanded"
    )


# --- CUSTOM CSS ---
def apply_custom_css():
    """Apply custom styling to the application."""
    st.markdown("""
        <style>
        /* Main styling */
        .stChatMessage { 
            border-radius: 10px; 
            padding: 15px; 
            margin: 5px 0;
        }
        .stChatMessage[data-testid="stChatMessageUser"] { 
            background-color: #f0f2f6; 
            border-left: 4px solid #006D00;
        }
        .stChatMessage[data-testid="stChatMessageAssistant"] { 
            background-color: #e8f4ea; 
            border-left: 4px solid #00a86b;
        }
        
        /* Headers */
        h1 { 
            color: #006D00; 
            font-weight: 700;
        }
        h2, h3 { 
            color: #00a86b; 
        }
        
        /* Status widget */
        div[data-testid="stStatusWidget"] { 
            border: 2px solid #006D00; 
            border-radius: 8px;
        }
        
        /* Sidebar */
        .css-1d391kg { 
            background-color: #f8f9fa; 
        }
        
        /* Buttons */
        .stButton>button {
            background-color: #006D00;
            color: white;
            border-radius: 5px;
            border: none;
            padding: 0.5rem 1rem;
            font-weight: 500;
        }
        .stButton>button:hover {
            background-color: #00a86b;
        }
        
        /* Metric cards */
        .metric-card {
            background: linear-gradient(135deg, #006D00 0%, #00a86b 100%);
            padding: 15px;
            border-radius: 10px;
            color: white;
            text-align: center;
            margin: 5px;
        }
        </style>
        """, unsafe_allow_html=True)


# --- EXAMPLE QUERIES ---
EXAMPLE_QUERIES = [
    "Show me the top 10 players by total distance covered",
    "Compare high speed running vs sprint distance",
    "What's the profile of A. Taggart?",
    "Which players have the highest acceleration?",
    "Show me the relationship between sprints and total distance"
]