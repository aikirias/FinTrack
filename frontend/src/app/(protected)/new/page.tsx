'use client';

import { FormEvent, useEffect, useState } from 'react';
import { api } from '@/lib/api';
import type { Account, Category } from '@/types';

export default function NewTransactionPage() {
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [result, setResult] = useState<string | null>(null);
  const [form, setForm] = useState({
    account_id: '',
    category_id: '',
    subcategory_id: '',
    currency_code: 'ARS',
    rate_type: 'official',
    amount_original: '',
    date: new Date().toISOString().slice(0, 10),
    time: new Date().toISOString().slice(11, 16),
    notes: '',
  });

  useEffect(() => {
    (async () => {
      const [acct, cats] = await Promise.all([api.getAccounts(), api.getCategories()]);
      setAccounts(acct as Account[]);
      setCategories(cats as Category[]);
    })();
  }, []);

  const flatCategories = categories.map((cat) => ({ id: cat.id, name: cat.name, type: cat.type, children: cat.children ?? [] }));

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    setResult(null);
    if (!form.account_id || !form.amount_original) {
      setResult('Completá los campos obligatorios.');
      return;
    }
    const timestamp = new Date(`${form.date}T${form.time}:00`).toISOString();
    await api.createTransaction({
      transaction_date: timestamp,
      account_id: Number(form.account_id),
      currency_code: form.currency_code,
      rate_type: form.rate_type,
      amount_original: form.amount_original,
      category_id: form.category_id ? Number(form.category_id) : null,
      subcategory_id: form.subcategory_id ? Number(form.subcategory_id) : null,
      notes: form.notes || null,
    });
    setResult('Movimiento registrado');
    setForm({ ...form, amount_original: '', notes: '' });
  };

  const selectedParent = flatCategories.find((cat) => String(cat.id) === form.category_id);

  return (
    <div className="max-w-3xl space-y-6">
      <h1 className="text-2xl font-semibold">Nueva transacción</h1>
      <form onSubmit={handleSubmit} className="space-y-4 rounded-2xl border border-white/5 bg-white/5 p-6">
        <div className="grid gap-4 sm:grid-cols-2">
          <div>
            <label className="text-sm text-slate-300">Cuenta</label>
            <select
              className="mt-1 w-full rounded-xl border border-white/10 bg-black/20 px-4 py-2"
              value={form.account_id}
              onChange={(e) => setForm({ ...form, account_id: e.target.value })}
              required
            >
              <option value="">Seleccioná cuenta</option>
              {accounts.map((account) => (
                <option key={account.id} value={account.id}>
                  {account.name}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="text-sm text-slate-300">Moneda</label>
            <select
              className="mt-1 w-full rounded-xl border border-white/10 bg-black/20 px-4 py-2"
              value={form.currency_code}
              onChange={(e) => setForm({ ...form, currency_code: e.target.value })}
            >
              <option value="ARS">ARS</option>
              <option value="USD">USD</option>
              <option value="BTC">BTC</option>
            </select>
          </div>
        </div>
        <div className="grid gap-4 sm:grid-cols-2">
          <div>
            <label className="text-sm text-slate-300">Monto</label>
            <input
              className="mt-1 w-full rounded-xl border border-white/10 bg-black/20 px-4 py-2"
              type="number"
              step="0.01"
              value={form.amount_original}
              onChange={(e) => setForm({ ...form, amount_original: e.target.value })}
              required
            />
          </div>
          <div>
            <label className="text-sm text-slate-300">Tipo de cambio</label>
            <select
              className="mt-1 w-full rounded-xl border border-white/10 bg-black/20 px-4 py-2"
              value={form.rate_type}
              onChange={(e) => setForm({ ...form, rate_type: e.target.value })}
            >
              <option value="official">Oficial</option>
              <option value="blue">Blue</option>
            </select>
          </div>
        </div>
        <div className="grid gap-4 sm:grid-cols-2">
          <div>
            <label className="text-sm text-slate-300">Fecha</label>
            <input
              type="date"
              className="mt-1 w-full rounded-xl border border-white/10 bg-black/20 px-4 py-2"
              value={form.date}
              onChange={(e) => setForm({ ...form, date: e.target.value })}
            />
          </div>
          <div>
            <label className="text-sm text-slate-300">Hora</label>
            <input
              type="time"
              className="mt-1 w-full rounded-xl border border-white/10 bg-black/20 px-4 py-2"
              value={form.time}
              onChange={(e) => setForm({ ...form, time: e.target.value })}
            />
          </div>
        </div>
        <div className="grid gap-4 sm:grid-cols-2">
          <div>
            <label className="text-sm text-slate-300">Categoría</label>
            <select
              className="mt-1 w-full rounded-xl border border-white/10 bg-black/20 px-4 py-2"
              value={form.category_id}
              onChange={(e) => setForm({ ...form, category_id: e.target.value, subcategory_id: '' })}
            >
              <option value="">Sin categoría</option>
              {flatCategories.map((cat) => (
                <option key={cat.id} value={cat.id}>
                  {cat.name}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="text-sm text-slate-300">Subcategoría</label>
            <select
              className="mt-1 w-full rounded-xl border border-white/10 bg-black/20 px-4 py-2"
              value={form.subcategory_id}
              onChange={(e) => setForm({ ...form, subcategory_id: e.target.value })}
            >
              <option value="">Sin subcategoría</option>
              {selectedParent?.children?.map((child) => (
                <option key={child.id} value={child.id}>
                  {child.name}
                </option>
              ))}
            </select>
          </div>
        </div>
        <div>
          <label className="text-sm text-slate-300">Notas</label>
          <textarea
            className="mt-1 w-full rounded-xl border border-white/10 bg-black/20 px-4 py-2"
            rows={3}
            value={form.notes}
            onChange={(e) => setForm({ ...form, notes: e.target.value })}
          />
        </div>
        <button type="submit" className="w-full rounded-xl bg-gradient-to-r from-emerald-400 to-teal-500 py-2 font-semibold">
          Guardar
        </button>
        {result && <p className="text-center text-sm text-emerald-300">{result}</p>}
      </form>
    </div>
  );
}
