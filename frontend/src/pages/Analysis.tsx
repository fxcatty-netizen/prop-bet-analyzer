import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { TrendingUp, Loader2, ArrowLeft, Star } from 'lucide-react';
import { apiService } from '../services/api';
import type { BetSlipWithAnalysis, PropAnalysisDetail } from '../types';

export default function Analysis() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [betSlip, setBetSlip] = useState<BetSlipWithAnalysis | null>(null);
  const [loading, setLoading] = useState(true);
  const [analyzing, setAnalyzing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadBetSlip();
  }, [id]);

  const loadBetSlip = async () => {
    try {
      const slip = await apiService.getBetSlip(parseInt(id!));
      setBetSlip(slip);
      
      // If not analyzed yet, analyze automatically
      if (slip.status === 'pending') {
        await analyzeBetSlip();
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load bet slip');
    } finally {
      setLoading(false);
    }
  };

  const analyzeBetSlip = async () => {
    setAnalyzing(true);
    setError(null);

    try {
      const analysis = await apiService.analyzeBetSlip(parseInt(id!));
      
      // Reload to get full bet slip with analysis
      const updatedSlip = await apiService.getBetSlip(parseInt(id!));
      setBetSlip(updatedSlip);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Analysis failed');
    } finally {
      setAnalyzing(false);
    }
  };

  const getConfidenceBadge = (confidence: number) => {
    if (confidence >= 70) return 'badge-success';
    if (confidence >= 58) return 'badge-info';
    if (confidence >= 45) return 'badge-warning';
    return 'badge-danger';
  };

  const getRecommendationText = (recommendation: string) => {
    const map: Record<string, string> = {
      strong_bet: 'Strong Bet',
      bet: 'Bet',
      neutral: 'Neutral',
      avoid: 'Avoid',
      strong_avoid: 'Strong Avoid',
    };
    return map[recommendation] || recommendation;
  };

  const getStars = (confidence: number) => {
    if (confidence >= 70) return 3;
    if (confidence >= 58) return 2;
    if (confidence >= 45) return 1;
    return 0;
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 py-8">
        <div className="max-w-4xl mx-auto px-4">
          <div className="card">
            <div className="text-center">
              <p className="text-red-600 mb-4">{error}</p>
              <button onClick={() => navigate('/dashboard')} className="btn-primary">
                Back to Dashboard
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (!betSlip) {
    return null;
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-6xl mx-auto px-4">
        {/* Header */}
        <div className="mb-6">
          <button
            onClick={() => navigate('/dashboard')}
            className="flex items-center text-gray-600 hover:text-gray-900 mb-4"
          >
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back to Dashboard
          </button>
          <h1 className="text-3xl font-bold text-gray-900">
            {betSlip.name || `Bet Slip #${betSlip.id}`}
          </h1>
          <p className="text-gray-600">{betSlip.prop_bets?.length || 0} props</p>
        </div>

        {/* Analyzing State */}
        {analyzing && (
          <div className="card mb-6">
            <div className="flex items-center justify-center py-8">
              <Loader2 className="w-8 h-8 animate-spin text-blue-600 mr-3" />
              <span className="text-lg">Analyzing your bet slip...</span>
            </div>
          </div>
        )}

        {/* Analysis Results */}
        {betSlip.analysis && !analyzing && (
          <>
            {/* Overall Summary */}
            <div className="card mb-6">
              <h2 className="text-2xl font-bold mb-4">Overall Analysis</h2>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div>
                  <p className="text-sm text-gray-600 mb-1">Overall Confidence</p>
                  <p className="text-4xl font-bold text-blue-600">
                    {betSlip.analysis.overall_confidence?.toFixed(0)}%
                  </p>
                </div>
                <div>
                  <p className="text-sm text-gray-600 mb-1">Risk Assessment</p>
                  <span
                    className={`badge text-lg ${
                      betSlip.analysis.risk_assessment === 'low'
                        ? 'badge-success'
                        : betSlip.analysis.risk_assessment === 'medium'
                        ? 'badge-warning'
                        : 'badge-danger'
                    }`}
                  >
                    {betSlip.analysis.risk_assessment?.toUpperCase()}
                  </span>
                </div>
                <div>
                  <p className="text-sm text-gray-600 mb-1">Recommended Bets</p>
                  <p className="text-4xl font-bold text-green-600">
                    {betSlip.analysis.recommended_bets?.length || 0}
                  </p>
                </div>
              </div>
            </div>

            {/* Individual Props Analysis */}
            <div className="space-y-4">
              {betSlip.analysis.prop_analyses?.map((propAnalysis: PropAnalysisDetail) => (
                <div key={propAnalysis.prop_id} className="card">
                  <div className="flex items-start justify-between mb-4">
                    <div className="flex-1">
                      <h3 className="text-xl font-bold text-gray-900">
                        {propAnalysis.player_name}
                      </h3>
                      <p className="text-gray-600">
                        {propAnalysis.stat_type.toUpperCase()} {propAnalysis.over_under} {propAnalysis.line}
                      </p>
                    </div>
                    <div className="text-right">
                      <div className="flex items-center gap-1 mb-1">
                        {[...Array(getStars(propAnalysis.confidence_score))].map((_, i) => (
                          <Star key={i} className="w-5 h-5 fill-yellow-400 text-yellow-400" />
                        ))}
                      </div>
                      <span className={`badge ${getConfidenceBadge(propAnalysis.confidence_score)}`}>
                        {getRecommendationText(propAnalysis.recommendation)}
                      </span>
                    </div>
                  </div>

                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
                    <div>
                      <p className="text-sm text-gray-600">Confidence</p>
                      <p className="text-2xl font-bold text-blue-600">
                        {propAnalysis.confidence_score.toFixed(0)}%
                      </p>
                    </div>
                    <div>
                      <p className="text-sm text-gray-600">Hit Rate (L10)</p>
                      <p className="text-2xl font-bold text-green-600">
                        {propAnalysis.hit_rate_last_10.toFixed(0)}%
                      </p>
                    </div>
                    <div>
                      <p className="text-sm text-gray-600">Recent Average</p>
                      <p className="text-2xl font-bold text-gray-900">
                        {propAnalysis.average_stat.toFixed(1)}
                      </p>
                    </div>
                    <div>
                      <p className="text-sm text-gray-600">Projection</p>
                      <p className="text-2xl font-bold text-purple-600">
                        {propAnalysis.pace_adjusted_projection.toFixed(1)}
                      </p>
                    </div>
                  </div>

                  {/* Factors */}
                  {propAnalysis.factors && Object.keys(propAnalysis.factors).length > 0 && (
                    <div className="mb-4">
                      <p className="text-sm font-medium text-gray-700 mb-2">Factors:</p>
                      <div className="flex flex-wrap gap-2">
                        {Object.entries(propAnalysis.factors).map(([key, value]) => (
                          <span
                            key={key}
                            className={`badge ${
                              value > 0.3
                                ? 'badge-success'
                                : value > -0.3
                                ? 'badge-info'
                                : 'badge-danger'
                            }`}
                          >
                            {key.replace(/_/g, ' ')}: {value > 0 ? '+' : ''}{(value * 10).toFixed(1)}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Analysis Notes */}
                  {propAnalysis.analysis_notes && (
                    <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                      <p className="text-sm text-blue-900">{propAnalysis.analysis_notes}</p>
                    </div>
                  )}
                </div>
              ))}
            </div>

            {/* Parlay Suggestions */}
            {betSlip.analysis.parlay_suggestions && betSlip.analysis.parlay_suggestions.length > 0 && (
              <div className="card mt-6">
                <h2 className="text-xl font-bold mb-4">Suggested Parlays</h2>
                <div className="space-y-3">
                  {betSlip.analysis.parlay_suggestions.map((parlay, index) => (
                    <div key={index} className="p-4 bg-green-50 border border-green-200 rounded-lg">
                      <div className="flex items-center justify-between mb-2">
                        <h3 className="font-medium text-gray-900">{parlay.description}</h3>
                        <span className="badge badge-success">
                          {parlay.confidence.toFixed(0)}% confidence
                        </span>
                      </div>
                      <p className="text-sm text-gray-600">
                        {parlay.props.length} props combined
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </>
        )}

        {/* No Analysis Yet */}
        {!betSlip.analysis && !analyzing && (
          <div className="card">
            <div className="text-center py-8">
              <TrendingUp className="w-16 h-16 text-gray-400 mx-auto mb-4" />
              <p className="text-gray-600 mb-4">This bet slip hasn't been analyzed yet</p>
              <button onClick={analyzeBetSlip} className="btn-primary">
                Analyze Now
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
