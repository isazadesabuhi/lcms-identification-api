def calculate_mz_score(ppm_error: float, ppm_tolerance: float = 10.0) -> float:
    """
    Convert ppm error into a score between 0 and 1.
    Lower ppm error = better score.
    """
    if ppm_error is None:
        return 0.0

    score = 1 - (ppm_error / ppm_tolerance)

    return max(0.0, min(1.0, score))


def calculate_overall_score(
    ppm_error: float,
    ms2_score: float | None,
    ppm_tolerance: float = 10.0,
) -> float:
    """
    Temporary MVP scoring:
    - 70% MS2 score
    - 30% m/z score
    """

    mz_score = calculate_mz_score(ppm_error, ppm_tolerance)

    if ms2_score is None:
        return round(mz_score * 0.3, 4)

    overall_score = (ms2_score * 0.7) + (mz_score * 0.3)

    return round(overall_score, 4)


def assign_confidence_level(ms2_score: float | None) -> str:
    """
    Temporary confidence levels before implementing official L1-L5.
    """

    if ms2_score is None:
        return "MZ_ONLY"

    if ms2_score >= 0.7:
        return "MZ_MS2_HIGH"

    if ms2_score >= 0.4:
        return "MZ_MS2_MEDIUM"

    return "MZ_MS2_LOW"