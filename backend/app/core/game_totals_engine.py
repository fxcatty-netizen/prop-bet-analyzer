"""
Advanced Game Totals & Quarter Predictions Engine.

Provides comprehensive game total projections using a multi-factor weighted model
with heavy emphasis on PACE, shooting efficiency, and star player utilization.
Integrates data from both nba_api (live) and BallDontLie (historical/season).
"""
import logging
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any, Tuple

logger = logging.getLogger(__name__)

# ============================================================
# Constants
# ============================================================
LEAGUE_AVG_PACE = 100.0          # League avg possessions per 48 min
LEAGUE_AVG_TOTAL = 225.0         # League avg combined score per game
LEAGUE_AVG_PPP = 1.14            # League avg points per possession
LEAGUE_AVG_EFG = 52.5            # League avg eFG%
LEAGUE_AVG_TS = 57.5             # League avg TS%

Q3_PACE_FACTOR = 0.91            # Q3 historically ~9% slower
Q4_CLOSE_FACTOR = 1.06           # Close games → faster Q4
Q4_MODERATE_FACTOR = 0.98        # Moderate lead → slightly slower
Q4_BLOWOUT_FACTOR = 0.88         # Blowout → garbage time

BLOWOUT_THRESHOLD = 20
CLOSE_GAME_THRESHOLD = 8
MODERATE_LEAD_THRESHOLD = 15

FOUL_TROUBLE_THRESHOLD = 3
SHOOTING_REGRESSION_RATE = 0.40  # Regress 40% back to mean

# Projection weights - heavy on PACE, shooting, stars per user request
TOTALS_WEIGHTS = {
    'pace_component': 0.30,
    'shooting_component': 0.25,
    'star_utilization': 0.20,
    'game_flow': 0.10,
    'team_ratings': 0.10,
    'regression': 0.05,
}


# ============================================================
# Data Structures
# ============================================================
@dataclass
class PaceAnalysis:
    """Detailed pace breakdown for the game."""
    first_half_possessions_est: float
    possessions_per_48_live: float
    points_per_possession_home: float
    points_per_possession_away: float
    home_season_pace: float
    away_season_pace: float
    matchup_expected_pace: float
    pace_deviation: float
    pace_trend: str                     # accelerating, decelerating, steady
    q1_pace: Optional[float] = None
    q2_pace: Optional[float] = None
    transition_rate: float = 0.0


@dataclass
class TeamShootingProfile:
    """Team-level shooting efficiency for one team."""
    team_abbr: str
    # Current game
    live_efg_pct: float
    live_ts_pct: float
    live_fg3_rate: float
    live_fg3_pct: float
    live_ft_rate: float
    live_ft_pct: float
    # Season baselines
    season_efg_pct: float
    season_ts_pct: float
    season_fg3_rate: float
    season_fg3_pct: float
    season_ft_rate: float
    # Regression signals
    shooting_regression_factor: float
    shooting_variance_level: str        # extreme_hot, hot, normal, cold, extreme_cold


@dataclass
class StarPlayerImpact:
    """Star player's impact on team total."""
    player_name: str
    player_id: int
    team_abbr: str
    first_half_points: int
    first_half_minutes: float
    usage_rate: float
    current_efficiency: float           # TS%
    foul_trouble: bool
    foul_count: int
    season_ppg: Optional[float] = None
    projected_2h_points: float = 0.0
    projected_2h_minutes: float = 0.0
    hot_cold_indicator: str = "normal"
    minutes_risk: str = "normal"
    impact_on_team_total: float = 0.0


@dataclass
class TeamQuarterProjection:
    """Per-team, per-quarter score projection."""
    team_abbr: str
    q1_actual: Optional[int] = None
    q2_actual: Optional[int] = None
    q3_projected: float = 0.0
    q4_projected: float = 0.0
    ot_probability: float = 0.0
    projected_final_score: float = 0.0


@dataclass
class SpreadPrediction:
    """Point spread analysis and prediction."""
    current_spread: int
    home_lead: bool
    projected_final_spread: float = 0.0
    spread_confidence: float = 50.0
    star_performance_differential: float = 0.0
    momentum_indicator: str = "neutral"
    close_game_probability: float = 35.0
    blowout_probability: float = 10.0


@dataclass
class OverUnderRecommendation:
    """Over/under recommendation with edge calculation."""
    projected_total: float
    projected_range_low: float
    projected_range_high: float
    reference_line: Optional[float] = None
    edge: float = 0.0
    edge_pct: float = 0.0
    recommendation: str = "neutral"
    confidence: float = 50.0


@dataclass
class EnhancedGameTotalProjection:
    """Complete enhanced game totals projection."""
    game_id: str
    home_team: str
    away_team: str
    home_score: int
    away_score: int
    current_total: int
    first_half_total: int
    score_differential: int
    period: int
    game_clock: str

    pace_analysis: PaceAnalysis = None
    home_shooting: TeamShootingProfile = None
    away_shooting: TeamShootingProfile = None
    star_players: List[StarPlayerImpact] = field(default_factory=list)

    home_quarters: TeamQuarterProjection = None
    away_quarters: TeamQuarterProjection = None

    projected_q3_total: float = 0.0
    projected_q4_total: float = 0.0
    projected_second_half_total: float = 0.0
    projected_final_total: float = 0.0

    spread_prediction: SpreadPrediction = None
    over_under: OverUnderRecommendation = None

    total_confidence: float = 50.0
    blowout_risk: bool = False
    model_factors: Dict[str, float] = field(default_factory=dict)
    analysis_notes: List[str] = field(default_factory=list)


