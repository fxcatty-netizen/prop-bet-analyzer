import { useEffect, useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  ArrowLeft, RefreshCw, Clock, AlertTriangle, TrendingUp,
  Target, Activity, Save, ChevronRight, Users, Zap, Timer, Shield,
  Flame, CheckCircle, BarChart3, Crosshair, Star, ArrowUpDown
} from 'lucide-react';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis,
  ResponsiveContainer
} from 'recharts';
import { apiService } from '../services/api';
import type {
  LiveGame,
  HalftimeAnalysisResponse
} from '../types';

export default function HalftimeAnalyzer() {
  const navigate = useNavigate();

  // State
  const [games, setGames] = useState<LiveGame[]>([]);
  const [selectedGame, setSelectedGame] = useState<LiveGame | null>(null);
  const [analysis, setAnalysis] = useState<HalftimeAnalysisResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [analyzing, setAnalyzing] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lastRefresh, setLastRefresh] = useState<Date>(new Date());
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [filterPropType, setFilterPropType] = useState<string>('all');
  const [minConfidence, setMinConfidence] = useState<number>(50);
  const [totalsTab, setTotalsTab] = useState<'projections' | 'pace' | 'shooting' | 'stars' | 'spread'>('projections');
  const [referenceLine, setReferenceLine] = useState<string>('');

  // Load games
  const loadGames = useCallback(async () => {
    console.log('[HalftimeAnalyzer] Loading games...');
    try {
      const liveGames = await apiService.getTodaysGames();
      console.log('[HalftimeAnalyzer] Loaded games:', liveGames?.length || 0, 'games');
      console.log('[HalftimeAnalyzer] Games data:', liveGames);
      setGames(liveGames || []);
      setLastRefresh(new Date());
      setError(null);
    } catch (err) {
      console.error('[HalftimeAnalyzer] Failed to load games:', err);
      setError('Failed to load live games');
    } finally {
      setLoading(false);
    }
  }, []);

  // Auto-refresh games every 30 seconds
  useEffect(() => {
    loadGames();
    if (autoRefresh) {
      const interval = setInterval(loadGames, 30000);
      return () => clearInterval(interval);
    }
  }, [loadGames, autoRefresh]);

  // Analyze selected game
  const analyzeGame = async (game: LiveGame) => {
    setSelectedGame(game);
    setAnalyzing(true);
    setAnalysis(null);
    setError(null);

    try {
      const result = await apiService.analyzeHalftimeGame(game.game_id);
      setAnalysis(result);
    } catch (err) {
      console.error('Failed to analyze game:', err);
      setError('Failed to analyze game');
    } finally {
      setAnalyzing(false);
    }
  };

  // Save snapshot
  const saveSnapshot = async () => {
    if (!selectedGame) return;
    setSaving(true);
    try {
      await apiService.saveHalftimeSnapshot(selectedGame.game_id);
      alert('Snapshot saved successfully!');
    } catch (err) {
      console.error('Failed to save snapshot:', err);
      alert('Failed to save snapshot');
    } finally {
      setSaving(false);
    }
  };

  // Filter player analyses
  const filteredAnalyses = analysis?.player_analyses.filter(a => {
    if (filterPropType !== 'all' && a.prop_type !== filterPropType) return false;
    if (a.confidence_score < minConfidence) return false;
    return true;
  }) || [];

  // Get game status badge color
  const getStatusColor = (status: number, isHalftime: boolean) => {
    if (isHalftime) return 'bg-yellow-100 text-yellow-800';
    if (status === 2) return 'bg-green-100 text-green-800';
    if (status === 3) return 'bg-gray-100 text-gray-800';
    return 'bg-blue-100 text-blue-800';
  };

  // Get recommendation color
  const getRecommendationColor = (rec: string) => {
    switch (rec) {
      case 'strong_bet': return 'bg-green-600 text-white';
      case 'bet': return 'bg-green-500 text-white';
      case 'lean': return 'bg-green-100 text-green-800';
      case 'neutral': return 'bg-gray-100 text-gray-800';
      case 'avoid': return 'bg-red-100 text-red-800';
      case 'strong_avoid': return 'bg-red-600 text-white';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  // Get confidence color
  const getConfidenceColor = (score: number) => {
    if (score >= 75) return 'text-green-600';
    if (score >= 60) return 'text-yellow-600';
    return 'text-red-600';
  };

  // Get O/U recommendation color
  const getOUColor = (rec: string) => {
    switch (rec) {
      case 'strong_over': return 'bg-green-600 text-white';
      case 'lean_over': return 'bg-green-100 text-green-800';
      case 'strong_under': return 'bg-red-600 text-white';
      case 'lean_under': return 'bg-red-100 text-red-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  // Get hot/cold color
  const getHotColdColor = (indicator: string) => {
    switch (indicator) {
      case 'hot': return 'text-red-500';
      case 'cold': return 'text-blue-500';
      default: return 'text-gray-500';
    }
  };

  // Get shooting variance badge
  const getVarianceBadge = (level: string) => {
    switch (level) {
      case 'extreme_hot': return 'bg-red-100 text-red-700';
      case 'hot': return 'bg-orange-100 text-orange-700';
      case 'normal': return 'bg-gray-100 text-gray-700';
      case 'cold': return 'bg-blue-100 text-blue-700';
      case 'extreme_cold': return 'bg-blue-200 text-blue-800';
      default: return 'bg-gray-100 text-gray-700';
    }
  };

  const enhanced = analysis?.enhanced_game_totals;

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 py-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center">
            <div className="flex items-center gap-4">
              <button
                onClick={() => navigate('/dashboard')}
                className="text-gray-600 hover:text-gray-900"
              >
                <ArrowLeft className="w-5 h-5" />
              </button>
              <div>
                <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
                  <Clock className="w-6 h-6 text-purple-600" />
                  Halftime Analyzer
                </h1>
                <p className="text-sm text-gray-600">
                  Real-time analysis of live NBA games at halftime
                </p>
              </div>
            </div>
            <div className="flex items-center gap-4">
              <label className="flex items-center gap-2 text-sm text-gray-600">
                <input
                  type="checkbox"
                  checked={autoRefresh}
                  onChange={(e) => setAutoRefresh(e.target.checked)}
                  className="rounded"
                />
                Auto-refresh
              </label>
              <button
                onClick={loadGames}
                disabled={loading}
                className="flex items-center gap-2 text-gray-600 hover:text-gray-900"
              >
                <RefreshCw className={`w-5 h-5 ${loading ? 'animate-spin' : ''}`} />
                Refresh
              </button>
              <span className="text-xs text-gray-400">
                Last: {lastRefresh.toLocaleTimeString()}
              </span>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 py-8 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Games List Panel */}
          <div className="lg:col-span-1">
            <div className="card">
              <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
                <Activity className="w-5 h-5 text-green-500" />
                Today's Games
              </h2>

              {loading && games.length === 0 ? (
                <div className="text-center py-8">
                  <RefreshCw className="w-8 h-8 animate-spin text-gray-400 mx-auto mb-2" />
                  <p className="text-gray-500">Loading games...</p>
                </div>
              ) : games.length === 0 ? (
                <div className="text-center py-8 text-gray-500">
                  <Clock className="w-12 h-12 text-gray-300 mx-auto mb-3" />
                  <p>No games scheduled today</p>
                </div>
              ) : (
                <div className="space-y-3">
                  {games.map((game) => (
                    <div
                      key={game.game_id}
                      onClick={() => analyzeGame(game)}
                      className={`p-4 border rounded-lg cursor-pointer transition-all ${
                        selectedGame?.game_id === game.game_id
                          ? 'border-purple-500 bg-purple-50'
                          : 'border-gray-200 hover:border-purple-300 hover:bg-gray-50'
                      }`}
                    >
                      <div className="flex items-center justify-between mb-2">
                        <span className={`px-2 py-0.5 rounded text-xs font-medium ${getStatusColor(game.game_status, game.is_halftime)}`}>
                          {game.is_halftime ? 'HALFTIME' : game.game_status_text}
                        </span>
                        {game.is_halftime && (
                          <span className="flex items-center gap-1 text-xs text-yellow-600">
                            <Zap className="w-3 h-3" />
                            Best time to analyze!
                          </span>
                        )}
                      </div>

                      <div className="flex items-center justify-between">
                        <div className="text-sm">
                          <div className="font-medium">{game.away_team_abbr}</div>
                          <div className="font-medium">{game.home_team_abbr}</div>
                        </div>
                        <div className="text-right">
                          <div className="text-lg font-bold">{game.away_score}</div>
                          <div className="text-lg font-bold">{game.home_score}</div>
                        </div>
                      </div>

                      {game.game_status === 2 && (
                        <div className="mt-2 text-xs text-gray-500 flex items-center gap-2">
                          <Timer className="w-3 h-3" />
                          Q{game.period} | {game.game_clock || '--:--'}
                        </div>
                      )}

                      <ChevronRight className="w-4 h-4 text-gray-400 absolute right-4 top-1/2 -translate-y-1/2 hidden group-hover:block" />
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* Analysis Panel */}
          <div className="lg:col-span-2 space-y-6">
            {!selectedGame ? (
              <div className="card text-center py-16">
                <Target className="w-16 h-16 text-gray-300 mx-auto mb-4" />
                <h3 className="text-lg font-medium text-gray-900 mb-2">
                  Select a Game to Analyze
                </h3>
                <p className="text-gray-500">
                  Choose a game from the list to see halftime analysis and prop suggestions
                </p>
              </div>
            ) : analyzing ? (
              <div className="card text-center py-16">
                <RefreshCw className="w-12 h-12 animate-spin text-purple-500 mx-auto mb-4" />
                <h3 className="text-lg font-medium text-gray-900">
                  Analyzing {selectedGame.away_team_abbr} @ {selectedGame.home_team_abbr}...
                </h3>
              </div>
            ) : error ? (
              <div className="card text-center py-16">
                <AlertTriangle className="w-16 h-16 text-red-400 mx-auto mb-4" />
                <h3 className="text-lg font-medium text-red-600">{error}</h3>
                <button
                  onClick={() => analyzeGame(selectedGame)}
                  className="mt-4 btn-primary"
                >
                  Try Again
                </button>
              </div>
            ) : analysis ? (
              <>
                {/* Game Header */}
                <div className="card">
                  <div className="flex items-center justify-between mb-4">
                    <h2 className="text-xl font-bold">
                      {analysis.game_info.away_team_abbr} @ {analysis.game_info.home_team_abbr}
                    </h2>
                    <div className="flex items-center gap-3">
                      <button
                        onClick={saveSnapshot}
                        disabled={saving}
                        className="btn-secondary flex items-center gap-2"
                      >
                        <Save className={`w-4 h-4 ${saving ? 'animate-pulse' : ''}`} />
                        Save Snapshot
                      </button>
                      <button
                        onClick={() => analyzeGame(selectedGame)}
                        className="btn-primary flex items-center gap-2"
                      >
                        <RefreshCw className="w-4 h-4" />
                        Refresh
                      </button>
                    </div>
                  </div>

                  {/* Score Display */}
                  <div className="grid grid-cols-3 gap-4 mb-4">
                    <div className="text-center">
                      <div className="text-sm text-gray-500">{analysis.game_info.away_team_name}</div>
                      <div className="text-4xl font-bold">{analysis.game_info.away_score}</div>
                    </div>
                    <div className="flex flex-col items-center justify-center">
                      <span className={`px-3 py-1 rounded-full text-sm font-medium ${getStatusColor(analysis.game_info.game_status, analysis.game_info.is_halftime)}`}>
                        {analysis.game_info.is_halftime ? 'HALFTIME' : analysis.game_info.game_status_text}
                      </span>
                      <span className="text-xs text-gray-400 mt-1">
                        Total: {analysis.game_info.total_score}
                      </span>
                    </div>
                    <div className="text-center">
                      <div className="text-sm text-gray-500">{analysis.game_info.home_team_name}</div>
                      <div className="text-4xl font-bold">{analysis.game_info.home_score}</div>
                    </div>
                  </div>

                  {/* Warnings */}
                  {analysis.warnings.length > 0 && (
                    <div className="flex flex-wrap gap-2">
                      {analysis.warnings.map((warning, i) => (
                        <span key={i} className="flex items-center gap-1 px-2 py-1 bg-yellow-100 text-yellow-800 text-xs rounded">
                          <AlertTriangle className="w-3 h-3" />
                          {warning}
                        </span>
                      ))}
                    </div>
                  )}
                </div>

                {/* Enhanced Game Totals Dashboard */}
                <div className="card">
                  <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                    <BarChart3 className="w-5 h-5 text-blue-500" />
                    Game Totals & Predictions
                    {enhanced && (
                      <span className={`ml-2 text-sm font-normal ${getConfidenceColor(enhanced.total_confidence)}`}>
                        {enhanced.total_confidence}% confidence
                      </span>
                    )}
                  </h3>

                  {/* Tab Bar */}
                  <div className="flex border-b mb-4 gap-1 overflow-x-auto">
                    {([
                      { id: 'projections', label: 'Projections', icon: TrendingUp },
                      { id: 'pace', label: 'Pace', icon: Timer },
                      { id: 'shooting', label: 'Shooting', icon: Crosshair },
                      { id: 'stars', label: 'Stars', icon: Star },
                      { id: 'spread', label: 'Spread', icon: ArrowUpDown },
                    ] as const).map(tab => (
                      <button
                        key={tab.id}
                        onClick={() => setTotalsTab(tab.id)}
                        className={`flex items-center gap-1.5 px-3 py-2 text-sm font-medium border-b-2 transition-colors whitespace-nowrap ${
                          totalsTab === tab.id
                            ? 'border-blue-500 text-blue-600'
                            : 'border-transparent text-gray-500 hover:text-gray-700'
                        }`}
                      >
                        <tab.icon className="w-4 h-4" />
                        {tab.label}
                      </button>
                    ))}
                  </div>

                  {/* TAB: Projections */}
                  {totalsTab === 'projections' && (
                    <div className="space-y-4">
                      {/* Quarter Scoreboard */}
                      {enhanced ? (
                        <>
                          <div className="overflow-x-auto">
                            <table className="w-full text-sm">
                              <thead>
                                <tr className="border-b bg-gray-50">
                                  <th className="text-left py-2 px-3">Team</th>
                                  <th className="text-center py-2 px-3">1H</th>
                                  <th className="text-center py-2 px-3 text-blue-600">Q3*</th>
                                  <th className="text-center py-2 px-3 text-purple-600">Q4*</th>
                                  <th className="text-center py-2 px-3 text-green-600 font-bold">Final*</th>
                                </tr>
                              </thead>
                              <tbody>
                                <tr className="border-b">
                                  <td className="py-2 px-3 font-medium">{enhanced.away_team}</td>
                                  <td className="py-2 px-3 text-center">{enhanced.away_score}</td>
                                  <td className="py-2 px-3 text-center text-blue-600">{enhanced.away_quarters.q3_projected}</td>
                                  <td className="py-2 px-3 text-center text-purple-600">{enhanced.away_quarters.q4_projected}</td>
                                  <td className="py-2 px-3 text-center text-green-600 font-bold">{enhanced.away_quarters.projected_final_score}</td>
                                </tr>
                                <tr className="border-b">
                                  <td className="py-2 px-3 font-medium">{enhanced.home_team}</td>
                                  <td className="py-2 px-3 text-center">{enhanced.home_score}</td>
                                  <td className="py-2 px-3 text-center text-blue-600">{enhanced.home_quarters.q3_projected}</td>
                                  <td className="py-2 px-3 text-center text-purple-600">{enhanced.home_quarters.q4_projected}</td>
                                  <td className="py-2 px-3 text-center text-green-600 font-bold">{enhanced.home_quarters.projected_final_score}</td>
                                </tr>
                                <tr className="bg-gray-50 font-bold">
                                  <td className="py-2 px-3">Total</td>
                                  <td className="py-2 px-3 text-center">{enhanced.first_half_total}</td>
                                  <td className="py-2 px-3 text-center text-blue-600">{enhanced.projected_q3_total}</td>
                                  <td className="py-2 px-3 text-center text-purple-600">{enhanced.projected_q4_total}</td>
                                  <td className="py-2 px-3 text-center text-green-600">{enhanced.projected_final_total}</td>
                                </tr>
                              </tbody>
                            </table>
                            <p className="text-xs text-gray-400 mt-1">* Projected values</p>
                          </div>

                          {/* O/U Recommendation */}
                          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <div className="bg-gradient-to-br from-blue-50 to-purple-50 rounded-lg p-4">
                              <div className="text-xs text-gray-500 mb-1">Over/Under Projection</div>
                              <div className="text-3xl font-bold">{enhanced.over_under.projected_total}</div>
                              <div className="text-sm text-gray-500">
                                Range: {enhanced.over_under.projected_range_low} - {enhanced.over_under.projected_range_high}
                              </div>
                              <div className="flex items-center gap-2 mt-2">
                                <span className={`px-2 py-1 rounded text-sm font-medium ${getOUColor(enhanced.over_under.recommendation)}`}>
                                  {enhanced.over_under.recommendation.replace('_', ' ').toUpperCase()}
                                </span>
                                <span className={`text-sm font-medium ${getConfidenceColor(enhanced.over_under.confidence)}`}>
                                  {enhanced.over_under.confidence}%
                                </span>
                              </div>
                              {enhanced.over_under.reference_line && (
                                <div className="mt-2 text-sm">
                                  <span className="text-gray-500">vs Line {enhanced.over_under.reference_line}:</span>{' '}
                                  <span className={`font-medium ${enhanced.over_under.edge >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                                    {enhanced.over_under.edge >= 0 ? '+' : ''}{enhanced.over_under.edge} ({enhanced.over_under.edge_pct}%)
                                  </span>
                                </div>
                              )}
                              <div className="mt-2 flex items-center gap-2">
                                <input
                                  type="number"
                                  placeholder="Enter Vegas line..."
                                  value={referenceLine}
                                  onChange={(e) => setReferenceLine(e.target.value)}
                                  className="text-sm border rounded px-2 py-1 w-36"
                                  step="0.5"
                                />
                                <span className="text-xs text-gray-400">for edge calc</span>
                              </div>
                            </div>

                            {/* Spread */}
                            <div className="bg-gradient-to-br from-orange-50 to-red-50 rounded-lg p-4">
                              <div className="text-xs text-gray-500 mb-1">Spread Prediction</div>
                              <div className="text-3xl font-bold">
                                {enhanced.spread_prediction.projected_final_spread > 0 ? enhanced.home_team : enhanced.away_team}{' '}
                                {enhanced.spread_prediction.projected_final_spread > 0 ? '-' : '-'}{Math.abs(enhanced.spread_prediction.projected_final_spread)}
                              </div>
                              <div className="text-sm text-gray-500">
                                Current: {enhanced.spread_prediction.home_lead ? enhanced.home_team : enhanced.away_team} {enhanced.spread_prediction.current_spread > 0 ? '+' : ''}{enhanced.spread_prediction.current_spread}
                              </div>
                              <div className="mt-2 flex items-center gap-3 text-sm">
                                <span className="text-gray-500">Close game: <span className="font-medium text-gray-700">{enhanced.spread_prediction.close_game_probability}%</span></span>
                                <span className="text-gray-500">Blowout: <span className="font-medium text-gray-700">{enhanced.spread_prediction.blowout_probability}%</span></span>
                              </div>
                              {enhanced.spread_prediction.momentum_indicator !== 'neutral' && (
                                <div className="mt-1 text-xs text-orange-600">
                                  Momentum: {enhanced.spread_prediction.momentum_indicator.toUpperCase()}
                                </div>
                              )}
                            </div>
                          </div>

                          {/* Analysis Notes */}
                          {enhanced.analysis_notes.length > 0 && (
                            <div className="bg-blue-50 rounded-lg p-3">
                              <div className="text-xs font-medium text-blue-700 mb-1">Analysis Notes</div>
                              {enhanced.analysis_notes.map((note, i) => (
                                <p key={i} className="text-sm text-blue-800 mb-1">{note}</p>
                              ))}
                            </div>
                          )}
                        </>
                      ) : (
                        /* Fallback to basic totals if enhanced not available */
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                          <div className="bg-gray-50 rounded-lg p-3">
                            <div className="text-xs text-gray-500">First Half</div>
                            <div className="text-2xl font-bold">{analysis.game_total_analysis.first_half_total}</div>
                          </div>
                          <div className="bg-blue-50 rounded-lg p-3">
                            <div className="text-xs text-gray-500">Proj. Q3</div>
                            <div className="text-2xl font-bold text-blue-600">{analysis.game_total_analysis.projected_q3_total}</div>
                          </div>
                          <div className="bg-purple-50 rounded-lg p-3">
                            <div className="text-xs text-gray-500">Proj. 2nd Half</div>
                            <div className="text-2xl font-bold text-purple-600">{analysis.game_total_analysis.projected_second_half_total}</div>
                          </div>
                          <div className="bg-green-50 rounded-lg p-3">
                            <div className="text-xs text-gray-500">Proj. Final</div>
                            <div className="text-2xl font-bold text-green-600">{analysis.game_total_analysis.projected_final_total}</div>
                          </div>
                        </div>
                      )}
                    </div>
                  )}

                  {/* TAB: Pace */}
                  {totalsTab === 'pace' && enhanced && (
                    <div className="space-y-4">
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                        <div className="bg-blue-50 rounded-lg p-3">
                          <div className="text-xs text-gray-500">Live Poss/48</div>
                          <div className="text-2xl font-bold text-blue-600">{enhanced.pace_analysis.possessions_per_48_live}</div>
                        </div>
                        <div className="bg-gray-50 rounded-lg p-3">
                          <div className="text-xs text-gray-500">Expected Pace</div>
                          <div className="text-2xl font-bold">{enhanced.pace_analysis.matchup_expected_pace}</div>
                        </div>
                        <div className="bg-purple-50 rounded-lg p-3">
                          <div className="text-xs text-gray-500">Deviation</div>
                          <div className={`text-2xl font-bold ${enhanced.pace_analysis.pace_deviation > 0 ? 'text-red-600' : enhanced.pace_analysis.pace_deviation < 0 ? 'text-blue-600' : 'text-gray-600'}`}>
                            {enhanced.pace_analysis.pace_deviation > 0 ? '+' : ''}{enhanced.pace_analysis.pace_deviation}%
                          </div>
                        </div>
                        <div className="bg-orange-50 rounded-lg p-3">
                          <div className="text-xs text-gray-500">Trend</div>
                          <div className={`text-lg font-bold ${enhanced.pace_analysis.pace_trend === 'accelerating' ? 'text-red-600' : enhanced.pace_analysis.pace_trend === 'decelerating' ? 'text-blue-600' : 'text-gray-600'}`}>
                            {enhanced.pace_analysis.pace_trend.charAt(0).toUpperCase() + enhanced.pace_analysis.pace_trend.slice(1)}
                          </div>
                        </div>
                      </div>

                      {/* Pace Bar Chart */}
                      <ResponsiveContainer width="100%" height={250}>
                        <BarChart data={[
                          { name: `${enhanced.home_team} Season`, value: enhanced.pace_analysis.home_season_pace, fill: '#3b82f6' },
                          { name: `${enhanced.away_team} Season`, value: enhanced.pace_analysis.away_season_pace, fill: '#ef4444' },
                          { name: 'Matchup Expected', value: enhanced.pace_analysis.matchup_expected_pace, fill: '#6b7280' },
                          { name: 'Live Game', value: enhanced.pace_analysis.possessions_per_48_live, fill: '#8b5cf6' },
                        ]}>
                          <CartesianGrid strokeDasharray="3 3" />
                          <XAxis dataKey="name" tick={{ fontSize: 11 }} />
                          <YAxis domain={['dataMin - 5', 'dataMax + 5']} />
                          <Tooltip />
                          <Bar dataKey="value" name="Pace (Poss/48)" />
                        </BarChart>
                      </ResponsiveContainer>

                      {/* PPP */}
                      <div className="grid grid-cols-2 gap-4">
                        <div className="bg-gray-50 rounded-lg p-3">
                          <div className="text-xs text-gray-500">{enhanced.home_team} Points Per Possession</div>
                          <div className="text-xl font-bold">{enhanced.pace_analysis.points_per_possession_home}</div>
                        </div>
                        <div className="bg-gray-50 rounded-lg p-3">
                          <div className="text-xs text-gray-500">{enhanced.away_team} Points Per Possession</div>
                          <div className="text-xl font-bold">{enhanced.pace_analysis.points_per_possession_away}</div>
                        </div>
                      </div>
                    </div>
                  )}

                  {/* TAB: Shooting */}
                  {totalsTab === 'shooting' && enhanced && (
                    <div className="space-y-4">
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        {[enhanced.home_shooting, enhanced.away_shooting].map((s) => (
                          <div key={s.team_abbr} className="border rounded-lg p-4">
                            <div className="flex items-center justify-between mb-3">
                              <span className="font-bold text-lg">{s.team_abbr}</span>
                              <span className={`px-2 py-0.5 rounded text-xs font-medium ${getVarianceBadge(s.shooting_variance_level)}`}>
                                {s.shooting_variance_level.replace('_', ' ').toUpperCase()}
                              </span>
                            </div>
                            <div className="grid grid-cols-3 gap-3 text-sm">
                              <div>
                                <div className="text-xs text-gray-500">eFG%</div>
                                <div className="font-bold">{s.live_efg_pct}%</div>
                                <div className="text-xs text-gray-400">Szn: {s.season_efg_pct}%</div>
                              </div>
                              <div>
                                <div className="text-xs text-gray-500">TS%</div>
                                <div className="font-bold">{s.live_ts_pct}%</div>
                                <div className="text-xs text-gray-400">Szn: {s.season_ts_pct}%</div>
                              </div>
                              <div>
                                <div className="text-xs text-gray-500">3P%</div>
                                <div className="font-bold">{s.live_fg3_pct}%</div>
                                <div className="text-xs text-gray-400">Szn: {s.season_fg3_pct}%</div>
                              </div>
                              <div>
                                <div className="text-xs text-gray-500">3pt Rate</div>
                                <div className="font-bold">{s.live_fg3_rate}%</div>
                              </div>
                              <div>
                                <div className="text-xs text-gray-500">FT Rate</div>
                                <div className="font-bold">{s.live_ft_rate}%</div>
                              </div>
                              <div>
                                <div className="text-xs text-gray-500">Regression</div>
                                <div className={`font-bold ${s.shooting_regression_factor < 1 ? 'text-red-600' : s.shooting_regression_factor > 1 ? 'text-green-600' : 'text-gray-600'}`}>
                                  {s.shooting_regression_factor.toFixed(3)}
                                </div>
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>

                      {/* Radar Chart: Shooting Profile Comparison */}
                      <ResponsiveContainer width="100%" height={300}>
                        <RadarChart data={[
                          { stat: 'eFG%', [enhanced.home_shooting.team_abbr]: enhanced.home_shooting.live_efg_pct, [enhanced.away_shooting.team_abbr]: enhanced.away_shooting.live_efg_pct },
                          { stat: 'TS%', [enhanced.home_shooting.team_abbr]: enhanced.home_shooting.live_ts_pct, [enhanced.away_shooting.team_abbr]: enhanced.away_shooting.live_ts_pct },
                          { stat: '3P%', [enhanced.home_shooting.team_abbr]: enhanced.home_shooting.live_fg3_pct, [enhanced.away_shooting.team_abbr]: enhanced.away_shooting.live_fg3_pct },
                          { stat: 'FT%', [enhanced.home_shooting.team_abbr]: enhanced.home_shooting.live_ft_pct, [enhanced.away_shooting.team_abbr]: enhanced.away_shooting.live_ft_pct },
                          { stat: '3pt Rate', [enhanced.home_shooting.team_abbr]: enhanced.home_shooting.live_fg3_rate, [enhanced.away_shooting.team_abbr]: enhanced.away_shooting.live_fg3_rate },
                        ]}>
                          <PolarGrid />
                          <PolarAngleAxis dataKey="stat" tick={{ fontSize: 11 }} />
                          <PolarRadiusAxis />
                          <Radar name={enhanced.home_shooting.team_abbr} dataKey={enhanced.home_shooting.team_abbr} stroke="#3b82f6" fill="#3b82f6" fillOpacity={0.2} />
                          <Radar name={enhanced.away_shooting.team_abbr} dataKey={enhanced.away_shooting.team_abbr} stroke="#ef4444" fill="#ef4444" fillOpacity={0.2} />
                          <Legend />
                          <Tooltip />
                        </RadarChart>
                      </ResponsiveContainer>
                    </div>
                  )}

                  {/* TAB: Stars */}
                  {totalsTab === 'stars' && enhanced && (
                    <div className="space-y-3">
                      {enhanced.star_players.length === 0 ? (
                        <p className="text-gray-500 text-center py-8">No star player data available</p>
                      ) : (
                        enhanced.star_players.map((star, i) => (
                          <div key={i} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                            <div className="flex-1">
                              <div className="flex items-center gap-2">
                                <span className="font-bold">{star.player_name}</span>
                                <span className="text-xs text-gray-500">{star.team_abbr}</span>
                                <span className={`text-xs font-medium ${getHotColdColor(star.hot_cold_indicator)}`}>
                                  {star.hot_cold_indicator === 'hot' ? 'HOT' : star.hot_cold_indicator === 'cold' ? 'COLD' : ''}
                                </span>
                              </div>
                              <div className="grid grid-cols-4 gap-3 mt-2 text-xs">
                                <div>
                                  <span className="text-gray-500">1H Pts:</span>{' '}
                                  <span className="font-medium">{star.first_half_points}</span>
                                </div>
                                <div>
                                  <span className="text-gray-500">Usage:</span>{' '}
                                  <span className="font-medium">{star.usage_rate}%</span>
                                </div>
                                <div>
                                  <span className="text-gray-500">TS%:</span>{' '}
                                  <span className="font-medium">{star.current_efficiency}%</span>
                                </div>
                                <div>
                                  <span className="text-gray-500">Fouls:</span>{' '}
                                  <span className={`font-medium ${star.foul_trouble ? 'text-red-600' : ''}`}>{star.foul_count}</span>
                                </div>
                              </div>
                            </div>
                            <div className="text-right ml-4">
                              <div className="text-sm text-gray-500">Proj 2H</div>
                              <div className="text-xl font-bold">{star.projected_2h_points} pts</div>
                              <div className="text-xs text-gray-500">{star.projected_2h_minutes} min</div>
                              <div className={`text-xs font-medium mt-1 ${star.impact_on_team_total >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                                {star.impact_on_team_total >= 0 ? '+' : ''}{star.impact_on_team_total} impact
                              </div>
                              {star.minutes_risk !== 'normal' && (
                                <span className="text-xs text-red-500">{star.minutes_risk.replace('_', ' ')}</span>
                              )}
                              {star.season_ppg && (
                                <div className="text-xs text-gray-400">Szn: {star.season_ppg} ppg</div>
                              )}
                            </div>
                          </div>
                        ))
                      )}
                    </div>
                  )}

                  {/* TAB: Spread */}
                  {totalsTab === 'spread' && enhanced && (
                    <div className="space-y-4">
                      <div className="grid grid-cols-2 gap-4">
                        <div className="bg-orange-50 rounded-lg p-4">
                          <div className="text-xs text-gray-500">Current Spread</div>
                          <div className="text-3xl font-bold">
                            {enhanced.spread_prediction.home_lead ? enhanced.home_team : enhanced.away_team}{' '}
                            {enhanced.spread_prediction.current_spread > 0 ? '+' : ''}{enhanced.spread_prediction.current_spread}
                          </div>
                        </div>
                        <div className="bg-green-50 rounded-lg p-4">
                          <div className="text-xs text-gray-500">Projected Final Spread</div>
                          <div className="text-3xl font-bold text-green-600">
                            {enhanced.spread_prediction.projected_final_spread > 0 ? enhanced.home_team : enhanced.away_team}{' '}
                            {Math.abs(enhanced.spread_prediction.projected_final_spread) > 0 ? '-' : ''}{Math.abs(enhanced.spread_prediction.projected_final_spread)}
                          </div>
                          <div className={`text-sm ${getConfidenceColor(enhanced.spread_prediction.spread_confidence)}`}>
                            {enhanced.spread_prediction.spread_confidence}% confidence
                          </div>
                        </div>
                      </div>

                      <div className="grid grid-cols-3 gap-4 text-sm">
                        <div className="bg-gray-50 rounded-lg p-3 text-center">
                          <div className="text-xs text-gray-500 mb-1">Close Game Prob</div>
                          <div className="text-xl font-bold">{enhanced.spread_prediction.close_game_probability}%</div>
                          <div className="text-xs text-gray-400">Final margin &le; 5</div>
                        </div>
                        <div className="bg-gray-50 rounded-lg p-3 text-center">
                          <div className="text-xs text-gray-500 mb-1">Blowout Prob</div>
                          <div className="text-xl font-bold">{enhanced.spread_prediction.blowout_probability}%</div>
                          <div className="text-xs text-gray-400">Final margin &ge; 15</div>
                        </div>
                        <div className="bg-gray-50 rounded-lg p-3 text-center">
                          <div className="text-xs text-gray-500 mb-1">Star Differential</div>
                          <div className={`text-xl font-bold ${enhanced.spread_prediction.star_performance_differential >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                            {enhanced.spread_prediction.star_performance_differential >= 0 ? '+' : ''}{enhanced.spread_prediction.star_performance_differential}
                          </div>
                          <div className="text-xs text-gray-400">{enhanced.home_team} star edge</div>
                        </div>
                      </div>

                      {enhanced.spread_prediction.momentum_indicator !== 'neutral' && (
                        <div className="bg-yellow-50 rounded-lg p-3 flex items-center gap-2">
                          <Zap className="w-4 h-4 text-yellow-600" />
                          <span className="text-sm text-yellow-800">
                            Momentum favors <strong>{enhanced.spread_prediction.momentum_indicator.toUpperCase()}</strong> team
                          </span>
                        </div>
                      )}

                      {/* OT probability */}
                      {enhanced.home_quarters.ot_probability > 5 && (
                        <div className="bg-purple-50 rounded-lg p-3 text-sm text-purple-800">
                          Overtime probability: <strong>{enhanced.home_quarters.ot_probability}%</strong>
                        </div>
                      )}
                    </div>
                  )}

                  {/* No enhanced data fallback for non-projections tabs */}
                  {totalsTab !== 'projections' && !enhanced && (
                    <div className="text-center py-8 text-gray-500">
                      Enhanced analysis not available for this game.
                    </div>
                  )}
                </div>

                {/* Top Suggestions */}
                {analysis.suggestions.length > 0 && (
                  <div className="card">
                    <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                      <Flame className="w-5 h-5 text-orange-500" />
                      Top Prop Suggestions ({analysis.suggestions.length})
                    </h3>

                    <div className="space-y-3">
                      {analysis.suggestions.slice(0, 5).map((suggestion, i) => (
                        <div
                          key={i}
                          className="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
                        >
                          <div>
                            <div className="flex items-center gap-2">
                              <span className="font-medium">{suggestion.player_name}</span>
                              <span className="text-xs text-gray-500">{suggestion.team_abbreviation}</span>
                            </div>
                            <div className="text-sm text-gray-600">
                              {suggestion.prop_type} O/U {suggestion.prop_line}
                            </div>
                            <div className="flex items-center gap-2 mt-1">
                              {suggestion.key_factors.map((factor, j) => (
                                <span key={j} className="text-xs px-2 py-0.5 bg-gray-200 rounded">
                                  {factor}
                                </span>
                              ))}
                            </div>
                          </div>
                          <div className="text-right">
                            <div className={`px-2 py-1 rounded text-sm font-medium ${getRecommendationColor(suggestion.recommendation)}`}>
                              {suggestion.recommendation.replace('_', ' ').toUpperCase()}
                            </div>
                            <div className={`text-lg font-bold mt-1 ${getConfidenceColor(suggestion.confidence_score)}`}>
                              {suggestion.confidence_score}%
                            </div>
                            <div className="text-xs text-gray-500">
                              Current: {suggestion.current_value} | Proj: {suggestion.projected_final}
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Player Analysis Table */}
                <div className="card">
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="text-lg font-semibold flex items-center gap-2">
                      <Users className="w-5 h-5 text-purple-500" />
                      Player Analysis
                    </h3>

                    <div className="flex items-center gap-4">
                      <select
                        value={filterPropType}
                        onChange={(e) => setFilterPropType(e.target.value)}
                        className="text-sm border rounded px-2 py-1"
                      >
                        <option value="all">All Props</option>
                        <option value="points">Points</option>
                        <option value="rebounds">Rebounds</option>
                        <option value="assists">Assists</option>
                      </select>

                      <div className="flex items-center gap-2">
                        <span className="text-sm text-gray-500">Min Conf:</span>
                        <input
                          type="range"
                          min="0"
                          max="100"
                          value={minConfidence}
                          onChange={(e) => setMinConfidence(parseInt(e.target.value))}
                          className="w-24"
                        />
                        <span className="text-sm font-medium w-10">{minConfidence}%</span>
                      </div>
                    </div>
                  </div>

                  {filteredAnalyses.length === 0 ? (
                    <div className="text-center py-8 text-gray-500">
                      No players match the current filters
                    </div>
                  ) : (
                    <div className="overflow-x-auto">
                      <table className="w-full text-sm">
                        <thead>
                          <tr className="border-b">
                            <th className="text-left py-2 px-2">Player</th>
                            <th className="text-left py-2 px-2">Prop</th>
                            <th className="text-right py-2 px-2">1H</th>
                            <th className="text-right py-2 px-2">Proj</th>
                            <th className="text-right py-2 px-2">Line</th>
                            <th className="text-right py-2 px-2">Edge</th>
                            <th className="text-center py-2 px-2">Conf</th>
                            <th className="text-center py-2 px-2">Rec</th>
                            <th className="text-center py-2 px-2">Risk</th>
                          </tr>
                        </thead>
                        <tbody>
                          {filteredAnalyses.map((player, i) => (
                            <tr key={i} className="border-b hover:bg-gray-50">
                              <td className="py-2 px-2">
                                <div className="font-medium">{player.player_name}</div>
                                <div className="text-xs text-gray-500">{player.team_abbreviation}</div>
                              </td>
                              <td className="py-2 px-2 capitalize">{player.prop_type}</td>
                              <td className="py-2 px-2 text-right">{player.first_half_value}</td>
                              <td className="py-2 px-2 text-right font-medium">{player.projected_final}</td>
                              <td className="py-2 px-2 text-right">{player.prop_line}</td>
                              <td className={`py-2 px-2 text-right font-medium ${player.distance_from_line >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                                {player.distance_from_line >= 0 ? '+' : ''}{player.distance_from_line}
                              </td>
                              <td className="py-2 px-2 text-center">
                                <span className={`font-bold ${getConfidenceColor(player.confidence_score)}`}>
                                  {player.confidence_score}%
                                </span>
                              </td>
                              <td className="py-2 px-2 text-center">
                                <span className={`px-2 py-0.5 rounded text-xs font-medium ${getRecommendationColor(player.recommendation)}`}>
                                  {player.recommendation.replace('_', ' ')}
                                </span>
                              </td>
                              <td className="py-2 px-2 text-center">
                                <div className="flex items-center justify-center gap-1">
                                  {player.foul_trouble && (
                                    <span title="Foul Trouble" className="text-yellow-500">
                                      <Shield className="w-4 h-4" />
                                    </span>
                                  )}
                                  {player.blowout_warning && (
                                    <span title="Blowout Warning" className="text-red-500">
                                      <AlertTriangle className="w-4 h-4" />
                                    </span>
                                  )}
                                  {!player.foul_trouble && !player.blowout_warning && (
                                    <span className="text-green-500">
                                      <CheckCircle className="w-4 h-4" />
                                    </span>
                                  )}
                                </div>
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  )}
                </div>
              </>
            ) : null}
          </div>
        </div>
      </main>
    </div>
  );
}
