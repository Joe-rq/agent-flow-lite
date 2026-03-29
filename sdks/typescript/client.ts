/**
 * Agent Flow Client - TypeScript SDK
 * 基于 OpenAPI 规范生成的 API 客户端
 */

import type { paths } from './schema';

type Paths = keyof paths;
type Methods<P extends Paths> = keyof paths[P];
type Operation<P extends Paths, M extends Methods<P>> = paths[P][M];

const DEFAULT_BASE_URL = 'http://localhost:8000';

export class AgentFlowClient {
  private baseUrl: string;
  private token: string | null = null;

  constructor(options?: { baseUrl?: string; token?: string }) {
    this.baseUrl = options?.baseUrl ?? DEFAULT_BASE_URL;
    if (options?.token) {
      this.token = options.token;
    }
  }

  setToken(token: string): void {
    this.token = token;
  }

  private getHeaders(): Record<string, string> {
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
    };
    if (this.token) {
      headers['Authorization'] = `Bearer ${this.token}`;
    }
    return headers;
  }

  async get<T>(path: string): Promise<T> {
    const response = await fetch(`${this.baseUrl}${path}`, {
      method: 'GET',
      headers: this.getHeaders(),
    });
    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: response.statusText }));
      throw new ApiError(response.status, error.detail || 'Request failed');
    }
    return response.json();
  }

  async post<T>(path: string, body?: unknown): Promise<T> {
    const response = await fetch(`${this.baseUrl}${path}`, {
      method: 'POST',
      headers: this.getHeaders(),
      body: body ? JSON.stringify(body) : undefined,
    });
    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: response.statusText }));
      throw new ApiError(response.status, error.detail || 'Request failed');
    }
    return response.json();
  }

  async put<T>(path: string, body: unknown): Promise<T> {
    const response = await fetch(`${this.baseUrl}${path}`, {
      method: 'PUT',
      headers: this.getHeaders(),
      body: JSON.stringify(body),
    });
    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: response.statusText }));
      throw new ApiError(response.status, error.detail || 'Request failed');
    }
    return response.json();
  }

  async delete<T>(path: string): Promise<T> {
    const response = await fetch(`${this.baseUrl}${path}`, {
      method: 'DELETE',
      headers: this.getHeaders(),
    });
    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: response.statusText }));
      throw new ApiError(response.status, error.detail || 'Request failed');
    }
    return response.json();
  }

  // === Health ===
  async healthCheck(): Promise<{ status: string }> {
    return this.get('/health');
  }

  // === Auth ===
  async login(email: string): Promise<{ token: string; user: { id: number; email: string; role: string } }> {
    const result = await this.post<{ token: string; user: { id: number; email: string; role: string } }>('/api/v1/auth/login', { email });
    if (result.token) {
      this.setToken(result.token);
    }
    return result;
  }

  async getMe(): Promise<{ id: number; email: string }> {
    return this.get('/api/v1/auth/me');
  }

  // === Workflows ===
  async listWorkflows(): Promise<{ id: number; name: string; description: string | null; created_at: string }[]> {
    return this.get('/api/v1/workflows');
  }

  async getWorkflow(id: number): Promise<{ id: number; name: string; description: string | null }> {
    return this.get(`/api/v1/workflows/${id}`);
  }

  async executeWorkflow(id: number, input?: Record<string, unknown>): Promise<{ execution_id: string; status: string }> {
    return this.post(`/api/v1/workflows/${id}/execute`, { input });
  }

  // === Skills ===
  async listSkills(): Promise<{ name: string; description: string }[]> {
    return this.get('/api/v1/skills');
  }

  async runSkill(name: string, params?: Record<string, unknown>): Promise<unknown> {
    return this.post(`/api/v1/skills/${name}/run`, { params });
  }

  // === Chat ===
  async createChatSession(): Promise<{ session_id: string }> {
    return this.post('/api/v1/chat/sessions');
  }

  async chatCompletions(sessionId: string, message: string): Promise<unknown> {
    return this.post('/api/v1/chat/completions', { session_id: sessionId, message });
  }

  // === Knowledge ===
  async listKnowledge(): Promise<unknown> {
    return this.get('/api/v1/knowledge');
  }

  async searchKnowledge(kbId: number, query: string): Promise<unknown> {
    return this.post(`/api/v1/knowledge/${kbId}/search`, { query });
  }
}

export class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
    this.name = 'ApiError';
  }
}

export default AgentFlowClient;
