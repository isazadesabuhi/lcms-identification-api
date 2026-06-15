from app.db.database import SessionLocal
from app.services.matching_service import run_mz_matching_for_sample


def main():
    db = SessionLocal()

    try:
        print("Running NEG sample matching...")
        neg_result = run_mz_matching_for_sample(
            db=db,
            sample_id=1,
            ppm_tolerance=10.0,
            max_candidates_per_feature=5,
            clear_previous_results=True,
        )
        print(neg_result)

        print("Running POS sample matching...")
        pos_result = run_mz_matching_for_sample(
            db=db,
            sample_id=2,
            ppm_tolerance=10.0,
            max_candidates_per_feature=5,
            clear_previous_results=True,
        )
        print(pos_result)

    finally:
        db.close()


if __name__ == "__main__":
    main()