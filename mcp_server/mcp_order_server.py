from mcp.server.fastmcp import FastMCP

from create_logger import setup_logger

logger = setup_logger("OrderMCP")

order_mcp = FastMCP(
    name="OrderTools",
    instructions="魔法物品订购工具，完成顾客对魔法物品的购买与预定。",
    log_level="ERROR",
    host="127.0.0.1",
    port=8003,
)


@order_mcp.tool(
    name="order_item",
    description="订购魔法物品。输入物品名称、数量、买家名号，完成购买。",
)
def order_item(item_name: str, quantity: int, buyer: str) -> str:
    """
    Args:
        item_name: 物品名称，如 '凤凰羽笔'
        quantity: 购买数量
        buyer: 买家名号，如 '大法师甘道夫'
    """
    logger.info(f"订购魔法物品: {item_name} x{quantity} — 买家: {buyer}")
    logger.info(f"交易完成！{buyer} 成功购得 {item_name} x{quantity}。")
    return f"恭喜，{buyer}！您已成功购得「{item_name}」x{quantity}。货物将由狮鹫快递送达，请注意查收（狮鹫可能会索要零食）。"


def create_order_mcp_server():
    logger.info("=== Order MCP Server ===")
    logger.info(f"Name: {order_mcp.name}")

    try:
        print("Order MCP Server running at http://127.0.0.1:8003/mcp")
        order_mcp.run(transport="streamable-http")
    except Exception as e:
        print(f"Server start failed: {e}")


if __name__ == "__main__":
    create_order_mcp_server()
