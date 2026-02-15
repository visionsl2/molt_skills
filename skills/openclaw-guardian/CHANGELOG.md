# CHANGELOG - OpenClaw Guardian

## v1.1 (2026-02-16)

### 🐛 修复

- **端口检测问题**：`Get-NetTCPConnection` 在某些情况下返回 0，无法正确获取 PID
  - 改用 `netstat -ano` 获取 PID（更可靠）
  - 保留备用方案（Get-NetTCPConnection）

### ✨ 新功能

- **交互式安装配置**：新增 `setup.js` 向导
  - 首次使用前引导用户配置
  - 支持自定义端口、检查间隔、重试次数
  - 配置保存到 `scripts/config.json`

- **启动前检查**：守护进程启动时自动检查配置文件
  - 无配置时提示用户运行 setup.js
  - 避免因配置错误导致的启动失败

### ♻️ 改进

- **健康检查逻辑优化**
  - 启动等待时间：8秒 → 15秒
  - 健康检查多次重试（最多3次）
  - 进程存在但不健康时不计数为失败

- **检查频率降低**
  - 检查间隔：10秒 → 30秒
  - 减少日志量和系统资源占用

### 📝 变更

```
v1.0 → v1.1 新增文件：
+ scripts/setup.js              # 安装配置向导
+ docs/README.md               # 详细文档
+ README.md                    # 使用指南

v1.0 → v1.1 修改文件：
~ scripts/openclaw-guardian.js  # 支持配置加载、改进检测逻辑
~ SKILL.md                     # 添加安装说明
```

## v1.0 (2026-02-13)

- 初始版本
- 进程监控
- 自动重启
- 配置备份
- 自动恢复

## 安装说明

```bash
# 1. 克隆或更新
cd skills/openclaw-guardian
git pull

# 2. 运行配置向导
node scripts/setup.js

# 3. 启动守护进程
node scripts/openclaw-guardian.js
```

## 问题反馈

如有 bug 或建议，请到 GitHub 提交 Issue：
https://github.com/visionsl2/molt_skills/issues
