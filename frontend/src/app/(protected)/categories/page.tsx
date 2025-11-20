'use client';

import { Fragment, useEffect, useMemo, useState } from 'react';
import { api } from '@/lib/api';
import type { Category } from '@/types';

type CategoryType = 'income' | 'expense';
interface EditableCategory {
  id: number;
  name: string;
  type: CategoryType;
  parent_id: number | null;
}

const typeLabels: Record<CategoryType, string> = {
  income: 'Ingresos',
  expense: 'Gastos',
};

export default function CategoriesPage() {
  const [categories, setCategories] = useState<Category[]>([]);
  const [activeType, setActiveType] = useState<CategoryType>('expense');
  const [name, setName] = useState('');
  const [parentId, setParentId] = useState<number | null>(null);
  const [subParent, setSubParent] = useState<number | null>(null);
  const [subName, setSubName] = useState('');
  const [subDrafts, setSubDrafts] = useState<Record<number, string>>({});
  const [editing, setEditing] = useState<EditableCategory | null>(null);
  const [message, setMessage] = useState<{ text: string; type: 'success' | 'error' } | null>(null);
  const [loading, setLoading] = useState(true);

  const load = async () => {
    setLoading(true);
    try {
      const data = (await api.getCategories()) as Category[];
      setCategories(data);
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

  const flatParents = useMemo(
    () =>
      categories
        .filter((cat) => !cat.parent_id && (cat.type === 'income' || cat.type === 'expense'))
        .map((cat) => ({ id: cat.id, name: cat.name, type: cat.type as CategoryType })),
    [categories]
  );

  const filteredCategories = useMemo(() => {
    return categories.filter((cat) => !cat.parent_id && cat.type === activeType);
  }, [categories, activeType]);

  const activeCategories = filteredCategories.filter((cat) => !cat.is_archived);
  const archivedCategories = filteredCategories.filter((cat) => cat.is_archived);

  const handleCreate = async () => {
    if (!name.trim()) return;
    try {
      await api.createCategory({ name, type: activeType, parent_id: parentId });
      setName('');
      setParentId(null);
      setMessage({ type: 'success', text: 'Categoría creada.' });
      load();
    } catch (error) {
      setMessage({ type: 'error', text: (error as Error).message });
    }
  };

  const handleCreateSub = async (parent_id: number, value: string) => {
    if (!value.trim()) return;
    try {
      const parent = categories.find((cat) => cat.id === parent_id);
      await api.createCategory({ name: value, type: parent?.type ?? activeType, parent_id });
      setSubDrafts((prev) => ({ ...prev, [parent_id]: '' }));
      setMessage({ type: 'success', text: 'Subcategoría creada.' });
      load();
    } catch (error) {
      setMessage({ type: 'error', text: (error as Error).message });
    }
  };

  const startEdit = (category: Category) => {
    setEditing({ id: category.id, name: category.name, type: category.type as CategoryType, parent_id: category.parent_id });
  };

  const handleUpdate = async () => {
    if (!editing || !editing.name.trim()) return;
    try {
      await api.updateCategory(editing.id, { name: editing.name });
      setMessage({ type: 'success', text: 'Categoría actualizada.' });
      setEditing(null);
      load();
    } catch (error) {
      setMessage({ type: 'error', text: (error as Error).message });
    }
  };

  const handleArchiveToggle = async (category: Category) => {
    try {
      await api.updateCategory(category.id, { is_archived: !category.is_archived });
      setMessage({ type: 'success', text: category.is_archived ? 'Categoría reactivada.' : 'Categoría archivada.' });
      load();
    } catch (error) {
      setMessage({ type: 'error', text: (error as Error).message });
    }
  };

  if (loading) {
    return <div className="text-slate-300">Cargando categorías...</div>;
  }

  const renderCategoryCard = (category: Category) => {
    const isEditing = editing?.id === category.id;
    return (
      <div key={category.id} className="rounded-2xl border border-white/5 bg-white/5 p-4">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div className="flex-1">
            {isEditing ? (
              <input
                value={editing?.name ?? ''}
                onChange={(e) => setEditing((prev) => (prev ? { ...prev, name: e.target.value } : prev))}
                className="w-full rounded-xl border border-white/10 bg-black/20 px-3 py-2"
              />
            ) : (
              <p className="text-lg font-semibold text-white">{category.name}</p>
            )}
            <p className="text-xs text-slate-400">{category.is_default ? 'Sistema' : 'Personalizada'}</p>
          </div>
          <div className="flex flex-wrap gap-2 text-xs">
            {isEditing ? (
              <>
                <button
                  className="rounded-full border border-white/10 px-3 py-1 text-white hover:bg-white/10"
                  onClick={handleUpdate}
                >
                  Guardar
                </button>
                <button
                  className="rounded-full border border-white/10 px-3 py-1 text-slate-300 hover:bg-white/5"
                  onClick={() => setEditing(null)}
                >
                  Cancelar
                </button>
              </>
            ) : (
              <>
                <button
                  className="rounded-full border border-white/10 px-3 py-1 text-white hover:bg-white/10"
                  onClick={() => startEdit(category)}
                >
                  Editar
                </button>
                <button
                  className="rounded-full border border-white/10 px-3 py-1 text-slate-200 hover:bg-white/5"
                  onClick={() => handleArchiveToggle(category)}
                >
                  {category.is_archived ? 'Reactivar' : 'Archivar'}
                </button>
              </>
            )}
          </div>
        </div>
        <div className="mt-4 space-y-2">
          {(category.children ?? []).filter((child) => !child.is_archived).map((child) => (
            <div key={child.id} className="flex items-center justify-between rounded-xl border border-white/5 bg-black/20 px-3 py-2 text-sm">
              <span>{child.name}</span>
              <div className="flex gap-2 text-xs">
                <button
                  className="rounded-full border border-white/10 px-2 py-1 text-white hover:bg-white/10"
                  onClick={() => startEdit(child)}
                >
                  Editar
                </button>
                <button
                  className="rounded-full border border-white/10 px-2 py-1 text-slate-200 hover:bg-white/5"
                  onClick={() => handleArchiveToggle(child)}
                >
                  {child.is_archived ? 'Reactivar' : 'Archivar'}
                </button>
              </div>
            </div>
          ))}
          <div className="flex items-center gap-2">
            <input
              value={subDrafts[category.id] ?? ''}
              onChange={(e) => setSubDrafts((prev) => ({ ...prev, [category.id]: e.target.value }))}
              placeholder="Agregar subcategoría"
              className="flex-1 rounded-xl border border-white/10 bg-black/20 px-3 py-2 text-sm"
            />
            <button
              className="rounded-full border border-white/10 px-3 py-2 text-xs text-white hover:bg-white/10"
              onClick={() => handleCreateSub(category.id, subDrafts[category.id] ?? '')}
            >
              Guardar
            </button>
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center gap-3">
        {(['expense', 'income'] as CategoryType[]).map((type) => (
          <button
            key={type}
            onClick={() => setActiveType(type)}
            className={`rounded-full px-4 py-1 text-sm font-semibold ${
              activeType === type ? 'bg-white text-primary' : 'border border-white/10 text-slate-300'
            }`}
          >
            {typeLabels[type]}
          </button>
        ))}
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
      <div className="grid gap-6 lg:grid-cols-[2fr,1fr]">
        <div className="space-y-4">
          {activeCategories.length ? (
            activeCategories.map((cat) => renderCategoryCard(cat))
          ) : (
            <p className="text-sm text-slate-400">No hay categorías activas para este tipo.</p>
          )}
          {archivedCategories.length > 0 && (
            <details className="rounded-2xl border border-white/5 bg-white/5 p-4">
              <summary className="cursor-pointer font-semibold text-white">Archivadas ({archivedCategories.length})</summary>
              <div className="mt-4 space-y-3">
                {archivedCategories.map((cat) => renderCategoryCard(cat))}
              </div>
            </details>
          )}
        </div>
        <div className="space-y-6">
          <section className="rounded-2xl border border-white/5 bg-white/5 p-4">
            <h2 className="mb-3 text-lg font-semibold">Nueva categoría ({typeLabels[activeType]})</h2>
            <input
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Nombre"
              className="mb-3 w-full rounded-xl border border-white/10 bg-black/20 px-4 py-2"
            />
            <select
              value={parentId ?? ''}
              onChange={(e) => setParentId(e.target.value ? Number(e.target.value) : null)}
              className="mb-3 w-full rounded-xl border border-white/10 bg-black/20 px-4 py-2"
            >
              <option value="">Sin padre</option>
              {activeCategories.map((parent) => (
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
          </section>
          <section className="rounded-2xl border border-white/5 bg-white/5 p-4">
            <h2 className="mb-3 text-lg font-semibold">Agregar subcategoría rápida</h2>
            <select
              value={subParent ?? ''}
              onChange={(e) => setSubParent(e.target.value ? Number(e.target.value) : null)}
              className="mb-3 w-full rounded-xl border border-white/10 bg-black/20 px-4 py-2"
            >
              <option value="">Seleccioná categoría padre</option>
              {activeCategories.map((parent) => (
                <option key={parent.id} value={parent.id}>
                  {parent.name}
                </option>
              ))}
            </select>
            <input
              value={subName}
              onChange={(e) => setSubName(e.target.value)}
              placeholder="Nombre de la subcategoría"
              className="mb-3 w-full rounded-xl border border-white/10 bg-black/20 px-4 py-2"
            />
            <button
              onClick={() => {
                if (subParent) handleCreateSub(subParent, subName);
                setSubName('');
                setSubParent(null);
              }}
              className="w-full rounded-xl bg-gradient-to-r from-emerald-400 to-teal-500 py-2 font-semibold"
            >
              Guardar subcategoría
            </button>
          </section>
        </div>
      </div>
    </div>
  );
}
