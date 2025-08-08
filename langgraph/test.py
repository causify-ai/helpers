"""Test script for AutoEDA Agent LangGraph."""

import asyncio
import json
from pathlib import Path

from langgraph_sdk import get_client

client = get_client(url="http://localhost:2024")

async def test_autoeda_agent():
    """Test the AutoEDA agent with sample data."""
    
    # Test data file path (absolute path to ensure it's found)
    test_file_path = "/home/maddev/src/helpers1/langgraph/src/agent/data.csv"
    
    # Sample schema content for testing
    sample_schema = {
        "type": "object",
        "properties": {
            "user_id": {
                "type": "integer",
                "description": "Unique identifier for user"
            },
            "username": {
                "type": "string",
                "description": "User's login name"
            },
            "email": {
                "type": "string",
                "format": "email",
                "description": "User's email address"
            },
            "age": {
                "type": "integer",
                "minimum": 0,
                "maximum": 150
            },
            "is_active": {
                "type": "boolean",
                "default": True
            }
        },
        "required": ["user_id", "username", "email"]
    }
    
    print("Testing AutoEDA Agent...")
    print(f"File path: {test_file_path}")
    print("=" * 50)
    
    try:
        async for chunk in client.runs.stream(
            None,  # Threadless run
            "agent",  # Name of assistant defined in langgraph.json
            input={
                "file_path": test_file_path,
                "schema_content": json.dumps(sample_schema, indent=2),
                "changeme": "Analyze this dataset for AutoEDA insights"
            },
            config={
                "configurable": {
                    "my_configurable_param": "AutoEDA_Analysis",
                    "openai_model": "gpt-3.5-turbo"
                }
            }
        ):
            print(f"Event: {chunk.event}")
            if hasattr(chunk, 'node') and chunk.node:
                print(f"Node: {chunk.node}")
            
            if chunk.data:
                if isinstance(chunk.data, dict):
                    # Pretty print the data
                    for key, value in chunk.data.items():
                        if key == "changeme" and isinstance(value, str):
                            print(f"\nAutoEDA Output:\n{value}")
                        elif key == "raw_data_result":
                            print(f"\nRaw Data Analysis Result:")
                            if isinstance(value, dict):
                                if "error" in value:
                                    print(f"  Error: {value['error']}")
                                else:
                                    print(f"  File: {value.get('file_path', 'unknown')}")
                                    print(f"  Rows: {value.get('total_rows', 0)}")
                                    print(f"  Columns: {value.get('total_columns', 0)}")
                            else:
                                print(f"  {value}")
                        elif key == "schema_result":
                            print(f"\nSchema Analysis Result:")
                            if isinstance(value, dict):
                                if "error" in value:
                                    print(f"  Error: {value['error']}")
                                else:
                                    print(f"  Total columns: {value.get('total_columns', 0)}")
                                    print(f"  Required: {value.get('required_columns', 0)}")
                                    print(f"  Optional: {value.get('optional_columns', 0)}")
                                    print(f"  Schema type: {value.get('schema_type', 'unknown')}")
                            else:
                                print(f"  {value}")
                        else:
                            print(f"{key}: {value}")
                else:
                    print(f"Data: {chunk.data}")
            print("-" * 30)
            
    except Exception as e:
        print(f"Error running AutoEDA agent: {e}")
        import traceback
        traceback.print_exc()

async def test_error_handling():
    """Test error handling with invalid inputs."""
    
    print("\nTesting error handling...")
    print("=" * 50)
    
    try:
        async for chunk in client.runs.stream(
            None,
            "agent",
            input={
                "file_path": "nonexistent_file.csv",
                "schema_content": "invalid json content",
                "changeme": "Test error handling"
            },
            config={
                "configurable": {
                    "my_configurable_param": "Error_Test",
                    "openai_model": "gpt-3.5-turbo"
                }
            }
        ):
            print(f"Event: {chunk.event}")
            if chunk.data:
                print(f"Data: {chunk.data}")
            print("-" * 30)
            
    except Exception as e:
        print(f"Expected error caught: {e}")

async def test_direct_nodes():
    """Test the nodes directly to verify they work."""
    print("\nTesting nodes directly...")
    print("=" * 50)
    
    try:
        # Import the graph and nodes
        from src.agent.graph import analyze_raw_data, parse_schema, State
        from langchain_core.runnables import RunnableConfig
        
        # Create test state
        state = State(
            file_path="/home/maddev/src/helpers1/langgraph/src/agent/data.csv",
            schema_content=json.dumps({
                "type": "object",
                "properties": {
                    "user_id": {"type": "integer"},
                    "username": {"type": "string"},
                    "email": {"type": "string"}
                },
                "required": ["user_id", "username"]
            })
        )
        
        config = RunnableConfig(configurable={})
        
        # Test raw data analysis
        print("Testing raw data analysis...")
        raw_result = await analyze_raw_data(state, config)
        print(f"Raw data result: {raw_result}")
        
        # Test schema parsing
        print("\nTesting schema parsing...")
        schema_result = await parse_schema(state, config)
        print(f"Schema result: {schema_result}")
        
    except Exception as e:
        print(f"Error in direct node testing: {e}")
        import traceback
        traceback.print_exc()

async def main():
    """Run all tests."""
    await test_autoeda_agent()
    await test_error_handling()
    await test_direct_nodes()

if __name__ == "__main__":
    asyncio.run(main())
