import uuid
from typing import Dict, Any, Optional
from datetime import datetime
import logging

from app.core.models.schemas import (
    LoanApplicationInput, 
    LoanPredictionResponse
)
from app.core.repositories.loan_repository import LoanRepository
from app.core.repositories.weight_repository import WeightRepository
from app.ml.models.predictor import LoanPredictor
from app.ml.explainer.llm_explainer import LLMExplainer
from app.utils.exceptions import PredictionError, ValidationError

logger = logging.getLogger(__name__)

class LoanService:
    """
    Enhanced business logic for loan approval process using unified predictor.
    
    Features:
    - Unified ML/fallback prediction handling
    - Comprehensive input validation
    - Detailed logging and error handling
    - Performance tracking
    - Graceful degradation
    """
    
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
    
    async def process_loan_application(
        self, 
        application_data: LoanApplicationInput
    ) -> LoanPredictionResponse:
        """
        Process a loan application with comprehensive analysis.
        
        Args:
            application_data: Validated loan application input
            
        Returns:
            Comprehensive loan prediction response
            
        Raises:
            ValidationError: If input validation fails
            PredictionError: If prediction process fails
        """
        
        start_time = datetime.now()
        
        try:
            # Generate unique application ID
            application_id = f"LOAN_{datetime.now().strftime('%Y%m%d')}_{uuid.uuid4().hex[:8].upper()}"
            logger.info(f"🏦 Processing loan application: {application_id}")
            
            # Convert to dictionary for processing
            input_dict = application_data.model_dump()
            
            # Enhanced input validation using predictor
            if self.predictor:
                is_valid, validation_errors = self.predictor.validate_input(input_dict)
                if not is_valid:
                    raise ValidationError(f"Input validation failed: {'; '.join(validation_errors)}")
            
            # Get current feature weights from admin configuration
            weights = {}
            try:
                weights = await self.weight_repository.get_active_weights()
                logger.debug(f"Retrieved {len(weights)} feature weights")
            except Exception as e:
                logger.warning(f"Could not retrieve feature weights: {e}")
            
            # Make prediction using unified predictor
            if not self.predictor:
                raise PredictionError("Predictor not available")
            
            prediction_result = await self.predictor.predict(input_dict, weights)
            
            # Log prediction details
            logger.info(f"✅ Prediction completed for {application_id}")
            logger.info(f"   Decision: {prediction_result.get('loan_decision')}")
            logger.info(f"   Risk Score: {prediction_result.get('risk_score')}")
            logger.info(f"   Method: {prediction_result.get('prediction_method', 'unknown')}")
            logger.info(f"   Processing Time: {prediction_result.get('processing_time_ms', 0)}ms")
            
            # Generate explanation using LLM if available
            explanation = await self._generate_explanation(input_dict, prediction_result)
            
            # Create comprehensive response
            response = self._build_response(
                application_id, 
                prediction_result, 
                explanation
            )
            
            # Save to database (non-blocking - don't fail if DB save fails)
            await self._save_application_async(
                application_id,
                input_dict,
                prediction_result,
                explanation
            )
            
            # Log final processing time
            total_time = (datetime.now() - start_time).total_seconds()
            logger.info(f"🎯 Application {application_id} processed in {total_time:.3f}s")
            
            return response
            
        except ValidationError as e:
            logger.error(f"❌ Validation error for application: {e}")
            raise
        except PredictionError as e:
            logger.error(f"❌ Prediction error for application: {e}")
            raise
        except Exception as e:
            logger.error(f"❌ Unexpected error processing loan application: {e}")
            raise PredictionError(f"Failed to process application: {str(e)}")
    
    async def _generate_explanation(
        self, 
        input_data: Dict[str, Any], 
        prediction_result: Dict[str, Any]
    ) -> str:
        """Generate human-readable explanation for the decision."""
        
        try:
            if self.explainer:
                explanation = self.explainer.generate_explanation(input_data, prediction_result)
                logger.debug("✅ LLM explanation generated")
                return explanation
        except Exception as e:
            logger.warning(f"LLM explanation failed: {e}")
        
        # Fallback to rule-based explanation
        return self._generate_fallback_explanation(prediction_result)
    
    def _generate_fallback_explanation(self, prediction_result: Dict[str, Any]) -> str:
        """Generate rule-based explanation as fallback."""
        
        decision = prediction_result.get('loan_decision', 'Unknown')
        risk_score = prediction_result.get('risk_score', 0)
        risk_factors = prediction_result.get('key_risk_factors', [])
        positive_factors = prediction_result.get('key_positive_factors', [])
        
        if decision == "Yes":
            explanation = f"Loan approved with risk score {risk_score}/100. "
            if positive_factors:
                explanation += f"Key strengths: {', '.join(positive_factors[:3])}. "
            if risk_factors:
                explanation += f"Areas to monitor: {', '.join(risk_factors[:2])}."
        else:
            explanation = f"Loan rejected due to high risk score {risk_score}/100. "
            if risk_factors:
                explanation += f"Primary concerns: {', '.join(risk_factors[:3])}. "
            explanation += "Consider improving financial profile before reapplying."
        
        return explanation.strip()
    
    def _build_response(
        self, 
        application_id: str, 
        prediction_result: Dict[str, Any], 
        explanation: str
    ) -> LoanPredictionResponse:
        """Build comprehensive loan prediction response."""
        
        return LoanPredictionResponse(
            application_id=application_id,
            loan_decision=prediction_result['loan_decision'],
            risk_score=prediction_result['risk_score'],
            risk_category=prediction_result['risk_category'],
            justification=explanation,
            recommendation=prediction_result['recommendation'],
            confidence_score=prediction_result.get('confidence_score'),
            key_risk_factors=prediction_result.get('key_risk_factors', []),
            key_positive_factors=prediction_result.get('key_positive_factors', []),
            suggested_loan_amount=prediction_result.get('suggested_loan_amount'),
            debt_to_income_ratio=prediction_result.get('debt_to_income_ratio'),
            credit_risk_score=prediction_result.get('credit_risk_score'),
            income_risk_score=prediction_result.get('income_risk_score'),
            employment_risk_score=prediction_result.get('employment_risk_score')
        )
    
    async def _save_application_async(
        self,
        application_id: str,
        input_data: Dict[str, Any],
        prediction_result: Dict[str, Any],
        explanation: str
    ):
        """Save application to database with error handling."""
        
        try:
            saved_application = await self.loan_repository.create_application(
                application_id=application_id,
                input_data=input_data,
                prediction_result=prediction_result,
                justification=explanation
            )
            
            if saved_application:
                logger.info(f"💾 Application {application_id} saved to database")
            else:
                logger.warning(f"⚠️  Failed to save application {application_id} to database")
                
        except Exception as e:
            logger.error(f"❌ Database save failed for {application_id}: {e}")
            # Don't fail the request if database save fails
    
    async def get_application_details(self, application_id: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a loan application.
        
        Args:
            application_id: Unique application identifier
            
        Returns:
            Application details or None if not found
        """
        
        try:
            logger.info(f"🔍 Retrieving application details: {application_id}")
            application = await self.loan_repository.get_application_by_id(application_id)
            
            if application:
                logger.info(f"✅ Application {application_id} found")
            else:
                logger.warning(f"⚠️  Application {application_id} not found")
                
            return application
            
        except Exception as e:
            logger.error(f"❌ Error getting application details for {application_id}: {e}")
            return None
    
    async def update_admin_decision(
        self, 
        application_id: str, 
        final_status: str, 
        admin_notes: Optional[str] = None
    ) -> bool:
        """
        Update application with admin override decision.
        
        Args:
            application_id: Unique application identifier
            final_status: Admin final decision (Yes/No)
            admin_notes: Optional admin notes
            
        Returns:
            True if update successful, False otherwise
        """
        
        try:
            logger.info(f"👨‍💼 Admin override for {application_id}: {final_status}")
            
            success = await self.loan_repository.update_admin_decision(
                application_id, final_status, admin_notes
            )
            
            if success:
                logger.info(f"✅ Admin decision updated for {application_id}")
            else:
                logger.warning(f"⚠️  Failed to update admin decision for {application_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"❌ Error updating admin decision for {application_id}: {e}")
            return False
    
    async def get_applications_for_review(
        self, 
        limit: int = 50, 
        offset: int = 0
    ) -> Dict[str, Any]:
        """
        Get applications that need admin review.
        
        Args:
            limit: Maximum number of applications to return
            offset: Number of applications to skip
            
        Returns:
            Dictionary with applications list and pagination info
        """
        
        try:
            logger.info(f"📋 Getting applications for review (limit={limit}, offset={offset})")
            
            result = await self.loan_repository.get_applications_for_review(limit, offset)
            
            logger.info(f"✅ Retrieved {len(result.get('applications', []))} applications for review")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Error getting applications for review: {e}")
            return {"applications": [], "total_count": 0, "has_more": False}
    
    async def get_model_performance_metrics(self) -> Dict[str, Any]:
        """
        Get comprehensive model performance metrics.
        
        Returns:
            Dictionary with performance metrics and predictor statistics
        """
        
        try:
            logger.info("📊 Retrieving model performance metrics")
            
            # Get database metrics
            db_metrics = await self.loan_repository.get_model_metrics()
            
            # Get predictor statistics if available
            predictor_stats = {}
            if self.predictor:
                predictor_info = self.predictor.get_model_info()
                predictor_stats = {
                    'predictor_loaded': predictor_info.get('model_loaded', False),
                    'prediction_method': 'ml' if predictor_info.get('model_loaded') else 'fallback',
                    'total_predictions': predictor_info.get('prediction_count', 0),
                    'performance_stats': predictor_info.get('performance_stats', {}),
                    'average_prediction_time_ms': int(
                        predictor_info.get('performance_stats', {}).get('avg_prediction_time', 0) * 1000
                    )
                }
            
            # Combine metrics
            combined_metrics = {
                'database_metrics': db_metrics,
                'predictor_metrics': predictor_stats,
                'system_health': {
                    'predictor_available': self.predictor is not None,
                    'database_accessible': db_metrics.get('total_applications', 0) >= 0
                },
                'generated_at': datetime.utcnow().isoformat()
            }
            
            logger.info("✅ Performance metrics retrieved successfully")
            return combined_metrics
            
        except Exception as e:
            logger.error(f"❌ Error getting model performance metrics: {e}")
            return {
                'database_metrics': {"accuracy": None, "total_applications": 0, "error": str(e)},
                'predictor_metrics': {},
                'system_health': {'predictor_available': False, 'database_accessible': False},
                'error': str(e)
            }
    
    async def validate_system_health(self) -> Dict[str, Any]:
        """
        Validate overall system health including predictor and database.
        
        Returns:
            Dictionary with comprehensive health status
        """
        
        health_status = {
            'overall_status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'components': {}
        }
        
        # Check predictor health
        if self.predictor:
            try:
                predictor_health = await self.predictor.health_check()
                health_status['components']['predictor'] = predictor_health
            except Exception as e:
                health_status['components']['predictor'] = {
                    'status': 'error',
                    'error': str(e)
                }
                health_status['overall_status'] = 'degraded'
        else:
            health_status['components']['predictor'] = {'status': 'not_available'}
            health_status['overall_status'] = 'degraded'
        
        # Check database health
        try:
            db_metrics = await self.loan_repository.get_model_metrics()
            health_status['components']['database'] = {
                'status': 'healthy',
                'total_applications': db_metrics.get('total_applications', 0)
            }
        except Exception as e:
            health_status['components']['database'] = {
                'status': 'error',
                'error': str(e)
            }
            health_status['overall_status'] = 'unhealthy'
        
        # Check feature weights
        try:
            weights = await self.weight_repository.get_active_weights()
            health_status['components']['feature_weights'] = {
                'status': 'healthy',
                'count': len(weights)
            }
        except Exception as e:
            health_status['components']['feature_weights'] = {
                'status': 'error',
                'error': str(e)
            }
        
        return health_status