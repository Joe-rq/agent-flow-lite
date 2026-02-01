# DeepSeek API 配置学习笔记

## 完成的工作
- 创建了 `backend/.env.example` 模板文件，包含 DeepSeek API 配置说明
- 创建了 `backend/app/core/config.py`，使用 pydantic-settings 加载环境变量
- 创建了 `backend/.env` 示例配置文件
- 更新了 `.gitignore` 确保 `.env` 文件不被提交
- 添加了必要的依赖：pydantic-settings, httpx
- 创建了 `test_deepseek.py` 测试脚本

## 关键配置
```python
# config.py 使用 pydantic-settings
class Settings(BaseSettings):
    deepseek_api_key: str = Field(default="")
    deepseek_model: str = Field(default="deepseek-chat")
    deepseek_api_base: str = Field(default="https://api.deepseek.com")
```

## API 端点验证
- API Base URL: `https://api.deepseek.com/chat/completions`
- 使用的模型: `deepseek-chat`
- API 格式兼容 OpenAI 标准

## 注意事项
1. API Key 从环境变量加载，不会硬编码在代码中
2. .env 文件被正确添加到 .gitignore
3. 测试脚本会检查 key 是否为示例值并给出提示

## 待办
- 用户需要从 https://platform.deepseek.com/api_keys 获取真实的 API Key
- 配置完成后可解锁 Task 7
