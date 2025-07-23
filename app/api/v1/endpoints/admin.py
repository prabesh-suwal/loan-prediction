from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, Any

from app.core.models.schemas import FeatureWeightUpdate
from app.core.services.admin_service import AdminService
from app.core.repositories.weight_repository import WeightRepository
from app.core.repositories.loan_repository import LoanRepository
from app.ml.models.trainer import ModelTrainer
from app.config.database import get_db

router = APIRouter()

def get_admin_service(db: Session = Depends(get_db)) -> AdminService:
    """Dependency to get admin service."""
    weight_repo = WeightRepository(db)
    loan_repo = LoanRepository(db)
    trainer = ModelTrainer()
    return AdminService(weight_repo, loan_repo, trainer)

@router.get("/feature-weights")
async def get_feature_weights(
    service: AdminService = Depends(get_admin_service)
):
    """Get all feature weights."""
    return await service.get_all_feature_weights()

@router.put("/feature-weights")
async def update_feature_weight(
    weight_update: FeatureWeightUpdate,
    service: AdminService = Depends(get_admin_service)
):
    """Update a feature weight."""
    success = await service.update_feature_weight(
        weight_update.feature_name,
        weight_update.weight,
        weight_update.description
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to update feature weight"
        )
    
    return {"message": "Feature weight updated successfully"}

@router.get("/model/performance")
async def get_model_performance(
    service: AdminService = Depends(get_admin_service)
):
    """Get model performance report."""
    return await service.get_model_performance_report()

@router.post("/model/retrain")
async def trigger_model_retraining(
    service: AdminService = Depends(get_admin_service)
):
    """Trigger model retraining."""
    return await service.trigger_model_retraining()
