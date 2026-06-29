from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from app.services.ms2_similarity_service import score_ms2_for_sample_matches
from app.db.database import get_db
from app.db.models import MatchResult, ReferenceSpectrum, UnknownFeature
from app.services.matching_service import (
    get_matching_summary_for_sample,
    get_ranked_results_for_sample,
    run_mz_matching_for_sample,
)

from io import StringIO

from app.services.export_service import generate_ranked_results_csv
from app.tasks import run_mz_matching_task, score_ms2_task

router = APIRouter()


@router.post("/run/{sample_id}")
def run_matching(
    sample_id: int,
    ppm_tolerance: float = Query(default=10.0, gt=0),
    max_candidates_per_feature: int = Query(default=5, gt=0, le=50),
    db: Session = Depends(get_db),
):
    return run_mz_matching_for_sample(
        db=db,
        sample_id=sample_id,
        ppm_tolerance=ppm_tolerance,
        max_candidates_per_feature=max_candidates_per_feature,
    )

@router.post("/score-ms2/{sample_id}")
def score_ms2_matches(
    sample_id: int,
    mz_tolerance: float = Query(default=0.02, gt=0),
    min_ms2_score: float = Query(default=0.7, ge=0, le=1),
    limit: int | None = Query(default=1000, gt=0),
    db: Session = Depends(get_db),
):
    return score_ms2_for_sample_matches(
        db=db,
        sample_id=sample_id,
        mz_tolerance=mz_tolerance,
        min_ms2_score=min_ms2_score,
        limit=limit,
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


@router.get("/ranked-results/{sample_id}")
def get_ranked_results(
    sample_id: int,
    limit_features: int = Query(default=50, gt=0, le=500),
    candidates_per_feature: int = Query(default=3, gt=0, le=20),
    db: Session = Depends(get_db),
):
    return get_ranked_results_for_sample(
        db=db,
        sample_id=sample_id,
        limit_features=limit_features,
        candidates_per_feature=candidates_per_feature,
    )

@router.get("/summary/{sample_id}")
def get_matching_summary(
    sample_id: int,
    ppm_tolerance: float = Query(default=10.0, gt=0),
    ms2_threshold: float = Query(default=0.7, ge=0, le=1),
    top_limit: int = Query(default=10, gt=0, le=100),
    db: Session = Depends(get_db),
):
    return get_matching_summary_for_sample(
        db=db,
        sample_id=sample_id,
        ppm_tolerance=ppm_tolerance,
        ms2_threshold=ms2_threshold,
        top_limit=top_limit,
    )


@router.get("/export-csv/{sample_id}")
def export_ranked_results_csv(
    sample_id: int,
    ppm_tolerance: float = Query(default=10.0, gt=0),
    ms2_threshold: float = Query(default=0.7, ge=0, le=1),
    limit: int = Query(default=1000, gt=0, le=10000),
    db: Session = Depends(get_db),
):
    csv_content = generate_ranked_results_csv(
        db=db,
        sample_id=sample_id,
        ppm_tolerance=ppm_tolerance,
        ms2_threshold=ms2_threshold,
        limit=limit,
    )

    file_like = StringIO(csv_content)

    filename = f"sample_{sample_id}_ranked_results.csv"

    return StreamingResponse(
        file_like,
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename={filename}"
        },
    )


@router.post("/run-task/{sample_id}")
def run_matching_task_endpoint(
    sample_id: int,
    ppm_tolerance: float = Query(default=10.0, gt=0),
    max_candidates_per_feature: int = Query(default=5, gt=0, le=50),
):
    task = run_mz_matching_task.delay(
        sample_id=sample_id,
        ppm_tolerance=ppm_tolerance,
        max_candidates_per_feature=max_candidates_per_feature,
    )

    return {
        "message": "m/z matching task executed.",
        "task_id": task.id,
        "sample_id": sample_id,
        "result": task.result,
    }


@router.post("/score-ms2-task/{sample_id}")
def score_ms2_task_endpoint(
    sample_id: int,
    mz_tolerance: float = Query(default=0.02, gt=0),
    min_ms2_score: float = Query(default=0.7, ge=0, le=1),
    limit: int | None = Query(default=1000, gt=0),
):
    task = score_ms2_task.delay(
        sample_id=sample_id,
        mz_tolerance=mz_tolerance,
        min_ms2_score=min_ms2_score,
        limit=limit,
    )

    return {
        "message": "MS2 scoring task executed.",
        "task_id": task.id,
        "sample_id": sample_id,
        "result": task.result,
    }