"""
BallDontLie Analytics Layer.

Computes derived analytics from raw BDL API data:
- Team offensive/defensive ratings from recent games
- League-wide defensive rankings (1-30)
- Positional defense analysis (how teams defend G/F/C)
- Player trend analysis (hit rate, trend slope, consistency)
"""
import logging
import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

# Position groupings: BDL uses G, F, C, G-F, F-C, etc.
POSITION_GROUPS = {
    "G": ["G", "G-F", "PG", "SG"],
    "F": ["F", "G-F", "F-C", "SF", "PF"],
    "C": ["C", "F-C"],
}

STAT_KEY_MAP = {
    "points": "pts",
    "rebounds": "reb",
    "assists": "ast",
    "steals": "stl",
    "blocks": "blk",
    "threes": "fg3m",
    "3pt": "fg3m",
    "turnovers": "turnover",
}


@dataclass
class TeamRatingsBDL:
    """Team offensive/defensive ratings derived from BDL recent games."""
    team_id: int
    team_abbr: str
    avg_points_scored: float = 0.0
    avg_points_allowed: float = 0.0
    avg_total: float = 0.0
    home_avg_scored: float = 0.0
    away_avg_scored: float = 0.0
    home_avg_allowed: float = 0.0
    away_avg_allowed: float = 0.0
    games_sampled: int = 0


@dataclass
class DefensiveRanking:
    """A team's defensive ranking across stat categories."""
    team_id: int
    team_abbr: str
    pts_allowed_avg: float = 0.0
    pts_rank: int = 15  # 1=best defense, 30=worst
    reb_allowed_avg: float = 0.0
    reb_rank: int = 15
    ast_allowed_avg: float = 0.0
    ast_rank: int = 15


@dataclass
class PositionalDefense:
    """How a team defends a specific position group."""
    team_abbr: str
    position: str  # G, F, or C
    avg_points_allowed: float = 0.0
    avg_rebounds_allowed: float = 0.0
    avg_assists_allowed: float = 0.0
    sample_size: int = 0
    rating: str = "average"  # elite, good, average, poor, terrible


@dataclass
class PlayerTrendAnalysis:
    """Player trend analysis from recent games."""
    player_name: str
    stat_type: str
    games_sampled: int = 0
    hit_rate: float = 0.0  # % of games hitting the line
    hits: int = 0
    misses: int = 0
    average_stat: float = 0.0
    recent_trend: float = 0.0  # slope: positive = trending up
    trend_direction: str = "steady"  # up, down, steady
    consistency: float = 0.5  # 0-1, higher = more consistent
    consistency_label: str = "medium"  # high, medium, low
    last_5_values: List[float] = field(default_factory=list)


