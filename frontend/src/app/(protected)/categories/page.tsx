'use client';

import { useEffect, useState } from 'react';
import { api } from '@/lib/api';
import type { Category } from '@/types';

export default function CategoriesPage() {
  const [categories, setCategories] = useState<Category[]>([]);
  const [name, setName] = useState('');
  const [type, setType] = useState<'income' | 'expense' | 'transfer'>('expense');
  const [parentId, setParentId] = useState<number | null>(null);
  const [subParent, setSubParent] = useState<number | null>(null);
  const [subName, setSubName] = useState('');

  const load = async () => {
    const data = (await api.getCategories()) as Category[];
    setCategories(data);
  };

  useEffect(() => {
    load();
  }, []);

  const flatParents = categories.map((cat) => ({ id: cat.id, name: cat.name, type: cat.type }));

  const handleCreate = async () => {
    if (!name.trim()) return;
    await api.createCategory({ name, type, parent_id: parentId });
    setName('');
    setParentId(null);
    load();
  };

  const handleCreateSub = async () => {
    if (!subName.trim() || !subParent) return;
    const parent = categories.find((cat) => cat.id === subParent);
    await api.createCategory({ name: subName, type: parent?.type ?? 'expense', parent_id: subParent });
    setSubName('');
    setSubParent(null);
    load();
  };

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold">Categorías</h1>
      <div className="grid gap-6 lg:grid-cols-2">
        <section className="rounded-2xl border border-white/5 bg-white/5 p-4">
          <h2 className="mb-4 text-lg font-semibold">Mapa</h2>
          <div className="space-y-3">
            {categories.map((category) => (
              <details key={category.id} className="rounded-xl border border-white/5 bg-black/20 p-3">
                <summary className="cursor-pointer text-white">
                  {category.name} <span className="text-xs text-slate-400">({category.type})</span>
                </summary>
                <div className="mt-3 space-y-1 text-sm text-slate-300">
                  {category.children?.length ? (
                    category.children.map((child) => <p key={child.id}>• {child.name}</p>)
                  ) : (
                    <p className="text-slate-500">Sin subcategorías</p>
                  )}
                </div>
              </details>
            ))}
          </div>
        </section>
        <section className="space-y-6">
          <div className="rounded-2xl border border-white/5 bg-white/5 p-4">
            <h2 className="mb-4 text-lg font-semibold">Crear categoría</h2>
            <input
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Nombre"
              className="mb-3 w-full rounded-xl border border-white/10 bg-black/20 px-4 py-2"
            />
            <select
              value={type}
              onChange={(e) => setType(e.target.value as typeof type)}
              className="mb-3 w-full rounded-xl border border-white/10 bg-black/20 px-4 py-2"
            >
              <option value="income">Ingreso</option>
              <option value="expense">Gasto</option>
              <option value="transfer">Transferencia</option>
            </select>
            <select
              value={parentId ?? ''}
              onChange={(e) => setParentId(e.target.value ? Number(e.target.value) : null)}
              className="mb-3 w-full rounded-xl border border-white/10 bg-black/20 px-4 py-2"
            >
              <option value="">Sin padre</option>
              {flatParents.map((parent) => (
                <option key={parent.id} value={parent.id}>
                  {parent.name}
                </option>
              ))}
            </select>
            <button
              onClick={handleCreate}
              className="w-full rounded-xl bg-gradient-to-r from-sky-500 to-cyan-400 py-2 font-semibold"
            >
              Guardar categoría
            </button>
          </div>
          <div className="rounded-2xl border border-white/5 bg-white/5 p-4">
            <h2 className="mb-4 text-lg font-semibold">Agregar subcategoría</h2>
            <select
              value={subParent ?? ''}
              onChange={(e) => setSubParent(e.target.value ? Number(e.target.value) : null)}
              className="mb-3 w-full rounded-xl border border-white/10 bg-black/20 px-4 py-2"
            >
              <option value="">Seleccioná categoría</option>
              {flatParents.map((parent) => (
                <option key={parent.id} value={parent.id}>
                  {parent.name}
                </option>
              ))}
            </select>
            <input
              value={subName}
              onChange={(e) => setSubName(e.target.value)}
              placeholder="Nombre"
              className="mb-3 w-full rounded-xl border border-white/10 bg-black/20 px-4 py-2"
            />
            <button
              onClick={handleCreateSub}
              className="w-full rounded-xl bg-gradient-to-r from-emerald-400 to-teal-500 py-2 font-semibold"
            >
              Guardar subcategoría
            </button>
          </div>
        </section>
      </div>
    </div>
  );
}
