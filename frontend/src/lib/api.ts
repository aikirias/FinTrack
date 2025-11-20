const API_URL = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000';

interface RequestOptions extends RequestInit {
  skipJson?: boolean;
}

type QueryValue = string | number | boolean | Array<string | number>;

const buildQuery = (params?: Record<string, QueryValue | null | undefined>) => {
  if (!params) return '';
  const search = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value === undefined || value === null || value === '') return;
    if (Array.isArray(value)) {
      value.forEach((item) => {
        if (item !== undefined && item !== null && item !== '') search.append(key, String(item));
      });
    } else {
      search.append(key, String(value));
    }
  });
  const queryString = search.toString();
  return queryString ? `?${queryString}` : '';
};

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

interface TransactionQueryParams {
  start?: string;
  end?: string;
  limit?: number;
  offset?: number;
  account_ids?: number[];
  category_ids?: number[];
  currency_code?: string;
  category_type?: 'income' | 'expense' | 'transfer';
  search?: string;
}

interface ReportQueryParams {
  start?: string;
  end?: string;
  currency?: 'ARS' | 'USD' | 'BTC';
  account_ids?: number[];
  category_ids?: number[];
  compare_previous?: boolean;
}

interface ReportCategoryParams extends ReportQueryParams {
  type?: 'income' | 'expense' | 'transfer';
}

interface BudgetQueryParams {
  month?: string;
  currency?: string;
}

interface ReprocessPayload {
  exchange_rate_id?: number;
  start?: string;
  end?: string;
}

export const api = {
  getAccounts: () => apiRequest('/accounts/'),
  getCategories: () => apiRequest('/categories/'),
  getTransactions: (params?: TransactionQueryParams) => apiRequest(`/transactions/${buildQuery(params)}`),
  getLatestRates: () => apiRequest('/exchange-rates/latest'),
  getReportSummary: (params?: ReportQueryParams) => apiRequest(`/reports/summary${buildQuery(params)}`),
  getReportTimeseries: (params?: ReportQueryParams & { interval?: 'month' | 'day' }) =>
    apiRequest(`/reports/timeseries${buildQuery(params)}`),
  getReportCategories: (params?: ReportCategoryParams) =>
    apiRequest(`/reports/categories${buildQuery(params)}`),
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
  getBudgets: (params?: BudgetQueryParams) => apiRequest(`/budgets/${buildQuery(params)}`),
  createBudget: (payload: Record<string, unknown>) =>
    apiRequest('/budgets/', { method: 'POST', body: JSON.stringify(payload) }),
  updateBudget: (id: number, payload: Record<string, unknown>) =>
    apiRequest(`/budgets/${id}`, { method: 'PATCH', body: JSON.stringify(payload) }),
  deleteBudget: (id: number) => apiRequest(`/budgets/${id}`, { method: 'DELETE', skipJson: true }),
  reprocessExchangeRates: (payload: ReprocessPayload) =>
    apiRequest('/exchange-rates/reprocess', { method: 'POST', body: JSON.stringify(payload) }),
};
