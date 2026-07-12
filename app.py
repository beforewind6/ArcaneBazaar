import asyncio
import uuid
import streamlit as st
from python_a2a import AgentNetwork, Message, TextContent, MessageRole, Task
from langchain_openai import ChatOpenAI
import json
from datetime import datetime
import pytz
import re

from config import LLM_CONFIG, AGENT_CONFIG, INTENT_AGENT_MAP
from create_logger import setup_logger
from main_prompts import ArcaneBazaarPrompts

logger = setup_logger("ArcaneBazaar")

st.set_page_config(
    page_title="ArcaneBazaar — 奥秘市集",
    layout="wide",
    page_icon="🔮",
)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=MedievaSharp&display=swap');

    .stApp {
        background: linear-gradient(135deg, #0a0a1a 0%, #1a0a2e 50%, #0a0f1a 100%);
    }

    .stChatMessage {
        background-color: rgba(30, 20, 50, 0.85) !important;
        border: 1px solid rgba(180, 140, 255, 0.2) !important;
        border-radius: 12px !important;
        padding: 15px !important;
        margin-bottom: 15px !important;
        box-shadow: 0 0 20px rgba(120, 60, 220, 0.1) !important;
    }

    .stChatMessage.user {
        background-color: rgba(40, 30, 60, 0.85) !important;
        border-color: rgba(200, 160, 255, 0.3) !important;
    }

    .stChatMessage * {
        color: #e8d5ff !important;
    }

    h1, h2, h3, .stMarkdown h1, .stMarkdown h2, .stMarkdown h3 {
        color: #c9a0ff !important;
        text-shadow: 0 0 10px rgba(150, 80, 255, 0.4);
    }

    .stButton button {
        background: linear-gradient(135deg, #5a2d82, #7b4fc0) !important;
        color: #e8d5ff !important;
        border: 1px solid rgba(180, 140, 255, 0.4) !important;
        border-radius: 8px !important;
    }

    .stExpander {
        background: rgba(20, 10, 40, 0.6) !important;
        border: 1px solid rgba(150, 100, 255, 0.3) !important;
        border-radius: 10px !important;
    }

    .footer {
        text-align: center;
        color: #6a5a8a;
        font-size: 0.85em;
        padding: 20px 0;
    }

    .footer span {
        color: #9a7ac0;
    }
</style>
""", unsafe_allow_html=True)

if "messages" not in st.session_state:
    st.session_state.messages = []
if "agent_network" not in st.session_state:
    st.session_state.agent_urls = {
        cfg["name"]: cfg["url"] for cfg in AGENT_CONFIG.values()
    }
    network = AgentNetwork(name="Arcane Bazaar Network")
    for cfg in AGENT_CONFIG.values():
        network.add(cfg["name"], cfg["url"])
    st.session_state.agent_network = network
    st.session_state.llm = ChatOpenAI(
        model=LLM_CONFIG["model"],
        api_key=LLM_CONFIG["api_key"],
        base_url=LLM_CONFIG["base_url"],
        temperature=LLM_CONFIG["temperature"],
    )
    st.session_state.conversation_history = ""


def intent_agent(user_input):
    chain = ArcaneBazaarPrompts.intent_prompt() | st.session_state.llm
    current_date = datetime.now(pytz.timezone("Asia/Shanghai")).strftime("%Y-%m-%d")
    intent_response = chain.invoke({
        "conversation_history": "\n".join(st.session_state.conversation_history.split("\n")[-6:]),
        "query": user_input,
        "current_date": current_date,
    }).content.strip()
    logger.info(f"意图识别原始响应: {intent_response}")

    intent_response = re.sub(r"^```json\s*|\s*```$", "", intent_response).strip()
    intent_output = json.loads(intent_response)
    intents = intent_output.get("intents", [])
    user_queries = intent_output.get("user_queries", {})
    follow_up_message = intent_output.get("follow_up_message", "")
    logger.info(f"intents: {intents} | queries: {user_queries} | follow_up: {follow_up_message}")
    return intents, user_queries, follow_up_message


# --- Layout ---
st.title("🔮 ArcaneBazaar — 奥秘市集")
st.markdown("*\"Where mana meets marketplace — 魔力交汇的市集\"*")

col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("💬 对话")

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("说出你的愿望，旅人……"):
        with st.chat_message("user"):
            st.markdown(prompt)
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.session_state.conversation_history += f"\nUser: {prompt}"

        llm = st.session_state.llm
        current_date = datetime.now(pytz.timezone("Asia/Shanghai")).strftime("%Y-%m-%d")

        with st.spinner("正在用水晶球占卜您的意图……"):
            try:
                intents, user_queries, follow_up_message = intent_agent(prompt)

                if "out_of_scope" in intents:
                    response = follow_up_message
                    st.session_state.conversation_history += f"\nAssistant: {response}"
                elif follow_up_message != "":
                    response = follow_up_message
                    st.session_state.conversation_history += f"\nAssistant: {response}"
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

                            agent = st.session_state.agent_network.get_agent(agent_name)
                            chat_history = (
                                "\n".join(st.session_state.conversation_history.split("\n")[-7:-1])
                                + f"\nUser: {query_str}"
                            )
                            message = Message(
                                content=TextContent(text=chat_history),
                                role=MessageRole.USER,
                            )
                            task = Task(
                                id="task-" + str(uuid.uuid4()),
                                message=message.to_dict(),
                            )
                            raw_response = asyncio.run(agent.send_task_async(task))
                            logger.info(f"{agent_name} 原始响应: {raw_response}")

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
                        logger.info(f"路由到代理: {routed_agents}")
                    st.session_state.conversation_history += f"\nAssistant: {response}"

                with st.chat_message("assistant"):
                    st.markdown(response)
                st.session_state.messages.append({"role": "assistant", "content": response})

            except json.JSONDecodeError as json_err:
                logger.error(f"意图识别JSON解析失败: {json_err}")
                error_message = f"水晶球出现了裂痕……意图解析失败：{str(json_err)}。请重试。"
                with st.chat_message("assistant"):
                    st.markdown(error_message)
                st.session_state.messages.append({"role": "assistant", "content": error_message})
            except Exception as e:
                logger.error(f"处理异常: {str(e)}")
                error_message = f"魔力波动干扰了传输……处理失败：{str(e)}。请重试。"
                with st.chat_message("assistant"):
                    st.markdown(error_message)
                st.session_state.messages.append({"role": "assistant", "content": error_message})

with col2:
    st.subheader("🛠️ 守护灵")

    agent_icons = {
        AGENT_CONFIG["phenomena"]["name"]: "🌋",
        AGENT_CONFIG["bazaar"]["name"]: "📜",
        AGENT_CONFIG["order"]["name"]: "⚖️",
    }

    agent_themes = {
        AGENT_CONFIG["phenomena"]["name"]: "异象占卜师",
        AGENT_CONFIG["bazaar"]["name"]: "市集掌柜",
        AGENT_CONFIG["order"]["name"]: "账房总管",
    }

    for agent_name in st.session_state.agent_network.agents.keys():
        agent_card = st.session_state.agent_network.get_agent_card(agent_name)
        agent_url = st.session_state.agent_urls.get(agent_name, "未知")
        icon = agent_icons.get(agent_name, "✨")
        theme = agent_themes.get(agent_name, "守护灵")

        with st.expander(f"{icon} {theme} — {agent_name}", expanded=False):
            st.markdown(f"**技能:** {agent_card.skills}")
            st.markdown(f"**描述:** {agent_card.description}")
            st.markdown(f"**契约地址:** `{agent_url}`")
            st.markdown(f"**状态:** 🟢 共鸣中")

st.markdown("---")
st.markdown(
    '<div class="footer">'
    '🔮 <span>ArcaneBazaar v1.0</span> — Built with '
    '<span>A2A Protocol</span> + <span>MCP</span> + <span>LangChain</span> — '
    '"May your mana never run dry."'
    '</div>',
    unsafe_allow_html=True,
)
