import { useEffect, useMemo, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import {
  ArrowLeft,
  Loader2,
  AlertTriangle,
  CheckCircle,
  PlayCircle,
  Square,
  ClipboardList,
} from 'lucide-react'

import Card from '../components/ui/Card'
import Input from '../components/ui/Input'
import Button from '../components/ui/Button'
import { gapBridgeService } from '../services/gapBridgeService'

const STATUS_DEFS = {
  not_started: { label: 'Non démarré', icon: Square, color: 'text-dark-300', bg: 'bg-dark-700/40' },
  in_progress: { label: 'En cours', icon: PlayCircle, color: 'text-primary-400', bg: 'bg-primary-500/10' },
  completed: { label: 'Terminé', icon: CheckCircle, color: 'text-green-400', bg: 'bg-green-500/10' },
}

function clampPercent(value) {
  const n = Number(value)
  if (Number.isNaN(n)) return 0
  return Math.max(0, Math.min(100, n))
}

export default function GapBridgePage() {
  const { cvId } = useParams()
  const navigate = useNavigate()

  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  const [plan, setPlan] = useState(null)
  const [summary, setSummary] = useState(null)

  const items = plan?.items || []

  // Si le backend renvoie une structure {plan_id: ..., ...} mais que le champ
  // d'identifiant varie, on essaie de le re-déduire ici.
  const planId = useMemo(() => {
    if (!plan) return null
    return plan.id || plan.plan_id || plan.planId || null
  }, [plan])

  const refresh = async (nextPlanId) => {
    if (!nextPlanId) return
    const [planData, summaryData] = await Promise.all([
      gapBridgeService.getPlan(nextPlanId),
      gapBridgeService.getSummary(nextPlanId),
    ])
    setPlan(planData)
    setSummary(summaryData)
  }

  useEffect(() => {
    let mounted = true
    const load = async () => {
      if (!cvId) {
        if (mounted) {
          setError('CV introuvable (cvId manquant dans l’URL)')
          setLoading(false)
        }
        return
      }

      setLoading(true)
      setError(null)

      try {
        // On génère direct à l’ouverture, comme demandé.
        const generated = await gapBridgeService.generatePlan(cvId)
        const nextPlanId = generated?.id || generated?.plan_id || generated?.planId
        if (!nextPlanId) throw new Error('Plan généré mais identifiant de plan introuvable')

        await refresh(nextPlanId)
      } catch (e) {
        if (mounted) setError(e?.message || 'Erreur lors de la génération du plan')
      } finally {
        if (mounted) setLoading(false)
      }
    }

    load()
    return () => {
      mounted = false
    }
  }, [cvId])

  const [progressDrafts, setProgressDrafts] = useState({})

  const updateDraft = (itemId, patch) => {
    setProgressDrafts((prev) => ({
      ...prev,
      [itemId]: {
        status: prev?.[itemId]?.status ?? 'in_progress',
        progressPercent: prev?.[itemId]?.progressPercent ?? 0,
        ...patch,
      },
    }))
  }

  const handleUpdateProgress = async (item) => {
    if (!planId) return

    const draft = progressDrafts?.[item.id] || {}
    const status = draft.status || item.status || 'in_progress'
    const progressPercent =
      draft.progressPercent !== undefined ? clampPercent(draft.progressPercent) : item.progress_percent

    try {
      setLoading(true)
      await gapBridgeService.updateProgress({
        itemId: item.id,
        status,
        progressPercent,
      })

      // Recharger
      await refresh(planId)
      setProgressDrafts((prev) => ({
        ...prev,
        [item.id]: undefined,
      }))
    } catch (e) {
      setError(e?.message || 'Erreur lors de la mise à jour de la progression')
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[calc(100vh-4rem)]">
        <Loader2 className="w-8 h-8 text-primary-500 animate-spin" />
      </div>
    )
  }

  if (error) {
    return (
      <div className="max-w-3xl mx-auto px-4 py-12 text-center">
        <AlertTriangle className="w-12 h-12 text-amber-500 mx-auto mb-4" />
        <h2 className="text-xl font-bold text-white mb-2">Impossible d’afficher le plan</h2>
        <p className="text-dark-400 mb-6">{error}</p>
        <Button variant="secondary" onClick={() => navigate('/dashboard')}>
          Retour au tableau de bord
        </Button>
      </div>
    )
  }

  return (
    <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8 animate-fade-in">
      <button
        onClick={() => navigate('/dashboard')}
        className="flex items-center gap-2 text-dark-400 hover:text-white mb-6 transition-colors"
      >
        <ArrowLeft className="w-4 h-4" />
        Retour au dashboard
      </button>

      <div className="mb-8">
        <h1 className="text-3xl font-bold text-white mb-2">Mon plan d’action</h1>
        <p className="text-dark-400">
          CV : <span className="text-primary-400 font-medium">{cvId}</span>
        </p>
      </div>

      {/* Summary */}
      <div className="grid md:grid-cols-2 gap-6 mb-8">
        <Card>
          <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
            <ClipboardList className="w-5 h-5 text-primary-500" />
            Résumé
          </h3>

          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-dark-400">Progression globale</span>
              <span className="text-white font-bold">{summary?.overall_progress_percent ?? 0}%</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-dark-400">Tâches terminées</span>
              <span className="text-white font-bold">
                {summary?.completed_items ?? 0} / {summary?.total_items ?? items.length}
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-dark-400">Durée estimée</span>
              <span className="text-white font-bold">{summary?.total_duration_hours ?? 0}h</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-dark-400">Fin estimée</span>
              <span className="text-white font-bold">{summary?.estimated_completion ?? '-'}</span>
            </div>
          </div>
        </Card>

        <Card>
          <h3 className="text-lg font-semibold mb-4">Étapes</h3>
          <div className="space-y-3">
            {items.length === 0 ? (
              <p className="text-dark-400">Aucune étape pour ce plan.</p>
            ) : (
              <div>
                <div className="text-sm text-dark-400 mb-2">Aperçu</div>
                <div className="space-y-2">
                  {items.slice(0, 5).map((it) => {
                    const def = STATUS_DEFS[it.status] || STATUS_DEFS.not_started
                    return (
                      <div key={it.id} className="flex items-center justify-between gap-4">
                        <div className="flex items-center gap-3 min-w-0">
                          <div className={`px-3 py-1 rounded-full text-xs font-medium ${def.bg} ${def.color}`}> 
                            {def.label}
                          </div>
                          <div className="truncate text-sm text-dark-200">
                            {it.skill_name || it.resource_title || 'Étape'}
                          </div>
                        </div>
                        <div className="text-sm text-dark-400">{it.progress_percent ?? 0}%</div>
                      </div>
                    )
                  })}
                </div>
              </div>
            )}

            {items.length > 5 && (
              <p className="text-xs text-dark-400">+ {items.length - 5} autres étapes</p>
            )}
          </div>
        </Card>
      </div>

      {/* Items */}
      <div className="space-y-4">
        {items.map((item) => {
          const def = STATUS_DEFS[item.status] || STATUS_DEFS.not_started

          const draft = progressDrafts?.[item.id] || {}
          const effectiveStatus = draft.status ?? item.status ?? 'not_started'
          const effectiveProgress =
            draft.progressPercent !== undefined ? clampPercent(draft.progressPercent) : item.progress_percent ?? 0

          const StatusIcon = def.icon

          return (
            <Card key={item.id} hover>
              <div className="flex flex-col md:flex-row md:items-start md:justify-between gap-6">
                <div className="min-w-0">
                  <div className="flex flex-wrap items-center gap-2 mb-3">
                    <div className={`inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-medium ${def.bg} ${def.color}`}>
                      <StatusIcon className="w-3.5 h-3.5" />
                      {def.label}
                    </div>
                    <span className="text-xs text-dark-400">Durée : {item.duration_hours ?? 0}h</span>
                    <span className="text-xs text-dark-400">Catégorie : {item.category || '-'}</span>
                  </div>

                  <h3 className="text-lg font-semibold text-white mb-2 truncate">
                    {item.skill_name || item.resource_title || 'Compétence'}
                  </h3>

                  <div className="text-sm text-dark-400 mb-4">
                    Ressource :{' '}
                    {item.resource_url ? (
                      <a
                        href={item.resource_url}
                        target="_blank"
                        rel="noreferrer"
                        className="text-primary-400 hover:text-primary-300 underline"
                      >
                        {item.resource_title || 'ouvrir'}
                      </a>
                    ) : (
                      <span className="text-dark-400">—</span>
                    )}
                  </div>

                  <div className="text-sm text-dark-400 mb-2">Progression actuelle</div>
                  <div className="h-3 bg-dark-900/50 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-primary-500"
                      style={{ width: `${item.progress_percent ?? 0}%` }}
                    />
                  </div>
                </div>

                <div className="w-full md:w-[360px]">
                  <div className="text-sm text-dark-400 mb-2">Mettre à jour</div>

                  <div className="grid grid-cols-2 gap-3 mb-3">
                    <Button
                      size="sm"
                      variant={effectiveStatus === 'in_progress' ? 'outline' : 'secondary'}
                      onClick={() => updateDraft(item.id, { status: 'in_progress' })}
                      disabled={loading}
                    >
                      Démarrer
                    </Button>
                    <Button
                      size="sm"
                      variant={effectiveStatus === 'completed' ? 'outline' : 'secondary'}
                      onClick={() => updateDraft(item.id, { status: 'completed', progressPercent: 100 })}
                      disabled={loading}
                    >
                      Terminer
                    </Button>
                  </div>

                  <div className="mb-3">
                    <Input
                      label="Progression (%)"
                      type="number"
                      min="0"
                      max="100"
                      value={effectiveProgress}
                      onChange={(e) => updateDraft(item.id, { progressPercent: e.target.value })}
                      disabled={loading || effectiveStatus === 'completed'}
                    />
                  </div>

                  <Button
                    className="w-full"
                    onClick={() => handleUpdateProgress(item)}
                    disabled={loading}
                  >
                    Mettre à jour
                  </Button>
                </div>
              </div>
            </Card>
          )
        })}

        {items.length === 0 && (
          <Card>
            <p className="text-dark-400">Aucune étape trouvée.</p>
          </Card>
        )}
      </div>

      <div className="mt-10 flex items-center justify-center">
        <Button variant="secondary" onClick={() => navigate('/dashboard')}>
          Retour au tableau de bord
        </Button>
      </div>
    </div>
  )
}

