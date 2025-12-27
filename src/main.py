from typing import List, Literal, Optional
from langchain_ollama import ChatOllama
import pandas as pd
from pydantic import BaseModel, Field
from langgraph.graph import StateGraph, START, END, MessagesState
from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage, AIMessage

# Import your tools
from src.tools.visualisation_tools import (
    create_dynamic_bar_chart, 
    create_dynamic_scatter_plot, 
    create_dynamic_radar_chart
)

# --- 1. CONFIGURATION & KNOWLEDGE BASE ---
DATA_URL = "https://raw.githubusercontent.com/SkillCorner/opendata/master/data/aggregates/aus1league_physicalaggregates_20242025_midfielders.csv"

def load_metric_definitions(filepath: str = "src/prompts/data_description.md") -> str:
    """Loads metric definitions."""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return "No metric definitions available."

METRIC_DEFINITIONS = load_metric_definitions()

def get_valid_columns():
    try: 
        return pd.read_csv(DATA_URL, nrows=0).columns.tolist()
    except: 
        return []

VALID_COLUMNS = get_valid_columns()

class AnalysisResponse(BaseModel):
    """Final output schema."""
    executive_summary: str = Field(..., description="High-level summary of findings.")
    detailed_analysis: str = Field(..., description="Detailed data breakdown with specific numbers.")
    key_trends: List[str] = Field(..., description="List of 3-5 key patterns or insights.")

# --- REGISTER TOOLS ---
tools = [create_dynamic_bar_chart, create_dynamic_scatter_plot, create_dynamic_radar_chart]
tools_by_name = {t.name: t for t in tools}

# MODELS - Using larger models for better reasoning
router_llm = ChatOllama(model="llama3.1:latest", temperature=0).bind_tools(tools)
analyst_llm = ChatOllama(model="llama3.1:latest", temperature=0)

# --- NODES ---

def agent_node(state: MessagesState):
    """
    Router Node: Analyzes query and selects appropriate visualization tool.
    """
    system_prompt = f"""You are a Data Visualization Router for sports analytics data.

AVAILABLE COLUMNS: {", ".join(VALID_COLUMNS[:20])}...

YOUR TASK: Analyze the user's query and select the MOST APPROPRIATE visualization tool.

TOOL SELECTION GUIDE:
1. **create_dynamic_radar_chart** - Use when user asks about:
   - A SPECIFIC PLAYER's profile, style, strengths, or overall performance
   - Examples: "Show me Messi's profile", "What are Ronaldo's strengths"
   
2. **create_dynamic_bar_chart** - Use when user asks for:
   - Rankings, top players, best/worst performers
   - Examples: "Top 10 fastest players", "Who has the most distance covered"
   
3. **create_dynamic_scatter_plot** - Use when user asks to:
   - Compare TWO metrics, find correlations, or see relationships
   - Examples: "Compare speed vs distance", "Show relationship between sprints and goals"

CRITICAL RULES:
- You MUST call exactly ONE tool
- Pass arguments as a simple dictionary: {{"query": "user's question", "title": "descriptive title"}}
- The "query" should be the user's original question or a clear restatement
- The "title" should be a professional chart title

Example of CORRECT tool call:
Tool: create_dynamic_radar_chart
Arguments: {{"query": "Show me the profile for Lionel Messi", "title": "Physical Profile: Lionel Messi"}}
"""
    
    messages = [SystemMessage(content=system_prompt)] + state["messages"]
    
    try:
        response = router_llm.invoke(messages)
        
        # Validate that tool was called
        if not hasattr(response, "tool_calls") or not response.tool_calls:
            # Fallback: create a default tool call
            print("Warning: LLM didn't call a tool. Creating default bar chart call.")
            response.tool_calls = [{
                "name": "create_dynamic_bar_chart",
                "args": {
                    "query": state["messages"][-1].content,
                    "title": "Player Analysis"
                },
                "id": "fallback_001"
            }]
        
        return {"messages": [response]}
    
    except Exception as e:
        print(f"Agent Node Error: {e}")
        # Create error message
        error_msg = AIMessage(content=f"Router failed to select tool: {e}")
        return {"messages": [error_msg]}


