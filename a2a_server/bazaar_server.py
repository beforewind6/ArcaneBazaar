import json
import asyncio
from datetime import datetime

import pytz
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client
from python_a2a import A2AServer, run_server, AgentCard, AgentSkill, TaskStatus, TaskState
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

from config import LLM_CONFIG
from create_logger import setup_logger

logger = setup_logger("BazaarAgent")

llm = ChatOpenAI(
    model=LLM_CONFIG["model"],
    base_url=LLM_CONFIG["base_url"],
    api_key=LLM_CONFIG["api_key"],
    temperature=LLM_CONFIG["temperature"],
)

table_schema_string = """
CREATE TABLE magical_items (
    id INT AUTO_INCREMENT PRIMARY KEY,
    item_name VARCHAR(128) NOT NULL COMMENT '物品名称',
    category VARCHAR(32) NOT NULL COMMENT '类别: potion/scroll/artifact/reagent/weapon/familiar',
    rarity VARCHAR(16) NOT NULL COMMENT '稀有度: Common/Uncommon/Rare/Epic/Legendary',
    origin_realm VARCHAR(64) NOT NULL COMMENT '产地',
    seller VARCHAR(64) NOT NULL COMMENT '卖家',
    stock INT NOT NULL DEFAULT 0 COMMENT '库存数量',
    price_mana DECIMAL(10,0) NOT NULL COMMENT '魔力水晶价格',
    description TEXT COMMENT '物品描述',
    UNIQUE KEY uk_item_seller (item_name, seller)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
"""

sql_prompt = ChatPromptTemplate.from_template(
    """
系统提示：你是一位魔法市集SQL生成器，需要从对话历史中提取用户意图和关键信息，基于 magical_items 表生成SELECT语句。
- 用户可能按物品名称、类别、稀有度、产地、卖家、价格范围等搜索。提取所有可用条件生成WHERE子句。
- 如果用户搜索信息不足（比如只说"有什么好东西"而无任何条件），输出JSON追问格式；信息齐全则输出纯SQL。
- 如果用户问与物品查询无关的问题，模仿最后一个示例回复。

示例：
- 对话: user: 有没有传奇级的artifact
输出: SELECT item_name, category, rarity, origin_realm, seller, stock, price_mana, description FROM magical_items WHERE rarity = 'Legendary' AND category = 'artifact'
- 对话: user: 帮我找凤凰羽笔
输出: SELECT item_name, category, rarity, origin_realm, seller, stock, price_mana, description FROM magical_items WHERE item_name LIKE '%凤凰羽笔%'
- 对话: user: 艾尔德格罗夫产的物品 稀有度Epic以上
输出: SELECT item_name, category, rarity, origin_realm, seller, stock, price_mana, description FROM magical_items WHERE origin_realm = '艾尔德格罗夫' AND rarity IN ('Epic', 'Legendary')

- 对话: user: 有什么好东西
输出: {{"status": "input_required", "message": "客官想找哪类宝贝？可以是类别（potion/scroll/artifact/reagent/weapon/familiar）、稀有度（Common到Legendary）、产地或具体名称。"}}
- 对话: user: 隐形
assistant: 您是找隐形相关的物品吗？请提供更多细节。
user: 对，隐身斗篷
输出: SELECT item_name, category, rarity, origin_realm, seller, stock, price_mana, description FROM magical_items WHERE item_name LIKE '%隐身%'

- 对话: user: 今天吃什么
输出: {{"status": "input_required", "message": "请提供魔法物品相关查询。您可以按类别、稀有度、产地或物品名称搜索。"}}

表结构：{table_schema_string}
对话历史: {conversation}
当前日期: {current_date} (Asia/Shanghai)
"""
)


async def get_items(sql):
    try:
        async with streamablehttp_client("http://127.0.0.1:8001/mcp") as (read, write, _):
            async with ClientSession(read, write) as session:
                await session.initialize()
                result = await session.call_tool("query_items", {"sql": sql})
                result_data = json.loads(result) if isinstance(result, str) else result
                logger.info(f"物品查询结果: {result_data}")
                return result_data.content[0].text
    except Exception as e:
        logger.error(f"物品MCP出错: {str(e)}")
        return {"status": "error", "message": f"物品查询出错: {str(e)}"}


