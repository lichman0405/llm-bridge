# app/api/v1/router.py
# This module defines the main API router for version 1 of our API.
# It includes all the endpoint routers for this version, allowing us to organize our API endpoints clean
# and maintainable.
# Author: Shibo Li
# Date: 2025-07-14
# Version: 0.1.0


from fastapi import APIRouter
from app.api.v1.endpoints import chat, anthropic_proxy

api_router = APIRouter()
api_router.include_router(chat.router, prefix="/v1", tags=["Chat (OpenAI Standard)"])
api_router.include_router(anthropic_proxy.router, prefix="/anthropic", tags=["Proxy (Anthropic)"])