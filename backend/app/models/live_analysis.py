"""
Database models for live halftime analysis.
"""
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, JSON, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class LiveAnalysisSnapshot(Base):
    """Stores analysis snapshots taken at halftime."""

    __tablename__ = "live_analysis_snapshots"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    game_id = Column(String, nullable=False, index=True)

    # Game info at snapshot time
    home_team = Column(String, nullable=False)
    away_team = Column(String, nullable=False)
    home_score = Column(Integer, nullable=False)
    away_score = Column(Integer, nullable=False)
    period = Column(Integer, nullable=False)
    game_clock = Column(String, nullable=True)

    # Full analysis data as JSON
    analysis_data = Column(JSON, nullable=False)

    # Summary metrics
    total_suggestions = Column(Integer, default=0)
    high_confidence_count = Column(Integer, default=0)
    projected_game_total = Column(Float, nullable=True)
    projected_q3_total = Column(Float, nullable=True)

    # Timestamps
    snapshot_time = Column(DateTime(timezone=True), server_default=func.now())

    # Relationship
    user = relationship("User", back_populates="live_snapshots")
    suggestions = relationship("LivePropSuggestion", back_populates="snapshot", cascade="all, delete-orphan")


class LivePropSuggestion(Base):
    """Individual prop suggestion from halftime analysis - tracks prediction accuracy."""

    __tablename__ = "live_prop_suggestions"

    id = Column(Integer, primary_key=True, index=True)
    snapshot_id = Column(Integer, ForeignKey("live_analysis_snapshots.id"), nullable=False)

    # Player/Prop info
    player_name = Column(String, nullable=False)
    player_id = Column(Integer, nullable=True)
    team_abbreviation = Column(String, nullable=True)
    prop_type = Column(String, nullable=False)  # points, rebounds, assists, etc.
    prop_line = Column(Float, nullable=False)
    over_under = Column(String, nullable=False)  # over or under

    # First half stats
    first_half_value = Column(Float, nullable=False)
    first_half_minutes = Column(Float, nullable=False)

    # Projections
    projected_final = Column(Float, nullable=False)
    confidence_score = Column(Float, nullable=False)
    recommendation = Column(String, nullable=False)  # strong_bet, bet, lean, neutral, avoid

    # Risk indicators
    foul_trouble = Column(Boolean, default=False)
    blowout_warning = Column(Boolean, default=False)
    pace_factor = Column(Float, nullable=True)
    utilization_rate = Column(Float, nullable=True)
    fatigue_factor = Column(Float, nullable=True)

    # Actual result (filled in after game)
    actual_final = Column(Float, nullable=True)
    hit = Column(Boolean, nullable=True)
    verified_at = Column(DateTime(timezone=True), nullable=True)

    # Relationship
    snapshot = relationship("LiveAnalysisSnapshot", back_populates="suggestions")
