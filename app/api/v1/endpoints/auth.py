# app/api/v1/endpoints/auth.py
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta
from typing import List

from app.config.database import get_db
from app.config.settings import settings
from app.core.auth.auth_utils import (
    AuthService, create_access_token, get_current_user, require_superadmin,
    require_admin_or_bm, log_user_action, get_client_ip, get_password_hash,
    verify_password
)
from app.core.models.database import User
from app.core.models.auth_schemas import (
    Token, UserCreate, UserResponse, UserUpdate, UserList, 
    PasswordChange, UserRole
)

router = APIRouter()

@router.post("/login", response_model=Token)
async def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """Authenticate user and return access token."""
    auth_service = AuthService(db)
    user = auth_service.authenticate_user(form_data.username, form_data.password)
    
    if not user:
        # Log failed login attempt
        await log_user_action(
            db=db,
            user_id=None,
            action="login_failed",
            details=f"Failed login attempt for username: {form_data.username}",
            ip_address=get_client_ip(request),
            user_agent=request.headers.get("User-Agent")
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create access token
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={
            "sub": user.username,
            "user_id": user.id,
            "role": user.role.value
        },
        expires_delta=access_token_expires
    )
    
    # Update last login
    auth_service.update_last_login(user.id)
    
    # Log successful login
    await log_user_action(
        db=db,
        user_id=user.id,
        action="login_success",
        details="User logged in successfully",
        ip_address=get_client_ip(request),
        user_agent=request.headers.get("User-Agent")
    )
    
    # Create user response
    user_response = UserResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        role=user.role,
        is_active=user.is_active,
        is_disabled=user.is_disabled,
        created_at=user.created_at,
        updated_at=user.updated_at,
        last_login=user.last_login,
        created_by_id=user.created_by_id
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": settings.access_token_expire_minutes * 60,
        "user_info": user_response
    }

@router.post("/logout")
async def logout(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Logout user (mainly for audit logging)."""
    await log_user_action(
        db=db,
        user_id=current_user.id,
        action="logout",
        details="User logged out",
        ip_address=get_client_ip(request),
        user_agent=request.headers.get("User-Agent")
    )
    
    return {"message": "Logged out successfully"}

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current user information."""
    return UserResponse(
        id=current_user.id,
        username=current_user.username,
        email=current_user.email,
        full_name=current_user.full_name,
        role=current_user.role,
        is_active=current_user.is_active,
        is_disabled=current_user.is_disabled,
        created_at=current_user.created_at,
        updated_at=current_user.updated_at,
        last_login=current_user.last_login,
        created_by_id=current_user.created_by_id
    )

@router.put("/change-password")
async def change_password(
    request: Request,
    password_data: PasswordChange,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Change current user's password."""
    # Verify current password
    if not verify_password(password_data.current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )
    
    # Verify new password confirmation
    if password_data.new_password != password_data.confirm_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password and confirmation don't match"
        )
    
    # Update password
    current_user.hashed_password = get_password_hash(password_data.new_password)
    db.commit()
    
    # Log password change
    await log_user_action(
        db=db,
        user_id=current_user.id,
        action="password_changed",
        details="User changed password",
        ip_address=get_client_ip(request),
        user_agent=request.headers.get("User-Agent")
    )
    
    return {"message": "Password changed successfully"}

# User Management Endpoints (Superadmin only)
@router.post("/users", response_model=UserResponse)
async def create_user(
    request: Request,
    user_data: UserCreate,
    current_user: User = Depends(require_superadmin),
    db: Session = Depends(get_db)
):
    """Create a new user (Superadmin only)."""
    auth_service = AuthService(db)
    
    try:
        new_user = auth_service.create_user(
            username=user_data.username,
            email=user_data.email,
            full_name=user_data.full_name,
            password=user_data.password,
            role=user_data.role,
            created_by_id=current_user.id,
            is_active=user_data.is_active
        )
        
        # Log user creation
        await log_user_action(
            db=db,
            user_id=current_user.id,
            action="user_created",
            resource_type="user",
            resource_id=str(new_user.id),
            details=f"Created user: {new_user.username} with role: {new_user.role.value}",
            ip_address=get_client_ip(request),
            user_agent=request.headers.get("User-Agent")
        )
        
        return UserResponse(
            id=new_user.id,
            username=new_user.username,
            email=new_user.email,
            full_name=new_user.full_name,
            role=new_user.role,
            is_active=new_user.is_active,
            is_disabled=new_user.is_disabled,
            created_at=new_user.created_at,
            updated_at=new_user.updated_at,
            last_login=new_user.last_login,
            created_by_id=new_user.created_by_id
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create user: {str(e)}"
        )

@router.get("/users", response_model=UserList)
async def list_users(
    page: int = 1,
    page_size: int = 20,
    role: UserRole = None,
    is_active: bool = None,
    current_user: User = Depends(require_superadmin),
    db: Session = Depends(get_db)
):
    """List all users with pagination (Superadmin only)."""
    query = db.query(User)
    
    # Apply filters
    if role:
        query = query.filter(User.role == role)
    if is_active is not None:
        query = query.filter(User.is_active == is_active)
    
    # Get total count
    total_count = query.count()
    
    # Apply pagination
    offset = (page - 1) * page_size
    users = query.offset(offset).limit(page_size).all()
    
    user_responses = []
    for user in users:
        user_responses.append(UserResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            role=user.role,
            is_active=user.is_active,
            is_disabled=user.is_disabled,
            created_at=user.created_at,
            updated_at=user.updated_at,
            last_login=user.last_login,
            created_by_id=user.created_by_id
        ))
    
    return UserList(
        users=user_responses,
        total_count=total_count,
        page=page,
        page_size=page_size,
        has_more=total_count > (page * page_size)
    )

