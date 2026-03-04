---
name: dingtalk-tools
description: 钉钉工具集，包含日历和日志功能。触发条件：用户说"创建日历"、"加日程"、"查日志"、"部门日志"等。
---

# 钉钉工具集

## 前提条件

1. 钉钉开放平台应用已配置
2. 已开通相关权限

## 配置信息

| 项目 | 值 |
|------|-----|
| 应用 AppKey | [APP_KEY] |
| 应用 AppSecret | [APP_SECRET] |
| 用户 OpenID | [OPEN_ID] (幻河) |
| 用户 UserID | [USER_ID] |
| 用户部门 ID | 1049669162 (智慧城市业务部) |

---

## 一、日历功能

### 权限要求
- `Calendar.Calendar.Write`

### API 端点
`https://api.dingtalk.com/v1.0/calendar/users/{openId}/calendars/primary/events`

### 创建日程

```bash
# 1. 获取 Token
curl -s "https://oapi.dingtalk.com/gettoken?appkey=[APP_KEY]&appsecret=[APP_SECRET]"

# 2. 创建日程
curl -s "https://api.dingtalk.com/v1.0/calendar/users/[OPEN_ID]/calendars/primary/events" \
  -X POST \
  -H "Content-Type: application/json" \
  -H "x-acs-dingtalk-access-token: <access_token>" \
  -d '{
    "summary": "会议标题",
    "description": "会议描述",
    "start": {"dateTime": "2026-03-03T10:00:00+08:00", "timeZone": "Asia/Shanghai"},
    "end": {"dateTime": "2026-03-03T11:00:00+08:00", "timeZone": "Asia/Shanghai"}
  }'
```

### 日期时间解析
- 用户说"明天上午10点开会" → 明天 = 当前日期 + 1 天
- 时间格式：`YYYY-MM-DDTHH:MM:SS+08:00`

---

## 二、日志功能

### 权限要求
- `qyapi_report_query` - 查询日志
- `qyapi_report_manage` - 管理日志（创建/删除，暂未调通）

### 获取日志模板

```bash
# 获取模板 ID
curl -s "https://oapi.dingtalk.com/topapi/report/template/getbyname?access_token=<token>" \
  -X POST \
  -H "Content-Type: application/json" \
  -d '{
    "template_name": "每天工作日志",
    "userid": "[USER_ID]"
  }'
```

返回：
```json
{
  "id": "1985e41421d14bafff5272e4764b6b87",
  "name": "每天工作日志",
  "fields": [
    {"field_name": "今日工作情况", "sort": 0},
    {"field_name": "需协助工作", "sort": 2},
    {"field_name": "明日工作计划", "sort": 3}
  ]
}
```

### 查询个人日志

```bash
curl -s "https://oapi.dingtalk.com/topapi/report/list?access_token=<token>" \
  -X POST \
  -H "Content-Type: application/json" \
  -d '{
    "userid": "[USER_ID]",
    "start_time": 1764556800000,
    "end_time": 1767225600000,
    "cursor": 0,
    "size": 10
  }'
```

参数说明：
- `start_time`/`end_time`：时间戳（毫秒），可以用 `date +%s000` 获取
- `cursor`：分页游标
- `size`：每页数量

### 查询部门日志

```bash
curl -s "https://oapi.dingtalk.com/topapi/report/list?access_token=<token>" \
  -X POST \
  -H "Content-Type: application/json" \
  -d '{
    "userid": "[USER_ID]",
    "dept_id": "1049669162",
    "start_time": 1764556800000,
    "end_time": 1767225600000,
    "cursor": 0,
    "size": 10
  }'
```

### 时间戳计算

```bash
# 获取当前时间戳（毫秒）
date +%s000

# 获取指定日期时间戳
date -j -f "%Y-%m-%d" "2024-12-01" +%s000
```

---

## 注意事项

1. 日历使用 OpenID，日志使用 UserID
2. Token 有 2 小时有效期
3. 创建日志接口暂未调通（返回 400001 系统错误）

## 维护

- 参考文档：https://open.dingtalk.com/document/
