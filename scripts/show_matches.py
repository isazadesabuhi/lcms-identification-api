from app.db.database import SessionLocal
from app.db.models import MatchResult, ReferenceSpectrum, UnknownFeature


def show_matches(limit: int = 20):
    db = SessionLocal()

    try:
        matches = (
            db.query(MatchResult, UnknownFeature, ReferenceSpectrum)
            .join(UnknownFeature, MatchResult.unknown_feature_id == UnknownFeature.id)
            .join(ReferenceSpectrum, MatchResult.reference_spectrum_id == ReferenceSpectrum.id)
            .order_by(MatchResult.ppm_error.asc())
            .limit(limit)
            .all()
        )

        print(f"Showing top {limit} matches:")
        print("=" * 100)

        for match, unknown, reference in matches:
            print(
                f"Match ID: {match.id} | "
                f"Ion mode: {match.ion_mode} | "
                f"Unknown feature: {unknown.feature_id} | "
                f"Unknown m/z: {unknown.mz:.6f} | "
                f"Reference spectrum ID: {reference.id} | "
                f"Reference: {reference.name} | "
                f"Reference m/z: {reference.precursor_mz:.6f} | "
                f"Formula: {reference.formula} | "
                f"Adduct: {reference.adduct} | "
                f"ppm error: {match.ppm_error:.3f} | "
                f"Confidence: {match.confidence_level}"
            )

    finally:
        db.close()


if __name__ == "__main__":
    show_matches()