@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    current_user: User = Depends(require_superadmin),
    db: Session = Depends(get_db)
):
    """Get user by ID (Superadmin only)."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return UserResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        role=user.role,
        is_active=user.is_active,
        is_disabled=user.is_disabled,
        created_at=user.created_at,
        updated_at=user.updated_at,
        last_login=user.last_login,
        created_by_id=user.created_by_id
    )

@router.put("/users/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    user_data: UserUpdate,
    request: Request,
    current_user: User = Depends(require_superadmin),
    db: Session = Depends(get_db)
):
    """Update user (Superadmin only)."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Prevent superadmin from disabling themselves
    if user.id == current_user.id and user_data.is_disabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot disable your own account"
        )
    
    # Update fields
    update_data = user_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(user, field, value)
    
    db.commit()
    db.refresh(user)
    
    # Log user update
    await log_user_action(
        db=db,
        user_id=current_user.id,
        action="user_updated",
        resource_type="user",
        resource_id=str(user.id),
        details=f"Updated user: {user.username}",
        ip_address=get_client_ip(request),
        user_agent=request.headers.get("User-Agent")
    )
    
    return UserResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        role=user.role,
        is_active=user.is_active,
        is_disabled=user.is_disabled,
        created_at=user.created_at,
        updated_at=user.updated_at,
        last_login=user.last_login,
        created_by_id=user.created_by_id
    )

@router.delete("/users/{user_id}")
async def delete_user(
    user_id: int,
    request: Request,
    current_user: User = Depends(require_superadmin),
    db: Session = Depends(get_db)
):
    """Disable user (soft delete) (Superadmin only)."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Prevent superadmin from deleting themselves
    if user.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account"
        )
    
    # Soft delete (disable user)
    user.is_disabled = True
    user.is_active = False
    db.commit()
    
    # Log user deletion
    await log_user_action(
        db=db,
        user_id=current_user.id,
        action="user_deleted",
        resource_type="user",
        resource_id=str(user.id),
        details=f"Disabled user: {user.username}",
        ip_address=get_client_ip(request),
        user_agent=request.headers.get("User-Agent")
    )
    
    return {"message": "User disabled successfully"}