def calculate_mz_score(ppm_error: float, ppm_tolerance: float = 10.0) -> float:
    """
    Convert ppm error into a score between 0 and 1.
    Lower ppm error = better score.
    """
    if ppm_error is None:
        return 0.0

    score = 1 - (ppm_error / ppm_tolerance)
    return round(max(0.0, min(1.0, score)), 4)


def calculate_rt_score(
    rt_error_seconds: float | None,
    rt_tolerance_seconds: float = 30.0,
) -> float | None:
    """
    Convert retention time error into a score between 0 and 1.
    Lower RT error = better score.

    If RT is missing, return None.
    """
    if rt_error_seconds is None:
        return None

    score = 1 - (rt_error_seconds / rt_tolerance_seconds)
    return round(max(0.0, min(1.0, score)), 4)


def calculate_overall_score(
    ppm_error: float,
    ms2_score: float | None,
    rt_error_seconds: float | None = None,
    ppm_tolerance: float = 10.0,
    rt_tolerance_seconds: float = 30.0,
) -> float:
    """
    Temporary MVP scoring.

    If MS2 and RT are available:
    - 60% MS2
    - 25% m/z
    - 15% RT

    If RT is not available:
    - 70% MS2
    - 30% m/z

    If MS2 is not available:
    - m/z score only, reduced weight
    """

    mz_score = calculate_mz_score(ppm_error, ppm_tolerance)
    rt_score = calculate_rt_score(rt_error_seconds, rt_tolerance_seconds)

    if ms2_score is None:
        if rt_score is None:
            return round(mz_score * 0.3, 4)

        return round((mz_score * 0.7) + (rt_score * 0.3), 4)

    if rt_score is None:
        overall_score = (ms2_score * 0.7) + (mz_score * 0.3)
    else:
        overall_score = (ms2_score * 0.6) + (mz_score * 0.25) + (rt_score * 0.15)

    return round(overall_score, 4)


def assign_confidence_level(ms2_score: float | None) -> str:
    """
    Temporary confidence levels before official L1-L5.
    """

    if ms2_score is None:
        return "MZ_ONLY"

    if ms2_score >= 0.7:
        return "MZ_MS2_HIGH"

    if ms2_score >= 0.4:
        return "MZ_MS2_MEDIUM"

    return "MZ_MS2_LOW"


def assign_identification_level(
    mz_match: bool,
    rt_match: bool,
    formula_match: bool,
    adduct_match: bool,
    ms2_match: bool,
) -> str:
    """
    Assign confidence level based on supervisor's L1-L5 logic.

    Current limitation:
    - Unknown formula/adduct are not yet clearly available from the uploaded unknown files.
    - Therefore L1/L2/L3/L5 may not appear until formula/adduct extraction is added.
    """

    if rt_match and mz_match and formula_match and adduct_match and ms2_match:
        return "L1"

    if mz_match and formula_match and adduct_match and ms2_match:
        return "L2"

    if formula_match and ms2_match:
        return "L3"

    if ms2_match:
        return "L4"

    if formula_match:
        return "L5"

    if mz_match and rt_match:
        return "MZ_RT_CANDIDATE"

    if mz_match:
        return "MZ_ONLY_CANDIDATE"

    return "NO_CONFIDENT_MATCH"