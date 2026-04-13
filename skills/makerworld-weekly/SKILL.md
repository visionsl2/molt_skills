---
name: makerworld-weekly
description: 每周二上午11点自动获取MakerWorld热门3D打印模型TOP10并发送到钉钉。触发方式：用户说"做3D打印热门模型报告"、"MakerWorld热门模型"、"3D打印模型报告"、"做热门模型简报"等。
---

# MakerWorld 每周简报

## 功能
- 每周二上午11:00自动执行（或手动触发）
- 采集MakerWorld热门模型榜单TOP10
- 发送完整简报到用户钉钉

## 操作流程

### 1. 打开浏览器
使用 browser 工具打开：`https://makerworld.com.cn/zh`

### 2. 登录（如需要）
需要用户登录账号

### 3. 获取热门榜单
- 截图热门模型页面
- 记录模型名称、作者、热度数、下载数

### 4. 整理完整简报
**必须发送完整版，格式如下：**
```
🔥 MakerWorld 热门3D打印模型 TOP 10

**数据来源：** MakerWorld 热门榜单 | **采集时间：** YYYY-MM-DD

---

## 1️⃣ 模型名
- **说明：** 模型描述
- **作者：** 作者名
- **热度：** ❤️ 热度数 | ⬇️ 下载数
- **链接：** https://makerworld.com.cn/zh/models/xxx

---

## 2️⃣ 模型名
...（重复以上格式直到10个）

---

### 5. 发送钉钉
使用 message 工具发送到用户钉钉：
- channel: dingtalk
- target: 016905440029103298
- **必须发送完整简报，包含所有10个模型的详细信息**

### 6. 保存报告
- 保存到 ~/openclaw_doc/reports/makerworld_hot_YYYYMMDD.md
- 截图保存到 ~/openclaw_doc/browser_screenshots/
