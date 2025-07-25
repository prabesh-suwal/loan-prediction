# app/api/v1/endpoints/admin_dashboard.py
from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, and_
from datetime import datetime, timedelta
from typing import List, Optional

from app.config.database import get_db
from app.core.auth.auth_utils import (
    require_admin_or_bm, get_current_user, log_user_action, get_client_ip
)
from app.core.models.database import User, LoanApplication, LoanStatus, AuditLog
from app.core.models.auth_schemas import (
    DashboardResponse, DashboardStats, RiskDistribution, ApprovalTrend,
    LoanStatusUpdate, LoanListResponse, LoanListFilters, AuditLogList, AuditLogResponse
)

router = APIRouter()

@router.get("/dashboard", response_model=DashboardResponse)
async def get_dashboard(
    current_user: User = Depends(require_admin_or_bm),
    db: Session = Depends(get_db)
):
    """Get dashboard statistics and data."""
    
    # Basic statistics
    total_applications = db.query(LoanApplication).count()
    drafted_applications = db.query(LoanApplication).filter(
        LoanApplication.status == LoanStatus.DRAFTED
    ).count()
    approved_applications = db.query(LoanApplication).filter(
        LoanApplication.status == LoanStatus.APPROVED
    ).count()
    rejected_applications = db.query(LoanApplication).filter(
        LoanApplication.status == LoanStatus.REJECTED
    ).count()
    
    # Calculate approval rate
    total_processed = approved_applications + rejected_applications
    approval_rate = (approved_applications / total_processed * 100) if total_processed > 0 else 0
    
    # Average risk score
    avg_risk_score = db.query(func.avg(LoanApplication.risk_score)).scalar() or 0
    
    # Total loan amounts
    total_loan_amount = db.query(func.sum(LoanApplication.loan_amount)).scalar() or 0
    approved_loan_amount = db.query(func.sum(LoanApplication.loan_amount)).filter(
        LoanApplication.status == LoanStatus.APPROVED
    ).scalar() or 0
    
    # Time-based applications
    now = datetime.utcnow()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = now - timedelta(days=7)
    month_start = now - timedelta(days=30)
    
    applications_today = db.query(LoanApplication).filter(
        LoanApplication.created_at >= today_start
    ).count()
    
    applications_this_week = db.query(LoanApplication).filter(
        LoanApplication.created_at >= week_start
    ).count()
    
    applications_this_month = db.query(LoanApplication).filter(
        LoanApplication.created_at >= month_start
    ).count()
    
    # Risk distribution
    low_risk = db.query(LoanApplication).filter(
        LoanApplication.risk_category == "Low"
    ).count()
    medium_risk = db.query(LoanApplication).filter(
        LoanApplication.risk_category == "Medium"
    ).count()
    high_risk = db.query(LoanApplication).filter(
        LoanApplication.risk_category == "High"
    ).count()
    
    # Approval trends (last 7 days)
    approval_trends = []
    for i in range(7):
        date = (now - timedelta(days=i)).date()
        date_start = datetime.combine(date, datetime.min.time())
        date_end = datetime.combine(date, datetime.max.time())
        
        day_approved = db.query(LoanApplication).filter(
            and_(
                LoanApplication.admin_decision_date >= date_start,
                LoanApplication.admin_decision_date <= date_end,
                LoanApplication.status == LoanStatus.APPROVED
            )
        ).count()
        
        day_rejected = db.query(LoanApplication).filter(
            and_(
                LoanApplication.admin_decision_date >= date_start,
                LoanApplication.admin_decision_date <= date_end,
                LoanApplication.status == LoanStatus.REJECTED
            )
        ).count()
        
        approval_trends.append(ApprovalTrend(
            date=date.isoformat(),
            approved=day_approved,
            rejected=day_rejected,
            total=day_approved + day_rejected
        ))
    
    # Recent applications (last 10)
    recent_applications = db.query(LoanApplication).order_by(
        desc(LoanApplication.created_at)
    ).limit(10).all()
    
    recent_apps_data = []
    for app in recent_applications:
        recent_apps_data.append({
            "application_id": app.application_id,
            "loan_amount": app.loan_amount,
            "risk_score": app.risk_score,
            "risk_category": app.risk_category,
            "status": app.status.value if app.status else "drafted",
            "created_at": app.created_at.isoformat() if app.created_at else None
        })
    
    return DashboardResponse(
        stats=DashboardStats(
            total_applications=total_applications,
            drafted_applications=drafted_applications,
            approved_applications=approved_applications,
            rejected_applications=rejected_applications,
            approval_rate=round(approval_rate, 2),
            average_risk_score=round(avg_risk_score, 2),
            total_loan_amount=total_loan_amount,
            approved_loan_amount=approved_loan_amount,
            applications_today=applications_today,
            applications_this_week=applications_this_week,
            applications_this_month=applications_this_month
        ),
        risk_distribution=RiskDistribution(
            low_risk=low_risk,
            medium_risk=medium_risk,
            high_risk=high_risk
        ),
        approval_trends=approval_trends,
        recent_applications=recent_apps_data
    )

