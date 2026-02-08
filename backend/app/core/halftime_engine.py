"""
Halftime Analysis Engine

Analyzes live NBA games at halftime to suggest second-half prop bets.
Uses multiple weighting factors for projection and confidence scoring.

Enhanced with:
- Shooting efficiency (FG%, 3P%, FT%, eFG%, TS%)
- Team offensive/defensive ratings
- Opponent defensive rank by stat type
- Plus/minus impact
- Assist-to-turnover ratio
"""
import logging
from typing import List, Dict, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import asyncio

from app.services.live_data_client import (
    LiveDataClient, LiveGameData, LivePlayerStats, live_data_client
)
from app.config import settings

logger = logging.getLogger(__name__)

# Configuration constants
BLOWOUT_THRESHOLD = getattr(settings, 'BLOWOUT_THRESHOLD', 20)
FOUL_TROUBLE_THRESHOLD = getattr(settings, 'FOUL_TROUBLE_THRESHOLD', 3)
LEAGUE_AVG_PACE = 100.0  # League average possessions per 48 min
LEAGUE_AVG_TOTAL = 225.0  # League average combined score
LEAGUE_AVG_OFF_RTG = 114.0  # League average offensive rating
LEAGUE_AVG_DEF_RTG = 114.0  # League average defensive rating

# Enhanced projection weights (must sum to 1.0)
PROJECTION_WEIGHTS = {
    'first_half_trend': 0.18,
    'shooting_efficiency': 0.18,  # INCREASED: shooting impact
    'shot_volume': 0.15,  # NEW: total shots attempted
    'opponent_defense': 0.14,  # INCREASED: opponent defensive rating
    'score_situation': 0.10,  # INCREASED: blowout/close game impact
    'historical_2h_avg': 0.08,
    'pace_adjustment': 0.07,
    'plus_minus_factor': 0.05,
    'utilization_rate': 0.03,
    'fatigue_factor': 0.02,
}

# Q3 adjustment factors
Q3_PACE_FACTOR = 0.92  # Q3 typically 8% slower than Q1/Q2
PACE_SUSTAINABILITY = 0.95

# Stat type to defensive category mapping
STAT_DEF_CATEGORY = {
    'points': 'PTS',
    'rebounds': 'REB',
    'assists': 'AST',
    'steals': 'STL',
    'blocks': 'BLK',
    'threes': '3PM',
    '3pt': '3PM',
}


@dataclass
class ShootingMetrics:
    """Detailed shooting efficiency metrics."""
    fg_pct: float = 0.0
    fg3_pct: float = 0.0
    ft_pct: float = 0.0
    efg_pct: float = 0.0  # Effective FG%
    ts_pct: float = 0.0   # True Shooting %
    points_per_shot: float = 0.0

    @property
    def efficiency_rating(self) -> str:
        """Get efficiency rating category."""
        if self.ts_pct >= 65:
            return "elite"
        elif self.ts_pct >= 58:
            return "excellent"
        elif self.ts_pct >= 52:
            return "good"
        elif self.ts_pct >= 45:
            return "average"
        else:
            return "poor"


@dataclass
class TeamRatings:
    """Team offensive and defensive ratings."""
    team_id: int
    team_abbr: str
    off_rating: float = LEAGUE_AVG_OFF_RTG
    def_rating: float = LEAGUE_AVG_DEF_RTG
    pace: float = LEAGUE_AVG_PACE
    # Defensive ranks by stat (1 = best defense, 30 = worst)
    def_rank_pts: int = 15
    def_rank_reb: int = 15
    def_rank_ast: int = 15
    def_rank_3pm: int = 15

    @property
    def net_rating(self) -> float:
        return self.off_rating - self.def_rating


@dataclass
class PlayerProjection:
    """Projected second-half and final stats for a player."""
    player_id: int
    player_name: str
    team_abbreviation: str
    prop_type: str
    prop_line: float

    first_half_value: float
    first_half_minutes: float

    projected_second_half: float
    projected_final: float

    confidence_score: float
    recommendation: str

    factors: Dict[str, float]

    foul_trouble: bool
    blowout_warning: bool
    pace_factor: float
    utilization_rate: float
    fatigue_factor: float
    minutes_projection: float

    # Enhanced metrics
    shooting_metrics: Optional[Dict[str, float]] = None
    assist_to_turnover: Optional[float] = None
    opponent_def_rank: Optional[int] = None
    opponent_def_rating: Optional[float] = None
    team_off_rating: Optional[float] = None

    season_average: Optional[float] = None
    second_half_historical_avg: Optional[float] = None
    plus_minus: int = 0
    shooting_efficiency: Optional[float] = None


@dataclass
class GameTotalProjection:
    """Projected game totals."""
    game_id: str
    home_team: str
    away_team: str
    current_total: int
    first_half_total: int
    score_differential: int

    first_half_pace: float
    pace_rating: str
    league_avg_pace_comparison: float

    projected_second_half_total: float
    projected_final_total: float
    projected_q3_total: float
    projected_q4_total: float

    total_confidence: float
    blowout_risk: bool
    pace_sustainability: float

    # Enhanced metrics
    home_off_rating: Optional[float] = None
    home_def_rating: Optional[float] = None
    away_off_rating: Optional[float] = None
    away_def_rating: Optional[float] = None


