from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class PropBetCreate(BaseModel):
    """Schema for creating a prop bet."""
    player_name: str = Field(..., min_length=1)
    stat_type: str = Field(..., description="points, rebounds, assists, etc.")
    line: float = Field(..., gt=0)
    over_under: str = Field(..., pattern="^(over|under)$")
    opponent_name: Optional[str] = None
    game_date: Optional[datetime] = None
    odds: Optional[int] = None


class PropBetResponse(PropBetCreate):
    """Schema for prop bet response."""
    id: int
    bet_slip_id: int
    player_id: Optional[int] = None
    team_name: Optional[str] = None
    game_id: Optional[int] = None
    
    class Config:
        from_attributes = True


class BetSlipCreate(BaseModel):
    """Schema for creating a bet slip."""
    name: Optional[str] = None
    prop_bets: List[PropBetCreate] = Field(..., min_items=1)


class BetSlipResponse(BaseModel):
    """Schema for bet slip response."""
    id: int
    user_id: int
    name: Optional[str]
    slip_type: str
    status: str
    created_at: datetime
    analyzed_at: Optional[datetime]
    prop_bets: List[PropBetResponse]
    
    class Config:
        from_attributes = True


class PropAnalysisDetail(BaseModel):
    """Detailed analysis for a single prop bet."""
    prop_id: int
    player_name: str
    stat_type: str
    line: float
    over_under: str
    
    # Analysis results
    confidence_score: float = Field(..., ge=0, le=100)
    hit_rate_last_10: float = Field(..., ge=0, le=100)
    average_stat: float
    opponent_defensive_rank: Optional[int] = None
    pace_adjusted_projection: float
    
    # Factor breakdown
    factors: Dict[str, float] = Field(default_factory=dict)
    
    # Recommendation
    recommendation: str = Field(..., description="strong_bet, bet, neutral, avoid, strong_avoid")
    analysis_notes: Optional[str] = None


class AnalysisResponse(BaseModel):
    """Schema for analysis response."""
    id: int
    bet_slip_id: int
    
    # Overall metrics
    overall_confidence: Optional[float] = Field(None, ge=0, le=100)
    risk_assessment: Optional[str] = None
    
    # Recommended bets
    recommended_bets: List[int] = Field(default_factory=list)
    parlay_suggestions: Optional[List[Dict[str, Any]]] = None
    
    # Individual prop analyses
    prop_analyses: List[PropAnalysisDetail]
    
    # Metadata
    analysis_notes: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class BetSlipWithAnalysis(BetSlipResponse):
    """Bet slip with analysis results."""
    analysis: Optional[AnalysisResponse] = None
