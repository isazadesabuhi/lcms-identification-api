from sqlalchemy import func
from sqlalchemy.orm import Session

from app.db.models import MatchResult, ReferenceSpectrum, UnknownFeature
from app.services.scoring_service import (
    assign_identification_level,
    calculate_mz_score,
    calculate_overall_score,
    calculate_rt_score,
)


def calculate_ppm_error(unknown_mz: float, reference_mz: float) -> float:
    """
    Calculate ppm error between unknown feature m/z and reference precursor m/z.
    """
    return abs(unknown_mz - reference_mz) / reference_mz * 1_000_000


def run_mz_matching_for_sample(
    db: Session,
    sample_id: int,
    ppm_tolerance: float = 10.0,
    max_candidates_per_feature: int = 5,
    clear_previous_results: bool = True,
) -> dict:
    """
    Basic matching:
    - takes unknown features from one sample
    - compares them against reference spectra with the same ion mode
    - keeps only the best candidates by ppm error for each unknown feature
    - stores matches where ppm error <= ppm_tolerance
    """

    unknown_features = (
        db.query(UnknownFeature)
        .filter(UnknownFeature.sample_id == sample_id)
        .all()
    )

    if not unknown_features:
        return {
            "sample_id": sample_id,
            "message": "No unknown features found for this sample.",
            "matches_created": 0,
        }

    ion_mode = unknown_features[0].ion_mode

    if clear_previous_results:
        unknown_feature_ids = [feature.id for feature in unknown_features]

        db.query(MatchResult).filter(
            MatchResult.unknown_feature_id.in_(unknown_feature_ids)
        ).delete(synchronize_session=False)

        db.commit()

    matches_created = 0
    features_with_matches = 0
    total_candidates_before_filtering = 0

    for feature in unknown_features:
        if feature.mz is None:
            continue

        mz_delta = feature.mz * ppm_tolerance / 1_000_000
        min_mz = feature.mz - mz_delta
        max_mz = feature.mz + mz_delta

        reference_candidates = (
            db.query(ReferenceSpectrum)
            .filter(ReferenceSpectrum.ion_mode == ion_mode)
            .filter(ReferenceSpectrum.precursor_mz >= min_mz)
            .filter(ReferenceSpectrum.precursor_mz <= max_mz)
            .all()
        )

        candidate_rows = []

        for reference in reference_candidates:
            if reference.precursor_mz is None:
                continue

            ppm_error = calculate_ppm_error(
                unknown_mz=feature.mz,
                reference_mz=reference.precursor_mz,
            )

            if ppm_error <= ppm_tolerance:
                candidate_rows.append(
                    {
                        "reference": reference,
                        "ppm_error": ppm_error,
                        "mz_error": abs(feature.mz - reference.precursor_mz),
                    }
                )

        if not candidate_rows:
            continue

        features_with_matches += 1
        total_candidates_before_filtering += len(candidate_rows)

        # Keep only best candidates for this unknown feature
        candidate_rows = sorted(
            candidate_rows,
            key=lambda item: item["ppm_error"],
        )[:max_candidates_per_feature]

        for candidate in candidate_rows:
            reference = candidate["reference"]

            match = MatchResult(
                unknown_feature_id=feature.id,
                reference_spectrum_id=reference.id,
                ion_mode=ion_mode,
                mz_error=candidate["mz_error"],
                ppm_error=candidate["ppm_error"],
                confidence_level="MZ_ONLY",
            )

            db.add(match)
            matches_created += 1

    db.commit()

    return {
        "sample_id": sample_id,
        "ion_mode": ion_mode,
        "ppm_tolerance": ppm_tolerance,
        "max_candidates_per_feature": max_candidates_per_feature,
        "unknown_features_checked": len(unknown_features),
        "features_with_matches": features_with_matches,
        "total_candidates_before_filtering": total_candidates_before_filtering,
        "matches_created": matches_created,
    }



