// User types
export interface User {
  id: number;
  email: string;
  username: string;
  full_name?: string;
  is_active: boolean;
  created_at: string;
}

export interface LoginCredentials {
  username: string;
  password: string;
}

export interface RegisterData {
  email: string;
  username: string;
  password: string;
  full_name?: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
}

// Prop Bet types
export interface PropBet {
  id?: number;
  player_name: string;
  stat_type: string;
  line: number;
  over_under: 'over' | 'under';
  opponent_name?: string;
  game_date?: string;
  odds?: number;
}

export interface BetSlip {
  id?: number;
  user_id?: number;
  name?: string;
  slip_type?: string;
  status?: string;
  created_at?: string;
  analyzed_at?: string;
  prop_bets: PropBet[];
  image_url?: string;
}

// Game log for chart display
export interface GameLogData {
  date: string;
  opponent: string;
  value: number;
  hit: boolean;
  minutes: number;
  pts: number;
  reb: number;
  ast: number;
  fg_pct: number;
  oreb: number;
  dreb: number;
}

// Analysis types
export interface PropAnalysisDetail {
  prop_id: number;
  player_name: string;
  stat_type: string;
  line: number;
  over_under: string;
  confidence_score: number;
  hit_rate_last_10: number;
  hit_rate_last_20: number;
  average_stat: number;
  median_stat: number;
  floor: number;
  ceiling: number;
  opponent_defensive_rank?: number;
  opponent_pace?: number;
  pace_adjusted_projection: number;
  factors: Record<string, number>;
  recommendation: 'strong_bet' | 'bet' | 'lean' | 'neutral' | 'avoid' | 'strong_avoid';
  analysis_notes?: string;
  game_logs: GameLogData[];
  shooting_stats: {
    fg_pct?: number;
    fg3_pct?: number;
    ft_pct?: number;
    avg_minutes?: number;
  };
  rebound_breakdown: {
    oreb_avg?: number;
    dreb_avg?: number;
    total_reb_avg?: number;
  };
  season_average?: number;
  // New outlier/props.cash style features
  current_streak?: number;
  streak_description?: string;
  last_n_hits?: string;
  home_hit_rate?: number;
  away_hit_rate?: number;
  home_average?: number;
  away_average?: number;
  location_edge?: string;
  trend_direction?: string;
  trend_description?: string;
  minutes_consistency?: string;
  avg_minutes_last_5?: number;
  avg_minutes_last_10?: number;
  expected_value?: number;
  ev_rating?: string;
}

export interface Analysis {
  id: number;
  bet_slip_id: number;
  overall_confidence?: number;
  risk_assessment?: string;
  recommended_bets: number[];
  strong_bets: number[];
  avoid_bets: number[];
  parlay_suggestions?: Array<{
    props: number[];
    confidence: number;
    description: string;
  }>;
  prop_analyses: PropAnalysisDetail[];
  analysis_notes?: string;
  created_at: string;
}

export interface BetSlipWithAnalysis extends BetSlip {
  analysis?: Analysis;
}

// API Error type
export interface ApiError {
  detail: string;
}

// Workspace types
export interface Workspace {
  id: number;
  user_id: number;
  name: string;
  created_at: string;
  slip_count: number;
  analyzed_count: number;
}

export interface WorkspaceWithSlips extends Workspace {
  bet_slips: BetSlip[];
}

export interface AggregatedProp {
  player_name: string;
  stat_type: string;
  line: number;
  over_under: string;
  confidence_score: number;
  hit_rate_last_10: number;
  hit_rate_last_20: number;
  average_stat: number;
  median_stat: number;
  floor: number;
  ceiling: number;
  recommendation: string;
  analysis_notes?: string;
  source_slips: number[];
  consensus_count: number;
  prop_ids: number[];
  game_logs: GameLogData[];
  shooting_stats: Record<string, number>;
  rebound_breakdown: Record<string, number>;
  season_average?: number;
  odds?: number;
}

export interface AggregatedAnalysis {
  workspace_id: number;
  workspace_name: string;
  total_slips: number;
  analyzed_slips: number;
  total_props: number;
  unique_props: number;
  props_by_confidence: AggregatedProp[];
  consensus_props: AggregatedProp[];
  strong_bets: AggregatedProp[];
  good_bets: AggregatedProp[];
  avoid_bets: AggregatedProp[];
  average_confidence: number;
}

// Ladder types
export interface LadderLeg {
  order: number;
  player_name: string;
  stat_type: string;
  line: number;
  over_under: string;
  odds: number;
  confidence: number;
  tier?: string;
  prop_id?: number;
  decimal_odds?: number;
  implied_probability?: number;
  payout_if_win?: number;
  cumulative_payout?: number;
}

export interface LadderBet {
  id: number;
  user_id: number;
  name?: string;
  ladder_type: 'progressive' | 'tiered' | 'challenge';
  starting_stake: number;
  target_amount?: number;
  legs: LadderLeg[];
  status: string;
  created_at: string;
  total_legs: number;
  combined_odds?: number;
  potential_payout?: number;
  win_probability?: number;
}

