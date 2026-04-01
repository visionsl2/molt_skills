#!/usr/bin/env python3
"""
知识库 MCP Client
调用远程知识库服务

Version: 1.0.0
Changelog:
  1.0.0 (2026-03-04) - 初始版本，支持远程知识库CRUD
"""

import requests
import sys
import json

SERVER_URL = "http://160.0.6.9:8877"

def search(query: str, top_k: int = 3, instance_id: str = "all"):
    """搜索知识库"""
    resp = requests.post(f"{SERVER_URL}/api/search", json={
        "query": query,
        "top_k": top_k,
        "instance_id": instance_id
    }, timeout=60)
    return resp.json()

def add(title: str, content: str = "", keywords: list = None, 
        source_type: str = "text", file_path: str = None,
        instance_id: str = "default"):
    """添加文档"""
    resp = requests.post(f"{SERVER_URL}/api/add", json={
        "title": title,
        "content": content,
        "keywords": keywords or [],
        "source_type": source_type,
        "file_path": file_path,
        "instance_id": instance_id
    }, timeout=120)
    return resp.json()

def list_docs(instance_id: str = "all"):
    """列出文档"""
    resp = requests.get(f"{SERVER_URL}/api/list", params={"instance_id": instance_id})
    return resp.json()

def stats():
    """获取统计"""
    resp = requests.get(f"{SERVER_URL}/api/stats")
    return resp.json()

def health():
    """健康检查"""
    resp = requests.get(f"{SERVER_URL}/health")
    return resp.json()

if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "search"
    
    if cmd == "search":
        query = sys.argv[2] if len(sys.argv) > 2 else "test"
        result = search(query)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    
    elif cmd == "add":
        title = sys.argv[2] if len(sys.argv) > 2 else "无标题"
        content = sys.argv[3] if len(sys.argv) > 3 else ""
        result = add(title, content)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    
    elif cmd == "list":
        result = list_docs()
        print(json.dumps(result, ensure_ascii=False, indent=2))
    
    elif cmd == "stats":
        result = stats()
        print(json.dumps(result, ensure_ascii=False, indent=2))
    
    elif cmd == "health":
        result = health()
        print(json.dumps(result, ensure_ascii=False, indent=2))
    
    else:
        print(f"Unknown command: {cmd}")
        print("Usage: python knowledge_mcp.py [search|add|list|stats|health]")
