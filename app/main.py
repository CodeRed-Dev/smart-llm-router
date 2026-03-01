"""
Smart LLM Router - Main FastAPI Application

This is the entry point for the Smart LLM Router service.
It provides the API endpoints for intelligent LLM routing with quality evaluation and fallback.
"""

from fastapi import FastAPI
from app.router import router as chat_router
from app.metrics import router as metrics_router

app = FastAPI(
    title="Smart LLM Router",
    description="Intelligent LLM routing with automated evaluation and fallback",
    version="0.1.0"
)

# Include routers
app.include_router(chat_router)
app.include_router(metrics_router)

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"ok": True}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)