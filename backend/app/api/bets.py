from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
import logging

from app.database import get_db
from app.models.user import User
from app.models.bet import BetSlip, PropBet, Analysis
from app.services.claude_ocr import claude_ocr_service

logger = logging.getLogger(__name__)
from app.schemas.bet import (
    BetSlipCreate,
    BetSlipResponse,
    BetSlipWithAnalysis,
    PropBetResponse,
    AnalysisResponse,
    PropAnalysisDetail
)
from app.dependencies import get_current_user
from app.core.analysis_engine import analysis_engine, PropBetData

router = APIRouter(prefix="/bets", tags=["Bets"])


@router.post("/upload", response_model=BetSlipResponse, status_code=status.HTTP_201_CREATED)
async def upload_bet_slip_image(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Upload a bet slip image and extract props using Claude OCR.
    
    Args:
        file: Uploaded image file
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Created bet slip with extracted props
    """
    # Validate file type
    if not file.content_type or not file.content_type.startswith('image/'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be an image"
        )
    
    try:
        # Read image data
        image_data = await file.read()
        
        # Extract props using Claude OCR
        props_data = await claude_ocr_service.extract_props_from_image(
            image_data, 
            file.content_type
        )
        
        if not props_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No prop bets could be extracted from the image. Please try manual entry."
            )
        
        # Create bet slip
        bet_slip = BetSlip(
            user_id=current_user.id,
            name=f"Uploaded bet slip - {datetime.utcnow().strftime('%Y-%m-%d %H:%M')}",
            slip_type="image",
            status="pending"
        )
        
        db.add(bet_slip)
        db.flush()
        
        # Create prop bets from extracted data
        for prop_data in props_data:
            prop_bet = PropBet(
                bet_slip_id=bet_slip.id,
                player_name=prop_data['player_name'],
                stat_type=prop_data['stat_type'],
                line=prop_data['line'],
                over_under=prop_data['over_under'],
                opponent_name=prop_data.get('opponent_name'),
                odds=prop_data.get('odds')
            )
            db.add(prop_bet)
        
        db.commit()
        db.refresh(bet_slip)
        
        logger.info(f"Successfully created bet slip {bet_slip.id} with {len(props_data)} props from image")
        
        return bet_slip
        
    except Exception as e:
        logger.error(f"Failed to process bet slip image: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process image: {str(e)}"
        )


@router.post("/", response_model=BetSlipResponse, status_code=status.HTTP_201_CREATED)
async def create_bet_slip(
    bet_slip_data: BetSlipCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new bet slip with prop bets.
    
    Args:
        bet_slip_data: Bet slip creation data
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Created bet slip object
    """
    # Create bet slip
    bet_slip = BetSlip(
        user_id=current_user.id,
        name=bet_slip_data.name,
        slip_type="manual",
        status="pending"
    )
    
    db.add(bet_slip)
    db.flush()  # Get the bet_slip.id
    
    # Create prop bets
    for prop_data in bet_slip_data.prop_bets:
        prop_bet = PropBet(
            bet_slip_id=bet_slip.id,
            player_name=prop_data.player_name,
            stat_type=prop_data.stat_type,
            line=prop_data.line,
            over_under=prop_data.over_under,
            opponent_name=prop_data.opponent_name,
            game_date=prop_data.game_date,
            odds=prop_data.odds
        )
        db.add(prop_bet)
    
    db.commit()
    db.refresh(bet_slip)
    
    return bet_slip


@router.get("/", response_model=List[BetSlipResponse])
def get_user_bet_slips(
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get all bet slips for the current user.
    
    Args:
        skip: Number of records to skip
        limit: Maximum number of records to return
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        List of bet slips
    """
    bet_slips = db.query(BetSlip).filter(
        BetSlip.user_id == current_user.id
    ).order_by(BetSlip.created_at.desc()).offset(skip).limit(limit).all()
    
    return bet_slips


@router.get("/{bet_slip_id}", response_model=BetSlipWithAnalysis)
def get_bet_slip(
    bet_slip_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get a specific bet slip with analysis.
    
    Args:
        bet_slip_id: Bet slip ID
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Bet slip with analysis results
    """
    bet_slip = db.query(BetSlip).filter(
        BetSlip.id == bet_slip_id,
        BetSlip.user_id == current_user.id
    ).first()
    
    if not bet_slip:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bet slip not found"
        )
    
    return bet_slip


@router.post("/{bet_slip_id}/analyze", response_model=AnalysisResponse)
async def analyze_bet_slip(
    bet_slip_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Analyze a bet slip and generate recommendations.
    
    Args:
        bet_slip_id: Bet slip ID to analyze
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Analysis results
    """
    # Fetch bet slip
    bet_slip = db.query(BetSlip).filter(
        BetSlip.id == bet_slip_id,
        BetSlip.user_id == current_user.id
    ).first()
    
    if not bet_slip:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bet slip not found"
        )
    
    # Check if already analyzed
    if bet_slip.status == "analyzed" and bet_slip.analysis:
        # Return existing analysis
        return _format_analysis_response(bet_slip.analysis, bet_slip.prop_bets)
    
    # Prepare prop data for analysis
    prop_data_list = []
    for prop in bet_slip.prop_bets:
        prop_data = PropBetData(
            prop_id=prop.id,
            player_name=prop.player_name,
            player_id=prop.player_id,
            stat_type=prop.stat_type,
            line=prop.line,
            over_under=prop.over_under,
            opponent_name=prop.opponent_name,
            game_date=prop.game_date
        )
        prop_data_list.append(prop_data)
    
    # Run analysis
    analysis_results = await analysis_engine.analyze_bet_slip(prop_data_list)
    
    # Store analysis in database
    # Convert PropAnalysis objects to dicts
    prop_analyses_dict = {}
    for prop_analysis in analysis_results["prop_analyses"]:
        prop_analyses_dict[prop_analysis.prop_id] = {
            "confidence_score": prop_analysis.confidence_score,
            "hit_rate_last_10": prop_analysis.hit_rate_last_10,
            "average_stat": prop_analysis.average_stat,
            "opponent_defensive_rank": prop_analysis.opponent_defensive_rank,
            "pace_adjusted_projection": prop_analysis.pace_adjusted_projection,
            "factors": prop_analysis.factors,
            "recommendation": prop_analysis.recommendation,
            "analysis_notes": prop_analysis.analysis_notes
        }
    
    # Check if analysis already exists
    existing_analysis = db.query(Analysis).filter(
        Analysis.bet_slip_id == bet_slip_id
    ).first()
    
    if existing_analysis:
        # Update existing
        existing_analysis.overall_confidence = analysis_results["overall_confidence"]
        existing_analysis.recommended_bets = analysis_results["recommended_bets"]
        existing_analysis.parlay_suggestions = analysis_results["parlay_suggestions"]
        existing_analysis.risk_assessment = analysis_results["risk_assessment"]
        existing_analysis.prop_analyses = prop_analyses_dict
    else:
        # Create new
        analysis = Analysis(
            bet_slip_id=bet_slip_id,
            overall_confidence=analysis_results["overall_confidence"],
            recommended_bets=analysis_results["recommended_bets"],
            parlay_suggestions=analysis_results["parlay_suggestions"],
            risk_assessment=analysis_results["risk_assessment"],
            prop_analyses=prop_analyses_dict
        )
        db.add(analysis)
    
    # Update bet slip status
    bet_slip.status = "analyzed"
    bet_slip.analyzed_at = datetime.utcnow()
    
    db.commit()
    
    if existing_analysis:
        db.refresh(existing_analysis)
        return _format_analysis_response(existing_analysis, bet_slip.prop_bets)
    else:
        db.refresh(analysis)
        return _format_analysis_response(analysis, bet_slip.prop_bets)


@router.delete("/{bet_slip_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_bet_slip(
    bet_slip_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete a bet slip.
    
    Args:
        bet_slip_id: Bet slip ID to delete
        db: Database session
        current_user: Current authenticated user
    """
    bet_slip = db.query(BetSlip).filter(
        BetSlip.id == bet_slip_id,
        BetSlip.user_id == current_user.id
    ).first()
    
    if not bet_slip:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bet slip not found"
        )
    
    db.delete(bet_slip)
    db.commit()
    
    return None


def _format_analysis_response(analysis: Analysis, prop_bets: List[PropBet]) -> AnalysisResponse:
    """Format analysis database object into response schema."""
    # Build prop bet lookup
    prop_lookup = {prop.id: prop for prop in prop_bets}
    
    # Format individual prop analyses
    prop_analyses = []
    for prop_id_str, prop_analysis_data in (analysis.prop_analyses or {}).items():
        prop_id = int(prop_id_str)
        prop = prop_lookup.get(prop_id)
        
        if prop:
            prop_analysis = PropAnalysisDetail(
                prop_id=prop_id,
                player_name=prop.player_name,
                stat_type=prop.stat_type,
                line=prop.line,
                over_under=prop.over_under,
                confidence_score=prop_analysis_data.get("confidence_score", 50.0),
                hit_rate_last_10=prop_analysis_data.get("hit_rate_last_10", 50.0),
                average_stat=prop_analysis_data.get("average_stat", prop.line),
                opponent_defensive_rank=prop_analysis_data.get("opponent_defensive_rank"),
                pace_adjusted_projection=prop_analysis_data.get("pace_adjusted_projection", prop.line),
                factors=prop_analysis_data.get("factors", {}),
                recommendation=prop_analysis_data.get("recommendation", "neutral"),
                analysis_notes=prop_analysis_data.get("analysis_notes")
            )
            prop_analyses.append(prop_analysis)
    
    return AnalysisResponse(
        id=analysis.id,
        bet_slip_id=analysis.bet_slip_id,
        overall_confidence=analysis.overall_confidence,
        risk_assessment=analysis.risk_assessment,
        recommended_bets=analysis.recommended_bets or [],
        parlay_suggestions=analysis.parlay_suggestions,
        prop_analyses=prop_analyses,
        analysis_notes=analysis.analysis_notes,
        created_at=analysis.created_at
    )
