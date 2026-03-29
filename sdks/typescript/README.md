# Agent Flow Client - TypeScript SDK

TypeScript SDK for Agent Flow Lite API.

## 安装

将 `sdks/typescript/` 目录复制到项目中:

```
sdks/typescript/
├── README.md     # 本文档
├── client.ts     # SDK 客户端
└── schema.d.ts   # OpenAPI 类型定义
```

## 快速开始

```typescript
import { AgentFlowClient } from './client';

// 创建客户端
const client = new AgentFlowClient({ baseUrl: 'http://localhost:8000' });

// 健康检查
const health = await client.healthCheck();
console.log(health); // { status: 'healthy' }

// 登录 (自动设置 token)
const login = await client.login('user@example.com');
console.log(login.user.email);

// 获取工作流列表
const workflows = await client.listWorkflows();
console.log(workflows);

// 获取技能列表
const skills = await client.listSkills();
console.log(skills);
```

## 主要 API

| 方法 | 描述 |
|------|------|
| `healthCheck()` | 健康检查 |
| `login(email)` | 登录 (自动设置 token) |
| `getMe()` | 获取当前用户 |
| `listWorkflows()` | 工作流列表 |
| `getWorkflow(id)` | 获取工作流 |
| `executeWorkflow(id, input)` | 执行工作流 |
| `listSkills()` | 技能列表 |
| `runSkill(name, params)` | 运行技能 |
| `createChatSession()` | 创建聊天会话 |
| `chatCompletions(sessionId, message)` | 发送消息 |
| `listKnowledge()` | 知识库列表 |
| `searchKnowledge(kbId, query)` | 搜索知识库 |

## 认证

登录后自动设置 token，也可手动设置:

```typescript
const client = new AgentFlowClient();
client.setToken('your-token');
```

## 错误处理

```typescript
import { ApiError } from './client';

try {
  const result = await client.getWorkflow(123);
} catch (error) {
  if (error instanceof ApiError) {
    console.error(`API 错误: ${error.status} - ${error.message}`);
  }
}
```

## 重新生成类型

```bash
# 确保后端运行
cd backend && uv run uvicorn main:app --reload

# 生成 TypeScript 类型
npx openapi-typescript http://localhost:8000/openapi.json -o sdks/typescript/schema.d.ts
```
