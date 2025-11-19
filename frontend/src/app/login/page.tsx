'use client';

import Link from 'next/link';
import { FormEvent, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/contexts/AuthContext';

export default function LoginPage() {
  const { login, loading, user } = useAuth();
  const router = useRouter();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  if (!loading && user) {
    router.replace('/dashboard');
  }

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      await login(email, password);
      router.replace('/dashboard');
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <main className="flex min-h-screen items-center justify-center bg-primary px-4">
      <div className="w-full max-w-md rounded-3xl border border-white/10 bg-secondary/80 p-8 shadow-2xl">
        <h1 className="text-2xl font-bold text-white">FinTrack</h1>
        <p className="mb-6 text-sm text-slate-300">Iniciá sesión para continuar</p>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="text-sm text-slate-200" htmlFor="email">Email</label>
            <input
              id="email"
              type="email"
              className="mt-1 w-full rounded-xl border border-white/10 bg-primary/40 px-4 py-2 text-white focus:outline-none"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
          </div>
          <div>
            <label className="text-sm text-slate-200" htmlFor="password">Contraseña</label>
            <input
              id="password"
              type="password"
              className="mt-1 w-full rounded-xl border border-white/10 bg-primary/40 px-4 py-2 text-white focus:outline-none"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
          </div>
          {error && <p className="text-sm text-rose-400">{error}</p>}
          <button
            type="submit"
            disabled={submitting}
            className="w-full rounded-xl bg-gradient-to-r from-cyan-500 to-blue-500 py-2 font-semibold text-white shadow-lg disabled:opacity-50"
          >
            {submitting ? 'Ingresando...' : 'Ingresar'}
          </button>
        </form>
        <p className="mt-4 text-center text-sm text-slate-400">
          ¿No tenés cuenta?{' '}
          <Link className="text-sky-400" href="/register">
            Registrate
          </Link>
        </p>
      </div>
    </main>
  );
}
