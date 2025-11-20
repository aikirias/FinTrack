'use client';

import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { api } from '@/lib/api';
import type { Account, Category, Transaction } from '@/types';

const arsFormatter = new Intl.NumberFormat('es-AR', { style: 'currency', currency: 'ARS' });
const usdFormatter = new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' });
const btcFormatter = new Intl.NumberFormat('en-US', { minimumFractionDigits: 8, maximumFractionDigits: 8 });
type SortField = 'date' | 'amount' | 'category' | 'type';
const PAGE_SIZE = 50;

export default function TransactionsPage() {
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadingPage, setLoadingPage] = useState(false);
  const [sortField, setSortField] = useState<SortField>('date');
  const [sortDirection, setSortDirection] = useState<'asc' | 'desc'>('desc');
  const [filters, setFilters] = useState({
    accountId: '',
    currency: '',
    type: '',
    search: '',
    startDate: '',
    endDate: '',
  });
  const filtersHash = useMemo(() => JSON.stringify(filters), [filters]);
  const [hasMore, setHasMore] = useState(true);
  const [dataReady, setDataReady] = useState(false);
  const sentinelRef = useRef<HTMLDivElement | null>(null);
  const filtersRef = useRef(filters);
  const offsetRef = useRef(0);
  const loadingPageRef = useRef(false);

  useEffect(() => {
    filtersRef.current = filters;
  }, [filters]);

  useEffect(() => {
    let active = true;
    (async () => {
      setLoading(true);
      try {
        const [cats, accts] = await Promise.all([api.getCategories(), api.getAccounts()]);
        if (!active) return;
        setCategories(cats as Category[]);
        setAccounts(accts as Account[]);
        setDataReady(true);
      } catch (error) {
        console.error(error);
        if (!active) return;
        setDataReady(true);
      } finally {
        if (!active) return;
      }
    })();
    return () => {
      active = false;
    };
  }, []);

  const fetchTransactions = useCallback(
    async (replace = false) => {
      if (loadingPageRef.current) return;
      loadingPageRef.current = true;
      setLoadingPage(true);
      try {
        const currentFilters = filtersRef.current;
        const effectiveOffset = replace ? 0 : offsetRef.current;
        const params = {
          limit: PAGE_SIZE,
          offset: effectiveOffset,
          start: currentFilters.startDate ? `${currentFilters.startDate}T00:00:00Z` : undefined,
          end: currentFilters.endDate ? `${currentFilters.endDate}T23:59:59Z` : undefined,
          account_ids: currentFilters.accountId ? [Number(currentFilters.accountId)] : undefined,
          currency_code: currentFilters.currency || undefined,
          category_type: currentFilters.type || undefined,
          search: currentFilters.search || undefined,
        };
        const txs = (await api.getTransactions(params)) as Transaction[];
        offsetRef.current = effectiveOffset + txs.length;
        setTransactions((prev) => (replace ? txs : [...prev, ...txs]));
        setHasMore(txs.length === PAGE_SIZE);
      } catch (error) {
        console.error(error);
        setHasMore(false);
      } finally {
        setLoading(false);
        loadingPageRef.current = false;
        setLoadingPage(false);
      }
    },
    []
  );

  useEffect(() => {
    if (!dataReady) return;
    offsetRef.current = 0;
    setTransactions([]);
    setHasMore(true);
    setLoading(true);
    fetchTransactions(true);
  }, [dataReady, filtersHash, fetchTransactions]);

  useEffect(() => {
    if (!sentinelRef.current) return;
    const target = sentinelRef.current;
    const observer = new IntersectionObserver((entries) => {
      const entry = entries[0];
      if (entry.isIntersecting && hasMore && !loadingPageRef.current) {
        fetchTransactions();
      }
    });
    observer.observe(target);
    return () => {
      observer.disconnect();
    };
  }, [hasMore, fetchTransactions]);

  const categoryMap = useMemo(() => {
    const map: Record<number, { name: string; type: string | undefined }> = {};
    const walk = (nodes: Category[]) => {
      nodes.forEach((cat) => {
        map[cat.id] = { name: cat.name, type: cat.type };
        if (cat.children) walk(cat.children);
      });
    };
    walk(categories);
    return map;
  }, [categories]);

  const enhancedTransactions = useMemo(() => {
    const accountLookup: Record<number, Account> = {};
    accounts.forEach((acc) => {
      accountLookup[acc.id] = acc;
    });
    return transactions.map((tx) => {
      const cat = tx.category_id ? categoryMap[tx.category_id] : undefined;
      const account = accountLookup[tx.account_id];
      return {
        ...tx,
        category_name: cat?.name ?? 'Sin categoría',
        category_type: cat?.type ?? 'Sin tipo',
        account_name: account?.name ?? 'Cuenta',
        account_currency: account?.currency_code ?? tx.currency_code,
      };
    });
  }, [transactions, categoryMap, accounts]);

  const sortedTransactions = useMemo(() => {
    const data = [...enhancedTransactions];
    data.sort((a, b) => {
      let result = 0;
      if (sortField === 'date') {
        result = new Date(a.transaction_date).getTime() - new Date(b.transaction_date).getTime();
      } else if (sortField === 'amount') {
        result = parseFloat(a.amount_original) - parseFloat(b.amount_original);
      } else if (sortField === 'category') {
        result = a.category_name.localeCompare(b.category_name);
      } else if (sortField === 'type') {
        result = a.category_type.localeCompare(b.category_type);
      }
      return sortDirection === 'asc' ? result : -result;
    });
    return data;
  }, [enhancedTransactions, sortField, sortDirection]);

  const handleSort = (field: SortField) => {
    if (field === sortField) {
      setSortDirection((prev) => (prev === 'asc' ? 'desc' : 'asc'));
    } else {
      setSortField(field);
      setSortDirection(field === 'date' ? 'desc' : 'asc');
    }
  };

  const formatOriginalAmount = (tx: Transaction) => {
    const value = parseFloat(tx.amount_original);
    if (tx.currency_code === 'USD') return usdFormatter.format(value);
    if (tx.currency_code === 'BTC') return `${btcFormatter.format(value)} BTC`;
    return arsFormatter.format(value);
  };

  const summary = useMemo(() => {
    return enhancedTransactions.reduce(
      (acc, tx) => {
        const catType = tx.category_type;
        const amountArs = parseFloat(tx.amount_ars);
        if (catType === 'income') acc.income += amountArs;
        else if (catType === 'expense') acc.expense += amountArs;
        return acc;
      },
      { income: 0, expense: 0 }
    );
  }, [enhancedTransactions]);

  if (loading) {
    return <div className="text-slate-300">Cargando movimientos...</div>;
  }

  return (
    <div>
      <div className="mb-6 space-y-3">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <h1 className="text-2xl font-semibold">Movimientos</h1>
            <p className="text-sm text-slate-400">
              Mostrando {sortedTransactions.length} movimientos
              {hasMore ? ' (hay más disponibles)' : ''}
            </p>
          </div>
          <button
            type="button"
            onClick={() => setFilters({ accountId: '', currency: '', type: '', search: '', startDate: '', endDate: '' })}
            className="rounded-full border border-white/10 px-4 py-2 text-sm text-slate-200 hover:border-white/40 hover:bg-white/10"
          >
            Limpiar filtros
          </button>
        </div>
        <div className="grid gap-3 lg:grid-cols-4">
          <input
            value={filters.search}
            onChange={(e) => setFilters((prev) => ({ ...prev, search: e.target.value }))}
            placeholder="Buscar por categoría, cuenta o nota"
            className="rounded-xl border border-white/10 bg-black/20 px-4 py-2 text-sm"
          />
          <select
            value={filters.accountId}
            onChange={(e) => setFilters((prev) => ({ ...prev, accountId: e.target.value }))}
            className="rounded-xl border border-white/10 bg-black/20 px-4 py-2 text-sm"
          >
            <option value="">Todas las cuentas</option>
            {accounts.map((account) => (
              <option key={account.id} value={account.id}>
                {account.name}
              </option>
            ))}
          </select>
          <select
            value={filters.currency}
            onChange={(e) => setFilters((prev) => ({ ...prev, currency: e.target.value }))}
            className="rounded-xl border border-white/10 bg-black/20 px-4 py-2 text-sm"
          >
            <option value="">Todas las monedas</option>
            <option value="ARS">ARS</option>
            <option value="USD">USD</option>
            <option value="BTC">BTC</option>
          </select>
          <select
            value={filters.type}
            onChange={(e) => setFilters((prev) => ({ ...prev, type: e.target.value }))}
            className="rounded-xl border border-white/10 bg-black/20 px-4 py-2 text-sm"
          >
            <option value="">Todo tipo</option>
            <option value="income">Ingreso</option>
            <option value="expense">Gasto</option>
          </select>
          <input
            type="date"
            value={filters.startDate}
            onChange={(e) => setFilters((prev) => ({ ...prev, startDate: e.target.value }))}
            className="rounded-xl border border-white/10 bg-black/20 px-4 py-2 text-sm"
          />
          <input
            type="date"
            value={filters.endDate}
            onChange={(e) => setFilters((prev) => ({ ...prev, endDate: e.target.value }))}
            className="rounded-xl border border-white/10 bg-black/20 px-4 py-2 text-sm"
          />
        </div>
        <div className="grid gap-4 sm:grid-cols-2">
          <div className="rounded-2xl border border-white/5 bg-white/5 p-4">
            <p className="text-xs uppercase tracking-widest text-slate-400">Ingresos filtrados (ARS)</p>
            <p className="text-2xl font-semibold text-emerald-200">{arsFormatter.format(summary.income)}</p>
          </div>
          <div className="rounded-2xl border border-white/5 bg-white/5 p-4">
            <p className="text-xs uppercase tracking-widest text-slate-400">Gastos filtrados (ARS)</p>
            <p className="text-2xl font-semibold text-rose-200">{arsFormatter.format(Math.abs(summary.expense))}</p>
          </div>
        </div>
      </div>
      <div className="overflow-auto rounded-2xl border border-white/5">
        <table className="min-w-full text-sm">
          <thead className="bg-white/5 text-left text-xs uppercase text-slate-400">
            <tr>
              <th className="px-4 py-3">
                <button type="button" onClick={() => handleSort('date')} className="flex items-center gap-1">
                  Fecha
                  {sortField === 'date' && <span>{sortDirection === 'asc' ? '↑' : '↓'}</span>}
                </button>
              </th>
              <th className="px-4 py-3">
                <button type="button" onClick={() => handleSort('category')} className="flex items-center gap-1">
                  Categoría
                  {sortField === 'category' && <span>{sortDirection === 'asc' ? '↑' : '↓'}</span>}
                </button>
              </th>
              <th className="px-4 py-3">
                <button type="button" onClick={() => handleSort('type')} className="flex items-center gap-1">
                  Tipo
                  {sortField === 'type' && <span>{sortDirection === 'asc' ? '↑' : '↓'}</span>}
                </button>
              </th>
              <th className="px-4 py-3">Moneda</th>
              <th className="px-4 py-3">
                <button type="button" onClick={() => handleSort('amount')} className="flex items-center gap-1">
                  Monto
                  {sortField === 'amount' && <span>{sortDirection === 'asc' ? '↑' : '↓'}</span>}
                </button>
              </th>
              <th className="px-4 py-3">Notas</th>
            </tr>
          </thead>
          <tbody>
            {sortedTransactions.map((tx) => (
              <tr key={tx.id} className="border-t border-white/5">
                <td className="px-4 py-3 text-slate-300">
                  {new Date(tx.transaction_date).toLocaleString('es-AR')}
                </td>
                <td className="px-4 py-3 text-slate-200">{tx.category_name}</td>
                <td className="px-4 py-3 text-slate-300 capitalize">{tx.category_type}</td>
                <td className="px-4 py-3 text-slate-300">{tx.currency_code}</td>
                <td className="px-4 py-3 font-semibold text-slate-100">{formatOriginalAmount(tx)}</td>
                <td className="px-4 py-3 text-slate-400">{tx.notes ?? '-'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {loadingPage && (
        <div className="py-3 text-center text-slate-400">Cargando más movimientos...</div>
      )}
      <div ref={sentinelRef} className="h-6" />
    </div>
  );
}
