from typing import List, Optional, Tuple, Any
import numpy as np
import pandas as pd
import duckdb
import matplotlib.pyplot as plt
from mplsoccer import Radar
from langchain_ollama import ChatOllama
from langchain_core.tools import tool
from pydantic import BaseModel, Field


try:
    from skillcornerviz.standard_plots import scatter_plot as scpl
    from skillcornerviz.standard_plots import bar_plot as bar
    import skillcornerviz.utils as put
    SKILLCORNER_AVAILABLE = True
except ImportError:
    print("⚠️ Warning: SkillCornerViz libraries not found. Using fallback matplotlib.")
    SKILLCORNER_AVAILABLE = False


DATA_URL = "https://raw.githubusercontent.com/SkillCorner/opendata/master/data/aggregates/aus1league_physicalaggregates_20242025_midfielders.csv"


llm_reasoner = ChatOllama(model="llama3.1:latest", temperature=0)


_cached_df = None

def load_data() -> pd.DataFrame:
    """Load data with caching to avoid repeated downloads."""
    global _cached_df
    if _cached_df is None:
        _cached_df = pd.read_csv(DATA_URL)
    return _cached_df.copy()

def get_columns_string(df: pd.DataFrame) -> str:
    """Returns column names as comma-separated string."""
    return ", ".join(df.columns.tolist())

def get_columns_with_types(df: pd.DataFrame) -> str:
    """
    Returns columns WITH their data types.
    Essential for distinguishing numeric vs text columns.
    """
    return ", ".join([f"{col} ({str(dtype)})" for col, dtype in df.dtypes.items()])



class BarChartConfig(BaseModel):
    """Configuration for Bar Chart."""
    reasoning: str = Field(..., description="Explain why you chose these columns.")
    name_column: str = Field("player_short_name", description="Column for player names (Y-Axis).")
    metric_column: str = Field(..., description="Numeric metric column to rank by (X-Axis).")
    sort_order: str = Field("DESC", description="'DESC' for highest first, 'ASC' for lowest first.")
    limit: int = Field(15, description="Number of players to show.")

class ScatterPlotConfig(BaseModel):
    """Configuration for Scatter Plot."""
    reasoning: str = Field(..., description="Explain metric choices and relationship being explored.")
    name_column: str = Field("player_short_name", description="Column for labeling data points.")
    group_column: str = Field("team_name", description="Column for grouping/coloring dots.")
    x_metric_column: str = Field(..., description="Numeric column for X-axis.")
    y_metric_column: str = Field(..., description="Numeric column for Y-axis.")
    highlight_entity: Optional[str] = Field(None, description="Specific team/group to highlight.")
    top_n_metric: str = Field(..., description="Which metric (x_metric or y_metric) to use for Top 5 labels.")

class RadarChartConfig(BaseModel):
    """Configuration for Radar Chart."""
    reasoning: str = Field(..., description="Justify metric selection for player profiling.")
    name_column: str = Field("player_short_name", description="Player name column.")
    metric_columns: List[str] = Field(..., description="List of 5-8 NUMERIC columns (int64 or float64 only).")
    target_player: str = Field(..., description="Name or partial name of the player to profile.")


def _generate_sql_from_config(config: Any, chart_type: str) -> str:
    """Build SQL query from Pydantic config."""
    if chart_type == "bar":
        return f"""
            SELECT {config.name_column}, {config.metric_column} 
            FROM my_df 
            WHERE {config.metric_column} IS NOT NULL
            ORDER BY {config.metric_column} {config.sort_order} 
            LIMIT {config.limit}
        """
    elif chart_type == "scatter":
        return f"""
            SELECT {config.name_column}, {config.group_column}, 
                   {config.x_metric_column}, {config.y_metric_column} 
            FROM my_df
            WHERE {config.x_metric_column} IS NOT NULL 
              AND {config.y_metric_column} IS NOT NULL
        """
    elif chart_type == "radar":
        metrics_sql = ", ".join(config.metric_columns)
        return f"""
            SELECT {config.name_column}, {metrics_sql} 
            FROM my_df 
            WHERE LOWER({config.name_column}) LIKE LOWER('%{config.target_player}%')
            LIMIT 1
        """
    return ""

