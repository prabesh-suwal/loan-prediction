from typing import Dict, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.core.models.database import FeatureWeights
import logging

logger = logging.getLogger(__name__)

class WeightRepository:
    """Repository for managing feature weights."""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def get_active_weights(self) -> Dict[str, float]:
        """Get all active feature weights."""
        try:
            weights = self.db.query(FeatureWeights).filter(
                FeatureWeights.is_active == True
            ).all()
            
            return {weight.feature_name: weight.weight for weight in weights}
            
        except Exception as e:
            logger.error(f"Error fetching weights: {e}")
            return {}
    
    async def update_weight(self, feature_name: str, weight: float, description: str = None) -> bool:
        """Update or create a feature weight."""
        try:
            existing = self.db.query(FeatureWeights).filter(
                FeatureWeights.feature_name == feature_name
            ).first()
            
            if existing:
                existing.weight = weight
                if description:
                    existing.description = description
            else:
                new_weight = FeatureWeights(
                    feature_name=feature_name,
                    weight=weight,
                    description=description
                )
                self.db.add(new_weight)
            
            self.db.commit()
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating weight: {e}")
            return False
    
    async def get_all_weights(self) -> List[Dict]:
        """Get all feature weights with metadata."""
        try:
            weights = self.db.query(FeatureWeights).all()
            return [
                {
                    "feature_name": w.feature_name,
                    "weight": w.weight,
                    "description": w.description,
                    "is_active": w.is_active,
                    "created_at": w.created_at,
                    "updated_at": w.updated_at
                }
                for w in weights
            ]
        except Exception as e:
            logger.error(f"Error fetching all weights: {e}")
            return []