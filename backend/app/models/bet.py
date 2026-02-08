from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, JSON, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class BetSlip(Base):
    """Bet slip submitted by user for analysis."""
    
    __tablename__ = "bet_slips"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String, nullable=True)  # User can name their bet slip
    slip_type = Column(String, default="manual")  # manual, ocr, etc.
    image_url = Column(String, nullable=True)  # If uploaded image
    status = Column(String, default="pending")  # pending, analyzed, failed
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    analyzed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="bet_slips")
    prop_bets = relationship("PropBet", back_populates="bet_slip", cascade="all, delete-orphan")
    analysis = relationship("Analysis", back_populates="bet_slip", uselist=False, cascade="all, delete-orphan")


class PropBet(Base):
    """Individual prop bet within a bet slip."""
    
    __tablename__ = "prop_bets"
    
    id = Column(Integer, primary_key=True, index=True)
    bet_slip_id = Column(Integer, ForeignKey("bet_slips.id"), nullable=False)
    
    # Prop details
    player_name = Column(String, nullable=False)
    player_id = Column(Integer, nullable=True)  # BallDontLie player ID if found
    team_name = Column(String, nullable=True)
    opponent_name = Column(String, nullable=True)
    stat_type = Column(String, nullable=False)  # points, rebounds, assists, etc.
    line = Column(Float, nullable=False)
    over_under = Column(String, nullable=False)  # over or under
    game_date = Column(DateTime(timezone=True), nullable=True)
    game_id = Column(Integer, nullable=True)  # BallDontLie game ID if found
    
    # Odds (if available)
    odds = Column(Integer, nullable=True)  # American odds format
    
    # Relationships
    bet_slip = relationship("BetSlip", back_populates="prop_bets")


class Analysis(Base):
    """Analysis results for a bet slip."""
    
    __tablename__ = "analyses"
    
    id = Column(Integer, primary_key=True, index=True)
    bet_slip_id = Column(Integer, ForeignKey("bet_slips.id"), nullable=False, unique=True)
    
    # Overall analysis
    overall_confidence = Column(Float, nullable=True)  # 0-100
    recommended_bets = Column(JSON, nullable=True)  # List of prop IDs to bet
    parlay_suggestions = Column(JSON, nullable=True)  # Suggested parlay combinations
    risk_assessment = Column(String, nullable=True)  # low, medium, high
    
    # Individual prop analyses (stored as JSON)
    # Format: {prop_id: {confidence, hit_rate, factors, recommendation, etc.}}
    prop_analyses = Column(JSON, nullable=True)
    
    # Analysis metadata
    analysis_notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    bet_slip = relationship("BetSlip", back_populates="analysis")