def _generate_data_with_llama(user_query: str, chart_type: str) -> Tuple[pd.DataFrame, Any]:
    """
    Uses LLM to determine appropriate columns and generates data via SQL.
    Includes self-correction if column names are wrong.
    """
    df_source = load_data()
    if chart_type == "radar":
        cols_context = get_columns_with_types(df_source)
        extra_instructions = """
CRITICAL: For 'metric_columns', select ONLY columns with types 'int64' or 'float64'.
DO NOT select 'object' type columns (these are text/strings, not numbers).
Look for metrics like distance, speed, acceleration, etc."""
    else:
        cols_context = get_columns_string(df_source)
        extra_instructions = ""
    
    # Setup DuckDB connection
    con = duckdb.connect(database=':memory:')
    con.register('my_df', df_source)
    
    print(f"\n--- LLM Reasoning for {chart_type.upper()} Chart ---")
    
    # Select config model
    config_model = {
        "bar": BarChartConfig,
        "scatter": ScatterPlotConfig,
        "radar": RadarChartConfig
    }[chart_type]
    
    structured_llm = llm_reasoner.with_structured_output(config_model)
    
    # ATTEMPT 1: Initial query
    base_prompt = f"""You are analyzing Australian A-League midfielder data.

AVAILABLE COLUMNS: {cols_context}

USER QUERY: {user_query}

YOUR TASK: Select the exact column names (case-sensitive) that best answer the query.
{extra_instructions}

Provide reasoning for your choices."""

    try:
        config = structured_llm.invoke(base_prompt)
        sql = _generate_sql_from_config(config, chart_type)
        
        print(f"Generated SQL:\n{sql}")
        result_df = con.execute(sql).df()
        
        if result_df.empty:
            print("Query returned no results")
            return pd.DataFrame(), None
        
        print(f"Retrieved {len(result_df)} rows")
        return result_df, config
    
    except Exception as initial_error:
        error_msg = str(initial_error)
        print(f"Initial attempt failed: {error_msg}")
        print("--- Attempting self-correction ---")
        
        correction_prompt = f"""PREVIOUS ATTEMPT FAILED with error:
{error_msg}

The error message often contains the CORRECT column names in quotes or "Candidate bindings".

AVAILABLE COLUMNS: {cols_context}
ORIGINAL USER QUERY: {user_query}

YOUR TASK: Fix the column names based on the error message. Look for exact matches in the available columns list.
{extra_instructions}"""

        try:
            config = structured_llm.invoke(correction_prompt)
            sql = _generate_sql_from_config(config, chart_type)
            
            print(f"Corrected SQL:\n{sql}")
            result_df = con.execute(sql).df()
            
            if result_df.empty:
                print("Corrected query returned no results")
                return pd.DataFrame(), None
            
            print(f" Retrieved {len(result_df)} rows after correction")
            return result_df, config
        
        except Exception as final_error:
            print(f"Self-correction also failed: {final_error}")
            return pd.DataFrame(), None



class ChartInput(BaseModel):
    """Input schema for all chart tools."""
    query: str = Field(..., description="User's question or request for visualization.")
    title: str = Field(..., description="Descriptive title for the chart.")

@tool(args_schema=ChartInput)
def create_dynamic_bar_chart(query: str, title: str) -> str:
    """
    Creates a horizontal bar chart ranking players by a single metric.
    
    USE CASES:
    - "Top 10 fastest players"
    - "Players with most distance covered"
    - "Lowest sprint count"
    
    Returns: PNG filename and data table in markdown format.
    """
    try:
        df_plot, config = _generate_data_with_llama(query, chart_type="bar")
        
        if df_plot.empty or config is None:
            return "Error: Could not generate bar chart. No data returned from query."
        
        # Create visualization
        if SKILLCORNER_AVAILABLE:
            fig, ax = bar.plot_bar_chart(
                df_plot,
                metric=config.metric_column,
                data_point_id=config.name_column,
                data_point_label=config.name_column,
                plot_title=title,
                label=config.metric_column.replace('_', ' ').title(),
                unit="",
                primary_highlight_color='#006D00',
                add_bar_values=True
            )
        else:
            # Fallback matplotlib implementation
            fig, ax = plt.subplots(figsize=(10, 8))
            ax.barh(df_plot[config.name_column], df_plot[config.metric_column], color='#006D00')
            ax.set_xlabel(config.metric_column.replace('_', ' ').title())
            ax.set_ylabel('Player')
            ax.set_title(title)
            plt.tight_layout()
        
        filename = f"bar_{config.metric_column}.png"
        fig.savefig(filename, bbox_inches="tight", dpi=300)
        plt.close(fig)
        
        print(f"Saved: {filename}")
        
        # Return results
        result = f"""**Bar Chart Created**: `{filename}`

**Chart Details:**
- Metric: {config.metric_column}
- Players shown: {len(df_plot)}
- Sort order: {config.sort_order}

**Data Table:**
{df_plot.to_markdown(index=False)}

**Reasoning:** {config.reasoning}
"""
        return result
    
    except Exception as e:
        return f"Bar Chart Error: {str(e)}"


