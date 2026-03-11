'use client';

import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { api } from '@/lib/api';
import type { Account, Category, Transaction } from '@/types';

const arsFormatter = new Intl.NumberFormat('es-AR', { style: 'currency', currency: 'ARS' });
const usdFormatter = new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' });
const btcFormatter = new Intl.NumberFormat('en-US', { minimumFractionDigits: 8, maximumFractionDigits: 8 });
type SortField = 'date' | 'amount' | 'category' | 'type';
const PAGE_SIZE = 50;

interface EditForm {
  transaction_date: string;
  amount_original: string;
  notes: string;
  category_id: string;
}

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
  const [totalCount, setTotalCount] = useState(0);
  const [dataReady, setDataReady] = useState(false);
  const sentinelRef = useRef<HTMLDivElement | null>(null);
  const filtersRef = useRef(filters);
  const offsetRef = useRef(0);
  const loadingPageRef = useRef(false);

  // Edit modal state
  const [editingTx, setEditingTx] = useState<Transaction | null>(null);
  const [editForm, setEditForm] = useState<EditForm>({ transaction_date: '', amount_original: '', notes: '', category_id: '' });
  const [editSaving, setEditSaving] = useState(false);
  const [editError, setEditError] = useState<string | null>(null);

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
    return () => { active = false; };
  }, []);

  const fetchTransactions = useCallback(async (replace = false) => {
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
      const { data, total } = await api.getTransactionsWithTotal(params);
      const txs = data as Transaction[];
      offsetRef.current = effectiveOffset + txs.length;
      if (replace) setTotalCount(total);
      setTransactions((prev) => (replace ? txs : [...prev, ...txs]));
      setHasMore(offsetRef.current < total);
    } catch (error) {
      console.error(error);
      setHasMore(false);
    } finally {
      setLoading(false);
      loadingPageRef.current = false;
      setLoadingPage(false);
    }
  }, []);

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
    return () => { observer.disconnect(); };
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

  const topLevelCategories = useMemo(() => categories.filter((c) => !c.parent_id && !c.is_archived), [categories]);

  const enhancedTransactions = useMemo(() => {
    const accountLookup: Record<number, Account> = {};
    accounts.forEach((acc) => { accountLookup[acc.id] = acc; });
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
      if (sortField === 'date') result = new Date(a.transaction_date).getTime() - new Date(b.transaction_date).getTime();
      else if (sortField === 'amount') result = parseFloat(a.amount_original) - parseFloat(b.amount_original);
      else if (sortField === 'category') result = a.category_name.localeCompare(b.category_name);
      else if (sortField === 'type') result = a.category_type.localeCompare(b.category_type);
      return sortDirection === 'asc' ? result : -result;
    });
    return data;
  }, [enhancedTransactions, sortField, sortDirection]);

  const handleSort = (field: SortField) => {
    if (field === sortField) setSortDirection((prev) => (prev === 'asc' ? 'desc' : 'asc'));
    else { setSortField(field); setSortDirection(field === 'date' ? 'desc' : 'asc'); }
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
        const amountArs = parseFloat(tx.amount_ars);
        if (tx.category_type === 'income') acc.income += amountArs;
        else if (tx.category_type === 'expense') acc.expense += amountArs;
        return acc;
      },
      { income: 0, expense: 0 }
    );
  }, [enhancedTransactions]);

  const openEdit = (tx: Transaction) => {
    setEditingTx(tx);
    setEditError(null);
    const d = new Date(tx.transaction_date);
    const pad = (n: number) => String(n).padStart(2, '0');
    const local = `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`;
    setEditForm({
      transaction_date: local,
      amount_original: tx.amount_original,
      notes: tx.notes ?? '',
      category_id: tx.category_id != null ? String(tx.category_id) : '',
    });
  };

  const handleEditSave = async () => {
    if (!editingTx) return;
    if (!editForm.amount_original || parseFloat(editForm.amount_original) <= 0) {
      setEditError('El monto debe ser mayor a 0');
      return;
    }
    setEditSaving(true);
    setEditError(null);
    try {
      const payload: Record<string, unknown> = {
        amount_original: editForm.amount_original,
        notes: editForm.notes || null,
        transaction_date: editForm.transaction_date ? new Date(editForm.transaction_date).toISOString() : undefined,
        category_id: editForm.category_id ? Number(editForm.category_id) : null,
      };
      const updated = (await api.updateTransaction(editingTx.id, payload)) as Transaction;
      setTransactions((prev) => prev.map((tx) => (tx.id === updated.id ? updated : tx)));
      setEditingTx(null);
    } catch (err) {
      setEditError((err as Error).message);
    } finally {
      setEditSaving(false);
    }
  };

  const handleDelete = async (tx: Transaction) => {
    if (!confirm(`¿Eliminar movimiento de ${formatOriginalAmount(tx)}?`)) return;
    try {
      await api.deleteTransaction(tx.id);
      setTransactions((prev) => prev.filter((t) => t.id !== tx.id));
      offsetRef.current = Math.max(0, offsetRef.current - 1);
    } catch (err) {
      alert((err as Error).message);
    }
  };

  if (loading) {
    return <div className="text-slate-300">Cargando movimientos...</div>;
  }

  return (
    <div>
      {/* Edit Modal */}
      {editingTx && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4">
          <div className="w-full max-w-md rounded-2xl border border-white/10 bg-[#0f172a] p-6 shadow-xl">
            <h2 className="mb-4 text-lg font-semibold text-white">Editar movimiento</h2>
            {editError && (
              <p className="mb-3 rounded-xl border border-rose-500/30 px-3 py-2 text-sm text-rose-300">{editError}</p>
            )}
            <div className="space-y-3">
              <div>
                <label className="mb-1 block text-xs text-slate-400">Fecha y hora</label>
                <input
                  type="datetime-local"
                  value={editForm.transaction_date}
                  onChange={(e) => setEditForm((f) => ({ ...f, transaction_date: e.target.value }))}
                  className="w-full rounded-xl border border-white/10 bg-black/30 px-3 py-2 text-sm text-white"
                />
              </div>
              <div>
                <label className="mb-1 block text-xs text-slate-400">
                  Monto ({editingTx.currency_code})
                </label>
                <input
                  type="number"
                  min="0"
                  step="any"
                  value={editForm.amount_original}
                  onChange={(e) => setEditForm((f) => ({ ...f, amount_original: e.target.value }))}
                  className="w-full rounded-xl border border-white/10 bg-black/30 px-3 py-2 text-sm text-white"
                />
              </div>
              <div>
                <label className="mb-1 block text-xs text-slate-400">Categoría</label>
                <select
                  value={editForm.category_id}
                  onChange={(e) => setEditForm((f) => ({ ...f, category_id: e.target.value }))}
                  className="w-full rounded-xl border border-white/10 bg-black/30 px-3 py-2 text-sm text-white"
                >
                  <option value="">Sin categoría</option>
                  {topLevelCategories.map((cat) => (
                    <option key={cat.id} value={cat.id}>{cat.name}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="mb-1 block text-xs text-slate-400">Notas</label>
                <input
                  type="text"
                  value={editForm.notes}
                  onChange={(e) => setEditForm((f) => ({ ...f, notes: e.target.value }))}
                  className="w-full rounded-xl border border-white/10 bg-black/30 px-3 py-2 text-sm text-white"
                  placeholder="Opcional"
                />
              </div>
            </div>
            <div className="mt-5 flex justify-end gap-3">
              <button
                onClick={() => setEditingTx(null)}
                className="rounded-xl border border-white/10 px-4 py-2 text-sm text-slate-300 hover:bg-white/5"
              >
                Cancelar
              </button>
              <button
                onClick={handleEditSave}
                disabled={editSaving}
                className="rounded-xl bg-gradient-to-r from-emerald-400 to-cyan-400 px-4 py-2 text-sm font-semibold text-black disabled:opacity-60"
              >
                {editSaving ? 'Guardando...' : 'Guardar'}
              </button>
            </div>
          </div>
        </div>
      )}

      <div className="mb-6 space-y-3">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <h1 className="text-2xl font-semibold">Movimientos</h1>
            <p className="text-sm text-slate-400">
              Mostrando {sortedTransactions.length} de {totalCount} movimientos
            </p>
          </div>
          <div className="flex flex-wrap gap-2">
            <button
              type="button"
              onClick={async () => {
                const params = {
                  start: filters.startDate ? `${filters.startDate}T00:00:00Z` : undefined,
                  end: filters.endDate ? `${filters.endDate}T23:59:59Z` : undefined,
                  account_ids: filters.accountId ? [Number(filters.accountId)] : undefined,
                  currency_code: filters.currency || undefined,
                  category_type: filters.type as 'income' | 'expense' | undefined || undefined,
                  search: filters.search || undefined,
                };
                const resp = await api.exportTransactionsCsv(params);
                const blob = await resp.blob();
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = 'movimientos.csv';
                a.click();
                URL.revokeObjectURL(url);
              }}
              className="rounded-full border border-white/10 px-4 py-2 text-sm text-slate-200 hover:border-white/40 hover:bg-white/10"
            >
              Exportar CSV
            </button>
            <button
              type="button"
              onClick={() => setFilters({ accountId: '', currency: '', type: '', search: '', startDate: '', endDate: '' })}
              className="rounded-full border border-white/10 px-4 py-2 text-sm text-slate-200 hover:border-white/40 hover:bg-white/10"
            >
              Limpiar filtros
            </button>
          </div>
        </div>
        <div className="grid grid-cols-1 gap-2 sm:grid-cols-2 lg:grid-cols-4">
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
              <option key={account.id} value={account.id}>{account.name}</option>
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
                  Fecha {sortField === 'date' && <span>{sortDirection === 'asc' ? '↑' : '↓'}</span>}
                </button>
              </th>
              <th className="px-4 py-3">
                <button type="button" onClick={() => handleSort('category')} className="flex items-center gap-1">
                  Categoría {sortField === 'category' && <span>{sortDirection === 'asc' ? '↑' : '↓'}</span>}
                </button>
              </th>
              <th className="px-4 py-3">
                <button type="button" onClick={() => handleSort('type')} className="flex items-center gap-1">
                  Tipo {sortField === 'type' && <span>{sortDirection === 'asc' ? '↑' : '↓'}</span>}
                </button>
              </th>
              <th className="px-4 py-3">Moneda</th>
              <th className="px-4 py-3">
                <button type="button" onClick={() => handleSort('amount')} className="flex items-center gap-1">
                  Monto {sortField === 'amount' && <span>{sortDirection === 'asc' ? '↑' : '↓'}</span>}
                </button>
              </th>
              <th className="px-4 py-3">Notas</th>
              <th className="px-4 py-3"></th>
            </tr>
          </thead>
          <tbody>
            {sortedTransactions.length === 0 && !loadingPage ? (
              <tr>
                <td colSpan={7} className="px-4 py-12 text-center text-slate-400">
                  No hay movimientos que coincidan con los filtros aplicados.
                </td>
              </tr>
            ) : (
              sortedTransactions.map((tx) => (
                <tr key={tx.id} className="border-t border-white/5 hover:bg-white/5">
                  <td className="px-4 py-3 text-slate-300">
                    {new Date(tx.transaction_date).toLocaleString('es-AR')}
                  </td>
                  <td className="px-4 py-3 text-slate-200">{tx.category_name}</td>
                  <td className="px-4 py-3 text-slate-300 capitalize">{tx.category_type}</td>
                  <td className="px-4 py-3 text-slate-300">{tx.currency_code}</td>
                  <td className="px-4 py-3 font-semibold text-slate-100">{formatOriginalAmount(tx)}</td>
                  <td className="px-4 py-3 text-slate-400">{tx.notes ?? '-'}</td>
                  <td className="px-4 py-3">
                    <div className="flex gap-2">
                      <button
                        type="button"
                        onClick={() => openEdit(tx)}
                        className="rounded-lg border border-white/10 px-2 py-1 text-xs text-slate-300 hover:bg-white/10"
                      >
                        Editar
                      </button>
                      <button
                        type="button"
                        onClick={() => handleDelete(tx)}
                        className="rounded-lg border border-rose-500/20 px-2 py-1 text-xs text-rose-300 hover:bg-rose-500/10"
                      >
                        Eliminar
                      </button>
                    </div>
                  </td>
                </tr>
              ))
            )}
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
