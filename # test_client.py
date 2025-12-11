# test_client.py
import asyncio
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

URL = "https://gnenhisgbx.us-east-1.awsapprunner.com/mcp"  # raíz (como lo dejamos)

async def main():
    async with streamablehttp_client(URL) as (read_stream, write_stream, _):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            tools = await session.list_tools()
            print("TOOLS:", [t.name for t in tools.tools])

            # ejemplo: invocar list_projects sin filtros
            result = await session.call_tool("list_projects", {})
            print("RESULT:", result)

asyncio.run(main())