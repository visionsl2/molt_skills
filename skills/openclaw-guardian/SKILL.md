# OpenClaw 配置守护技能

## 概述

自动监控 OpenClaw Gateway 进程状态，在配置错误导致无法启动时自动恢复备份的配置。

## 功能

1. **进程监控** - 每 10 秒检查 Gateway 状态
2. **自动重启** - Gateway 意外退出时自动启动
3. **配置备份** - 修改配置前自动备份
4. **自动恢复** - 连续启动失败 > 3 次时，自动恢复上一个备份的配置
5. **备份清理** - 只保留最近 5 个备份文件

## 文件结构

```
skills/openclaw-guardian/
├── SKILL.md                    # 技能说明
├── scripts/
│   ├── openclaw-guardian.js    # 守护进程主脚本
│   ├── config-manager.js       # 配置管理脚本
│   └── config-manager.bat      # Windows 批处理版本
└── docs/
    └── README.md               # 详细文档
```

## 使用方法

### 启动守护进程

```bash
node scripts/openclaw-guardian.js
```

### 配置管理

```bash
# 备份当前配置
node scripts/config-manager.js backup

# 从文件更新配置（自动备份）
node scripts/config-manager.js update <file.json>

# 应用配置补丁（自动备份）
node scripts/config-manager.js patch <patch.json>

# 恢复指定备份
node scripts/config-manager.js restore <backup-file>
```

### 备份位置

```
C:\Users\visio\.openclaw\backups\
```

## 配置说明

| 参数 | 默认值 | 说明 |
|------|--------|------|
| checkInterval | 10000 | 检查间隔（毫秒） |
| maxRetries | 3 | 连续失败次数阈值 |
| backupDir | C:\Users\visio\.openclaw\backups | 备份目录 |

## 工作流程

```
1. 守护进程每 10 秒检查 Gateway 状态
2. 如果 Gateway 未运行或无响应 → 尝试启动
3. 如果启动失败 → 连续失败计数 +1
4. 如果连续失败 > 3 次 → 自动恢复上一个备份的配置
5. 使用恢复的配置重新启动
```

## 注意事项

1. **修改配置前备份** - AI 修改 openclaw.json 前必须先调用 `config-manager.js backup`
2. **守护进程会读取配置** - 守护进程从配置文件读取端口等参数
3. **备份保留** - 只保留最近 5 个备份，自动清理旧备份

## 常见问题

### Q: 如何手动恢复配置？

```bash
# 查看备份列表
dir C:\Users\visio\.openclaw\backups\

# 恢复指定备份
node scripts/config-manager.js restore "C:\Users\visio\.openclaw\backups\openclaw.json.bak.2026-02-13T02-22-20-180Z"
```

### Q: 如何查看守护进程日志？

```bash
type scripts\guardian-log.txt
```

### Q: 如何停止守护进程？

```bash
taskkill /F /IM node.exe /FI "WINDOWTITLE eq *openclaw-guardian*"
```

## 版本

- v1.0 (2026-02-13) - 初始版本
