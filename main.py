import asyncio
import json
import uuid
from datetime import datetime
import pytz
import re
from python_a2a import AgentNetwork, TextContent, Message, MessageRole, Task
from langchain_openai import ChatOpenAI

from config import LLM_CONFIG, AGENT_CONFIG
from create_logger import setup_logger
from main_prompts import ArcaneBazaarPrompts

logger = setup_logger("ArcaneBazaarCLI")

messages = []
agent_network = None
llm = None
agent_urls = {}
conversation_history = ""


def initialize_system():
    global agent_network, llm, agent_urls, conversation_history

    agent_urls = {cfg["name"]: cfg["url"] for cfg in AGENT_CONFIG.values()}

    network = AgentNetwork(name="Arcane Bazaar Network")
    for cfg in AGENT_CONFIG.values():
        network.add(cfg["name"], cfg["url"])
    agent_network = network

    llm = ChatOpenAI(
        model=LLM_CONFIG["model"],
        api_key=LLM_CONFIG["api_key"],
        base_url=LLM_CONFIG["base_url"],
        temperature=LLM_CONFIG["temperature"],
    )

    conversation_history = ""


def intent_agent(user_input):
    global conversation_history, llm

    chain = ArcaneBazaarPrompts.intent_prompt() | llm
    current_date = datetime.now(pytz.timezone("Asia/Shanghai")).strftime("%Y-%m-%d")
    intent_response = chain.invoke({
        "conversation_history": "\n".join(conversation_history.split("\n")[-6:]),
        "query": user_input,
        "current_date": current_date,
    }).content.strip()
    logger.info(f"意图识别: {intent_response}")

    intent_response = re.sub(r"^```json\s*|\s*```$", "", intent_response).strip()
    intent_output = json.loads(intent_response)
    intents = intent_output.get("intents", [])
    user_queries = intent_output.get("user_queries", {})
    follow_up_message = intent_output.get("follow_up_message", "")
    return intents, user_queries, follow_up_message


def process_user_input(prompt):
    global messages, conversation_history, llm

    messages.append({"role": "user", "content": prompt})
    conversation_history += f"\nUser: {prompt}"

    print("\n🔮 占卜中……")
    try:
        intents, user_queries, follow_up_message = intent_agent(prompt)

        if "out_of_scope" in intents:
            response = follow_up_message
            conversation_history += f"\nAssistant: {response}"
        elif follow_up_message != "":
            response = follow_up_message
            conversation_history += f"\nAssistant: {response}"
        else:
            responses = []
            routed_agents = []

            intent_to_agent_name = {
                "phenomena": AGENT_CONFIG["phenomena"]["name"],
                "item": AGENT_CONFIG["bazaar"]["name"],
                "order": AGENT_CONFIG["order"]["name"],
            }

            for intent in intents:
                logger.info(f"处理意图: {intent}")
                agent_name = intent_to_agent_name.get(intent)

                if intent == "lore":
                    chain = ArcaneBazaarPrompts.lore_prompt() | llm
                    lore_response = chain.invoke({"query": prompt}).content.strip()
                    responses.append(lore_response)
                elif agent_name:
                    query_str = user_queries.get(intent, {})
                    logger.info(f"{agent_name} 查询: {query_str}")

                    agent = agent_network.get_agent(agent_name)
                    chat_history = (
                        "\n".join(conversation_history.split("\n")[-7:-1])
                        + f"\nUser: {query_str}"
                    )
                    message = Message(content=TextContent(text=chat_history), role=MessageRole.USER)
                    task = Task(id="task-" + str(uuid.uuid4()), message=message.to_dict())
                    raw_response = asyncio.run(agent.send_task_async(task))

                    if raw_response.status.state == "completed":
                        agent_result = raw_response.artifacts[0]["parts"][0]["text"]
                    else:
                        agent_result = raw_response.status.message["content"]["text"]

                    if agent_name == AGENT_CONFIG["phenomena"]["name"]:
                        chain = ArcaneBazaarPrompts.summarize_phenomena_prompt() | llm
                        final_response = chain.invoke({
                            "query": query_str,
                            "raw_response": agent_result,
                        }).content.strip()
                    elif agent_name == AGENT_CONFIG["bazaar"]["name"]:
                        chain = ArcaneBazaarPrompts.summarize_item_prompt() | llm
                        final_response = chain.invoke({
                            "query": query_str,
                            "raw_response": agent_result,
                        }).content.strip()
                    else:
                        final_response = agent_result

                    responses.append(final_response)
                    routed_agents.append(agent_name)
                else:
                    responses.append("这个请求超出了市集的范围……")

            response = "\n\n".join(responses)
            if routed_agents:
                logger.info(f"路由到: {routed_agents}")
            conversation_history += f"\nAssistant: {response}"

        print(f"\n📜 守护灵的回复:\n{response}\n")
        messages.append({"role": "assistant", "content": response})

    except json.JSONDecodeError as e:
        logger.error(f"JSON解析失败: {e}")
        error_message = f"水晶球出现了裂痕……意图解析失败: {str(e)}。请重试。"
        print(f"\n❌ {error_message}\n")
        messages.append({"role": "assistant", "content": error_message})
    except Exception as e:
        logger.error(f"处理异常: {str(e)}")
        error_message = f"魔力波动干扰了传输……处理失败: {str(e)}。请重试。"
        print(f"\n❌ {error_message}\n")
        messages.append({"role": "assistant", "content": error_message})


def display_agent_cards():
    print("\n🛠️ 守护灵契约:")
    icons = {
        AGENT_CONFIG["phenomena"]["name"]: "🌋",
        AGENT_CONFIG["bazaar"]["name"]: "📜",
        AGENT_CONFIG["order"]["name"]: "⚖️",
    }
    for agent_name in agent_network.agents.keys():
        agent_card = agent_network.get_agent_card(agent_name)
        agent_url = agent_urls.get(agent_name, "未知")
        icon = icons.get(agent_name, "✨")
        print(f"  {icon} {agent_name}")
        print(f"     技能: {agent_card.skills}")
        print(f"     描述: {agent_card.description}")
        print(f"     地址: {agent_url}")
        print(f"     状态: 🟢 共鸣中")


if __name__ == "__main__":
    initialize_system()
    print("=" * 60)
    print("🔮  ArcaneBazaar — 奥秘市集")
    print("    \"Where mana meets marketplace\"")
    print("=" * 60)
    print("输入 'quit' 离开市集 | 输入 'cards' 查看守护灵契约")
    print()

    display_agent_cards()

    while True:
        prompt = input("\n💬 说出你的愿望，旅人: ").strip()
        if prompt.lower() == "quit":
            print("\n🌟 愿魔力与你同在。欢迎再次光临奥秘市集！")
            break
        elif prompt.lower() == "cards":
            display_agent_cards()
            continue
        elif not prompt:
            continue
        else:
            process_user_input(prompt)
