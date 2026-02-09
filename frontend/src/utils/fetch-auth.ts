import { useAuthStore } from '@/stores/auth'

export function createAuthenticatedHeaders(
  contentType = 'application/json'
): Record<string, string> {
  const headers: Record<string, string> = {}

  if (contentType) {
    headers['Content-Type'] = contentType
  }
  const authStore = useAuthStore()
  if (authStore.token) {
    headers['Authorization'] = `Bearer ${authStore.token}`
  }
  return headers
}

export async function authenticatedFetch(
  url: string,
  options: RequestInit = {}
): Promise<Response> {
  const headers = createAuthenticatedHeaders()
  const mergedOptions: RequestInit = {
    ...options,
    headers: {
      ...headers,
      ...(options.headers as Record<string, string>),
    },
  }
  return fetch(url, mergedOptions)
}
