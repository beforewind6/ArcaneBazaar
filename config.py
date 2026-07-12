"""
ArcaneBazaar — Multi-Agent Magical Marketplace
Configuration
"""
import os

LLM_CONFIG = {
    "base_url": "https://api.siliconflow.cn/v1",
    "api_key": os.getenv("SILICONFLOW_API_KEY", "sk-your-key-here"),
    "model": "Qwen/Qwen2.5-72B-Instruct",
    "temperature": 0.1,
}

DB_CONFIG = {
    "host": os.getenv("MYSQL_HOST", "localhost"),
    "port": int(os.getenv("MYSQL_PORT", 3306)),
    "user": os.getenv("MYSQL_USER", "root"),
    "password": os.getenv("MYSQL_PASSWORD", ""),
    "database": "arcane_bazaar",
}

AGENT_CONFIG = {
    "phenomena": {
        "name": "PhenomenaQueryAssistant",
        "port": 5005,
        "url": "http://localhost:5005",
        "description": "Scry mystical phenomena across realms",
    },
    "bazaar": {
        "name": "BazaarQueryAssistant",
        "port": 5006,
        "url": "http://localhost:5006",
        "description": "Search the grand bazaar for magical items",
    },
    "order": {
        "name": "BazaarOrderAssistant",
        "port": 5007,
        "url": "http://localhost:5007",
        "description": "Handle purchases and barter agreements",
    },
}

MCP_CONFIG = {
    "phenomena": {"port": 8002, "url": "http://localhost:8002"},
    "bazaar": {"port": 8001, "url": "http://localhost:8001"},
    "order": {"port": 8003, "url": "http://localhost:8003"},
}

INTENT_AGENT_MAP = {
    "phenomena": AGENT_CONFIG["phenomena"],
    "item": AGENT_CONFIG["bazaar"],
    "order": AGENT_CONFIG["order"],
    "lore": None,
    "out_of_scope": None,
}
