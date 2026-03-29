# Agent Flow Client - Python SDK

Python SDK for Agent Flow Lite API.

## 安装

将 `sdks/python/client.py` 复制到项目中即可使用。

## 快速开始

```python
from client import AgentFlowClient

# 创建客户端
client = AgentFlowClient(base_url="http://localhost:8000")

# 健康检查
health = client.health_check()
print(health)  # {'status': 'healthy'}

# 登录 (自动设置 token)
login_result = client.login('user@example.com')
print(login_result['user']['email'])

# 获取工作流列表
workflows = client.list_workflows()
print(workflows)

# 获取技能列表
skills = client.list_skills()
print(skills)
```

## 主要 API

| 方法 | 描述 |
|------|------|
| `health_check()` | 健康检查 |
| `login(email)` | 登录 (自动设置 token) |
| `get_me()` | 获取当前用户 |
| `list_workflows()` | 工作流列表 |
| `get_workflow(id)` | 获取工作流 |
| `execute_workflow(id, input)` | 执行工作流 |
| `list_skills()` | 技能列表 |
| `run_skill(name, params)` | 运行技能 |
| `create_chat_session()` | 创建聊天会话 |
| `chat_completions(session_id, message)` | 发送消息 |
| `list_knowledge()` | 知识库列表 |
| `search_knowledge(kb_id, query)` | 搜索知识库 |

## 认证

登录后自动设置 token，也可手动设置:

```python
client = AgentFlowClient()
client.set_token("your-token")
```

## 错误处理

```python
from client import ApiError

try:
    result = client.get_workflow(123)
except ApiError as e:
    print(f"API 错误: {e.status} - {e.message}")
```

## 文件结构

```
sdks/python/
├── README.md     # 本文档
└── client.py     # SDK 客户端
```
