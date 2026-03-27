# -*- coding: utf-8 -*-
"""
bid_generator/retriever.py
===========================
检索器：根据招标需求检索知识库中的相关段落

优化版本 v2:
1. 过滤"垃圾标题"（承诺函、公司简介等通用内容）
2. 标题匹配度加权：query关键词出现在heading中时加分
3. 过滤过短内容（参考价值低）
"""

import logging
import re
from typing import List, Dict, Any, Optional

from config import TOP_K, SIMILARITY_THRESHOLD, logger
from knowledge_base import BidKnowledgeBase

# ========== 章节过滤器定义 ==========

CHAPTER_FILTERS = {
    "项目总体说明":    ["第一章", "项目基本情况", "企业概况", "建设目标"],
    "技术架构":        ["第二章", "技术架构", "技术路线", "软件技术架构"],
    "业务功能":        ["第三章", "系统管理", "资产管理", "故障管理", "维修管理", "报表管理"],
    "实施计划":       ["第五章", "实施计划", "实施团队", "项目实施", "培训"],
    "技术支持":        ["第七章", "技术支持和维护", "售后服务", "质保"],
}

# ========== 垃圾标题过滤（通用内容，参考价值低）==========
JUNK_HEADINGS = {
    "承诺函", "公司简介", "公司介绍", "法定代表人", "授权委托书",
    "投标函", "投标保证金", "退还保证金", "资格证明", "营业执照",
    "商务偏差表", "技术偏差表", "分项明细表", "报价明细",
    "目录", "投标文件", "技术标", "商务标",
    "具备履行合同", "投标单位", "中标候选人", "评标结果",
    "扫描结果", "测试结果", "交付文档", "交付成果",
}

# ========== 标题级别权重（越小越重要）==========
HEADING_LEVEL_WEIGHTS = {1: 1.0, 2: 0.9, 3: 0.8}


