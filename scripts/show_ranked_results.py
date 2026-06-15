from app.db.database import SessionLocal
from app.db.models import MatchResult, ReferenceSpectrum, UnknownFeature


def show_ranked_results(sample_id: int, limit_features: int = 20, candidates_per_feature: int = 3):
    db = SessionLocal()

    try:
        unknown_features = (
            db.query(UnknownFeature)
            .filter(UnknownFeature.sample_id == sample_id)
            .limit(limit_features)
            .all()
        )

        for feature in unknown_features:
            matches = (
                db.query(MatchResult, ReferenceSpectrum)
                .join(ReferenceSpectrum, MatchResult.reference_spectrum_id == ReferenceSpectrum.id)
                .filter(MatchResult.unknown_feature_id == feature.id)
                .order_by(
                    MatchResult.ms2_score.desc().nullslast(),
                    MatchResult.ppm_error.asc(),
                )
                .limit(candidates_per_feature)
                .all()
            )

            if not matches:
                continue

            print("=" * 100)
            print(
                f"Unknown feature {feature.feature_id} | "
                f"m/z: {feature.mz:.6f} | "
                f"RT: {feature.retention_time_minutes} min | "
                f"Ion mode: {feature.ion_mode}"
            )

            for match, reference in matches:
                print(
                    f"  Candidate: {reference.name} | "
                    f"Formula: {reference.formula} | "
                    f"Adduct: {reference.adduct} | "
                    f"Ref m/z: {reference.precursor_mz:.6f} | "
                    f"ppm: {match.ppm_error:.3f} | "
                    f"MS2: {match.ms2_score} | "
                    f"Confidence: {match.confidence_level}"
                )

    finally:
        db.close()


if __name__ == "__main__":
    print("NEG ranked results")
    show_ranked_results(sample_id=1)

    print("\nPOS ranked results")
    show_ranked_results(sample_id=2)