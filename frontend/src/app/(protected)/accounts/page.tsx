'use client';

import { useEffect, useState } from 'react';
import { api } from '@/lib/api';
import type { Account } from '@/types';

export default function AccountsPage() {
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [form, setForm] = useState({ name: '', currency_code: 'ARS', description: '' });

  const load = async () => {
    const data = (await api.getAccounts()) as Account[];
    setAccounts(data);
  };

  useEffect(() => {
    load();
  }, []);

  const handleSubmit = async () => {
    if (!form.name.trim()) return;
    await api.createAccount({ ...form, description: form.description || null });
    setForm({ name: '', currency_code: 'ARS', description: '' });
    load();
  };

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold">Cuentas</h1>
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {accounts.map((account) => (
          <div key={account.id} className="rounded-2xl border border-white/5 bg-white/5 p-4">
            <p className="text-sm text-slate-400">{account.currency_code}</p>
            <p className="text-xl font-semibold text-white">{account.name}</p>
            <p className="text-xs text-slate-500">{account.description ?? 'Sin descripción'}</p>
            <span className="mt-2 inline-block rounded-full border border-white/10 px-3 py-1 text-xs text-slate-300">
              {account.is_archived ? 'Archivada' : 'Activa'}
            </span>
          </div>
        ))}
      </div>
      <section className="rounded-2xl border border-white/5 bg-white/5 p-4">
        <h2 className="mb-4 text-lg font-semibold">Nueva cuenta</h2>
        <div className="grid gap-3 sm:grid-cols-3">
          <input
            value={form.name}
            onChange={(e) => setForm({ ...form, name: e.target.value })}
            placeholder="Nombre"
            className="rounded-xl border border-white/10 bg-black/20 px-4 py-2"
          />
          <select
            value={form.currency_code}
            onChange={(e) => setForm({ ...form, currency_code: e.target.value })}
            className="rounded-xl border border-white/10 bg-black/20 px-4 py-2"
          >
            <option value="ARS">ARS</option>
            <option value="USD">USD</option>
            <option value="BTC">BTC</option>
          </select>
          <input
            value={form.description}
            onChange={(e) => setForm({ ...form, description: e.target.value })}
            placeholder="Descripción"
            className="rounded-xl border border-white/10 bg-black/20 px-4 py-2"
          />
        </div>
        <button
          onClick={handleSubmit}
          className="mt-4 rounded-xl bg-gradient-to-r from-sky-500 to-cyan-400 px-4 py-2 font-semibold"
        >
          Guardar cuenta
        </button>
      </section>
    </div>
  );
}
