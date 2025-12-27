

import streamlit as st
import sys
import traceback
from langchain_core.messages import HumanMessage

# Import configuration and styling
from src.app_config import setup_page, apply_custom_css

# Import utility functions
from src.app_utils import (
    StreamlitCapturer,
    parse_analysis_response,
    find_generated_image
)

# Import UI components
from src.app_components import (
    initialize_session_state,
    render_sidebar,
    render_welcome_screen,
    render_chat_message
)

# Import LangGraph workflow
from src.main import app as graph_app, VALID_COLUMNS

# --- SETUP ---
setup_page()
apply_custom_css()
initialize_session_state()

# --- SIDEBAR ---
render_sidebar(VALID_COLUMNS)

# --- MAIN CONTENT ---
st.title("⚽ SkillCorner AI Data Analyst")

# Show welcome screen if conversation hasn't started
if not st.session_state.conversation_started:
    render_welcome_screen()

# --- RENDER CHAT HISTORY ---
for msg in st.session_state.messages:
    render_chat_message(msg)

# --- QUERY PROCESSING FUNCTION ---
def process_user_query(prompt):
    """
    Process user query through the LangGraph workflow.
    
    Args:
        prompt: User's question/query
    """
    # Mark conversation as started
    st.session_state.conversation_started = True
    
    # Add user message to history
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # Display user message
    with st.chat_message("user"):
        st.markdown(prompt)

    # Process with assistant
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        
        # Show processing status
        with st.status("🔄 Analyzing your query...", expanded=True) as status_container:
            # Capture logs
            capturer = StreamlitCapturer(status_container)
            original_stdout = sys.stdout
            
            final_state = None
            error_occurred = False
            
            try:
                # Redirect stdout to capture print statements
                sys.stdout = capturer
                
                # Run LangGraph workflow
                inputs = {"messages": [HumanMessage(content=prompt)]}
                final_state = graph_app.invoke(inputs, config={"recursion_limit": 20})
                
                status_container.update(
                    label="✅ Analysis Complete!", 
                    state="complete", 
                    expanded=False
                )
                
            except Exception as e:
                error_occurred = True
                status_container.update(
                    label="❌ Error Occurred", 
                    state="error", 
                    expanded=True
                )
                st.error(f"**Workflow Error:** {str(e)}")
                
                # Show traceback in expander
                with st.expander("🐛 Debug Info"):
                    st.code(traceback.format_exc())
                
            finally:
                # Restore stdout
                sys.stdout = original_stdout

        # Process successful results
        if final_state and not error_occurred:
            try:
                history = final_state["messages"]
                last_message = history[-1]
                
                # Find generated image
                generated_image = find_generated_image(history)
                
                # Parse response
                parsed = parse_analysis_response(last_message.content)
                
                # Display formatted response
                message_placeholder.markdown(parsed["formatted"])
                
                # Prepare response payload
                response_payload = {
                    "role": "assistant", 
                    "content": parsed["formatted"],
                    "logs": capturer.get_value()
                }
                
                # Display image if found
                if generated_image:
                    col1, col2, col3 = st.columns([1, 3, 1])
                    with col2:
                        st.image(
                            generated_image, 
                            caption="📊 Generated Visualization", 
                            use_container_width=True
                        )
                    response_payload["image"] = generated_image
                    
                    # Add download button
                    with open(generated_image, "rb") as file:
                        st.download_button(
                            label="📥 Download Chart",
                            data=file,
                            file_name=generated_image,
                            mime="image/png"
                        )
                
                # Save to session state
                st.session_state.messages.append(response_payload)
                
            except Exception as e:
                st.error(f"**Display Error:** {str(e)}")
                message_placeholder.markdown(
                    "⚠️ Response received but could not be formatted properly."
                )
                
        elif error_occurred:
            # Add error message to history
            st.session_state.messages.append({
                "role": "assistant",
                "content": "❌ I encountered an error processing your request. Please try rephrasing your query or check the logs above.",
                "logs": capturer.get_value()
            })


# --- CHAT INPUT HANDLING ---
# Check for prefilled query from example selector
prefilled = st.session_state.get("prefilled_query", "")
if prefilled:
    prompt = prefilled
    st.session_state["prefilled_query"] = ""  # Clear it
    process_query = True
else:
    prompt = st.chat_input("💬 Ask me anything about player performance...")
    process_query = bool(prompt)

# Process the query
if process_query and prompt:
    process_user_query(prompt)
    st.rerun()