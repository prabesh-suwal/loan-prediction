from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Dict, Any

from app.core.models.schemas import (
    LoanApplicationInput, 
    LoanPredictionResponse, 
    AdminOverride
)
from app.core.services.loan_service import LoanService
from app.core.repositories.loan_repository import LoanRepository
from app.core.repositories.weight_repository import WeightRepository
from app.ml.models.predictor import LoanPredictor
from app.ml.explainer.llm_explainer import LLMExplainer
from app.config.database import get_db
from app.utils.exceptions import ValidationError, PredictionError

router = APIRouter()

def get_loan_service(db: Session = Depends(get_db)) -> LoanService:
    """Dependency to get loan service."""
    from app.main import app
    
    loan_repo = LoanRepository(db)
    weight_repo = WeightRepository(db)
    predictor = app.state.predictor
    explainer = LLMExplainer()
    
    return LoanService(loan_repo, weight_repo, predictor, explainer)

@router.post("/predict", response_model=LoanPredictionResponse)
async def predict_loan_approval(
    application: LoanApplicationInput,
    service: LoanService = Depends(get_loan_service)
):
    """Predict loan approval for a new application."""
    
    try:
        result = await service.process_loan_application(application)
        return result
        
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except PredictionError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/applications/{application_id}")
async def get_application(
    application_id: str,
    service: LoanService = Depends(get_loan_service)
):
    """Get details of a specific loan application."""
    
    application = await service.get_application_details(application_id)
    
    if not application:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found"
        )
    
    return application

@router.put("/applications/{application_id}/admin-decision")
async def update_admin_decision(
    application_id: str,
    override: AdminOverride,
    service: LoanService = Depends(get_loan_service)
):
    """Update application with admin override decision."""
    
    success = await service.update_admin_decision(
        application_id=application_id,
        final_status=override.final_status,
        admin_notes=override.admin_notes
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found or update failed"
        )
    
    return {"message": "Admin decision updated successfully"}

@router.get("/applications/review/pending")
async def get_pending_applications(
    limit: int = 50,
    offset: int = 0,
    service: LoanService = Depends(get_loan_service)
):
    """Get applications pending admin review."""
    
    result = await service.get_applications_for_review(limit, offset)
    return result

@router.get("/metrics/model-performance")
async def get_model_performance(
    service: LoanService = Depends(get_loan_service)
):
    """Get current model performance metrics."""
    
    metrics = await service.get_model_performance_metrics()
    return metrics