export interface ProgressiveCalculation {
  starting_stake: number;
  legs: LadderLeg[];
  final_payout: number;
  total_odds_multiplier: number;
  overall_probability: number;
  roi_percentage: number;
}

export interface TieredCalculation {
  tiers: Record<string, LadderLeg[]>;
  tier_counts: Record<string, number>;
  suggested_allocation: Record<string, number>;
}

export interface ChallengeCalculation {
  start_amount: number;
  target_amount: number;
  recommended_legs: LadderLeg[];
  projected_payout: number;
  required_multiplier: number;
  achieved_multiplier: number;
  success_probability: number;
  meets_target: boolean;
}

export interface LadderCalculation {
  ladder_type: string;
  progressive?: ProgressiveCalculation;
  tiered?: TieredCalculation;
  challenge?: ChallengeCalculation;
}

// Kalshi types
export interface KalshiProp {
  player_name: string;
  stat_type: string;
  line: number;
  over_under: string;
  odds: number;
  kalshi_ticker: string;
  close_time?: string;
  volume?: number;
  yes_price?: number;
}

export interface KalshiPropAnalyzed extends KalshiProp {
  confidence_score: number;
  hit_rate_last_10: number;
  hit_rate_last_20: number;
  average_stat: number;
  median_stat: number;
  floor: number;
  ceiling: number;
  recommendation: string;
  analysis_notes: string;
  season_average?: number;
  // New outlier/props.cash style features
  current_streak: number;
  streak_description: string;
  last_n_hits: string;
  home_hit_rate?: number;
  away_hit_rate?: number;
  home_average?: number;
  away_average?: number;
  location_edge?: string;
  trend_direction: string;
  trend_description: string;
  minutes_consistency: string;
  avg_minutes_last_5?: number;
  avg_minutes_last_10?: number;
  expected_value?: number;
  ev_rating: string;
}

export interface KalshiPropsResponse {
  props: KalshiProp[];
  count: number;
  message?: string;
}

export interface KalshiAnalyzedResponse {
  props: KalshiPropAnalyzed[];
  count: number;
  analyzed_count: number;
  failed_count: number;
  message?: string;
}

// ============== Live Game / Halftime Types ==============

export interface LiveGame {
  game_id: string;
  game_status: number;
  game_status_text: string;
  period: number;
  game_clock: string;
  home_team_id: number;
  home_team_name: string;
  home_team_abbr: string;
  home_score: number;
  away_team_id: number;
  away_team_name: string;
  away_team_abbr: string;
  away_score: number;
  game_date: string;
  game_time_utc?: string;
  is_halftime: boolean;
  score_differential: number;
  total_score: number;
}

export interface LivePlayerStats {
  player_id: number;
  player_name: string;
  team_id: number;
  team_abbreviation: string;
  minutes: string;
  minutes_float: number;
  points: number;
  rebounds: number;
  assists: number;
  steals: number;
  blocks: number;
  turnovers: number;
  fouls: number;
  fg_made: number;
  fg_attempted: number;
  fg_pct: number;
  fg3_made: number;
  fg3_attempted: number;
  fg3_pct: number;
  ft_made: number;
  ft_attempted: number;
  ft_pct: number;
  plus_minus: number;
  starter: boolean;
}

export interface TeamInfo {
  team_id: number;
  team_name: string;
  team_abbr: string;
  score: number;
}

export interface LiveBoxScore {
  game_id: string;
  home_team: TeamInfo;
  away_team: TeamInfo;
  home_players: LivePlayerStats[];
  away_players: LivePlayerStats[];
}

export interface HalftimePlayerAnalysis {
  player_id: number;
  player_name: string;
  team_abbreviation: string;
  prop_type: string;
  prop_line: number;
  over_under?: string;

  // First half performance
  first_half_value: number;
  first_half_minutes: number;
  first_half_pace: number;

  // Historical context
  season_average?: number;
  second_half_historical_avg?: number;
  last_5_games_avg?: number;

  // Projections
  projected_second_half: number;
  projected_final: number;
  distance_from_line: number;

  // Confidence and recommendation
  confidence_score: number;
  recommendation: 'strong_bet' | 'bet' | 'lean' | 'neutral' | 'avoid' | 'strong_avoid';

  // Factor breakdown
  factors: Record<string, number>;

  // Risk indicators
  foul_trouble: boolean;
  blowout_warning: boolean;
  pace_factor: number;
  utilization_rate: number;
  fatigue_factor: number;
  minutes_projection: number;

  // Extra stats
  plus_minus?: number;
  assist_to_turnover?: number;
  shooting_efficiency?: number;

  analysis_notes?: string;
}

export interface GameTotalAnalysis {
  game_id: string;
  home_team: string;
  away_team: string;

  // Current state
  current_total: number;
  first_half_total: number;
  score_differential: number;

  // Pace metrics
  first_half_pace: number;
  pace_rating: 'slow' | 'average' | 'fast' | 'very_fast';
  league_avg_pace_comparison: number;

