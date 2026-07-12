from mcp.server.fastmcp import FastMCP

from config import DB_CONFIG
from create_logger import setup_logger
from query_data.query1 import BazaarService

logger = setup_logger("BazaarMCP")


def create_bazaar_mcp_server():
    bazaar_mcp = FastMCP(
        name="BazaarTools",
        instructions="市集查询工具，基于 magical_items 表。可用于查询各类魔法物品、按稀有度/产地/类别筛选。",
        log_level="ERROR",
        host="127.0.0.1",
        port=8001,
    )

    service = BazaarService()

    @bazaar_mcp.tool(
        name="query_items",
        description="查询魔法物品数据。输入SQL，如 SELECT * FROM magical_items WHERE category='potion' AND rarity='Epic'",
    )
    def query_items(sql: str) -> str:
        logger.info(f"执行物品查询: {sql}")
        return service.execute_query(sql)

    logger.info("=== Bazaar MCP Server ===")
    logger.info(f"Name: {bazaar_mcp.name}")

    try:
        print("Bazaar MCP Server running at http://127.0.0.1:8001/mcp")
        bazaar_mcp.run(transport="streamable-http")
    except Exception as e:
        print(f"Server start failed: {e}")


if __name__ == "__main__":
    create_bazaar_mcp_server()
