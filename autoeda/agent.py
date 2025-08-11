"""
LangChain single-node agent template with OpenAI API integration and .env
support.

This refactors the original LangGraph single-node graph template to use
LangChain's Runnable workflow and standard components.

Import as:

import autoeda.agent as auagent
"""

import dataclasses
import os
from typing import Any, Dict, Optional

import dotenv
import langchain_core.runnables as lcrun  # type: ignore
import openai  # type: ignore

import autoeda.raw_data_analyzer as aradaana
import autoeda.schema_parser as aschpars

# Load environment variables from .env.
dotenv.load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
client = openai.OpenAI(api_key=OPENAI_API_KEY)


# #############################################################################
# Configuration
# #############################################################################


@dataclasses.dataclass
class Configuration:
    """
    Configurable parameters for the agent.
    """

    openai_model: str = "gpt-3.5-turbo"
    analysis_depth: str = "standard"  # "basic", "standard", "deep"
    include_schema_metadata: bool = True


# #############################################################################
# State
# #############################################################################


@dataclasses.dataclass
class State:
    """
    Input state for the agent.
    """

    file_path: str = ""
    raw_data_result: Optional[Dict[str, Any]] = None
    schema_file_path: str = ""
    schema_content: str = ""
    schema_result: Optional[Dict[str, Any]] = None
    analysis_output: str = ""


# #############################################################################
# Steps as LangChain Runnables
# #############################################################################


def call_model(state: State, config: Configuration) -> State:
    """
    Process input and returns output using OpenAI API.
    """
    model = config.openai_model
    # Check for errors and build appropriate context
    error_context = ""
    if state.raw_data_result and "error" in state.raw_data_result:
        error_context = f"️Data analysis failed: {state.raw_data_result['error']}"
    elif state.schema_result and "error" in state.schema_result:
        error_context = f"Schema parsing failed: {state.schema_result['error']}"
    if error_context:
        prompt = f"""You are an AutoEDA assistant. An error occurred during data analysis:
































{error_context}

Please provide:
1. Potential causes of this error
2. Troubleshooting steps to resolve the issue
3. Alternative approaches for data analysis
4. General recommendations for handling similar data files
"""
    else:
        # Build consolidated dataset summary
        total_rows = (
            state.raw_data_result.get("total_rows", 0)
            if state.raw_data_result
            else 0
        )
        total_columns = (
            state.raw_data_result.get("total_columns", 0)
            if state.raw_data_result
            else 0
        )
        file_path = (
            state.raw_data_result.get("file_path", "unknown")
            if state.raw_data_result
            else "unknown"
        )

        # Determine dataset characteristics for targeted analysis
        dataset_size = (
            "small"
            if total_rows < 1000
            else "medium" if total_rows < 100000 else "large"
        )
        dataset_width = (
            "narrow"
            if total_columns < 10
            else "wide" if total_columns < 50 else "very wide"
        )

        # Build schema insights
        schema_insights = ""
        if state.schema_result and "error" not in state.schema_result:
            required_cols = state.schema_result.get("required_columns", 0)
            optional_cols = state.schema_result.get("optional_columns", 0)
            schema_type = state.schema_result.get("schema_type", "unknown")

            schema_insights = f"""
Schema Structure ({schema_type}):
• {total_columns} columns total ({required_cols} required, {optional_cols} optional)
• Column breakdown:"""

            # Group columns by data type for better insights
            col_types: Dict[str, int] = {}
            nullable_count = 0
            for col in state.schema_result.get("columns", []):
                data_type = col["data_type"]
                col_types[data_type] = col_types.get(data_type, 0) + 1
                if col.get("nullable", False):
                    nullable_count += 1

            for dtype, count in col_types.items():
                schema_insights += f"\n  - {dtype}: {count} columns"

            if nullable_count > 0:
                schema_insights += (
                    f"\n• {nullable_count} columns allow null values"
                )

        # Build targeted recommendations based on dataset characteristics
        analysis_focus = ""
        if dataset_size == "small":
            analysis_focus = "completeness analysis and pattern detection"
        elif dataset_size == "large":
            analysis_focus = "sampling strategies and performance optimization"
        else:
            analysis_focus = "statistical profiling and distribution analysis"

        if dataset_width in {"wide", "very wide"}:
            analysis_focus += ", feature selection and dimensionality reduction"

        prompt = (
            f"You are an expert AutoEDA assistant. "
            f"Analyze this {dataset_size}, {dataset_width} dataset:\n\n"
            f"Dataset Overview:\n"
            f"• File: {file_path}\n"
            f"• Size: {total_rows:,} rows × {total_columns} columns\n"
            f"• Focus areas: {analysis_focus}\n"
            f"{schema_insights}\n\n"
            f"Based on these characteristics, provide targeted recommendations:\n\n"
            f"1. **Data Quality Assessment**: Identify specific validation rules, "
            f"missing value patterns, and potential anomalies to investigate\n\n"
            f"2. **Statistical Analysis Plan**: Recommend appropriate statistical "
            f"methods and exploratory techniques for this dataset size and structure\n\n"
            f"3. **Visualization Strategy**: Suggest specific chart types and "
            f"visualization approaches that work best for this data profile\n\n"
            f"4. **Risk Areas**: Highlight potential data quality issues, biases, "
            f"or limitations to investigate based on the schema and size\n\n"
            f"5. **Next Steps**: Provide a prioritized action plan for the "
            f"exploratory data analysis process\n\n"
            f"Keep recommendations practical and specific to the dataset characteristics."
        )

    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,  # Lower temperature for more consistent, analytical responses
        max_tokens=1024,  # Increased for more detailed recommendations
    )

    output_text = response.choices[0].message.content

    state.analysis_output = output_text
    return state