class BidRetriever:
    """
    标书检索器 v2：
      - 向量检索 + 标题匹配加权 + 垃圾内容过滤
      - 返回带相似度分数的相关段落
    """

    def __init__(self, kb: BidKnowledgeBase = None):
        self.kb = kb or BidKnowledgeBase()

    @staticmethod
    def parse_keywords(requirement_text: str) -> List[str]:
        """
        从招标需求文本中提取关键词（简单启发式）。
        返回关键词列表。
        """
        # 去除标点，保留中文和英文
        text = re.sub(r"[^\w\u4e00-\u9fff\s]", " ", requirement_text)
        words = text.split()
        # 过滤掉单字和常见停用词
        stopwords = {"的", "了", "是", "在", "和", "与", "或", "及", "等", "为", "以", "对", "于", "按", "将", "可", "能", "要", "会", "该", "本", "其", "中"}
        keywords = [w for w in words if len(w) >= 2 and w not in stopwords]
        # 合并相邻关键词形成短语
        phrases = []
        for i in range(len(keywords) - 1):
            phrase = f"{keywords[i]}{keywords[i+1]}"
            if len(phrase) >= 4:
                phrases.append(phrase)
        return keywords[:20] + phrases[:10]

    def _is_junk_heading(self, heading_path: str, chunk_text: str) -> bool:
        """判断是否为垃圾标题"""
        # 空标题（只有文档名）
        if not heading_path or len(heading_path.strip()) < 5:
            return True
        
        # 检查垃圾关键词
        for junk in JUNK_HEADINGS:
            if junk in heading_path:
                return True
        
        return False

    def _calculate_title_bonus(self, heading_path: str, query_keywords: List[str]) -> float:
        """
        计算标题匹配度加分
        查询关键词出现在标题中时，给与加分
        """
        bonus = 0.0
        heading_lower = heading_path.lower()
        for kw in query_keywords:
            if len(kw) >= 3 and kw in heading_path:
                bonus += 0.05  # 每个匹配加0.05
        return bonus

    def _rerank_results(
        self,
        results: List[Dict[str, Any]],
        query_keywords: List[str],
        min_score: float = SIMILARITY_THRESHOLD,
    ) -> List[Dict[str, Any]]:
        """
        对检索结果进行重排序：
        1. 过滤垃圾标题
        2. 过滤过短内容（<50字）
        3. 加上标题匹配度加分
        4. 加上标题级别权重
        """
        reranked = []
        
        for r in results:
            heading = r.get("heading_path", "")
            text = r.get("chunk_text", "")
            
            # 过滤垃圾标题
            if self._is_junk_heading(heading, text):
                continue
            
            # 过滤过短内容
            if len(text.strip()) < 50:
                continue
            
            # 计算综合分数
            base_score = r["score"]
            title_bonus = self._calculate_title_bonus(heading, query_keywords)
            level_weight = HEADING_LEVEL_WEIGHTS.get(r.get("heading_level", 3), 0.8)
            
            final_score = base_score + title_bonus
            r["final_score"] = final_score
            r["title_bonus"] = title_bonus
            
            if final_score >= min_score:
                reranked.append(r)
        
        # 按最终分数降序排序
        reranked.sort(key=lambda x: x["final_score"], reverse=True)
        return reranked

    def retrieve(
        self,
        requirement_text: str,
        top_k: int = TOP_K,
        min_score: float = SIMILARITY_THRESHOLD,
        chapter_filter: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        检索相关段落 v2。

        参数:
          requirement_text: 招标需求文本
          top_k: 返回数量
          min_score: 最低相似度
          chapter_filter: 可选，章节类别关键词（如 "技术架构"）

        返回:
          [{"chunk_id", "doc_name", "heading_path", "chunk_text", "score", "final_score"}, ...]
        """
        # Step 1: 提取关键词，构建检索 query
        keywords = self.parse_keywords(requirement_text)
        logger.info(f"[Retriever] 提取关键词: {keywords[:8]}")

        query = requirement_text[:500]  # 用需求前500字作为主检索query
        if chapter_filter:
            query += f" {chapter_filter}"
        if keywords:
            query += " " + " ".join(keywords[:5])

        # Step 2: 向量检索（取更多候选）
        raw_results = self.kb.search(query, top_k=top_k * 3, min_score=0.0)

        # Step 3: 章节过滤（如果指定）
        if chapter_filter:
            filter_terms = CHAPTER_FILTERS.get(chapter_filter, [chapter_filter])
            filtered = []
            for r in raw_results:
                heading = r.get("heading_path", "")
                text = r.get("chunk_text", "")
                if any(term in heading or term in text for term in filter_terms):
                    filtered.append(r)
            if not filtered:
                # 没匹配到，放宽过滤
                filtered = raw_results[:top_k]
            raw_results = filtered

        # Step 4: 重排序（过滤垃圾、标题加权）
        results = self._rerank_results(raw_results, keywords, min_score=0.2)[:top_k]

        logger.info(f"[Retriever] 检索到 {len(results)} 个相关段落")
        for i, r in enumerate(results, 1):
            logger.info(f"  [{i}] score={r['final_score']:.3f}(base={r['score']:.3f}, bonus={r.get('title_bonus',0):.3f}) | {r['doc_name'][:30]} | {r['heading_path'][:50]}")
            logger.info(f"      内容预览: {r['chunk_text'][:60].strip()}...")

        return results

    def retrieve_by_chapters(
        self,
        requirement_text: str,
        chapters: List[str],
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        按多个章节类别分别检索。

        参数:
          requirement_text: 招标需求文本
          chapters: 章节类别列表，如 ["技术架构", "业务功能"]

        返回:
          {章节类别: [检索结果列表], ...}
        """
        output = {}
        for chapter in chapters:
            results = self.retrieve(
                requirement_text,
                top_k=TOP_K,
                chapter_filter=chapter,
            )
            output[chapter] = results
        return output
