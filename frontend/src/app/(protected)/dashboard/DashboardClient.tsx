'use client';

import { useCallback, useEffect, useMemo, useState } from 'react';
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
const calendarAmountFormatter = new Intl.NumberFormat('es-AR', {
  style: 'currency',
  currency: 'ARS',
  maximumFractionDigits: 0,
});
const usdFormatter = new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' });
const usdShortFormatter = new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 });
const btcFormatter = new Intl.NumberFormat('en-US', { minimumFractionDigits: 8, maximumFractionDigits: 8 });
const btcShortFormatter = new Intl.NumberFormat('en-US', { minimumFractionDigits: 4, maximumFractionDigits: 4 });
const timeOptions = [
  { label: 'Mes actual', value: 'current', months: null },
  { label: '1M', value: '1m', months: 1 },
  { label: '3M', value: '3m', months: 3 },
  { label: '6M', value: '6m', months: 6 },
  { label: '1A', value: '1y', months: 12 },
  { label: 'Todo', value: 'all', months: null },
];

const colorPalette = ['#fb7185', '#f97316', '#facc15', '#34d399', '#38bdf8', '#a78bfa', '#f472b6', '#f59e0b'];
const weekDays = ['Dom', 'Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb'];
const heatLevels = ['bg-white/5 border-white/10', 'bg-rose-950/30 border-rose-900/40', 'bg-rose-900/40 border-rose-700/50', 'bg-rose-700/50 border-rose-500/60', 'bg-rose-500/70 border-rose-400/80'];
const currencyOptions: Array<{ label: string; value: 'ARS' | 'USD' | 'BTC' }> = [
  { label: 'ARS', value: 'ARS' },
  { label: 'USD', value: 'USD' },
  { label: 'BTC', value: 'BTC' },
];
const emojiMap: Record<string, string> = {
  Servicios: '💡',
  Comida: '🍽️',
  Transporte: '🚕',
  'Compras Personales': '🛍️',
  Salud: '🧑‍⚕️',
  Regalos: '🎁',
  Viajes: '✈️',
  Hogar: '🏠',
  Ocio: '🎮',
  Emprendimientos: '🚀',
  Otros: '💸',
};

