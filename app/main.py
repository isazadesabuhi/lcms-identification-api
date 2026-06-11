from fastapi import FastAPI
from app.api.routes import health, reference, samples, matching

app = FastAPI(
    title="LC-MS Compound Identification API",
    description="FastAPI platform for identifying unknown compounds from MZmine CSV and MGF exports.",
    version="0.1.0",
)

app.include_router(health.router, prefix="/health", tags=["Health"])
app.include_router(reference.router, prefix="/reference", tags=["Reference Library"])
app.include_router(samples.router, prefix="/samples", tags=["Unknown Samples"])
app.include_router(matching.router, prefix="/matching", tags=["Matching"])