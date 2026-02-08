"""
Pydantic schemas for halftime analysis API.
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


# ============== Live Game Schemas ==============

class LivePlayerStatsResponse(BaseModel):
    """Live player statistics from a game in progress."""
    player_id: int
    player_name: str
    team_id: int
    team_abbreviation: str
    minutes: str
    minutes_float: float
    points: int
    rebounds: int
    assists: int
    steals: int
    blocks: int
    turnovers: int
    fouls: int
    fg_made: int
    fg_attempted: int
    fg_pct: float
    fg3_made: int
    fg3_attempted: int
    fg3_pct: float
    ft_made: int
    ft_attempted: int
    ft_pct: float
    plus_minus: int
    starter: bool


class TeamInfoResponse(BaseModel):
    """Team info in a live game."""
    team_id: int
    team_name: str
    team_abbr: str
    score: int


class LiveGameResponse(BaseModel):
    """Live game data response."""
    game_id: str
    game_status: int
    game_status_text: str
    period: int
    game_clock: str
    home_team_id: int
    home_team_name: str
    home_team_abbr: str
    home_score: int
    away_team_id: int
    away_team_name: str
    away_team_abbr: str
    away_score: int
    game_date: str
    game_time_utc: Optional[str] = None
    is_halftime: bool
    score_differential: int = 0
    total_score: int = 0


class LiveBoxScoreResponse(BaseModel):
    """Box score response for a live game."""
    game_id: str
    home_team: TeamInfoResponse
    away_team: TeamInfoResponse
    home_players: List[LivePlayerStatsResponse]
    away_players: List[LivePlayerStatsResponse]


# ============== Analysis Schemas ==============

class HalftimePlayerAnalysisResponse(BaseModel):
    """Analysis result for a single player at halftime."""
    player_id: int
    player_name: str
    team_abbreviation: str
    prop_type: str
    prop_line: float
    over_under: str = "over"

    # First half performance
    first_half_value: float
    first_half_minutes: float
    first_half_pace: float = Field(description="First half stat per minute")

    # Historical context
    season_average: Optional[float] = None
    second_half_historical_avg: Optional[float] = None
    last_5_games_avg: Optional[float] = None

    # Projections
    projected_second_half: float
    projected_final: float
    distance_from_line: float = Field(description="Projected final - line")

    # Confidence and recommendation
    confidence_score: float = Field(ge=0, le=100)
    recommendation: str = Field(description="strong_bet, bet, lean, neutral, avoid, strong_avoid")

    # Factor breakdown
    factors: Dict[str, float] = Field(default_factory=dict)

    # Risk indicators
    foul_trouble: bool = False
    blowout_warning: bool = False
    pace_factor: float = Field(default=1.0, description="Game pace relative to league average")
    utilization_rate: float = Field(default=0.0, description="Usage % in first half")
    fatigue_factor: float = Field(default=1.0, description="1.0 = normal, <1 = fatigued")
    minutes_projection: float = Field(default=0.0, description="Expected remaining minutes")

    # Extra stats
    plus_minus: int = 0
    assist_to_turnover: Optional[float] = None
    shooting_efficiency: Optional[float] = None

    analysis_notes: Optional[str] = None


class GameTotalAnalysisResponse(BaseModel):
    """Analysis of game totals at halftime."""
    game_id: str
    home_team: str
    away_team: str

    # Current state
    current_total: int
    first_half_total: int
    score_differential: int

    # Pace metrics
    first_half_pace: float = Field(description="Points per minute in first half")
    pace_rating: str = Field(description="slow, average, fast, very_fast")
    league_avg_pace_comparison: float = Field(description="Relative to league average")

    # Projections
    projected_second_half_total: float
    projected_final_total: float
    projected_q3_total: float
    projected_q4_total: float

    # Confidence
    total_confidence: float = Field(ge=0, le=100)

    # Risk factors
    blowout_risk: bool = False
    pace_sustainability: float = Field(description="How sustainable is current pace")

    analysis_notes: Optional[str] = None


class PropSuggestionResponse(BaseModel):
    """A suggested prop bet from halftime analysis."""
    player_name: str
    team_abbreviation: str
    prop_type: str
    prop_line: float
    current_value: float
    projected_final: float
    confidence_score: float
    recommendation: str
    edge: float = Field(description="Expected edge over the line")
    risk_level: str = Field(description="low, medium, high")
    key_factors: List[str] = Field(default_factory=list)


class HalftimeAnalysisResponse(BaseModel):
    """Complete halftime analysis response."""
    game_id: str
    game_info: LiveGameResponse
    game_total_analysis: GameTotalAnalysisResponse
    player_analyses: List[HalftimePlayerAnalysisResponse]
    suggestions: List[PropSuggestionResponse]
    analysis_timestamp: datetime
    warnings: List[str] = Field(default_factory=list)
    enhanced_game_totals: Optional["EnhancedGameTotalAnalysisResponse"] = None


class HalftimeSuggestionsResponse(BaseModel):
    """Filtered prop suggestions response."""
    game_id: str
    suggestions: List[PropSuggestionResponse]
    total_count: int
    high_confidence_count: int
    filters_applied: Dict[str, Any] = Field(default_factory=dict)


# ============== Snapshot Schemas ==============

class SnapshotCreateRequest(BaseModel):
    """Request to save an analysis snapshot."""
    game_id: str


class SnapshotResponse(BaseModel):
    """Response after saving a snapshot."""
    id: int
    game_id: str
    home_team: str
    away_team: str
    home_score: int
    away_score: int
    total_suggestions: int
    high_confidence_count: int
    snapshot_time: datetime

    class Config:
        from_attributes = True


class SnapshotDetailResponse(SnapshotResponse):
    """Detailed snapshot response including all analysis data."""
    analysis_data: Dict[str, Any]
    suggestions: List[PropSuggestionResponse]


# ============== Game Total Props Schemas ==============

class GameTotalPropResponse(BaseModel):
    """A game total prop from Kalshi."""
    game_id: Optional[str] = None
    home_team: str
    away_team: str
    line: float
    over_odds: int
    under_odds: int
    kalshi_ticker: Optional[str] = None
    close_time: Optional[str] = None


class GameTotalPropsListResponse(BaseModel):
    """List of game total props."""
    props: List[GameTotalPropResponse]
    count: int


# ============== Enhanced Game Totals Schemas ==============

class PaceAnalysisResponse(BaseModel):
    """Detailed pace breakdown for a game."""
    first_half_possessions_est: float
    possessions_per_48_live: float
    points_per_possession_home: float
    points_per_possession_away: float
    home_season_pace: float
    away_season_pace: float
    matchup_expected_pace: float
    pace_deviation: float = Field(description="% deviation from expected pace")
    pace_trend: str = Field(description="accelerating, decelerating, steady")
    q1_pace: Optional[float] = None
    q2_pace: Optional[float] = None
    transition_rate: float = 0.0


class TeamShootingProfileResponse(BaseModel):
    """Team-level shooting efficiency profile."""
    team_abbr: str
    live_efg_pct: float
    live_ts_pct: float
    live_fg3_rate: float
    live_fg3_pct: float
    live_ft_rate: float
    live_ft_pct: float
    season_efg_pct: float
    season_ts_pct: float
    season_fg3_rate: float
    season_fg3_pct: float
    season_ft_rate: float
    shooting_regression_factor: float = Field(description="<1.0 = expect regression down, >1.0 = expect recovery")
    shooting_variance_level: str = Field(description="extreme_hot, hot, normal, cold, extreme_cold")


class StarPlayerImpactResponse(BaseModel):
    """Star player impact on team total."""
    player_name: str
    player_id: int
    team_abbr: str
    first_half_points: int
    first_half_minutes: float
    usage_rate: float
    current_efficiency: float = Field(description="TS%")
    foul_trouble: bool
    foul_count: int
    season_ppg: Optional[float] = None
    projected_2h_points: float
    projected_2h_minutes: float
    hot_cold_indicator: str = Field(description="hot, normal, cold")
    minutes_risk: str = Field(description="normal, foul_risk, blowout_risk")
    impact_on_team_total: float = Field(description="+/- points vs baseline")


class TeamQuarterProjectionResponse(BaseModel):
    """Per-team quarter-by-quarter score projection."""
    team_abbr: str
    q1_actual: Optional[int] = None
    q2_actual: Optional[int] = None
    q3_projected: float
    q4_projected: float
    ot_probability: float = 0.0
    projected_final_score: float


class SpreadPredictionResponse(BaseModel):
    """Point spread prediction."""
    current_spread: int
    home_lead: bool
    projected_final_spread: float
    spread_confidence: float
    star_performance_differential: float
    momentum_indicator: str = Field(description="home, away, neutral")
    close_game_probability: float
    blowout_probability: float


class OverUnderRecommendationResponse(BaseModel):
    """Over/under recommendation with edge calculation."""
    projected_total: float
    projected_range_low: float
    projected_range_high: float
    reference_line: Optional[float] = None
    edge: float = Field(description="Projected total minus reference line")
    edge_pct: float
    recommendation: str = Field(description="strong_over, lean_over, neutral, lean_under, strong_under")
    confidence: float


class EnhancedGameTotalAnalysisResponse(BaseModel):
    """Complete enhanced game totals analysis with deep analytics."""
    model_config = {"protected_namespaces": ()}
    game_id: str
    home_team: str
    away_team: str
    home_score: int
    away_score: int
    current_total: int
    first_half_total: int
    score_differential: int

    # Sub-analyses
    pace_analysis: PaceAnalysisResponse
    home_shooting: TeamShootingProfileResponse
    away_shooting: TeamShootingProfileResponse
    star_players: List[StarPlayerImpactResponse]

    # Per-team quarter projections
    home_quarters: TeamQuarterProjectionResponse
    away_quarters: TeamQuarterProjectionResponse

    # Combined projections
    projected_q3_total: float
    projected_q4_total: float
    projected_second_half_total: float
    projected_final_total: float

    # Spread and O/U
    spread_prediction: SpreadPredictionResponse
    over_under: OverUnderRecommendationResponse

    # Confidence and meta
    total_confidence: float
    blowout_risk: bool
    model_factors: Dict[str, float] = Field(default_factory=dict)
    analysis_notes: List[str] = Field(default_factory=list)


# Update forward ref for HalftimeAnalysisResponse
HalftimeAnalysisResponse.model_rebuild()
