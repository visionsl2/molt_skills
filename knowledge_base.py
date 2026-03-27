# -*- coding: utf-8 -*-
"""
bid_generator/knowledge_base.py
================================
知识库：读取历史标书 → 按 H1/H2/H3 切片 → 向量化 → 存入 LanceDB
支持增量更新（根据文档路径判断是否已处理）
"""

import hashlib
import logging
import re
from pathlib import Path
from typing import List, Dict, Any, Optional

import lancedb
from lancedb.embeddings import EmbeddingFunctionRegistry, EmbeddingFunctionConfig
from lancedb.pydantic import LanceModel, Vector

from config import (
    BID_DOCS_DIR, KB_DIR, DB_NAME,
    EMBED_MODEL, OLLAMA_BASE_URL, logger
)

# ========== LanceDB Schema ==========

class ChunkRecord(LanceModel):
    """单个切片记录"""
    chunk_id: str          # 唯一 ID（MD5）
    doc_path: str          # 来源文档路径
    doc_name: str          # 来源文档名（不含路径）
    heading_path: str      # 标题路径，如 "第一章 > 1.1 > 1.1.1"
    heading_level: int     # 标题级别（1/2/3）
    chunk_text: str        # 切片正文内容
    vector: Vector(dim=768)  # 向量（自动由 LanceDB + Ollama 填充）

# ========== 初始化 Embedding Function（使用 LanceDB 内置 Ollama 集成）==========

def _get_embed_fn():
    """获取 Ollama embedding 函数（从 LanceDB 注册表）"""
    registry = EmbeddingFunctionRegistry.get_instance()
    cls = registry.get("ollama")  # LanceDB 内置 ollama 集成
    return cls.create(
        name=EMBED_MODEL,
        host=OLLAMA_BASE_URL,
    )


# ========== KnowledgeBase 主类 ==========

