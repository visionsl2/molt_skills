---
name: knowledge-base
description: 知识库管理工具，支持本地和远程两种模式。触发方式：用户说"查知识库"、"搜一下"、"添加知识"、"存到知识库"等。
version: 1.2.1
github: https://github.com/visionsl2/molt_skills
---

# knowledge-base Skill

> 知识库Skill - 向量语义检索 + Word图片提取

---

## ⚙️ 首次安装配置

### 1. 远程知识库服务器地址

**默认配置**（如需修改编辑 `knowledge_mcp.py`）：
```python
SERVER_URL = "http://160.0.6.9:8877"  # IP: 160.0.6.9  端口: 8877
```

> ⚠️ **首次使用请确认**：远程知识库服务器是否可用，如不可用请联系管理员部署 `knowledge-mcp-server`

### 2. 本地依赖安装

```bash
pip install lancedb pyarrow requests python-docx pypdf openpyxl
```

### 3. Ollama 配置（Embedding模型）

本地和远程 Ollama 都支持，编辑 `skill.py` 修改地址：

#### 本地 Ollama（默认）
```python
OLLAMA_URL = "http://localhost:11434/api/embeddings"
```
```bash
ollama serve
ollama pull nomic-embed-text
```

#### 远程 Ollama
```python
OLLAMA_URL = "http://<远程IP>:<端口>/api/embeddings"
# 示例: http://160.0.6.9:11434/api/embeddings
```
> ⚠️ 远程 Ollama 服务器需满足以下条件：
> 1. 安装 `nomic-embed-text` 模型：`ollama pull nomic-embed-text`
> 2. 允许外部访问：启动时加 `--host 0.0.0.0`
> 3. 端口默认 `11434`，如有修改请同步更新 URL

---

## 🔍 搜索流程（远程优先，本地兜底）

```
用户提问 → 远程知识库 search()
              ↓ 有结果
          返回结果给用户
              ↓ 无结果
          本地知识库 search()
              ↓ 有结果
          返回结果给用户
              ↓ 无结果
          提示"知识库暂无相关内容"
```

> 📌 **默认策略**：优先使用远程知识库，远程没有匹配内容时才会调用本地知识库

---

## 功能列表

### 1️⃣ 自动检索知识库
- **远程优先**：先从远程知识库语义搜索
- **本地兜底**：远程无结果时，搜索本地 LanceDB
- 基于向量相似度检索，理解语义而非关键词匹配

### 2️⃣ 添加内容到知识库
- **默认添加到远程知识库**
- 支持多种文件格式自动解析
- 本地同步存储（原始文档 + 向量）

### 3️⃣ Word图片提取
- 自动从Word文档中提取图片并保存
- 检索结果返回文字 + 相关图片路径

---

## 支持的文件格式

| 类型 | 状态 | 说明 |
|------|------|------|
| txt/md | ✅ | 直接读取 |
| docx | ✅ | Word文档 + **图片提取** |
| pdf | ✅ | PDF文档 |
| xlsx/xls | ✅ | Excel表格 |
| url | ✅ | 网页抓取 |

---

## 📁 本地存储结构

```
~/openclaw_doc/knowledge/
├── lancedb/          # 向量数据库
├── docs/             # 原文存储 (txt)
└── images/           # Word提取的图片
```

---

## 🔧 维护命令

```bash
# 查看远程知识库状态
python3 knowledge_mcp.py health

# 查看远程知识库文档列表
python3 knowledge_mcp.py list

# 搜索测试（自动走远程+本地流程）
python3 skill.py search "关键词"

# 手动添加文档到远程
python3 knowledge_mcp.py add "文档标题" "文档内容"
```

---

## 技术栈

| 组件 | 说明 |
|------|------|
| **远程服务** | knowledge-mcp-server v2.1 |
| **向量数据库** | LanceDB（本地） |
| **Embedding模型** | Ollama nomic-embed-text (768维) |
| **文件解析** | python-docx, pypdf, openpyxl |

---

## 更新日志

| 版本 | 日期 | 内容 |
|------|------|------|
| v1.2.1 | 2026-04-01 | 新增远程Ollama配置说明 |
| v1.2.0 | 2026-04-01 | 优化搜索流程：远程优先，本地兜底；添加配置说明 |
| v1.1.0 | 2026-03-30 | 新增docx图片提取功能 |
| v1.0.0 | 2026-03-04 | 初始版本 |
