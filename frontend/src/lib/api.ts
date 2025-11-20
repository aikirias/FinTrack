const API_URL = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000';

interface RequestOptions extends RequestInit {
  skipJson?: boolean;
}

export async function apiRequest<T = unknown>(path: string, options: RequestOptions = {}): Promise<T> {
  const headers: HeadersInit = {
    'Content-Type': 'application/json',
    ...(options.headers || {}),
  };

  const response = await fetch(`${API_URL}${path}`, {
    ...options,
    headers,
    credentials: 'include',
  });

  if (!response.ok) {
    let detail = 'Error inesperado';
    try {
      const data = await response.json();
      detail = (data as any)?.detail ?? JSON.stringify(data);
    } catch {
      detail = await response.text();
    }
    throw new Error(detail);
  }

  if (options.skipJson) {
    return null as T;
  }

  try {
    return await response.json();
  } catch {
    return null as T;
  }
}

export const api = {
  getAccounts: () => apiRequest('/accounts/'),
  getCategories: () => apiRequest('/categories/'),
  getTransactions: () => apiRequest('/transactions/'),
  getLatestRates: () => apiRequest('/exchange-rates/latest'),
  createTransaction: (payload: Record<string, unknown>) =>
    apiRequest('/transactions/', { method: 'POST', body: JSON.stringify(payload) }),
  createCategory: (payload: Record<string, unknown>) =>
    apiRequest('/categories/', { method: 'POST', body: JSON.stringify(payload) }),
  updateCategory: (id: number, payload: Record<string, unknown>) =>
    apiRequest(`/categories/${id}`, { method: 'PATCH', body: JSON.stringify(payload) }),
  createAccount: (payload: Record<string, unknown>) =>
    apiRequest('/accounts/', { method: 'POST', body: JSON.stringify(payload) }),
  updateAccount: (id: number, payload: Record<string, unknown>) =>
    apiRequest(`/accounts/${id}`, { method: 'PATCH', body: JSON.stringify(payload) }),
};
