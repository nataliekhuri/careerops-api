import * as Dialog from '@radix-ui/react-dialog'
import * as Menu from '@radix-ui/react-dropdown-menu'
import {
  Building2,
  CalendarDays,
  ChevronDown,
  ClipboardList,
  KanbanSquare,
  LayoutDashboard,
  LogOut,
  Menu as MenuIcon,
  Settings,
  X,
} from 'lucide-react'
import { useState } from 'react'
import { Link, NavLink, Outlet } from 'react-router'
import { toast } from 'sonner'

import { useAuth } from '@/auth/context'
import { Logo } from '@/components/Logo'
import { cn } from '@/lib/cn'

const NAV = [
  { to: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { to: '/applications', label: 'Applications', icon: ClipboardList },
  { to: '/board', label: 'Board', icon: KanbanSquare },
  { to: '/interviews', label: 'Interviews', icon: CalendarDays },
  { to: '/companies', label: 'Companies', icon: Building2 },
  { to: '/settings', label: 'Settings', icon: Settings },
]

function NavItems({ onNavigate }: { onNavigate?: () => void }) {
  return (
    <ul className="space-y-1">
      {NAV.map(({ to, label, icon: Icon }) => (
        <li key={to}>
          <NavLink
            to={to}
            onClick={onNavigate}
            className={({ isActive }) =>
              cn(
                'flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors',
                isActive ? 'bg-brand-50 text-brand-700' : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900',
              )
            }
          >
            <Icon className="size-4" aria-hidden />
            {label}
          </NavLink>
        </li>
      ))}
    </ul>
  )
}

function UserMenu() {
  const { user, logout } = useAuth()
  if (!user) return null
  const name = user.full_name || user.email
  const initials = name
    .split(/[\s@.]+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0]?.toUpperCase())
    .join('')

  return (
    <Menu.Root>
      <Menu.Trigger className="flex w-full items-center gap-3 rounded-lg p-2 text-left hover:bg-slate-100">
        <span
          className="flex size-8 shrink-0 items-center justify-center rounded-full bg-brand-100 text-xs font-semibold text-brand-700"
          aria-hidden
        >
          {initials}
        </span>
        <span className="min-w-0 flex-1">
          <span className="block truncate text-sm font-medium text-slate-900">{user.full_name || 'Your account'}</span>
          <span className="block truncate text-xs text-slate-500">{user.email}</span>
        </span>
        <ChevronDown className="size-4 text-slate-400" aria-hidden />
      </Menu.Trigger>
      <Menu.Portal>
        <Menu.Content
          side="top"
          align="start"
          sideOffset={8}
          className="z-50 min-w-56 rounded-lg bg-white p-1 shadow-lg ring-1 ring-slate-200"
        >
          <Menu.Item asChild>
            <Link
              to="/settings"
              className="flex cursor-pointer items-center gap-2 rounded-md px-3 py-2 text-sm text-slate-700 outline-none data-[highlighted]:bg-slate-100"
            >
              <Settings className="size-4" aria-hidden /> Settings
            </Link>
          </Menu.Item>
          <Menu.Item
            onSelect={() => {
              logout('/login')
              toast.success('You have been signed out')
            }}
            className="flex cursor-pointer items-center gap-2 rounded-md px-3 py-2 text-sm text-slate-700 outline-none data-[highlighted]:bg-slate-100"
          >
            <LogOut className="size-4" aria-hidden /> Sign out
          </Menu.Item>
        </Menu.Content>
      </Menu.Portal>
    </Menu.Root>
  )
}

export function AppLayout() {
  const [mobileOpen, setMobileOpen] = useState(false)

  return (
    <div className="min-h-screen">
      <a
        href="#main"
        className="sr-only z-50 rounded-md bg-white px-4 py-2 focus:not-sr-only focus:fixed focus:top-2 focus:left-2"
      >
        Skip to content
      </a>

      {/* Desktop sidebar */}
      <aside className="fixed inset-y-0 left-0 hidden w-64 flex-col border-r border-slate-200 bg-white lg:flex">
        <div className="flex h-16 items-center px-6">
          <Logo to="/dashboard" />
        </div>
        <nav aria-label="Main" className="flex-1 px-4 py-4">
          <NavItems />
        </nav>
        <div className="border-t border-slate-200 p-3">
          <UserMenu />
        </div>
      </aside>

      {/* Mobile top bar + drawer */}
      <header className="sticky top-0 z-30 flex h-16 items-center gap-4 border-b border-slate-200 bg-white px-4 lg:hidden">
        <Dialog.Root open={mobileOpen} onOpenChange={setMobileOpen}>
          <Dialog.Trigger className="rounded-md p-2 text-slate-600 hover:bg-slate-100" aria-label="Open menu">
            <MenuIcon className="size-5" aria-hidden />
          </Dialog.Trigger>
          <Dialog.Portal>
            <Dialog.Overlay className="fixed inset-0 z-40 bg-slate-900/40" />
            <Dialog.Content className="fixed inset-y-0 left-0 z-50 flex w-72 flex-col bg-white shadow-xl">
              <div className="flex h-16 items-center justify-between px-4">
                <Logo to="/dashboard" />
                <Dialog.Close className="rounded-md p-2 text-slate-500 hover:bg-slate-100" aria-label="Close menu">
                  <X className="size-5" aria-hidden />
                </Dialog.Close>
              </div>
              <Dialog.Title className="sr-only">Navigation</Dialog.Title>
              <Dialog.Description className="sr-only">Main navigation</Dialog.Description>
              <nav aria-label="Main" className="flex-1 px-4 py-2">
                <NavItems onNavigate={() => setMobileOpen(false)} />
              </nav>
              <div className="border-t border-slate-200 p-3">
                <UserMenu />
              </div>
            </Dialog.Content>
          </Dialog.Portal>
        </Dialog.Root>
        <Logo to="/dashboard" />
      </header>

      <main id="main" className="lg:pl-64">
        <div className="mx-auto max-w-6xl px-4 py-8 sm:px-6 lg:px-8">
          <Outlet />
        </div>
      </main>
    </div>
  )
}
