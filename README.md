# 🔮 ArcaneBazaar — 奥秘市集

> *"Where mana meets marketplace."*
>
> 魔力交汇的市集，由 AI 守护灵代为经营的奇幻交易所。

---

## 🧙 这是什么魔法？

**ArcaneBazaar** 是一个基于 Google **A2A (Agent-to-Agent)** 协议的多智能体魔法市集系统。你只需要用自然语言说出你的愿望——查询今日异象、搜罗传奇宝物、下达购买指令——三位 AI 守护灵便会通力协作，为你完成一切。

告别在货架间翻找卷轴的日子。让 AI 替你跑腿。

```
你: "猩红荒原今天有魔力风暴吗？顺便帮我看看有没有龙息药剂卖。"

🔮 系统:
  → PhenomenaQueryAssistant 占卜异象...
  → BazaarQueryAssistant 搜索市集...
  → 两位守护灵各自回复，汇总呈现
```

---

## 🏗️ 奥秘市集的建筑蓝图

```
                   🔮 旅人 (你)
                        │
                   ┌────▼────┐
                   │ 奥秘市集  │  Streamlit / CLI
                   │  门  厅   │  意图识别 → 路由
                   └─┬──┬──┬─┘
                     │  │  │
          ┌──────────┘  │  └──────────┐
          │             │             │
    ┌─────▼─────┐ ┌────▼────┐ ┌─────▼─────┐
    │ 🌋 异象   │ │ 📜 市集 │ │ ⚖️ 账房   │
    │ 占卜师    │ │ 掌  柜   │ │ 总  管    │
    │ :5005     │ │ :5006    │ │ :5007     │
    └─────┬─────┘ └────┬────┘ └─────┬─────┘
          │             │             │
    ┌─────▼─────┐ ┌────▼────┐ ┌─────▼─────┐
    │ MCP 异象  │ │ MCP 市集│ │ MCP 订购  │
    │ 工  具    │ │ 工  具   │ │ 工  具    │
    │ :8002     │ │ :8001    │ │ :8003     │
    └─────┬─────┘ └────┬────┘ └─────┬─────┘
          │             │             │
          └─────────────┼─────────────┘
                        │
                  ┌─────▼─────┐
                  │   📚      │
                  │  MySQL    │
                  │ arcane_   │
                  │ bazaar    │
                  └───────────┘
```

三层架构：**UI → A2A 守护灵 → MCP 工具 → 数据库**

LLM 负责：意图理解、SQL 生成、结果润色。守护灵们只负责调度和执行。

---

## 🎭 三位守护灵

| 守护灵 | 契约端口 | 职责 | 口头禅 |
|---|---|---|---|
| 🌋 **PhenomenaQueryAssistant** | `:5005` | 占卜各领域魔力异象 | *"水晶球显示……"* |
| 📜 **BazaarQueryAssistant** | `:5006` | 搜索市集中的魔法物品 | *"瞧一瞧看一看！"* |
| ⚖️ **BazaarOrderAssistant** | `:5007` | 处理购买与交易 | *"一手交钱一手交货！"* |

每个守护灵都配备了自己的 **MCP 工具**（`:8001` / `:8002` / `:8003`），通过 MySQL 直接查询或操作数据。

---

## 🧪 炼金配方 (技术栈)

| 材料 | 用途 |
|---|---|
| **Python 3.12+** | 熬煮一切的坩埚 |
| **Streamlit** | 水晶球投影 (Web UI) |
| **A2A Protocol** (`python-a2a`) | 守护灵之间的心灵感应 |
| **MCP Protocol** (`mcp`) | 法术符文 (工具调用协议) |
| **LangChain** | 咒语组件 (LLM 编排) |
| **Qwen 2.5 72B** | 大贤者之脑 (LLM, via SiliconFlow) |
| **MySQL** | 大图书馆 (数据存储) |
| **FastAPI / Uvicorn** | 守护灵的契约通道 |

---

## 📖 奥秘大典 (数据库)

### `mystical_phenomena` — 异象预报

七大领域、每日更新的魔力观测数据：

| 领域 | 今日异象 | 危险等级 |
|---|---|---|
| 🌳 艾尔德格罗夫 | 仙子灯群舞 | 🟢 1/5 |
| ⛰️ 铁炉山脉 | 矿脉闪烁 | 🟡 2/5 |
| 🏜️ 猩红荒原 | 沙尘暴 | 🟠 4/5 |
| 🏝️ 破碎群岛 | 潮汐涌动 | 🟡 2/5 |
| 🗼 天穹尖塔 | 星辰排列 | 🟢 1/5 |
| 💎 水晶洞窟 | 水晶共鸣 | 🟡 2/5 |
| 🌌 虚空边境 | 边界稳定 | 🟢 1/5 |

