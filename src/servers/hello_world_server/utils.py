from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.types import ListToolsResult
import asyncio
import json

"""
This file contains utility functions for the hello world server.

It demonstrates how to:
- Configure the server parameters for stdio communication
- Create a stdio client connection using the server parameters
- Initialize a client session using the read/write channels
- Request the list of available tools from the server
"""

# Configure the server parameters for stdio communication
# This sets up how the client will communicate with the server process
server_params = StdioServerParameters(
    # The command to start the server process
    # In this case, we're using Python to run our server
    command="python",
    # Arguments to pass to the command
    # Here we're telling Python to run our server.py file
    args=["src/servers/hello_world_server/server.py"]
)
print("Server parameters:", server_params)

async def get_tools_list() -> ListToolsResult:
    # Create a stdio client connection using the server parameters
    # This establishes communication channels (read/write) with the server process
    async with stdio_client(server_params) as (read, write):
        # Create a new client session using the read/write channels
        # The session manages the communication protocol with the server
        async with ClientSession(read, write) as session:
            # Initialize the session - this sets up the initial handshake
            # and establishes the communication protocol
            await session.initialize()
            # Request the list of available tools from the server
            # This is an async operation that waits for the server's response
            tools = await session.list_tools()
            return tools

if __name__ == "__main__":
    # Get the list of available tools from the server
    tools = asyncio.run(get_tools_list()) # Type: <class 'mcp.types.ListToolsResult'>
    # Convert the Tool objects to dictionaries
    tools_dict = [tool.__dict__ for tool in tools.tools]
    # Print the tools in a readable JSON format
    print(json.dumps(tools_dict, indent=2))