def tool_node(state: MessagesState):
    """Executes the selected visualization tool."""
    last_message = state["messages"][-1]
    results = []
    
    # Check if last message has tool calls
    if not hasattr(last_message, "tool_calls") or not last_message.tool_calls:
        error_msg = ToolMessage(
            content="System Error: No tool was selected. Unable to generate visualization.",
            tool_call_id="error_001"
        )
        return {"messages": [error_msg]}

    for tool_call in last_message.tool_calls:
        tool_name = tool_call["name"]
        args = tool_call["args"]
        tool_call_id = tool_call.get("id", "unknown")
        
        print(f"\n---Executing Tool: {tool_name} ---")
        print(f"Arguments: {args}")
        
        tool = tools_by_name.get(tool_name)
        
        if not tool:
            output = f"Error: Tool '{tool_name}' not found. Available tools: {list(tools_by_name.keys())}"
            results.append(ToolMessage(content=output, tool_call_id=tool_call_id))
            continue
        
        try:
            # Validate arguments
            if not isinstance(args, dict):
                raise ValueError(f"Invalid arguments type: {type(args)}. Expected dict.")
            
            if "query" not in args or "title" not in args:
                raise ValueError(f"Missing required arguments. Got: {args.keys()}. Need: 'query' and 'title'")
            
            # Execute tool
            output = tool.invoke(args)
            print(f"✅ Tool executed successfully")
            
        except Exception as e:
            output = f"Tool Execution Error ({tool_name}): {str(e)}"
            print(f"{output}")
        
        results.append(ToolMessage(content=str(output), tool_call_id=tool_call_id))
    
    return {"messages": results}


def analysis_node(state: MessagesState):
    """
    Analyst Node: Interprets visualization results and provides insights.
    """
    print("\n--- Analyzing Results ---")
    tool_messages = [msg for msg in state["messages"] if isinstance(msg, ToolMessage)]
    
    if not tool_messages:
        return {"messages": [AIMessage(content="No visualization data available for analysis.")]}
    
    latest_tool_output = tool_messages[-1].content
    
    system_prompt = f"""You are a Lead Sports Performance Analyst specializing in physical performance metrics.

METRIC CONTEXT:
{METRIC_DEFINITIONS}

YOUR TASK:
Analyze the visualization results and provide professional insights.

GUIDELINES:
1. If the tool output contains "Error", explain what went wrong and suggest alternatives
2. If successful, interpret the data in the context of sports performance
3. Highlight standout performers or interesting patterns
4. Use specific numbers and player names from the data
5. Keep language professional but accessible

TOOL OUTPUT:
{latest_tool_output}

Provide your analysis in the structured format requested."""

    try:
        structured_llm = analyst_llm.with_structured_output(AnalysisResponse)
        
        analysis_messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content="Analyze the visualization results and provide insights.")
        ]
        
        final_output = structured_llm.invoke(analysis_messages)
        
        # Format the response nicely
        formatted_response = f"""
**EXECUTIVE SUMMARY**
{final_output.executive_summary}

**DETAILED ANALYSIS**
{final_output.detailed_analysis}

**KEY TRENDS**
{chr(10).join(f'• {trend}' for trend in final_output.key_trends)}
"""
        
        return {"messages": [AIMessage(content=formatted_response)]}
    
    except Exception as e:
        print(f"❌ Analysis Error: {e}")
        return {"messages": [AIMessage(content=f"Analysis failed: {e}\n\nRaw tool output:\n{latest_tool_output}")]}



workflow = StateGraph(MessagesState)
workflow.add_node("agent", agent_node)
workflow.add_node("tool_node", tool_node)
workflow.add_node("analysis_node", analysis_node)
workflow.add_edge(START, "agent")
workflow.add_edge("agent", "tool_node")
workflow.add_edge("tool_node", "analysis_node")
workflow.add_edge("analysis_node", END)
app = workflow.compile()


