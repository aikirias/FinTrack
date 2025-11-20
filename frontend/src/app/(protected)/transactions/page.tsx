'use client';

import { useEffect, useMemo, useState } from 'react';
import { api } from '@/lib/api';
import type { Category, Transaction } from '@/types';

const arsFormatter = new Intl.NumberFormat('es-AR', { style: 'currency', currency: 'ARS' });
const usdFormatter = new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' });
const btcFormatter = new Intl.NumberFormat('en-US', { minimumFractionDigits: 8, maximumFractionDigits: 8 });
type SortField = 'date' | 'amount' | 'category' | 'type';

export default function TransactionsPage() {
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [loading, setLoading] = useState(true);
  const [sortField, setSortField] = useState<SortField>('date');
  const [sortDirection, setSortDirection] = useState<'asc' | 'desc'>('desc');
  const [visibleCount, setVisibleCount] = useState(50);

  useEffect(() => {
    (async () => {
      setLoading(true);
      try {
        const [txs, cats] = await Promise.all([api.getTransactions(), api.getCategories()]);
        setTransactions(txs as Transaction[]);
        setCategories(cats as Category[]);
      } finally {
        setLoading(false);
      }
    })();
  }, []);

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

  const flattened = useMemo(() => {
    return transactions.map((tx) => {
      const cat = tx.category_id ? categoryMap[tx.category_id] : undefined;
      return {
        ...tx,
        category_name: cat?.name ?? 'Sin categoría',
        category_type: cat?.type ?? 'Sin tipo',
      };
    });
  }, [transactions, categoryMap]);

  const sortedTransactions = useMemo(() => {
    const data = [...flattened];
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
  }, [flattened, sortField, sortDirection]);

  const visibleTransactions = sortedTransactions.slice(0, visibleCount);

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

  if (loading) {
    return <div className="text-slate-300">Cargando movimientos...</div>;
  }

  return (
    <div>
      <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold">Movimientos</h1>
          <p className="text-sm text-slate-400">
            Mostrando {visibleTransactions.length} de {sortedTransactions.length}
          </p>
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
            {visibleTransactions.map((tx) => (
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
      {visibleCount < sortedTransactions.length && (
        <div className="mt-4 flex justify-center">
          <button
            type="button"
            onClick={() => setVisibleCount((prev) => prev + 50)}
            className="rounded-full border border-white/10 px-4 py-2 text-sm text-white hover:border-white/40 hover:bg-white/10"
          >
            Cargar más
          </button>
        </div>
      )}
    </div>
  );
}
