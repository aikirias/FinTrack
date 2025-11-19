'use client';

import { useEffect, useMemo, useState } from 'react';
import { api } from '@/lib/api';
import type { Category, Transaction } from '@/types';

const currencyFormatter = new Intl.NumberFormat('es-AR', { style: 'currency', currency: 'ARS' });

export default function TransactionsPage() {
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [loading, setLoading] = useState(true);

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
    const map: Record<number, string> = {};
    const walk = (nodes: Category[]) => {
      nodes.forEach((cat) => {
        map[cat.id] = cat.name;
        if (cat.children) walk(cat.children);
      });
    };
    walk(categories);
    return map;
  }, [categories]);

  if (loading) {
    return <div className="text-slate-300">Cargando movimientos...</div>;
  }

  return (
    <div>
      <h1 className="mb-4 text-2xl font-semibold">Movimientos</h1>
      <div className="overflow-auto rounded-2xl border border-white/5">
        <table className="min-w-full text-sm">
          <thead className="bg-white/5 text-left text-xs uppercase text-slate-400">
            <tr>
              <th className="px-4 py-3">Fecha</th>
              <th className="px-4 py-3">Categoría</th>
              <th className="px-4 py-3">Moneda</th>
              <th className="px-4 py-3">Monto</th>
              <th className="px-4 py-3">Notas</th>
            </tr>
          </thead>
          <tbody>
            {transactions.map((tx) => {
              const cat = tx.category_id ? categoryMap[tx.category_id] : 'Sin categoría';
              return (
                <tr key={tx.id} className="border-t border-white/5">
                  <td className="px-4 py-3 text-slate-300">{new Date(tx.transaction_date).toLocaleString('es-AR')}</td>
                  <td className="px-4 py-3 text-slate-200">{cat}</td>
                  <td className="px-4 py-3 text-slate-300">{tx.currency_code}</td>
                  <td className="px-4 py-3 font-semibold text-slate-100">{currencyFormatter.format(parseFloat(tx.amount_ars))}</td>
                  <td className="px-4 py-3 text-slate-400">{tx.notes ?? '-'}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
