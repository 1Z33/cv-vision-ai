export default function Card({ children, className = '', hover = false }) {
  return (
    <div 
      className={`
        bg-dark-800/50 backdrop-blur-lg border border-dark-700/50 rounded-xl p-6
        ${hover ? 'hover:border-primary-500/30 hover:bg-dark-800/70 transition-all duration-300' : ''}
        ${className}
      `}
    >
      {children}
    </div>
  )
}