class HalftimeAnalysisEngine:
    """Engine for analyzing live NBA games at halftime."""

    def __init__(self, live_client: Optional[LiveDataClient] = None):
        self.live_client = live_client or live_data_client
        self._team_ratings_cache: Dict[int, TeamRatings] = {}

    def _get_stat_value(self, stats: LivePlayerStats, prop_type: str) -> float:
        """Extract the relevant stat value based on prop type."""
        stat_mapping = {
            'points': stats.points,
            'rebounds': stats.rebounds,
            'assists': stats.assists,
            'steals': stats.steals,
            'blocks': stats.blocks,
            'threes': stats.fg3_made,
            '3pt': stats.fg3_made,
            'turnovers': stats.turnovers,
            'pts+reb': stats.points + stats.rebounds,
            'pts+ast': stats.points + stats.assists,
            'reb+ast': stats.rebounds + stats.assists,
            'pts+reb+ast': stats.points + stats.rebounds + stats.assists,
        }
        return float(stat_mapping.get(prop_type.lower(), 0))

    def _calculate_shooting_metrics(self, stats: LivePlayerStats) -> ShootingMetrics:
        """
        Calculate comprehensive shooting efficiency metrics.

        - FG%: Field Goal Percentage
        - 3P%: Three Point Percentage
        - FT%: Free Throw Percentage
        - eFG%: Effective Field Goal % = (FGM + 0.5 * 3PM) / FGA
        - TS%: True Shooting % = PTS / (2 * (FGA + 0.44 * FTA))
        - Points Per Shot: PTS / FGA
        """
        fg_pct = (stats.fg_made / stats.fg_attempted * 100) if stats.fg_attempted > 0 else 0
        fg3_pct = (stats.fg3_made / stats.fg3_attempted * 100) if stats.fg3_attempted > 0 else 0
        ft_pct = (stats.ft_made / stats.ft_attempted * 100) if stats.ft_attempted > 0 else 0

        # Effective FG%
        efg_pct = ((stats.fg_made + 0.5 * stats.fg3_made) / stats.fg_attempted * 100) if stats.fg_attempted > 0 else 0

        # True Shooting %
        tsa = stats.fg_attempted + 0.44 * stats.ft_attempted  # True Shooting Attempts
        ts_pct = (stats.points / (2 * tsa) * 100) if tsa > 0 else 0

        # Points per shot
        pps = stats.points / stats.fg_attempted if stats.fg_attempted > 0 else 0

        return ShootingMetrics(
            fg_pct=round(fg_pct, 1),
            fg3_pct=round(fg3_pct, 1),
            ft_pct=round(ft_pct, 1),
            efg_pct=round(efg_pct, 1),
            ts_pct=round(ts_pct, 1),
            points_per_shot=round(pps, 2)
        )

    def _calculate_assist_to_turnover(self, stats: LivePlayerStats) -> Optional[float]:
        """Calculate assist to turnover ratio."""
        if stats.turnovers == 0:
            return float(stats.assists) if stats.assists > 0 else None
        return round(stats.assists / stats.turnovers, 2)

    def _calculate_utilization_rate(self, stats: LivePlayerStats, team_stats: List[LivePlayerStats]) -> float:
        """
        Calculate player's utilization rate in first half.
        Based on FGA, FTA, and TOV relative to team totals.
        """
        if not team_stats:
            return 0.0

        team_fga = sum(p.fg_attempted for p in team_stats)
        team_fta = sum(p.ft_attempted for p in team_stats)
        team_tov = sum(p.turnovers for p in team_stats)

        team_possessions = team_fga + 0.44 * team_fta + team_tov
        if team_possessions == 0:
            return 0.0

        player_possessions = stats.fg_attempted + 0.44 * stats.ft_attempted + stats.turnovers
        return (player_possessions / team_possessions) * 100

    def _calculate_pace_factor(
        self,
        game_data: LiveGameData,
        first_half_minutes: float = 24.0
    ) -> float:
        """Calculate game pace relative to league average."""
        total_score = game_data.total_score
        if first_half_minutes <= 0:
            return 1.0

        points_per_min = total_score / first_half_minutes
        expected_ppm = LEAGUE_AVG_TOTAL / 48.0

        return points_per_min / expected_ppm if expected_ppm > 0 else 1.0

    def _calculate_plus_minus_factor(self, plus_minus: int, minutes: float) -> float:
        """
        Calculate plus/minus impact factor.

        Positive plus/minus suggests player contributes to winning,
        which often correlates with more opportunities.

        Returns multiplier (1.0 = neutral, >1 = positive impact, <1 = negative)
        """
        if minutes <= 0:
            return 1.0

        # Per-minute plus/minus
        pm_per_min = plus_minus / minutes

        # Convert to factor: +5 per min = 1.10x, -5 per min = 0.90x
        factor = 1.0 + (pm_per_min * 0.02)

        # Clamp between 0.85 and 1.15
        return max(0.85, min(1.15, factor))

    def _get_opponent_def_adjustment(
        self,
        opponent_def_rank: int,
        prop_type: str
    ) -> float:
        """
        Calculate adjustment factor based on opponent's defensive rank.

        Rank 1-10: Strong defense = reduce projection
        Rank 11-20: Average defense = neutral
        Rank 21-30: Weak defense = increase projection

        Returns multiplier (1.0 = neutral)
        """
        if opponent_def_rank <= 5:
            return 0.90  # Elite defense
        elif opponent_def_rank <= 10:
            return 0.95  # Good defense
        elif opponent_def_rank <= 20:
            return 1.0   # Average
        elif opponent_def_rank <= 25:
            return 1.05  # Below average
        else:
            return 1.10  # Poor defense

    def _get_shooting_efficiency_factor(
        self,
        shooting: ShootingMetrics,
        prop_type: str
    ) -> float:
        """
        Calculate shooting efficiency factor for projection.

        Hot shooting = boost projection
        Cold shooting = reduce projection (regression expected)
        """
        if prop_type == 'points':
            # For points, use True Shooting %
            if shooting.ts_pct >= 70:
                return 1.12  # Very hot, but expect some regression
            elif shooting.ts_pct >= 60:
                return 1.08
            elif shooting.ts_pct >= 55:
                return 1.04
            elif shooting.ts_pct >= 45:
                return 1.0
            elif shooting.ts_pct >= 35:
                return 0.95  # Cold, might heat up
            else:
                return 0.90
        elif prop_type == 'threes' or prop_type == '3pt':
            # For threes, use 3P%
            if shooting.fg3_pct >= 50:
                return 1.10
            elif shooting.fg3_pct >= 40:
                return 1.05
            elif shooting.fg3_pct >= 33:
                return 1.0
            elif shooting.fg3_pct >= 20:
                return 0.95
            else:
                return 0.90
        else:
            # For non-shooting stats, slight boost for efficient players
            if shooting.ts_pct >= 55:
                return 1.02
            return 1.0

    async def _get_team_ratings(self, team_id: int, team_abbr: str) -> TeamRatings:
        """
        Fetch team offensive/defensive ratings from nba_api.
        Uses cache to avoid repeated API calls.
        Short timeout to prevent hanging on cloud servers.
        """
        if team_id in self._team_ratings_cache:
            return self._team_ratings_cache[team_id]

        ratings = TeamRatings(team_id=team_id, team_abbr=team_abbr)
        api_timeout = 10  # seconds

        try:
            from nba_api.stats.endpoints import leaguedashteamstats

            loop = asyncio.get_event_loop()

            # Get team stats with timeout
            stats = await asyncio.wait_for(
                loop.run_in_executor(
                    None,
                    lambda: leaguedashteamstats.LeagueDashTeamStats(
                        season='2024-25',
                        measure_type_detailed_defense='Advanced',
                        timeout=api_timeout
                    )
                ),
                timeout=api_timeout + 2
            )

            df = stats.get_data_frames()[0]
            team_row = df[df['TEAM_ID'] == team_id]

            if not team_row.empty:
                ratings.off_rating = float(team_row['OFF_RATING'].iloc[0])
                ratings.def_rating = float(team_row['DEF_RATING'].iloc[0])
                ratings.pace = float(team_row['PACE'].iloc[0]) if 'PACE' in team_row else LEAGUE_AVG_PACE

            # Get defensive rankings by opponent stats
            def_stats = await asyncio.wait_for(
                loop.run_in_executor(
                    None,
                    lambda: leaguedashteamstats.LeagueDashTeamStats(
                        season='2024-25',
                        measure_type_detailed_defense='Opponent',
                        timeout=api_timeout
                    )
                ),
                timeout=api_timeout + 2
            )

            def_df = def_stats.get_data_frames()[0]

            # Sort by opponent stats to get rankings
            def_df_sorted = def_df.sort_values('OPP_PTS', ascending=True)
            def_df_sorted['PTS_RANK'] = range(1, len(def_df_sorted) + 1)

            def_df_sorted = def_df.sort_values('OPP_REB', ascending=True)
            def_df_sorted['REB_RANK'] = range(1, len(def_df_sorted) + 1)

            def_df_sorted = def_df.sort_values('OPP_AST', ascending=True)
            def_df_sorted['AST_RANK'] = range(1, len(def_df_sorted) + 1)

            def_df_sorted = def_df.sort_values('OPP_FG3M', ascending=True)
            def_df_sorted['3PM_RANK'] = range(1, len(def_df_sorted) + 1)

            team_def = def_df_sorted[def_df_sorted['TEAM_ID'] == team_id]
            if not team_def.empty:
                ratings.def_rank_pts = int(team_def['PTS_RANK'].iloc[0]) if 'PTS_RANK' in team_def else 15
                ratings.def_rank_reb = int(team_def['REB_RANK'].iloc[0]) if 'REB_RANK' in team_def else 15
                ratings.def_rank_ast = int(team_def['AST_RANK'].iloc[0]) if 'AST_RANK' in team_def else 15
                ratings.def_rank_3pm = int(team_def['3PM_RANK'].iloc[0]) if '3PM_RANK' in team_def else 15

        except asyncio.TimeoutError:
            logger.warning(f"Timeout fetching team ratings for {team_abbr} - using defaults")
        except Exception as e:
            logger.warning(f"Could not fetch team ratings for {team_abbr}: {e}")

        self._team_ratings_cache[team_id] = ratings
        return ratings

    def _detect_foul_trouble(self, fouls: int, minutes: float) -> bool:
        """Check if player is in foul trouble."""
        if fouls >= FOUL_TROUBLE_THRESHOLD:
            return True
        if minutes > 0 and fouls / minutes > 0.125:
            return True
        return False

    def _detect_blowout(self, score_diff: int) -> bool:
        """Check if game is a potential blowout."""
        return abs(score_diff) >= BLOWOUT_THRESHOLD

    def _get_fatigue_factor(self, is_back_to_back: bool, rest_days: int = 1) -> float:
        """Calculate fatigue adjustment factor."""
        if is_back_to_back:
            return 0.92
        if rest_days >= 3:
            return 1.02
        return 1.0

    def _calculate_minutes_projection(
        self,
        first_half_minutes: float,
        foul_trouble: bool,
        blowout_warning: bool,
        is_starter: bool
    ) -> float:
        """Project second-half minutes based on various factors."""
        base_projection = first_half_minutes

        if foul_trouble:
            base_projection *= 0.75

        if blowout_warning:
            if is_starter:
                base_projection *= 0.70
            else:
                base_projection *= 1.15

        return min(base_projection, 24.0)

    def _calculate_shot_volume_factor(
        self,
        fg_attempted: int,
        ft_attempted: int,
        minutes: float,
        prop_type: str
    ) -> float:
        """
        Calculate shot volume factor - high volume shooters tend to maintain production.

        More shots = more opportunities = higher projection multiplier for points.
        For non-scoring stats, high volume indicates engagement.
        """
        if minutes <= 0:
            return 1.0

        # Shots per minute
        total_shots = fg_attempted + (ft_attempted * 0.44)  # Weight FTs less
        shots_per_min = total_shots / minutes

        if prop_type == 'points':
            # For points, shot volume is crucial
            if shots_per_min >= 1.0:  # 12+ shots per half pace
                return 1.15
            elif shots_per_min >= 0.75:  # 9+ shots per half pace
                return 1.10
            elif shots_per_min >= 0.5:  # 6+ shots per half pace
                return 1.05
            elif shots_per_min >= 0.3:
                return 1.0
            else:
                return 0.90  # Low volume = fewer opportunities
        else:
            # For other stats, volume indicates general engagement
            if shots_per_min >= 0.75:
                return 1.05
            elif shots_per_min >= 0.4:
                return 1.0
            else:
                return 0.95

        return 1.0

    def _calculate_second_half_projection(
        self,
        first_half_value: float,
        first_half_minutes: float,
        projected_minutes: float,
        pace_factor: float,
        utilization_rate: float,
        fatigue_factor: float,
        historical_2h_avg: Optional[float],
        blowout_warning: bool,
        shooting_metrics: ShootingMetrics,
        plus_minus: int,
        opponent_def_rank: int,
        prop_type: str,
        fg_attempted: int = 0,
        ft_attempted: int = 0,
        score_differential: int = 0
    ) -> Tuple[float, Dict[str, float]]:
        """
        Calculate projected second-half value using enhanced weighted factors.

        Returns: (projection, component_breakdown)
        """
        if first_half_minutes <= 0:
            return (historical_2h_avg if historical_2h_avg else 0.0, {})

        first_half_rate = first_half_value / first_half_minutes
        components = {}

        # 1. First half trend (extrapolate current rate)
        components['first_half_trend'] = first_half_rate * projected_minutes

        # 2. Shooting efficiency factor - INCREASED WEIGHT
        shooting_factor = self._get_shooting_efficiency_factor(shooting_metrics, prop_type)
        components['shooting_efficiency'] = components['first_half_trend'] * shooting_factor

        # 3. Shot volume factor - NEW HEAVY WEIGHT
        shot_volume_factor = self._calculate_shot_volume_factor(
            fg_attempted, ft_attempted, first_half_minutes, prop_type
        )
        components['shot_volume'] = components['first_half_trend'] * shot_volume_factor

        # 4. Opponent defense factor - INCREASED WEIGHT
        opp_def_factor = self._get_opponent_def_adjustment(opponent_def_rank, prop_type)
        components['opponent_defense'] = components['first_half_trend'] * opp_def_factor

        # 5. Score situation - INCREASED WEIGHT
        # More nuanced: close games = more minutes for stars, blowouts = garbage time
        if blowout_warning:
            components['score_situation'] = components['first_half_trend'] * 0.75
        elif abs(score_differential) <= 5:
            # Very close game - stars play heavy minutes
            components['score_situation'] = components['first_half_trend'] * 1.08
        elif abs(score_differential) <= 10:
            components['score_situation'] = components['first_half_trend'] * 1.03
        else:
            components['score_situation'] = components['first_half_trend']

        # 6. Historical second half average
        if historical_2h_avg:
            components['historical_2h_avg'] = historical_2h_avg * (projected_minutes / 24.0)
        else:
            components['historical_2h_avg'] = components['first_half_trend']

        # 7. Pace adjustment
        components['pace_adjustment'] = components['first_half_trend'] * pace_factor * PACE_SUSTAINABILITY

        # 8. Plus/minus factor
        pm_factor = self._calculate_plus_minus_factor(plus_minus, first_half_minutes)
        components['plus_minus_factor'] = components['first_half_trend'] * pm_factor

        # 9. Utilization adjustment
        utilization_multiplier = 1.0
        if utilization_rate > 30:
            utilization_multiplier = 0.90 + (30 - utilization_rate) * 0.01
        elif utilization_rate < 15:
            utilization_multiplier = 1.05
        components['utilization_rate'] = components['first_half_trend'] * utilization_multiplier

        # 10. Fatigue factor
        components['fatigue_factor'] = components['first_half_trend'] * fatigue_factor

        # Weighted combination
        projected = sum(
            components[key] * PROJECTION_WEIGHTS[key]
            for key in PROJECTION_WEIGHTS
        )

        return max(0, projected), components

    def _calculate_confidence_score(
        self,
        projected_final: float,
        prop_line: float,
        first_half_value: float,
        historical_consistency: float,
        shooting_metrics: ShootingMetrics,
        foul_trouble: bool,
        blowout_warning: bool,
        utilization_rate: float,
        plus_minus: int,
        opponent_def_rank: int,
        assist_to_turnover: Optional[float]
    ) -> Tuple[float, str]:
        """
        Calculate confidence score (0-100) and recommendation.
        Enhanced with shooting, plus/minus, and opponent factors.
        """
        confidence = 50.0

        # 1. Distance from line (25% weight)
        distance = projected_final - prop_line
        distance_pct = (distance / prop_line) * 100 if prop_line > 0 else 0

        if abs(distance_pct) > 20:
            confidence += 20 * (1 if distance > 0 else -1)
        elif abs(distance_pct) > 10:
            confidence += 12 * (1 if distance > 0 else -1)
        elif abs(distance_pct) > 5:
            confidence += 6 * (1 if distance > 0 else -1)

        # 2. First half progress (20% weight)
        progress_pct = (first_half_value / prop_line) * 100 if prop_line > 0 else 0

        if progress_pct >= 60:
            confidence += 18
        elif progress_pct >= 50:
            confidence += 10
        elif progress_pct >= 40:
            confidence += 4
        elif progress_pct < 30:
            confidence -= 8

        # 3. Shooting efficiency (15% weight) - NEW enhanced
        if shooting_metrics.ts_pct >= 65:
            confidence += 10
        elif shooting_metrics.ts_pct >= 55:
            confidence += 6
        elif shooting_metrics.ts_pct >= 45:
            confidence += 2
        elif shooting_metrics.ts_pct < 35:
            confidence -= 6

        # 4. Plus/minus impact (10% weight) - NEW
        if plus_minus >= 10:
            confidence += 8
        elif plus_minus >= 5:
            confidence += 4
        elif plus_minus <= -10:
            confidence -= 6
        elif plus_minus <= -5:
            confidence -= 3

        # 5. Opponent defense (10% weight) - NEW
        if opponent_def_rank >= 25:  # Weak defense
            confidence += 6
        elif opponent_def_rank >= 20:
            confidence += 3
        elif opponent_def_rank <= 5:  # Strong defense
            confidence -= 6
        elif opponent_def_rank <= 10:
            confidence -= 3

        # 6. Assist-to-turnover ratio (5% weight) - NEW
        if assist_to_turnover is not None:
            if assist_to_turnover >= 3.0:
                confidence += 4
            elif assist_to_turnover >= 2.0:
                confidence += 2
            elif assist_to_turnover < 1.0:
                confidence -= 2

        # 7. Historical consistency (5% weight)
        if historical_consistency > 70:
            confidence += 4
        elif historical_consistency < 30:
            confidence -= 4

        # 8. Penalties
        if foul_trouble:
            confidence -= 10

        if blowout_warning:
            confidence -= 12

        if utilization_rate > 35:
            confidence -= 4

        # Clip to 0-100
        confidence = max(0, min(100, confidence))

        # Determine recommendation
        if distance > 0:  # Over looks good
            if confidence >= 75:
                recommendation = "strong_bet"
            elif confidence >= 65:
                recommendation = "bet"
            elif confidence >= 55:
                recommendation = "lean"
            elif confidence >= 45:
                recommendation = "neutral"
            else:
                recommendation = "avoid"
        else:  # Under looks better
            if confidence <= 25:
                recommendation = "strong_avoid"
            elif confidence <= 35:
                recommendation = "avoid"
            elif confidence <= 45:
                recommendation = "neutral"
            else:
                recommendation = "lean"

        return confidence, recommendation

    def _get_opponent_def_rank_for_stat(self, opp_ratings: TeamRatings, prop_type: str) -> int:
        """Get opponent's defensive rank for a specific stat type."""
        if prop_type == 'points':
            return opp_ratings.def_rank_pts
        elif prop_type == 'rebounds':
            return opp_ratings.def_rank_reb
        elif prop_type == 'assists':
            return opp_ratings.def_rank_ast
        elif prop_type in ['threes', '3pt']:
            return opp_ratings.def_rank_3pm
        return 15  # Default to average

    async def analyze_halftime_player(
        self,
        live_stats: LivePlayerStats,
        prop_line: float,
        prop_type: str,
        game_data: LiveGameData,
        team_stats: List[LivePlayerStats],
        opponent_team_id: int,
        opponent_abbr: str,
        team_ratings: Optional[TeamRatings] = None,
        is_back_to_back: bool = False
    ) -> PlayerProjection:
        """
        Analyze a player's halftime stats and project second-half performance.
        Enhanced with shooting metrics, team ratings, and opponent defense.
        """
        first_half_value = self._get_stat_value(live_stats, prop_type)
        first_half_minutes = live_stats.minutes_float

        # Calculate all factors
        shooting_metrics = self._calculate_shooting_metrics(live_stats)
        assist_to_turnover = self._calculate_assist_to_turnover(live_stats)
        utilization_rate = self._calculate_utilization_rate(live_stats, team_stats)
        pace_factor = self._calculate_pace_factor(game_data)
        foul_trouble = self._detect_foul_trouble(live_stats.fouls, first_half_minutes)
        blowout_warning = self._detect_blowout(game_data.score_differential)
        fatigue_factor = self._get_fatigue_factor(is_back_to_back)

        # Get opponent defensive ratings
        opp_ratings = await self._get_team_ratings(opponent_team_id, opponent_abbr)
        opponent_def_rank = self._get_opponent_def_rank_for_stat(opp_ratings, prop_type)

        # Get historical data
        historical_2h_avg = None
        season_avg = None
        try:
            season_stats = await self.live_client.get_player_season_stats(live_stats.player_id)
            if season_stats:
                if prop_type == 'points':
                    season_avg = season_stats.get('avg_points')
                    historical_2h_avg = season_stats.get('second_half_avg_points')
                elif prop_type == 'rebounds':
                    season_avg = season_stats.get('avg_rebounds')
                    historical_2h_avg = season_stats.get('second_half_avg_rebounds')
                elif prop_type == 'assists':
                    season_avg = season_stats.get('avg_assists')
                    historical_2h_avg = season_stats.get('second_half_avg_assists')
        except Exception as e:
            logger.warning(f"Could not fetch historical stats for {live_stats.player_name}: {e}")

        # Project minutes
        minutes_projection = self._calculate_minutes_projection(
            first_half_minutes,
            foul_trouble,
            blowout_warning,
            live_stats.starter
        )

        # Calculate enhanced second-half projection
        projected_second_half, projection_components = self._calculate_second_half_projection(
            first_half_value=first_half_value,
            first_half_minutes=first_half_minutes,
            projected_minutes=minutes_projection,
            pace_factor=pace_factor,
            utilization_rate=utilization_rate,
            fatigue_factor=fatigue_factor,
            historical_2h_avg=historical_2h_avg,
            blowout_warning=blowout_warning,
            shooting_metrics=shooting_metrics,
            plus_minus=live_stats.plus_minus,
            opponent_def_rank=opponent_def_rank,
            prop_type=prop_type,
            fg_attempted=live_stats.fg_attempted,
            ft_attempted=live_stats.ft_attempted,
            score_differential=game_data.score_differential
        )

        projected_final = first_half_value + projected_second_half

        # Calculate enhanced confidence score
        historical_consistency = 50.0
        confidence, recommendation = self._calculate_confidence_score(
            projected_final=projected_final,
            prop_line=prop_line,
            first_half_value=first_half_value,
            historical_consistency=historical_consistency,
            shooting_metrics=shooting_metrics,
            foul_trouble=foul_trouble,
            blowout_warning=blowout_warning,
            utilization_rate=utilization_rate,
            plus_minus=live_stats.plus_minus,
            opponent_def_rank=opponent_def_rank,
            assist_to_turnover=assist_to_turnover
        )

        # Build enhanced factors breakdown
        shot_volume_factor = self._calculate_shot_volume_factor(
            live_stats.fg_attempted, live_stats.ft_attempted, first_half_minutes, prop_type
        )
        factors = {
            'first_half_progress': (first_half_value / prop_line * 100) if prop_line > 0 else 0,
            'shots_attempted': live_stats.fg_attempted,
            'shot_volume_factor': shot_volume_factor,
            'shooting_ts_pct': shooting_metrics.ts_pct,
            'shooting_efg_pct': shooting_metrics.efg_pct,
            'opponent_def_rank': opponent_def_rank,
            'opponent_def_adjustment': self._get_opponent_def_adjustment(opponent_def_rank, prop_type),
            'score_differential': game_data.score_differential,
            'pace_factor': pace_factor,
            'plus_minus': live_stats.plus_minus,
            'plus_minus_factor': self._calculate_plus_minus_factor(live_stats.plus_minus, first_half_minutes),
            'utilization_rate': utilization_rate,
            'fatigue_factor': fatigue_factor,
            'assist_to_turnover': assist_to_turnover or 0,
            'foul_trouble_penalty': -10 if foul_trouble else 0,
            'blowout_penalty': -12 if blowout_warning else 0,
        }

        return PlayerProjection(
            player_id=live_stats.player_id,
            player_name=live_stats.player_name,
            team_abbreviation=live_stats.team_abbreviation,
            prop_type=prop_type,
            prop_line=prop_line,
            first_half_value=first_half_value,
            first_half_minutes=first_half_minutes,
            projected_second_half=round(projected_second_half, 1),
            projected_final=round(projected_final, 1),
            confidence_score=round(confidence, 1),
            recommendation=recommendation,
            factors=factors,
            foul_trouble=foul_trouble,
            blowout_warning=blowout_warning,
            pace_factor=round(pace_factor, 2),
            utilization_rate=round(utilization_rate, 1),
            fatigue_factor=fatigue_factor,
            minutes_projection=round(minutes_projection, 1),
            shooting_metrics={
                'fg_pct': shooting_metrics.fg_pct,
                'fg3_pct': shooting_metrics.fg3_pct,
                'ft_pct': shooting_metrics.ft_pct,
                'efg_pct': shooting_metrics.efg_pct,
                'ts_pct': shooting_metrics.ts_pct,
                'efficiency_rating': shooting_metrics.efficiency_rating,
            },
            assist_to_turnover=assist_to_turnover,
            opponent_def_rank=opponent_def_rank,
            opponent_def_rating=opp_ratings.def_rating,
            team_off_rating=team_ratings.off_rating if team_ratings else None,
            season_average=round(season_avg, 1) if season_avg else None,
            second_half_historical_avg=round(historical_2h_avg, 1) if historical_2h_avg else None,
            plus_minus=live_stats.plus_minus,
            shooting_efficiency=shooting_metrics.ts_pct
        )

    async def analyze_game_totals(
        self,
        game_data: LiveGameData,
        box_score: Dict[str, Any],
        home_ratings: Optional[TeamRatings] = None,
        away_ratings: Optional[TeamRatings] = None
    ) -> GameTotalProjection:
        """Analyze and project game totals at halftime."""
        first_half_total = game_data.total_score
        first_half_minutes = 24.0

        first_half_pace = first_half_total / first_half_minutes
        expected_pace = LEAGUE_AVG_TOTAL / 48.0
        league_avg_pace_comparison = first_half_pace / expected_pace

        if league_avg_pace_comparison >= 1.15:
            pace_rating = "very_fast"
        elif league_avg_pace_comparison >= 1.05:
            pace_rating = "fast"
        elif league_avg_pace_comparison >= 0.95:
            pace_rating = "average"
        else:
            pace_rating = "slow"

        blowout_risk = self._detect_blowout(game_data.score_differential)

        if league_avg_pace_comparison >= 1.2:
            pace_sustainability = 0.90
        elif league_avg_pace_comparison >= 1.1:
            pace_sustainability = 0.93
        elif league_avg_pace_comparison <= 0.85:
            pace_sustainability = 1.05
        else:
            pace_sustainability = PACE_SUSTAINABILITY

        base_second_half = first_half_total * pace_sustainability

        if blowout_risk:
            base_second_half *= 0.92

        projected_second_half_total = base_second_half
        projected_final_total = first_half_total + projected_second_half_total

        projected_q3_total = (projected_second_half_total / 2) * Q3_PACE_FACTOR
        projected_q4_total = projected_second_half_total - projected_q3_total

        total_confidence = 60.0

        if 0.95 <= league_avg_pace_comparison <= 1.05:
            total_confidence += 15
        elif 0.90 <= league_avg_pace_comparison <= 1.10:
            total_confidence += 8
        else:
            total_confidence -= 10

        if blowout_risk:
            total_confidence -= 15

        total_confidence = max(0, min(100, total_confidence))

        return GameTotalProjection(
            game_id=game_data.game_id,
            home_team=game_data.home_team_abbr,
            away_team=game_data.away_team_abbr,
            current_total=first_half_total,
            first_half_total=first_half_total,
            score_differential=game_data.score_differential,
            first_half_pace=round(first_half_pace, 2),
            pace_rating=pace_rating,
            league_avg_pace_comparison=round(league_avg_pace_comparison, 2),
            projected_second_half_total=round(projected_second_half_total, 1),
            projected_final_total=round(projected_final_total, 1),
            projected_q3_total=round(projected_q3_total, 1),
            projected_q4_total=round(projected_q4_total, 1),
            total_confidence=round(total_confidence, 1),
            blowout_risk=blowout_risk,
            pace_sustainability=round(pace_sustainability, 2),
            home_off_rating=home_ratings.off_rating if home_ratings else None,
            home_def_rating=home_ratings.def_rating if home_ratings else None,
            away_off_rating=away_ratings.off_rating if away_ratings else None,
            away_def_rating=away_ratings.def_rating if away_ratings else None
        )

    async def get_halftime_analysis(
        self,
        game_id: str,
        prop_lines: Optional[Dict[str, Dict[str, float]]] = None
    ) -> Dict[str, Any]:
        """
        Get complete halftime analysis for a game.
        Enhanced with team ratings and opponent defensive analysis.
        """
        games = await self.live_client.get_todays_games()
        game_data = next((g for g in games if g.game_id == game_id), None)

        if not game_data:
            raise ValueError(f"Game {game_id} not found")

        box_score = await self.live_client.get_live_box_score(game_id)

        # Get team ratings
        home_ratings = await self._get_team_ratings(game_data.home_team_id, game_data.home_team_abbr)
        away_ratings = await self._get_team_ratings(game_data.away_team_id, game_data.away_team_abbr)

        # Analyze game totals
        game_total_analysis = await self.analyze_game_totals(
            game_data, box_score, home_ratings, away_ratings
        )

        # Analyze players
        player_analyses = []
        all_players = box_score.get('home', []) + box_score.get('away', [])

        home_b2b = await self.live_client.is_back_to_back(game_data.home_team_id)
        away_b2b = await self.live_client.is_back_to_back(game_data.away_team_id)

        for player in all_players:
            if player.minutes_float < 5:
                continue

            is_home = player.team_abbreviation == game_data.home_team_abbr
            is_b2b = home_b2b if is_home else away_b2b
            team_stats = box_score.get('home' if is_home else 'away', [])

            # Opponent info for defensive adjustments
            opponent_team_id = game_data.away_team_id if is_home else game_data.home_team_id
            opponent_abbr = game_data.away_team_abbr if is_home else game_data.home_team_abbr
            team_ratings = home_ratings if is_home else away_ratings

            player_props = prop_lines.get(player.player_name, {}) if prop_lines else {}
            default_prop_types = ['points', 'rebounds', 'assists']

            for prop_type in default_prop_types:
                if prop_type in player_props:
                    prop_line = player_props[prop_type]
                else:
                    first_half_val = self._get_stat_value(player, prop_type)
                    prop_line = first_half_val * 2

                if prop_line <= 0:
                    continue

                try:
                    analysis = await self.analyze_halftime_player(
                        live_stats=player,
                        prop_line=prop_line,
                        prop_type=prop_type,
                        game_data=game_data,
                        team_stats=team_stats,
                        opponent_team_id=opponent_team_id,
                        opponent_abbr=opponent_abbr,
                        team_ratings=team_ratings,
                        is_back_to_back=is_b2b
                    )
                    player_analyses.append(analysis)
                except Exception as e:
                    logger.warning(f"Failed to analyze {player.player_name} for {prop_type}: {e}")

        # Generate suggestions
        suggestions = []
        for analysis in player_analyses:
            if analysis.confidence_score >= 60 and analysis.recommendation in ['strong_bet', 'bet', 'lean']:
                edge = analysis.projected_final - analysis.prop_line
                risk_level = 'low' if analysis.confidence_score >= 75 else ('medium' if analysis.confidence_score >= 65 else 'high')

                key_factors = []
                if analysis.factors.get('first_half_progress', 0) >= 50:
                    key_factors.append("Strong 1H progress")
                if analysis.shooting_metrics and analysis.shooting_metrics.get('ts_pct', 0) >= 60:
                    key_factors.append(f"Hot shooting ({analysis.shooting_metrics['ts_pct']:.0f}% TS)")
                if analysis.plus_minus >= 8:
                    key_factors.append(f"+{analysis.plus_minus} plus/minus")
                if analysis.opponent_def_rank and analysis.opponent_def_rank >= 25:
                    key_factors.append("Weak opponent defense")
                if analysis.pace_factor >= 1.1:
                    key_factors.append("Fast pace game")
                if analysis.foul_trouble:
                    key_factors.append("Warning: Foul trouble")
                if analysis.blowout_warning:
                    key_factors.append("Warning: Blowout risk")

                suggestions.append({
                    'player_name': analysis.player_name,
                    'team_abbreviation': analysis.team_abbreviation,
                    'prop_type': analysis.prop_type,
                    'prop_line': analysis.prop_line,
                    'current_value': analysis.first_half_value,
                    'projected_final': analysis.projected_final,
                    'confidence_score': analysis.confidence_score,
                    'recommendation': analysis.recommendation,
                    'edge': round(edge, 1),
                    'risk_level': risk_level,
                    'key_factors': key_factors
                })

        suggestions.sort(key=lambda x: x['confidence_score'], reverse=True)

        warnings = []
        if game_total_analysis.blowout_risk:
            warnings.append(f"Blowout warning: {game_data.score_differential} point differential")
        if game_total_analysis.pace_rating == "very_fast":
            warnings.append("Very fast pace - projections may have higher variance")

        # Enhanced game totals analysis
        enhanced_game_totals = None
        try:
            from app.core.game_totals_engine import GameTotalsEngine
            from app.services.balldontlie import balldontlie_service
            from dataclasses import asdict
            totals_engine = GameTotalsEngine(
                live_client=self.live_client,
                bdl_service=balldontlie_service
            )
            enhanced_result = await totals_engine.analyze(
                game_data, box_score, home_ratings, away_ratings
            )
            enhanced_game_totals = asdict(enhanced_result)
        except Exception as e:
            logger.warning(f"Enhanced game totals analysis failed: {e}")

        return {
            'game_id': game_id,
            'game_info': {
                'game_id': game_data.game_id,
                'game_status': game_data.game_status,
                'game_status_text': game_data.game_status_text,
                'period': game_data.period,
                'game_clock': game_data.game_clock,
                'home_team_id': game_data.home_team_id,
                'home_team_name': game_data.home_team_name,
                'home_team_abbr': game_data.home_team_abbr,
                'home_score': game_data.home_score,
                'away_team_id': game_data.away_team_id,
                'away_team_name': game_data.away_team_name,
                'away_team_abbr': game_data.away_team_abbr,
                'away_score': game_data.away_score,
                'game_date': game_data.game_date,
                'is_halftime': game_data.is_halftime,
                'score_differential': game_data.score_differential,
                'total_score': game_data.total_score,
            },
            'team_ratings': {
                'home': {
                    'off_rating': home_ratings.off_rating,
                    'def_rating': home_ratings.def_rating,
                    'net_rating': home_ratings.net_rating,
                    'pace': home_ratings.pace,
                },
                'away': {
                    'off_rating': away_ratings.off_rating,
                    'def_rating': away_ratings.def_rating,
                    'net_rating': away_ratings.net_rating,
                    'pace': away_ratings.pace,
                }
            },
            'game_total_analysis': {
                'game_id': game_total_analysis.game_id,
                'home_team': game_total_analysis.home_team,
                'away_team': game_total_analysis.away_team,
                'current_total': game_total_analysis.current_total,
                'first_half_total': game_total_analysis.first_half_total,
                'score_differential': game_total_analysis.score_differential,
                'first_half_pace': game_total_analysis.first_half_pace,
                'pace_rating': game_total_analysis.pace_rating,
                'league_avg_pace_comparison': game_total_analysis.league_avg_pace_comparison,
                'projected_second_half_total': game_total_analysis.projected_second_half_total,
                'projected_final_total': game_total_analysis.projected_final_total,
                'projected_q3_total': game_total_analysis.projected_q3_total,
                'projected_q4_total': game_total_analysis.projected_q4_total,
                'total_confidence': game_total_analysis.total_confidence,
                'blowout_risk': game_total_analysis.blowout_risk,
                'pace_sustainability': game_total_analysis.pace_sustainability,
            },
            'player_analyses': [
                {
                    'player_id': a.player_id,
                    'player_name': a.player_name,
                    'team_abbreviation': a.team_abbreviation,
                    'prop_type': a.prop_type,
                    'prop_line': a.prop_line,
                    'first_half_value': a.first_half_value,
                    'first_half_minutes': a.first_half_minutes,
                    'first_half_pace': round(a.first_half_value / a.first_half_minutes, 2) if a.first_half_minutes > 0 else 0,
                    'season_average': a.season_average,
                    'second_half_historical_avg': a.second_half_historical_avg,
                    'projected_second_half': a.projected_second_half,
                    'projected_final': a.projected_final,
                    'distance_from_line': round(a.projected_final - a.prop_line, 1),
                    'confidence_score': a.confidence_score,
                    'recommendation': a.recommendation,
                    'factors': a.factors,
                    'foul_trouble': a.foul_trouble,
                    'blowout_warning': a.blowout_warning,
                    'pace_factor': a.pace_factor,
                    'utilization_rate': a.utilization_rate,
                    'fatigue_factor': a.fatigue_factor,
                    'minutes_projection': a.minutes_projection,
                    'plus_minus': a.plus_minus,
                    'shooting_efficiency': a.shooting_efficiency,
                    'shooting_metrics': a.shooting_metrics,
                    'assist_to_turnover': a.assist_to_turnover,
                    'opponent_def_rank': a.opponent_def_rank,
                    'opponent_def_rating': a.opponent_def_rating,
                    'team_off_rating': a.team_off_rating,
                }
                for a in player_analyses
            ],
            'suggestions': suggestions,
            'analysis_timestamp': datetime.utcnow().isoformat(),
            'warnings': warnings,
            'enhanced_game_totals': enhanced_game_totals,
        }


# Global instance
halftime_engine = HalftimeAnalysisEngine()
