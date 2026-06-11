from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import MatchResult, ReferenceSpectrum, UnknownFeature
from app.services.matching_service import run_mz_matching_for_sample

router = APIRouter()


@router.post("/run/{sample_id}")
def run_matching(
    sample_id: int,
    ppm_tolerance: float = Query(default=10.0, gt=0),
    db: Session = Depends(get_db),
):
    return run_mz_matching_for_sample(
        db=db,
        sample_id=sample_id,
        ppm_tolerance=ppm_tolerance,
    )


@router.get("/results/{sample_id}")
def get_matching_results(
    sample_id: int,
    limit: int = Query(default=50, gt=0, le=500),
    db: Session = Depends(get_db),
):
    rows = (
        db.query(MatchResult, UnknownFeature, ReferenceSpectrum)
        .join(UnknownFeature, MatchResult.unknown_feature_id == UnknownFeature.id)
        .join(ReferenceSpectrum, MatchResult.reference_spectrum_id == ReferenceSpectrum.id)
        .filter(UnknownFeature.sample_id == sample_id)
        .order_by(MatchResult.ppm_error.asc())
        .limit(limit)
        .all()
    )

    results = []

    for match, unknown, reference in rows:
        results.append(
            {
                "match_id": match.id,
                "ion_mode": match.ion_mode,
                "confidence_level": match.confidence_level,
                "ppm_error": match.ppm_error,
                "mz_error": match.mz_error,
                "unknown": {
                    "feature_id": unknown.feature_id,
                    "mz": unknown.mz,
                    "retention_time_minutes": unknown.retention_time_minutes,
                },
                "reference": {
                    "spectrum_id": reference.id,
                    "name": reference.name,
                    "formula": reference.formula,
                    "adduct": reference.adduct,
                    "precursor_mz": reference.precursor_mz,
                    "retention_time_seconds": reference.retention_time_seconds,
                    "smiles": reference.smiles,
                },
            }
        )

    return {
        "sample_id": sample_id,
        "count": len(results),
        "results": results,
    }