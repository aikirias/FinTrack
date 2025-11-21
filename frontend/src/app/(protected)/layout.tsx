'use client';

import clsx from 'clsx';
import { useAuth } from '@/contexts/AuthContext';
import { useRouter } from 'next/navigation';
import { useEffect, useState } from 'react';
import { Sidebar } from '@/components/Sidebar';

export default function ProtectedLayout({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth();
  const router = useRouter();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  useEffect(() => {
    if (!loading && !user) {
      router.replace('/login');
    }
  }, [loading, user, router]);

  if (loading || !user) {
    return (
      <div className="flex min-h-screen items-center justify-center text-slate-300">
        Cargando...
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-primary flex flex-col md:flex-row">
      {/* Desktop sidebar */}
      <div className="hidden md:block">
        <Sidebar />
      </div>

      {/* Mobile header */}
      <div className="md:hidden">
        <header className="flex items-center justify-between border-b border-white/5 bg-secondary/80 px-4 py-3">
          <div>
            <p className="text-xs uppercase tracking-widest text-slate-400">FinTrack</p>
            <p className="text-sm font-semibold text-white">Control multimoneda</p>
          </div>
          <button
            type="button"
            onClick={() => setMobileMenuOpen((prev) => !prev)}
            className="rounded-lg border border-white/10 bg-white/5 px-3 py-2 text-sm text-white"
            aria-label="Abrir menú"
          >
            ☰
          </button>
        </header>
        {mobileMenuOpen && (
          <div className="fixed inset-0 z-50 flex">
            <div className="h-full w-72 bg-secondary/95 p-4 shadow-2xl">
              <Sidebar className="border-r-0 min-h-full" onNavigate={() => setMobileMenuOpen(false)} />
            </div>
            <button
              className="flex-1 bg-black/60"
              type="button"
              aria-label="Cerrar menú"
              onClick={() => setMobileMenuOpen(false)}
            />
          </div>
        )}
      </div>

      <main className="flex-1 bg-primary/95 p-4 md:p-8">{children}</main>
    </div>
  );
}
