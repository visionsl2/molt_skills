---
name: knowledge-base
description: 知识库管理工具，支持本地和远程两种模式。触发方式：用户说"查知识库"、"搜一下"、"添加知识"、"存到知识库"等。
version: 1.1.0
github: https://github.com/visionsl2/molt_skills
---

# knowledge-base Skill

> 知识库Skill - 向量语义检索 + Word图片提取

## 触发条件
用户发送文件、URL或直接提问时，自动进行知识库检索

## 功能列表

### 1️⃣ 自动检索知识库
- 用户提问时，先从本地知识库语义搜索相关内容
- 基于向量相似度检索，理解语义而非关键词匹配
- 搜不到相关内容时，自动fallback到网上搜索

### 2️⃣ 添加内容到知识库
- 用户发送文件时，自动提取内容并向量化存储
- 支持多种文件格式自动解析

### 3️⃣ Word图片提取
- 自动从Word文档中提取图片并保存
- 检索结果返回文字 + 相关图片路径

## 支持的文件格式

| 类型 | 状态 | 说明 |
|------|------|------|
| txt/md | ✅ | 直接读取 |
| docx | ✅ | Word文档 + **图片提取** |
| pdf | ✅ | PDF文档 |
| xlsx/xls | ✅ | Excel表格 |
| url | ✅ | 网页抓取 |

## 工作流程

```
用户发送文件 → 内容提取 → 向量化存储
                              ↓
用户提问 → 语义检索 → 返回结果
```

## 图片存储说明
- 目录: ~/openclaw_doc/knowledge/images/
- 格式: {doc_id}_{序号}.{png|jpg|jpeg}
- 检索时可返回相关图片

## 技术栈
- 向量数据库: LanceDB
- Embedding模型: Ollama nomic-embed-text (768维)
- 文件解析: pypdf, openpyxl, python-docx

## 使用示例

**添加文档：**
- 用户发送PDF/Word文件 → 自动提取文字并存入知识库

**检索知识：**
- 用户提问 → 先搜本地知识库 → 返回结果

**检索结果包含：**
- 标题
- 内容摘要
- 原文（长文本）
- 相关图片列表

## 本地存储结构
```
~/openclaw_doc/knowledge/
├── lancedb/          # 向量数据库
├── docs/             # 原文存储 (txt)
└── images/           # Word提取的图片
```

## 维护命令
```bash
# 查看知识库文档数
ls ~/openclaw_doc/knowledge/docs/

# 查看提取的图片
ls ~/openclaw_doc/knowledge/images/

# 搜索测试
python3 skill.py search "关键词"
```

## 更新日志
- 2026-03-04: 支持Word文档图片提取
- 2026-03-03: 初始版本，向量检索