agent_card = AgentCard(
    name="BazaarQueryAssistant",
    description="市集掌柜——帮您搜罗天下奇珍异宝，按类别、稀有度、产地一网打尽。",
    url="http://localhost:5006",
    version="1.0.0",
    capabilities={"streaming": True, "memory": True},
    skills=[
        AgentSkill(
            name="search magical items",
            description="搜索魔法物品市集，支持按类别、稀有度、产地、名称等条件查询",
            examples=[
                "有没有传奇级artifact",
                "帮我找凤凰羽笔",
                "猩红荒原出产的药水",
                "5000水晶以下的武器",
            ],
        )
    ],
)


class BazaarQueryServer(A2AServer):
    def __init__(self):
        super().__init__(agent_card=agent_card)
        self.llm = llm
        self.sql_prompt = sql_prompt
        self.schema = table_schema_string

    def generate_sql_query(self, conversation: str) -> dict:
        try:
            chain = self.sql_prompt | self.llm
            current_date = datetime.now(pytz.timezone("Asia/Shanghai")).strftime("%Y-%m-%d")
            output = chain.invoke({
                "conversation": conversation,
                "current_date": current_date,
                "table_schema_string": self.schema,
            }).content.strip()
            logger.info(f"LLM输出: {output}")
            if output.startswith("{"):
                return json.loads(output)
            return {"status": "sql", "sql": output}
        except Exception as e:
            logger.error(f"SQL生成失败: {str(e)}")
            return {"status": "input_required", "message": "店铺账本出了点问题……请重新描述您要寻找的物品。"}

    def handle_task(self, task):
        content = (task.message or {}).get("content", {})
        conversation = content.get("text", "") if isinstance(content, dict) else ""
        logger.info(f"对话历史: {conversation}")

        try:
            gen_result = self.generate_sql_query(conversation)
            if gen_result["status"] == "input_required":
                task.status = TaskStatus(
                    state=TaskState.INPUT_REQUIRED,
                    message={"role": "agent", "content": {"text": gen_result["message"]}},
                )
                return task

            sql_query = gen_result["sql"]
            logger.info(f"生成的SQL: {sql_query}")

            item_result = asyncio.run(get_items(sql_query))
            response = json.loads(item_result) if isinstance(item_result, str) else item_result

            if response.get("status") == "success":
                data = response.get("data", [])
                response_text = "\n".join([
                    f"【{d['rarity']}】{d['item_name']} ({d['category']}) — {d['price_mana']}水晶 | "
                    f"库存: {d['stock']} | 产地: {d['origin_realm']} | 卖家: {d['seller']}\n"
                    f"  {d.get('description', '')}"
                    for d in data
                ])
                if not response_text:
                    response_text = "翻遍了货架也没找到……试试换个条件？"
                task.artifacts = [{"parts": [{"type": "text", "text": response_text}]}]
                task.status = TaskStatus(state=TaskState.COMPLETED)
            elif response.get("status") == "no_data":
                task.status = TaskStatus(
                    state=TaskState.INPUT_REQUIRED,
                    message={"role": "agent", "content": {"text": response.get("message", "客官，这宝贝小店暂无存货……")}},
                )
            else:
                task.status = TaskStatus(
                    state=TaskState.FAILED,
                    message={"role": "agent", "content": {"text": response.get("message", "查询出了点问题，客官稍等……")}},
                )
            return task
        except Exception as e:
            logger.error(f"查询失败: {str(e)}")
            task.status = TaskStatus(
                state=TaskState.FAILED,
                message={"role": "agent", "content": {"text": f"查询失败: {str(e)}"}},
            )
            return task


if __name__ == "__main__":
    server = BazaarQueryServer()
    print(f"\n=== {server.agent_card.name} ===")
    print(f"描述: {server.agent_card.description}")
    for skill in server.agent_card.skills:
        print(f"  - {skill.name}: {skill.description}")
    run_server(server, host="127.0.0.1", port=5006)
