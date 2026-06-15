from sqlalchemy.orm import Session

from app.db.models import MatchResult, ReferenceSpectrum, UnknownFeature


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