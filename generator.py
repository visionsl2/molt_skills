# -*- coding: utf-8 -*-
"""
bid_generator/generator.py
===========================
生成器：调用 Minimax 2.7 生成应标方案各章节内容。
单章节生成，基于：模板章节要求 + 检索到的相关段落 + 招标需求。
"""

import logging
import re
import time
from typing import List, Dict, Any, Optional

import requests

from config import logger

# ========== Minimax API 配置 ==========
import os
MINIMAX_API_KEY = os.environ.get("MINIMAX_API_KEY", "")
if not MINIMAX_API_KEY:
    raise ValueError("请先设置环境变量: export MINIMAX_API_KEY='你的API Key'")
MINIMAX_BASE_URL = "https://api.minimaxi.com/v1"
MINIMAX_MODEL = "MiniMax-M2.7"

# ========== 系统提示词 ==========

SYSTEM_PROMPT = """你是一位资深的企业设备/资产管理系统投标方案撰写专家。
你的任务是根据招标需求、模板章节要求及相关历史段落，撰写高质量的应标技术方案。

写作要求：
1. 严格按照模板章节结构输出内容，章节标题与模板保持一致
2. 内容要专业、详实、可落地，结合招标需求进行定制化撰写
3. 适当引用检索到的相关段落（融合改写，不要直接复制）
4. 使用正式书面语，段落充实，避免空洞套话
5. 如果相关段落不足，则基于你的专业知识补充完整内容
6. 输出纯正文内容（不加 Markdown 标记），便于直接写入 Word 文档
"""

# ========== 单章节生成提示词模板 ==========

CHAPTER_PROMPT_TEMPLATE = """## 当前任务

**招标需求摘要：**
{requirement}

---

**模板章节要求：**
{chapter_title}
（模板描述：{chapter_desc}）

---

**相关历史段落（仅供参考，融合改写）：**
{context}

---

## 请撰写该章节的完整内容

严格按照上述"模板章节要求"撰写正文内容。
"""


class BidGenerator:
    """
    标书内容生成器：
      - 基于招标需求 + 相关段落 + 模板章节
      - 调用 Minimax 2.7 生成单章节正文
    """

    def __init__(self, model: str = None, api_key: str = None, base_url: str = None):
        self.model = model or MINIMAX_MODEL
        self.api_key = api_key or MINIMAX_API_KEY
        self.base_url = base_url or MINIMAX_BASE_URL

    def _call_minimax(self, prompt: str, system_prompt: str, max_tokens: int = 800) -> str:
        """调用 Minimax API"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        
        payload = {
            "model": self.model,
            "max_tokens": max_tokens,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ],
        }
        
        response = requests.post(
            f"{self.base_url}/chat/completions",
            headers=headers,
            json=payload,
            timeout=120,
        )
        
        if response.status_code != 200:
            raise Exception(f"API error: {response.status_code} - {response.text}")
        
        result = response.json()
        # 支持 OpenAI 格式
        if "choices" in result:
            content = result["choices"][0]["message"]["content"]
        else:
            raise Exception(f"Unknown response format: {result}")
        
        # 去除思考标签
        content = re.sub(r'<think>.*?</think>', '', content, flags=re.DOTALL)
        return content

    def generate_chapter(
        self,
        chapter_title: str,
        chapter_desc: str,
        requirement: str,
        context_chunks: List[Dict[str, Any]],
        model: str = None,
        max_tokens: int = 800,
    ) -> str:
        """
        生成单个章节内容。

        参数:
          chapter_title: 章节标题（模板中的标题）
          chapter_desc:  章节描述（模板中的子标题或说明）
          requirement:   招标需求全文
          context_chunks: 检索到的相关段落列表
          model:         可覆盖默认模型
          max_tokens:   最大生成长度

        返回:
          生成的正文内容（str）
        """
        model = model or self.model

        # 构造上下文段落
        if context_chunks:
            context_lines = []
            for i, chunk in enumerate(context_chunks, 1):
                source = f"【来源：{chunk['doc_name']} | {chunk['heading_path']}】"
                text = chunk['chunk_text'][:300]  # 截断避免超出上下文
                context_lines.append(f"{i}. {source}\n   {text}")
            context_text = "\n\n".join(context_lines)
        else:
            context_text = "（无相关历史段落，请基于招标需求和你的专业知识撰写完整内容）"

        prompt = CHAPTER_PROMPT_TEMPLATE.format(
            requirement=requirement[:800],
            chapter_title=chapter_title,
            chapter_desc=chapter_desc or "（无详细描述，按标准格式撰写）",
            context=context_text,
        )

        logger.info(f"[Generator] 生成章节: {chapter_title[:40]}（模型: {model}）")

        try:
            content = self._call_minimax(prompt, SYSTEM_PROMPT, max_tokens)
            content = content.strip()
            logger.info(f"[Generator]  生成完成，长度: {len(content)} 字")
            return content
        except Exception as e:
            logger.error(f"[Generator] 生成失败: {e}")
            return f"（生成失败：{e}）"

    def generate_chapters(
        self,
        chapters: List[Dict[str, str]],
        requirement: str,
        context_map: Dict[str, List[Dict[str, Any]]],
        model: str = None,
    ) -> Dict[str, str]:
        """
        批量生成多个章节。

        参数:
          chapters:   章节列表 [{"title": "...", "desc": "..."}, ...]
          requirement: 招标需求全文
          context_map: {章节标题: [检索结果]}，无结果时为空列表
          model:      可覆盖默认模型

        返回:
          {章节标题: 生成内容, ...}
        """
        output = {}
        for i, ch in enumerate(chapters, 1):
            title = ch["title"]
            desc = ch.get("desc", "")
            chunks = context_map.get(title, [])

            logger.info(f"[Generator] [{i}/{len(chapters)}] 正在生成: {title}")
            content = self.generate_chapter(
                chapter_title=title,
                chapter_desc=desc,
                requirement=requirement,
                context_chunks=chunks,
                model=model,
            )
            output[title] = content
            time.sleep(1)  # 避免请求过快
        return output

    @staticmethod
    def check_model_available() -> bool:
        """检查模型是否可用"""
        try:
            headers = {"Authorization": f"Bearer {MINIMAX_API_KEY}"}
            response = requests.post(
                f"{MINIMAX_BASE_URL}/chat/completions",
                headers=headers,
                json={"model": MINIMAX_MODEL, "max_tokens": 10, "messages": [{"role": "user", "content": "hi"}]},
                timeout=30,
            )
            return response.status_code == 200
        except Exception as e:
            logger.warning(f"[Generator] Minimax API 不可用: {e}")
            return False
