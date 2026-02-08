from typing import List, Dict, Optional
from datetime import datetime
import numpy as np
from dataclasses import dataclass
import logging

from app.services.balldontlie import balldontlie_service

logger = logging.getLogger(__name__)


@dataclass
class PropBetData:
    """Data class for prop bet information."""
    prop_id: int
    player_name: str
    player_id: Optional[int]
    stat_type: str
    line: float
    over_under: str
    opponent_name: Optional[str]
    game_date: Optional[datetime]


@dataclass
class PropAnalysis:
    """Analysis results for a single prop bet."""
    prop_id: int
    player_name: str
    stat_type: str
    line: float
    over_under: str
    confidence_score: float
    hit_rate_last_10: float
    average_stat: float
    opponent_defensive_rank: Optional[int]
    pace_adjusted_projection: float
    factors: Dict[str, float]
    recommendation: str
    analysis_notes: Optional[str] = None


class AnalysisEngine:
    """Core analysis engine for prop bet evaluation."""
    
    STAT_TYPE_MAP = {
        'points': 'pts',
        'pts': 'pts',
        'rebounds': 'reb',
        'reb': 'reb',
        'assists': 'ast',
        'ast': 'ast',
        'threes': 'fg3m',
        '3pm': 'fg3m',
        'steals': 'stl',
        'stl': 'stl',
        'blocks': 'blk',
        'blk': 'blk'
    }
    
    def __init__(self):
        self.service = balldontlie_service
    
    async def analyze_prop(self, prop: PropBetData) -> PropAnalysis:
        """
        Analyze a single prop bet.
        
        Args:
            prop: Prop bet data
            
        Returns:
            Prop analysis results
        """
        logger.info(f"Analyzing prop: {prop.player_name} {prop.stat_type} {prop.over_under} {prop.line}")
        
        # Get player info if needed
        if not prop.player_id:
            player_data = await self.service.search_player(prop.player_name)
            if player_data:
                prop.player_id = player_data.get("id")
        
        if not prop.player_id:
            # Cannot analyze without player data
            return self._create_default_analysis(prop, "Player not found in database")
        
        # Fetch player stats
        recent_games = await self.service.get_player_stats(prop.player_id, limit=10)
        
        if not recent_games:
            return self._create_default_analysis(prop, "No recent game data available")
        
        # Calculate hit rate
        hit_rate = self._calculate_hit_rate(recent_games, prop)
        
        # Calculate average stat
        stat_key = self.STAT_TYPE_MAP.get(prop.stat_type.lower(), prop.stat_type.lower())
        average_stat = self._calculate_average_stat(recent_games, stat_key)
        
        # Get opponent data (simplified for now)
        opponent_rank = None
        if prop.opponent_name:
            opponent_data = await self.service.search_team_by_name(prop.opponent_name)
            if opponent_data:
                # Simplified ranking - in production, fetch actual defensive rankings
                opponent_rank = 15  # Middle of the pack default
        
        # Calculate pace adjustment (simplified)
        pace_adjustment = 1.0  # Default pace factor
        pace_adjusted_projection = average_stat * pace_adjustment
        
        # Analyze factors
        factors = self._analyze_factors(recent_games, prop, stat_key)
        
        # Calculate confidence score
        confidence = self._calculate_confidence(hit_rate, factors, average_stat, prop.line)
        
        # Generate recommendation
        recommendation = self._generate_recommendation(confidence, prop.over_under)
        
        # Analysis notes
        notes = self._generate_analysis_notes(prop, hit_rate, average_stat, factors)
        
        return PropAnalysis(
            prop_id=prop.prop_id,
            player_name=prop.player_name,
            stat_type=prop.stat_type,
            line=prop.line,
            over_under=prop.over_under,
            confidence_score=round(confidence, 2),
            hit_rate_last_10=round(hit_rate, 2),
            average_stat=round(average_stat, 2),
            opponent_defensive_rank=opponent_rank,
            pace_adjusted_projection=round(pace_adjusted_projection, 2),
            factors=factors,
            recommendation=recommendation,
            analysis_notes=notes
        )
    
    def _calculate_hit_rate(self, games: List[Dict], prop: PropBetData) -> float:
        """Calculate how often the player hit this prop in recent games."""
        stat_key = self.STAT_TYPE_MAP.get(prop.stat_type.lower(), prop.stat_type.lower())
        
        hits = 0
        valid_games = 0
        
        for game in games:
            stat_value = game.get(stat_key, 0)
            if stat_value is not None:
                valid_games += 1
                if prop.over_under == 'over' and stat_value > prop.line:
                    hits += 1
                elif prop.over_under == 'under' and stat_value < prop.line:
                    hits += 1
        
        return (hits / valid_games * 100) if valid_games > 0 else 0
    
    def _calculate_average_stat(self, games: List[Dict], stat_key: str) -> float:
        """Calculate average stat value from recent games."""
        values = []
        for game in games:
            value = game.get(stat_key, 0)
            if value is not None:
                values.append(value)
        
        return np.mean(values) if values else 0
    
    def _analyze_factors(self, games: List[Dict], prop: PropBetData, stat_key: str) -> Dict[str, float]:
        """
        Analyze various factors affecting the prop.
        
        Returns:
            Dictionary of factor names to impact scores (-1 to 1)
        """
        factors = {}
        
        # Recent trend
        if len(games) >= 5:
            recent_stats = [game.get(stat_key, 0) for game in games[:5] if game.get(stat_key) is not None]
            if recent_stats:
                trend = np.polyfit(range(len(recent_stats)), recent_stats, 1)[0]
                factors['recent_trend'] = float(np.clip(trend / 5, -1, 1))
        
        # Consistency
        stats = [game.get(stat_key, 0) for game in games if game.get(stat_key) is not None]
        if stats:
            variance = np.var(stats)
            # Lower variance is better (more consistent)
            consistency_score = 1 - min(variance / 50, 1)
            factors['consistency'] = float(consistency_score)
        
        # Home/Away (simplified - would need game details)
        factors['home_away'] = 0.0  # Neutral for now
        
        # Rest days (simplified)
        factors['rest'] = 0.0  # Neutral for now
        
        # Minutes played trend
        minutes = [game.get('min', '0:00') for game in games if game.get('min')]
        if minutes:
            # Convert minutes to float (e.g., "34:25" -> 34.42)
            try:
                min_values = []
                for m in minutes:
                    if isinstance(m, str) and ':' in m:
                        parts = m.split(':')
                        min_values.append(int(parts[0]) + int(parts[1]) / 60)
                    else:
                        min_values.append(float(m) if m else 0)
                
                if min_values:
                    avg_minutes = np.mean(min_values)
                    # Playing time impact: 30+ minutes is good
                    factors['playing_time'] = float(min(avg_minutes / 35, 1.0))
            except:
                factors['playing_time'] = 0.5  # Neutral if can't parse
        
        return factors
    
    def _calculate_confidence(self, hit_rate: float, factors: Dict[str, float], 
                            avg_stat: float, line: float) -> float:
        """
        Calculate overall confidence score (0-100).
        
        Args:
            hit_rate: Historical hit rate percentage
            factors: Factor analysis results
            avg_stat: Average stat value
            line: Prop line value
            
        Returns:
            Confidence score 0-100
        """
        # Base confidence from hit rate
        base_confidence = hit_rate
        
        # Distance from line adjustment
        distance_from_line = abs(avg_stat - line)
        # If average is far from line (in right direction), boost confidence
        if avg_stat > line:
            distance_boost = min(distance_from_line * 2, 10)
        else:
            distance_boost = -min(distance_from_line * 2, 10)
        
        # Factor adjustments
        factor_weights = {
            'recent_trend': 8,
            'consistency': 10,
            'home_away': 5,
            'rest': 3,
            'playing_time': 8
        }
        
        factor_adjustment = sum(
            factors.get(k, 0) * v 
            for k, v in factor_weights.items()
        )
        
        confidence = base_confidence + distance_boost + factor_adjustment
        return float(np.clip(confidence, 0, 100))
    
    def _generate_recommendation(self, confidence: float, over_under: str) -> str:
        """Generate actionable recommendation based on confidence."""
        if confidence >= 70:
            return 'strong_bet'
        elif confidence >= 58:
            return 'bet'
        elif confidence >= 45:
            return 'neutral'
        elif confidence >= 30:
            return 'avoid'
        else:
            return 'strong_avoid'
    
    def _generate_analysis_notes(self, prop: PropBetData, hit_rate: float, 
                                average_stat: float, factors: Dict[str, float]) -> str:
        """Generate human-readable analysis notes."""
        notes = []
        
        # Hit rate note
        if hit_rate >= 70:
            notes.append(f"Player has hit this prop in {hit_rate:.0f}% of last 10 games (strong track record).")
        elif hit_rate >= 50:
            notes.append(f"Player has hit this prop in {hit_rate:.0f}% of last 10 games (decent track record).")
        else:
            notes.append(f"Player has only hit this prop in {hit_rate:.0f}% of last 10 games (poor track record).")
        
        # Average vs line
        if average_stat > prop.line:
            diff = average_stat - prop.line
            notes.append(f"Player's average ({average_stat:.1f}) is {diff:.1f} above the line.")
        elif average_stat < prop.line:
            diff = prop.line - average_stat
            notes.append(f"Player's average ({average_stat:.1f}) is {diff:.1f} below the line.")
        else:
            notes.append(f"Player's average matches the line exactly.")
        
        # Key factors
        if factors.get('recent_trend', 0) > 0.3:
            notes.append("Player is trending up recently.")
        elif factors.get('recent_trend', 0) < -0.3:
            notes.append("Player is trending down recently.")
        
        if factors.get('consistency', 0) > 0.7:
            notes.append("Player has been very consistent.")
        elif factors.get('consistency', 0) < 0.3:
            notes.append("Player's performance has been inconsistent.")
        
        return " ".join(notes)
    
    def _create_default_analysis(self, prop: PropBetData, reason: str) -> PropAnalysis:
        """Create a default analysis when data is unavailable."""
        return PropAnalysis(
            prop_id=prop.prop_id,
            player_name=prop.player_name,
            stat_type=prop.stat_type,
            line=prop.line,
            over_under=prop.over_under,
            confidence_score=50.0,
            hit_rate_last_10=50.0,
            average_stat=prop.line,
            opponent_defensive_rank=None,
            pace_adjusted_projection=prop.line,
            factors={},
            recommendation='neutral',
            analysis_notes=f"Unable to analyze: {reason}"
        )
    
    async def analyze_bet_slip(self, props: List[PropBetData]) -> Dict:
        """
        Analyze an entire bet slip.
        
        Args:
            props: List of prop bets to analyze
            
        Returns:
            Dictionary containing overall analysis and individual prop analyses
        """
        # Analyze each prop
        prop_analyses = []
        for prop in props:
            analysis = await self.analyze_prop(prop)
            prop_analyses.append(analysis)
        
        # Calculate overall confidence (average of all props)
        confidences = [a.confidence_score for a in prop_analyses]
        overall_confidence = np.mean(confidences) if confidences else 50.0
        
        # Identify recommended bets (confidence >= 58)
        recommended = [a.prop_id for a in prop_analyses if a.confidence_score >= 58]
        
        # Risk assessment
        if overall_confidence >= 65:
            risk = "low"
        elif overall_confidence >= 50:
            risk = "medium"
        else:
            risk = "high"
        
        # Generate parlay suggestions (top 2-3 props)
        top_props = sorted(prop_analyses, key=lambda x: x.confidence_score, reverse=True)[:3]
        parlay_suggestions = [
            {
                "props": [p.prop_id for p in top_props[:2]],
                "confidence": np.mean([p.confidence_score for p in top_props[:2]]),
                "description": "Top 2 props parlay"
            },
            {
                "props": [p.prop_id for p in top_props],
                "confidence": np.mean([p.confidence_score for p in top_props]),
                "description": "Top 3 props parlay"
            }
        ] if len(top_props) >= 2 else []
        
        return {
            "overall_confidence": round(overall_confidence, 2),
            "risk_assessment": risk,
            "recommended_bets": recommended,
            "parlay_suggestions": parlay_suggestions,
            "prop_analyses": prop_analyses
        }


# Global instance
analysis_engine = AnalysisEngine()
