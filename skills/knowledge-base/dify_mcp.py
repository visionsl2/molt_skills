#!/usr/bin/env python3
"""
Dify 知识库 MCP Client
对接 Dify v1 API 实现知识库检索和新增

配置：
  - DIFY_BASE_URL: http://160.0.6.9/v1
  - DIFY_API_KEY: dataset-GeVY5VrH2Uu0cgr931oLHaze
  - DIFY_DATASET_ID: 9c3e5075-386d-49cf-a500-b92705eccdf7
"""

import requests
import sys
import json
import time

# ============== 配置 ==============
DIFY_BASE_URL = "http://160.0.6.9/v1"
DIFY_API_KEY = "dataset-GeVY5VrH2Uu0cgr931oLHaze"
DIFY_DATASET_ID = "9c3e5075-386d-49cf-a500-b92705eccdf7"
# =================================

HEADERS = {
    "Authorization": f"Bearer {DIFY_API_KEY}",
    "Content-Type": "application/json"
}


def search(query: str, top_k: int = 3) -> dict:
    """
    检索 Dify 知识库
    POST /v1/datasets/{id}/retrieve
    """
    url = f"{DIFY_BASE_URL}/datasets/{DIFY_DATASET_ID}/retrieve"
    payload = {
        "query": query,
        "top_k": top_k
    }
    resp = requests.post(url, headers=HEADERS, json=payload, timeout=30)
    resp.raise_for_status()
    return resp.json()


def list_datasets(page_size: int = 20) -> dict:
    """列出所有知识库 GET /v1/datasets"""
    url = f"{DIFY_BASE_URL}/datasets"
    resp = requests.get(url, headers=HEADERS, params={"page_size": page_size}, timeout=15)
    resp.raise_for_status()
    return resp.json()


def get_dataset(dataset_id: str = None) -> dict:
    """获取指定知识库详情 GET /v1/datasets/{id}"""
    url = f"{DIFY_BASE_URL}/datasets/{dataset_id or DIFY_DATASET_ID}"
    resp = requests.get(url, headers=HEADERS, timeout=15)
    resp.raise_for_status()
    return resp.json()


def list_documents(dataset_id: str = None, page_size: int = 20) -> dict:
    """列出知识库中的文档 GET /v1/datasets/{id}/documents"""
    url = f"{DIFY_BASE_URL}/datasets/{dataset_id or DIFY_DATASET_ID}/documents"
    resp = requests.get(url, headers=HEADERS, params={"page_size": page_size}, timeout=15)
    resp.raise_for_status()
    return resp.json()


def add_document_by_text(title: str, content: str, dataset_id: str = None) -> dict:
    """
    向 Dify 知识库添加文档（纯文本）
    POST /v1/datasets/{id}/document/create-by-text
    Dify 处理文档是异步的，返回 document_id 后需要等待 indexing 完成。
    """
    url = f"{DIFY_BASE_URL}/datasets/{dataset_id or DIFY_DATASET_ID}/document/create-by-text"
    payload = {
        "name": title,
        "text": content,
        "indexing_technique": "high_quality",
        "process_rule": {
            "mode": "automatic"
        }
    }
    resp = requests.post(url, headers=HEADERS, json=payload, timeout=30)
    resp.raise_for_status()
    return resp.json()


def get_document_status(document_id: str, dataset_id: str = None) -> dict:
    """查询文档 indexing 状态 GET /v1/datasets/{id}/documents/{doc_id}"""
    url = f"{DIFY_BASE_URL}/datasets/{dataset_id or DIFY_DATASET_ID}/documents/{document_id}"
    resp = requests.get(url, headers=HEADERS, timeout=15)
    resp.raise_for_status()
    return resp.json()


def wait_for_indexing(document_id: str, dataset_id: str = None, timeout: int = 120, poll_interval: int = 5) -> dict:
    """
    等待文档 indexing 完成
    indexing_status 流程: waiting → parsing → cleaning → splitting → indexing → completed / error
    """
    start = time.time()
    while time.time() - start < timeout:
        status = get_document_status(document_id, dataset_id)
        info = status.get("document", {})
        idx_status = info.get("indexing_status", "")
        display = info.get("display_status", "")
        enabled = info.get("enabled", False)

        print(f"  [Dify] 状态: {idx_status} / {display} / enabled={enabled}")

        if idx_status == "completed":
            print(f"  [Dify] 文档处理完成！")
            return status
        elif idx_status == "error":
            raise RuntimeError(f"文档 indexing 失败: {info.get('error')}")

        time.sleep(poll_interval)

    raise TimeoutError(f"文档 indexing 超时（{timeout}s）: {document_id}")


def add_document_sync(title: str, content: str, dataset_id: str = None, wait: bool = True) -> dict:
    """同步添加文档（可选等待 indexing 完成）"""
    print(f"  [Dify] 正在创建文档: {title}")
    result = add_document_by_text(title, content, dataset_id)
    doc_info = result.get("document", {})
    doc_id = doc_info.get("id")
    print(f"  [Dify] 文档已创建，ID: {doc_id}，等待索引...")

    if wait:
        return wait_for_indexing(doc_id, dataset_id)
    return result


def delete_document(document_id: str, dataset_id: str = None) -> dict:
    """删除文档 DELETE /v1/datasets/{id}/documents/{doc_id}"""
    url = f"{DIFY_BASE_URL}/datasets/{dataset_id or DIFY_DATASET_ID}/documents/{document_id}"
    resp = requests.delete(url, headers=HEADERS, timeout=15)
    resp.raise_for_status()
    return resp.json() if resp.content else {"success": True}


# ============== CLI ==============
if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "search"

    if cmd == "search":
        query = sys.argv[2] if len(sys.argv) > 2 else "测试"
        top_k = int(sys.argv[3]) if len(sys.argv) > 3 else 3
        result = search(query, top_k)
        print(json.dumps(result, ensure_ascii=False, indent=2))

    elif cmd == "list":
        result = list_datasets()
        datasets = result.get("data", [])
        for ds in datasets:
            print(f"  [{ds['id']}] {ds['name']} | 文档:{ds['document_count']} | 可用:{ds['total_available_documents']}")

    elif cmd == "docs":
        result = list_documents()
        docs = result.get("data", [])
        print(f"共 {len(docs)} 个文档：")
        for d in docs:
            print(f"  [{d['id']}] {d['name']} | 状态:{d.get('indexing_status','?')} | 字数:{d.get('word_count',0)}")

    elif cmd == "add":
        title = sys.argv[2] if len(sys.argv) > 2 else "测试文档"
        content = sys.argv[3] if len(sys.argv) > 3 else "测试内容"
        result = add_document_sync(title, content)
        print(json.dumps(result, ensure_ascii=False, indent=2))

    elif cmd == "status":
        doc_id = sys.argv[2] if len(sys.argv) > 2 else ""
        if doc_id:
            result = get_document_status(doc_id)
        else:
            result = list_documents()
        print(json.dumps(result, ensure_ascii=False, indent=2))

    else:
        print(f"Usage: python dify_mcp.py [search|list|docs|add|status]")
