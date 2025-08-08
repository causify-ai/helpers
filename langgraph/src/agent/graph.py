"""LangGraph single-node graph template, with OpenAI API integration and .env support."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional, TypedDict

from langchain_core.runnables import RunnableConfig
from langgraph.graph import StateGraph
import openai

import os
from dotenv import load_dotenv

from .raw_data_analyzer import RawDataAnalyzer
from .schema_parser import parse_schema_content

# Load environment variables from .env.
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
client = openai.AsyncOpenAI(api_key=OPENAI_API_KEY)

class Configuration(TypedDict):
    """Configurable parameters for the agent."""
    my_configurable_param: str
    openai_model: str   

@dataclass
class State:
    """Input state for the agent."""
    file_path: str = ""
    raw_data_result: Optional[Dict[str, Any]] = None
    schema_content: str = ""
    schema_result: Optional[Dict[str, Any]] = None
    changeme: str = "example"

async def call_model(state: State, config: RunnableConfig) -> Dict[str, Any]:
    """Process input and returns output using OpenAI API."""
    configuration = config["configurable"]
    model = configuration.get("openai_model", "gpt-3.5-turbo")

    # Build context from schema parser results
    schema_context = ""
    if state.schema_result and "error" not in state.schema_result:
        schema_context = f"""
Schema Analysis Results:
- Total columns: {state.schema_result.get('total_columns', 0)}
- Required columns: {state.schema_result.get('required_columns', 0)}
- Optional columns: {state.schema_result.get('optional_columns', 0)}
- Schema type: {state.schema_result.get('schema_type', 'unknown')}

Column Details:
"""
        for col in state.schema_result.get('columns', []):
            schema_context += f"- {col['name']}: {col['data_type']} (required: {col['required']}, nullable: {col['nullable']})\n"
            if col.get('description'):
                schema_context += f"  Description: {col['description']}\n"

    # Build context from raw data analysis
    raw_data_context = ""
    if state.raw_data_result and "error" not in state.raw_data_result:
        raw_data_context = f"""
Raw Data Analysis Results:
- File: {state.raw_data_result.get('file_path', 'unknown')}
- Total rows: {state.raw_data_result.get('total_rows', 0)}
- Total columns: {state.raw_data_result.get('total_columns', 0)}
"""

    prompt = f"""You are an AutoEDA (Automated Exploratory Data Analysis) assistant. 
Based on the data analysis and schema information below, provide insights and recommendations for exploratory data analysis.

{raw_data_context}

{schema_context}

Configured parameter: {configuration.get('my_configurable_param')}
Additional context: {state.changeme}

Please provide:
1. Key insights about the dataset structure
2. Recommended exploratory data analysis steps
3. Potential data quality issues to investigate
4. Suggested visualizations or analysis techniques
"""

    response = await client.chat.completions.create(model=model,
    messages=[{"role": "user", "content": prompt}],
    temperature=0.7,
    max_tokens=512)

    output_text = response.choices[0].message.content

    return {
        "changeme": output_text
    }

async def analyze_raw_data(state: State, config: RunnableConfig) -> Dict[str, Any]:
    """Analyze raw data file and generate schema."""
    if not state.file_path:
        return {"raw_data_result": {"error": "No file path provided"}}
    
    analyzer = RawDataAnalyzer()
    result = analyzer.analyze_file(state.file_path)
    
    if result.error_message:
        return {"raw_data_result": {"error": result.error_message}}
    
    # Convert result to dict for state
    raw_data_result = {
        "file_path": result.file_path,
        "total_rows": result.total_rows,
        "total_columns": result.total_columns,
        "suggested_schema": result.suggested_schema,
        "analysis_metadata": result.analysis_metadata
    }
    
    return {"raw_data_result": raw_data_result}

async def parse_schema(state: State, config: RunnableConfig) -> Dict[str, Any]:
    """Parse schema content and extract column information."""
    if not state.schema_content:
        return {"schema_result": {"error": "No schema content provided"}}
    
    result = parse_schema_content(state.schema_content)
    
    if result.error_message:
        return {"schema_result": {"error": result.error_message}}
    
    # Convert result to dict for state
    schema_result = {
        "total_columns": result.total_columns,
        "required_columns": result.required_columns,
        "optional_columns": result.optional_columns,
        "schema_type": result.schema_type,
        "columns": [
            {
                "name": col.name,
                "data_type": col.data_type,
                "required": col.required,
                "description": col.description,
                "nullable": col.nullable
            } for col in result.columns
        ]
    }
    
    return {"schema_result": schema_result}

# Define the graph
graph = (
    StateGraph(State, config_schema=Configuration)
    .add_node("analyze_raw_data", analyze_raw_data)
    .add_node("parse_schema", parse_schema)
    .add_node("call_model", call_model)
    .add_edge("__start__", "analyze_raw_data")
    .add_edge("analyze_raw_data", "parse_schema")
    .add_edge("parse_schema", "call_model")
    .compile(name="AutoEDA Agent Graph")
)