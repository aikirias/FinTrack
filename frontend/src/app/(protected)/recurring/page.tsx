'use client';

import { useEffect, useState } from 'react';
import { api } from '@/lib/api';
import type { Account, Category, RecurringTransaction } from '@/types';

const FREQUENCY_LABELS: Record<string, string> = {
  daily: 'Diaria',
  weekly: 'Semanal',
  monthly: 'Mensual',
  yearly: 'Anual',
};

const CURRENCIES = ['ARS', 'USD', 'BTC'];
const RATE_TYPES = [
  { value: 'official', label: 'Oficial' },
  { value: 'blue', label: 'Blue' },
];

interface FormState {
  name: string;
  account_id: string;
  category_id: string;
  subcategory_id: string;
  amount_original: string;
  currency_code: string;
  rate_type: string;
  notes: string;
  frequency: string;
  next_run_date: string;
}

const emptyForm = (): FormState => ({
  name: '',
  account_id: '',
  category_id: '',
  subcategory_id: '',
  amount_original: '',
  currency_code: 'ARS',
  rate_type: 'official',
  notes: '',
  frequency: 'monthly',
  next_run_date: new Date().toISOString().slice(0, 10),
});

export default function RecurringPage() {
  const [items, setItems] = useState<RecurringTransaction[]>([]);
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [form, setForm] = useState<FormState>(emptyForm());
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = async () => {
    setLoading(true);
    try {
      const [rts, accs, cats] = await Promise.all([
        api.getRecurringTransactions() as Promise<RecurringTransaction[]>,
        api.getAccounts() as Promise<Account[]>,
        api.getCategories() as Promise<Category[]>,
      ]);
      setItems(rts);
      setAccounts(accs);
      setCategories(cats);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  const parentCategories = categories.filter((c) => c.parent_id == null && !c.is_archived);
  const selectedCategory = categories.find((c) => c.id === Number(form.category_id));
  const subCategories = selectedCategory
    ? categories.filter((c) => c.parent_id === selectedCategory.id && !c.is_archived)
    : [];

  const openCreate = () => {
    setEditingId(null);
    setForm(emptyForm());
    setError(null);
    setShowForm(true);
  };

  const openEdit = (rt: RecurringTransaction) => {
    setEditingId(rt.id);
    setForm({
      name: rt.name,
      account_id: rt.account_id != null ? String(rt.account_id) : '',
      category_id: rt.category_id != null ? String(rt.category_id) : '',
      subcategory_id: rt.subcategory_id != null ? String(rt.subcategory_id) : '',
      amount_original: rt.amount_original,
      currency_code: rt.currency_code,
      rate_type: rt.rate_type,
      notes: rt.notes ?? '',
      frequency: rt.frequency,
      next_run_date: rt.next_run_date,
    });
    setError(null);
    setShowForm(true);
  };

  const handleSave = async () => {
    if (!form.name.trim() || !form.amount_original || !form.next_run_date) {
      setError('Completá nombre, monto y fecha de inicio.');
      return;
    }
    setSaving(true);
    setError(null);
    try {
      const payload: Record<string, unknown> = {
        name: form.name.trim(),
        account_id: form.account_id ? Number(form.account_id) : null,
        category_id: form.category_id ? Number(form.category_id) : null,
        subcategory_id: form.subcategory_id ? Number(form.subcategory_id) : null,
        amount_original: form.amount_original,
        currency_code: form.currency_code,
        rate_type: form.rate_type,
        notes: form.notes.trim() || null,
        frequency: form.frequency,
        next_run_date: form.next_run_date,
      };
      if (editingId != null) {
        await api.updateRecurringTransaction(editingId, payload);
      } else {
        await api.createRecurringTransaction(payload);
      }
      setShowForm(false);
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setSaving(false);
    }
  };

  const handleToggle = async (rt: RecurringTransaction) => {
    try {
      await api.updateRecurringTransaction(rt.id, { is_active: !rt.is_active });
      await load();
    } catch {
      // silent
    }
  };

  const handleDelete = async (rt: RecurringTransaction) => {
    if (!confirm(`¿Eliminar "${rt.name}"?`)) return;
    try {
      await api.deleteRecurringTransaction(rt.id);
      await load();
    } catch {
      // silent
    }
  };

  const f = (v: string, key: keyof FormState) => setForm((prev) => ({ ...prev, [key]: v }));

  const inputCls = 'w-full rounded-xl border border-white/10 bg-white/5 px-3 py-2 text-sm text-white focus:outline-none';
  const labelCls = 'mb-1 block text-xs text-slate-400';

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-white">Transacciones recurrentes</h1>
        <button
          onClick={openCreate}
          className="rounded-xl bg-gradient-to-r from-emerald-400 to-teal-500 px-4 py-2 text-sm font-semibold text-white shadow"
        >
          + Nueva
        </button>
      </div>

      {showForm && (
        <div className="rounded-2xl border border-white/10 bg-secondary/80 p-6 shadow-xl">
          <h2 className="mb-4 text-lg font-semibold text-white">
            {editingId != null ? 'Editar recurrente' : 'Nueva transacción recurrente'}
          </h2>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <div className="sm:col-span-2">
              <label className={labelCls}>Nombre</label>
              <input className={inputCls} value={form.name} onChange={(e) => f(e.target.value, 'name')} placeholder="Ej: Sueldo, Alquiler..." />
            </div>
            <div>
              <label className={labelCls}>Cuenta</label>
              <select className={inputCls} value={form.account_id} onChange={(e) => f(e.target.value, 'account_id')}>
                <option value="">Sin cuenta</option>
                {accounts.filter((a) => !a.is_archived).map((a) => (
                  <option key={a.id} value={a.id}>{a.name}</option>
                ))}
              </select>
            </div>
            <div>
              <label className={labelCls}>Categoría</label>
              <select
                className={inputCls}
                value={form.category_id}
                onChange={(e) => { f(e.target.value, 'category_id'); f('', 'subcategory_id'); }}
              >
                <option value="">Sin categoría</option>
                {parentCategories.map((c) => (
                  <option key={c.id} value={c.id}>{c.name} ({c.type === 'income' ? 'ingreso' : c.type === 'expense' ? 'gasto' : 'transfer'})</option>
                ))}
              </select>
            </div>
            {subCategories.length > 0 && (
              <div>
                <label className={labelCls}>Subcategoría</label>
                <select className={inputCls} value={form.subcategory_id} onChange={(e) => f(e.target.value, 'subcategory_id')}>
                  <option value="">Sin subcategoría</option>
                  {subCategories.map((c) => (
                    <option key={c.id} value={c.id}>{c.name}</option>
                  ))}
                </select>
              </div>
            )}
            <div>
              <label className={labelCls}>Monto</label>
              <input className={inputCls} type="number" step="any" min="0" value={form.amount_original} onChange={(e) => f(e.target.value, 'amount_original')} placeholder="0.00" />
            </div>
            <div>
              <label className={labelCls}>Moneda</label>
              <select className={inputCls} value={form.currency_code} onChange={(e) => f(e.target.value, 'currency_code')}>
                {CURRENCIES.map((c) => <option key={c} value={c}>{c}</option>)}
              </select>
            </div>
            <div>
              <label className={labelCls}>Tipo de tasa</label>
              <select className={inputCls} value={form.rate_type} onChange={(e) => f(e.target.value, 'rate_type')}>
                {RATE_TYPES.map((r) => <option key={r.value} value={r.value}>{r.label}</option>)}
              </select>
            </div>
            <div>
              <label className={labelCls}>Frecuencia</label>
              <select className={inputCls} value={form.frequency} onChange={(e) => f(e.target.value, 'frequency')}>
                {Object.entries(FREQUENCY_LABELS).map(([v, l]) => (
                  <option key={v} value={v}>{l}</option>
                ))}
              </select>
            </div>
            <div>
              <label className={labelCls}>Próxima ejecución</label>
              <input className={inputCls} type="date" value={form.next_run_date} onChange={(e) => f(e.target.value, 'next_run_date')} />
            </div>
            <div className="sm:col-span-2">
              <label className={labelCls}>Notas</label>
              <input className={inputCls} value={form.notes} onChange={(e) => f(e.target.value, 'notes')} placeholder="Opcional..." />
            </div>
          </div>
          {error && <p className="mt-3 text-sm text-rose-400">{error}</p>}
          <div className="mt-4 flex gap-3">
            <button
              onClick={handleSave}
              disabled={saving}
              className="rounded-xl bg-gradient-to-r from-emerald-400 to-teal-500 px-5 py-2 text-sm font-semibold text-white disabled:opacity-50"
            >
              {saving ? 'Guardando...' : 'Guardar'}
            </button>
            <button
              onClick={() => setShowForm(false)}
              className="rounded-xl border border-white/10 px-5 py-2 text-sm text-slate-300 hover:bg-white/5"
            >
              Cancelar
            </button>
          </div>
        </div>
      )}

      {loading ? (
        <p className="text-slate-400">Cargando...</p>
      ) : items.length === 0 ? (
        <div className="rounded-2xl border border-white/10 bg-secondary/60 p-10 text-center">
          <p className="text-slate-400">No hay transacciones recurrentes configuradas.</p>
          <p className="mt-1 text-sm text-slate-500">Usá "+ Nueva" para agregar pagos o cobros recurrentes.</p>
        </div>
      ) : (
        <div className="overflow-hidden rounded-2xl border border-white/10">
          <table className="w-full text-sm text-slate-300">
            <thead className="border-b border-white/10 bg-white/5 text-xs text-slate-400">
              <tr>
                <th className="px-4 py-3 text-left">Nombre</th>
                <th className="px-4 py-3 text-left">Categoría</th>
                <th className="px-4 py-3 text-right">Monto</th>
                <th className="px-4 py-3 text-center">Frec.</th>
                <th className="px-4 py-3 text-center">Próxima</th>
                <th className="px-4 py-3 text-center">Estado</th>
                <th className="px-4 py-3 text-center">Acciones</th>
              </tr>
            </thead>
            <tbody>
              {items.map((rt) => {
                const cat = categories.find((c) => c.id === rt.category_id);
                const isIncome = cat?.type === 'income';
                return (
                  <tr key={rt.id} className={`border-b border-white/5 transition hover:bg-white/5 ${!rt.is_active ? 'opacity-50' : ''}`}>
                    <td className="px-4 py-3 font-medium text-white">{rt.name}</td>
                    <td className="px-4 py-3">
                      {cat ? (
                        <span className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-medium ${isIncome ? 'bg-emerald-500/20 text-emerald-300' : 'bg-rose-500/20 text-rose-300'}`}>
                          {isIncome ? '▲' : '▼'} {cat.name}
                        </span>
                      ) : (
                        <span className="text-slate-500">—</span>
                      )}
                    </td>
                    <td className="px-4 py-3 text-right font-mono">
                      <span className={isIncome ? 'text-emerald-400' : 'text-rose-400'}>
                        {isIncome ? '+' : '-'}{Number(rt.amount_original).toLocaleString('es-AR')} {rt.currency_code}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-center">{FREQUENCY_LABELS[rt.frequency] ?? rt.frequency}</td>
                    <td className="px-4 py-3 text-center">{rt.next_run_date}</td>
                    <td className="px-4 py-3 text-center">
                      <button
                        onClick={() => handleToggle(rt)}
                        className={`rounded-full px-2 py-0.5 text-xs font-medium transition ${rt.is_active ? 'bg-emerald-500/20 text-emerald-300 hover:bg-emerald-500/30' : 'bg-slate-500/20 text-slate-400 hover:bg-slate-500/30'}`}
                      >
                        {rt.is_active ? 'Activa' : 'Inactiva'}
                      </button>
                    </td>
                    <td className="px-4 py-3 text-center">
                      <div className="flex justify-center gap-2">
                        <button
                          onClick={() => openEdit(rt)}
                          className="rounded-lg px-2 py-1 text-xs text-sky-400 hover:bg-white/5"
                        >
                          Editar
                        </button>
                        <button
                          onClick={() => handleDelete(rt)}
                          className="rounded-lg px-2 py-1 text-xs text-rose-400 hover:bg-white/5"
                        >
                          Eliminar
                        </button>
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