@tool(args_schema=ChartInput)
def create_dynamic_scatter_plot(query: str, title: str) -> str:
    """
    Creates a scatter plot comparing two metrics across players.
    
    USE CASES:
    - "Compare speed vs distance"
    - "Relationship between sprints and high-speed running"
    - "Correlation analysis"
    
    Returns: PNG filename with top 5, bottom 5, and outliers labeled.
    """
    try:
        df_plot, config = _generate_data_with_llama(query, chart_type="scatter")
        
        if df_plot.empty or config is None:
            return "❌ Error: Could not generate scatter plot. No data returned from query."
        
        # Determine primary metric for labeling
        label_metric = config.top_n_metric if config.top_n_metric in df_plot.columns else config.y_metric_column
        
        # Get top 5 and bottom 5 players
        top_5_df = df_plot.nlargest(5, label_metric)
        bottom_5_df = df_plot.nsmallest(5, label_metric)
        
        top_5_names = set(top_5_df[config.name_column].tolist())
        bottom_5_names = set(bottom_5_df[config.name_column].tolist())
        
        print(f"📊 Top 5 by {label_metric}: {list(top_5_names)}")
        print(f"📊 Bottom 5 by {label_metric}: {list(bottom_5_names)}")
        
        # Create matplotlib scatter plot
        fig, ax = plt.subplots(figsize=(14, 10))
        
        # Plot all points
        ax.scatter(
            df_plot[config.x_metric_column], 
            df_plot[config.y_metric_column],
            alpha=0.5,
            s=100,
            c='#cccccc',
            edgecolors='black',
            linewidth=0.5,
            label='All Players'
        )
        
        # Highlight top 5 (green)
        top_5_data = df_plot[df_plot[config.name_column].isin(top_5_names)]
        ax.scatter(
            top_5_data[config.x_metric_column],
            top_5_data[config.y_metric_column],
            alpha=0.8,
            s=150,
            c='#006D00',
            edgecolors='black',
            linewidth=1.5,
            label='Top 5',
            zorder=5
        )
        
        # Highlight bottom 5 (red)
        bottom_5_data = df_plot[df_plot[config.name_column].isin(bottom_5_names)]
        ax.scatter(
            bottom_5_data[config.x_metric_column],
            bottom_5_data[config.y_metric_column],
            alpha=0.8,
            s=150,
            c='#d62728',
            edgecolors='black',
            linewidth=1.5,
            label='Bottom 5',
            zorder=5
        )
        
        # Add labels for top 5 (above points)
        for _, row in top_5_data.iterrows():
            ax.annotate(
                row[config.name_column],
                xy=(row[config.x_metric_column], row[config.y_metric_column]),
                xytext=(0, 10),
                textcoords='offset points',
                ha='center',
                fontsize=9,
                fontweight='bold',
                color='#006D00',
                bbox=dict(boxstyle='round,pad=0.3', facecolor='white', edgecolor='#006D00', alpha=0.8)
            )
        
        # Add labels for bottom 5 (below points)
        for _, row in bottom_5_data.iterrows():
            ax.annotate(
                row[config.name_column],
                xy=(row[config.x_metric_column], row[config.y_metric_column]),
                xytext=(0, -10),
                textcoords='offset points',
                ha='center',
                fontsize=9,
                fontweight='bold',
                color='#d62728',
                bbox=dict(boxstyle='round,pad=0.3', facecolor='white', edgecolor='#d62728', alpha=0.8)
            )
        
        # Add trend line
        z = np.polyfit(df_plot[config.x_metric_column], df_plot[config.y_metric_column], 1)
        p = np.poly1d(z)
        ax.plot(
            df_plot[config.x_metric_column],
            p(df_plot[config.x_metric_column]),
            "k--",
            alpha=0.3,
            linewidth=1,
            label='Trend Line'
        )
        
        # Formatting
        ax.set_xlabel(config.x_metric_column.replace('_', ' ').title(), fontsize=12, fontweight='bold')
        ax.set_ylabel(config.y_metric_column.replace('_', ' ').title(), fontsize=12, fontweight='bold')
        ax.set_title(title, fontsize=14, fontweight='bold', pad=20)
        ax.legend(loc='best', framealpha=0.9)
        ax.grid(True, alpha=0.3, linestyle='--')
        
        plt.tight_layout()
        
        filename = "scatter_plot_generated.png"
        fig.savefig(filename, bbox_inches="tight", dpi=300, facecolor='white')
        plt.close(fig)
        
        print(f"✅ Saved: {filename}")
        
        # Combine top and bottom for summary
        highlighted_df = pd.concat([top_5_df, bottom_5_df]).drop_duplicates()
        
        result = f"""✅ **Scatter Plot Created**: `{filename}`

**Chart Details:**
- X-axis: {config.x_metric_column}
- Y-axis: {config.y_metric_column}
- Total players: {len(df_plot)}
- Highlighted: Top 5 (🟢 green) and Bottom 5 (🔴 red) by {label_metric}

**Top 5 Players:**
{top_5_df[[config.name_column, config.x_metric_column, config.y_metric_column]].to_markdown(index=False)}

**Bottom 5 Players:**
{bottom_5_df[[config.name_column, config.x_metric_column, config.y_metric_column]].to_markdown(index=False)}

**Reasoning:** {config.reasoning}
"""
        return result
    
    except Exception as e:
        return f"❌ Scatter Plot Error: {str(e)}"

