import React, { useState } from 'react';
import api from '../../services/api';

const ScoreBar = ({ label, score }) => (
  <div className="mb-3">
    <div className="flex justify-between text-sm mb-1">
      <span className="text-gray-600">{label}</span>
      <span className={`font-semibold ${score >= 60 ? 'text-green-600' : 'text-red-600'}`}>
        {score}
      </span>
    </div>
    <div className="w-full bg-gray-200 rounded-full h-2">
      <div
        className={`h-2 rounded-full ${score >= 80 ? 'bg-green-500' : score >= 60 ? 'bg-yellow-500' : 'bg-red-500'}`}
        style={{ width: `${score}%` }}
      />
    </div>
  </div>
);

const Badge = ({ children, className }) => (
  <span className={`px-2 py-1 rounded-full text-xs font-medium ${className}`}>{children}</span>
);

const Card = ({ children, className = '' }) => (
  <div className={`bg-white rounded-lg shadow-md p-4 ${className}`}>{children}</div>
);

export const CVGeminiAnalysis = ({ cvId }) => {
  const [analysis, setAnalysis] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const runAnalysis = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.post(`/cvs/${cvId}/analyze-gemini`);
      setAnalysis(res.data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Erreur lors de l\'analyse');
    }
    setLoading(false);
  };

  const getScoreColor = (score) => {
    if (score >= 80) return 'text-green-600';
    if (score >= 60) return 'text-yellow-600';
    return 'text-red-600';
  };

  if (!analysis && !loading && !error) {
    return (
      <Card className="border-dashed border-2 border-purple-200 text-center">
        <div className="py-6">
          <div className="text-4xl mb-3">✨</div>
          <h3 className="text-lg font-semibold mb-2">Analyse IA avancée</h3>
          <p className="text-gray-600 mb-4 text-sm">Obtenez une analyse détaillée de votre CV par l\'IA Gemini</p>
          <button
            onClick={runAnalysis}
            disabled={loading}
            className="bg-purple-600 text-white px-4 py-2 rounded-lg hover:bg-purple-700 disabled:opacity-50 flex items-center mx-auto"
          >
            {loading ? '⏳' : '✨'} Analyser avec Gemini
          </button>
        </div>
      </Card>
    );
  }

  if (loading) {
    return (
      <Card className="text-center py-12">
        <div className="text-3xl animate-spin mb-3">⏳</div>
        <p className="text-gray-600">Analyse en cours avec Gemini...</p>
      </Card>
    );
  }

  if (error) {
    return (
      <Card className="border-red-200">
        <div className="text-red-600 mb-2 font-semibold">❌ Erreur</div>
        <p className="text-gray-600 mb-4">{error}</p>
        <button
          onClick={runAnalysis}
          className="border border-gray-300 px-4 py-2 rounded-lg hover:bg-gray-50"
        >
          Réessayer
        </button>
      </Card>
    );
  }

  // IMPORTANT: backend retourne AnalysisResponse (noms *_score, detected_skills, etc.)
  // et non le format imbriqué prévu dans le pseudo-code TypeScript.
  return (
    <div className="space-y-4">
      {/* Score global */}
      <Card>
        <div className="flex items-center gap-2 mb-4">
          <span className="text-xl">✨</span>
          <h3 className="font-semibold">Analyse IA</h3>
          <Badge className="bg-purple-100 text-purple-700">Gemini</Badge>
        </div>

        <div className="flex items-center justify-between mb-4">
          <div>
            <div className={`text-4xl font-bold ${getScoreColor(analysis.overall_score)}`}>{analysis.overall_score}/100</div>
            <div className="text-sm text-gray-500">Score global</div>
          </div>
          <div className="text-right">
            <div className="text-lg font-semibold capitalize">{analysis.estimated_seniority || '—'}</div>
            <div className="text-sm text-gray-500">{analysis.experience_years ?? '—'} ans d\'expérience</div>
          </div>
        </div>

        <ScoreBar label="Structure" score={analysis.structure_score} />
        <ScoreBar label="Contenu" score={analysis.content_score} />
        <ScoreBar label="Mots-clés" score={analysis.keywords_score} />
      </Card>

      {/* Compétences */}
      <Card>
        <h4 className="font-semibold text-sm mb-3">🛠️ Compétences détectées</h4>
        <div className="flex flex-wrap gap-2 mb-3">
          {(analysis.detected_skills || []).map((skill) => (
            <Badge key={skill} className="bg-green-100 text-green-700">
              ✅ {skill}
            </Badge>
          ))}
        </div>
        {(analysis.missing_skills || []).length > 0 && (
          <div>
            <div className="text-sm text-gray-500 mb-2">Manquantes :</div>
            <div className="flex flex-wrap gap-2">
              {analysis.missing_skills.map((skill) => (
                <Badge key={skill} className="bg-orange-100 text-orange-700">
                  ⚠️ {skill}
                </Badge>
              ))}
            </div>
          </div>
        )}
      </Card>

      {/* Forces & Faiblesses */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Card className="border-l-4 border-l-green-400">
          <h4 className="font-semibold text-green-700 text-sm mb-3">💪 Forces</h4>
          <ul className="space-y-2">
            {(analysis.strengths || []).map((s, i) => (
              <li key={i} className="text-sm flex items-start gap-2">
                <span className="text-green-500 mt-0.5">✓</span>
                <span>{s}</span>
              </li>
            ))}
          </ul>
        </Card>

        <Card className="border-l-4 border-l-orange-400">
          <h4 className="font-semibold text-orange-700 text-sm mb-3">⚠️ Points à améliorer</h4>
          <ul className="space-y-2">
            {(analysis.weaknesses || []).map((w, i) => (
              <li key={i} className="text-sm flex items-start gap-2">
                <span className="text-orange-500 mt-0.5">!</span>
                <span>{w}</span>
              </li>
            ))}
          </ul>
        </Card>
      </div>

      {/* Recommandations */}
      <Card>
        <h4 className="font-semibold text-sm mb-3">💡 Recommandations</h4>
        <ul className="space-y-2">
          {(analysis.recommendations || []).map((r, i) => (
            <li key={i} className="text-sm bg-blue-50 p-3 rounded-lg flex items-start gap-2">
              <span className="text-blue-500 font-bold">{i + 1}.</span>
              <span>{r}</span>
            </li>
          ))}
        </ul>
      </Card>

      {/* Matching Job */}
      {analysis.job_match && (
        <Card className="border-l-4 border-l-purple-400">
          <h4 className="font-semibold text-purple-700 text-sm mb-3">🎯 Matching offre</h4>
          <div className={`text-3xl font-bold ${getScoreColor(analysis.job_match.match_score)} mb-2`}>
            {analysis.job_match.match_score}%
          </div>
          <p className="text-sm text-gray-600 mb-3">{analysis.job_match.gap_analysis}</p>
          {analysis.job_match.learning_path?.length > 0 && (
            <div>
              <div className="text-sm font-semibold mb-2">Plan d\'action :</div>
              <ul className="space-y-1">
                {analysis.job_match.learning_path.map((step, i) => (
                  <li key={i} className="text-sm flex items-center gap-2">
                    <span className="text-purple-500">→</span>
                    {step}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </Card>
      )}

      <button
        onClick={runAnalysis}
        className="w-full border border-gray-300 px-4 py-2 rounded-lg hover:bg-gray-50"
      >
        ✨ Réanalyser
      </button>
    </div>
  );
};

