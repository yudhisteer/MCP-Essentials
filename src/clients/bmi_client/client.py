from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
import asyncio
from mcp.types import ListToolsResult
from openai import OpenAI
import os
import json
from src.shared.utils import debug_print

def prompt_to_identify_tools(tools: ListToolsResult, query: str) -> str:
    """
    Generate a structured prompt for tool selection and usage.
    
    This function creates a formatted prompt that helps the LLM understand:
    - Available tools and their capabilities
    - The user's query
    - How to format tool usage responses
    
    Args:
        tools: List of available tools with their descriptions and schemas
        query: User's question or request
        
    Returns:
        str: A well-structured prompt for the LLM
    """
    # Format tools information in a clear, structured way
    tools_info = "\n".join([
        f"Tool: {tool.name}\n"
        f"Description: {tool.description}\n"
        f"Input Schema: {tool.inputSchema}\n"
        for tool in tools.tools
    ])
    
    return f"""You are a helpful AI assistant with access to specialized tools. Your task is to help users by either:
    1. Directly answering their questions when no tool is needed
    2. Using the appropriate tool when required

    Available Tools:
    {tools_info}

    User's Question: {query}

    If you need to use a tool, respond ONLY with a JSON object in this exact format:
    {{
        "tool": "tool-name",
        "arguments": {{
            "argument-name": "value"
        }}
    }}

    If no tool is needed, respond directly with your answer.

    Remember:
    - Only use tools when necessary
    - Follow the exact JSON format when using tools
    - Provide clear, helpful responses when answering directly"""

def llm_client(message:str) -> str:
    """
    Send a message to the LLM and return the response.
    
    This function:
    - Initializes the OpenAI client
    - Sends a message to GPT-4
    - Returns the model's response
    
    Args:
        message: The prompt to send to the LLM
        
    Returns:
        str: The LLM's response
    """
    openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    response = openai_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role":"system", "content":"You are an intelligent assistant. You will execute tasks as prompted"},
            {"role": "user", "content": message}
        ],
    )

    return response.choices[0].message.content.strip()

# Configure the MCP server connection parameters
# This tells the client how to start and connect to the BMI server
server_params = StdioServerParameters(
    command="python",  # Use Python interpreter
    args=["src/servers/bmi_server/server.py"]  # Path to the BMI server script
)

async def main(query: str) -> None:
    """
    Main function that orchestrates the BMI calculation process.
    
    This function:
    1. Establishes connection with the BMI server
    2. Gets available tools
    3. Uses LLM to determine which tool to use
    4. Executes the tool call
    5. Processes and displays results
    
    Args:
        query: The user's question about BMI calculation
    """
    # Create a stdio connection to the server
    async with stdio_client(server_params) as (read, write):
        # Create a client session for MCP communication
        async with ClientSession(read, write) as session:
            # Initialize the MCP session
            await session.initialize()

            # Get list of available tools from the server
            tools = await session.list_tools()
            debug_print("Available tools:", tools)

            # Create a prompt to help LLM choose the right tool
            prompt_for_tools_selection = prompt_to_identify_tools(tools, query)
            debug_print("Prompt:", prompt_for_tools_selection)

            # Get LLM's decision on which tool to use
            llm_response = llm_client(prompt_for_tools_selection)
            debug_print("LLM response:", llm_response)  

            # Convert the LLM string response into a dict
            tool_call = json.loads(llm_response)
            debug_print("Tool call:", tool_call)

            # Execute the tool call and get the result
            result = await session.call_tool(tool_call["tool"], arguments=tool_call["arguments"])
            debug_print("Result:", result)
            formatted_result = result.content[0].text
            debug_print(f"BMI for weight {tool_call["arguments"]["weight_kg"]}kg and height {tool_call["arguments"]["height_cm"]}cm is {formatted_result}")

            # Get a natural language explanation of the result from the LLM
            result_prompt = f"Here is the result for the query '{query}': The BMI is {formatted_result}"
            result_llm_response = llm_client(result_prompt)
            print("Result LLM response:", result_llm_response)

# Entry point of the script
if __name__ == "__main__":
    # Example query to demonstrate the functionality
    query = "What is the BMI of a 180cm tall person weighing 84kg?"
    asyncio.run(main(query))
