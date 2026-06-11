from app.db.database import SessionLocal
from app.db.models import (
    MatchResult,
    ReferenceLibrary,
    ReferencePeak,
    ReferenceSpectrum,
    UnknownFeature,
    UnknownPeak,
    UnknownSample,
    UnknownSpectrum,
)


def main():
    db = SessionLocal()

    try:
        print("Reference libraries:", db.query(ReferenceLibrary).count())
        print("Reference spectra:", db.query(ReferenceSpectrum).count())
        print("Reference peaks:", db.query(ReferencePeak).count())

        print("Unknown samples:", db.query(UnknownSample).count())
        print("Unknown features:", db.query(UnknownFeature).count())
        print("Unknown spectra:", db.query(UnknownSpectrum).count())
        print("Unknown peaks:", db.query(UnknownPeak).count())

        print("Match results:", db.query(MatchResult).count())

        print("\nReference libraries:")
        for library in db.query(ReferenceLibrary).all():
            print(library.id, library.name, library.ion_mode, library.source_filename)

        print("\nUnknown samples:")
        for sample in db.query(UnknownSample).all():
            print(sample.id, sample.name, sample.ion_mode, sample.csv_filename, sample.mgf_filename)

    finally:
        db.close()


if __name__ == "__main__":
    main()