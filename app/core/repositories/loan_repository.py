from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_, func
from datetime import datetime, timedelta

from app.core.models.database import LoanApplication, ModelMetrics
from app.config.database import get_db
import logging

logger = logging.getLogger(__name__)

class LoanRepository:
    """Data access layer for loan operations."""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def create_application(
        self,
        application_id: str,
        input_data: Dict[str, Any],
        prediction_result: Dict[str, Any],
        justification: str
    ) -> Optional[LoanApplication]:
        """Create a new loan application record."""
        
        try:
            # Calculate derived features
            total_income = input_data.get('applicant_income', 0) + input_data.get('coapplicant_income', 0)
            loan_amount = input_data.get('loan_amount', 0)
            loan_term = input_data.get('loan_amount_term', 1)
            emi = (loan_amount * 1000) / loan_term if loan_term > 0 else 0  # Convert to actual EMI
            emi_income_ratio = emi / (total_income / 12) if total_income > 0 else 0
            
            application = LoanApplication(
                application_id=application_id,
                gender=input_data.get('gender'),
                married=input_data.get('married'),
                dependents=input_data.get('dependents'),
                education=input_data.get('education'),
                self_employed=input_data.get('self_employed'),
                applicant_income=input_data.get('applicant_income'),
                coapplicant_income=input_data.get('coapplicant_income'),
                loan_amount=input_data.get('loan_amount'),
                loan_amount_term=input_data.get('loan_amount_term'),
                credit_history=input_data.get('credit_history'),
                property_area=input_data.get('property_area'),
                total_income=total_income,
                emi=emi,
                emi_income_ratio=emi_income_ratio,
                predicted_approval=prediction_result.get('loan_decision'),
                risk_score=prediction_result.get('risk_score'),
                risk_category=prediction_result.get('risk_category'),
                ml_justification=justification,
                recommendation=prediction_result.get('recommendation'),
                confidence_score=prediction_result.get('confidence_score')
            )
            
            self.db.add(application)
            self.db.commit()
            self.db.refresh(application)
            
            logger.info(f"Successfully created loan application: {application_id}")
            return application
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating application {application_id}: {e}")
            return None
    
    async def get_application_by_id(self, application_id: str) -> Optional[Dict[str, Any]]:
        """Get application by ID."""
        
        try:
            application = self.db.query(LoanApplication).filter(
                LoanApplication.application_id == application_id
            ).first()
            
            if application:
                return {
                    "application_id": application.application_id,
                    "gender": application.gender,
                    "married": application.married,
                    "dependents": application.dependents,
                    "education": application.education,
                    "self_employed": application.self_employed,
                    "applicant_income": application.applicant_income,
                    "coapplicant_income": application.coapplicant_income,
                    "loan_amount": application.loan_amount,
                    "loan_amount_term": application.loan_amount_term,
                    "credit_history": application.credit_history,
                    "property_area": application.property_area,
                    "predicted_approval": application.predicted_approval,
                    "risk_score": application.risk_score,
                    "risk_category": application.risk_category,
                    "recommendation": application.recommendation,
                    "confidence_score": application.confidence_score,
                    "ml_justification": application.ml_justification,
                    "final_status": application.final_status,
                    "admin_notes": application.admin_notes,
                    "created_at": application.created_at.isoformat() if application.created_at else None,
                    "updated_at": application.updated_at.isoformat() if application.updated_at else None
                }
            return None
            
        except Exception as e:
            logger.error(f"Error fetching application {application_id}: {e}")
            return None

    async def update_admin_decision(
        self, 
        application_id: str, 
        final_status: str, 
        admin_notes: Optional[str] = None
    ) -> bool:
        """Update application with admin decision."""
        
        try:
            application = self.db.query(LoanApplication).filter(
                LoanApplication.application_id == application_id
            ).first()
            
            if not application:
                logger.warning(f"Application not found: {application_id}")
                return False
            
            application.final_status = final_status
            application.admin_notes = admin_notes
            application.updated_at = datetime.utcnow()
            
            self.db.commit()
            logger.info(f"Updated admin decision for {application_id}: {final_status}")
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating admin decision for {application_id}: {e}")
            return False

    async def get_applications_for_review(
        self, 
        limit: int = 50, 
        offset: int = 0
    ) -> Dict[str, Any]:
        """Get applications that need admin review."""
        
        try:
            # Get applications with high risk or conflicting recommendations
            query = self.db.query(LoanApplication).filter(
                and_(
                    LoanApplication.final_status.is_(None),
                    LoanApplication.risk_score > 60  # High risk applications
                )
            ).order_by(desc(LoanApplication.created_at))
            
            total_count = query.count()
            applications = query.offset(offset).limit(limit).all()
            
            app_list = []
            for app in applications:
                app_list.append({
                    "application_id": app.application_id,
                    "applicant_income": app.applicant_income,
                    "loan_amount": app.loan_amount,
                    "predicted_approval": app.predicted_approval,
                    "risk_score": app.risk_score,
                    "risk_category": app.risk_category,
                    "recommendation": app.recommendation,
                    "created_at": app.created_at.isoformat() if app.created_at else None
                })
            
            return {
                "applications": app_list,
                "total_count": total_count,
                "has_more": total_count > (offset + limit)
            }
            
        except Exception as e:
            logger.error(f"Error fetching applications for review: {e}")
            return {"applications": [], "total_count": 0, "has_more": False}

    async def get_applications_for_retraining(self) -> List[Dict[str, Any]]:
        """Get applications with admin decisions for model retraining."""
        
        try:
            applications = self.db.query(LoanApplication).filter(
                LoanApplication.final_status.isnot(None)
            ).all()
            
            app_list = []
            for app in applications:
                app_list.append({
                    "application_id": app.application_id,
                    "predicted_approval": app.predicted_approval,
                    "final_status": app.final_status,
                    "risk_score": app.risk_score,
                    "risk_category": app.risk_category,
                    "created_at": app.created_at.isoformat() if app.created_at else None
                })
            
            return app_list
            
        except Exception as e:
            logger.error(f"Error fetching retraining data: {e}")
            return []

    async def get_model_metrics(self) -> Dict[str, Any]:
        """Get latest model performance metrics."""
        
        try:
            # Get accuracy metrics from recent applications
            thirty_days_ago = datetime.utcnow() - timedelta(days=30)
            
            recent_apps = self.db.query(LoanApplication).filter(
                and_(
                    LoanApplication.created_at >= thirty_days_ago,
                    LoanApplication.final_status.isnot(None)
                )
            ).all()
            
            if not recent_apps:
                return {"accuracy": None, "total_applications": 0, "period_days": 30}
            
            # Calculate accuracy
            correct_predictions = sum(
                1 for app in recent_apps 
                if app.predicted_approval == app.final_status
            )
            
            accuracy = correct_predictions / len(recent_apps)
            
            # Risk distribution
            risk_distribution = {
                "Low": sum(1 for app in recent_apps if app.risk_category == "Low"),
                "Medium": sum(1 for app in recent_apps if app.risk_category == "Medium"),
                "High": sum(1 for app in recent_apps if app.risk_category == "High")
            }
            
            return {
                "accuracy": accuracy,
                "total_applications": len(recent_apps),
                "correct_predictions": correct_predictions,
                "period_days": 30,
                "risk_distribution": risk_distribution
            }
            
        except Exception as e:
            logger.error(f"Error calculating model metrics: {e}")
            return {"accuracy": None, "total_applications": 0, "period_days": 30}