class BidKnowledgeBase:
    """
    标书知识库：
      - 读取历史 docx 标书，按标题切片
      - 向量化后存入 LanceDB
      - 支持增量更新（对比已有 chunk_id）
    """

    def __init__(self, db_path: str = None):
        self.db_path = db_path or str(KB_DIR / DB_NAME)
        self.embed_fn = _get_embed_fn()
        self._db: Optional[lancedb.LanceDBConnection] = None
        self._table = None

    @property
    def db(self) -> lancedb.LanceDBConnection:
        if self._db is None:
            self._db = lancedb.connect(self.db_path)
        return self._db

    @property
    def table(self):
        if self._table is None:
            table_names = self.db.table_names()
            if DB_NAME in table_names:
                self._table = self.db.open_table(DB_NAME)
            else:
                # 首次创建，带 schema 和 embedding function
                self._table = self.db.create_table(
                    DB_NAME,
                    schema=ChunkRecord,
                    embedding_functions=[
                        EmbeddingFunctionConfig(
                            vector_column="vector",
                            source_column="chunk_text",
                            function=self.embed_fn,
                        )
                    ],
                )
                logger.info(f"创建新表: {DB_NAME}")
        return self._table

    # ------------------------------------------------------------------
    # 文档读取与切片
    # ------------------------------------------------------------------

    @staticmethod
    def _read_docx(path: Path) -> List[Dict[str, Any]]:
        """用 python-docx 读取 docx，返回段落列表（含标题/正文信息）"""
        from docx import Document

        doc = Document(str(path))
        paragraphs = []
        for para in doc.paragraphs:
            paragraphs.append({
                "text": para.text.strip(),
                "style": para.style.name if para.style else "",
            })
        return paragraphs

    @staticmethod
    def _is_heading(para: Dict[str, Any]) -> bool:
        """判断段落是否为标题（H1-H3）"""
        style = para["style"]
        text = para["text"]
        if not text:
            return False
        heading_keywords = ["标题", "Heading", "heading"]
        is_heading = any(k in style for k in heading_keywords)
        if not is_heading and len(text) < 80:
            pattern = r"^(第[一二三四五六七八九十\d]+章|[一二三四五六七八九十\d]+\.[\d]+|[①②③④⑤])"
            is_heading = bool(re.match(pattern, text))
        return is_heading

    @staticmethod
    def _heading_level(text: str) -> int:
        """估算标题级别"""
        if re.match(r"^第[一二三四五六七八九十]+章", text):
            return 1
        if re.match(r"^[一二三四五六七八九十\d]+\.[\d]+", text):
            return 2
        if re.match(r"^[①②③④⑤]", text):
            return 3
        return 3

    def _build_chunks(self, doc_path: Path) -> List[Dict[str, Any]]:
        """将一个 docx 切片为多个 chunk"""
        paragraphs = self._read_docx(doc_path)
        chunks = []
        current_h1 = ""
        current_h2 = ""
        current_h3 = ""
        current_texts: List[str] = []

        def flush():
            if current_texts:
                text = "\n".join(current_texts).strip()
                if text:
                    heading_path = " > ".join(filter(None, [current_h1, current_h2, current_h3]))
                    chunk_id = hashlib.md5(
                        f"{doc_path}:{heading_path}:{text[:50]}".encode()
                    ).hexdigest()
                    # Truncate aggressively to stay within nomic-embed-text context window
                    if len(text) > 1000:
                        text = text[:1000]
                    chunks.append({
                        "chunk_id":    chunk_id,
                        "doc_path":    str(doc_path),
                        "doc_name":    doc_path.name,
                        "heading_path": heading_path,
                        "heading_level": self._heading_level(current_h3 or current_h2 or current_h1),
                        "chunk_text":  text,
                    })
                current_texts.clear()

        for para in paragraphs:
            text = para["text"]
            if not text:
                continue
            if self._is_heading(para):
                flush()
                level = self._heading_level(text)
                if level == 1:
                    current_h1 = text
                    current_h2 = ""
                    current_h3 = ""
                elif level == 2:
                    current_h2 = text
                    current_h3 = ""
                else:
                    current_h3 = text
            else:
                current_texts.append(text)

        flush()
        logger.info(f"  切片完成，共 {len(chunks)} 个 chunk（文档：{doc_path.name}）")
        return chunks

    # ------------------------------------------------------------------
    # 向量检索 / 增量更新
    # ------------------------------------------------------------------

    def index_doc(self, doc_path: Path, force: bool = False) -> int:
        """
        对单个文档进行切片+向量化+存储。
        增量：已存在的 chunk_id 会被跳过。
        返回实际新增的 chunk 数。
        """
        chunks = self._build_chunks(doc_path)
        if not chunks:
            return 0

        existing_ids = set()
        try:
            existing = self.table.to_pandas()
            if not existing.empty:
                existing_ids = set(existing["chunk_id"].tolist())
        except Exception:
            pass

        new_chunks = [c for c in chunks if c["chunk_id"] not in existing_ids]
        if not new_chunks:
            logger.info(f"  文档已最新，跳过：{doc_path.name}")
            return 0

        # Add one by one to completely avoid context length overflow in batch embedding
        added = 0
        for c in new_chunks:
            try:
                self.table.add([c])
                added += 1
            except Exception as e:
                logger.warning(f"    跳过过长 chunk: {c['heading_path'][:60]} ({len(c['chunk_text'])} chars)")
                continue

        logger.info(f"  新增 {added} 个 chunk（{doc_path.name}）")
        return added

    def index_all(self, force: bool = False) -> Dict[str, int]:
        """对 BID_DOCS_DIR 下所有 docx 文件建立索引"""
        if not BID_DOCS_DIR.exists():
            logger.warning(f"标书目录不存在：{BID_DOCS_DIR}")
            return {}

        docx_files = list(BID_DOCS_DIR.glob("*.docx")) + list(BID_DOCS_DIR.glob("*.doc"))
        logger.info(f"发现 {len(docx_files)} 个标书文档，开始建索引...")

        results = {}
        for f in docx_files:
            try:
                n = self.index_doc(f, force=force)
                results[f.name] = n
            except Exception as e:
                logger.error(f"  索引失败 {f.name}: {e}")
                results[f.name] = -1

        return results

    def search(self, query: str, top_k: int = 5, min_score: float = 0.0) -> List[Dict[str, Any]]:
        """
        向量检索最相关的 chunks。
        返回: [{"chunk_id", "doc_name", "heading_path", "chunk_text", "score"}, ...]
        """
        try:
            results = self.table.search(query, query_type="vector").limit(top_k).to_list()
        except Exception as e:
            logger.error(f"检索失败: {e}")
            return []

        output = []
        for r in results:
            # LanceDB returns "_distance" (cosine distance, lower = more similar)
            # Convert to similarity score: 1 - distance (ranges 0-1, higher = more similar)
            distance = r.get("_distance", 1.0)
            score = max(0.0, 1.0 - distance)
            if score < min_score:
                continue
            output.append({
                "chunk_id":     r["chunk_id"],
                "doc_name":     r["doc_name"],
                "heading_path": r["heading_path"],
                "heading_level": r["heading_level"],
                "chunk_text":   r["chunk_text"],
                "score":        score,
            })
        return output

    def count(self) -> int:
        """返回当前索引的 chunk 总数"""
        try:
            return len(self.table)
        except Exception:
            return 0
