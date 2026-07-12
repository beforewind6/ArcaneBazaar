import mysql.connector
import json
from datetime import date, datetime, timedelta
from decimal import Decimal

from mcp.server.fastmcp import FastMCP

from config import DB_CONFIG
from create_logger import setup_logger
from utils.format import DateEncoder, default_encoder

logger = setup_logger("PhenomenaMCP")


class PhenomenaService:
    def __init__(self):
        self.conn = mysql.connector.connect(
            host=DB_CONFIG["host"],
            user=DB_CONFIG["user"],
            password=DB_CONFIG["password"],
            database=DB_CONFIG["database"],
        )

    def execute_query(self, sql: str) -> str:
        try:
            cursor = self.conn.cursor(dictionary=True)
            cursor.execute(sql)
            results = cursor.fetchall()
            cursor.close()
            for result in results:
                for key, value in result.items():
                    if isinstance(value, (date, datetime, timedelta, Decimal)):
                        result[key] = default_encoder(value)
            return json.dumps(
                {"status": "success", "data": results}
                if results
                else {"status": "no_data", "message": "水晶球一片模糊……未找到该领域或日期的异象数据。"},
                cls=DateEncoder,
                ensure_ascii=False,
            )
        except Exception as e:
            logger.error(f"异象查询错误: {str(e)}")
            return json.dumps({"status": "error", "message": str(e)}, ensure_ascii=False)


def create_phenomena_mcp_server():
    phenomena_mcp = FastMCP(
        name="PhenomenaTools",
        instructions="异象查询工具，基于 mystical_phenomena 表。可用于查询各领域的魔力浓度、异象类型、危险等级等。",
        log_level="ERROR",
        host="127.0.0.1",
        port=8002,
    )

    service = PhenomenaService()

    @phenomena_mcp.tool(
        name="query_phenomena",
        description="查询异象数据。输入SQL，如 SELECT * FROM mystical_phenomena WHERE realm='艾尔德格罗夫' AND fx_date='2026-07-13'",
    )
    def query_phenomena(sql: str) -> str:
        logger.info(f"执行异象查询: {sql}")
        return service.execute_query(sql)

    logger.info("=== Phenomena MCP Server ===")
    logger.info(f"Name: {phenomena_mcp.name}")

    try:
        print("Phenomena MCP Server running at http://127.0.0.1:8002/mcp")
        phenomena_mcp.run(transport="streamable-http")
    except Exception as e:
        print(f"Server start failed: {e}")


if __name__ == "__main__":
    create_phenomena_mcp_server()
