import asyncio
import uuid

from langchain_openai import ChatOpenAI
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client
from langchain_mcp_adapters.tools import load_mcp_tools
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain_core.prompts import ChatPromptTemplate
from python_a2a import (
    AgentCard, AgentSkill, run_server, TaskStatus, TaskState,
    A2AServer, A2AClient, Message, TextContent, MessageRole, Task,
)

from config import LLM_CONFIG
from create_logger import setup_logger

logger = setup_logger("OrderAgent")

llm = ChatOpenAI(
    model=LLM_CONFIG["model"],
    base_url=LLM_CONFIG["base_url"],
    api_key=LLM_CONFIG["api_key"],
    temperature=LLM_CONFIG["temperature"],
)


async def order_items(query):
    try:
        async with streamablehttp_client("http://127.0.0.1:8003/mcp") as (read, write, _):
            async with ClientSession(read, write) as session:
                await session.initialize()
                tools = await load_mcp_tools(session)

                prompt = ChatPromptTemplate.from_messages([
                    ("system",
                     "你是一位魔法物品订购助手，能够调用工具完成物品购买。"
                     "你需要仔细分析工具需要的参数（item_name物品名称, quantity数量, buyer买家名号），"
                     "从用户提供的信息中提取。如果信息不足，向用户追问。不能编造参数。"),
                    ("human", "{input}"),
                    ("placeholder", "{agent_scratchpad}"),
                ])

                agent = create_tool_calling_agent(llm, tools, prompt)
                agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)
                response = await agent_executor.ainvoke({"input": query})

                return {"status": "success", "message": response["output"]}
    except Exception as e:
        logger.error(f"订购MCP出错: {str(e)}")
        return {"status": "error", "message": f"订购出错: {str(e)}"}


agent_card = AgentCard(
    name="BazaarOrderAssistant",
    description="市集掌柜的账房——处理魔法物品的购买与交易，一手交钱一手交货。",
    url="http://localhost:5007",
    version="1.0.0",
    capabilities={"streaming": True, "memory": True},
    skills=[
        AgentSkill(
            name="order magical items",
            description="根据客户需求完成魔法物品的订购与交易",
            examples=[
                "我要买3支凤凰羽笔，记在大法师甘道夫账上",
                "订购一个隐身斗篷",
                "来两瓶龙息药剂",
            ],
        )
    ],
)


class BazaarOrderServer(A2AServer):
    def __init__(self):
        super().__init__(agent_card=agent_card)
        self.llm = llm
        self.bazaar_client = A2AClient("http://localhost:5006")

    def handle_task(self, task):
        content = (task.message or {}).get("content", {})
        conversation = content.get("text", "") if isinstance(content, dict) else ""
        logger.info(f"对话历史: {conversation}")

        try:
            # Step 1: 查询市集库存
            message_bazaar = Message(content=TextContent(text=conversation), role=MessageRole.USER)
            task_bazaar = Task(id="task-" + str(uuid.uuid4()), message=message_bazaar.to_dict())

            bazaar_result_task = asyncio.run(self.bazaar_client.send_task_async(task_bazaar))
            logger.info(f"市集查询结果: {bazaar_result_task}")

            if bazaar_result_task.status.state != "completed":
                required_message = bazaar_result_task.status.message["content"]["text"]
                logger.info(f"库存未查到: {required_message}")
                task.status = TaskStatus(
                    state=TaskState.INPUT_REQUIRED,
                    message={"role": "agent", "content": {"text": required_message}},
                )
                return task

            bazaar_result = bazaar_result_task.artifacts[0]["parts"][0]["text"]
            logger.info(f"库存信息: {bazaar_result}")

            # Step 2: 执行订购
            order_result = asyncio.run(order_items(conversation + "\n库存信息：" + bazaar_result))
            logger.info(f"订购结果: {order_result}")

            data = order_result.get("message", "")
            if order_result.get("status") == "success":
                result = f"库存确认：\n{bazaar_result}\n\n订购结果：\n{data}"
                task.artifacts = [{"parts": [{"type": "text", "text": result}]}]
                task.status = TaskStatus(state=TaskState.COMPLETED)
            else:
                task.status = TaskStatus(
                    state=TaskState.FAILED,
                    message={"role": "agent", "content": {"text": data}},
                )
            return task
        except Exception as e:
            logger.error(f"订购失败: {str(e)}")
            task.status = TaskStatus(
                state=TaskState.FAILED,
                message={"role": "agent", "content": {"text": f"订购失败: {str(e)}"}},
            )
            return task


if __name__ == "__main__":
    server = BazaarOrderServer()
    print(f"\n=== {server.agent_card.name} ===")
    print(f"描述: {server.agent_card.description}")
    for skill in server.agent_card.skills:
        print(f"  - {skill.name}: {skill.description}")
    run_server(server, host="127.0.0.1", port=5007)