# ============================================================
# Engine
# ============================================================
class GameTotalsEngine:
    """
    Advanced game totals prediction engine.

    Weighting: heavy on PACE (0.30), shooting efficiency (0.25),
    and star utilization (0.20) per user requirements.
    """

    def __init__(self, live_client, bdl_service=None, bdl_analytics=None):
        self.live_client = live_client
        self.bdl_service = bdl_service
        self.bdl_analytics = bdl_analytics
        self._season_stats_cache: Dict[int, Optional[Dict]] = {}

    async def _get_player_season_stats(self, player_id: int, player_name: str) -> Optional[Dict]:
        """Get player season stats using nba_api with BDL fallback (cached per analysis run)."""
        if player_id in self._season_stats_cache:
            return self._season_stats_cache[player_id]

        stats = None
        # Try nba_api first
        try:
            raw = await self.live_client.get_player_season_stats(player_id)
            if raw:
                stats = {
                    'pts': raw.get('avg_points', 0),
                    'fg_pct': raw.get('avg_fg_pct', 0) / 100 if raw.get('avg_fg_pct', 0) > 1 else raw.get('avg_fg_pct', 0),
                    'fg3_pct': raw.get('avg_fg3_pct', 0) / 100 if raw.get('avg_fg3_pct', 0) > 1 else raw.get('avg_fg3_pct', 0),
                    'ft_pct': raw.get('avg_ft_pct', 0) / 100 if raw.get('avg_ft_pct', 0) > 1 else raw.get('avg_ft_pct', 0),
                    'min': raw.get('avg_minutes', 0),
                }
        except Exception as e:
            logger.debug(f"nba_api season stats failed for {player_name} ({player_id}): {e}")

        # BDL fallback
        if stats is None and self.bdl_analytics:
            try:
                bdl = await self.bdl_analytics.get_player_season_avg(player_name)
                if bdl:
                    stats = {
                        'pts': bdl.get('pts', 0),
                        'fg_pct': bdl.get('fg_pct', 0),
                        'fg3_pct': bdl.get('fg3_pct', 0),
                        'ft_pct': bdl.get('ft_pct', 0),
                        'min': bdl.get('min', 0),
                    }
                    logger.info(f"Used BDL fallback for {player_name} season stats")
            except Exception as e:
                logger.debug(f"BDL season stats also failed for {player_name}: {e}")

        self._season_stats_cache[player_id] = stats
        return stats

    # ----------------------------------------------------------
    # Helpers
    # ----------------------------------------------------------
    @staticmethod
    def _elapsed_minutes(game_data) -> float:
        """Estimate elapsed game minutes from period and clock."""
        period = game_data.period
        clock = game_data.game_clock or ""

        # Each quarter is 12 minutes
        completed_quarters = max(period - 1, 0)
        elapsed = completed_quarters * 12.0

        # Parse remaining clock in current quarter
        remaining_in_q = 12.0
        try:
            if ":" in clock:
                parts = clock.replace("PT", "").replace("S", "").split(":")
                if len(parts) == 2:
                    mins = float(parts[0].replace("M", ""))
                    secs = float(parts[1])
                    remaining_in_q = mins + secs / 60.0
            elif clock:
                remaining_in_q = float(clock.replace("PT", "").replace("M", "").replace("S", "")) / 60.0
        except (ValueError, IndexError):
            pass

        elapsed += (12.0 - remaining_in_q)
        return max(elapsed, 1.0)

    # ----------------------------------------------------------
    # Main Entry Point
    # ----------------------------------------------------------
    async def analyze(
        self,
        game_data,
        box_score: Dict[str, Any],
        home_ratings=None,
        away_ratings=None,
        reference_line: Optional[float] = None
    ) -> EnhancedGameTotalProjection:
        """Run complete enhanced game totals analysis."""
        home_players = box_score.get('home', [])
        away_players = box_score.get('away', [])

        # Aggregate team box scores
        home_agg = self.live_client.aggregate_team_box_score(home_players)
        away_agg = self.live_client.aggregate_team_box_score(away_players)

        # Period-aware elapsed time
        elapsed_min = self._elapsed_minutes(game_data)
        total_game_min = 48.0
        remaining_min = max(total_game_min - elapsed_min, 0.0)
        elapsed_fraction = elapsed_min / total_game_min

        # 1. Pace Analysis (weight: 0.30)
        pace = self._analyze_pace(
            game_data, home_agg, away_agg,
            home_ratings, away_ratings, elapsed_min
        )

        # 2. Shooting Profiles (weight: 0.25)
        home_shooting = await self._analyze_team_shooting(
            game_data.home_team_abbr, home_players, home_agg
        )
        away_shooting = await self._analyze_team_shooting(
            game_data.away_team_abbr, away_players, away_agg
        )

        # 3. Star Player Analysis (weight: 0.20)
        stars = await self._analyze_star_players(
            home_players, away_players, game_data, home_agg, away_agg, remaining_min
        )

        # 4. Game flow assessment
        blowout_risk = abs(game_data.score_differential) >= BLOWOUT_THRESHOLD
        is_close = abs(game_data.score_differential) <= CLOSE_GAME_THRESHOLD

        # 5. Build per-component remaining-game projections
        current_total = game_data.total_score
        scoring_rate = current_total / max(elapsed_min, 1)  # Points per minute so far

        # -- Pace component: possession-based projection
        pace_projected_remaining = self._pace_projection(
            pace, home_agg, away_agg, current_total, remaining_min, elapsed_min
        )

        # -- Shooting component: efficiency-adjusted projection
        shooting_projected_remaining = self._shooting_projection(
            home_shooting, away_shooting, scoring_rate, current_total, remaining_min
        )

        # -- Star utilization component
        star_projected_remaining = self._star_utilization_projection(
            stars, scoring_rate, current_total, remaining_min
        )

        # -- Game flow component
        game_flow_projected_remaining = self._game_flow_projection(
            game_data, scoring_rate, current_total, remaining_min
        )

        # -- Team ratings component
        ratings_projected_remaining = self._team_ratings_projection(
            home_ratings, away_ratings, current_total, remaining_min
        )

        # -- Regression component (mean reversion to league average)
        season_avg_total = LEAGUE_AVG_TOTAL
        if home_ratings and away_ratings:
            expected_pace = (home_ratings.pace + away_ratings.pace) / 2
            avg_off_rtg = (home_ratings.off_rating + away_ratings.off_rating) / 2
            season_avg_total = expected_pace * (avg_off_rtg / 100) * 2
        # Remaining portion of season average
        regression_projected_remaining = season_avg_total * (remaining_min / total_game_min)

        # Weighted combination
        projected_remaining = (
            TOTALS_WEIGHTS['pace_component'] * pace_projected_remaining +
            TOTALS_WEIGHTS['shooting_component'] * shooting_projected_remaining +
            TOTALS_WEIGHTS['star_utilization'] * star_projected_remaining +
            TOTALS_WEIGHTS['game_flow'] * game_flow_projected_remaining +
            TOTALS_WEIGHTS['team_ratings'] * ratings_projected_remaining +
            TOTALS_WEIGHTS['regression'] * regression_projected_remaining
        )

        projected_final = current_total + projected_remaining

        # 6. Quarter projections
        home_q, away_q = self._project_quarters(
            projected_remaining, game_data, home_ratings, away_ratings,
            home_agg, away_agg, elapsed_min
        )

        projected_q3 = home_q.q3_projected + away_q.q3_projected
        projected_q4 = home_q.q4_projected + away_q.q4_projected

        # 7. Spread prediction
        spread = self._predict_spread(
            game_data, stars, home_ratings, away_ratings, pace
        )

        # 8. Over/Under recommendation
        variance = self._calculate_variance(pace, home_shooting, away_shooting)
        over_under = self._calculate_over_under(
            projected_final, variance, reference_line,
            season_avg_total, home_shooting, away_shooting, pace
        )

        # 9. Overall confidence
        total_confidence = self._calculate_total_confidence(
            pace, home_shooting, away_shooting, stars, blowout_risk, is_close
        )

        # 10. Analysis notes
        notes = self._generate_notes(
            pace, home_shooting, away_shooting, stars,
            blowout_risk, game_data
        )

        return EnhancedGameTotalProjection(
            game_id=game_data.game_id,
            home_team=game_data.home_team_abbr,
            away_team=game_data.away_team_abbr,
            home_score=game_data.home_score,
            away_score=game_data.away_score,
            current_total=game_data.total_score,
            first_half_total=current_total,
            score_differential=game_data.score_differential,
            period=game_data.period,
            game_clock=game_data.game_clock,
            pace_analysis=pace,
            home_shooting=home_shooting,
            away_shooting=away_shooting,
            star_players=stars,
            home_quarters=home_q,
            away_quarters=away_q,
            projected_q3_total=round(projected_q3, 1),
            projected_q4_total=round(projected_q4, 1),
            projected_second_half_total=round(projected_remaining, 1),
            projected_final_total=round(projected_final, 1),
            spread_prediction=spread,
            over_under=over_under,
            total_confidence=round(total_confidence, 1),
            blowout_risk=blowout_risk,
            model_factors={k: round(v, 3) for k, v in TOTALS_WEIGHTS.items()},
            analysis_notes=notes,
        )

    # ----------------------------------------------------------
    # Pace Analysis
    # ----------------------------------------------------------
    def _analyze_pace(
        self, game_data, home_agg, away_agg, home_ratings, away_ratings,
        elapsed_min: float = 24.0
    ) -> PaceAnalysis:
        """Possession-based pace analysis - the heaviest weighted factor."""
        home_poss = home_agg['estimated_possessions']
        away_poss = away_agg['estimated_possessions']
        total_poss_elapsed = (home_poss + away_poss) / 2  # Average both teams

        # Extrapolate to per-48 based on actual elapsed time
        poss_per_48_live = total_poss_elapsed * (48.0 / max(elapsed_min, 1))

        # Points per possession
        home_ppp = home_agg['total_points'] / max(home_poss, 1)
        away_ppp = away_agg['total_points'] / max(away_poss, 1)

        # Season pace from team ratings
        home_season_pace = home_ratings.pace if home_ratings else LEAGUE_AVG_PACE
        away_season_pace = away_ratings.pace if away_ratings else LEAGUE_AVG_PACE
        matchup_expected = (home_season_pace + away_season_pace) / 2

        # Deviation: how much faster/slower than expected
        pace_deviation = ((poss_per_48_live - matchup_expected) / max(matchup_expected, 1)) * 100

        # Q1 vs Q2 pace trend (estimate from score if period >= 2)
        q1_pace = None
        q2_pace = None
        pace_trend = "steady"

        # With live score we can't perfectly split Q1/Q2 scores,
        # but we can use total_score / period to approximate
        if game_data.period >= 2:
            avg_q_pace = game_data.total_score / game_data.period
            # If current period is 2 and we're at half, split is roughly even
            # For simplicity, use a heuristic
            q1_pace = avg_q_pace * 1.02  # Q1 typically slightly faster
            q2_pace = avg_q_pace * 0.98

            if pace_deviation > 5:
                pace_trend = "accelerating"
            elif pace_deviation < -5:
                pace_trend = "decelerating"

        return PaceAnalysis(
            first_half_possessions_est=round(total_poss_elapsed, 1),
            possessions_per_48_live=round(poss_per_48_live, 1),
            points_per_possession_home=round(home_ppp, 3),
            points_per_possession_away=round(away_ppp, 3),
            home_season_pace=round(home_season_pace, 1),
            away_season_pace=round(away_season_pace, 1),
            matchup_expected_pace=round(matchup_expected, 1),
            pace_deviation=round(pace_deviation, 1),
            pace_trend=pace_trend,
            q1_pace=round(q1_pace, 1) if q1_pace else None,
            q2_pace=round(q2_pace, 1) if q2_pace else None,
        )

    def _pace_projection(self, pace, home_agg, away_agg, current_total,
                         remaining_min: float = 24.0, elapsed_min: float = 24.0):
        """Project remaining-game total from pace analysis."""
        # Use live PPP * expected remaining possessions
        live_ppp = (
            (home_agg['total_points'] + away_agg['total_points']) /
            max(pace.first_half_possessions_est, 1)
        )

        # Possessions per minute from live data
        poss_per_min = pace.first_half_possessions_est / max(elapsed_min, 1)

        # Expected remaining poss per min from season pace
        expected_poss_per_min = pace.matchup_expected_pace / 48.0

        # Regress live pace 30% toward season expectation
        regressed_ppm = poss_per_min * 0.70 + expected_poss_per_min * 0.30

        # Apply slight slowdown for remaining game
        regressed_ppm *= 0.97

        remaining_poss = regressed_ppm * remaining_min

        # PPP also regresses toward league average
        regressed_ppp = live_ppp * 0.75 + LEAGUE_AVG_PPP * 0.25

        return remaining_poss * regressed_ppp * 2  # Both teams

    # ----------------------------------------------------------
    # Shooting Efficiency Analysis
    # ----------------------------------------------------------
    async def _analyze_team_shooting(
        self, team_abbr, players, team_agg
    ) -> TeamShootingProfile:
        """Analyze team shooting efficiency with regression signals."""
        fga = team_agg['total_fg_attempted']
        fta = team_agg['total_ft_attempted']
        fg3a = team_agg['total_fg3_attempted']
        fgm = team_agg['total_fg_made']
        fg3m = team_agg['total_fg3_made']
        ftm = team_agg['total_ft_made']
        pts = team_agg['total_points']

        # Live shooting metrics
        live_efg = ((fgm + 0.5 * fg3m) / max(fga, 1)) * 100
        live_ts = (pts / max(2 * (fga + 0.44 * fta), 1)) * 100
        live_fg3_rate = (fg3a / max(fga, 1)) * 100
        live_fg3_pct = (fg3m / max(fg3a, 1)) * 100
        live_ft_rate = (fta / max(fga, 1)) * 100
        live_ft_pct = (ftm / max(fta, 1)) * 100

        # Season baselines - try BallDontLie, fall back to league averages
        season_efg = LEAGUE_AVG_EFG
        season_ts = LEAGUE_AVG_TS
        season_fg3_rate = 38.0  # league average ~38%
        season_fg3_pct = 36.0   # league average ~36%
        season_ft_rate = 25.0   # league average ~25%

        # Fetch season baselines from nba_api for top minutes players
        try:
            top_players = sorted(players, key=lambda p: p.minutes_float, reverse=True)[:5]
            total_mins = sum(p.minutes_float for p in top_players)
            weighted_fg = 0
            weighted_fg3 = 0
            weighted_ft = 0
            got_data = False

            for p in top_players:
                stats = await self._get_player_season_stats(p.player_id, p.player_name)
                if stats and total_mins > 0:
                    w = p.minutes_float / total_mins
                    fg = stats.get('fg_pct', 0)
                    fg3 = stats.get('fg3_pct', 0)
                    ft = stats.get('ft_pct', 0)
                    weighted_fg += fg * w
                    weighted_fg3 += fg3 * w
                    weighted_ft += ft * w
                    got_data = True

            if got_data and weighted_fg > 0:
                season_fg3_pct = weighted_fg3 * 100
                season_ft_rate = 25.0
                season_efg = (weighted_fg + 0.5 * weighted_fg3 * (season_fg3_rate / 100)) * 100
                season_ts = season_efg * 1.08
        except Exception as e:
            logger.warning(f"Failed to fetch season shooting for {team_abbr}: {e}")

        # Regression analysis
        efg_deviation = live_efg - season_efg
        regression_factor = 1.0
        if abs(efg_deviation) > 5:
            regression_factor = 1.0 - (efg_deviation * SHOOTING_REGRESSION_RATE / 100)

        # Variance classification
        if efg_deviation > 8:
            variance_level = "extreme_hot"
        elif efg_deviation > 3:
            variance_level = "hot"
        elif efg_deviation > -3:
            variance_level = "normal"
        elif efg_deviation > -8:
            variance_level = "cold"
        else:
            variance_level = "extreme_cold"

        return TeamShootingProfile(
            team_abbr=team_abbr,
            live_efg_pct=round(live_efg, 1),
            live_ts_pct=round(live_ts, 1),
            live_fg3_rate=round(live_fg3_rate, 1),
            live_fg3_pct=round(live_fg3_pct, 1),
            live_ft_rate=round(live_ft_rate, 1),
            live_ft_pct=round(live_ft_pct, 1),
            season_efg_pct=round(season_efg, 1),
            season_ts_pct=round(season_ts, 1),
            season_fg3_rate=round(season_fg3_rate, 1),
            season_fg3_pct=round(season_fg3_pct, 1),
            season_ft_rate=round(season_ft_rate, 1),
            shooting_regression_factor=round(regression_factor, 3),
            shooting_variance_level=variance_level,
        )

    def _shooting_projection(self, home_s, away_s, scoring_rate, current_total,
                             remaining_min: float = 24.0):
        """Project remaining total from shooting efficiency analysis."""
        avg_regression = (home_s.shooting_regression_factor + away_s.shooting_regression_factor) / 2

        # Remaining points based on current scoring rate
        base_remaining = scoring_rate * remaining_min * 0.97  # Slight natural decline
        adjusted = base_remaining * avg_regression

        # High 3-point rate increases variance
        avg_fg3_rate = (home_s.live_fg3_rate + away_s.live_fg3_rate) / 2
        if avg_fg3_rate > 42:
            adjusted *= 1.02
        elif avg_fg3_rate < 30:
            adjusted *= 0.98

        return adjusted

    # ----------------------------------------------------------
    # Star Player Analysis
    # ----------------------------------------------------------
    async def _analyze_star_players(
        self, home_players, away_players, game_data, home_agg, away_agg,
        remaining_min: float = 24.0
    ) -> List[StarPlayerImpact]:
        """Identify and analyze top players' impact on team totals."""
        stars = []

        for team_label, players, team_agg in [
            (game_data.home_team_abbr, home_players, home_agg),
            (game_data.away_team_abbr, away_players, away_agg),
        ]:
            if not players:
                continue

            # Calculate usage rate for each player
            team_poss = team_agg['estimated_possessions']
            player_usage = []
            for p in players:
                if p.minutes_float < 3:
                    continue
                p_poss = p.fg_attempted + 0.44 * p.ft_attempted + p.turnovers
                usage = (p_poss / max(team_poss, 1)) * 100
                player_usage.append((p, usage))

            # Top 3 by usage
            player_usage.sort(key=lambda x: x[1], reverse=True)
            top_stars = player_usage[:3]

            for p, usage_rate in top_stars:
                # Shooting efficiency (TS%)
                ts_pct = 0.0
                if p.fg_attempted > 0 or p.ft_attempted > 0:
                    ts_denom = 2 * (p.fg_attempted + 0.44 * p.ft_attempted)
                    ts_pct = (p.points / max(ts_denom, 1)) * 100

                # Foul trouble
                foul_trouble = p.fouls >= FOUL_TROUBLE_THRESHOLD

                # Minutes risk assessment
                minutes_risk = "normal"
                if foul_trouble:
                    minutes_risk = "foul_risk"
                elif abs(game_data.score_differential) >= BLOWOUT_THRESHOLD:
                    minutes_risk = "blowout_risk"

                # Season PPG from nba_api
                season_ppg = None
                try:
                    stats = await self._get_player_season_stats(p.player_id, p.player_name)
                    if stats:
                        season_ppg = stats.get('pts', None)
                except Exception:
                    pass

                # Hot/cold indicator
                hot_cold = "normal"
                if season_ppg and season_ppg > 0 and p.minutes_float >= 8:
                    # Compare per-minute scoring rate to season
                    live_ppm = p.points / max(p.minutes_float, 1)
                    season_ppm = season_ppg / 34.0  # ~34 min avg for starters
                    ratio = live_ppm / max(season_ppm, 0.01)
                    if ratio > 1.25:
                        hot_cold = "hot"
                    elif ratio < 0.75:
                        hot_cold = "cold"

                # Project remaining minutes
                base_remaining_mins = min(remaining_min, 24.0)
                if foul_trouble:
                    base_remaining_mins *= 0.75
                elif minutes_risk == "blowout_risk":
                    if p.starter if hasattr(p, 'starter') else True:
                        base_remaining_mins *= 0.70
                    else:
                        base_remaining_mins *= 1.15
                projected_2h_mins = min(base_remaining_mins, remaining_min)

                # Project 2H points
                if p.minutes_float > 0:
                    live_ppm = p.points / p.minutes_float
                    # Regress toward season rate
                    if season_ppg and season_ppg > 0:
                        season_ppm = season_ppg / 34.0
                        regressed_ppm = live_ppm * 0.60 + season_ppm * 0.40
                    else:
                        regressed_ppm = live_ppm * 0.85  # Slight regression without data
                    projected_2h_pts = regressed_ppm * projected_2h_mins
                else:
                    projected_2h_pts = 0.0

                # Impact: how much this star shifts the team total vs baseline
                baseline_2h_pts = (season_ppg / 2) if season_ppg else projected_2h_pts
                impact = projected_2h_pts - baseline_2h_pts

                stars.append(StarPlayerImpact(
                    player_name=p.player_name,
                    player_id=p.player_id,
                    team_abbr=team_label,
                    first_half_points=p.points,
                    first_half_minutes=round(p.minutes_float, 1),
                    usage_rate=round(usage_rate, 1),
                    current_efficiency=round(ts_pct, 1),
                    foul_trouble=foul_trouble,
                    foul_count=p.fouls,
                    season_ppg=round(season_ppg, 1) if season_ppg else None,
                    projected_2h_points=round(projected_2h_pts, 1),
                    projected_2h_minutes=round(projected_2h_mins, 1),
                    hot_cold_indicator=hot_cold,
                    minutes_risk=minutes_risk,
                    impact_on_team_total=round(impact, 1),
                ))

        return stars

    def _star_utilization_projection(self, stars, scoring_rate, current_total,
                                     remaining_min: float = 24.0):
        """Project remaining total based on star player impacts."""
        base_remaining = scoring_rate * remaining_min * 0.95

        if not stars:
            return base_remaining

        # Sum star impacts
        total_impact = sum(s.impact_on_team_total for s in stars if s.impact_on_team_total != 0)

        # Stars with foul trouble drag down projection
        foul_trouble_stars = [s for s in stars if s.foul_trouble]
        if foul_trouble_stars:
            foul_penalty = len(foul_trouble_stars) * 3.5
            base_remaining -= foul_penalty

        # Hot stars boost, cold stars reduce
        hot_count = len([s for s in stars if s.hot_cold_indicator == "hot"])
        cold_count = len([s for s in stars if s.hot_cold_indicator == "cold"])
        base_remaining += hot_count * 1.5 - cold_count * 1.0

        return max(base_remaining + total_impact * 0.5, scoring_rate * remaining_min * 0.70)

    # ----------------------------------------------------------
    # Game Flow Projection
    # ----------------------------------------------------------
    def _game_flow_projection(self, game_data, scoring_rate, current_total,
                              remaining_min: float = 24.0):
        """Project remaining total based on game flow / score situation."""
        diff = abs(game_data.score_differential)
        base_remaining = scoring_rate * remaining_min

        if diff >= BLOWOUT_THRESHOLD:
            return base_remaining * 0.85
        elif diff <= CLOSE_GAME_THRESHOLD:
            return base_remaining * 1.03
        elif diff <= MODERATE_LEAD_THRESHOLD:
            return base_remaining * 0.97
        else:
            return base_remaining * 0.92

    # ----------------------------------------------------------
    # Team Ratings Projection
    # ----------------------------------------------------------
    def _team_ratings_projection(self, home_ratings, away_ratings, current_total,
                                 remaining_min: float = 24.0):
        """Project remaining points from team offensive/defensive ratings."""
        if not home_ratings or not away_ratings:
            return current_total * (remaining_min / 48.0) * 0.95

        avg_pace = (home_ratings.pace + away_ratings.pace) / 2
        remaining_fraction = remaining_min / 48.0

        home_expected_pts = (avg_pace * home_ratings.off_rating / 100) * remaining_fraction
        away_expected_pts = (avg_pace * away_ratings.off_rating / 100) * remaining_fraction

        # Adjust for opponent defense
        home_vs_def = home_expected_pts * (LEAGUE_AVG_PPP * 100 / max(away_ratings.def_rating, 80))
        away_vs_def = away_expected_pts * (LEAGUE_AVG_PPP * 100 / max(home_ratings.def_rating, 80))

        return home_vs_def + away_vs_def

    # ----------------------------------------------------------
    # Quarter Projections
    # ----------------------------------------------------------
    def _project_quarters(
        self, projected_remaining, game_data, home_ratings, away_ratings,
        home_agg, away_agg, elapsed_min: float = 24.0
    ) -> Tuple[TeamQuarterProjection, TeamQuarterProjection]:
        """Project per-team, per-quarter scores based on elapsed time."""
        diff = abs(game_data.score_differential)
        period = game_data.period

        # Determine which quarters still need projecting
        if diff >= BLOWOUT_THRESHOLD:
            q4_factor = Q4_BLOWOUT_FACTOR
        elif diff <= CLOSE_GAME_THRESHOLD:
            q4_factor = Q4_CLOSE_FACTOR
        else:
            q4_factor = Q4_MODERATE_FACTOR

        # Split remaining points into Q3/Q4 portions
        # If we're already past Q3, all remaining goes to Q4
        if period >= 4:
            # Already in Q4 or later
            combined_q3 = 0.0
            combined_q4 = projected_remaining
        elif period >= 3:
            # In Q3 - estimate how much of Q3 remains
            q3_elapsed = elapsed_min - 24.0
            q3_remaining_frac = max(0, (12.0 - q3_elapsed) / 12.0)
            q3_portion = projected_remaining * (q3_remaining_frac * Q3_PACE_FACTOR / (Q3_PACE_FACTOR + q4_factor))
            combined_q3 = q3_portion
            combined_q4 = projected_remaining - q3_portion
        else:
            # Halftime or earlier
            q3_share = Q3_PACE_FACTOR / (Q3_PACE_FACTOR + q4_factor)
            q4_share = 1.0 - q3_share
            combined_q3 = projected_remaining * q3_share
            combined_q4 = projected_remaining * q4_share

        # Split per-team by offensive rating ratio
        if home_ratings and away_ratings:
            home_off = home_ratings.off_rating
            away_off = away_ratings.off_rating
        else:
            total = home_agg['total_points'] + away_agg['total_points']
            home_off = (home_agg['total_points'] / max(total, 1)) * 228
            away_off = (away_agg['total_points'] / max(total, 1)) * 228

        home_share = home_off / max(home_off + away_off, 1)
        away_share = 1.0 - home_share

        home_q3 = combined_q3 * home_share
        home_q4 = combined_q4 * home_share
        away_q3 = combined_q3 * away_share
        away_q4 = combined_q4 * away_share

        # OT probability
        home_proj_final = game_data.home_score + home_q3 + home_q4
        away_proj_final = game_data.away_score + away_q3 + away_q4
        proj_margin = abs(home_proj_final - away_proj_final)
        ot_prob = max(0, min(25, 15 - proj_margin * 2))

        home_quarter = TeamQuarterProjection(
            team_abbr=game_data.home_team_abbr,
            q1_actual=None,
            q2_actual=None,
            q3_projected=round(home_q3, 1),
            q4_projected=round(home_q4, 1),
            ot_probability=round(ot_prob, 1),
            projected_final_score=round(home_proj_final, 1),
        )

        away_quarter = TeamQuarterProjection(
            team_abbr=game_data.away_team_abbr,
            q1_actual=None,
            q2_actual=None,
            q3_projected=round(away_q3, 1),
            q4_projected=round(away_q4, 1),
            ot_probability=round(ot_prob, 1),
            projected_final_score=round(away_proj_final, 1),
        )

        return home_quarter, away_quarter

    # ----------------------------------------------------------
    # Spread Prediction
    # ----------------------------------------------------------
    def _predict_spread(self, game_data, stars, home_ratings, away_ratings, pace):
        """Predict final point spread."""
        current_spread = game_data.home_score - game_data.away_score
        home_lead = current_spread > 0

        # Season-based expected margin from net ratings
        if home_ratings and away_ratings:
            home_net = home_ratings.off_rating - home_ratings.def_rating
            away_net = away_ratings.off_rating - away_ratings.def_rating
            rating_spread = (home_net - away_net) / 2  # Per-game expected margin
        else:
            rating_spread = 0

        # Blend live performance with season expectations
        # Weight live at 60% since we have half a game of data
        projected_spread = current_spread * 0.60 + rating_spread * 0.40

        # Star performance differential
        home_star_impact = sum(
            s.impact_on_team_total for s in stars
            if s.team_abbr == game_data.home_team_abbr
        )
        away_star_impact = sum(
            s.impact_on_team_total for s in stars
            if s.team_abbr == game_data.away_team_abbr
        )
        star_diff = home_star_impact - away_star_impact
        projected_spread += star_diff * 0.3

        # Momentum from pace
        momentum = "neutral"
        if current_spread > 5 and pace.pace_trend == "accelerating":
            momentum = "home" if home_lead else "away"
        elif current_spread < -5 and pace.pace_trend == "accelerating":
            momentum = "away" if not home_lead else "home"

        # Probabilities
        abs_proj = abs(projected_spread)
        close_game_prob = max(5, min(60, 45 - abs_proj * 3))
        blowout_prob = max(2, min(50, abs_proj * 2.5 - 10))

        # Confidence in spread prediction
        spread_conf = 50.0
        if abs(current_spread) > 15:
            spread_conf += 15  # Large leads more predictable
        if home_ratings and away_ratings:
            spread_conf += 10  # Have season data
        spread_conf = max(20, min(85, spread_conf))

        return SpreadPrediction(
            current_spread=current_spread,
            home_lead=home_lead,
            projected_final_spread=round(projected_spread, 1),
            spread_confidence=round(spread_conf, 1),
            star_performance_differential=round(star_diff, 1),
            momentum_indicator=momentum,
            close_game_probability=round(close_game_prob, 1),
            blowout_probability=round(blowout_prob, 1),
        )

    # ----------------------------------------------------------
    # Over/Under
    # ----------------------------------------------------------
    def _calculate_variance(self, pace, home_s, away_s) -> float:
        """Calculate projection variance (uncertainty range)."""
        base_variance = 4.0  # Base +/- 4 points

        # Higher pace deviation = more uncertainty
        pace_mult = 1.0 + abs(pace.pace_deviation) * 0.02

        # Extreme shooting = more uncertainty (regression unpredictable)
        shooting_mult = 1.0
        for s in [home_s, away_s]:
            if s.shooting_variance_level in ("extreme_hot", "extreme_cold"):
                shooting_mult += 0.15
            elif s.shooting_variance_level in ("hot", "cold"):
                shooting_mult += 0.08

        # High 3pt rate = more variance
        avg_fg3_rate = (home_s.live_fg3_rate + away_s.live_fg3_rate) / 2
        three_mult = 1.0 + max(0, (avg_fg3_rate - 35) * 0.01)

        return base_variance * pace_mult * shooting_mult * three_mult

    def _calculate_over_under(
        self, projected_total, variance, reference_line,
        season_avg_total, home_s, away_s, pace
    ) -> OverUnderRecommendation:
        """Calculate over/under recommendation with edge."""
        range_low = projected_total - variance
        range_high = projected_total + variance

        # Reference line: user-provided or estimated from season averages
        line = reference_line if reference_line else round(season_avg_total * 2) / 2

        edge = projected_total - line
        edge_pct = (edge / max(line, 1)) * 100

        # Confidence based on how much data supports the projection
        confidence = 50.0
        # Strong pace data
        if abs(pace.pace_deviation) < 5:
            confidence += 10  # Predictable pace
        # Normal shooting (less regression risk)
        for s in [home_s, away_s]:
            if s.shooting_variance_level == "normal":
                confidence += 5

        # Edge magnitude boosts confidence
        if abs(edge) > 4:
            confidence += 10
        elif abs(edge) > 2:
            confidence += 5

        confidence = max(20, min(90, confidence))

        # Recommendation
        if edge > 4 and confidence >= 65:
            rec = "strong_over"
        elif edge > 1.5 and confidence >= 50:
            rec = "lean_over"
        elif edge < -4 and confidence >= 65:
            rec = "strong_under"
        elif edge < -1.5 and confidence >= 50:
            rec = "lean_under"
        else:
            rec = "neutral"

        return OverUnderRecommendation(
            projected_total=round(projected_total, 1),
            projected_range_low=round(range_low, 1),
            projected_range_high=round(range_high, 1),
            reference_line=line,
            edge=round(edge, 1),
            edge_pct=round(edge_pct, 1),
            recommendation=rec,
            confidence=round(confidence, 1),
        )

    # ----------------------------------------------------------
    # Overall Confidence
    # ----------------------------------------------------------
    def _calculate_total_confidence(
        self, pace, home_s, away_s, stars, blowout_risk, is_close
    ) -> float:
        """Calculate overall projection confidence score (0-100)."""
        confidence = 50.0

        # Pace stability boosts confidence
        if abs(pace.pace_deviation) < 5:
            confidence += 12
        elif abs(pace.pace_deviation) < 10:
            confidence += 6
        else:
            confidence -= 8

        # Normal shooting is more predictable
        for s in [home_s, away_s]:
            if s.shooting_variance_level == "normal":
                confidence += 5
            elif s.shooting_variance_level in ("extreme_hot", "extreme_cold"):
                confidence -= 6

        # Star player health
        foul_trouble_count = sum(1 for s in stars if s.foul_trouble)
        if foul_trouble_count > 0:
            confidence -= foul_trouble_count * 4

        # Blowout reduces total prediction accuracy
        if blowout_risk:
            confidence -= 12

        # Close game = more variance in Q4
        if is_close:
            confidence -= 3

        return max(15, min(95, confidence))

    # ----------------------------------------------------------
    # Notes Generation
    # ----------------------------------------------------------
    def _generate_notes(
        self, pace, home_s, away_s, stars, blowout_risk, game_data
    ) -> List[str]:
        """Generate human-readable analysis notes."""
        notes = []

        # Pace notes
        if pace.pace_deviation > 10:
            notes.append(
                f"Game is running {pace.pace_deviation:.0f}% faster than expected "
                f"({pace.possessions_per_48_live:.0f} poss/48 vs {pace.matchup_expected_pace:.0f} expected). "
                f"Expect some regression in 2H."
            )
        elif pace.pace_deviation < -10:
            notes.append(
                f"Game is running {abs(pace.pace_deviation):.0f}% slower than expected. "
                f"Could pick up if trailing team pushes pace."
            )

        if pace.pace_trend == "accelerating":
            notes.append("Pace is accelerating - Q2 was faster than Q1.")
        elif pace.pace_trend == "decelerating":
            notes.append("Pace is decelerating - game has slowed since Q1.")

        # Shooting notes
        for s in [home_s, away_s]:
            if s.shooting_variance_level == "extreme_hot":
                notes.append(
                    f"{s.team_abbr} shooting {s.live_efg_pct:.1f}% eFG (season: {s.season_efg_pct:.1f}%). "
                    f"Extreme hot shooting - heavy regression expected."
                )
            elif s.shooting_variance_level == "extreme_cold":
                notes.append(
                    f"{s.team_abbr} shooting only {s.live_efg_pct:.1f}% eFG (season: {s.season_efg_pct:.1f}%). "
                    f"Cold shooting likely to recover."
                )

        # Star notes
        hot_stars = [s for s in stars if s.hot_cold_indicator == "hot"]
        if hot_stars:
            names = ", ".join(s.player_name for s in hot_stars[:2])
            notes.append(f"Star(s) running hot: {names}. Factor in regression.")

        foul_stars = [s for s in stars if s.foul_trouble]
        if foul_stars:
            names = ", ".join(f"{s.player_name} ({s.foul_count}F)" for s in foul_stars)
            notes.append(f"Foul trouble: {names}. Minutes may be limited in 2H.")

        if blowout_risk:
            notes.append(
                f"Blowout alert: {game_data.score_differential} pt differential. "
                f"Starters may rest, reducing total."
            )

        return notes
