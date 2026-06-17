/**
 * Panneau complet d'entretien vocal avec statistiques
 */

import React, { useState } from 'react';
import { VocalInterview } from './VocalInterview';
import { BarChart3, TrendingUp } from 'lucide-react';

interface VocalInterviewPanelProps {
  sessionId: string;
  jobTitle?: string;
}

export const VocalInterviewPanel: React.FC<VocalInterviewPanelProps> = ({ sessionId, jobTitle = 'Poste' }) => {
  const [showStats, setShowStats] = useState(false);

  return (
    <div className="vocal-interview-panel max-w-4xl mx-auto">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-800">🎙️ Simulation d'entretien vocal</h1>
        <p className="text-gray-600 mt-1">
          Poste : <span className="font-medium text-blue-600">{jobTitle}</span>
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <VocalInterview sessionId={sessionId} />
        </div>

        <div className="space-y-4">
          <div className="bg-yellow-50 border border-yellow-200 rounded-xl p-4">
            <h3 className="font-semibold text-yellow-800 mb-2 flex items-center gap-2">
              <TrendingUp size={18} />
              Conseils
            </h3>
            <ul className="text-sm text-yellow-700 space-y-2">
              <li>• Parlez clairement et à un rythme modéré</li>
              <li>• Répondez en 1-2 minutes maximum</li>
              <li>• Utilisez la méthode STAR (Situation, Tâche, Action, Résultat)</li>
              <li>• Maintenez une intonation confiante</li>
            </ul>
          </div>

          <div className="bg-gray-50 rounded-xl p-4">
            <h3 className="font-semibold text-gray-700 mb-2 flex items-center gap-2">
              <BarChart3 size={18} />
              Évaluation
            </h3>
            <div className="space-y-3">
              <div className="flex justify-between text-sm">
                <span className="text-gray-600">Contenu</span>
                <span className="font-medium">Pertinence des réponses</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-gray-600">Clarté</span>
                <span className="font-medium">Structure et fluidité</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-gray-600">Confiance</span>
                <span className="font-medium">Ton et assurance</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default VocalInterviewPanel;