export default function DashboardPage() {
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [rates, setRates] = useState<ExchangeRate | null>(null);
  const [loading, setLoading] = useState(true);
  const [timeRange, setTimeRange] = useState<(typeof timeOptions)[number]['value']>('3m');
  const [baseCurrency, setBaseCurrency] = useState<'ARS' | 'USD' | 'BTC'>('ARS');
  const [selectedCategoryId, setSelectedCategoryId] = useState<number | null>(null);
  const [selectedIncomeCategoryId, setSelectedIncomeCategoryId] = useState<number | null>(null);
  const [detailOpen, setDetailOpen] = useState(false);
  const [selectedDayDetail, setSelectedDayDetail] = useState<{
    date: Date;
    transactions: Transaction[];
    total: number;
  } | null>(null);
  const [calendarMonth, setCalendarMonth] = useState(() => {
    const today = new Date();
    return `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, '0')}`;
  });
  const getAmount = useCallback(
    (tx: Transaction) => {
      if (baseCurrency === 'USD') return parseFloat(tx.amount_usd);
      if (baseCurrency === 'BTC') return parseFloat(tx.amount_btc);
      return parseFloat(tx.amount_ars);
    },
    [baseCurrency]
  );
  const formatAmount = useCallback(
    (value: number) => {
      if (baseCurrency === 'USD') return usdFormatter.format(value);
      if (baseCurrency === 'BTC') return `${btcFormatter.format(value)} BTC`;
      return currencyFormatter.format(value);
    },
    [baseCurrency]
  );
  const formatShortAmount = useCallback(
    (value: number) => {
      if (baseCurrency === 'USD') return usdShortFormatter.format(value);
      if (baseCurrency === 'BTC') return `${btcShortFormatter.format(value)} BTC`;
      return calendarAmountFormatter.format(value);
    },
    [baseCurrency]
  );
  const handleCategorySelect = (categoryId: number) => {
    setSelectedCategoryId((prev) => (prev === categoryId ? null : categoryId));
    setDetailOpen(false);
  };
  const handleIncomeCategorySelect = (categoryId: number) => {
    setSelectedIncomeCategoryId((prev) => (prev === categoryId ? null : categoryId));
  };
  const openCategoryDetail = () => {
    if (selectedCategoryId) setDetailOpen(true);
  };
  const handleExport = () => {
    if (!filteredTransactions.length) return;
    const escape = (value: string | number | null | undefined) => {
      if (value === null || value === undefined) return '""';
      const str = String(value).replace(/"/g, '""');
      return `"${str}"`;
    };
    const header = [
      'Fecha',
      'Cuenta',
      'Categoría',
      'Subcategoría',
      'Moneda',
      'Monto original',
      'ARS',
      'USD',
      'BTC',
      'Notas',
    ]
      .map(escape)
      .join(',');
    const rows = filteredTransactions.map((tx) => {
      const category = tx.category_id ? categoryMap[tx.category_id]?.name ?? '' : '';
      const subcategory = tx.subcategory_id ? categoryMap[tx.subcategory_id]?.name ?? '' : '';
      const account = accountMap[tx.account_id]?.name ?? '';
      return [
        new Date(tx.transaction_date).toLocaleString('es-AR'),
        account,
        category,
        subcategory,
        tx.currency_code,
        tx.amount_original,
        tx.amount_ars,
        tx.amount_usd,
        tx.amount_btc,
        tx.notes ?? '',
      ]
        .map(escape)
        .join(',');
    });
    const csv = [header, ...rows].join('\n');
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `fintrack-${new Date().toISOString().slice(0, 10)}.csv`;
    link.click();
    URL.revokeObjectURL(url);
  };

  const renderTrendLabel = (value: number | null | undefined) => {
    if (value === null || value === undefined) return null;
    const color = value >= 0 ? 'text-emerald-300' : 'text-rose-300';
    return (
      <p className={`text-xs font-semibold ${color}`}>
        {value >= 0 ? '+' : ''}
        {(value * 100).toFixed(1)}% vs período anterior
      </p>
    );
  };

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

  useEffect(() => {
    if (!selectedCategoryId) {
      setDetailOpen(false);
    }
  }, [selectedCategoryId]);

  useEffect(() => {
    setSelectedDayDetail(null);
  }, [calendarMonth, baseCurrency]);

  useEffect(() => {
    if (detailOpen || selectedDayDetail) {
      const original = document.body.style.overflow;
      document.body.style.overflow = 'hidden';
      return () => {
        document.body.style.overflow = original;
      };
    }
    return undefined;
  }, [detailOpen, selectedDayDetail]);

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

  const accountMap = useMemo(() => {
    const map: Record<number, Account> = {};
    accounts.forEach((account) => {
      map[account.id] = account;
    });
    return map;
  }, [accounts]);

  const timeRangeStart = useMemo(() => {
    if (timeRange === 'all') return null;
    const now = new Date();
    if (timeRange === 'current') return new Date(now.getFullYear(), now.getMonth(), 1);
    const option = timeOptions.find((opt) => opt.value === timeRange);
    if (option?.months) {
      const start = new Date();
      start.setMonth(start.getMonth() - option.months);
      return start;
    }
    return null;
  }, [timeRange]);

  const filteredTransactions = useMemo(() => {
    if (!timeRangeStart) return transactions;
    return transactions.filter((tx) => new Date(tx.transaction_date) >= timeRangeStart);
  }, [transactions, timeRangeStart]);

  const aggregateStats = useCallback(
    (list: Transaction[]) => {
      return list.reduce(
        (acc, tx) => {
          const cat = tx.category_id ? categoryMap[tx.category_id] : null;
          const amount = getAmount(tx);
          if (cat?.type === 'income') {
            acc.income += amount;
          } else {
            acc.expense += amount;
          }
          return acc;
        },
        { income: 0, expense: 0 }
      );
    },
    [categoryMap, getAmount]
  );

  const stats = useMemo(() => {
    const totals = aggregateStats(filteredTransactions);
    return { ...totals, balance: totals.income - totals.expense };
  }, [filteredTransactions, aggregateStats]);

  const previousStats = useMemo(() => {
    if (!timeRangeStart) return null;
    const end = new Date();
    const duration = Math.max(0, end.getTime() - timeRangeStart.getTime());
    if (duration === 0) return null;
    const previousEnd = timeRangeStart;
    const previousStart = new Date(timeRangeStart.getTime() - duration);
    const rangeTransactions = transactions.filter((tx) => {
      const date = new Date(tx.transaction_date);
      return date >= previousStart && date < previousEnd;
    });
    const totals = aggregateStats(rangeTransactions);
    return { ...totals, balance: totals.income - totals.expense };
  }, [timeRangeStart, transactions, aggregateStats]);

  const statsTrend = useMemo(() => {
    if (!previousStats) return null;
    const diff = (current: number, previous: number) => {
      if (!previous) return null;
      return (current - previous) / previous;
    };
    return {
      income: diff(stats.income, previousStats.income),
      expense: diff(stats.expense, previousStats.expense),
      balance: diff(stats.balance, previousStats.balance),
    };
  }, [stats, previousStats]);

  const lineData = useMemo(() => {
    const grouped: Record<string, { income: number; expense: number }> = {};
    filteredTransactions.forEach((tx) => {
      const date = new Date(tx.transaction_date);
      const key = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}`;
      grouped[key] = grouped[key] || { income: 0, expense: 0 };
      const cat = tx.category_id ? categoryMap[tx.category_id] : null;
      const amount = getAmount(tx);
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
  }, [filteredTransactions, categoryMap, getAmount]);

  const expenseSummary = useMemo(() => {
    const totals: Record<number, { id: number; label: string; value: number }> = {};
    filteredTransactions.forEach((tx) => {
      const cat = tx.category_id ? categoryMap[tx.category_id] : null;
      if (cat?.type !== 'expense') return;
      if (!totals[cat.id]) {
        totals[cat.id] = { id: cat.id, label: cat.name, value: 0 };
      }
      totals[cat.id].value += getAmount(tx);
    });
    const entries = Object.values(totals).sort((a, b) => b.value - a.value);
    const total = entries.reduce((sum, entry) => sum + entry.value, 0);
    const colors = entries.map((_, idx) => colorPalette[idx % colorPalette.length]);
    return {
      total,
      entries,
      colors,
      chart: {
        labels: entries.map((entry) => entry.label),
        datasets: [
          {
            label: 'Gastos',
            data: entries.map((entry) => entry.value),
            backgroundColor: colors,
            borderColor: '#0f172a',
            hoverOffset: 8,
          },
        ],
      },
    };
  }, [filteredTransactions, categoryMap, getAmount]);

  useEffect(() => {
    if (selectedCategoryId && !expenseSummary.entries.some((entry) => entry.id === selectedCategoryId)) {
      setSelectedCategoryId(null);
    }
  }, [expenseSummary.entries, selectedCategoryId]);

  const incomeInsights = useMemo(() => {
    const totals: Record<string, { id: number; label: string; value: number }> = {};
    filteredTransactions.forEach((tx) => {
      const cat = tx.category_id ? categoryMap[tx.category_id] : null;
      if (cat?.type !== 'income') return;
      if (!totals[cat.id]) {
        totals[cat.id] = { id: cat.id, label: cat.name, value: 0 };
      }
      totals[cat.id].value += getAmount(tx);
    });
    const entries = Object.values(totals).sort((a, b) => b.value - a.value);
    const total = entries.reduce((sum, entry) => sum + entry.value, 0);
    const colors = entries.map((_, idx) => colorPalette[idx % colorPalette.length]);
    return {
      total,
      entries,
      colors,
      chart: {
        labels: entries.map((entry) => entry.label),
        datasets: [
          {
            label: 'Ingresos',
            data: entries.map((entry) => entry.value),
            backgroundColor: colors,
            borderColor: '#0f172a',
            hoverOffset: 8,
          },
        ],
      },
    };
  }, [filteredTransactions, categoryMap, getAmount]);

  useEffect(() => {
    if (selectedIncomeCategoryId && !incomeInsights.entries.some((entry) => entry.id === selectedIncomeCategoryId)) {
      setSelectedIncomeCategoryId(null);
    }
  }, [incomeInsights.entries, selectedIncomeCategoryId]);

  const selectedCategoryData = useMemo(() => {
    if (!selectedCategoryId) return null;
    const category = categoryMap[selectedCategoryId];
    if (!category) return null;
    const catTransactions = filteredTransactions.filter((tx) => tx.category_id === selectedCategoryId);
    if (!catTransactions.length) return null;
    const total = catTransactions.reduce((sum, tx) => sum + getAmount(tx), 0);
    const share = expenseSummary.total ? total / expenseSummary.total : 0;
    const timelineTotals: Record<string, number> = {};
    const subTotals: Record<string, { label: string; value: number }> = {};
    const accountTotals: Record<string, { label: string; value: number }> = {};

    catTransactions.forEach((tx) => {
      const amount = getAmount(tx);
      const subId = tx.subcategory_id;
      const key = subId ? String(subId) : 'none';
      const label = subId ? categoryMap[subId]?.name ?? 'Sin subcategoría' : 'Sin subcategoría';
      if (!subTotals[key]) {
        subTotals[key] = { label, value: 0 };
      }
      subTotals[key].value += amount;
      const accountKey = String(tx.account_id);
      const accountLabel = accountMap[tx.account_id]?.name ?? 'Cuenta';
      if (!accountTotals[accountKey]) {
        accountTotals[accountKey] = { label: accountLabel, value: 0 };
      }
      accountTotals[accountKey].value += amount;
      const dayKey = new Date(tx.transaction_date).toISOString().slice(0, 10);
      timelineTotals[dayKey] = (timelineTotals[dayKey] || 0) + amount;
    });

    const subEntries = Object.values(subTotals).sort((a, b) => b.value - a.value);
    const accountEntries = Object.values(accountTotals).sort((a, b) => b.value - a.value);
    const timelineLabels = Object.keys(timelineTotals).sort();
    const timelineChart = {
      labels: timelineLabels.map((label) =>
        new Date(label).toLocaleDateString('es-AR', { day: 'numeric', month: 'short' })
      ),
      datasets: [
        {
          label: category.name,
          data: timelineLabels.map((label) => timelineTotals[label]),
          borderColor: '#fb7185',
          backgroundColor: 'rgba(251, 113, 133, 0.25)',
          fill: true,
          tension: 0.4,
        },
      ],
    };

    let previousTotal: number | null = null;
    let trend: number | null = null;
    if (timeRangeStart) {
      const periodEnd = new Date();
      const periodStart = timeRangeStart;
      const duration = Math.max(1, periodEnd.getTime() - periodStart.getTime());
      const previousStart = new Date(periodStart.getTime() - duration);
      const previousEnd = periodStart;
      previousTotal = transactions
        .filter((tx) => {
          if (tx.category_id !== selectedCategoryId) return false;
          const txDate = new Date(tx.transaction_date);
          return txDate >= previousStart && txDate < previousEnd;
        })
        .reduce((sum, tx) => sum + getAmount(tx), 0);
      if (previousTotal === 0) {
        trend = null;
      } else {
        trend = (total - previousTotal) / previousTotal;
      }
    }

    const sortedTransactions = [...catTransactions].sort(
      (a, b) => new Date(b.transaction_date).getTime() - new Date(a.transaction_date).getTime()
    );
    const largest = sortedTransactions.reduce(
      (acc, tx) => {
        const value = getAmount(tx);
        if (value > acc.amount) {
          return { amount: value, tx };
        }
        return acc;
      },
      { amount: 0, tx: sortedTransactions[0] }
    );

    return {
      category,
      total,
      share,
      count: catTransactions.length,
      avgTicket: total / catTransactions.length,
      subEntries,
      accountEntries,
      timelineChart,
      recentTransactions: sortedTransactions.slice(0, 4),
      transactions: sortedTransactions,
      previousTotal,
      trend,
      largestTransaction: largest.tx,
      largestAmount: largest.amount,
    };
  }, [
    selectedCategoryId,
    filteredTransactions,
    categoryMap,
    expenseSummary.total,
    timeRangeStart,
    transactions,
    accountMap,
    getAmount,
  ]);

  const selectedIncomeData = useMemo(() => {
    if (!selectedIncomeCategoryId) return null;
    const category = categoryMap[selectedIncomeCategoryId];
    if (!category) return null;
    const catTransactions = filteredTransactions.filter((tx) => tx.category_id === selectedIncomeCategoryId);
    if (!catTransactions.length) return null;
    const total = catTransactions.reduce((sum, tx) => sum + getAmount(tx), 0);
    const share = incomeInsights.total ? total / incomeInsights.total : 0;
    const timelineTotals: Record<string, number> = {};
    const accountTotals: Record<string, { label: string; value: number }> = {};

    catTransactions.forEach((tx) => {
      const amount = getAmount(tx);
      const accountKey = String(tx.account_id);
      const accountLabel = accountMap[tx.account_id]?.name ?? 'Cuenta';
      if (!accountTotals[accountKey]) {
        accountTotals[accountKey] = { label: accountLabel, value: 0 };
      }
      accountTotals[accountKey].value += amount;
      const dayKey = new Date(tx.transaction_date).toISOString().slice(0, 10);
      timelineTotals[dayKey] = (timelineTotals[dayKey] || 0) + amount;
    });

    const accountEntries = Object.values(accountTotals).sort((a, b) => b.value - a.value);
    const timelineLabels = Object.keys(timelineTotals).sort();
    const timelineChart = {
      labels: timelineLabels.map((label) =>
        new Date(label).toLocaleDateString('es-AR', { day: 'numeric', month: 'short' })
      ),
      datasets: [
        {
          label: category.name,
          data: timelineLabels.map((label) => timelineTotals[label]),
          borderColor: '#22d3ee',
          backgroundColor: 'rgba(34, 211, 238, 0.25)',
          fill: true,
          tension: 0.4,
        },
      ],
    };

    const sortedTransactions = [...catTransactions].sort(
      (a, b) => new Date(b.transaction_date).getTime() - new Date(a.transaction_date).getTime()
    );
    const largest = sortedTransactions.reduce(
      (acc, tx) => {
        const value = getAmount(tx);
        if (value > acc.amount) {
          return { amount: value, tx };
        }
        return acc;
      },
      { amount: 0, tx: sortedTransactions[0] }
    );

    return {
      category,
      total,
      share,
      count: catTransactions.length,
      avgTicket: total / catTransactions.length,
      accountEntries,
      timelineChart,
      recentTransactions: sortedTransactions.slice(0, 4),
      largestTransaction: largest.tx,
      largestAmount: largest.amount,
    };
  }, [selectedIncomeCategoryId, filteredTransactions, categoryMap, incomeInsights.total, accountMap, getAmount]);

  const calendarData = useMemo(() => {
    const [yearStr, monthStr] = calendarMonth.split('-');
    const year = Number(yearStr);
    const monthIndex = Number(monthStr) - 1;
    if (Number.isNaN(year) || Number.isNaN(monthIndex)) return null;
    const monthStart = new Date(year, monthIndex, 1);
    const monthEnd = new Date(year, monthIndex + 1, 0);
    const totals: Record<number, number> = {};
    const dayTransactions: Record<number, Transaction[]> = {};
    transactions.forEach((tx) => {
      const cat = tx.category_id ? categoryMap[tx.category_id] : null;
      if (cat?.type !== 'expense') return;
      const date = new Date(tx.transaction_date);
      if (date.getFullYear() === year && date.getMonth() === monthIndex) {
        const day = date.getDate();
        totals[day] = (totals[day] || 0) + parseFloat(tx.amount_ars);
        if (!dayTransactions[day]) dayTransactions[day] = [];
        dayTransactions[day].push(tx);
      }
    });
    const highest = Object.values(totals).reduce((max, value) => Math.max(max, value), 0);
    const leadingEmpty = monthStart.getDay();
    const cells: ({ day: number; amount: number; level: number; transactions: Transaction[] } | null)[] = [];
    for (let i = 0; i < leadingEmpty; i += 1) cells.push(null);
    for (let day = 1; day <= monthEnd.getDate(); day += 1) {
      const amount = totals[day] || 0;
      let level = 0;
      if (highest > 0) {
        const intensity = amount / highest;
        if (intensity >= 0.75) level = 4;
        else if (intensity >= 0.5) level = 3;
        else if (intensity >= 0.25) level = 2;
        else if (intensity > 0) level = 1;
      }
      cells.push({ day, amount, level, transactions: dayTransactions[day] || [] });
    }
    while (cells.length % 7 !== 0) {
      cells.push(null);
    }
    const total = Object.values(totals).reduce((sum, value) => sum + value, 0);
    const avg = monthEnd.getDate() ? total / monthEnd.getDate() : 0;
    return {
      cells,
      total,
      avg,
      max: highest,
      label: monthStart.toLocaleDateString('es-AR', { month: 'long', year: 'numeric' }),
      monthStart,
    };
  }, [calendarMonth, transactions, categoryMap, getAmount]);

  const handleCalendarDayClick = (cell: { day: number; amount: number; transactions: Transaction[] }) => {
    if (!calendarData) return;
    if (!cell.transactions.length) return;
    const date = new Date(calendarData.monthStart.getFullYear(), calendarData.monthStart.getMonth(), cell.day);
    const ordered = [...cell.transactions].sort(
      (a, b) => new Date(b.transaction_date).getTime() - new Date(a.transaction_date).getTime()
    );
    setSelectedDayDetail({
      date,
      transactions: ordered,
      total: cell.amount,
    });
  };

  const exportDisabled = filteredTransactions.length === 0;

  if (loading) {
    return <div className="text-slate-300">Cargando datos...</div>;
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <h1 className="text-2xl font-semibold text-white">Dashboard</h1>
          <button
            type="button"
            onClick={handleExport}
            disabled={exportDisabled}
            className={`rounded-full border border-white/10 px-4 py-2 text-sm font-semibold transition ${
              exportDisabled
                ? 'cursor-not-allowed text-slate-500'
                : 'text-white hover:border-white/40 hover:bg-white/10'
            }`}
          >
            Exportar CSV
          </button>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <div className="flex gap-2 rounded-full border border-white/10 bg-white/5 p-1">
            {timeOptions.map((opt) => (
              <button
                key={opt.value}
                onClick={() => setTimeRange(opt.value)}
                className={`rounded-full px-4 py-1 text-sm font-semibold ${
                  timeRange === opt.value ? 'bg-white text-primary' : 'text-slate-300'
                }`}
              >
                {opt.label}
              </button>
            ))}
          </div>
          <div className="flex gap-2 rounded-full border border-white/10 bg-white/5 p-1">
            {currencyOptions.map((opt) => (
              <button
                key={opt.value}
                onClick={() => setBaseCurrency(opt.value)}
                className={`rounded-full px-3 py-1 text-sm font-semibold ${
                  baseCurrency === opt.value ? 'bg-white text-primary' : 'text-slate-300'
                }`}
              >
                {opt.label}
              </button>
            ))}
          </div>
        </div>
      </div>
      <div className="grid gap-4 md:grid-cols-3">
        <div className="rounded-2xl border border-white/5 bg-white/5 p-4">
          <p className="text-sm text-slate-300">Balance</p>
          <p className="text-3xl font-semibold text-white">{formatAmount(stats.balance)}</p>
          {renderTrendLabel(statsTrend?.balance)}
        </div>
        <div className="rounded-2xl border border-white/5 bg-white/5 p-4">
          <p className="text-sm text-slate-300">Ingresos</p>
          <p className="text-3xl font-semibold text-emerald-300">{formatAmount(stats.income)}</p>
          {renderTrendLabel(statsTrend?.income)}
          <div className="mt-2 h-1 rounded-full bg-emerald-500/40">
            <div style={{ width: stats.expense + stats.income ? `${Math.min(100, (stats.income / (stats.income + stats.expense)) * 100)}%` : '0%' }} className="h-full rounded-full bg-emerald-400" />
          </div>
        </div>
        <div className="rounded-2xl border border-white/5 bg-white/5 p-4">
          <p className="text-sm text-slate-300">Gastos</p>
          <p className="text-3xl font-semibold text-rose-300">{formatAmount(stats.expense)}</p>
          {renderTrendLabel(statsTrend?.expense)}
          <div className="mt-2 h-1 rounded-full bg-rose-500/30">
            <div style={{ width: stats.expense + stats.income ? `${Math.min(100, (stats.expense / (stats.income + stats.expense)) * 100)}%` : '0%' }} className="h-full rounded-full bg-rose-400" />
          </div>
        </div>
      </div>

      <div className="rounded-2xl border border-white/5 bg-white/5 p-4">
        <h3 className="mb-4 text-lg font-semibold">Evolución mensual</h3>
        <Line
          data={lineData}
          options={{
            plugins: { legend: { labels: { color: '#cbd5f5' } } },
            scales: {
              x: { ticks: { color: '#cbd5f5' } },
              y: { ticks: { color: '#cbd5f5' } },
            },
          }}
        />
      </div>

      <div className="grid gap-6 xl:grid-cols-2">
        <div className="rounded-2xl border border-white/5 bg-white/5 p-4">
          <div className="mb-4 flex items-center justify-between">
            <h3 className="text-lg font-semibold">Distribución de gastos</h3>
            <span className="text-sm text-slate-300">Total {formatAmount(expenseSummary.total)}</span>
          </div>
          {expenseSummary.entries.length ? (
            <div className="flex flex-col gap-4">
              <div className="mx-auto w-60">
                <Doughnut
                  data={expenseSummary.chart}
                  options={{
                    cutout: '60%',
                    plugins: {
                      legend: { display: false },
                      tooltip: {
                        callbacks: {
                          label: (ctx) => `${ctx.label}: ${formatAmount(Number(ctx.formattedValue))}`,
                        },
                      },
                    },
                  }}
                />
              </div>
              <ul className="flex-1 space-y-2">
                {expenseSummary.entries.map((entry, index) => {
                  const { id, label, value } = entry;
                  const pct = expenseSummary.total ? (value / expenseSummary.total) * 100 : 0;
                  const emoji = emojiMap[label.split(' ')[0]] ?? '💸';
                  const color = expenseSummary.colors[index % expenseSummary.colors.length];
                  const selected = selectedCategoryId === id;
                  return (
                    <li key={`${id}-${label}`}>
                      <button
                        type="button"
                        aria-pressed={selected}
                        onClick={() => handleCategorySelect(id)}
                        className={`flex w-full items-center justify-between rounded-xl border bg-black/20 px-3 py-2 text-left transition ${
                          selected ? 'border-white/40 bg-white/10 shadow-lg shadow-rose-500/10' : 'border-white/5'
                        }`}
                        style={{ borderColor: selected ? color : undefined }}
                      >
                        <div className="flex items-center gap-3">
                          <span className="text-xl" style={{ textShadow: '0 0 6px rgba(0,0,0,0.3)' }}>{emoji}</span>
                          <div>
                            <p className="font-semibold text-white">{label}</p>
                            <p className="text-xs text-slate-400">{pct.toFixed(1)}%</p>
                          </div>
                        </div>
                        <span className="font-semibold" style={{ color }}>
                          {formatAmount(value)}
                        </span>
                      </button>
                    </li>
                  );
                })}
              </ul>
            </div>
          ) : (
            <p className="text-sm text-slate-400">Sin datos suficientes.</p>
          )}
        </div>

        <div className="rounded-2xl border border-white/5 bg-white/5 p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs uppercase tracking-widest text-slate-400">Detalle por categoría</p>
              <h3 className="text-lg font-semibold">
                {selectedCategoryData ? (
                  <>
                    <span className="mr-1">
                      {emojiMap[selectedCategoryData.category.name] ??
                        emojiMap[selectedCategoryData.category.name.split(' ')[0]] ??
                        '💸'}
                    </span>
                    {selectedCategoryData.category.name}
                  </>
                ) : (
                  'Elegí una categoría'
                )}
              </h3>
            </div>
            {selectedCategoryData && (
              <button
                type="button"
                onClick={openCategoryDetail}
                className="rounded-full border border-white/10 px-3 py-1 text-xs text-slate-200 hover:bg-white/10"
              >
                Ver detalle
              </button>
            )}
          </div>
          {selectedCategoryData ? (
            <div className="mt-4 space-y-4">
              <div>
                <p className="text-3xl font-semibold text-rose-200">{formatAmount(selectedCategoryData.total)}</p>
                <p className="text-xs text-slate-400">
                    {(selectedCategoryData.share * 100).toFixed(1)}% del gasto del período · {selectedCategoryData.count} movimientos ·
                    Ticket promedio {formatAmount(selectedCategoryData.avgTicket)}
                </p>
              </div>
              <div className="grid gap-4 md:grid-cols-2">
                <div>
                  <p className="text-sm text-slate-300">Subcategorías</p>
                  {selectedCategoryData.subEntries.length ? (
                    <ul className="mt-2 space-y-2 text-sm text-slate-200">
                      {selectedCategoryData.subEntries.map((entry) => {
                        const share = selectedCategoryData.total ? (entry.value / selectedCategoryData.total) * 100 : 0;
                        return (
                          <li key={entry.label} className="rounded-xl border border-white/5 bg-black/20 p-3">
                            <div className="flex items-center justify-between">
                              <span>{entry.label}</span>
                                <span className="font-semibold">{formatAmount(entry.value)}</span>
                            </div>
                            <div className="mt-2 h-1.5 rounded-full bg-white/5">
                              <div className="h-full rounded-full bg-rose-400" style={{ width: `${Math.min(100, share)}%` }} />
                            </div>
                          </li>
                        );
                      })}
                    </ul>
                  ) : (
                    <p className="mt-2 text-xs text-slate-400">No hay subcategorías con movimientos.</p>
                  )}
                </div>
                <div>
                  <p className="text-sm text-slate-300">Ritmo de gasto</p>
                  {selectedCategoryData.timelineChart.labels.length > 0 ? (
                    <Line
                      data={selectedCategoryData.timelineChart}
                      options={{
                        plugins: { legend: { display: false } },
                        scales: {
                          x: { ticks: { color: '#cbd5f5' } },
                          y: { ticks: { color: '#cbd5f5' } },
                        },
                      }}
                    />
                  ) : (
                    <p className="mt-2 text-xs text-slate-400">Aún no hay datos temporales.</p>
                  )}
                </div>
              </div>
              <div>
                <p className="text-sm text-slate-300">Últimos movimientos</p>
                <div className="mt-2 space-y-2">
                  {selectedCategoryData.recentTransactions.map((tx) => (
                    <div
                      key={tx.id}
                      className="rounded-xl border border-white/5 bg-black/15 px-3 py-2 text-sm text-slate-200"
                    >
                      <div className="flex items-center justify-between">
                        <span>{new Date(tx.transaction_date).toLocaleDateString('es-AR', { day: 'numeric', month: 'short' })}</span>
                        <span className="font-semibold text-rose-200">-{formatAmount(getAmount(tx))}</span>
                      </div>
                      <p className="text-xs text-slate-400">
                        {accountMap[tx.account_id]?.name ?? 'Cuenta'}
                        {tx.notes ? ` · ${tx.notes}` : ''}
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          ) : (
            <p className="mt-4 text-sm text-slate-400">
              Seleccioná una categoría para analizar sus subcategorías, ritmo temporal y últimas operaciones.
            </p>
          )}
        </div>
      </div>


      <div className="rounded-2xl border border-white/5 bg-white/5 p-4">
        <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
          <div>
            <h3 className="text-lg font-semibold">Calendario de gastos</h3>
            <p className="text-sm text-slate-400">{calendarData?.label ?? 'Seleccioná un mes'}</p>
          </div>
          <input
            type="month"
            value={calendarMonth}
            onChange={(e) => setCalendarMonth(e.target.value)}
            className="rounded-xl border border-white/10 bg-black/20 px-3 py-1 text-sm text-white"
          />
        </div>
        {calendarData ? (
          <>
            <div className="grid grid-cols-7 gap-1 text-center text-xs font-semibold text-slate-400">
              {weekDays.map((day) => (
                <span key={day}>{day}</span>
              ))}
            </div>
            <div className="mt-2 grid grid-cols-7 gap-2">
              {calendarData.cells.map((cell, idx) => {
                if (!cell) {
                  return <div key={`empty-${idx}`} className="min-h-[4.5rem] rounded-xl border border-white/5" />;
                }
                const hasTransactions = cell.transactions.length > 0;
                return (
                  <button
                    key={`${calendarMonth}-${cell.day}-${idx}`}
                    type="button"
                    onClick={() => hasTransactions && handleCalendarDayClick(cell)}
                    disabled={!hasTransactions}
                    className={`flex min-h-[4.5rem] flex-col justify-between rounded-2xl border p-2 text-left transition ${
                      heatLevels[cell.level]
                    } ${hasTransactions ? 'hover:-translate-y-0.5 focus:outline-none focus:ring-2 focus:ring-rose-400' : 'opacity-60'}`}
                  >
                    <span className="text-sm font-semibold text-white">{cell.day}</span>
                    <span
                      className={`truncate text-xs font-semibold ${
                        hasTransactions ? 'text-rose-50' : 'text-slate-500'
                      }`}
                    >
                      {hasTransactions ? formatShortAmount(cell.amount) : 'Sin gastos'}
                    </span>
                  </button>
                );
              })}
            </div>
            <div className="mt-4 flex flex-wrap items-center gap-4 text-xs text-slate-400">
              <span>Total mensual: {formatAmount(calendarData.total)}</span>
              <span>Promedio diario: {formatAmount(calendarData.avg)}</span>
              <div className="flex items-center gap-1">
                <span>Nivel:</span>
                {heatLevels.map((cls, index) => (
                  <span key={cls} className={`h-4 w-4 rounded-full border ${cls}`} aria-label={`Nivel ${index}`} />
                ))}
              </div>
            </div>
          </>
        ) : (
          <p className="text-sm text-slate-400">No pudimos construir el calendario para el mes seleccionado.</p>
        )}
      </div>

      <div className="grid gap-6 xl:grid-cols-2">
        <div className="rounded-2xl border border-white/5 bg-white/5 p-4">
          <div className="mb-4 flex items-center justify-between">
            <h3 className="text-lg font-semibold">Distribución de ingresos</h3>
            <span className="text-sm text-slate-300">Total {formatAmount(incomeInsights.total)}</span>
          </div>
          {incomeInsights.entries.length ? (
            <div className="flex flex-col gap-4">
              <div className="mx-auto w-60">
                <Doughnut
                  data={incomeInsights.chart}
                  options={{
                    cutout: '60%',
                    plugins: {
                      legend: { display: false },
                      tooltip: {
                        callbacks: {
                          label: (ctx) => `${ctx.label}: ${formatAmount(Number(ctx.formattedValue))}`,
                        },
                      },
                    },
                  }}
                />
              </div>
              <ul className="flex-1 space-y-2">
                {incomeInsights.entries.map((entry, index) => {
                  const { id, label, value } = entry;
                  const pct = incomeInsights.total ? (value / incomeInsights.total) * 100 : 0;
                  const color = incomeInsights.colors[index % incomeInsights.colors.length];
                  const selected = selectedIncomeCategoryId === id;
                  return (
                    <li key={`${id}-${label}`}>
                      <button
                        type="button"
                        aria-pressed={selected}
                        onClick={() => handleIncomeCategorySelect(id)}
                        className={`flex w-full items-center justify-between rounded-xl border bg-black/20 px-3 py-2 text-left transition ${
                          selected ? 'border-white/40 bg-white/10 shadow-lg shadow-emerald-500/10' : 'border-white/5'
                        }`}
                        style={{ borderColor: selected ? color : undefined }}
                      >
                        <div className="flex items-center gap-3">
                          <span className="text-xl" style={{ textShadow: '0 0 6px rgba(0,0,0,0.3)' }}>💰</span>
                          <div>
                            <p className="font-semibold text-white">{label}</p>
                            <p className="text-xs text-slate-400">{pct.toFixed(1)}%</p>
                          </div>
                        </div>
                        <span className="font-semibold" style={{ color }}>
                          {formatAmount(value)}
                        </span>
                      </button>
                    </li>
                  );
                })}
              </ul>
            </div>
          ) : (
            <p className="text-sm text-slate-400">Todavía no registraste ingresos en este período.</p>
          )}
        </div>
        <div className="rounded-2xl border border-white/5 bg-white/5 p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs uppercase tracking-widest text-slate-400">Detalle por categoría (ingresos)</p>
              <h3 className="text-lg font-semibold">
                {selectedIncomeData ? selectedIncomeData.category.name : 'Elegí una categoría'}
              </h3>
            </div>
          </div>
          {selectedIncomeData ? (
            <div className="mt-4 space-y-4">
              <div>
                <p className="text-3xl font-semibold text-emerald-200">{formatAmount(selectedIncomeData.total)}</p>
                <p className="text-xs text-slate-400">
                  {(selectedIncomeData.share * 100).toFixed(1)}% del ingreso del período · {selectedIncomeData.count} movimientos ·
                  Ticket promedio {formatAmount(selectedIncomeData.avgTicket)}
                </p>
              </div>
              <div className="grid gap-4 md:grid-cols-2">
                <div>
                  <p className="text-sm text-slate-300">Cuentas</p>
                  {selectedIncomeData.accountEntries.length ? (
                    <ul className="mt-2 space-y-2 text-sm text-slate-200">
                      {selectedIncomeData.accountEntries.map((entry) => {
                        const share = selectedIncomeData.total ? (entry.value / selectedIncomeData.total) * 100 : 0;
                        return (
                          <li key={entry.label} className="rounded-xl border border-white/5 bg-black/20 p-3">
                            <div className="flex items-center justify-between">
                              <span>{entry.label}</span>
                              <span className="font-semibold">{formatAmount(entry.value)}</span>
                            </div>
                            <div className="mt-2 h-1.5 rounded-full bg-white/5">
                              <div className="h-full rounded-full bg-emerald-400" style={{ width: `${Math.min(100, share)}%` }} />
                            </div>
                          </li>
                        );
                      })}
                    </ul>
                  ) : (
                    <p className="mt-2 text-xs text-slate-400">No hay cuentas con movimientos.</p>
                  )}
                </div>
                <div>
                  <p className="text-sm text-slate-300">Ritmo de ingreso</p>
                  {selectedIncomeData.timelineChart.labels.length > 0 ? (
                    <Line
                      data={selectedIncomeData.timelineChart}
                      options={{
                        plugins: { legend: { display: false } },
                        scales: {
                          x: { ticks: { color: '#cbd5f5' } },
                          y: { ticks: { color: '#cbd5f5' } },
                        },
                      }}
                    />
                  ) : (
                    <p className="mt-2 text-xs text-slate-400">Aún no hay datos temporales.</p>
                  )}
                </div>
              </div>
              <div>
                <p className="text-sm text-slate-300">Últimos movimientos</p>
                <div className="mt-2 space-y-2">
                  {selectedIncomeData.recentTransactions.map((tx) => (
                    <div
                      key={tx.id}
                      className="rounded-xl border border-white/5 bg-black/15 px-3 py-2 text-sm text-slate-200"
                    >
                      <div className="flex items-center justify-between">
                        <span>{new Date(tx.transaction_date).toLocaleDateString('es-AR', { day: 'numeric', month: 'short' })}</span>
                        <span className="font-semibold text-emerald-200">+{formatAmount(getAmount(tx))}</span>
                      </div>
                      <p className="text-xs text-slate-400">
                        {accountMap[tx.account_id]?.name ?? 'Cuenta'}
                        {tx.notes ? ` · ${tx.notes}` : ''}
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          ) : (
            <p className="mt-4 text-sm text-slate-400">
              Seleccioná una categoría de ingreso para analizar su detalle.
            </p>
          )}
        </div>
      </div>


      {detailOpen && selectedCategoryData && (
        <div className="fixed inset-0 z-50 overflow-y-auto bg-slate-950 px-4 py-8 sm:px-8">
          <div className="mx-auto flex w-full max-w-5xl flex-col space-y-6">
            <div className="flex items-start justify-between gap-4 border-b border-white/10 pb-4">
              <div>
                <p className="text-xs uppercase tracking-widest text-slate-400">Detalle de categoría</p>
                <h2 className="text-2xl font-semibold text-white">{selectedCategoryData.category.name}</h2>
                <p className="text-sm text-slate-400">
                  {selectedCategoryData.count} movimientos en el período seleccionado ·{' '}
                  {(selectedCategoryData.share * 100).toFixed(1)}% del gasto filtrado
                </p>
              </div>
              <button
                type="button"
                onClick={() => setDetailOpen(false)}
                className="rounded-full border border-white/20 px-3 py-1 text-sm text-slate-200 hover:bg-white/10"
              >
                Cerrar
              </button>
            </div>
            <div className="grid gap-4 md:grid-cols-4">
              <div className="rounded-2xl border border-white/10 bg-black/20 p-4">
                <p className="text-xs uppercase tracking-widest text-slate-400">Total período</p>
                <p className="text-2xl font-semibold text-white">{formatAmount(selectedCategoryData.total)}</p>
                {typeof selectedCategoryData.previousTotal === 'number' && (
                  <p className="text-xs text-slate-400">
                    Vs período anterior:{' '}
                    {formatAmount(selectedCategoryData.previousTotal)}{' '}
                    {typeof selectedCategoryData.trend === 'number' ? (
                      <span className={selectedCategoryData.trend >= 0 ? 'text-rose-300' : 'text-emerald-300'}>
                        ({selectedCategoryData.trend >= 0 ? '+' : ''}
                        {(selectedCategoryData.trend * 100).toFixed(1)}%)
                      </span>
                    ) : (
                      <span className="text-slate-500">(sin variación)</span>
                    )}
                  </p>
                )}
              </div>
              <div className="rounded-2xl border border-white/10 bg-black/20 p-4">
                <p className="text-xs uppercase tracking-widest text-slate-400">Ticket promedio</p>
                <p className="text-2xl font-semibold text-white">{formatAmount(selectedCategoryData.avgTicket)}</p>
                <p className="text-xs text-slate-400">Basado en {selectedCategoryData.count} movimientos</p>
              </div>
              <div className="rounded-2xl border border-white/10 bg-black/20 p-4">
                <p className="text-xs uppercase tracking-widest text-slate-400">Movimiento más alto</p>
                <p className="text-2xl font-semibold text-white">
                  {formatAmount(selectedCategoryData.largestAmount)}
                </p>
                <p className="text-xs text-slate-400">
                  {new Date(selectedCategoryData.largestTransaction.transaction_date).toLocaleDateString('es-AR')} ·{' '}
                  {accountMap[selectedCategoryData.largestTransaction.account_id]?.name ?? 'Cuenta'}
                </p>
              </div>
              <div className="rounded-2xl border border-white/10 bg-black/20 p-4">
                <p className="text-xs uppercase tracking-widest text-slate-400">Última actividad</p>
                <p className="text-2xl font-semibold text-white">
                  {formatAmount(getAmount(selectedCategoryData.recentTransactions[0]))}
                </p>
                <p className="text-xs text-slate-400">
                  {new Date(selectedCategoryData.recentTransactions[0].transaction_date).toLocaleString('es-AR')}
                </p>
              </div>
            </div>
            <div className="mt-6 grid gap-6 lg:grid-cols-2">
              <div className="rounded-2xl border border-white/10 bg-black/20 p-4">
                <div className="mb-2 flex items-center justify-between">
                  <h3 className="text-lg font-semibold">Evolución dentro del período</h3>
                  <span className="text-xs text-slate-400">Lineal</span>
                </div>
                {selectedCategoryData.timelineChart.labels.length ? (
                  <Line
                    data={selectedCategoryData.timelineChart}
                    options={{
                      plugins: { legend: { display: false } },
                      scales: { x: { ticks: { color: '#cbd5f5' } }, y: { ticks: { color: '#cbd5f5' } } },
                    }}
                  />
                ) : (
                  <p className="text-sm text-slate-400">No hay suficientes datos para graficar.</p>
                )}
              </div>
              <div className="rounded-2xl border border-white/10 bg-black/20 p-4">
                <div className="mb-2 flex items-center justify-between">
                  <h3 className="text-lg font-semibold">Subcategorías destacadas</h3>
                  <span className="text-xs text-slate-400">Top {selectedCategoryData.subEntries.length}</span>
                </div>
                {selectedCategoryData.subEntries.length ? (
                  <Bar
                    data={{
                      labels: selectedCategoryData.subEntries.map((entry) => entry.label),
                      datasets: [
                        {
                          label: 'Gasto',
                          data: selectedCategoryData.subEntries.map((entry) => entry.value),
                          backgroundColor: '#fb7185',
                        },
                      ],
                    }}
                    options={{
                      plugins: { legend: { display: false } },
                      indexAxis: 'y',
                      scales: { x: { ticks: { color: '#cbd5f5' } }, y: { ticks: { color: '#cbd5f5' } } },
                    }}
                  />
                ) : (
                  <p className="text-sm text-slate-400">No hay subcategorías para mostrar.</p>
                )}
              </div>
            </div>
            <div className="mt-6 grid gap-6 lg:grid-cols-2">
              <div className="rounded-2xl border border-white/10 bg-black/20 p-4">
                <div className="mb-2 flex items-center justify-between">
                  <h3 className="text-lg font-semibold">Cuentas asociadas</h3>
                  <span className="text-xs text-slate-400">Ranking por monto</span>
                </div>
                {selectedCategoryData.accountEntries.length ? (
                  <Bar
                    data={{
                      labels: selectedCategoryData.accountEntries.map((entry) => entry.label),
                      datasets: [
                        {
                          label: 'Gasto',
                          data: selectedCategoryData.accountEntries.map((entry) => entry.value),
                          backgroundColor: '#6366f1',
                        },
                      ],
                    }}
                    options={{
                      plugins: { legend: { display: false } },
                      indexAxis: 'y',
                      scales: { x: { ticks: { color: '#cbd5f5' } }, y: { ticks: { color: '#cbd5f5' } } },
                    }}
                  />
                ) : (
                  <p className="text-sm text-slate-400">No registramos cuentas para esta categoría.</p>
                )}
              </div>
              <div className="rounded-2xl border border-white/10 bg-black/20 p-4">
                <div className="mb-2 flex items-center justify-between">
                  <h3 className="text-lg font-semibold">Transacciones recientes</h3>
                  <span className="text-xs text-slate-400">Últimas 12</span>
                </div>
                <div className="max-h-72 overflow-y-auto pr-2">
                  <table className="w-full text-sm text-slate-200">
                    <thead className="text-xs uppercase text-slate-400">
                      <tr>
                        <th className="py-1 text-left">Fecha</th>
                        <th className="py-1 text-left">Cuenta</th>
                        <th className="py-1 text-left">Detalle</th>
                        <th className="py-1 text-right">Monto</th>
                      </tr>
                    </thead>
                    <tbody>
                      {selectedCategoryData.transactions.slice(0, 12).map((tx) => (
                        <tr key={tx.id} className="border-b border-white/5">
                          <td className="py-1">
                            {new Date(tx.transaction_date).toLocaleDateString('es-AR', {
                              day: '2-digit',
                              month: 'short',
                            })}
                          </td>
                          <td className="py-1">{accountMap[tx.account_id]?.name ?? 'Cuenta'}</td>
                          <td className="py-1 text-slate-400">
                            {tx.subcategory_id ? (categoryMap[tx.subcategory_id]?.name ?? '') : ''}
                            {tx.notes ? ` · ${tx.notes}` : ''}
                          </td>
                         <td className="py-1 text-right font-semibold text-rose-200">
                            {formatAmount(getAmount(tx))}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {selectedDayDetail && (
        <div className="fixed inset-0 z-50 overflow-y-auto bg-slate-950/95 px-4 py-8 sm:px-8">
          <div className="mx-auto w-full max-w-3xl rounded-2xl border border-white/10 bg-black/40 p-6 shadow-xl">
            <div className="flex items-start justify-between gap-4 border-b border-white/10 pb-4">
              <div>
                <p className="text-xs uppercase tracking-widest text-slate-400">Gastos del día</p>
                <h2 className="text-2xl font-semibold text-white">
                  {selectedDayDetail.date.toLocaleDateString('es-AR', {
                    weekday: 'long',
                    day: 'numeric',
                    month: 'long',
                  })}
                </h2>
                <p className="text-sm text-slate-400">
                  Total {formatAmount(selectedDayDetail.total)} · {selectedDayDetail.transactions.length} movimientos
                </p>
              </div>
              <button
                type="button"
                onClick={() => setSelectedDayDetail(null)}
                className="rounded-full border border-white/20 px-3 py-1 text-sm text-slate-200 hover:bg-white/10"
              >
                Cerrar
              </button>
            </div>
            <div className="mt-4 space-y-3">
              {selectedDayDetail.transactions.map((tx) => {
                const cat = tx.category_id ? categoryMap[tx.category_id] : null;
                const account = accountMap[tx.account_id]?.name ?? 'Cuenta';
                const amount = getAmount(tx);
                return (
                  <div
                    key={tx.id}
                    className="rounded-2xl border border-white/10 bg-black/30 px-4 py-3 text-sm text-slate-200"
                  >
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="font-semibold text-white">{cat?.name ?? 'Sin categoría'}</p>
                        <p className="text-xs text-slate-400">
                          {account} · {new Date(tx.transaction_date).toLocaleTimeString('es-AR', {
                            hour: '2-digit',
                            minute: '2-digit',
                          })}
                        </p>
                      </div>
                      <span className="text-sm font-semibold text-rose-200">-{formatAmount(amount)}</span>
                    </div>
                    {tx.notes && <p className="mt-1 text-xs text-slate-400">{tx.notes}</p>}
                  </div>
                );
              })}
              {!selectedDayDetail.transactions.length && (
                <p className="text-sm text-slate-400">No hay movimientos registrados.</p>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
