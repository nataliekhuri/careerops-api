import { cn } from '@/lib/cn'

export type Variant = 'primary' | 'secondary' | 'ghost' | 'danger'
export type Size = 'sm' | 'md' | 'lg'

export const variants: Record<Variant, string> = {
  primary: 'bg-brand-600 text-white shadow-sm hover:bg-brand-700 disabled:bg-brand-600/60',
  secondary: 'bg-white text-slate-700 ring-1 ring-inset ring-slate-300 shadow-sm hover:bg-slate-50',
  ghost: 'text-slate-600 hover:bg-slate-100 hover:text-slate-900',
  danger: 'bg-red-600 text-white shadow-sm hover:bg-red-700 disabled:bg-red-600/60',
}

export const sizes: Record<Size, string> = {
  sm: 'h-8 px-3 text-sm',
  md: 'h-10 px-4 text-sm',
  lg: 'h-12 px-6 text-base',
}

/** Tailwind classes to make a router <Link> look like a button. */
export function buttonClasses(variant: Variant = 'primary', size: Size = 'md', className?: string) {
  return cn(
    'inline-flex items-center justify-center gap-2 rounded-lg font-medium transition-colors',
    variants[variant],
    sizes[size],
    className,
  )
}
