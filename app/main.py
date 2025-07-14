# app/main.py
# This is the main entry point for our FastAPI application.
# It initializes the FastAPI app, includes the API routers, and defines any global settings or
# configurations needed for the application.
# Author: Shibo Li
# Date: 2025-07-14
# Version: 0.1.0

# app/main.py

from fastapi import FastAPI
from app.api.v1.router import api_router

# Create the main FastAPI application instance.
app = FastAPI(
    title="LLM Bridge API",
    version="0.1.0",
    description="A bridge to connect various LLM APIs through a unified interface."
)

# Include the version 1 API router.
# All routes from api_router will be prefixed with "/v1".
app.include_router(api_router, prefix="/v1")


@app.get("/", tags=["Health Check"])
async def read_root():
    """
    A simple health check endpoint.
    """
    return {"status": "ok", "message": "Welcome to the LLM Bridge!"}