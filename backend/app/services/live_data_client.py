"""
Live NBA data client using nba_api library.
Fetches real-time game data, box scores, and live player stats.
"""
import logging
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
import asyncio
from functools import lru_cache

from nba_api.live.nba.endpoints import scoreboard, boxscore
from nba_api.stats.endpoints import (
    leaguegamefinder,
    commonplayerinfo,
    playergamelog,
    teamgamelog,
    leaguedashteamstats
)
from nba_api.stats.static import teams as nba_teams

from app.config import settings

logger = logging.getLogger(__name__)


@dataclass
class LivePlayerStats:
    """Live player statistics from an ongoing game."""
    player_id: int
    player_name: str
    team_id: int
    team_abbreviation: str
    minutes: str  # Format: "PT12M30S" or "12:30"
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


@dataclass
class LiveGameData:
    """Live game data including scores and status."""
    game_id: str
    game_status: int  # 1=scheduled, 2=in_progress, 3=final
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
    is_halftime: bool = False

    @property
    def score_differential(self) -> int:
        """Absolute score difference."""
        return abs(self.home_score - self.away_score)

    @property
    def total_score(self) -> int:
        """Combined score."""
        return self.home_score + self.away_score


class LiveDataClient:
    """Client for fetching live NBA game data using nba_api."""

    def __init__(self):
        self.timeout = getattr(settings, 'NBA_API_TIMEOUT', 10)
        self._team_cache: Dict[int, Dict] = {}
        self._initialize_team_cache()

    def _initialize_team_cache(self):
        """Cache team information for quick lookups."""
        try:
            all_teams = nba_teams.get_teams()
            for team in all_teams:
                self._team_cache[team['id']] = team
        except Exception as e:
            logger.warning(f"Failed to initialize team cache: {e}")

    def _parse_minutes(self, minutes_str: str) -> float:
        """Parse minutes string to float.

        Handles formats:
        - "PT12M30S" (ISO duration)
        - "12:30" (MM:SS)
        - "12" (just minutes)
        """
        if not minutes_str:
            return 0.0

        try:
            # ISO duration format: PT12M30S
            if minutes_str.startswith("PT"):
                minutes_str = minutes_str[2:]  # Remove PT
                minutes = 0.0
                if "M" in minutes_str:
                    m_idx = minutes_str.index("M")
                    minutes = float(minutes_str[:m_idx])
                    minutes_str = minutes_str[m_idx + 1:]
                if "S" in minutes_str:
                    seconds = float(minutes_str.replace("S", ""))
                    minutes += seconds / 60.0
                return minutes

            # MM:SS format
            if ":" in minutes_str:
                parts = minutes_str.split(":")
                return float(parts[0]) + float(parts[1]) / 60.0

            # Just a number
            return float(minutes_str)
        except (ValueError, IndexError):
            return 0.0

    def _parse_player_stats(self, player_data: Dict, team_abbr: str) -> LivePlayerStats:
        """Parse player statistics from API response."""
        stats = player_data.get('statistics', {})

        minutes_str = stats.get('minutes', '') or stats.get('min', '') or '0'
        minutes_float = self._parse_minutes(minutes_str)

        # Calculate percentages safely
        fg_att = stats.get('fieldGoalsAttempted', 0) or 0
        fg3_att = stats.get('threePointersAttempted', 0) or 0
        ft_att = stats.get('freeThrowsAttempted', 0) or 0

        fg_pct = (stats.get('fieldGoalsMade', 0) / fg_att * 100) if fg_att > 0 else 0.0
        fg3_pct = (stats.get('threePointersMade', 0) / fg3_att * 100) if fg3_att > 0 else 0.0
        ft_pct = (stats.get('freeThrowsMade', 0) / ft_att * 100) if ft_att > 0 else 0.0

        return LivePlayerStats(
            player_id=player_data.get('personId', 0),
            player_name=f"{player_data.get('firstName', '')} {player_data.get('familyName', '')}".strip(),
            team_id=player_data.get('teamId', 0),
            team_abbreviation=team_abbr,
            minutes=minutes_str,
            minutes_float=minutes_float,
            points=stats.get('points', 0) or 0,
            rebounds=stats.get('reboundsTotal', 0) or 0,
            assists=stats.get('assists', 0) or 0,
            steals=stats.get('steals', 0) or 0,
            blocks=stats.get('blocks', 0) or 0,
            turnovers=stats.get('turnovers', 0) or 0,
            fouls=stats.get('foulsPersonal', 0) or 0,
            fg_made=stats.get('fieldGoalsMade', 0) or 0,
            fg_attempted=fg_att,
            fg_pct=round(fg_pct, 1),
            fg3_made=stats.get('threePointersMade', 0) or 0,
            fg3_attempted=fg3_att,
            fg3_pct=round(fg3_pct, 1),
            ft_made=stats.get('freeThrowsMade', 0) or 0,
            ft_attempted=ft_att,
            ft_pct=round(ft_pct, 1),
            plus_minus=stats.get('plusMinusPoints', 0) or 0,
            starter=player_data.get('starter', '') == '1' or player_data.get('position', '') != ''
        )

    async def get_todays_games(self) -> List[LiveGameData]:
        """Fetch all of today's NBA games."""
        try:
            # Run synchronous NBA API call in thread pool
            loop = asyncio.get_event_loop()
            board = await loop.run_in_executor(None, scoreboard.ScoreBoard)
            games_data = board.get_dict()

            games = []
            scoreboard_data = games_data.get('scoreboard', {})

            for game in scoreboard_data.get('games', []):
                home_team = game.get('homeTeam', {})
                away_team = game.get('awayTeam', {})

                # Determine if at halftime (period 2 and game clock shows halftime)
                period = game.get('period', 0)
                game_clock = game.get('gameClock', '')
                game_status = game.get('gameStatus', 1)
                game_status_text = game.get('gameStatusText', '')

                # Check for halftime - typically at end of period 2 or status text contains "Halftime"
                is_halftime = (
                    'halftime' in game_status_text.lower() or
                    (period == 2 and game_status == 2 and game_clock in ['', 'PT00M00.00S', '0:00'])
                )

                games.append(LiveGameData(
                    game_id=game.get('gameId', ''),
                    game_status=game_status,
                    game_status_text=game_status_text,
                    period=period,
                    game_clock=game_clock,
                    home_team_id=home_team.get('teamId', 0),
                    home_team_name=home_team.get('teamName', ''),
                    home_team_abbr=home_team.get('teamTricode', ''),
                    home_score=home_team.get('score', 0),
                    away_team_id=away_team.get('teamId', 0),
                    away_team_name=away_team.get('teamName', ''),
                    away_team_abbr=away_team.get('teamTricode', ''),
                    away_score=away_team.get('score', 0),
                    game_date=game.get('gameCode', '')[:8] if game.get('gameCode') else '',
                    game_time_utc=game.get('gameTimeUTC'),
                    is_halftime=is_halftime
                ))

            logger.info(f"Fetched {len(games)} games for today")
            return games

        except Exception as e:
            logger.error(f"Failed to fetch today's games: {e}")
            return []

    async def get_halftime_games(self) -> List[LiveGameData]:
        """Fetch only games that are currently at halftime."""
        games = await self.get_todays_games()
        halftime_games = [g for g in games if g.is_halftime]
        logger.info(f"Found {len(halftime_games)} games at halftime")
        return halftime_games

    async def get_live_games(self) -> List[LiveGameData]:
        """Fetch only games that are currently in progress."""
        games = await self.get_todays_games()
        live_games = [g for g in games if g.game_status == 2]
        logger.info(f"Found {len(live_games)} live games")
        return live_games

    async def get_live_box_score(self, game_id: str) -> Dict[str, List[LivePlayerStats]]:
        """
        Fetch live box score for a specific game.

        Returns dict with 'home' and 'away' keys, each containing list of LivePlayerStats.
        """
        try:
            loop = asyncio.get_event_loop()
            box = await loop.run_in_executor(
                None,
                lambda: boxscore.BoxScore(game_id=game_id)
            )
            box_data = box.get_dict()

            game = box_data.get('game', {})
            home_team = game.get('homeTeam', {})
            away_team = game.get('awayTeam', {})

            home_abbr = home_team.get('teamTricode', '')
            away_abbr = away_team.get('teamTricode', '')

            home_players = []
            for player in home_team.get('players', []):
                if player.get('status', '') == 'ACTIVE' or player.get('played', '') == '1':
                    stats = self._parse_player_stats(player, home_abbr)
                    if stats.minutes_float > 0:  # Only include players who have played
                        home_players.append(stats)

            away_players = []
            for player in away_team.get('players', []):
                if player.get('status', '') == 'ACTIVE' or player.get('played', '') == '1':
                    stats = self._parse_player_stats(player, away_abbr)
                    if stats.minutes_float > 0:
                        away_players.append(stats)

            # Sort by points for easier viewing
            home_players.sort(key=lambda x: x.points, reverse=True)
            away_players.sort(key=lambda x: x.points, reverse=True)

            logger.info(f"Fetched box score for game {game_id}: {len(home_players)} home, {len(away_players)} away players")

            return {
                'home': home_players,
                'away': away_players,
                'home_team': {
                    'team_id': home_team.get('teamId'),
                    'team_name': home_team.get('teamName'),
                    'team_abbr': home_abbr,
                    'score': home_team.get('score', 0)
                },
                'away_team': {
                    'team_id': away_team.get('teamId'),
                    'team_name': away_team.get('teamName'),
                    'team_abbr': away_abbr,
                    'score': away_team.get('score', 0)
                }
            }

        except Exception as e:
            logger.error(f"Failed to fetch box score for game {game_id}: {e}")
            return {'home': [], 'away': [], 'home_team': {}, 'away_team': {}}

    async def get_team_pace(self, team_id: int, season: str = "2024-25") -> Optional[float]:
        """Get team's pace (possessions per 48 minutes)."""
        try:
            loop = asyncio.get_event_loop()
            stats = await loop.run_in_executor(
                None,
                lambda: leaguedashteamstats.LeagueDashTeamStats(
                    season=season,
                    measure_type_detailed_defense='Base'
                )
            )
            df = stats.get_data_frames()[0]
            team_row = df[df['TEAM_ID'] == team_id]
            if not team_row.empty:
                return float(team_row['PACE'].iloc[0])
            return None
        except Exception as e:
            logger.warning(f"Failed to get team pace for team {team_id}: {e}")
            return None

    async def get_player_season_stats(self, player_id: int, season: str = "2024-25") -> Optional[Dict]:
        """Get player's season averages."""
        try:
            loop = asyncio.get_event_loop()
            gamelog = await loop.run_in_executor(
                None,
                lambda: playergamelog.PlayerGameLog(
                    player_id=player_id,
                    season=season
                )
            )
            df = gamelog.get_data_frames()[0]

            if df.empty:
                return None

            # Calculate averages
            return {
                'games_played': len(df),
                'avg_points': float(df['PTS'].mean()),
                'avg_rebounds': float(df['REB'].mean()),
                'avg_assists': float(df['AST'].mean()),
                'avg_steals': float(df['STL'].mean()),
                'avg_blocks': float(df['BLK'].mean()),
                'avg_minutes': float(df['MIN'].mean()),
                'avg_fg_pct': float(df['FG_PCT'].mean() * 100),
                'avg_fg3_pct': float(df['FG3_PCT'].mean() * 100) if 'FG3_PCT' in df else 0,
                'avg_ft_pct': float(df['FT_PCT'].mean() * 100) if 'FT_PCT' in df else 0,
                # Second half averages (approximate - use overall for now)
                'second_half_avg_points': float(df['PTS'].mean()) * 0.48,  # Typical 2H share
                'second_half_avg_rebounds': float(df['REB'].mean()) * 0.52,
                'second_half_avg_assists': float(df['AST'].mean()) * 0.48,
            }
        except Exception as e:
            logger.warning(f"Failed to get player season stats for {player_id}: {e}")
            return None

    async def get_player_last_n_games(self, player_id: int, n: int = 10, season: str = "2024-25") -> List[Dict]:
        """Get player's last N game logs."""
        try:
            loop = asyncio.get_event_loop()
            gamelog = await loop.run_in_executor(
                None,
                lambda: playergamelog.PlayerGameLog(
                    player_id=player_id,
                    season=season
                )
            )
            df = gamelog.get_data_frames()[0]

            if df.empty:
                return []

            # Take last N games
            games = []
            for _, row in df.head(n).iterrows():
                games.append({
                    'game_date': row['GAME_DATE'],
                    'matchup': row['MATCHUP'],
                    'points': int(row['PTS']),
                    'rebounds': int(row['REB']),
                    'assists': int(row['AST']),
                    'steals': int(row['STL']),
                    'blocks': int(row['BLK']),
                    'minutes': float(row['MIN']),
                    'fg_pct': float(row['FG_PCT'] * 100),
                    'plus_minus': int(row['PLUS_MINUS']) if 'PLUS_MINUS' in row else 0
                })

            return games
        except Exception as e:
            logger.warning(f"Failed to get last {n} games for player {player_id}: {e}")
            return []

    async def is_back_to_back(self, team_id: int) -> bool:
        """Check if team is playing on a back-to-back."""
        try:
            yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
            loop = asyncio.get_event_loop()
            games = await loop.run_in_executor(
                None,
                lambda: leaguegamefinder.LeagueGameFinder(
                    team_id_nullable=team_id,
                    date_from_nullable=yesterday,
                    date_to_nullable=yesterday
                )
            )
            df = games.get_data_frames()[0]
            return len(df) > 0
        except Exception as e:
            logger.warning(f"Failed to check back-to-back for team {team_id}: {e}")
            return False

    def aggregate_team_box_score(self, players: List[LivePlayerStats]) -> Dict[str, Any]:
        """
        Aggregate individual player stats into team-level totals.
        Includes possession estimation using standard NBA formula.
        """
        total_fga = sum(p.fg_attempted for p in players)
        total_fta = sum(p.ft_attempted for p in players)
        total_tov = sum(p.turnovers for p in players)

        return {
            'total_points': sum(p.points for p in players),
            'total_rebounds': sum(p.rebounds for p in players),
            'total_assists': sum(p.assists for p in players),
            'total_steals': sum(p.steals for p in players),
            'total_blocks': sum(p.blocks for p in players),
            'total_turnovers': total_tov,
            'total_fouls': sum(p.fouls for p in players),
            'total_fg_made': sum(p.fg_made for p in players),
            'total_fg_attempted': total_fga,
            'total_fg3_made': sum(p.fg3_made for p in players),
            'total_fg3_attempted': sum(p.fg3_attempted for p in players),
            'total_ft_made': sum(p.ft_made for p in players),
            'total_ft_attempted': total_fta,
            'total_minutes': sum(p.minutes_float for p in players),
            'team_fg_pct': (sum(p.fg_made for p in players) / max(total_fga, 1)) * 100,
            'team_fg3_pct': (sum(p.fg3_made for p in players) / max(sum(p.fg3_attempted for p in players), 1)) * 100,
            'team_ft_pct': (sum(p.ft_made for p in players) / max(total_fta, 1)) * 100,
            # Standard possession estimation: Poss = FGA + 0.44 * FTA + TOV * 0.96
            'estimated_possessions': total_fga + 0.44 * total_fta + total_tov * 0.96,
        }


# Global instance
live_data_client = LiveDataClient()