@router.get("/loans", response_model=LoanListResponse)
async def list_loans(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[LoanStatus] = None,
    risk_category: Optional[str] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    min_loan_amount: Optional[float] = None,
    max_loan_amount: Optional[float] = None,
    property_area: Optional[str] = None,
    search: Optional[str] = None,
    current_user: User = Depends(require_admin_or_bm),
    db: Session = Depends(get_db)
):
    """List loan applications with filters and pagination."""
    
    query = db.query(LoanApplication)
    
    # Apply filters
    filters_applied = {}
    
    if status:
        query = query.filter(LoanApplication.status == status)
        filters_applied["status"] = status.value
    
    if risk_category:
        query = query.filter(LoanApplication.risk_category == risk_category)
        filters_applied["risk_category"] = risk_category
    
    if date_from:
        query = query.filter(LoanApplication.created_at >= date_from)
        filters_applied["date_from"] = date_from.isoformat()
    
    if date_to:
        query = query.filter(LoanApplication.created_at <= date_to)
        filters_applied["date_to"] = date_to.isoformat()
    
    if min_loan_amount is not None:
        query = query.filter(LoanApplication.loan_amount >= min_loan_amount)
        filters_applied["min_loan_amount"] = min_loan_amount
    
    if max_loan_amount is not None:
        query = query.filter(LoanApplication.loan_amount <= max_loan_amount)
        filters_applied["max_loan_amount"] = max_loan_amount
    
    if property_area:
        query = query.filter(LoanApplication.property_area == property_area)
        filters_applied["property_area"] = property_area
    
    if search:
        search_pattern = f"%{search}%"
        query = query.filter(LoanApplication.application_id.ilike(search_pattern))
        filters_applied["search"] = search
    
    # Get total count
    total_count = query.count()
    
    # Apply pagination and ordering
    offset = (page - 1) * page_size
    loans = query.order_by(desc(LoanApplication.created_at)).offset(offset).limit(page_size).all()
    
    # Convert to dictionary format
    loans_data = [loan.to_dict() for loan in loans]
    
    return LoanListResponse(
        loans=loans_data,
        total_count=total_count,
        page=page,
        page_size=page_size,
        has_more=total_count > (page * page_size),
        filters_applied=filters_applied
    )

@router.get("/loans/{application_id}")
async def get_loan_detail(
    application_id: str,
    current_user: User = Depends(require_admin_or_bm),
    db: Session = Depends(get_db)
):
    """Get detailed loan application information."""
    
    loan = db.query(LoanApplication).filter(
        LoanApplication.application_id == application_id
    ).first()
    
    if not loan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Loan application not found"
        )
    
    return loan.to_dict()

