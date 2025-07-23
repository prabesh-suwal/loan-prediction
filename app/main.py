# app/main.py - Updated with proper ML model loading
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
from contextlib import asynccontextmanager
from datetime import datetime
import uuid

from app.config.settings import settings
from app.config.database import engine, Base
from app.utils.logger import setup_logging
from app.core.models.schemas import LoanApplicationInput, LoanPredictionResponse

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan events."""
    # Startup
    logger.info("Starting Loan Approval System...")
    
    # Create database tables
    Base.metadata.create_all(bind=engine)
    
    # Load ML model
    try:
        from app.ml.models.predictor import LoanPredictor
        predictor = LoanPredictor()
        
        if predictor.load_model():
            logger.info("✓ ML model loaded successfully")
            app.state.predictor = predictor
        else:
            logger.warning("⚠️ ML model not found - predictions will not work")
            app.state.predictor = None
    except Exception as e:
        logger.error(f"❌ Error loading ML model: {e}")
        app.state.predictor = None
    
    yield
    
    # Shutdown
    logger.info("Shutting down Loan Approval System...")

# Create FastAPI application
app = FastAPI(
    title=settings.project_name,
    version=settings.version,
    description="AI-powered loan approval system with real-time risk assessment",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Loan Approval System API",
        "version": settings.version,
        "status": "running",
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    model_status = "loaded" if (hasattr(app.state, 'predictor') and 
                               app.state.predictor and 
                               app.state.predictor.is_loaded) else "not_loaded"
    
    try:
        # Test database connection
        from sqlalchemy import text
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        db_status = "healthy"
    except Exception:
        db_status = "unhealthy"
    
    return {
        "status": "healthy",
        "model_status": model_status,
        "database_status": db_status,
        "timestamp": datetime.utcnow().isoformat()
    }

@app.post("/api/v1/loans/predict", response_model=LoanPredictionResponse)
async def predict_loan_approval(application: LoanApplicationInput):
    """Predict loan approval for a new application."""
    
    # Check if model is loaded
    if not hasattr(app.state, 'predictor') or not app.state.predictor or not app.state.predictor.is_loaded:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="ML model not loaded. Please train a model first."
        )
    
    try:
        # Generate unique application ID
        application_id = f"LOAN_{datetime.now().strftime('%Y%m%d')}_{uuid.uuid4().hex[:8].upper()}"
        
        # Convert Pydantic model to dict
        input_data = application.model_dump()
        
        # Make prediction
        prediction_result = app.state.predictor.predict(input_data)
        
        # Create response
        response = LoanPredictionResponse(
            application_id=application_id,
            loan_decision=prediction_result['loan_decision'],
            risk_score=prediction_result['risk_score'],
            risk_category=prediction_result['risk_category'],
            justification=prediction_result['justification'],
            recommendation=prediction_result['recommendation'],
            confidence_score=prediction_result.get('confidence_score')
        )
        
        logger.info(f"Processed loan application {application_id}: {prediction_result['loan_decision']}")
        return response
        
    except Exception as e:
        logger.error(f"Prediction error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Prediction failed: {str(e)}"
        )

@app.get("/api/v1/model/info")
async def get_model_info():
    """Get information about the loaded model."""
    
    if not hasattr(app.state, 'predictor') or not app.state.predictor:
        return {
            "model_loaded": False,
            "message": "No model loaded"
        }
    
    predictor = app.state.predictor
    
    return {
        "model_loaded": predictor.is_loaded,
        "model_path": predictor.model_path,
        "preprocessor_path": predictor.preprocessor_path,
        "features": predictor.preprocessor_info.get('feature_names', []) if predictor.preprocessor_info else []
    }

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error"}
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug
    )