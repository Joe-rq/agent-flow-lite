"""
Agent Flow Client - Python SDK
基于 OpenAPI 规范生成的 API 客户端
"""

import json
from dataclasses import dataclass
from typing import Any, Optional
from urllib.request import Request, urlopen
from urllib.error import HTTPError

DEFAULT_BASE_URL = "http://localhost:8000"


@dataclass
class ApiError(Exception):
    """API 错误"""
    status: int
    message: str

    def __str__(self) -> str:
        return f"ApiError({self.status}): {self.message}"


class AgentFlowClient:
    """Agent Flow Lite API 客户端"""

    def __init__(
        self,
        base_url: str = DEFAULT_BASE_URL,
        token: Optional[str] = None,
    ):
        self.base_url = base_url.rstrip("/")
        self.token = token

    def set_token(self, token: str) -> None:
        """设置认证令牌"""
        self.token = token

    def _get_headers(self) -> dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    def _request(
        self,
        method: str,
        path: str,
        body: Optional[Any] = None,
    ) -> Any:
        url = f"{self.base_url}{path}"
        headers = self._get_headers()
        data = json.dumps(body).encode() if body else None

        request = Request(url, data=data, headers=headers, method=method)

        try:
            with urlopen(request) as response:
                return json.loads(response.read().decode())
        except HTTPError as e:
            error_body = e.read().decode()
            try:
                error_data = json.loads(error_body)
                message = error_data.get("detail", error_body)
            except json.JSONDecodeError:
                message = error_body
            raise ApiError(e.code, message)

    def get(self, path: str) -> Any:
        """GET 请求"""
        return self._request("GET", path)

    def post(self, path: str, body: Optional[Any] = None) -> Any:
        """POST 请求"""
        return self._request("POST", path, body)

    def put(self, path: str, body: Any) -> Any:
        """PUT 请求"""
        return self._request("PUT", path, body)

    def delete(self, path: str) -> Any:
        """DELETE 请求"""
        return self._request("DELETE", path)

    # === Health ===
    def health_check(self) -> dict[str, str]:
        """健康检查"""
        return self.get("/health")

    # === Auth ===
    def login(self, email: str) -> dict[str, Any]:
        """
        登录

        Args:
            email: 用户邮箱

        Returns:
            包含 token 和用户信息的字典
        """
        result = self.post("/api/v1/auth/login", {"email": email})
        # 自动设置 token
        if "token" in result:
            self.set_token(result["token"])
        return result

    def get_me(self) -> dict[str, Any]:
        """获取当前用户信息"""
        return self.get("/api/v1/auth/me")

    # === Workflows ===
    def list_workflows(self) -> list[dict[str, Any]]:
        """获取工作流列表"""
        return self.get("/api/v1/workflows")

    def get_workflow(self, workflow_id: int) -> dict[str, Any]:
        """获取单个工作流"""
        return self.get(f"/api/v1/workflows/{workflow_id}")

    def execute_workflow(
        self,
        workflow_id: int,
        input_data: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        """执行工作流"""
        return self.post(
            f"/api/v1/workflows/{workflow_id}/execute",
            {"input": input_data} if input_data else None,
        )

    # === Skills ===
    def list_skills(self) -> list[dict[str, str]]:
        """获取技能列表"""
        return self.get("/api/v1/skills")

    def run_skill(
        self,
        name: str,
        params: Optional[dict[str, Any]] = None,
    ) -> Any:
        """运行技能"""
        return self.post(f"/api/v1/skills/{name}/run", {"params": params})

    # === Chat ===
    def create_chat_session(self) -> dict[str, str]:
        """创建聊天会话"""
        return self.post("/api/v1/chat/sessions")

    def chat_completions(
        self,
        session_id: str,
        message: str,
    ) -> Any:
        """发送聊天消息"""
        return self.post(
            "/api/v1/chat/completions",
            {"session_id": session_id, "message": message},
        )

    # === Knowledge ===
    def list_knowledge(self) -> Any:
        """获取知识库列表"""
        return self.get("/api/v1/knowledge")

    def search_knowledge(
        self,
        kb_id: int,
        query: str,
    ) -> Any:
        """搜索知识库"""
        return self.post(
            f"/api/v1/knowledge/{kb_id}/search",
            {"query": query},
        )
