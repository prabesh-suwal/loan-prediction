import uuid
from typing import Dict, Any, Optional
from datetime import datetime
import logging

from app.core.models.schemas import (
    LoanApplicationInput, 
    LoanPredictionResponse, 
    RiskCategory, 
    LoanDecision, 
    Recommendation
)
from app.core.repositories.loan_repository import LoanRepository
from app.core.repositories.weight_repository import WeightRepository
from app.ml.models.predictor import LoanPredictor
from app.ml.explainer.llm_explainer import LLMExplainer
from app.utils.validators import LoanValidator
from app.utils.exceptions import PredictionError, ValidationError

logger = logging.getLogger(__name__)

class LoanService:
    """Business logic for loan approval process."""
    
    def __init__(
        self,
        loan_repository: LoanRepository,
        weight_repository: WeightRepository,
        predictor: LoanPredictor,
        explainer: LLMExplainer
    ):
        self.loan_repository = loan_repository
        self.weight_repository = weight_repository
        self.predictor = predictor
        self.explainer = explainer
        self.validator = LoanValidator()
    
    async def process_loan_application(
        self, 
        application_data: LoanApplicationInput
    ) -> LoanPredictionResponse:
        """Process a new loan application."""
        
        try:
            # Generate unique application ID
            application_id = f"LOAN_{datetime.now().strftime('%Y%m%d')}_{uuid.uuid4().hex[:8].upper()}"
            
            # Validate input data
            self.validator.validate_loan_application(application_data.dict())
            
            # Get current feature weights from admin
            weights = await self.weight_repository.get_active_weights()
            
            # Convert to dictionary for ML processing
            input_dict = application_data.dict()
            
            # Make ML prediction
            prediction_result = self.predictor.predict(input_dict, weights)
            
            # Generate explanation
            explanation = self.explainer.generate_explanation(
                input_dict, 
                prediction_result
            )
            
            # Create response
            response = LoanPredictionResponse(
                application_id=application_id,
                loan_decision=LoanDecision(prediction_result['loan_decision']),
                risk_score=prediction_result['risk_score'],
                risk_category=RiskCategory(prediction_result['risk_category']),
                justification=explanation,
                recommendation=Recommendation(prediction_result['recommendation']),
                confidence_score=prediction_result.get('confidence_score')
            )
            
            # Save to database
            await self.loan_repository.create_application(
                application_id=application_id,
                input_data=input_dict,
                prediction_result=prediction_result,
                justification=explanation
            )
            
            logger.info(f"Processed loan application {application_id}")
            return response
            
        except ValidationError as e:
            logger.error(f"Validation error: {e}")
            raise
        except Exception as e:
            logger.error(f"Error processing loan application: {e}")
            raise PredictionError(f"Failed to process application: {str(e)}")
    
    async def get_application_details(self, application_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a loan application."""
        return await self.loan_repository.get_application_by_id(application_id)
    
    async def update_admin_decision(
        self, 
        application_id: str, 
        final_status: str, 
        admin_notes: Optional[str] = None
    ) -> bool:
        """Update application with admin override decision."""
        
        try:
            success = await self.loan_repository.update_admin_decision(
                application_id, final_status, admin_notes
            )
            
            if success:
                logger.info(f"Admin decision updated for {application_id}: {final_status}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error updating admin decision: {e}")
            return False
    
    async def get_applications_for_review(
        self, 
        limit: int = 50, 
        offset: int = 0
    ) -> Dict[str, Any]:
        """Get applications that need admin review."""
        return await self.loan_repository.get_applications_for_review(limit, offset)
    
    async def get_model_performance_metrics(self) -> Dict[str, Any]:
        """Get current model performance metrics."""
        return await self.loan_repository.get_model_metrics()