'use client';

import { useCallback, useEffect, useMemo, useState } from 'react';
import { api } from '@/lib/api';
import type { Budget, Category } from '@/types';

const currencyOptions: Array<'ARS' | 'USD' | 'BTC'> = ['ARS', 'USD', 'BTC'];

const getCurrentMonthValue = () => {
  const now = new Date();
  return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}`;
};

export default function BudgetsPage() {
  const [categories, setCategories] = useState<Category[]>([]);
  const [budget, setBudget] = useState<Budget | null>(null);
  const [drafts, setDrafts] = useState<Record<number, string>>({});
  const [name, setName] = useState('');
  const [selectedMonth, setSelectedMonth] = useState(getCurrentMonthValue);
  const [currency, setCurrency] = useState<'ARS' | 'USD' | 'BTC'>('ARS');
  const [loading, setLoading] = useState(true);
  const [loadingBudget, setLoadingBudget] = useState(false);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  const topLevelCategories = useMemo(() => categories.filter((cat) => !cat.parent_id), [categories]);
  const incomeCategories = topLevelCategories.filter((cat) => cat.type === 'income');
  const expenseCategories = topLevelCategories.filter((cat) => cat.type === 'expense');

  const categoryTypeMap = useMemo(() => {
    const map: Record<number, Category['type']> = {};
    topLevelCategories.forEach((cat) => {
      map[cat.id] = cat.type;
    });
    return map;
  }, [topLevelCategories]);

  const totals = useMemo(() => {
    return Object.entries(drafts).reduce(
      (acc, [categoryId, value]) => {
        const numeric = parseFloat(value);
        if (Number.isNaN(numeric) || numeric <= 0) return acc;
        const type = categoryTypeMap[Number(categoryId)];
        if (type === 'income') acc.income += numeric;
        if (type === 'expense') acc.expense += numeric;
        return acc;
      },
      { income: 0, expense: 0 }
    );
  }, [drafts, categoryTypeMap]);

  const amountFormatter = useMemo(
    () =>
      new Intl.NumberFormat('es-AR', {
        style: 'currency',
        currency,
        maximumFractionDigits: 0,
      }),
    [currency]
  );

  const notify = useCallback((type: 'success' | 'error', text: string) => {
    setMessage({ type, text });
    setTimeout(() => setMessage(null), 4000);
  }, []);

  const loadBudget = useCallback(async () => {
    setLoadingBudget(true);
    try {
      const monthParam = `${selectedMonth}-01`;
      const data = (await api.getBudgets({ month: monthParam, currency })) as Budget[];
      const nextBudget = data.length ? data[0] : null;
      setBudget(nextBudget);
      if (nextBudget) {
        setName(nextBudget.name ?? '');
        const nextDrafts: Record<number, string> = {};
        nextBudget.items.forEach((item) => {
          nextDrafts[item.category_id] = item.amount;
        });
        setDrafts(nextDrafts);
      } else {
        setName('');
        setDrafts({});
      }
    } finally {
      setLoadingBudget(false);
    }
  }, [currency, selectedMonth]);

  useEffect(() => {
    (async () => {
      setLoading(true);
      try {
        const cats = (await api.getCategories()) as Category[];
        setCategories(cats);
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  useEffect(() => {
    if (!loading) {
      loadBudget();
    }
  }, [loading, loadBudget]);

  const handleDraftChange = (categoryId: number, value: string) => {
    setDrafts((prev) => ({ ...prev, [categoryId]: value }));
  };

  const buildPayloadItems = () => {
    return Object.entries(drafts)
      .map(([categoryId, value]) => {
        const numeric = parseFloat(value);
        if (Number.isNaN(numeric) || numeric <= 0) return null;
        return { category_id: Number(categoryId), amount: numeric };
      })
      .filter(Boolean) as Array<{ category_id: number; amount: number }>;
  };

  const handleSave = async () => {
    const items = buildPayloadItems();
    if (!items.length) {
      notify('error', 'Ingresá al menos un monto para guardar.');
      return;
    }
    setSaving(true);
    try {
      const payload = {
        name: name?.trim() || null,
        items,
      };
      if (budget) {
        await api.updateBudget(budget.id, payload);
      } else {
        await api.createBudget({
          month: `${selectedMonth}-01`,
          currency_code: currency,
          name: name?.trim() || null,
          items,
        });
      }
      notify('success', 'Presupuesto guardado.');
      loadBudget();
    } catch (error) {
      notify('error', (error as Error).message);
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async () => {
    if (!budget) return;
    setSaving(true);
    try {
      await api.deleteBudget(budget.id);
      notify('success', 'Presupuesto eliminado.');
      setBudget(null);
      setDrafts({});
      setName('');
    } catch (error) {
      notify('error', (error as Error).message);
    } finally {
      setSaving(false);
    }
  };

  const renderCategoryInputs = (list: Category[]) => {
    if (!list.length) {
      return <p className="text-sm text-slate-400">No hay categorías disponibles.</p>;
    }
    return (
      <div className="space-y-3">
        {list.map((category) => (
          <div
            key={category.id}
            className="flex items-center justify-between rounded-2xl border border-white/5 bg-black/20 px-4 py-3"
          >
            <div>
              <p className="font-semibold text-white">{category.name}</p>
              <p className="text-xs text-slate-400">Objetivo mensual</p>
            </div>
            <input
              type="number"
              min={0}
              step="0.01"
              value={drafts[category.id] ?? ''}
              onChange={(e) => handleDraftChange(category.id, e.target.value)}
              className="w-32 rounded-xl border border-white/10 bg-black/30 px-3 py-2 text-right text-sm"
              placeholder="0"
            />
          </div>
        ))}
      </div>
    );
  };

  if (loading) {
    return <div className="text-slate-300">Cargando categorías...</div>;
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold text-white">Presupuestos</h1>
          <p className="text-sm text-slate-400">Asigná montos objetivo por categoría y moneda.</p>
        </div>
        <div className="flex flex-wrap items-center gap-3">
          <input
            type="month"
            value={selectedMonth}
            onChange={(e) => setSelectedMonth(e.target.value)}
            className="rounded-xl border border-white/10 bg-black/20 px-4 py-2 text-sm"
          />
          <div className="flex gap-2 rounded-full border border-white/10 bg-white/5 p-1">
            {currencyOptions.map((opt) => (
              <button
                key={opt}
                onClick={() => setCurrency(opt)}
                className={`rounded-full px-3 py-1 text-sm font-semibold ${
                  currency === opt ? 'bg-white text-primary' : 'text-slate-300'
                }`}
              >
                {opt}
              </button>
            ))}
          </div>
          <button
            onClick={handleSave}
            disabled={saving || loadingBudget}
            className="rounded-xl bg-gradient-to-r from-emerald-400 to-cyan-400 px-4 py-2 text-sm font-semibold text-primary disabled:opacity-60"
          >
            {saving ? 'Guardando...' : 'Guardar presupuesto'}
          </button>
          {budget && (
            <button
              onClick={handleDelete}
              disabled={saving}
              className="rounded-xl border border-white/10 px-4 py-2 text-sm text-slate-300 hover:bg-white/5 disabled:opacity-40"
            >
              Eliminar
            </button>
          )}
        </div>
      </div>

      {message && (
        <div
          className={`rounded-2xl border px-4 py-2 text-sm ${
            message.type === 'error' ? 'border-rose-500/40 text-rose-200' : 'border-emerald-500/40 text-emerald-200'
          }`}
        >
          {message.text}
        </div>
      )}

      <div className="rounded-2xl border border-white/5 bg-white/5 p-4">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <p className="text-sm text-slate-300">Nombre del presupuesto</p>
            <input
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Ej. Febrero 2024"
              className="mt-1 w-full rounded-xl border border-white/10 bg-black/20 px-4 py-2 text-sm"
            />
          </div>
            <div className="flex gap-6 text-sm text-slate-300">
              <div>
                <p className="text-xs uppercase tracking-widest text-emerald-300">Ingresos objetivo</p>
                <p className="text-lg font-semibold text-white">{amountFormatter.format(totals.income)}</p>
              </div>
              <div>
                <p className="text-xs uppercase tracking-widest text-rose-300">Gastos objetivo</p>
                <p className="text-lg font-semibold text-white">{amountFormatter.format(totals.expense)}</p>
              </div>
            </div>
          </div>
        </div>

      {loadingBudget ? (
        <div className="text-sm text-slate-400">Cargando presupuesto...</div>
      ) : (
        <div className="grid gap-6 lg:grid-cols-2">
          <section className="rounded-2xl border border-white/5 bg-white/5 p-4">
            <h2 className="mb-3 text-lg font-semibold text-white">Ingresos</h2>
            {renderCategoryInputs(incomeCategories)}
          </section>
          <section className="rounded-2xl border border-white/5 bg-white/5 p-4">
            <h2 className="mb-3 text-lg font-semibold text-white">Gastos</h2>
            {renderCategoryInputs(expenseCategories)}
          </section>
        </div>
      )}
    </div>
  );
}
