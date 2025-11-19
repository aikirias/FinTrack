'use client';

import { useEffect, useMemo, useState } from 'react';
import { api } from '@/lib/api';
import type { Account, Category, ExchangeRate, Transaction } from '@/types';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  ArcElement,
  Tooltip,
  Legend,
  BarElement,
} from 'chart.js';
import { Line, Doughnut, Bar } from 'react-chartjs-2';

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, ArcElement, Tooltip, Legend, BarElement);

const currencyFormatter = new Intl.NumberFormat('es-AR', { style: 'currency', currency: 'ARS' });

export default function DashboardPage() {
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [rates, setRates] = useState<ExchangeRate | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    (async () => {
      setLoading(true);
      try {
        const [acct, cats, txs, rate] = await Promise.all([
          api.getAccounts(),
          api.getCategories(),
          api.getTransactions(),
          api.getLatestRates(),
        ]);
        setAccounts(acct as Account[]);
        setCategories(cats as Category[]);
        setTransactions(txs as Transaction[]);
        setRates(rate as ExchangeRate);
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  const categoryMap = useMemo(() => {
    const map: Record<number, Category> = {};
    const traverse = (nodes: Category[]) => {
      nodes.forEach((node) => {
        map[node.id] = node;
        if (node.children) traverse(node.children);
      });
    };
    traverse(categories);
    return map;
  }, [categories]);

  const stats = useMemo(() => {
    let income = 0;
    let expense = 0;
    transactions.forEach((tx) => {
      const cat = tx.category_id ? categoryMap[tx.category_id] : null;
      const amount = parseFloat(tx.amount_ars);
      if (cat?.type === 'income') {
        income += amount;
      } else {
        expense += amount;
      }
    });
    return {
      income,
      expense,
      balance: income - expense,
    };
  }, [transactions, categoryMap]);

  const lineData = useMemo(() => {
    const grouped: Record<string, { income: number; expense: number }> = {};
    transactions.forEach((tx) => {
      const date = new Date(tx.transaction_date);
      const key = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}`;
      grouped[key] = grouped[key] || { income: 0, expense: 0 };
      const cat = tx.category_id ? categoryMap[tx.category_id] : null;
      const amount = parseFloat(tx.amount_ars);
      if (cat?.type === 'income') {
        grouped[key].income += amount;
      } else {
        grouped[key].expense += amount;
      }
    });
    const labels = Object.keys(grouped).sort();
    return {
      labels,
      datasets: [
        {
          label: 'Ingresos',
          data: labels.map((label) => grouped[label].income),
          borderColor: '#22d3ee',
          backgroundColor: 'rgba(34, 211, 238, 0.3)',
        },
        {
          label: 'Gastos',
          data: labels.map((label) => grouped[label].expense),
          borderColor: '#fb7185',
          backgroundColor: 'rgba(251, 113, 133, 0.3)',
        },
      ],
    };
  }, [transactions, categoryMap]);

  const topCategories = useMemo(() => {
    const totals: Record<string, number> = {};
    transactions.forEach((tx) => {
      const cat = tx.category_id ? categoryMap[tx.category_id] : null;
      if (!cat) return;
      const amount = parseFloat(tx.amount_ars);
      if (cat.type === 'expense') {
        totals[cat.name] = (totals[cat.name] || 0) + amount;
      }
    });
    const entries = Object.entries(totals)
      .sort((a, b) => b[1] - a[1])
      .slice(0, 5);
    return {
      labels: entries.map(([label]) => label),
      datasets: [
        {
          label: 'Gasto',
          data: entries.map(([, value]) => value),
          backgroundColor: ['#fb7185', '#f97316', '#facc15', '#34d399', '#38bdf8'],
        },
      ],
    };
  }, [transactions, categoryMap]);

  const lastMovements = useMemo(() => {
    return [...transactions]
      .sort((a, b) => new Date(b.transaction_date).getTime() - new Date(a.transaction_date).getTime())
      .slice(0, 5);
  }, [transactions]);

  if (loading) {
    return <div className="text-slate-300">Cargando datos...</div>;
  }

  return (
    <div className="space-y-6">
      <div className="grid gap-4 md:grid-cols-3">
        <div className="rounded-2xl border border-white/5 bg-white/5 p-4">
          <p className="text-sm text-slate-300">Balance</p>
          <p className="text-3xl font-semibold text-white">{currencyFormatter.format(stats.balance)}</p>
        </div>
        <div className="rounded-2xl border border-white/5 bg-white/5 p-4">
          <p className="text-sm text-slate-300">Ingresos</p>
          <p className="text-3xl font-semibold text-emerald-300">{currencyFormatter.format(stats.income)}</p>
        </div>
        <div className="rounded-2xl border border-white/5 bg-white/5 p-4">
          <p className="text-sm text-slate-300">Gastos</p>
          <p className="text-3xl font-semibold text-rose-300">{currencyFormatter.format(stats.expense)}</p>
        </div>
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        <div className="rounded-2xl border border-white/5 bg-white/5 p-4 lg:col-span-2">
          <h3 className="mb-4 text-lg font-semibold">Evolución mensual</h3>
          <Line data={lineData} options={{ plugins: { legend: { labels: { color: '#cbd5f5' } } }, scales: { x: { ticks: { color: '#cbd5f5' } }, y: { ticks: { color: '#cbd5f5' } } } }} />
        </div>
        <div className="rounded-2xl border border-white/5 bg-white/5 p-4">
          <h3 className="mb-4 text-lg font-semibold">Top categorías</h3>
          {topCategories.labels.length ? (
            <Doughnut data={topCategories} options={{ plugins: { legend: { labels: { color: '#cbd5f5' } } } }} />
          ) : (
            <p className="text-sm text-slate-400">Sin datos suficientes.</p>
          )}
        </div>
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        <div className="rounded-2xl border border-white/5 bg-white/5 p-4 lg:col-span-2">
          <h3 className="mb-4 text-lg font-semibold">Últimos movimientos</h3>
          <div className="space-y-3">
            {lastMovements.map((tx) => {
              const cat = tx.category_id ? categoryMap[tx.category_id] : null;
              const amount = parseFloat(tx.amount_ars);
              const isIncome = cat?.type === 'income';
              return (
                <div key={tx.id} className="flex items-center justify-between rounded-xl border border-white/5 bg-black/10 px-4 py-3">
                  <div>
                    <p className="font-semibold text-white">{cat?.name ?? 'Sin categoría'}</p>
                    <p className="text-xs text-slate-400">{new Date(tx.transaction_date).toLocaleString('es-AR')}</p>
                  </div>
                  <p className={`text-sm font-semibold ${isIncome ? 'text-emerald-300' : 'text-rose-300'}`}>
                    {isIncome ? '+' : '-'}{currencyFormatter.format(amount)}
                  </p>
                </div>
              );
            })}
          </div>
        </div>
        <div className="rounded-2xl border border-white/5 bg-white/5 p-4">
          <h3 className="mb-4 text-lg font-semibold">Distribución diaria</h3>
          <Bar
            data={{
              labels: lastMovements.map((tx) => new Date(tx.transaction_date).toLocaleDateString('es-AR')),
              datasets: [
                {
                  label: 'Saldo',
                  data: lastMovements.map((tx) => {
                    const cat = tx.category_id ? categoryMap[tx.category_id] : null;
                    const amount = parseFloat(tx.amount_ars);
                    return cat?.type === 'income' ? amount : -amount;
                  }),
                  backgroundColor: lastMovements.map((tx) => {
                    const cat = tx.category_id ? categoryMap[tx.category_id] : null;
                    return cat?.type === 'income' ? '#22d3ee' : '#fb7185';
                  }),
                },
              ],
            }}
            options={{
              plugins: { legend: { display: false } },
              scales: {
                x: { ticks: { color: '#cbd5f5' } },
                y: { ticks: { color: '#cbd5f5' } },
              },
            }}
          />
          {rates && (
            <p className="mt-4 text-xs text-slate-400">
              USD oficial: {rates.usd_ars_oficial} · USD blue: {rates.usd_ars_blue ?? 's/d'} · BTC: {rates.btc_ars}
            </p>
          )}
        </div>
      </div>
    </div>
  );
}
