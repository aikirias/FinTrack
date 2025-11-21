'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import clsx from 'clsx';
import { useAuth } from '@/contexts/AuthContext';

const links = [
  { href: '/dashboard', label: 'Dashboard' },
  { href: '/new', label: 'Nueva transacción' },
  { href: '/transactions', label: 'Movimientos' },
  { href: '/budgets', label: 'Presupuestos' },
  { href: '/categories', label: 'Categorías' },
  { href: '/accounts', label: 'Cuentas' },
];

interface SidebarProps {
  className?: string;
  onNavigate?: () => void;
}

export function Sidebar({ className, onNavigate }: SidebarProps) {
  const pathname = usePathname();
  const { logout } = useAuth();

  return (
    <aside
      className={clsx(
        'flex min-h-screen w-64 flex-col border-r border-white/5 bg-secondary/80 p-6',
        className
      )}
    >
      <div className="mb-8">
        <h2 className="text-xl font-bold text-white">FinTrack</h2>
        <p className="text-sm text-slate-400">Control multimoneda</p>
      </div>
      <nav className="flex-1 space-y-1">
        {links.map((link) => (
          <Link
            key={link.href}
            href={link.href}
            className={`block rounded-xl px-3 py-2 text-sm font-medium transition ${
              pathname.startsWith(link.href)
                ? 'bg-white/10 text-white'
                : 'text-slate-300 hover:bg-white/5'
            }`}
            onClick={onNavigate}
          >
            {link.label}
          </Link>
        ))}
      </nav>
      <button
        onClick={logout}
        className="mt-6 rounded-xl border border-white/10 px-3 py-2 text-sm text-slate-300 hover:bg-white/5"
      >
        Cerrar sesión
      </button>
    </aside>
  );
}
