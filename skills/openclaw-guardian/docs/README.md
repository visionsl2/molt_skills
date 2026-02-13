# OpenClaw 配置守护进程 - 详细文档

## 简介

OpenClaw 配置守护进程是一个用于保护 OpenClaw 系统稳定性的脚本。它监控 Gateway 进程状态，在配置错误导致无法启动时自动恢复备份的配置。

## 系统要求

- Node.js 16+
- Windows 10/11
- OpenClaw 已安装

## 安装

技能已集成到 OpenClaw 工作区，无需额外安装。

## 快速开始

### 1. 启动守护进程

```bash
cd C:\Users\visio\.openclaw\workspace
node scripts/openclaw-guardian.js
```

建议使用 PM2 或 Windows 任务计划程序保持守护进程常驻运行。

### 2. 验证守护进程运行

```bash
# 查看日志
type scripts\guardian-log.txt

# 查看进程
tasklist /FI "IMAGENAME eq node.exe"
```

## 配置管理

### 备份当前配置

```bash
node scripts/config-manager.js backup
```

这会创建带时间戳的备份文件：
```
C:\Users\visio\.openclaw\backups\openclaw.json.bak.2026-02-13T10-30-00-000Z
```

### 更新配置（自动备份）

```bash
node scripts/config-manager.js update new-config.json
```

### 应用补丁（自动备份）

```bash
node scripts/config-manager.js patch patch.json
```

### 恢复配置

```bash
# 查看可用备份
dir C:\Users\visio\.openclaw\backups\

# 恢复指定备份
node scripts/config-manager.js restore "C:\Users\visio\.openclaw\backups\openclaw.json.bak.2026-02-13T10-30-00-000Z"
```

## 工作原理

### 状态检查

守护进程每 10 秒检查一次 Gateway 状态：

1. 检查端口是否有进程监听
2. 发送 HTTP 请求到 /health 端点
3. 判断进程是否正常运行

### 启动失败处理

当 Gateway 启动失败时：

1. 连续失败计数 +1
2. 记录日志
3. 等待下次检查

### 自动恢复

当连续失败次数超过阈值（默认 3 次）：

1. 从备份目录找到最新的备份文件
2. 将备份文件复制到配置目录
3. 使用恢复的配置重新启动
4. 重置连续失败计数

### 备份管理

- 备份位置：`C:\Users\visio\.openclaw\backups\`
- 命名格式：`openclaw.json.bak.ISO时间戳`
- 最大保留：5 个备份
- 自动清理：每次备份后删除旧备份

## 配置参数

修改 `scripts/openclaw-guardian.js` 中的 CONFIG 对象：

```javascript
const CONFIG = {
  checkInterval: 10000,       // 检查间隔（毫秒）
  gatewayPort: null,          // 从配置文件读取
  gatewayPath: '...',         // Gateway 路径
  logFile: '...',             // 日志文件
  stateFile: '...',           // 状态文件
  configFile: '...',          // 配置文件
  backupDir: '...',           // 备份目录
  maxRetries: 3,             // 连续失败阈值
};
```

## 日志分析

### 正常日志

```
[2026/2/13 10:30:00] ========== 守护进程启动 ==========
[2026/2/13 10:30:00] 📊 已加载状态，连续失败: 0
[2026/2/13 10:30:00] --- 检查 ---
[2026/2/13 10:30:02] ✅ 正常
[2026/2/13 10:30:02] 守护进程运行中...
```

### 启动失败日志

```
[2026/2/13 10:31:00] --- 检查 ---
[2026/2/13 10:31:00] ⚠️ 未运行
[2026/2/13 10:31:00] 🔄 重启次数: 1, 连续失败: 1
[2026/2/13 10:31:00] 🚀 启动 Gateway...
[2026/2/13 10:31:08] ❌ 启动失败
```

### 自动恢复日志

```
[2026/2/13 10:32:00] --- 检查 ---
[2026/2/13 10:32:00] ⚠️ 未运行
[2026/2/13 10:32:00] 🔄 重启次数: 4, 连续失败: 4
[2026/2/13 10:32:00] ⚠️ 连续失败超过 3 次，尝试恢复配置...
[2026/2/13 10:32:00] ✅ 已恢复配置: openclaw.json.bak.2026-02-13T10-30-00-000Z
[2026/2/13 10:32:00] ✅ 配置已恢复，将使用上一个正常配置重新启动
[2026/2/13 10:32:00] 🚀 启动 Gateway...
[2026/2/13 10:32:08] ✅ Gateway 已启动，PID: 12345
```

## 故障排除

### 守护进程无法启动

检查是否有其他进程占用了端口：
```bash
netstat -ano | findstr 18789
```

### 备份恢复失败

检查备份目录权限：
```bash
dir C:\Users\visio\.openclaw\backups\
```

### Gateway 持续失败

1. 检查配置文件语法：`node -c openclaw.json`
2. 查看 Gateway 错误日志
3. 手动恢复配置后重试

## 自动化配置

### Windows 开机自启

1. 打开任务计划程序
2. 创建基本任务
3. 触发器：计算机启动
4. 操作：启动程序
5. 程序：`node C:\Users\visio\.openclaw\workspace\scripts\openclaw-guardian.js`

### 使用 PM2

```bash
npm install -g pm2
pm2 start scripts/openclaw-guardian.js --name openclaw-guardian
pm2 save
pm2 startup
```

## 升级记录

### v1.0 (2026-02-13)

- 初始版本
- 进程监控
- 自动重启
- 配置备份与恢复
