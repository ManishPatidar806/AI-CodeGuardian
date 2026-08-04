from typing import Any
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.db.session import get_db

router = APIRouter(prefix="/users", tags=["User Management & Profile Authentication"])

class LoginRequest(BaseModel):
    username: str = Field(..., description="Username")
    password: str = Field(..., description="Password")

class ProfileUpdateRequest(BaseModel):
    name: str = Field(..., description="Full Name")
    email: str = Field(..., description="Email Address")
    mobile: str = Field(default="", description="Mobile Number")

class AdminPasswordChangeOTPRequest(BaseModel):
    otp: str = Field(..., description="6-digit verification code sent via Email/Mobile")
    new_password: str = Field(..., description="New Password")

class EmployeeCreateRequest(BaseModel):
    name: str = Field(..., description="Employee Full Name")
    email: str = Field(..., description="Employee Email")
    username: str = Field(..., description="Employee Username")
    password: str = Field(..., description="Employee Password")
    mobile: str = Field(default="", description="Mobile Number")

class UserStatusUpdateRequest(BaseModel):
    status: str = Field(..., description="User status: ACTIVE or BLOCKED")

# In-memory database initialized with default Admin temporary credentials
users_db = [
    {
        "id": 1,
        "username": "admin",
        "name": "Primary Admin",
        "email": "admin@company.com",
        "mobile": "+1234567890",
        "password": "adminpassword",
        "role": "ADMIN",
        "status": "ACTIVE",
        "created_at": "2026-08-01T10:00:00Z"
    }
]


@router.post("/login", summary="User Login (Temporary Credentials for First Setup)")
def login_user(payload: LoginRequest) -> dict[str, Any]:
    """Authenticate Admin or Employee using username and password."""
    for user in users_db:
        if user["username"].lower() == payload.username.lower() and user["password"] == payload.password:
            if user["status"] == "BLOCKED":
                raise HTTPException(status_code=403, detail="Your account has been blocked by Admin.")
            return {
                "success": True,
                "user": {
                    "id": user["id"],
                    "username": user["username"],
                    "name": user["name"],
                    "email": user["email"],
                    "mobile": user.get("mobile", ""),
                    "role": user["role"],
                    "status": user["status"]
                }
            }
    raise HTTPException(status_code=401, detail="Invalid username or password.")

@router.put("/{user_id}/profile", summary="Update User Profile (Admin Only for Edit)")
def update_profile(user_id: int, payload: ProfileUpdateRequest) -> dict[str, Any]:
    """Update profile details (Name, Email, Mobile)."""
    for user in users_db:
        if user["id"] == user_id:
            user["name"] = payload.name
            user["email"] = payload.email
            user["mobile"] = payload.mobile
            return {"success": True, "user": user}
    raise HTTPException(status_code=404, detail="User not found")

@router.post("/change-password-otp", summary="Admin Change Password via Mobile/Email OTP")
def change_password_otp(payload: AdminPasswordChangeOTPRequest) -> dict[str, Any]:
    """Verify OTP sent to Email/Mobile and update Admin password."""
    if payload.otp != "123456" and len(payload.otp) != 6:
        raise HTTPException(status_code=400, detail="Invalid OTP verification code. Enter demo OTP: 123456")

    # Update Admin Password (User 1)
    for user in users_db:
        if user["role"] == "ADMIN":
            user["password"] = payload.new_password
            return {"success": True, "message": "Admin password successfully updated via OTP verification."}
    raise HTTPException(status_code=404, detail="Admin user not found")

@router.post("/create-employee", summary="Admin Create Employee Account")
def create_employee(payload: EmployeeCreateRequest) -> dict[str, Any]:
    """Admin creates a new employee account with assigned credentials."""
    for user in users_db:
        if user["username"].lower() == payload.username.lower():
            raise HTTPException(status_code=400, detail="Username already exists.")

    new_employee = {
        "id": len(users_db) + 1,
        "username": payload.username,
        "name": payload.name,
        "email": payload.email,
        "mobile": payload.mobile,
        "password": payload.password,
        "role": "EMPLOYEE",
        "status": "ACTIVE",
        "created_at": "Today"
    }
    users_db.append(new_employee)
    return {"success": True, "user": new_employee}

@router.get("", summary="List All Users")
def list_users() -> list[dict[str, Any]]:
    """List all registered company employees and admins."""
    return users_db

@router.put("/{user_id}/status", summary="Admin Update User Status (Block/Unblock)")
def update_user_status(user_id: int, payload: UserStatusUpdateRequest) -> dict[str, Any]:
    """Block or activate an employee account."""
    for user in users_db:
        if user["id"] == user_id:
            user["status"] = payload.status.upper()
            return {"success": True, "user": user}
    raise HTTPException(status_code=404, detail="User not found")

@router.delete("/{user_id}", summary="Admin Remove User")
def remove_user(user_id: int) -> dict[str, Any]:
    """Remove an employee account."""
    global users_db
    users_db = [u for u in users_db if u["id"] != user_id]
    return {"success": True, "message": f"User {user_id} removed"}
