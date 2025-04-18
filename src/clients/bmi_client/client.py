from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
import asyncio
from mcp.types import ListToolsResult
server_params = StdioServerParameters(command="python", args=["src/servers/bmi_server/server.py"])
from openai import OpenAI
import os
import json
from src.shared.utils import debug_print

def prompt_to_identify_tools(tools: ListToolsResult, query: str) -> str:
    """
    Generate a structured prompt for tool selection and usage.
    
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

async def main(query: str) -> None:
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:

            # Initialize the session
            await session.initialize()

            # Get the list of available tools
            tools = await session.list_tools()
            debug_print("Available tools:", tools)

            # Generate a structured prompt for tool selection and usage
            prompt_for_tools_selection = prompt_to_identify_tools(tools, query)
            debug_print("Prompt:", prompt_for_tools_selection)

            # Send the prompt to the LLM
            llm_response = llm_client(prompt_for_tools_selection)
            debug_print("LLM response:", llm_response)  

            # Parse the LLM response to get the tool call
            tool_call = json.loads(llm_response)
            debug_print("Tool call:", tool_call)

            # Execute the tool call
            result = await session.call_tool(tool_call["tool"], arguments=tool_call["arguments"])
            formatted_result = result.content[0].text
            debug_print(f"BMI for weight {tool_call["arguments"]["weight_kg"]}kg and height {tool_call["arguments"]["height_cm"]}cm is {formatted_result}")

            # Send the result back to the LLM
            result_prompt = f"Here is the result for the query '{query}': The BMI is {formatted_result}"
            result_llm_response = llm_client(result_prompt)
            print("Result LLM response:", result_llm_response)


if __name__ == "__main__":
    query = "What is the BMI of a 180cm tall person weighing 84kg?"
    asyncio.run(main(query))
