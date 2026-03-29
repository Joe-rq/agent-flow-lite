# Environment Contract

## Runtime Requirements

- Node.js: `^20.19.0 || >=22.12.0`
- Python: `>=3.11`
- uv: backend 依赖与运行入口

## Backend Environment Variables

复制 `backend/.env.example` 为 `backend/.env`，至少补这些键：

- `DEEPSEEK_API_KEY`
- `DEEPSEEK_API_BASE`
- `DEEPSEEK_MODEL`
- `SILICONFLOW_API_KEY`
- `SILICONFLOW_API_BASE`
- `EMBEDDING_MODEL`
- `ADMIN_EMAIL`
- `CORS_ORIGINS`

## Operational Notes

- 修改 `EMBEDDING_MODEL` 后，现有 ChromaDB 索引可能与新维度不兼容
- `backend/data/` 为运行时数据，不应被代码逻辑假定为稳定初始状态
- 本地启动前需要分别准备 frontend 依赖和 backend 虚拟环境