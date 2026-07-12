"""
Test the Phenomena MCP server connection.
Run after starting mcp_phenomena_server.py
"""
import asyncio
import json
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client


async def main():
    try:
        async with streamablehttp_client("http://127.0.0.1:8002/mcp") as (read, write, _):
            async with ClientSession(read, write) as session:
                await session.initialize()

                result = await session.call_tool(
                    "query_phenomena",
                    {"sql": "SELECT * FROM mystical_phenomena WHERE realm='艾尔德格罗夫' AND fx_date='2026-07-13'"}
                )
                data = json.loads(result.content[0].text)
                print(json.dumps(data, ensure_ascii=False, indent=2))
    except Exception as e:
        print(f"Test failed: {e}")


if __name__ == "__main__":
    asyncio.run(main())
