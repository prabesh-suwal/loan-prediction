from typing import Dict, Any, List, Optional
import logging
from datetime import datetime, timedelta

from app.core.repositories.weight_repository import WeightRepository
from app.core.repositories.loan_repository import LoanRepository
from app.ml.models.trainer import ModelTrainer
from app.utils.exceptions import ValidationError

logger = logging.getLogger(__name__)

class AdminService:
    """Service for admin operations."""
    
    def __init__(
        self,
        weight_repository: WeightRepository,
        loan_repository: LoanRepository,
        model_trainer: ModelTrainer
    ):
        self.weight_repository = weight_repository
        self.loan_repository = loan_repository
        self.model_trainer = model_trainer
    
    async def update_feature_weight(
        self, 
        feature_name: str, 
        weight: float, 
        description: str = None
    ) -> bool:
        """Update feature weight configuration."""
        
        if weight <= 0 or weight > 10:
            raise ValidationError("Weight must be between 0 and 10")
        
        return await self.weight_repository.update_weight(
            feature_name, weight, description
        )
    
    async def get_all_feature_weights(self) -> List[Dict[str, Any]]:
        """Get all feature weights."""
        return await self.weight_repository.get_all_weights()
    
    async def get_model_performance_report(self) -> Dict[str, Any]:
        """Generate comprehensive model performance report."""
        
        # Get basic metrics
        basic_metrics = await self.loan_repository.get_model_metrics()
        
        # Get applications for detailed analysis
        applications = await self.loan_repository.get_applications_for_retraining()
        
        if not applications:
            return {
                "error": "No applications with admin decisions found",
                "basic_metrics": basic_metrics
            }
        
        # Calculate detailed metrics
        approved_apps = [app for app in applications if app['final_status'] == 'Yes']
        rejected_apps = [app for app in applications if app['final_status'] == 'No']
        
        # Accuracy by risk category
        risk_accuracy = {}
        for risk_cat in ['Low', 'Medium', 'High']:
            cat_apps = [app for app in applications if app['risk_category'] == risk_cat]
            if cat_apps:
                correct = sum(
                    1 for app in cat_apps 
                    if app['predicted_approval'] == app['final_status']
                )
                risk_accuracy[risk_cat] = correct / len(cat_apps)
        
        # Model drift indicators
        recent_apps = [
            app for app in applications 
            if app['created_at'] and 
            datetime.fromisoformat(app['created_at'].replace('Z', '+00:00')) > 
            datetime.now() - timedelta(days=7)
        ]
        
        drift_score = 0
        if recent_apps and len(applications) > len(recent_apps):
            recent_accuracy = sum(
                1 for app in recent_apps 
                if app['predicted_approval'] == app['final_status']
            ) / len(recent_apps)
            
            overall_accuracy = basic_metrics.get('accuracy', 0)
            drift_score = abs(recent_accuracy - overall_accuracy)
        
        return {
            "basic_metrics": basic_metrics,
            "total_applications": len(applications),
            "approved_applications": len(approved_apps),
            "rejected_applications": len(rejected_apps),
            "accuracy_by_risk": risk_accuracy,
            "model_drift_score": drift_score,
            "recommendation": self._get_retraining_recommendation(
                basic_metrics.get('accuracy', 0), drift_score, len(applications)
            )
        }
    
    async def trigger_model_retraining(self) -> Dict[str, Any]:
        """Trigger model retraining with latest data."""
        
        try:
            # Get training data
            training_data = await self.loan_repository.get_applications_for_retraining()
            
            if len(training_data) < 50:
                return {
                    "success": False,
                    "message": "Insufficient training data (minimum 50 samples required)",
                    "sample_count": len(training_data)
                }
            
            # Train new model
            result = await self.model_trainer.retrain_model(training_data)
            
            logger.info(f"Model retraining completed: {result}")
            return {
                "success": True,
                "message": "Model retraining completed successfully",
                "metrics": result
            }
            
        except Exception as e:
            logger.error(f"Model retraining failed: {e}")
            return {
                "success": False,
                "message": f"Model retraining failed: {str(e)}"
            }
    
    def _get_retraining_recommendation(
        self, 
        accuracy: float, 
        drift_score: float, 
        sample_count: int
    ) -> str:
        """Get recommendation for model retraining."""
        
        if accuracy < 0.7:
            return "URGENT: Model accuracy is below 70%. Immediate retraining recommended."
        elif drift_score > 0.1:
            return "WARNING: Significant model drift detected. Retraining recommended."
        elif sample_count > 500 and accuracy < 0.85:
            return "ADVISORY: Consider retraining to improve model performance."
        else:
            return "OK: Model performance is acceptable. Continue monitoring."
