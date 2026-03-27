# -*- coding: utf-8 -*-
"""
bid_generator/config.py
=======================
全局配置：路径、Ollama 模型、日志等
"""

import os
from pathlib import Path

# ========== 路径配置 ==========
WORKSPACE       = Path("/Users/visionsl/.openclaw/workspace")
KB_DIR          = WORKSPACE / "bid_generator" / "data"
TEMPLATE_PATH   = WORKSPACE / "应标方案模板.md"
TEMPLATE_OUT_DIR= WORKSPACE / "bid_generator" / "templates"

# 历史标书方案目录
BID_DOCS_DIR    = Path("/Users/visionsl/Documents/资料/标书方案")

# 确保目录存在
KB_DIR.mkdir(parents=True, exist_ok=True)
TEMPLATE_OUT_DIR.mkdir(parents=True, exist_ok=True)

# ========== 向量模型配置（Ollama，本地） ==========
EMBED_MODEL     = "nomic-embed-text"   # 向量化模型
OLLAMA_BASE_URL = "http://localhost:11434"

# ========== 生成模型配置（Minimax 2.7，在线） ==========
# API Key 从环境变量读取，禁止硬编码！
import os
MINIMAX_API_KEY = os.environ.get("MINIMAX_API_KEY", "")
if not MINIMAX_API_KEY:
    raise ValueError("请设置环境变量 MINIMAX_API_KEY")

MINIMAX_BASE_URL = "https://api.minimaxi.com/v1/chat/completions"
GENERATE_MODEL  = "MiniMax-M2.7"       # 生成模型

# ========== LanceDB 配置 ==========
DB_NAME         = "bid_knowledge"       # LanceDB 数据库名

# ========== 检索配置 ==========
TOP_K           = 5                      # 默认返回 top-K 相关段落
SIMILARITY_THRESHOLD = 0.3              # 最低相似度阈值

# ========== 日志配置 ==========
import logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("bid_generator")
