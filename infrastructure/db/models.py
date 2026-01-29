from sqlalchemy.orm import DeclarativeBase, Mapped
from sqlalchemy import Column, UUID as sql_uuid
from typing import Optional
from uuid import UUID

"""     uuid: UUID
    name: str
    email: str
    password_hash: str
    creator: User
    role: UserRole
    created_at: date
    status: UserStatus = UserStatus.ACTIVE
    last_login: str | None = None """
class Base(DeclarativeBase):
    pass

class UserModel(Base):
    __tablename__ = "users"

    uuid: Mapped[UUID] = Column(sql_uuid, primary_key=True, nullable=False)