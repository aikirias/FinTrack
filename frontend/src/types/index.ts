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
