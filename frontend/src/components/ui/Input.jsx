import { forwardRef } from 'react'

const Input = forwardRef(({ label, error, className = '', ...props }, ref) => {
  return (
    <div className={className}>
      {label && (
        <label className="block text-sm font-medium text-dark-300 mb-2">
          {label}
        </label>
      )}
      <input
        ref={ref}
        className={`
          w-full px-4 py-3 bg-dark-800 border rounded-lg text-white placeholder-dark-400
          focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent
          transition-all duration-200
          ${error ? 'border-red-500 focus:ring-red-500' : 'border-dark-700'}
        `}
        {...props}
      />
      {error && (
        <p className="mt-1 text-sm text-red-400">{error}</p>
      )}
    </div>
  )
})

Input.displayName = 'Input'

export default Input