### `magical_items` — 市集货架

20 件魔法物品，从 100 水晶的魔力原石到 200,000 水晶的时间沙漏，涵盖六大类别：artifact（神器）、potion（药剂）、scroll（卷轴）、reagent（材料）、weapon（武器）、familiar（宠物）。

---

## 🚀 开业指南

### 0. 前置要求

- Python 3.12+
- MySQL 8.0+
- SiliconFlow API Key（或兼容 OpenAI 接口的任意 LLM 服务）

### 1. 克隆 & 安装

```bash
cd ArcaneBazaar
pip install -r requirements.txt
```

### 2. 初始化数据库

```bash
mysql -u root -p < sql/schema.sql
mysql -u root -p < sql/sample_data.sql
```

### 3. 配置 API Key

```bash
$env:SILICONFLOW_API_KEY = "sk-your-key-here"
```

或在 `config.py` 中直接修改默认值。

### 4. 召唤守护灵

打开 **四个终端窗口**，依次执行：

```bash
# 终端 1 — 启动 MCP 工具服务器
python mcp_server/mcp_phenomena_server.py   # 异象工具  :8002
python mcp_server/mcp_bazaar_server.py      # 市集工具  :8001
python mcp_server/mcp_order_server.py       # 订购工具  :8003

# 终端 2 — 启动 A2A 守护灵
python a2a_server/phenomena_server.py       # 异象占卜师 :5005
python a2a_server/bazaar_server.py          # 市集掌柜   :5006
python a2a_server/order_server.py           # 账房总管   :5007

# 终端 3 — 启动 Web 界面
streamlit run app.py

# 终端 4 (可选) — CLI 模式
python main.py
```

> 提示：MCP 和 A2A 服务器各需要独立进程。可以使用 `start` (Windows) 或 `&` (Linux) 在后台运行。

### 5. 开始对话

浏览器访问 `http://localhost:8501`，试试这些咒语：

- *"天穹尖塔今天有流星雨吗？"*
- *"帮我找传奇级的 artifact"*
- *"有没有5000水晶以下的武器？"*
- *"我要买一支凤凰羽笔"*
- *"给我讲讲虚空边境的故事"*

---

## 🗺️ 对话示例

```
💬 旅人: 猩红荒原未来3天有什么危险异象吗？

📜 守护灵:
  根据魔力之眼的观测，猩红荒原未来三日异象如下——
  7/13: 沙尘暴（普通。很沙。很多。）
  7/14: 魔力风暴！危险等级 5/5，魔力暴走概率 90%
        ——上次有人被传送到巨魔的浴缸里。强烈建议居家。
  7/15: 血月残影，危险等级 3/5，概率 45%
        ——老佣兵说这是吉兆，但上次他这么说的时候遇到了三条龙。

💬 旅人: 有龙息药剂吗？来两瓶。

📜 守护灵:
  【Epic】龙息药剂 (potion) — 8,000水晶 | 库存: 15 | 猩红荒原
    服用后获得喷火能力10分钟。副作用：自燃、黄金渴望、筑巢冲动。
  库存确认：15瓶在库。

  订购结果：恭喜！「龙息药剂」x2 已购入！狮鹫快递正在路上（可能索要零食）。
```

---

## 🧭 项目结构

```
ArcaneBazaar/
├── app.py                  # Streamlit Web 界面
├── main.py                 # CLI 命令行界面
├── main_prompts.py         # 所有 LLM 提示词模板
├── config.py               # 配置中心
├── create_logger.py        # 日志工具
├── requirements.txt        # Python 依赖
│
├── a2a_server/             # A2A 协议守护灵
│   ├── phenomena_server.py # 异象占卜师
│   ├── bazaar_server.py    # 市集掌柜
│   └── order_server.py     # 账房总管
│
├── mcp_server/             # MCP 协议工具
│   ├── mcp_phenomena_server.py
│   ├── mcp_bazaar_server.py
│   └── mcp_order_server.py
│
├── query_data/             # 数据库查询服务
│   └── query1.py
│
├── sql/                    # SQL Schema & 数据
│   ├── schema.sql
│   └── sample_data.sql
│
├── utils/                  # 工具函数
│   └── format.py
│
└── test/                   # 测试脚本
    ├── test_phenomena_mcp_server.py
    └── test_bazaar_agent_server.py
```

---

## ⚠️ 免责声明

本系统为技术演示项目。所有魔法物品均为虚构，不提供真实龙息药剂、传送卷轴或凤凰羽笔的购买服务。如您在现实世界成功施法，请联系最近的魔法学院。

---

*Built with A2A Protocol + MCP + LangChain + a pinch of pixie dust.*

*"May your mana never run dry."* 🔮