@router.put("/loans/{application_id}/status")
async def update_loan_status(
    application_id: str,
    status_update: LoanStatusUpdate,
    request: Request,
    current_user: User = Depends(require_admin_or_bm),
    db: Session = Depends(get_db)
):
    """Update loan application status."""
    
    loan = db.query(LoanApplication).filter(
        LoanApplication.application_id == application_id
    ).first()
    
    if not loan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Loan application not found"
        )
    
    # Store previous status for logging
    previous_status = loan.status
    
    # Update loan status
    loan.status = status_update.status
    loan.admin_notes = status_update.admin_notes
    loan.reviewed_by_id = current_user.id
    loan.admin_decision_date = datetime.utcnow()
    
    db.commit()
    
    # Log the status change
    await log_user_action(
        db=db,
        user_id=current_user.id,
        action="loan_status_updated",
        resource_type="loan_application",
        resource_id=application_id,
        details=f"Status changed from {previous_status.value if previous_status else 'None'} to {status_update.status.value}",
        ip_address=get_client_ip(request),
        user_agent=request.headers.get("User-Agent")
    )
    
    return {
        "message": "Loan status updated successfully",
        "application_id": application_id,
        "new_status": status_update.status.value,
        "reviewed_by": current_user.full_name
    }

@router.get("/audit-logs", response_model=AuditLogList)
async def get_audit_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    user_id: Optional[int] = None,
    action: Optional[str] = None,
    resource_type: Optional[str] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    current_user: User = Depends(require_admin_or_bm),
    db: Session = Depends(get_db)
):
    """Get audit logs with filters and pagination."""
    
    query = db.query(AuditLog).join(User, AuditLog.user_id == User.id, isouter=True)
    
    # Apply filters
    if user_id:
        query = query.filter(AuditLog.user_id == user_id)
    
    if action:
        query = query.filter(AuditLog.action.ilike(f"%{action}%"))
    
    if resource_type:
        query = query.filter(AuditLog.resource_type == resource_type)
    
    if date_from:
        query = query.filter(AuditLog.created_at >= date_from)
    
    if date_to:
        query = query.filter(AuditLog.created_at <= date_to)
    
    # Get total count
    total_count = query.count()
    
    # Apply pagination
    offset = (page - 1) * page_size
    audit_logs = query.order_by(desc(AuditLog.created_at)).offset(offset).limit(page_size).all()
    
    # Format response
    logs_data = []
    for log in audit_logs:
        username = None
        if log.user_id:
            user = db.query(User).filter(User.id == log.user_id).first()
            username = user.username if user else None
        
        logs_data.append(AuditLogResponse(
            id=log.id,
            user_id=log.user_id,
            username=username,
            action=log.action,
            resource_type=log.resource_type,
            resource_id=log.resource_id,
            details=log.details,
            ip_address=log.ip_address,
            created_at=log.created_at
        ))
    
    return AuditLogList(
        logs=logs_data,
        total_count=total_count,
        page=page,
        page_size=page_size,
        has_more=total_count > (page * page_size)
    )

@router.get("/export/loans")
async def export_loans(
    format: str = Query("csv", regex="^(csv|excel)$"),
    status: Optional[LoanStatus] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    current_user: User = Depends(require_admin_or_bm),
    db: Session = Depends(get_db)
):
    """Export loan data to CSV or Excel format."""
    
    query = db.query(LoanApplication)
    
    # Apply filters
    if status:
        query = query.filter(LoanApplication.status == status)
    
    if date_from:
        query = query.filter(LoanApplication.created_at >= date_from)
    
    if date_to:
        query = query.filter(LoanApplication.created_at <= date_to)
    
    loans = query.all()
    
    # Log export action
    await log_user_action(
        db=db,
        user_id=current_user.id,
        action="data_export",
        resource_type="loan_application",
        details=f"Exported {len(loans)} loan records in {format} format"
    )
    
    # For now, return count (actual export implementation would require additional libraries)
    return {
        "message": f"Export prepared for {len(loans)} loan applications",
        "format": format,
        "count": len(loans),
        "note": "Actual file export implementation requires additional libraries like pandas and openpyxl"
    }