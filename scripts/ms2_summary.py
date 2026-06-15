from app.db.database import SessionLocal
from app.db.models import MatchResult


def main():
    db = SessionLocal()

    try:
        total = db.query(MatchResult).count()

        scored = (
            db.query(MatchResult)
            .filter(MatchResult.ms2_score.isnot(None))
            .count()
        )

        strong = (
            db.query(MatchResult)
            .filter(MatchResult.confidence_level == "MZ_MS2")
            .count()
        )

        mz_only = (
            db.query(MatchResult)
            .filter(MatchResult.confidence_level == "MZ_ONLY")
            .count()
        )

        print("MS2 summary")
        print("=" * 50)
        print("Total matches:", total)
        print("Scored matches:", scored)
        print("MZ_MS2 matches:", strong)
        print("MZ_ONLY matches:", mz_only)

    finally:
        db.close()


if __name__ == "__main__":
    main()