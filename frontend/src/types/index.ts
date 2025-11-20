export interface User {
  id: number;
  email: string;
  timezone: string;
  is_active: boolean;
}

export interface Account {
  id: number;
  name: string;
  currency_code: string;
  description?: string | null;
  is_archived: boolean;
}

export interface Category {
  id: number;
  name: string;
  type: 'income' | 'expense' | 'transfer';
  parent_id?: number | null;
  is_archived?: boolean;
  is_default?: boolean;
  children?: Category[];
}

export interface Transaction {
  id: number;
  transaction_date: string;
  account_id: number;
  category_id: number | null;
  subcategory_id: number | null;
  currency_code: string;
  amount_original: string;
  amount_ars: string;
  amount_usd: string;
  amount_btc: string;
  notes?: string | null;
  rate_type: string;
}

export interface ExchangeRate {
  id: number;
  usd_ars_oficial: string;
  usd_ars_blue: string | null;
  btc_usd: string;
  btc_ars: string;
  effective_date: string;
}

export interface ReportTotals {
  income: string;
  expense: string;
  transfers: string;
  balance: string;
}

export interface ReportSummaryResponse {
  currency: 'ARS' | 'USD' | 'BTC';
  range: {
    start: string | null;
    end: string | null;
  };
  totals: ReportTotals;
  previous_totals: ReportTotals | null;
  budget_totals: ReportBudgetTotals | null;
}

export interface ReportTimeseriesPoint {
  period: string;
  income: string;
  expense: string;
}

export interface ReportTimeseriesResponse {
  currency: 'ARS' | 'USD' | 'BTC';
  interval: 'month' | 'day';
  points: ReportTimeseriesPoint[];
}

export interface ReportCategoryEntry {
  category_id: number | null;
  name: string;
  total: string;
  type: 'income' | 'expense' | 'transfer';
}

export interface ReportCategoryResponse {
  currency: 'ARS' | 'USD' | 'BTC';
  entries: ReportCategoryEntry[];
}

export interface ReportBudgetTotals {
  income: string;
  expense: string;
}

export interface BudgetItem {
  id: number;
  category_id: number;
  amount: string;
}

export interface Budget {
  id: number;
  month: string;
  currency_code: string;
  name?: string | null;
  items: BudgetItem[];
}

export interface ExchangeRateReprocessResult {
  processed: number;
  updated: number;
  skipped: number;
}
