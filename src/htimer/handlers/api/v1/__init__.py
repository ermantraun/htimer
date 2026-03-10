from fastapi import APIRouter
from fastapi import HTTPException


routers: list[APIRouter] = []

exception_handlers: list[HTTPException] = []

__all__ = ["routers", "exception_handlers"]