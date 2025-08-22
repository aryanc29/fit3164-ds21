from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid

from app.core.database import Base


class User(Base):
    """User model for authentication and authorization"""
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    
    # Authentication
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    
    # Profile information
    first_name = Column(String(100))
    last_name = Column(String(100))
    organization = Column(String(200))
    user_type = Column(String(50), default="general")  # student, educator, farmer, planner, researcher, general
    
    # 2FA
    is_2fa_enabled = Column(Boolean, default=False)
    totp_secret = Column(String(32))  # Base32 encoded secret
    backup_codes = Column(Text)  # JSON array of backup codes
    
    # Account management
    last_login = Column(DateTime)
    password_reset_token = Column(String(255))
    password_reset_expires = Column(DateTime)
    email_verification_token = Column(String(255))
    email_verification_expires = Column(DateTime)
    
    # Preferences
    preferred_units = Column(String(20), default="metric")  # metric, imperial
    timezone = Column(String(50), default="UTC")
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    datasets = relationship("UserDataset", back_populates="user", cascade="all, delete-orphan")
    feedback = relationship("UserFeedback", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User(username='{self.username}', email='{self.email}')>"


class UserFeedback(Base):
    """User feedback model"""
    __tablename__ = "user_feedback"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=True)  # Allow anonymous feedback
    
    # Feedback content
    subject = Column(String(200), nullable=False)
    message = Column(Text, nullable=False)
    category = Column(String(50), default="general")  # bug, feature, general, usability
    
    # Contact information (for anonymous users)
    contact_email = Column(String(255))
    contact_name = Column(String(100))
    
    # Status tracking
    status = Column(String(20), default="new")  # new, in_progress, resolved, closed
    priority = Column(String(20), default="normal")  # low, normal, high, critical
    
    # Response
    admin_response = Column(Text)
    response_date = Column(DateTime)
    
    # Browser/System info for bug reports
    user_agent = Column(String(500))
    page_url = Column(String(500))
    browser_info = Column(Text)  # JSON string
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="feedback")

    def __repr__(self):
        return f"<UserFeedback(subject='{self.subject}', status='{self.status}')>"


class UserSession(Base):
    """User session model for JWT token management"""
    __tablename__ = "user_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    
    # Token information
    refresh_token_hash = Column(String(255), nullable=False)
    access_token_jti = Column(String(255))  # JWT ID for access token
    
    # Session metadata
    device_info = Column(String(500))
    ip_address = Column(String(45))  # IPv6 max length
    user_agent = Column(String(500))
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    last_used = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)
    
    # Status
    is_active = Column(Boolean, default=True)
    revoked_at = Column(DateTime)
    revoked_reason = Column(String(100))

    def __repr__(self):
        return f"<UserSession(user_id='{self.user_id}', active='{self.is_active}')>"
