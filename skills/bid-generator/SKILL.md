---
name: bid-generator
description: 自动应标方案生成系统。根据招标需求，自动从历史标书知识库中检索相关内容，AI生成应标方案Word文档。触发方式：用户说"生成应标方案"、"生成标书"、"自动投标"等。
---

# 自动应标方案生成系统

## 概述

根据招标需求，自动从历史标书知识库中检索相关内容，AI生成应标方案初稿。

## 工作流程

```
招标需求 → 关键词提取 → 向量检索(LanceDB) → AI生成(Minimax 2.7) → Word文档
```

## 快速开始

### 1. 首次安装配置

**Python 依赖**：
```bash
pip3 install python-docx lancedb requests
```

**环境变量配置**（必须）：
```bash
# 在 ~/.zshrc 或 ~/.bashrc 中添加：
export MINIMAX_API_KEY="你的API Key"

# 然后生效：
source ~/.zshrc  # 或 source ~/.bashrc
```

**获取 Minimax API Key**：
- 访问 [Minimax 开放平台](https://www.minimax.io/)
- 注册/登录账号
- 在控制台创建 API Key

**Ollama 服务**（用于向量 Embedding）：
```bash
# 确保 Ollama 服务运行中
ollama serve

# 下载向量模型（如果还没有）
ollama pull nomic-embed-text
```

### 2. 使用命令

```bash
cd ~/.openclaw/workspace/skills/bid-generator

# 完整生成（44章节，约20-25分钟）
python3 main.py --requirement "招标需求文本或文件路径" --output 我的方案.docx

# 快速测试（5章节）
python3 main.py --max-chapters 5 --output test.docx

# 从招标文件生成
python3 main.py --requirement /path/to/招标文件.docx --output 方案.docx
```

### 3. 参数说明

| 参数 | 说明 |
|------|------|
| `--requirement, -r` | 招标需求（字符串或 .txt/.docx 文件路径） |
| `--output, -o` | 输出 Word 路径（默认: test_output.docx） |
| `--no-build-kb` | 跳过知识库构建，复用现有索引 |
| `--max-chapters` | 最多生成章节数（0=全部，默认0） |

---

## 目录结构

```
bid-generator/
├── SKILL.md           # 本文档
├── config.py          # 配置文件（API Key 从环境变量读取）
├── knowledge_base.py # 文档读取、切片、向量化、存储到 LanceDB
├── retriever.py      # 向量检索 + 垃圾内容过滤 + 标题匹配加权
├── generator.py       # 调用 Minimax 2.7 生成章节内容
├── doc_builder.py     # 构建 Word 文档（python-docx）
├── main.py            # 主入口
├── templates/
│   └── 应标方案模板.md  # 应标方案模板（7章53节）
└── data/             # LanceDB 知识库（1265 chunks 历史标书 + 37 chunks CPIOT白皮书）
```

---

## 知识库

### 当前内容
- **历史标书**：7份设备/资产管理投标方案（共1265个chunk）
- **物联网白皮书**：CPIOT中设智控物联平台技术白皮书（37个chunk）

### 更新知识库
新的标书或资料放到以下目录，然后告诉小K更新：
```
/Users/visionsl/Documents/资料/标书方案
```

支持格式：
- Word 文档（.doc / .docx）✅
- Markdown 文本（.md）✅
- PDF（需先转换）❌ → 先用 markitdown 转成 .md

---

## 模板结构

生成的方案包含7章：

1. **项目总体说明** - 项目基本情况、安全保障机制
2. **系统技术说明** - 技术架构、CPII工具集、性能/安全性设计
3. **系统业务功能设计** - 资产管理、故障管理、维修管理、报表等
4. **应用平台技术方案** - 非功能性设计、二次开发平台
5. **项目实施方案** - 实施计划、团队、质量控制、风险防控
6. **培训计划** - 培训对象、课程安排
7. **技术支持和维护服务** - 售后服务内容、质保期服务

---

## 移植到其他设备

### 步骤

**1. 拷贝 skill 目录**：
```bash
scp -r ~/.openclaw/workspace/skills/bid-generator user@目标机器:~/.openclaw/workspace/skills/
```

**2. 拷贝知识库数据（建议）**：
```bash
# 如果不拷贝，首次使用会自动重建索引（需要从原始文件）
scp -r ~/.openclaw/workspace/skills/bid-generator/data user@目标机器:~/.openclaw/workspace/skills/bid-generator/
```

**3. 安装依赖**：
```bash
pip3 install python-docx lancedb requests
```

**4. 配置环境变量**：
```bash
export MINIMAX_API_KEY="你的API Key"
```

**5. 启动 Ollama**：
```bash
ollama serve
```

---

## 技术栈

- Python 3
- python-docx（Word生成）
- LanceDB（向量数据库）
- Ollama（本地AI，用于向量化）
- nomic-embed-text（向量化模型）
- Minimax 2.7（在线AI，用于内容生成）

---

## 注意事项

1. **API Key 安全**：Key 只放在环境变量中，不写在代码里
2. **Ollama 必须运行**：`ollama serve` 需要保持运行状态
3. **生成时间**：完整方案约需20-25分钟，请耐心等待
4. **生成内容为初稿**：需人工审核调整后再使用
5. **中文输入**：招标需求建议提供中文内容，效果更佳

---

## 扩展建议

1. **增加更多历史标书**：放入标书目录即可自动索引
2. **调整模板**：修改 `templates/应标方案模板.md`
3. **更换生成模型**：修改 `config.py` 中的 `GENERATE_MODEL`
4. **添加新行业模板**：创建新的模板文件，调整章节结构

---

*版本：v1.1*
*更新日期：2026-03-27*
*更新内容：API Key 改为环境变量配置*
