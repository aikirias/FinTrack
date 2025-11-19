'use client';

import { useAuth } from '@/contexts/AuthContext';
import { useRouter } from 'next/navigation';
import { useEffect } from 'react';
import { Sidebar } from '@/components/Sidebar';

export default function ProtectedLayout({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth();
  const router = useRouter();

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
    <div className="flex min-h-screen bg-primary">
      <Sidebar />
      <main className="min-h-screen flex-1 bg-primary/95 p-8">
        {children}
      </main>
    </div>
  );
}
