from app.db.database import SessionLocal
from app.services.ingestion_service import (
    import_reference_mgf,
    import_unknown_sample,
)


def main():
    db = SessionLocal()

    try:
        print("Importing NEG reference library...")
        neg_ref_result = import_reference_mgf(
            db=db,
            file_path="data/reference/neg/20241003_enamdisc_neg_ms2.mgf",
            library_name="enamdisc_neg",
            ion_mode="NEG",
        )
        print(neg_ref_result)

        print("Importing POS reference library...")
        pos_ref_result = import_reference_mgf(
            db=db,
            file_path="data/reference/pos/20241003_enamdisc_pos_ms2.mgf",
            library_name="enamdisc_pos",
            ion_mode="POS",
        )
        print(pos_ref_result)

        print("Importing NEG unknown sample...")
        neg_sample_result = import_unknown_sample(
            db=db,
            csv_file_path="data/unknown/neg/NEG_fbmn_quant.csv",
            mgf_file_path="data/unknown/neg/NEG_fbmn.mgf",
            sample_name="unknown_neg_fbmn",
            ion_mode="NEG",
        )
        print(neg_sample_result)

        print("Importing POS unknown sample...")
        pos_sample_result = import_unknown_sample(
            db=db,
            csv_file_path="data/unknown/pos/POS_fbmn_quant.csv",
            mgf_file_path="data/unknown/pos/POS_fbmn.mgf",
            sample_name="unknown_pos_fbmn",
            ion_mode="POS",
        )
        print(pos_sample_result)

    finally:
        db.close()


if __name__ == "__main__":
    main()