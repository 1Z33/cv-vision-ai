import { cn } from '../../utils/cn'

export default function Button({ 
  children, 
  variant = 'primary', 
  size = 'md', 
  className, 
  disabled,
  ...props 
}) {
  const variants = {
    primary: 'bg-primary-600 hover:bg-primary-500 text-white shadow-lg shadow-primary-600/20',
    secondary: 'bg-dark-700 hover:bg-dark-600 text-white border border-dark-600',
    outline: 'border-2 border-primary-500 text-primary-400 hover:bg-primary-500/10',
    ghost: 'hover:bg-dark-800 text-dark-300 hover:text-white',
    danger: 'bg-red-600 hover:bg-red-500 text-white',
  }

  const sizes = {
    sm: 'px-3 py-1.5 text-sm',
    md: 'px-6 py-3 text-base',
    lg: 'px-8 py-4 text-lg',
  }

  return (
    <button
      className={cn(
        'inline-flex items-center justify-center rounded-lg font-medium transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed',
        variants[variant],
        sizes[size],
        className
      )}
      disabled={disabled}
      {...props}
    >
      {children}
    </button>
  )
}