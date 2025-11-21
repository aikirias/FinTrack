'use client';

import { FormEvent, useEffect, useState } from 'react';
import { api } from '@/lib/api';
import type { Account, Category } from '@/types';

export default function NewTransactionPage() {
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [transactionType, setTransactionType] = useState<'income' | 'expense' | 'transfer'>('expense');
  const [result, setResult] = useState<string | null>(null);
  const [form, setForm] = useState({
    account_id: '',
    target_account_id: '',
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

  useEffect(() => {
    setForm((prev) => ({ ...prev, category_id: '', subcategory_id: '' }));
  }, [transactionType]);

  const flatCategories = categories.map((cat) => ({ id: cat.id, name: cat.name, type: cat.type, children: cat.children ?? [] }));
  const filteredParents = flatCategories.filter((cat) => cat.type === transactionType);

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    setResult(null);
    if (!form.account_id || !form.amount_original || (transactionType === 'transfer' && !form.target_account_id)) {
      setResult('Completá los campos obligatorios.');
      return;
    }
    if (transactionType === 'transfer' && form.target_account_id === form.account_id) {
      setResult('Elegí dos cuentas distintas para transferir.');
      return;
    }
    const timestamp = new Date(`${form.date}T${form.time}:00`).toISOString();
    const makePayload = (payload: Record<string, unknown>) => ({
      transaction_date: timestamp,
      currency_code: form.currency_code,
      rate_type: form.rate_type,
      amount_original: form.amount_original,
      notes: form.notes || null,
      ...payload,
    });

    if (transactionType === 'transfer') {
      await api.createTransaction(
        makePayload({
          account_id: Number(form.account_id),
          category_id: null,
          subcategory_id: null,
        })
      );
      await api.createTransaction(
        makePayload({
          account_id: Number(form.target_account_id),
          category_id: null,
          subcategory_id: null,
          amount_original: String(-Number(form.amount_original)),
        })
      );
    } else {
      await api.createTransaction(
        makePayload({
          account_id: Number(form.account_id),
          category_id: form.category_id ? Number(form.category_id) : null,
          subcategory_id: form.subcategory_id ? Number(form.subcategory_id) : null,
        })
      );
    }
    setResult('Movimiento registrado');
    setForm({ ...form, amount_original: '', notes: '', category_id: '', subcategory_id: '', target_account_id: '' });
  };

  const selectedParent = flatCategories.find((cat) => String(cat.id) === form.category_id);

  return (
    <div className="max-w-3xl space-y-6 pb-10">
      <h1 className="text-2xl font-semibold">Nueva transacción</h1>
      <form onSubmit={handleSubmit} className="space-y-4 rounded-2xl border border-white/5 bg-white/5 p-4 md:p-6">
        <div className="flex flex-wrap gap-2 rounded-full border border-white/10 bg-black/20 p-1">
          {(['expense', 'income', 'transfer'] as const).map((type) => (
            <button
              key={type}
              type="button"
              onClick={() => setTransactionType(type)}
              className={`rounded-full px-4 py-1 text-sm font-semibold ${
                transactionType === type ? 'bg-white text-primary' : 'text-slate-200'
              }`}
            >
              {type === 'expense' ? 'Gasto' : type === 'income' ? 'Ingreso' : 'Transferencia'}
            </button>
          ))}
        </div>
        <div className={`grid gap-4 ${transactionType === 'transfer' ? 'grid-cols-1 sm:grid-cols-3' : 'grid-cols-1 sm:grid-cols-2'}`}>
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
          {transactionType === 'transfer' && (
            <div>
              <label className="text-sm text-slate-300">Cuenta destino</label>
              <select
                className="mt-1 w-full rounded-xl border border-white/10 bg-black/20 px-4 py-2"
                value={form.target_account_id}
                onChange={(e) => setForm({ ...form, target_account_id: e.target.value })}
                required
              >
                <option value="">Seleccioná cuenta</option>
                {accounts
                  .filter((account) => account.id !== Number(form.account_id))
                  .map((account) => (
                    <option key={account.id} value={account.id}>
                      {account.name}
                    </option>
                  ))}
              </select>
            </div>
          )}
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
              {filteredParents.map((cat) => (
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
