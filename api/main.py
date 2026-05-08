"""
ResourceAAS FastAPI backend.

Run from the repo root:
    uvicorn api.main:app --reload --port 8000
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routers import generate_aas, validate

app = FastAPI(
    title="ResourceAAS API",
    description="Backend for the ResourceAAS UI: SHACL validation and AI generation context.",
    version="2.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5678",
        "http://127.0.0.1:5678",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(validate.router, prefix="/api", tags=["validate"])
app.include_router(generate_aas.router, prefix="/api", tags=["generate"])


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
