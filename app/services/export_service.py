import csv
from io import StringIO

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.db.models import MatchResult, ReferenceSpectrum, UnknownFeature
from app.services.scoring_service import (
    assign_identification_level,
    calculate_mz_score,
    calculate_overall_score,
    calculate_rt_score,
)


def generate_ranked_results_csv(
    db: Session,
    sample_id: int,
    ppm_tolerance: float = 10.0,
    ms2_threshold: float = 0.7,
    limit: int = 1000,
) -> str:
    """
    Generate CSV content for ranked candidate identification results.
    """

    rows = (
        db.query(MatchResult, UnknownFeature, ReferenceSpectrum)
        .join(UnknownFeature, MatchResult.unknown_feature_id == UnknownFeature.id)
        .join(ReferenceSpectrum, MatchResult.reference_spectrum_id == ReferenceSpectrum.id)
        .filter(UnknownFeature.sample_id == sample_id)
        .order_by(
            func.coalesce(MatchResult.ms2_score, -1).desc(),
            MatchResult.ppm_error.asc(),
        )
        .limit(limit)
        .all()
    )

    output = StringIO()

    fieldnames = [
        "sample_id",
        "unknown_feature_id",
        "ion_mode",
        "unknown_mz",
        "unknown_retention_time_minutes",
        "reference_spectrum_id",
        "reference_name",
        "reference_formula",
        "reference_adduct",
        "reference_mz",
        "reference_retention_time_minutes",
        "ppm_error",
        "mz_error",
        "mz_score",
        "rt_error_minutes",
        "rt_score",
        "ms2_score",
        "overall_score",
        "confidence_level",
        "smiles",
    ]

    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()

    for match, feature, reference in rows:
        unknown_rt_minutes = feature.retention_time_minutes
        reference_rt_minutes = reference.retention_time_minutes

        rt_error_minutes = None

        if unknown_rt_minutes is not None and reference_rt_minutes is not None:
            rt_error_minutes = abs(unknown_rt_minutes - reference_rt_minutes)

        mz_score = calculate_mz_score(match.ppm_error)
        rt_score = calculate_rt_score(rt_error_minutes)

        overall_score = calculate_overall_score(
            ppm_error=match.ppm_error,
            ms2_score=match.ms2_score,
            rt_error_minutes=rt_error_minutes,
        )

        mz_match = match.ppm_error is not None and match.ppm_error <= ppm_tolerance
        rt_match = rt_score is not None and rt_score > 0
        ms2_match = match.ms2_score is not None and match.ms2_score >= ms2_threshold

        # Unknown formula/adduct are not clearly available yet.
        formula_match = False
        adduct_match = False

        confidence_level = assign_identification_level(
            mz_match=mz_match,
            rt_match=rt_match,
            formula_match=formula_match,
            adduct_match=adduct_match,
            ms2_match=ms2_match,
        )

        writer.writerow(
            {
                "sample_id": sample_id,
                "unknown_feature_id": feature.feature_id,
                "ion_mode": feature.ion_mode,
                "unknown_mz": feature.mz,
                "unknown_retention_time_minutes": feature.retention_time_minutes,
                "reference_spectrum_id": reference.id,
                "reference_name": reference.name,
                "reference_formula": reference.formula,
                "reference_adduct": reference.adduct,
                "reference_mz": reference.precursor_mz,
                "reference_retention_time_minutes": reference.retention_time_minutes,
                "ppm_error": match.ppm_error,
                "mz_error": match.mz_error,
                "mz_score": mz_score,
                "rt_error_minutes": rt_error_minutes,
                "rt_score": rt_score,
                "ms2_score": match.ms2_score,
                "overall_score": overall_score,
                "confidence_level": confidence_level,
                "smiles": reference.smiles,
            }
        )

    return output.getvalue()
