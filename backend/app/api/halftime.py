"""
Halftime Analysis API endpoints.

Provides real-time halftime analysis for live NBA games.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
import logging

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.models.live_analysis import LiveAnalysisSnapshot, LivePropSuggestion
from app.services.live_data_client import live_data_client, LivePlayerStats
from app.services.balldontlie import balldontlie_service
from app.core.halftime_engine import halftime_engine
from app.core.game_totals_engine import GameTotalsEngine
from app.schemas.halftime import (
    LiveGameResponse,
    LiveBoxScoreResponse,
    LivePlayerStatsResponse,
    TeamInfoResponse,
    HalftimeAnalysisResponse,
    HalftimeSuggestionsResponse,
    HalftimePlayerAnalysisResponse,
    GameTotalAnalysisResponse,
    PropSuggestionResponse,
    SnapshotResponse,
    SnapshotDetailResponse,
    SnapshotCreateRequest,
    EnhancedGameTotalAnalysisResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/halftime", tags=["halftime"])


def _convert_player_stats(stats: LivePlayerStats) -> LivePlayerStatsResponse:
    """Convert LivePlayerStats dataclass to response schema."""
    return LivePlayerStatsResponse(
        player_id=stats.player_id,
        player_name=stats.player_name,
        team_id=stats.team_id,
        team_abbreviation=stats.team_abbreviation,
        minutes=stats.minutes,
        minutes_float=stats.minutes_float,
        points=stats.points,
        rebounds=stats.rebounds,
        assists=stats.assists,
        steals=stats.steals,
        blocks=stats.blocks,
        turnovers=stats.turnovers,
        fouls=stats.fouls,
        fg_made=stats.fg_made,
        fg_attempted=stats.fg_attempted,
        fg_pct=stats.fg_pct,
        fg3_made=stats.fg3_made,
        fg3_attempted=stats.fg3_attempted,
        fg3_pct=stats.fg3_pct,
        ft_made=stats.ft_made,
        ft_attempted=stats.ft_attempted,
        ft_pct=stats.ft_pct,
        plus_minus=stats.plus_minus,
        starter=stats.starter
    )


@router.get("/games/live", response_model=List[LiveGameResponse])
async def get_live_games(
):
    """Get all live NBA games currently in progress."""
    try:
        games = await live_data_client.get_live_games()
        return [
            LiveGameResponse(
                game_id=g.game_id,
                game_status=g.game_status,
                game_status_text=g.game_status_text,
                period=g.period,
                game_clock=g.game_clock,
                home_team_id=g.home_team_id,
                home_team_name=g.home_team_name,
                home_team_abbr=g.home_team_abbr,
                home_score=g.home_score,
                away_team_id=g.away_team_id,
                away_team_name=g.away_team_name,
                away_team_abbr=g.away_team_abbr,
                away_score=g.away_score,
                game_date=g.game_date,
                game_time_utc=g.game_time_utc,
                is_halftime=g.is_halftime,
                score_differential=g.score_differential,
                total_score=g.total_score
            )
            for g in games
        ]
    except Exception as e:
        logger.error(f"Error fetching live games: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch live games")


@router.get("/games/today", response_model=List[LiveGameResponse])
async def get_todays_games(
):
    """Get all of today's NBA games (scheduled, live, and completed)."""
    try:
        games = await live_data_client.get_todays_games()
        return [
            LiveGameResponse(
                game_id=g.game_id,
                game_status=g.game_status,
                game_status_text=g.game_status_text,
                period=g.period,
                game_clock=g.game_clock,
                home_team_id=g.home_team_id,
                home_team_name=g.home_team_name,
                home_team_abbr=g.home_team_abbr,
                home_score=g.home_score,
                away_team_id=g.away_team_id,
                away_team_name=g.away_team_name,
                away_team_abbr=g.away_team_abbr,
                away_score=g.away_score,
                game_date=g.game_date,
                game_time_utc=g.game_time_utc,
                is_halftime=g.is_halftime,
                score_differential=g.score_differential,
                total_score=g.total_score
            )
            for g in games
        ]
    except Exception as e:
        logger.error(f"Error fetching today's games: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch today's games")


