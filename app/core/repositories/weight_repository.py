from typing import Dict, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_
import logging

logger = logging.getLogger(__name__)

class WeightRepository:
    """Repository for managing feature weights with proper error handling."""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def get_active_weights(self) -> Dict[str, float]:
        """Get all active feature weights with error handling."""
        try:
            # Import here to avoid circular imports and relationship issues
            from app.core.models.database import FeatureWeights
            
            weights = self.db.query(FeatureWeights).filter(
                FeatureWeights.is_active == True
            ).all()
            
            result = {weight.feature_name: weight.weight for weight in weights}
            logger.debug(f"Retrieved {len(result)} active feature weights")
            
            return result
            
        except ImportError as e:
            logger.error(f"Import error in get_active_weights: {e}")
            return self._get_default_weights()
        except Exception as e:
            logger.error(f"Error fetching weights: {e}")
            return self._get_default_weights()
    
    async def get_all_weights(self) -> List[Dict]:
        """Get all feature weights with metadata."""
        try:
            from app.core.models.database import FeatureWeights
            
            weights = self.db.query(FeatureWeights).all()
            
            result = [
                {
                    "feature_name": w.feature_name,
                    "weight": w.weight,
                    "description": w.description,
                    "is_active": w.is_active,
                    "created_at": w.created_at.isoformat() if w.created_at else None,
                    "updated_at": w.updated_at.isoformat() if w.updated_at else None
                }
                for w in weights
            ]
            
            logger.debug(f"Retrieved {len(result)} total feature weights")
            return result
            
        except Exception as e:
            logger.error(f"Error fetching all weights: {e}")
            return []
    
    async def update_weight(self, feature_name: str, weight: float, description: str = None) -> bool:
        """Update or create a feature weight."""
        try:
            from app.core.models.database import FeatureWeights
            
            existing = self.db.query(FeatureWeights).filter(
                FeatureWeights.feature_name == feature_name
            ).first()
            
            if existing:
                existing.weight = weight
                if description:
                    existing.description = description
                logger.info(f"Updated weight for {feature_name}: {weight}")
            else:
                new_weight = FeatureWeights(
                    feature_name=feature_name,
                    weight=weight,
                    description=description,
                    is_active=True
                )
                self.db.add(new_weight)
                logger.info(f"Created new weight for {feature_name}: {weight}")
            
            self.db.commit()
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating weight for {feature_name}: {e}")
            return False
    
    def _get_default_weights(self) -> Dict[str, float]:
        """Return default feature weights as fallback."""
        
        default_weights = {
            "credit_history": 2.5,
            "total_income": 2.0,
            "emi_income_ratio": 1.8,
            "loan_amount": 1.5,
            "education": 1.2,
            "employment_stability": 1.1,
            "property_area": 1.0,
            "self_employed": 0.9,
            "married": 0.8,
            "dependents": 0.7,
            "gender": 0.5
        }
        
        logger.info("Using default feature weights as fallback")
        return default_weights