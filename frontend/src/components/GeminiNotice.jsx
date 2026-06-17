import Card from './ui/Card'

export default function GeminiNotice({ fallbackReason, message }) {
  const reasonText = fallbackReason ? String(fallbackReason) : ''

  return (
    <Card className="p-4 mb-4 border-primary-500/30 bg-primary-500/10">
      <div className="text-sm text-primary-200 font-medium">
        {message || 'Gemini indisponible — mode analyse locale active'}
      </div>
      {reasonText ? (
        <div className="text-xs text-primary-100/90 mt-1">
          Détail : {reasonText}
        </div>
      ) : null}
    </Card>
  )
}