@router.get("/games/halftime", response_model=List[LiveGameResponse])
async def get_halftime_games(
):
    """Get only games that are currently at halftime."""
    try:
        games = await live_data_client.get_halftime_games()
        return [
            LiveGameResponse(
                game_id=g.game_id,
                game_status=g.game_status,
                game_status_text=g.game_status_text,
                period=g.period,
                game_clock=g.game_clock,
                home_team_id=g.home_team_id,
                home_team_name=g.home_team_name,
                home_team_abbr=g.home_team_abbr,
                home_score=g.home_score,
                away_team_id=g.away_team_id,
                away_team_name=g.away_team_name,
                away_team_abbr=g.away_team_abbr,
                away_score=g.away_score,
                game_date=g.game_date,
                game_time_utc=g.game_time_utc,
                is_halftime=g.is_halftime,
                score_differential=g.score_differential,
                total_score=g.total_score
            )
            for g in games
        ]
    except Exception as e:
        logger.error(f"Error fetching halftime games: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch halftime games")


@router.get("/games/{game_id}/boxscore", response_model=LiveBoxScoreResponse)
async def get_game_boxscore(
    game_id: str,
):
    """Get the live box score for a specific game."""
    try:
        box_score = await live_data_client.get_live_box_score(game_id)

        if not box_score.get('home') and not box_score.get('away'):
            raise HTTPException(status_code=404, detail="Game not found or no data available")

        home_team = box_score.get('home_team', {})
        away_team = box_score.get('away_team', {})

        return LiveBoxScoreResponse(
            game_id=game_id,
            home_team=TeamInfoResponse(
                team_id=home_team.get('team_id', 0),
                team_name=home_team.get('team_name', ''),
                team_abbr=home_team.get('team_abbr', ''),
                score=home_team.get('score', 0)
            ),
            away_team=TeamInfoResponse(
                team_id=away_team.get('team_id', 0),
                team_name=away_team.get('team_name', ''),
                team_abbr=away_team.get('team_abbr', ''),
                score=away_team.get('score', 0)
            ),
            home_players=[_convert_player_stats(p) for p in box_score.get('home', [])],
            away_players=[_convert_player_stats(p) for p in box_score.get('away', [])]
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching box score for game {game_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch box score")


@router.get("/games/{game_id}/analyze")
async def analyze_halftime_game(
    game_id: str,
):
    """
    Get full halftime analysis for a game.

    Includes:
    - Game total projections (Q3, final)
    - Player prop analysis with projections
    - Confidence scores and recommendations
    - Risk indicators (foul trouble, blowout)
    """
    try:
        analysis = await halftime_engine.get_halftime_analysis(game_id)
        return analysis
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error analyzing game {game_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to analyze game")


@router.get("/games/{game_id}/suggestions", response_model=HalftimeSuggestionsResponse)
async def get_halftime_suggestions(
    game_id: str,
    min_confidence: float = Query(default=60.0, ge=0, le=100),
    prop_type: Optional[str] = Query(default=None, description="Filter by prop type (points, rebounds, assists)"),
):
    """
    Get prop bet suggestions for a game at halftime.

    Filters suggestions by minimum confidence score and optionally by prop type.
    """
    try:
        analysis = await halftime_engine.get_halftime_analysis(game_id)

        suggestions = analysis.get('suggestions', [])

        # Apply filters
        filtered = [
            s for s in suggestions
            if s['confidence_score'] >= min_confidence
            and (prop_type is None or s['prop_type'].lower() == prop_type.lower())
        ]

        return HalftimeSuggestionsResponse(
            game_id=game_id,
            suggestions=[
                PropSuggestionResponse(**s) for s in filtered
            ],
            total_count=len(filtered),
            high_confidence_count=len([s for s in filtered if s['confidence_score'] >= 75]),
            filters_applied={
                'min_confidence': min_confidence,
                'prop_type': prop_type
            }
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting suggestions for game {game_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get suggestions")


@router.get("/games/{game_id}/totals", response_model=EnhancedGameTotalAnalysisResponse)
async def get_game_totals_analysis(
    game_id: str,
    reference_line: Optional[float] = Query(
        default=None,
        description="Vegas total line for O/U edge calculation"
    ),
):
    """
    Get comprehensive game totals analysis including:
    - Advanced pace analysis (possessions-based)
    - Team shooting efficiency with regression signals
    - Star player impact analysis
    - Per-team quarter-by-quarter projections
    - Point spread prediction
    - Over/Under recommendation with edge
    """
    try:
        # Get live game data
        games = await live_data_client.get_todays_games()
        game_data = next((g for g in games if g.game_id == game_id), None)

        if not game_data:
            raise HTTPException(status_code=404, detail=f"Game {game_id} not found")

        if game_data.game_status == 1:
            raise HTTPException(status_code=400, detail="Game has not started yet")

        box_score = await live_data_client.get_live_box_score(game_id)

        if not box_score.get('home') and not box_score.get('away'):
            raise HTTPException(status_code=404, detail="No box score data available")

        # Get team ratings from halftime engine (reuse existing method)
        home_ratings = await halftime_engine._get_team_ratings(
            game_data.home_team_id, game_data.home_team_abbr
        )
        away_ratings = await halftime_engine._get_team_ratings(
            game_data.away_team_id, game_data.away_team_abbr
        )

        # Run enhanced totals analysis
        totals_engine = GameTotalsEngine(
            live_client=live_data_client,
            bdl_service=balldontlie_service
        )
        result = await totals_engine.analyze(
            game_data, box_score, home_ratings, away_ratings,
            reference_line=reference_line
        )

        # Convert dataclass to dict for Pydantic
        return _enhanced_totals_to_response(result)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing game totals for {game_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to analyze game totals")


def _enhanced_totals_to_response(result) -> dict:
    """Convert EnhancedGameTotalProjection dataclass to response dict."""
    from dataclasses import asdict
    data = asdict(result)
    return data


@router.post("/games/{game_id}/snapshot", response_model=SnapshotResponse)
async def save_analysis_snapshot(
    game_id: str,
    db: Session = Depends(get_db)
):
    """
    Save a snapshot of the current halftime analysis.

    Useful for tracking prediction accuracy over time.
    """
    try:
        # Get current analysis
        analysis = await halftime_engine.get_halftime_analysis(game_id)

        game_info = analysis.get('game_info', {})
        game_total = analysis.get('game_total_analysis', {})
        suggestions = analysis.get('suggestions', [])

        # Create snapshot (using default user_id=1 since auth is disabled)
        snapshot = LiveAnalysisSnapshot(
            user_id=1,
            game_id=game_id,
            home_team=game_info.get('home_team_abbr', ''),
            away_team=game_info.get('away_team_abbr', ''),
            home_score=game_info.get('home_score', 0),
            away_score=game_info.get('away_score', 0),
            period=game_info.get('period', 0),
            game_clock=game_info.get('game_clock', ''),
            analysis_data=analysis,
            total_suggestions=len(suggestions),
            high_confidence_count=len([s for s in suggestions if s['confidence_score'] >= 75]),
            projected_game_total=game_total.get('projected_final_total'),
            projected_q3_total=game_total.get('projected_q3_total'),
        )
        db.add(snapshot)
        db.flush()

        # Save individual suggestions for tracking
        for suggestion in suggestions:
            prop_suggestion = LivePropSuggestion(
                snapshot_id=snapshot.id,
                player_name=suggestion['player_name'],
                team_abbreviation=suggestion['team_abbreviation'],
                prop_type=suggestion['prop_type'],
                prop_line=suggestion['prop_line'],
                over_under='over',
                first_half_value=suggestion['current_value'],
                first_half_minutes=0,  # Would need to look up
                projected_final=suggestion['projected_final'],
                confidence_score=suggestion['confidence_score'],
                recommendation=suggestion['recommendation'],
                foul_trouble='foul trouble' in ' '.join(suggestion.get('key_factors', [])).lower(),
                blowout_warning='blowout' in ' '.join(suggestion.get('key_factors', [])).lower(),
            )
            db.add(prop_suggestion)

        db.commit()
        db.refresh(snapshot)

        return SnapshotResponse(
            id=snapshot.id,
            game_id=snapshot.game_id,
            home_team=snapshot.home_team,
            away_team=snapshot.away_team,
            home_score=snapshot.home_score,
            away_score=snapshot.away_score,
            total_suggestions=snapshot.total_suggestions,
            high_confidence_count=snapshot.high_confidence_count,
            snapshot_time=snapshot.snapshot_time
        )

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error saving snapshot for game {game_id}: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to save snapshot")


@router.get("/snapshots", response_model=List[SnapshotResponse])
async def get_user_snapshots(
    limit: int = Query(default=20, le=100),
    db: Session = Depends(get_db)
):
    """Get user's saved analysis snapshots."""
    snapshots = db.query(LiveAnalysisSnapshot)\
        .filter(LiveAnalysisSnapshot.user_id == 1)\
        .order_by(LiveAnalysisSnapshot.snapshot_time.desc())\
        .limit(limit)\
        .all()

    return [
        SnapshotResponse(
            id=s.id,
            game_id=s.game_id,
            home_team=s.home_team,
            away_team=s.away_team,
            home_score=s.home_score,
            away_score=s.away_score,
            total_suggestions=s.total_suggestions,
            high_confidence_count=s.high_confidence_count,
            snapshot_time=s.snapshot_time
        )
        for s in snapshots
    ]


@router.get("/snapshots/{snapshot_id}", response_model=SnapshotDetailResponse)
async def get_snapshot_detail(
    snapshot_id: int,
    db: Session = Depends(get_db)
):
    """Get detailed snapshot including full analysis data."""
    snapshot = db.query(LiveAnalysisSnapshot)\
        .filter(
            LiveAnalysisSnapshot.id == snapshot_id,
            LiveAnalysisSnapshot.user_id == 1
        )\
        .first()

    if not snapshot:
        raise HTTPException(status_code=404, detail="Snapshot not found")

    suggestions = snapshot.analysis_data.get('suggestions', [])

    return SnapshotDetailResponse(
        id=snapshot.id,
        game_id=snapshot.game_id,
        home_team=snapshot.home_team,
        away_team=snapshot.away_team,
        home_score=snapshot.home_score,
        away_score=snapshot.away_score,
        total_suggestions=snapshot.total_suggestions,
        high_confidence_count=snapshot.high_confidence_count,
        snapshot_time=snapshot.snapshot_time,
        analysis_data=snapshot.analysis_data,
        suggestions=[PropSuggestionResponse(**s) for s in suggestions]
    )


@router.delete("/snapshots/{snapshot_id}")
async def delete_snapshot(
    snapshot_id: int,
    db: Session = Depends(get_db)
):
    """Delete a saved snapshot."""
    snapshot = db.query(LiveAnalysisSnapshot)\
        .filter(
            LiveAnalysisSnapshot.id == snapshot_id,
            LiveAnalysisSnapshot.user_id == 1
        )\
        .first()

    if not snapshot:
        raise HTTPException(status_code=404, detail="Snapshot not found")

    db.delete(snapshot)
    db.commit()

    return {"message": "Snapshot deleted successfully"}
