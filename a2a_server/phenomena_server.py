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

logger = setup_logger("PhenomenaAgent")

llm = ChatOpenAI(
    model=LLM_CONFIG["model"],
    base_url=LLM_CONFIG["base_url"],
    api_key=LLM_CONFIG["api_key"],
    temperature=LLM_CONFIG["temperature"],
)

table_schema_string = """
CREATE TABLE mystical_phenomena (
    id INT AUTO_INCREMENT PRIMARY KEY,
    realm VARCHAR(64) NOT NULL COMMENT '领域名称',
    fx_date DATE NOT NULL COMMENT '预报日期',
    mana_level DECIMAL(4,1) NOT NULL COMMENT '魔力浓度 (0-10)',
    phenomenon_type VARCHAR(64) NOT NULL COMMENT '异象类型',
    danger_rating TINYINT NOT NULL DEFAULT 1 COMMENT '危险等级 1-5',
    magic_surge_chance DECIMAL(4,1) NOT NULL DEFAULT 0 COMMENT '魔力暴走概率 (%)',
    temp_high INT NOT NULL COMMENT '以太温度高',
    temp_low INT NOT NULL COMMENT '以太温度低',
    description TEXT COMMENT '异象描述',
    UNIQUE KEY uk_realm_date (realm, fx_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
"""

sql_prompt = ChatPromptTemplate.from_template(
    """
系统提示：你是一位异象占卜SQL生成器，需要从对话历史中提取关键信息，基于 mystical_phenomena 表生成SELECT语句。
- 查询异象至少需要"领域"和"日期"信息。如果对话历史中缺乏必要信息，输出JSON追问格式；信息齐全则输出纯SQL。
- 如果用户问与异象无关的问题，模仿最后两个示例回复。

示例：
- 对话: user: 艾尔德格罗夫 2026-07-13
输出: SELECT realm, fx_date, mana_level, phenomenon_type, danger_rating, magic_surge_chance, temp_high, temp_low, description FROM mystical_phenomena WHERE realm = '艾尔德格罗夫' AND fx_date = '2026-07-13'
- 对话: user: 猩红荒原未来3天
输出: SELECT realm, fx_date, mana_level, phenomenon_type, danger_rating, magic_surge_chance, temp_high, temp_low, description FROM mystical_phenomena WHERE realm = '猩红荒原' AND fx_date BETWEEN '2026-07-13' AND '2026-07-15' ORDER BY fx_date

- 对话: user: 艾尔德格罗夫
输出: {{"status": "input_required", "message": "请提供具体的日期，例如 '2026-07-13'。"}}
- 对话: user: 今天
assistant: 请问您想查询哪个领域？
user: 天穹尖塔
输出: SELECT realm, fx_date, mana_level, phenomenon_type, danger_rating, magic_surge_chance, temp_high, temp_low, description FROM mystical_phenomena WHERE realm = '天穹尖塔' AND fx_date = '2026-07-13'

- 对话: user: 你好
输出: {{"status": "input_required", "message": "请提供领域和日期，例如 '艾尔德格罗夫 2026-07-13'。"}}
- 对话: user: 今天吃什么
输出: {{"status": "input_required", "message": "请提供异象相关查询，包括领域和日期。"}}

表结构：{table_schema_string}
对话历史: {conversation}
当前日期: {current_date} (Asia/Shanghai)
"""
)


async def get_phenomena(sql):
    try:
        async with streamablehttp_client("http://127.0.0.1:8002/mcp") as (read, write, _):
            async with ClientSession(read, write) as session:
                await session.initialize()
                result = await session.call_tool("query_phenomena", {"sql": sql})
                result_data = json.loads(result) if isinstance(result, str) else result
                logger.info(f"异象查询结果: {result_data}")
                return result_data.content[0].text
    except Exception as e:
        logger.error(f"异象MCP出错: {str(e)}")
        return {"status": "error", "message": f"异象查询出错: {str(e)}"}


agent_card = AgentCard(
    name="PhenomenaQueryAssistant",
    description="占卜各领域的魔力异象——魔力浓度、异象类型、危险等级，一探便知。",
    url="http://localhost:5005",
    version="1.0.0",
    capabilities={"streaming": True, "memory": True},
    skills=[
        AgentSkill(
            name="scry phenomena",
            description="查询各领域的魔力异象预报，支持自然语言输入",
            examples=[
                "艾尔德格罗夫今天的魔力浓度",
                "猩红荒原未来3天有魔力风暴吗",
                "天穹尖塔的星辰排列",
            ],
        )
    ],
)


class PhenomenaQueryServer(A2AServer):
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
            return {"status": "input_required", "message": "水晶球感应模糊……请提供领域和日期。"}

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

            phenomena_result = asyncio.run(get_phenomena(sql_query))
            response = json.loads(phenomena_result) if isinstance(phenomena_result, str) else phenomena_result

            if response.get("status") == "success":
                data = response.get("data", [])
                response_text = "\n".join([
                    f"{d['realm']} {d['fx_date']}: {d['phenomenon_type']}，魔力浓度 {d['mana_level']}，"
                    f"危险等级 {d['danger_rating']}/5，魔力暴走概率 {d['magic_surge_chance']}%，"
                    f"气温 {d['temp_low']}-{d['temp_high']}° — {d.get('description', '')}"
                    for d in data
                ])
                task.artifacts = [{"parts": [{"type": "text", "text": response_text}]}]
                task.status = TaskStatus(state=TaskState.COMPLETED)
            elif response.get("status") == "no_data":
                task.status = TaskStatus(
                    state=TaskState.INPUT_REQUIRED,
                    message={"role": "agent", "content": {"text": response.get("message", "")}},
                )
            else:
                task.status = TaskStatus(
                    state=TaskState.FAILED,
                    message={"role": "agent", "content": {"text": response.get("message", "查询失败。")}},
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
    server = PhenomenaQueryServer()
    print(f"\n=== {server.agent_card.name} ===")
    print(f"描述: {server.agent_card.description}")
    for skill in server.agent_card.skills:
        print(f"  - {skill.name}: {skill.description}")
    run_server(server, host="127.0.0.1", port=5005)
