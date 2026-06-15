from math import sqrt
from typing import Iterable

from sqlalchemy.orm import Session

from app.db.models import (
    MatchResult,
    ReferencePeak,
    ReferenceSpectrum,
    UnknownFeature,
    UnknownPeak,
    UnknownSpectrum,
)


def _prepare_peaks(peaks: Iterable) -> list[tuple[float, float]]:
    """
    Convert SQLAlchemy peak objects into sorted (mz, intensity) tuples.
    Ignores zero or negative intensities.
    """
    prepared = []

    for peak in peaks:
        if peak.mz is None or peak.intensity is None:
            continue

        if peak.intensity <= 0:
            continue

        prepared.append((float(peak.mz), float(peak.intensity)))

    return sorted(prepared, key=lambda item: item[0])


def calculate_cosine_similarity(
    unknown_peaks,
    reference_peaks,
    mz_tolerance: float = 0.02,
) -> tuple[float, int]:
    """
    Simple MS2 cosine similarity using m/z tolerance.

    Returns:
    - cosine score between 0 and 1
    - number of matched peaks
    """

    unknown = _prepare_peaks(unknown_peaks)
    reference = _prepare_peaks(reference_peaks)

    if not unknown or not reference:
        return 0.0, 0

    unknown_norm = sqrt(sum(intensity ** 2 for _, intensity in unknown))
    reference_norm = sqrt(sum(intensity ** 2 for _, intensity in reference))

    if unknown_norm == 0 or reference_norm == 0:
        return 0.0, 0

    i = 0
    j = 0
    dot_product = 0.0
    matched_peaks = 0

    while i < len(unknown) and j < len(reference):
        unknown_mz, unknown_intensity = unknown[i]
        reference_mz, reference_intensity = reference[j]

        mz_diff = unknown_mz - reference_mz

        if abs(mz_diff) <= mz_tolerance:
            dot_product += unknown_intensity * reference_intensity
            matched_peaks += 1
            i += 1
            j += 1
        elif mz_diff < 0:
            i += 1
        else:
            j += 1

    score = dot_product / (unknown_norm * reference_norm)

    return float(score), matched_peaks


def score_ms2_for_sample_matches(
    db: Session,
    sample_id: int,
    mz_tolerance: float = 0.02,
    min_ms2_score: float = 0.7,
    limit: int | None = None,
) -> dict:
    """
    For each MatchResult of a sample:
    - find the unknown spectrum linked by feature_id
    - find reference spectrum peaks
    - calculate MS2 cosine similarity
    - update MatchResult.ms2_score
    - update confidence_level
    """

    query = (
        db.query(MatchResult, UnknownFeature, ReferenceSpectrum)
        .join(UnknownFeature, MatchResult.unknown_feature_id == UnknownFeature.id)
        .join(ReferenceSpectrum, MatchResult.reference_spectrum_id == ReferenceSpectrum.id)
        .filter(UnknownFeature.sample_id == sample_id)
        .order_by(MatchResult.ppm_error.asc())
    )

    if limit:
        query = query.limit(limit)

    rows = query.all()

    scored_matches = 0
    matches_with_unknown_spectrum = 0
    matches_above_threshold = 0

    for match, unknown_feature, reference_spectrum in rows:
        unknown_spectrum = (
            db.query(UnknownSpectrum)
            .filter(UnknownSpectrum.sample_id == sample_id)
            .filter(UnknownSpectrum.feature_id == unknown_feature.feature_id)
            .first()
        )

        if unknown_spectrum is None:
            continue

        matches_with_unknown_spectrum += 1

        unknown_peaks = (
            db.query(UnknownPeak)
            .filter(UnknownPeak.spectrum_id == unknown_spectrum.id)
            .all()
        )

        reference_peaks = (
            db.query(ReferencePeak)
            .filter(ReferencePeak.spectrum_id == reference_spectrum.id)
            .all()
        )

        score, matched_peaks = calculate_cosine_similarity(
            unknown_peaks=unknown_peaks,
            reference_peaks=reference_peaks,
            mz_tolerance=mz_tolerance,
        )

        match.ms2_score = score

        if score >= min_ms2_score:
            match.confidence_level = "MZ_MS2"
            matches_above_threshold += 1
        else:
            match.confidence_level = "MZ_ONLY"

        scored_matches += 1

    db.commit()

    return {
        "sample_id": sample_id,
        "matches_checked": len(rows),
        "matches_with_unknown_spectrum": matches_with_unknown_spectrum,
        "scored_matches": scored_matches,
        "matches_above_ms2_threshold": matches_above_threshold,
        "mz_tolerance": mz_tolerance,
        "min_ms2_score": min_ms2_score,
    }