def analyze_raw_data(state: State, _config: Configuration) -> State:
    """
    Analyze raw data file and generate schema.
    """
    if not state.file_path:
        state.raw_data_result = {"error": "No file path provided"}
        return state
    analyzer = aradaana.RawDataAnalyzer()
    result = analyzer.analyze_file(state.file_path)
    if result.error_message:
        state.raw_data_result = {"error": result.error_message}
        return state
    # Convert result to dict for state
    raw_data_result = {
        "file_path": result.file_path,
        "total_rows": result.total_rows,
        "total_columns": result.total_columns,
        "suggested_schema": result.suggested_schema,
        "analysis_metadata": result.analysis_metadata,
    }
    state.raw_data_result = raw_data_result
    # Generate schema file
    schema_file_path = state.file_path + ".schema.json"
    try:
        analyzer.save_schema(result, schema_file_path)
        state.schema_file_path = schema_file_path
        # Load schema content from the generated file
        with open(schema_file_path, "r", encoding="utf-8") as f:
            schema_content = f.read()
        state.schema_content = schema_content
    except (OSError, IOError) as e:
        state.raw_data_result["schema_file_error"] = str(e)
    return state


def parse_schema(state: State, _config: Configuration) -> State:
    """
    Parse schema content and extract column information.
    """
    if not state.schema_content:
        state.schema_result = {"error": "No schema content provided"}
        return state
    result = aschpars.parse_schema_content(state.schema_content)
    if result.error_message:
        state.schema_result = {"error": result.error_message}
        return state
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
                "nullable": col.nullable,
            }
            for col in result.columns
        ],
    }
    state.schema_result = schema_result
    return state


# #############################################################################
# AutoEDAAgent
# #############################################################################


class AutoEDAAgent:
    """
    AutoEDA Agent implemented using LangChain Runnables.
    """

    def __init__(self, config: Optional[Configuration] = None):
        self.config = config or Configuration()
        self.workflow = (
            lcrun.RunnableSequence()
            .add(
                lcrun.RunnableLambda(
                    lambda state: analyze_raw_data(state, self.config)
                )
            )
            .add(
                lcrun.RunnableLambda(
                    lambda state: parse_schema(state, self.config)
                )
            )
            .add(
                lcrun.RunnableLambda(lambda state: call_model(state, self.config))
            )
        )

    def run(self, state: State) -> State:
        result = self.workflow.invoke(state)
        return result  # type: ignore


# Example usage:
# agent = AutoEDAAgent(Configuration(
#     openai_model="gpt-4",
#     analysis_depth="deep",
#     include_schema_metadata=True
# ))
# initial_state = State(file_path="mydata.csv")
# # schema_content will be auto-generated from the file
# result_state = agent.run(initial_state)
# print(result_state.analysis_output)