  // Projections
  projected_second_half_total: number;
  projected_final_total: number;
  projected_q3_total: number;
  projected_q4_total: number;

  // Confidence
  total_confidence: number;

  // Risk factors
  blowout_risk: boolean;
  pace_sustainability: number;

  analysis_notes?: string;
}

export interface PropSuggestion {
  player_name: string;
  team_abbreviation: string;
  prop_type: string;
  prop_line: number;
  current_value: number;
  projected_final: number;
  confidence_score: number;
  recommendation: string;
  edge: number;
  risk_level: 'low' | 'medium' | 'high';
  key_factors: string[];
}

export interface HalftimeAnalysisResponse {
  game_id: string;
  game_info: LiveGame;
  game_total_analysis: GameTotalAnalysis;
  player_analyses: HalftimePlayerAnalysis[];
  suggestions: PropSuggestion[];
  analysis_timestamp: string;
  warnings: string[];
  enhanced_game_totals?: EnhancedGameTotalAnalysis;
}

export interface HalftimeSuggestionsResponse {
  game_id: string;
  suggestions: PropSuggestion[];
  total_count: number;
  high_confidence_count: number;
  filters_applied: Record<string, any>;
}

export interface AnalysisSnapshot {
  id: number;
  game_id: string;
  home_team: string;
  away_team: string;
  home_score: number;
  away_score: number;
  total_suggestions: number;
  high_confidence_count: number;
  snapshot_time: string;
}

export interface SnapshotDetail extends AnalysisSnapshot {
  analysis_data: HalftimeAnalysisResponse;
  suggestions: PropSuggestion[];
}

export interface GameTotalProp {
  game_id?: string;
  home_team: string;
  away_team: string;
  line: number;
  over_odds: number;
  under_odds: number;
  kalshi_ticker?: string;
  close_time?: string;
}

// ============== Enhanced Game Totals Types ==============

export interface PaceAnalysis {
  first_half_possessions_est: number;
  possessions_per_48_live: number;
  points_per_possession_home: number;
  points_per_possession_away: number;
  home_season_pace: number;
  away_season_pace: number;
  matchup_expected_pace: number;
  pace_deviation: number;
  pace_trend: 'accelerating' | 'decelerating' | 'steady';
  q1_pace?: number;
  q2_pace?: number;
  transition_rate: number;
}

export interface TeamShootingProfile {
  team_abbr: string;
  live_efg_pct: number;
  live_ts_pct: number;
  live_fg3_rate: number;
  live_fg3_pct: number;
  live_ft_rate: number;
  live_ft_pct: number;
  season_efg_pct: number;
  season_ts_pct: number;
  season_fg3_rate: number;
  season_fg3_pct: number;
  season_ft_rate: number;
  shooting_regression_factor: number;
  shooting_variance_level: 'extreme_hot' | 'hot' | 'normal' | 'cold' | 'extreme_cold';
}

export interface StarPlayerImpact {
  player_name: string;
  player_id: number;
  team_abbr: string;
  first_half_points: number;
  first_half_minutes: number;
  usage_rate: number;
  current_efficiency: number;
  foul_trouble: boolean;
  foul_count: number;
  season_ppg?: number;
  projected_2h_points: number;
  projected_2h_minutes: number;
  hot_cold_indicator: 'hot' | 'normal' | 'cold';
  minutes_risk: string;
  impact_on_team_total: number;
}

export interface TeamQuarterProjection {
  team_abbr: string;
  q1_actual?: number;
  q2_actual?: number;
  q3_projected: number;
  q4_projected: number;
  ot_probability: number;
  projected_final_score: number;
}

export interface SpreadPrediction {
  current_spread: number;
  home_lead: boolean;
  projected_final_spread: number;
  spread_confidence: number;
  star_performance_differential: number;
  momentum_indicator: 'home' | 'away' | 'neutral';
  close_game_probability: number;
  blowout_probability: number;
}

export interface OverUnderRecommendation {
  projected_total: number;
  projected_range_low: number;
  projected_range_high: number;
  reference_line?: number;
  edge: number;
  edge_pct: number;
  recommendation: 'strong_over' | 'lean_over' | 'neutral' | 'lean_under' | 'strong_under';
  confidence: number;
}

export interface EnhancedGameTotalAnalysis {
  game_id: string;
  home_team: string;
  away_team: string;
  home_score: number;
  away_score: number;
  current_total: number;
  first_half_total: number;
  score_differential: number;

  pace_analysis: PaceAnalysis;
  home_shooting: TeamShootingProfile;
  away_shooting: TeamShootingProfile;
  star_players: StarPlayerImpact[];

  home_quarters: TeamQuarterProjection;
  away_quarters: TeamQuarterProjection;

  projected_q3_total: number;
  projected_q4_total: number;
  projected_second_half_total: number;
  projected_final_total: number;

  spread_prediction: SpreadPrediction;
  over_under: OverUnderRecommendation;

  total_confidence: number;
  blowout_risk: boolean;
  model_factors: Record<string, number>;
  analysis_notes: string[];
}
