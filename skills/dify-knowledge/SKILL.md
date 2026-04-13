---
name: dify-knowledge
description: Dify 知识库工具，支持检索和新增文档。触发方式：用户说"查Dify知识库"、"搜Dify"、"搜知识库"、"查中设云知识库"、"添加知识到Dify"等。
version: 1.1.0
---

# Dify 知识库 Skill

> 对接 Dify v1 API（路径：`/v1/datasets/{id}/document/create-by-text`）
> 支持**检索**和**新增文档**两大功能

---

## ⚙️ 配置

| 参数 | 值 |
|------|-----|
| Dify 地址 | http://160.0.6.9/v1 |
| 知识库 ID | 9c3e5075-386d-49cf-a500-b92705eccdf7 |
| 知识库名称 | 中设云知识库 |
| API Key | `dataset-GeVY5VrH2Uu0cgr931oLHaze` |

---

## 🔍 搜索流程

```
用户提问
   ↓
Dify 知识库语义检索
   ↓
格式化返回（标题 + 内容摘要 + 相似度分数 + 文档ID）
```

---

## 📌 功能列表

### 1️⃣ 检索知识库 ✅
- 向量语义检索，理解语义而非关键词匹配
- 返回相关文档片段、来源文档名、相似度分数
- 默认返回 top 3 条最相关结果

### 2️⃣ 新增文档 ✅
- 纯文本方式添加文档
- 异步 indexing（约10-30秒），可选择是否等待完成
- 新增后可直接检索到

### 3️⃣ 列出文档 ✅
- 查看知识库中所有文档及状态

---

## 🔧 维护命令

```bash
# 搜索知识库
python3 skill.py search "设备管理"
python3 skill.py search "关键词" 5

# 添加文档（等待索引，约10-30秒）
python3 skill.py add "文档标题" "文档内容"

# 添加文档（不等待，快速返回）
python3 skill.py add "文档标题" "文档内容" --no-wait

# 列出文档
python3 skill.py docs
```

---

## 技术栈

| 组件 | 说明 |
|------|------|
| **知识库** | Dify v1.11.1（自部署） |
| **向量模型** | bge-m3（由 Dify/Ollama 提供） |
| **检索方式** | 语义相似度搜索（semantic_search） |
| **新增方式** | REST API + 异步 indexing |
