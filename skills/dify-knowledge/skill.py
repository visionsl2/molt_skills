#!/usr/bin/env python3
"""
Dify 知识库 Skill 工具

功能：
  1. 检索 Dify 知识库（语义检索）
  2. 新增文档（纯文本，自动等待索引完成）
  3. 列出知识库文档

用法：
  python3 skill.py search "关键词"
  python3 skill.py add "标题" "内容"
  python3 skill.py list
"""

import sys
import json
from dify_mcp import (
    search as dify_search,
    list_documents,
    add_document_sync,
    list_datasets,
    get_document_status,
)

# 默认返回条数
DEFAULT_TOP_K = 3


def format_results(dify_result: dict, top_k: int = 3) -> list[dict]:
    """格式化 Dify 检索结果为统一格式"""
    records = dify_result.get("records", [])
    results = []
    for r in records[:top_k]:
        seg = r.get("segment", {})
        doc = seg.get("document", {})
        results.append({
            "title": doc.get("name", ""),
            "content": seg.get("content", ""),
            "score": r.get("score", 0),
            "doc_id": doc.get("id", ""),
            "segment_id": seg.get("id", ""),
            "word_count": seg.get("word_count", 0),
            "position": seg.get("position", 0),
            "source": "dify"
        })
    return results


def search(query: str, top_k: int = DEFAULT_TOP_K) -> list[dict]:
    """
    搜索 Dify 知识库

    Args:
        query: 搜索关键词
        top_k: 返回结果数量（默认3）

    Returns:
        格式化后的结果列表
    """
    try:
        dify_result = dify_search(query, top_k=top_k)
        return format_results(dify_result, top_k)
    except Exception as e:
        print(f"[Dify] 搜索失败: {e}", file=sys.stderr)
        return []


def add_doc(title: str, content: str, wait: bool = True) -> dict:
    """
    向 Dify 知识库添加文档（同步方式，等待索引完成）

    Args:
        title: 文档标题
        content: 文档内容（纯文本）
        wait: 是否等待索引完成（默认True，索引约需10-30秒）

    Returns:
        添加结果（包含 document_id 和 indexing 状态）
    """
    try:
        result = add_document_sync(title, content, wait=wait)
        doc = result.get("document", {})
        return {
            "success": True,
            "document_id": doc.get("id"),
            "name": doc.get("name"),
            "indexing_status": doc.get("indexing_status"),
            "display_status": doc.get("display_status"),
            "enabled": doc.get("enabled"),
            "word_count": doc.get("word_count"),
            "result": result
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def list_docs() -> dict:
    """列出知识库所有文档"""
    try:
        result = list_documents()
        docs = result.get("data", [])
        return {
            "success": True,
            "total": result.get("total", 0),
            "count": len(docs),
            "has_more": result.get("has_more", False),
            "documents": [{
                "id": d["id"],
                "name": d["name"],
                "indexing_status": d.get("indexing_status"),
                "display_status": d.get("display_status"),
                "word_count": d.get("word_count", 0),
            } for d in docs]
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


# ============== CLI ==============
if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "search"

    if cmd == "search":
        query = sys.argv[2] if len(sys.argv) > 2 else "测试"
        top_k = int(sys.argv[3]) if len(sys.argv) > 3 else DEFAULT_TOP_K
        results = search(query, top_k)
        print(json.dumps(results, ensure_ascii=False, indent=2))

    elif cmd == "add":
        title = sys.argv[2] if len(sys.argv) > 2 else "无标题"
        content = sys.argv[3] if len(sys.argv) > 3 else ""
        no_wait = "--no-wait" in sys.argv
        result = add_doc(title, content, wait=not no_wait)
        print(json.dumps(result, ensure_ascii=False, indent=2))

    elif cmd in ("list", "docs"):
        result = list_docs()
        if result.get("success"):
            print(f"共 {result['count']} 个文档（总计 {result['total']}）：")
            for d in result["documents"]:
                print(f"  [{d['id'][:8]}] {d['name']} | {d['indexing_status']} / {d['display_status']} | {d['word_count']}字")
        else:
            print(f"失败: {result.get('error')}")

    else:
        print("Usage: python skill.py [search|add|list|docs]")
        print("  search <query> [top_k]    - 搜索知识库")
        print("  add <title> <content>      - 添加文档（等待索引约10-30秒）")
        print("  add <title> <content> --no-wait  - 添加文档（不等待）")
        print("  list                      - 列出所有文档")
