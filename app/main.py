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
from app.api.v1.api import api_router

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan events."""
    # Startup
    logger.info("🚀 Starting Loan Approval System...")
    
    # Create database tables
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("✓ Database tables created/verified")
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")
    
    # Initialize ML predictor (singleton pattern)
    try:
        from app.ml.models.predictor import get_predictor
        predictor = get_predictor()
        
        # Store predictor in app state for access by endpoints
        app.state.predictor = predictor
        
        if predictor.is_loaded:
            logger.info("✅ ML model loaded successfully")
            model_info = predictor.get_model_info()
            logger.info(f"   Model: {model_info.get('model_type')}")
            logger.info(f"   Features: {model_info.get('feature_count')}")
        else:
            logger.warning("⚠️  ML model not loaded - using fallback prediction")
            logger.info("💡 System will use rule-based prediction until model is trained")
        
        # Perform health check
        health_result = await predictor.health_check()
        logger.info(f"🏥 Predictor health: {health_result['predictor_status']}")
        
    except Exception as e:
        logger.error(f"❌ Error initializing predictor: {e}")
        # Don't fail startup - create placeholder
        app.state.predictor = None
    
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down Loan Approval System...")
    
    # Log final statistics if predictor exists
    if hasattr(app.state, 'predictor') and app.state.predictor:
        stats = app.state.predictor._performance_stats
        logger.info(f"📊 Final stats: {stats['total_predictions']} total predictions")
        logger.info(f"   ML predictions: {stats['ml_predictions']}")
        logger.info(f"   Fallback predictions: {stats['fallback_predictions']}")
    
    # Shutdown
    logger.info("Shutting down Loan Approval System...")

# Create FastAPI application
app = FastAPI(
    title=settings.project_name,
    version=settings.version,
    description="AI-powered loan approval system with real-time risk assessment and unified prediction engine",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)


# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



# Include API routes
app.include_router(api_router, prefix=settings.api_v1_str)

@app.get("/")
async def root():
    """Root endpoint."""
    predictor_status = "not_available"
    if hasattr(app.state, 'predictor') and app.state.predictor:
        if app.state.predictor.is_loaded:
            predictor_status = "ml_ready"
        else:
            predictor_status = "fallback_ready"

    return {
        "message": "Loan Approval System API",
        "version": settings.version,
        "status": "running",
        "predictor_status": predictor_status,
        "timestamp": datetime.utcnow().isoformat(),
        "endpoints": {
            "docs": "/docs",
            "health": "/health",
            "api": "/api/v1",
            "auth": "/api/v1/auth",
            "loans": "/api/v1/loans",
            "admin": "/api/v1/admin",
            "predict": "/api/v1/loans/predict",
            "model_info": "/api/v1/model/info"
        }
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

@app.get("/health")
async def health_check():
    """Enhanced health check endpoint."""
    
    # Check predictor health
    predictor_health = {"status": "not_available"}
    if hasattr(app.state, 'predictor') and app.state.predictor:
        try:
            predictor_health = await app.state.predictor.health_check()
        except Exception as e:
            predictor_health = {"status": "error", "error": str(e)}
    
    # Check database status
    try:
        from sqlalchemy import text
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        db_status = "healthy"
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        db_status = "unhealthy"
    
    # Overall status
    if db_status == "healthy" and predictor_health.get("status") in ["healthy", "degraded"]:
        overall_status = "healthy"
    elif db_status == "healthy":
        overall_status = "degraded"  # DB good, predictor issues
    else:
        overall_status = "unhealthy"  # DB issues
    
    return {
        "status": overall_status,
        "timestamp": datetime.utcnow().isoformat(),
        "version": settings.version,
        "components": {
            "database": db_status,
            "predictor": predictor_health
        }
    }


# # Direct loan prediction endpoint (backward compatibility)
# @app.post("/api/v1/loans/predict", response_model=LoanPredictionResponse)
# async def predict_loan_approval(application: LoanApplicationInput):
#     """Predict loan approval for a new application."""
    
#     # Check if model is loaded
#     if not hasattr(app.state, 'predictor') or not app.state.predictor or not app.state.predictor.is_loaded:
#         raise HTTPException(
#             status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
#             detail="ML model not loaded. Please train a model first."
#         )
    
#     try:
#         # Generate unique application ID
#         application_id = f"LOAN_{datetime.now().strftime('%Y%m%d')}_{uuid.uuid4().hex[:8].upper()}"
        
#         # Convert Pydantic model to dict
#         input_data = application.model_dump()
        
#         # Make prediction
#         prediction_result = app.state.predictor.predict(input_data)
        
#         # Create response
#         response = LoanPredictionResponse(
#             application_id=application_id,
#             loan_decision=prediction_result['loan_decision'],
#             risk_score=prediction_result['risk_score'],
#             risk_category=prediction_result['risk_category'],
#             justification=prediction_result['justification'],
#             recommendation=prediction_result['recommendation'],
#             confidence_score=prediction_result.get('confidence_score')
#         )
        
#         # Save to database if loan service is available
#         try:
#             from app.config.database import SessionLocal
#             from app.core.repositories.loan_repository import LoanRepository
#             from app.core.models.auth_schemas import LoanStatus
            
#             db = SessionLocal()
#             loan_repo = LoanRepository(db)
#             await loan_repo.create_application(
#                 application_id=application_id,
#                 input_data=input_data,
#                 prediction_result=prediction_result,
#                 justification=prediction_result['justification'],
#                 status=LoanStatus.DRAFTED
#             )
#             db.close()
#         except Exception as e:
#             logger.warning(f"Could not save to database: {e}")
        
#         logger.info(f"Processed loan application {application_id}: {prediction_result['loan_decision']}")
#         return response
        
#     except Exception as e:
#         logger.error(f"Prediction error: {e}")
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail=f"Prediction failed: {str(e)}"
        # )

# Include individual routers (more reliable than importing the combined api_router)
logger.info("Mounting API endpoints...")

try:
    from app.api.v1.endpoints.loans import router as loans_router
    app.include_router(loans_router, prefix="/api/v1/loans", tags=["loans"])
    logger.info("✅ loans router mounted")
except Exception as e:
    logger.error(f"❌ Failed to mount loans router: {e}")


# Mount authentication endpoints
try:
    from app.api.v1.endpoints.auth import router as auth_router
    app.include_router(auth_router, prefix="/api/v1/auth", tags=["authentication"])
    logger.info("✅ Authentication router mounted")
except Exception as e:
    logger.error(f"❌ Failed to mount auth router: {e}")


# Mount admin dashboard endpoints
try:
    from app.api.v1.endpoints.admin_dashboard import router as dashboard_router
    app.include_router(dashboard_router, prefix="/api/v1/admin", tags=["admin-dashboard"])
    logger.info("✅ Admin dashboard router mounted")
except Exception as e:
    logger.error(f"❌ Failed to mount dashboard router: {e}")

# Mount basic admin endpoints
try:
    from app.api.v1.endpoints.admin import router as admin_router
    app.include_router(admin_router, prefix="/api/v1/admin", tags=["admin"])
    logger.info("✅ Admin router mounted")
except Exception as e:
    logger.error(f"❌ Failed to mount admin router: {e}")



# Mount health endpoints
try:
    from app.api.v1.endpoints.health import router as health_router
    app.include_router(health_router, prefix="/api/v1/health", tags=["health"])
    logger.info("✅ Health router mounted")
except Exception as e:
    logger.error(f"❌ Failed to mount health router: {e}")

# @app.get("/api/v1/model/info")
# async def get_model_info():
#     """Get information about the loaded model."""
    
#     if not hasattr(app.state, 'predictor') or not app.state.predictor:
#         return {
#             "model_loaded": False,
#             "message": "No model loaded"
#         }
    
#     predictor = app.state.predictor
    
#     return {
#         "model_loaded": predictor.is_loaded,
#         "model_path": predictor.model_path,
#         "preprocessor_path": predictor.preprocessor_path,
#         "features": predictor.preprocessor_info.get('feature_names', []) if predictor.preprocessor_info else []
#     }


@app.get("/api/v1/model/info")
async def get_model_info():
    """Get comprehensive information about the ML model and predictor."""
    
    if not hasattr(app.state, 'predictor') or not app.state.predictor:
        return {
            "model_loaded": False,
            "message": "Predictor not available",
            "status": "error"
        }
    
    try:
        model_info = app.state.predictor.get_model_info()
        
        # Add feature importance if available
        feature_importance = app.state.predictor.get_feature_importance()
        if feature_importance:
            # Get top 10 most important features
            top_features = sorted(
                feature_importance.items(), 
                key=lambda x: x[1], 
                reverse=True
            )[:10]
            model_info['top_features'] = top_features
        
        return model_info
        
    except Exception as e:
        logger.error(f"Error getting model info: {e}")
        return {
            "model_loaded": False,
            "message": f"Error retrieving model info: {str(e)}",
            "status": "error"
        }
    

@app.get("/api/v1/model/validate")
async def validate_prediction_capability():
    """Validate that the prediction system is working correctly."""
    
    if not hasattr(app.state, 'predictor') or not app.state.predictor:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Predictor not available"
        )
    
    # Test prediction with sample data
    test_data = {
        'gender': 'Male',
        'married': 'Yes',
        'dependents': 1,
        'education': 'Graduate',
        'age': 32,
        'self_employed': 'No',
        'applicant_income': 50000,
        'monthly_expenses': 30000,
        'loan_amount': 200,
        'loan_amount_term': 360,
        'credit_history': 1,
        'property_area': 'Urban'
    }
    
    try:
        # Validate input
        is_valid, errors = app.state.predictor.validate_input(test_data)
        if not is_valid:
            return {
                "validation": "failed",
                "errors": errors,
                "status": "error"
            }
        
        # Test prediction
        result = await app.state.predictor.predict(test_data)
        
        return {
            "validation": "success",
            "test_prediction": {
                "decision": result.get('loan_decision'),
                "risk_score": result.get('risk_score'),
                "method": result.get('prediction_method'),
                "processing_time_ms": result.get('processing_time_ms')
            },
            "status": "healthy"
        }
        
    except Exception as e:
        logger.error(f"Prediction validation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Prediction validation failed: {str(e)}"
        )

# Add a test endpoint to verify mounting
@app.get("/api/v1/test")
async def test_api():
    """Test endpoint to verify API mounting."""
    return {
        "message": "API v1 is working",
        "timestamp": datetime.utcnow().isoformat(),
        "available_routes": len(app.routes)
    }


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler with detailed logging."""
    
    logger.error(f"Unhandled exception on {request.url}: {exc}", exc_info=True)
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "Internal server error",
            "timestamp": datetime.utcnow().isoformat(),
            "path": str(request.url),
            "request_id": f"req_{int(datetime.utcnow().timestamp())}"
        }
    )

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """HTTP exception handler."""
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.detail,
            "timestamp": datetime.utcnow().isoformat(),
            "path": str(request.url)
        }
    )

# Log final status
logger.info(f"Application started with {len(app.routes)} routes")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )