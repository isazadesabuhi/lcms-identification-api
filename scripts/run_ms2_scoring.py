from app.db.database import SessionLocal
from app.services.ms2_similarity_service import score_ms2_for_sample_matches


def main():
    db = SessionLocal()

    try:
        print("Scoring NEG matches with MS2 similarity...")
        neg_result = score_ms2_for_sample_matches(
            db=db,
            sample_id=1,
            mz_tolerance=0.02,
            min_ms2_score=0.7,
            limit=1000,
        )
        print(neg_result)

        print("Scoring POS matches with MS2 similarity...")
        pos_result = score_ms2_for_sample_matches(
            db=db,
            sample_id=2,
            mz_tolerance=0.02,
            min_ms2_score=0.7,
            limit=1000,
        )
        print(pos_result)

    finally:
        db.close()


if __name__ == "__main__":
    main()