"""
Application Utility Functions
Helper functions for parsing, finding images, and capturing logs
"""

import os
import re
import ast
from io import StringIO
from langchain_core.messages import ToolMessage


# --- LOG CAPTURE CLASS ---
class StreamlitCapturer:
    """Captures stdout and displays in Streamlit status container."""
    
    def __init__(self, container):
        self.container = container
        self.buffer = StringIO()
        self.log_lines = []

    def write(self, text):
        self.buffer.write(text)
        if text.strip():
            clean_text = text.replace("---", "").strip()
            if clean_text and clean_text not in self.log_lines:
                self.log_lines.append(clean_text)
                # Show only important logs in real-time
                if any(keyword in clean_text.lower() for keyword in 
                       ["executing", "sql", "error", "success", "created"]):
                    self.container.write(f"⚙️ {clean_text}")

    def flush(self):
        pass
        
    def get_value(self):
        return "\n".join(self.log_lines)


# --- RESPONSE PARSING ---
def parse_analysis_response(content: str) -> dict:
    """
    Parse the structured analysis response.
    
    Args:
        content: String content from analyst LLM
        
    Returns:
        Dictionary with formatted sections
    """
    try:
        if isinstance(content, str) and "executive_summary" in content:
            data = ast.literal_eval(content)
            
            # Format trends list
            trends = data.get('key_trends', [])
            if isinstance(trends, list):
                trends_text = "\n".join([f"• {t}" for t in trends])
            else:
                trends_text = str(trends)
            
            return {
                "summary": data.get('executive_summary', 'N/A'),
                "analysis": data.get('detailed_analysis', 'N/A'),
                "trends": trends_text,
                "formatted": f"""
### 📋 Executive Summary
{data.get('executive_summary', 'N/A')}

### 🔍 Detailed Analysis
{data.get('detailed_analysis', 'N/A')}

### 📊 Key Trends
{trends_text}
"""
            }
    except Exception as e:
        pass
    
    # Fallback: return content as-is
    return {
        "summary": "Analysis completed",
        "analysis": content,
        "trends": "",
        "formatted": content
    }


# --- IMAGE FINDING ---
def find_generated_image(messages: list) -> str:
    """
    Search through messages to find generated PNG file.
    
    Args:
        messages: List of message objects from LangGraph
        
    Returns:
        Filename of PNG or None
    """
    for msg in reversed(messages):
        if isinstance(msg, ToolMessage):
            content = str(msg.content)
            
            # Try multiple regex patterns
            patterns = [
                r"'([^']+\.png)'",  # Single quotes
                r'"([^"]+\.png)"',  # Double quotes
                r'`([^`]+\.png)`',  # Backticks
                r'([\w\-\.]+\.png)'  # Simple filename
            ]
            
            for pattern in patterns:
                match = re.search(pattern, content)
                if match:
                    filename = match.group(1)
                    if os.path.exists(filename):
                        return filename
    
    return None


# --- CONVERSATION EXPORT ---
def export_conversation(messages: list) -> str:
    """
    Export conversation as formatted text.
    
    Args:
        messages: List of message dictionaries
        
    Returns:
        Formatted text string
    """
    lines = []
    for msg in messages:
        role = msg.get('role', 'unknown').upper()
        content = msg.get('content', '')
        lines.append(f"{role}: {content}")
        lines.append("")
    
    return "\n".join(lines)