'use client';

import { useEffect, useMemo, useState } from 'react';
import { api } from '@/lib/api';
import type { Account, Category, Transaction } from '@/types';

const arsFormatter = new Intl.NumberFormat('es-AR', { style: 'currency', currency: 'ARS' });
const usdFormatter = new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' });
const btcFormatter = new Intl.NumberFormat('en-US', { minimumFractionDigits: 8, maximumFractionDigits: 8 });

export default function AccountsPage() {
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [loading, setLoading] = useState(true);
  const [form, setForm] = useState({ name: '', currency_code: 'ARS', description: '' });
  const [editingId, setEditingId] = useState<number | null>(null);
  const [editForm, setEditForm] = useState({ name: '', currency_code: 'ARS', description: '' });
  const [savingEdit, setSavingEdit] = useState(false);
  const [actionLoading, setActionLoading] = useState<number | null>(null);
  const [message, setMessage] = useState<{ text: string; type: 'success' | 'error' } | null>(null);

  const load = async () => {
    setLoading(true);
    try {
      const [acct, txs, cats] = await Promise.all([
        api.getAccounts(),
        api.getTransactions(),
        api.getCategories(),
      ]);
      setAccounts(acct as Account[]);
      setTransactions(txs as Transaction[]);
      setCategories(cats as Category[]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  useEffect(() => {
    if (!message) return;
    const timeout = setTimeout(() => setMessage(null), 4000);
    return () => clearTimeout(timeout);
  }, [message]);

  const categoryTypeMap = useMemo(() => {
    const map: Record<number, Category['type'] | undefined> = {};
    const walk = (nodes: Category[]) => {
      nodes.forEach((cat) => {
        map[cat.id] = cat.type;
        if (cat.children) walk(cat.children);
      });
    };
    walk(categories);
    return map;
  }, [categories]);

  const accountMap = useMemo(() => {
    const map: Record<number, Account> = {};
    accounts.forEach((acc) => {
      map[acc.id] = acc;
    });
    return map;
  }, [accounts]);

  const balanceMap = useMemo(() => {
    const map: Record<number, number> = {};
    transactions.forEach((tx) => {
      const account = accountMap[tx.account_id];
      if (!account) return;
      const categoryType = tx.category_id ? categoryTypeMap[tx.category_id] : undefined;
      if (categoryType !== 'income' && categoryType !== 'expense') return;
      let amount = 0;
      if (account.currency_code === 'USD') amount = parseFloat(tx.amount_usd);
      else if (account.currency_code === 'BTC') amount = parseFloat(tx.amount_btc);
      else amount = parseFloat(tx.amount_ars);
      if (Number.isNaN(amount)) amount = 0;
      map[account.id] = (map[account.id] || 0) + (categoryType === 'income' ? amount : -amount);
    });
    return map;
  }, [transactions, accountMap, categoryTypeMap]);

  const getBalance = (accountId: number) => balanceMap[accountId] ?? 0;
  const hasBalance = (accountId: number) => Math.abs(getBalance(accountId)) > 0.01;

  const formatByCurrency = (code: string, value: number) => {
    const adjusted = Math.abs(value) < 0.00001 ? 0 : value;
    if (code === 'USD') return usdFormatter.format(adjusted);
    if (code === 'BTC') return `${btcFormatter.format(adjusted)} BTC`;
    return arsFormatter.format(adjusted);
  };

  const handleSubmit = async () => {
    if (!form.name.trim()) return;
    try {
      await api.createAccount({ ...form, description: form.description || null });
      setForm({ name: '', currency_code: 'ARS', description: '' });
      setMessage({ type: 'success', text: 'Cuenta creada correctamente.' });
      await load();
    } catch (error) {
      setMessage({ type: 'error', text: (error as Error).message });
    }
  };

  const startEdit = (account: Account) => {
    setEditingId(account.id);
    setEditForm({
      name: account.name,
      currency_code: account.currency_code,
      description: account.description ?? '',
    });
  };

  const handleUpdate = async () => {
    if (!editingId || !editForm.name.trim()) return;
    setSavingEdit(true);
    try {
      await api.updateAccount(editingId, {
        name: editForm.name,
        currency_code: editForm.currency_code,
        description: editForm.description || null,
      });
      setEditingId(null);
      setEditForm({ name: '', currency_code: 'ARS', description: '' });
      setMessage({ type: 'success', text: 'Cuenta actualizada.' });
      await load();
    } catch (error) {
      setMessage({ type: 'error', text: (error as Error).message });
    } finally {
      setSavingEdit(false);
    }
  };

  const handleArchiveToggle = async (account: Account) => {
    const goingToArchive = !account.is_archived;
    if (goingToArchive && hasBalance(account.id)) {
      setMessage({ type: 'error', text: 'No podés suspender una cuenta con saldo.' });
      return;
    }
    setActionLoading(account.id);
    try {
      await api.updateAccount(account.id, { is_archived: !account.is_archived });
      setMessage({ type: 'success', text: account.is_archived ? 'Cuenta reactivada.' : 'Cuenta suspendida.' });
      await load();
    } catch (error) {
      setMessage({ type: 'error', text: (error as Error).message });
    } finally {
      setActionLoading(null);
    }
  };

  const handleDelete = async (account: Account) => {
    if (hasBalance(account.id)) {
      setMessage({ type: 'error', text: 'No podés eliminar una cuenta con saldo.' });
      return;
    }
    if (!window.confirm(`¿Eliminar "${account.name}"? Se ocultará pero su historial seguirá disponible.`)) {
      return;
    }
    setActionLoading(account.id);
    try {
      await api.updateAccount(account.id, { is_archived: true });
      setMessage({ type: 'success', text: 'Cuenta eliminada (soft delete).' });
      await load();
    } catch (error) {
      setMessage({ type: 'error', text: (error as Error).message });
    } finally {
      setActionLoading(null);
    }
  };

  if (loading) {
    return <div className="text-slate-300">Cargando cuentas...</div>;
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold">Cuentas</h1>
        <p className="text-sm text-slate-400">Gestioná tus cuentas, saldos y estados.</p>
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
      <div className="overflow-auto rounded-2xl border border-white/5">
        <table className="min-w-full text-sm">
          <thead className="bg-white/5 text-left text-xs uppercase text-slate-400">
            <tr>
              <th className="px-4 py-3">Nombre</th>
              <th className="px-4 py-3">Moneda</th>
              <th className="px-4 py-3">Balance</th>
              <th className="px-4 py-3">Estado</th>
              <th className="px-4 py-3">Acciones</th>
            </tr>
          </thead>
          <tbody>
            {accounts.map((account) => {
              const balance = getBalance(account.id);
              const balanceLabel =
                balance === 0 ? '0' : formatByCurrency(account.currency_code, balance);
              const isEditing = editingId === account.id;
              return (
                <tr key={account.id} className="border-t border-white/5">
                  <td className="px-4 py-3 align-top">
                    {isEditing ? (
                      <div className="space-y-2">
                        <input
                          value={editForm.name}
                          onChange={(e) => setEditForm({ ...editForm, name: e.target.value })}
                          className="w-full rounded-xl border border-white/10 bg-black/20 px-3 py-2 text-white"
                        />
                        <textarea
                          value={editForm.description}
                          onChange={(e) => setEditForm({ ...editForm, description: e.target.value })}
                          className="w-full rounded-xl border border-white/10 bg-black/20 px-3 py-2 text-sm text-slate-200"
                          placeholder="Descripción"
                        />
                      </div>
                    ) : (
                      <>
                        <p className="font-semibold text-white">{account.name}</p>
                        <p className="text-xs text-slate-400">{account.description ?? 'Sin descripción'}</p>
                      </>
                    )}
                  </td>
                  <td className="px-4 py-3 align-top">
                    {isEditing ? (
                      <select
                        value={editForm.currency_code}
                        onChange={(e) => setEditForm({ ...editForm, currency_code: e.target.value })}
                        className="rounded-xl border border-white/10 bg-black/20 px-3 py-2 text-white"
                      >
                        <option value="ARS">ARS</option>
                        <option value="USD">USD</option>
                        <option value="BTC">BTC</option>
                      </select>
                    ) : (
                      <span className="rounded-full border border-white/10 px-3 py-1 text-xs text-slate-200">
                        {account.currency_code}
                      </span>
                    )}
                  </td>
                  <td className="px-4 py-3 align-top">
                    <span className={balance >= 0 ? 'text-emerald-300' : 'text-rose-300'}>{balanceLabel}</span>
                  </td>
                  <td className="px-4 py-3 align-top">
                    <span
                      className={`rounded-full px-3 py-1 text-xs ${
                        account.is_archived ? 'border border-white/10 text-slate-400' : 'bg-emerald-500/20 text-emerald-200'
                      }`}
                    >
                      {account.is_archived ? 'Suspendida' : 'Activa'}
                    </span>
                  </td>
                  <td className="px-4 py-3 align-top">
                    {isEditing ? (
                      <div className="flex flex-wrap gap-2">
                        <button
                          className="rounded-full border border-white/10 px-3 py-1 text-xs text-white hover:bg-white/10"
                          onClick={handleUpdate}
                          disabled={savingEdit}
                        >
                          {savingEdit ? 'Guardando...' : 'Guardar'}
                        </button>
                        <button
                          className="rounded-full border border-white/10 px-3 py-1 text-xs text-slate-300 hover:bg-white/5"
                          onClick={() => {
                            setEditingId(null);
                            setEditForm({ name: '', currency_code: 'ARS', description: '' });
                          }}
                          disabled={savingEdit}
                        >
                          Cancelar
                        </button>
                      </div>
                    ) : (
                      <div className="flex flex-wrap gap-2">
                        <button
                          className="rounded-full border border-white/10 px-3 py-1 text-xs text-white hover:bg-white/10"
                          onClick={() => startEdit(account)}
                        >
                          Editar
                        </button>
                        <button
                          className="rounded-full border border-white/10 px-3 py-1 text-xs text-slate-200 hover:bg-white/5"
                          onClick={() => handleArchiveToggle(account)}
                          disabled={actionLoading === account.id || (!account.is_archived && hasBalance(account.id))}
                        >
                          {account.is_archived ? 'Reactivar' : 'Suspender'}
                        </button>
                        <button
                          className="rounded-full border border-rose-500/40 px-3 py-1 text-xs text-rose-200 hover:bg-rose-500/10"
                          onClick={() => handleDelete(account)}
                          disabled={actionLoading === account.id || hasBalance(account.id)}
                        >
                          Eliminar
                        </button>
                      </div>
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
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
