from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    # clerk_user_id is the authoritative identity key — set by Clerk on first sign-in.
    clerk_user_id = Column(String(255), unique=True, index=True, nullable=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    # password_hash is kept nullable; Clerk owns authentication so no local password is stored.
    password_hash = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships — integer PK preserved so households.owner_id FK stays intact.
    households = relationship("Household", back_populates="owner", cascade="all, delete-orphan")

