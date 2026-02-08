import httpx
import time
from typing import List, Dict, Optional, Any, Tuple
from datetime import datetime, timedelta
from app.config import settings
import logging

logger = logging.getLogger(__name__)


class BallDontLieService:
    """Service for interacting with the BallDontLie API."""

    def __init__(self):
        self.base_url = settings.BALLDONTLIE_BASE_URL
        self.api_key = settings.BALLDONTLIE_API_KEY
        self.headers = {
            "Authorization": self.api_key
        }
        self._cache: Dict[str, Tuple[Any, float]] = {}
        self._cache_ttl = 300  # 5 minutes

    async def _cached_request(self, cache_key: str, endpoint: str, params: Optional[Dict] = None) -> Dict:
        """Request with in-memory TTL cache to avoid duplicate API calls."""
        now = time.time()
        if cache_key in self._cache:
            cached_data, cached_at = self._cache[cache_key]
            if now - cached_at < self._cache_ttl:
                return cached_data

        result = await self._make_request(endpoint, params)
        self._cache[cache_key] = (result, now)
        return result

    async def _make_request(self, endpoint: str, params: Optional[Dict] = None) -> Dict:
        """Make an async HTTP request to the BallDontLie API."""
        url = f"{self.base_url}{endpoint}"
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=self.headers, params=params, timeout=30.0)
                response.raise_for_status()
                return response.json()
        except httpx.HTTPError as e:
            logger.error(f"API request failed: {e}")
            raise
    
    async def search_player(self, name: str) -> Optional[Dict]:
        """
        Search for a player by name.
        
        Args:
            name: Player name to search for
            
        Returns:
            Player data or None if not found
        """
        try:
            # Split name into parts
            parts = name.strip().split()
            if len(parts) >= 2:
                first_name = parts[0]
                last_name = " ".join(parts[1:])
            else:
                first_name = ""
                last_name = name
            
            # Search players
            params = {}
            if first_name:
                params["first_name"] = first_name
            if last_name:
                params["last_name"] = last_name
            
            response = await self._make_request("/v1/players", params)
            players = response.get("data", [])
            
            if players:
                # Return first match
                return players[0]
            
            return None
            
        except Exception as e:
            logger.error(f"Player search failed for {name}: {e}")
            return None
    
    async def get_player_stats(self, player_id: int, limit: int = 10) -> List[Dict]:
        """
        Get recent game stats for a player.
        
        Args:
            player_id: BallDontLie player ID
            limit: Number of recent games to fetch
            
        Returns:
            List of game stats
        """
        try:
            params = {
                "player_ids[]": player_id,
                "per_page": limit
            }
            
            response = await self._make_request("/v1/stats", params)
            return response.get("data", [])
            
        except Exception as e:
            logger.error(f"Failed to fetch player stats for player {player_id}: {e}")
            return []
    
    async def get_player_season_averages(self, player_id: int, season: int = 2024) -> Optional[Dict]:
        """
        Get season averages for a player.
        
        Args:
            player_id: BallDontLie player ID
            season: NBA season year
            
        Returns:
            Season averages data
        """
        try:
            params = {
                "season": season,
                "player_ids[]": player_id
            }
            
            response = await self._make_request("/v1/season_averages", params)
            data = response.get("data", [])
            
            if data:
                return data[0]
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to fetch season averages for player {player_id}: {e}")
            return None
    
    async def get_team(self, team_id: int) -> Optional[Dict]:
        """Get team information."""
        try:
            response = await self._make_request(f"/v1/teams/{team_id}")
            return response.get("data")
        except Exception as e:
            logger.error(f"Failed to fetch team {team_id}: {e}")
            return None
    
    async def search_team_by_name(self, name: str) -> Optional[Dict]:
        """
        Search for a team by name.
        
        Args:
            name: Team name or abbreviation
            
        Returns:
            Team data or None if not found
        """
        try:
            response = await self._make_request("/v1/teams")
            teams = response.get("data", [])
            
            name_lower = name.lower()
            
            # Try exact matches first
            for team in teams:
                if (team.get("name", "").lower() == name_lower or 
                    team.get("full_name", "").lower() == name_lower or
                    team.get("abbreviation", "").lower() == name_lower):
                    return team
            
            # Try partial matches
            for team in teams:
                if (name_lower in team.get("name", "").lower() or 
                    name_lower in team.get("full_name", "").lower()):
                    return team
            
            return None
            
        except Exception as e:
            logger.error(f"Team search failed for {name}: {e}")
            return None
    
    async def get_upcoming_games(self, team_id: Optional[int] = None, days: int = 7) -> List[Dict]:
        """
        Get upcoming games.
        
        Args:
            team_id: Optional team ID to filter by
            days: Number of days ahead to look
            
        Returns:
            List of upcoming games
        """
        try:
            today = datetime.now()
            end_date = today + timedelta(days=days)
            
            params = {
                "start_date": today.strftime("%Y-%m-%d"),
                "end_date": end_date.strftime("%Y-%m-%d")
            }
            
            if team_id:
                params["team_ids[]"] = team_id
            
            response = await self._make_request("/v1/games", params)
            return response.get("data", [])
            
        except Exception as e:
            logger.error(f"Failed to fetch upcoming games: {e}")
            return []
    
    async def get_team_stats(self, team_id: int, season: int = 2024) -> Optional[Dict]:
        """
        Get team season statistics.

        Args:
            team_id: Team ID
            season: Season year

        Returns:
            Team stats data
        """
        try:
            params = {
                "season": season,
                "team_ids[]": team_id
            }

            # Note: This endpoint may need adjustment based on actual API
            response = await self._cached_request(
                f"team_stats_{team_id}_{season}",
                "/v1/stats/team_season", params
            )
            data = response.get("data", [])

            if data:
                return data[0]

            return None

        except Exception as e:
            logger.error(f"Failed to fetch team stats for {team_id}: {e}")
            return None

    async def get_team_recent_games(self, team_id: int, limit: int = 10, season: int = 2025) -> List[Dict]:
        """
        Get team's recent game results for trend analysis.

        Returns list of games with scores for computing recent form,
        average total, and scoring trends.
        """
        try:
            today = datetime.now()
            start_of_season = datetime(today.year if today.month >= 10 else today.year - 1, 10, 1)

            params = {
                "team_ids[]": team_id,
                "per_page": limit,
                "start_date": start_of_season.strftime("%Y-%m-%d"),
                "end_date": today.strftime("%Y-%m-%d"),
            }

            response = await self._cached_request(
                f"team_recent_{team_id}_{limit}",
                "/v1/games", params
            )
            games = response.get("data", [])
            # Return most recent games (API returns chronologically)
            return sorted(games, key=lambda g: g.get("date", ""), reverse=True)[:limit]

        except Exception as e:
            logger.error(f"Failed to fetch recent games for team {team_id}: {e}")
            return []

    async def get_multiple_player_season_averages(
        self, player_ids: List[int], season: int = 2025
    ) -> Dict[int, Dict]:
        """
        Batch fetch season averages for multiple players.
        Returns dict keyed by player_id.
        """
        results = {}
        for pid in player_ids:
            try:
                avg = await self.get_player_season_averages(pid, season)
                if avg:
                    results[pid] = avg
            except Exception as e:
                logger.warning(f"Failed to get season averages for player {pid}: {e}")
        return results

    def clear_cache(self):
        """Clear the in-memory cache."""
        self._cache.clear()


# Global instance
balldontlie_service = BallDontLieService()