class BDLAnalytics:
    """Analytics engine powered by BallDontLie data."""

    def __init__(self, bdl_service):
        self.bdl = bdl_service
        self._team_ratings_cache: Dict[int, TeamRatingsBDL] = {}
        self._defensive_rankings_cache: Optional[List[DefensiveRanking]] = None

    async def get_team_ratings(self, team_id: int, team_abbr: str = "") -> TeamRatingsBDL:
        """
        Compute team offensive/defensive ratings from recent games.
        Cached per instance lifetime.
        """
        if team_id in self._team_ratings_cache:
            return self._team_ratings_cache[team_id]

        ratings = TeamRatingsBDL(team_id=team_id, team_abbr=team_abbr)

        try:
            games = await self.bdl.get_team_recent_games_with_scores(team_id, limit=10)
            if not games:
                self._team_ratings_cache[team_id] = ratings
                return ratings

            scored = [g["team_score"] for g in games if g["team_score"]]
            allowed = [g["opponent_score"] for g in games if g["opponent_score"]]
            home_games = [g for g in games if g["is_home"]]
            away_games = [g for g in games if not g["is_home"]]

            ratings.games_sampled = len(games)
            ratings.avg_points_scored = np.mean(scored) if scored else 0
            ratings.avg_points_allowed = np.mean(allowed) if allowed else 0
            ratings.avg_total = ratings.avg_points_scored + ratings.avg_points_allowed

            if home_games:
                ratings.home_avg_scored = np.mean([g["team_score"] for g in home_games])
                ratings.home_avg_allowed = np.mean([g["opponent_score"] for g in home_games])
            if away_games:
                ratings.away_avg_scored = np.mean([g["team_score"] for g in away_games])
                ratings.away_avg_allowed = np.mean([g["opponent_score"] for g in away_games])

        except Exception as e:
            logger.warning(f"Failed to compute team ratings for {team_abbr}: {e}")

        self._team_ratings_cache[team_id] = ratings
        return ratings

    async def get_defensive_rankings(self) -> List[DefensiveRanking]:
        """
        Rank all 30 teams by points/rebounds/assists allowed.
        Returns list sorted by pts_rank (best defense first).
        Cached per instance.
        """
        if self._defensive_rankings_cache is not None:
            return self._defensive_rankings_cache

        rankings = []
        try:
            teams = await self.bdl.get_all_teams()
            if not teams:
                return rankings

            # Fetch recent games for each team
            for team in teams:
                tid = team.get("id")
                abbr = team.get("abbreviation", "")
                if not tid:
                    continue
                r = await self.get_team_ratings(tid, abbr)
                rankings.append(DefensiveRanking(
                    team_id=tid,
                    team_abbr=abbr,
                    pts_allowed_avg=round(r.avg_points_allowed, 1),
                    reb_allowed_avg=0,  # would need box score data
                    ast_allowed_avg=0,
                ))

            # Rank by points allowed (ascending = best defense)
            rankings.sort(key=lambda x: x.pts_allowed_avg)
            for i, r in enumerate(rankings):
                r.pts_rank = i + 1

        except Exception as e:
            logger.warning(f"Failed to compute defensive rankings: {e}")

        self._defensive_rankings_cache = rankings
        return rankings

    async def get_team_defensive_rank(self, team_id: int) -> Optional[DefensiveRanking]:
        """Get a specific team's defensive ranking."""
        rankings = await self.get_defensive_rankings()
        for r in rankings:
            if r.team_id == team_id:
                return r
        return None

    async def get_positional_defense(
        self, team_abbr: str, position: str
    ) -> PositionalDefense:
        """
        Analyze how a team defends a specific position group (G/F/C).
        Uses the team's recent opponent player stats.

        Since BDL doesn't have a direct "stats against" endpoint, we approximate
        using league-average positional scoring and the team's overall defensive rating.
        """
        result = PositionalDefense(team_abbr=team_abbr, position=position)

        try:
            # Get the team's overall defensive rating
            teams = await self.bdl.get_all_teams()
            team = next((t for t in teams if t.get("abbreviation", "").upper() == team_abbr.upper()), None)
            if not team:
                return result

            team_id = team.get("id")
            ratings = await self.get_team_ratings(team_id, team_abbr)
            def_rank = await self.get_team_defensive_rank(team_id)

            # League average positional scoring splits
            # (approximate: guards ~45% of team points, forwards ~35%, centers ~20%)
            positional_splits = {
                "G": {"pts": 0.45, "reb": 0.20, "ast": 0.55},
                "F": {"pts": 0.35, "reb": 0.40, "ast": 0.30},
                "C": {"pts": 0.20, "reb": 0.40, "ast": 0.15},
            }
            split = positional_splits.get(position, positional_splits["F"])

            result.avg_points_allowed = round(ratings.avg_points_allowed * split["pts"], 1)
            result.avg_rebounds_allowed = round(ratings.avg_points_allowed * split["reb"] * 0.4, 1)
            result.avg_assists_allowed = round(ratings.avg_points_allowed * split["ast"] * 0.22, 1)
            result.sample_size = ratings.games_sampled

            # Rate the defense
            if def_rank:
                rank = def_rank.pts_rank
                if rank <= 5:
                    result.rating = "elite"
                elif rank <= 10:
                    result.rating = "good"
                elif rank <= 20:
                    result.rating = "average"
                elif rank <= 25:
                    result.rating = "poor"
                else:
                    result.rating = "terrible"

        except Exception as e:
            logger.warning(f"Failed positional defense for {team_abbr} vs {position}: {e}")

        return result

    async def get_player_trend_analysis(
        self,
        player_name: str,
        stat_type: str,
        line: float
    ) -> PlayerTrendAnalysis:
        """
        Analyze a player's recent trend for a specific stat vs a prop line.
        Ported from analysis_engine.py patterns.

        Returns hit rate, trend slope, consistency score.
        """
        result = PlayerTrendAnalysis(
            player_name=player_name,
            stat_type=stat_type,
        )

        try:
            games = await self.bdl.get_player_recent_stats(player_name, limit=10)
            if not games:
                return result

            stat_key = STAT_KEY_MAP.get(stat_type.lower(), stat_type.lower())
            values = []
            for g in games:
                val = g.get(stat_key)
                if val is not None:
                    values.append(float(val))

            if not values:
                return result

            result.games_sampled = len(values)
            result.average_stat = round(float(np.mean(values)), 1)

            # Hit rate: how many games exceeded the line
            hits = sum(1 for v in values if v > line)
            result.hits = hits
            result.misses = len(values) - hits
            result.hit_rate = round((hits / len(values)) * 100, 1) if values else 0

            # Recent trend: linear regression slope over last 5 games
            recent = values[:5]  # Most recent 5
            result.last_5_values = [round(v, 1) for v in recent]
            if len(recent) >= 3:
                # polyfit: positive slope = improving
                coeffs = np.polyfit(range(len(recent)), list(reversed(recent)), 1)
                slope = float(coeffs[0])
                result.recent_trend = round(np.clip(slope / 5, -1, 1), 2)
                if result.recent_trend > 0.15:
                    result.trend_direction = "up"
                elif result.recent_trend < -0.15:
                    result.trend_direction = "down"
                else:
                    result.trend_direction = "steady"

            # Consistency: inverse variance (from analysis_engine pattern)
            if len(values) >= 3:
                variance = float(np.var(values))
                consistency = 1 - min(variance / 50, 1)
                result.consistency = round(max(0, min(1, consistency)), 2)
                if result.consistency >= 0.7:
                    result.consistency_label = "high"
                elif result.consistency >= 0.4:
                    result.consistency_label = "medium"
                else:
                    result.consistency_label = "low"

        except Exception as e:
            logger.warning(f"Failed trend analysis for {player_name} ({stat_type}): {e}")

        return result

    async def get_player_season_avg(self, player_name: str) -> Optional[Dict]:
        """
        Get player season averages via BDL. Fallback for nba_api.
        Returns dict with pts, reb, ast, min, fg_pct, fg3_pct, ft_pct.
        """
        try:
            player = await self.bdl.search_player(player_name)
            if not player:
                return None

            player_id = player.get("id")
            position = player.get("position", "")
            avg = await self.bdl.get_player_season_averages(player_id, season=2024)
            if not avg:
                return None

            return {
                "pts": avg.get("pts", 0),
                "reb": avg.get("reb", 0),
                "ast": avg.get("ast", 0),
                "min": float(str(avg.get("min", "0")).split(":")[0]) if avg.get("min") else 0,
                "fg_pct": avg.get("fg_pct", 0),
                "fg3_pct": avg.get("fg3_pct", 0),
                "ft_pct": avg.get("ft_pct", 0),
                "position": position,
                "games_played": avg.get("games_played", 0),
            }
        except Exception as e:
            logger.warning(f"Failed BDL season avg for {player_name}: {e}")
            return None

    def get_position_group(self, position: str) -> str:
        """Map a player's position string to G/F/C group."""
        pos = position.upper().strip()
        for group, variants in POSITION_GROUPS.items():
            if pos in variants:
                return group
        # Default to F if unknown
        return "F"