@tool(args_schema=ChartInput)
def create_dynamic_radar_chart(query: str, title: str) -> str:
    """
    Creates a radar/spider chart profiling a single player across multiple metrics.
    
    USE CASES:
    - "Show me [player name]'s profile"
    - "What are [player]'s strengths?"
    - "Visualize [player]'s performance"
    
    Returns: PNG filename with player's metrics compared to league min/max.
    """
    try:
        df_plot, config = _generate_data_with_llama(query, chart_type="radar")
        
        if df_plot.empty or config is None:
            return f" Error: Could not find player data. Make sure the player name is spelled correctly."
        
        df_source = load_data()
        params = config.metric_columns
        low = [df_source[col].min() for col in params]
        high = [df_source[col].max() for col in params]
        player_values = df_plot.iloc[0][params].tolist()
        player_name = df_plot.iloc[0][config.name_column]
        radar = Radar(params, low, high, num_rings=4, ring_width=1, center_circle_radius=1)
        fig, ax = radar.setup_axis()
        
        radar.draw_circles(ax=ax, facecolor='#ffb2b2', edgecolor='#fc5f5f')
        radar.draw_radar(player_values, ax=ax, kwargs_radar={'facecolor': '#aa65b2', 'alpha': 0.6})
        radar.draw_range_labels(ax=ax, fontsize=10)
        radar.draw_param_labels(ax=ax, fontsize=12)
        
        fig.suptitle(f"{title}\n{player_name}", fontsize=14, y=0.98)
        
        filename = f"radar_{player_name.replace(' ', '_')}.png"
        fig.savefig(filename, bbox_inches="tight", dpi=150)
        plt.close(fig)
        
        print(f"✅ Saved: {filename}")
        metrics_df = pd.DataFrame({
            'Metric': params,
            'Player Value': player_values,
            'League Min': low,
            'League Max': high
        })
        
        result = f"""**Radar Chart Created**: `{filename}`

**Player Profile:** {player_name}

**Metrics Analyzed:**
{metrics_df.to_markdown(index=False)}

**Interpretation:**
- Values closer to the edge indicate performance closer to league maximum
- Each ring represents 25% of the range between min and max
- Metrics: {', '.join([m.replace('_', ' ').title() for m in params])}

**Reasoning:** {config.reasoning}
"""
        return result
    
    except Exception as e:
        return f"Radar Chart Error: {str(e)}"