# knowledge-base Skill

## 触发条件
用户发送文件、URL或直接提问时，自动进行知识库检索

## 功能
1. **自动检索知识库** - 用户提问时，先从本地知识库语义搜索相关内容
2. **添加内容到知识库** - 用户发送文件时，自动提取内容并向量化存储
3. **提取Word图片** - 自动从Word文档中提取图片并保存
4. **智能 fallback** - 知识库搜不到相关内容时，再上网搜索

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
用户发送Word文件 → 提取文字 + 提取图片 → 文字向量化存储 + 图片保存到本地
                              ↓
用户检索 → 返回文字内容 + 相关图片路径
```

## 图片存储位置
- 目录: ~/openclaw_doc/knowledge/images/
- 格式: {doc_id}_{序号}.{png|jpg|jpeg}

## 代码位置
- Skill工具: ~/.openclaw/workspace/skills/knowledge-base/skill.py
- 向量数据: ~/openclaw_doc/knowledge/lancedb/
- 原文存储: ~/openclaw_doc/knowledge/docs/
- 图片存储: ~/openclaw_doc/knowledge/images/

## 技术栈
- 向量数据库: LanceDB
- Embedding模型: Ollama nomic-embed-text
- 文件解析: pypdf, openpyxl, python-docx

## 使用示例
- 发送Word(含图片) → 自动提取文字+图片并存入知识库
- 检索 → 返回文字内容 + 图片列表

## 维护
- 查看知识库文档数: `ls ~/openclaw_doc/knowledge/docs/`
- 查看提取的图片: `ls ~/openclaw_doc/knowledge/images/`
- 推送到GitHub: 每次更新skill后同步推送
