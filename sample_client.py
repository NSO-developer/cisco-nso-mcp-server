#!/usr/bin/env python3
"""
Sample client for Cisco NSO MCP Server

This script demonstrates how to connect to the MCP server and list available tools.
"""
import asyncio
import os
from fastmcp import Client
from fastmcp.client.transports import PythonStdioTransport


async def main():
    print("Connecting to MCP server...")

    # create server parameters
    server_params = PythonStdioTransport(
        python_cmd="python3",
        script_path="cisco_nso_mcp_server/server.py",
        args=[
            "--nso-scheme=https",
            "--nso-address=127.0.0.1",
            "--nso-port=8888",
            "--nso-username=admin",
            "--nso-password=admin",
            "--no-nso-verify"
        ],
        env={**os.environ}
    )

    # create and enter the context managers directly in this task
    # Use 'Client(server_params)' to use stdio transport
    # Use 'Client("http://127.0.0.1:8000/mcp")' to use HTTP transport
    async with Client(server_params) as client:

        # list available tools
        tools = await client.list_tools()
        print("\nAvailable tools:")
        for tool in tools:
            print(f"- {tool.name}: {tool.description}")

        # call a tool
        ned_response = await client.call_tool("get_device_ned_ids")
        print("\nNED IDs:")
        print(ned_response.content[0].text)

if __name__ == "__main__":
    asyncio.run(main())
