from app.core.celery_app import celery_app
from app.db.database import SessionLocal
from app.services.matching_service import run_mz_matching_for_sample
from app.services.ms2_similarity_service import score_ms2_for_sample_matches


@celery_app.task(name="run_mz_matching_task")
def run_mz_matching_task(
    sample_id: int,
    ppm_tolerance: float = 10.0,
    max_candidates_per_feature: int = 5,
):
    db = SessionLocal()

    try:
        return run_mz_matching_for_sample(
            db=db,
            sample_id=sample_id,
            ppm_tolerance=ppm_tolerance,
            max_candidates_per_feature=max_candidates_per_feature,
            clear_previous_results=True,
        )
    finally:
        db.close()


@celery_app.task(name="score_ms2_task")
def score_ms2_task(
    sample_id: int,
    mz_tolerance: float = 0.02,
    min_ms2_score: float = 0.7,
    limit: int | None = 1000,
):
    db = SessionLocal()

    try:
        return score_ms2_for_sample_matches(
            db=db,
            sample_id=sample_id,
            mz_tolerance=mz_tolerance,
            min_ms2_score=min_ms2_score,
            limit=limit,
        )
    finally:
        db.close()