def get_ranked_results_for_sample(
    db: Session,
    sample_id: int,
    limit_features: int = 50,
    candidates_per_feature: int = 3,
) -> dict:
    """
    Return ranked identification candidates for each unknown feature.

    Ranking:
    1. Highest MS2 score first
    2. Lowest ppm error second
    """

    unknown_features = (
        db.query(UnknownFeature)
        .filter(UnknownFeature.sample_id == sample_id)
        .limit(limit_features)
        .all()
    )

    results = []

    for feature in unknown_features:
        matches = (
            db.query(MatchResult, ReferenceSpectrum)
            .join(
                ReferenceSpectrum,
                MatchResult.reference_spectrum_id == ReferenceSpectrum.id,
            )
            .filter(MatchResult.unknown_feature_id == feature.id)
            .order_by(
                func.coalesce(MatchResult.ms2_score, -1).desc(),
                MatchResult.ppm_error.asc(),
            )
            .limit(candidates_per_feature)
            .all()
        )

        if not matches:
            continue

        candidates = []

        for match, reference in matches:
            unknown_rt_seconds = (
                feature.retention_time_minutes * 60
                if feature.retention_time_minutes is not None
                else None
            )

            reference_rt_seconds = reference.retention_time_seconds

            rt_error_seconds = None

            if unknown_rt_seconds is not None and reference_rt_seconds is not None:
                rt_error_seconds = abs(unknown_rt_seconds - reference_rt_seconds)

            mz_score = calculate_mz_score(match.ppm_error)

            rt_score = calculate_rt_score(rt_error_seconds)

            overall_score = calculate_overall_score(
                ppm_error=match.ppm_error,
                ms2_score=match.ms2_score,
                rt_error_seconds=rt_error_seconds,
            )

            mz_match = match.ppm_error is not None and match.ppm_error <= 10

            rt_match = rt_score is not None and rt_score > 0

            ms2_match = match.ms2_score is not None and match.ms2_score >= 0.7

            # Not available yet from unknown CSV/MGF
            formula_match = False
            adduct_match = False

            confidence = assign_identification_level(
                mz_match=mz_match,
                rt_match=rt_match,
                formula_match=formula_match,
                adduct_match=adduct_match,
                ms2_match=ms2_match,
            )

            candidates.append(
                {
                    "match_id": match.id,
                    "confidence_level": confidence,
                    "ppm_error": match.ppm_error,
                    "mz_error": match.mz_error,
                    "mz_score": mz_score,
                    "rt_error_seconds": rt_error_seconds,
                    "rt_score": rt_score,
                    "ms2_score": match.ms2_score,
                    "overall_score": overall_score,
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
        
        results.append(
            {
                "unknown_feature": {
                    "id": feature.id,
                    "feature_id": feature.feature_id,
                    "mz": feature.mz,
                    "retention_time_minutes": feature.retention_time_minutes,
                    "ion_mode": feature.ion_mode,
                    "best_ion": feature.best_ion,
                    "neutral_mass": feature.neutral_mass,
                },
                "candidates": candidates,
            }
        )

    return {
        "sample_id": sample_id,
        "limit_features": limit_features,
        "candidates_per_feature": candidates_per_feature,
        "features_with_candidates": len(results),
        "results": results,
    }


def get_matching_summary_for_sample(
    db: Session,
    sample_id: int,
    ppm_tolerance: float = 10.0,
    ms2_threshold: float = 0.7,
    top_limit: int = 10,
) -> dict:
    """
    Return a high-level matching summary for one unknown sample.
    """

    total_features = (
        db.query(UnknownFeature)
        .filter(UnknownFeature.sample_id == sample_id)
        .count()
    )

    rows = (
        db.query(MatchResult, UnknownFeature, ReferenceSpectrum)
        .join(UnknownFeature, MatchResult.unknown_feature_id == UnknownFeature.id)
        .join(ReferenceSpectrum, MatchResult.reference_spectrum_id == ReferenceSpectrum.id)
        .filter(UnknownFeature.sample_id == sample_id)
        .all()
    )

    confidence_counts = {}
    features_with_candidates = set()
    scored_ms2_candidates = 0
    strong_ms2_candidates = 0
    ranked_candidates = []

    for match, feature, reference in rows:
        features_with_candidates.add(feature.id)

        unknown_rt_seconds = (
            feature.retention_time_minutes * 60
            if feature.retention_time_minutes is not None
            else None
        )

        reference_rt_seconds = reference.retention_time_seconds

        rt_error_seconds = None

        if unknown_rt_seconds is not None and reference_rt_seconds is not None:
            rt_error_seconds = abs(unknown_rt_seconds - reference_rt_seconds)

        rt_score = calculate_rt_score(rt_error_seconds)

        mz_match = match.ppm_error is not None and match.ppm_error <= ppm_tolerance
        rt_match = rt_score is not None and rt_score > 0
        ms2_match = match.ms2_score is not None and match.ms2_score >= ms2_threshold

        # Current limitation: unknown formula/adduct are not yet available
        formula_match = False
        adduct_match = False

        confidence = assign_identification_level(
            mz_match=mz_match,
            rt_match=rt_match,
            formula_match=formula_match,
            adduct_match=adduct_match,
            ms2_match=ms2_match,
        )

        confidence_counts[confidence] = confidence_counts.get(confidence, 0) + 1

        if match.ms2_score is not None:
            scored_ms2_candidates += 1

        if ms2_match:
            strong_ms2_candidates += 1

        overall_score = calculate_overall_score(
            ppm_error=match.ppm_error,
            ms2_score=match.ms2_score,
            rt_error_seconds=rt_error_seconds,
        )

        ranked_candidates.append(
            {
                "unknown_feature_id": feature.feature_id,
                "unknown_mz": feature.mz,
                "ion_mode": feature.ion_mode,
                "reference_name": reference.name,
                "reference_formula": reference.formula,
                "reference_adduct": reference.adduct,
                "reference_mz": reference.precursor_mz,
                "ppm_error": match.ppm_error,
                "ms2_score": match.ms2_score,
                "rt_error_seconds": rt_error_seconds,
                "overall_score": overall_score,
                "confidence_level": confidence,
            }
        )

    ranked_candidates = sorted(
        ranked_candidates,
        key=lambda item: (
            item["overall_score"] if item["overall_score"] is not None else 0
        ),
        reverse=True,
    )[:top_limit]

    return {
        "sample_id": sample_id,
        "total_unknown_features": total_features,
        "features_with_candidates": len(features_with_candidates),
        "total_candidate_matches": len(rows),
        "scored_ms2_candidates": scored_ms2_candidates,
        "strong_ms2_candidates": strong_ms2_candidates,
        "confidence_counts": confidence_counts,
        "top_candidates": ranked_candidates,
    }