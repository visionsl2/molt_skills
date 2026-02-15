# OpenClaw Guardian - 使用指南

## 📦 安装

### 1. 克隆或更新 skill

```bash
# 克隆（首次）
cd skills
git clone https://github.com/visionsl2/molt_skills.git

# 更新（已有）
cd skills/openclaw-guardian
git pull
```

### 2. 运行安装配置

首次使用前必须先配置：

```bash
cd skills/openclaw-guardian
node scripts/setup.js
```

安装程序会引导您设置：
- Gateway 端口（默认 18789）
- 检查间隔（默认 30 秒）
- 连续失败重试次数（默认 3 次）

配置完成后会保存到 `scripts/config.json`。

### 3. 启动守护进程

```bash
node scripts/openclaw-guardian.js
```

## ⚙️ 配置

### 重新配置

```bash
node scripts/setup.js
```

### 查看当前配置

```bash
type scripts\config.json
```

## 📖 使用命令

### 备份当前配置

```bash
node scripts/config-manager.js backup
```

### 恢复配置

```bash
# 查看备份列表
dir C:\Users\visio\.openclaw\backups\

# 恢复指定备份
node scripts/config-manager.js restore "C:\Users\visio\.openclaw\backups\openclaw.json.bak.2026-02-16TXX-XX-XX-XXXZ"
```

### 查看日志

```bash
type scripts\guardian-log.txt
```

## 🛠️ 常见问题

### Q: 守护进程检测不到运行中的 Gateway？

A: 确保已运行 `setup.js` 配置正确的端口。如果仍然检测失败，可能是权限问题，尝试以管理员身份运行。

### Q: 如何停止守护进程？

```bash
taskkill /F /IM node.exe /FI "WINDOWTITLE eq *openclaw-guardian*"
```

### Q: 日志太多怎么办？

A: 检查间隔已设置为 30 秒，日志量适中。如需调整，重新运行 `setup.js`。

### Q: Gateway 不断重启怎么办？

A: 检查日志中的错误信息，可能是配置文件损坏。守护进程会在连续失败 3 次后自动恢复上一个备份的配置。

## 📁 文件结构

```
openclaw-guardian/
├── SKILL.md              # 技能说明
├── README.md             # 本文件
├── CHANGELOG.md          # 更新日志
├── scripts/
│   ├── setup.js              # 安装配置向导
│   ├── openclaw-guardian.js  # 守护进程主脚本
│   ├── config-manager.js     # 配置管理
│   └── config.json          # 用户配置（运行时生成）
└── docs/
    └── README.md         # 详细文档
```

## 🔗 相关链接

- GitHub: https://github.com/visionsl2/molt_skills
- OpenClaw: https://docs.openclaw.ai
