from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import health, matching, molecules, reference, samples
from app.core.config import settings

app = FastAPI(
    title="LC-MS Compound Identification API",
    description="FastAPI platform for identifying unknown compounds from MZmine CSV and MGF exports.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        origin.strip()
        for origin in settings.cors_origins.split(",")
        if origin.strip()
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, prefix="/health", tags=["Health"])
app.include_router(reference.router, prefix="/reference", tags=["Reference Library"])
app.include_router(samples.router, prefix="/samples", tags=["Unknown Samples"])
app.include_router(matching.router, prefix="/matching", tags=["Matching"])
app.include_router(molecules.router, prefix="/molecules", tags=["Molecules"])
