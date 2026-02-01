"""
DeepSeek API 测试脚本
用法: uv run python test_deepseek.py
"""

import httpx
from app.core.config import get_settings


def test_deepseek_api():
    """测试 DeepSeek API 连通性"""
    settings = get_settings()
    
    if not settings.deepseek_api_key or settings.deepseek_api_key == "your-api-key-here":
        print("❌ 错误: 请在 backend/.env 中设置有效的 DEEPSEEK_API_KEY")
        print("获取 API Key: https://platform.deepseek.com/api_keys")
        return False
    
    print(f"=== DeepSeek API 测试 ===")
    print(f"模型: {settings.deepseek_model}")
    print(f"API Base: {settings.deepseek_api_base}")
    print()
    
    # 发送测试请求
    url = f"{settings.deepseek_api_base}/chat/completions"
    headers = {
        "Authorization": f"Bearer {settings.deepseek_api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": settings.deepseek_model,
        "messages": [
            {"role": "user", "content": "Hello, please respond briefly."}
        ],
        "max_tokens": 100
    }
    
    try:
        with httpx.Client(timeout=30.0) as client:
            response = client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            
            data = response.json()
            message = data["choices"][0]["message"]["content"]
            
            print("✅ API 连通性测试成功!")
            print(f"\n回复: {message}")
            return True
            
    except httpx.HTTPStatusError as e:
        print(f"❌ HTTP 错误: {e.response.status_code} - {e.response.text}")
        return False
    except Exception as e:
        print(f"❌ 请求失败: {e}")
        return False


if __name__ == "__main__":
    success = test_deepseek_api()
    exit(0 if success else 1)
