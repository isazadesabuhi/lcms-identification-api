from app.db.database import SessionLocal
from app.services.matching_service import run_mz_matching_for_sample


def main():
    db = SessionLocal()

    try:
        # If you imported NEG first and POS second, usually:
        # sample_id=1 => unknown_neg_fbmn
        # sample_id=2 => unknown_pos_fbmn

        print("Running NEG sample matching...")
        neg_result = run_mz_matching_for_sample(
            db=db,
            sample_id=1,
            ppm_tolerance=10.0,
        )
        print(neg_result)

        print("Running POS sample matching...")
        pos_result = run_mz_matching_for_sample(
            db=db,
            sample_id=2,
            ppm_tolerance=10.0,
        )
        print(pos_result)

    finally:
        db.close()


if __name__ == "__main__":
    main()